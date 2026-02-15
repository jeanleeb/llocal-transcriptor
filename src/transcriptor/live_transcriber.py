"""Real-time transcription engine combining audio capture and faster-whisper."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from transcriptor.audio_capture import SAMPLE_RATE, AudioCapture
from transcriptor.transcriber import Segment, Transcriber

# Minimum audio length (in seconds) worth transcribing.
MIN_CHUNK_SECONDS = 0.5


class TranscriptionCallback(Protocol):
    """Called after each chunk is transcribed."""

    def __call__(self, segments: list[Segment], full_text: str) -> None: ...


@dataclass
class LiveSession:
    """Holds accumulated state of a live transcription session."""

    segments: list[Segment] = field(default_factory=list)
    language: str = ""
    language_probability: float = 0.0

    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments if s.text.strip())


class LiveTranscriber:
    """Orchestrates real-time transcription from audio input.

    Captures audio from the microphone (or a specified device), feeds chunks
    to the Whisper model at regular intervals, and notifies callers via a
    callback as new segments are produced.
    """

    def __init__(
        self,
        model_name: str = "base",
        language: str | None = None,
        device: str | None = None,
        audio_device: int | None = None,
        chunk_interval: float = 3.0,
    ) -> None:
        self.transcriber = Transcriber(model_name=model_name, device=device)
        self._language = language if language and language != "auto" else None
        self._audio_device = audio_device
        self._chunk_interval = chunk_interval
        self._session = LiveSession()
        self._time_offset = 0.0
        self._running = False

    @property
    def session(self) -> LiveSession:
        return self._session

    def run(self, on_update: TranscriptionCallback | None = None) -> LiveSession:
        """Start live transcription.  Blocks until ``stop()`` is called or Ctrl+C.

        Args:
            on_update: Callback invoked with (new_segments, full_text) after each chunk.

        Returns:
            The completed :class:`LiveSession` with all transcribed segments.
        """
        capture = AudioCapture(device=self._audio_device)
        self._running = True

        try:
            capture.start()
            while self._running:
                time.sleep(self._chunk_interval)
                audio_chunk = capture.read()

                chunk_duration = len(audio_chunk) / SAMPLE_RATE
                if chunk_duration < MIN_CHUNK_SECONDS:
                    self._time_offset += chunk_duration
                    continue

                new_segments = self._process_chunk(audio_chunk)

                if new_segments and on_update:
                    on_update(new_segments, self._session.text)
        except KeyboardInterrupt:
            pass
        finally:
            capture.stop()
            self._running = False

        return self._session

    def stop(self) -> None:
        """Signal the transcription loop to stop."""
        self._running = False

    def _process_chunk(self, audio_chunk: np.ndarray) -> list[Segment]:
        """Transcribe one chunk and return segments with adjusted timestamps."""
        result = self.transcriber.transcribe_audio(audio_chunk, language=self._language)

        adjusted: list[Segment] = []
        for seg in result.segments:
            adjusted.append(
                Segment(
                    start=seg.start + self._time_offset,
                    end=seg.end + self._time_offset,
                    text=seg.text,
                )
            )

        chunk_duration = len(audio_chunk) / SAMPLE_RATE
        self._time_offset += chunk_duration

        self._session.segments.extend(adjusted)
        if result.language:
            self._session.language = result.language
            self._session.language_probability = result.language_probability

        return adjusted
