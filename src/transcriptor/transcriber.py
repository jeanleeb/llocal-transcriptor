"""Audio transcription engine using faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

from transcriptor.config import WHISPER_MODELS


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    segments: list[Segment]
    language: str
    language_probability: float
    text: str

    def to_txt(self) -> str:
        return self.text

    def to_srt(self) -> str:
        lines: list[str] = []
        for i, seg in enumerate(self.segments, 1):
            lines.append(str(i))
            lines.append(f"{_format_time_srt(seg.start)} --> {_format_time_srt(seg.end)}")
            lines.append(seg.text.strip())
            lines.append("")
        return "\n".join(lines)

    def to_json(self) -> str:
        import json

        return json.dumps(
            {
                "language": self.language,
                "language_probability": self.language_probability,
                "text": self.text,
                "segments": [
                    {"start": s.start, "end": s.end, "text": s.text.strip()} for s in self.segments
                ],
            },
            ensure_ascii=False,
            indent=2,
        )


def _format_time_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _detect_device() -> str:
    """Detect best available compute device."""
    try:
        import torch  # ty:ignore[unresolved-import]

        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


class Transcriber:
    def __init__(self, model_name: str = "base", device: str | None = None) -> None:
        if model_name not in WHISPER_MODELS:
            msg = f"Unknown model '{model_name}'. Available: {', '.join(WHISPER_MODELS)}"
            raise ValueError(msg)

        self.model_name = model_name
        self.device = device or _detect_device()
        compute_type = "float16" if self.device == "cuda" else "int8"
        self.model = WhisperModel(model_name, device=self.device, compute_type=compute_type)

    def transcribe(
        self,
        audio_path: str | Path,
        language: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe an audio file.

        Args:
            audio_path: Path to audio/video file (ffmpeg handles format conversion).
            language: Language code ('en', 'pt') or None for auto-detection.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            msg = f"Audio file not found: {audio_path}"
            raise FileNotFoundError(msg)

        lang_arg = language if language and language != "auto" else None

        segments_iter, info = self.model.transcribe(
            str(audio_path),
            language=lang_arg,
            beam_size=5,
            vad_filter=True,
        )

        segments: list[Segment] = []
        full_text_parts: list[str] = []
        for seg in segments_iter:
            segments.append(Segment(start=seg.start, end=seg.end, text=seg.text))
            full_text_parts.append(seg.text.strip())

        return TranscriptionResult(
            segments=segments,
            language=info.language,
            language_probability=info.language_probability,
            text=" ".join(full_text_parts),
        )

    def transcribe_audio(
        self,
        audio: np.ndarray,
        language: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe audio from a numpy array.

        Args:
            audio: Audio data as float32 numpy array (16 kHz mono).
            language: Language code ('en', 'pt') or None for auto-detection.
        """
        if audio.size == 0:
            return TranscriptionResult(segments=[], language="", language_probability=0.0, text="")

        lang_arg = language if language and language != "auto" else None

        segments_iter, info = self.model.transcribe(
            audio,
            language=lang_arg,
            beam_size=5,
            vad_filter=True,
        )

        segments: list[Segment] = []
        full_text_parts: list[str] = []
        for seg in segments_iter:
            segments.append(Segment(start=seg.start, end=seg.end, text=seg.text))
            full_text_parts.append(seg.text.strip())

        return TranscriptionResult(
            segments=segments,
            language=info.language,
            language_probability=info.language_probability,
            text=" ".join(full_text_parts),
        )
