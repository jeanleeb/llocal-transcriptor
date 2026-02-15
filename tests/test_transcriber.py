"""Tests for transcriptor.transcriber."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from transcriptor.transcriber import (
    Segment,
    Transcriber,
    TranscriptionResult,
    _format_time_srt,
)


class TestFormatTimeSrt:
    def test_zero(self):
        assert _format_time_srt(0.0) == "00:00:00,000"

    def test_simple_seconds(self):
        assert _format_time_srt(5.0) == "00:00:05,000"

    def test_milliseconds(self):
        assert _format_time_srt(1.5) == "00:00:01,500"

    def test_minutes(self):
        assert _format_time_srt(65.0) == "00:01:05,000"

    def test_hours(self):
        assert _format_time_srt(3661.123) == "01:01:01,123"

    def test_large_value(self):
        assert _format_time_srt(7200.0) == "02:00:00,000"


def _make_result(segments: list[Segment] | None = None) -> TranscriptionResult:
    if segments is None:
        segments = [
            Segment(start=0.0, end=2.5, text=" Hello world "),
            Segment(start=2.5, end=5.0, text=" Second segment "),
        ]
    return TranscriptionResult(
        segments=segments,
        language="en",
        language_probability=0.95,
        text=" ".join(s.text.strip() for s in segments),
    )


class TestTranscriptionResult:
    def test_to_txt(self):
        result = _make_result()
        assert result.to_txt() == "Hello world Second segment"

    def test_to_srt(self):
        result = _make_result()
        srt = result.to_srt()
        lines = srt.split("\n")
        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:02,500"
        assert lines[2] == "Hello world"
        assert lines[3] == ""
        assert lines[4] == "2"
        assert lines[5] == "00:00:02,500 --> 00:00:05,000"
        assert lines[6] == "Second segment"

    def test_to_json(self):
        import json

        result = _make_result()
        data = json.loads(result.to_json())
        assert data["language"] == "en"
        assert data["language_probability"] == 0.95
        assert data["text"] == "Hello world Second segment"
        assert len(data["segments"]) == 2
        assert data["segments"][0]["start"] == 0.0
        assert data["segments"][0]["text"] == "Hello world"

    def test_to_srt_empty(self):
        result = _make_result(segments=[])
        assert result.to_srt() == ""

    def test_to_json_unicode(self):
        import json

        segments = [Segment(start=0.0, end=1.0, text=" Olá mundo ção ")]
        result = _make_result(segments)
        data = json.loads(result.to_json())
        assert data["segments"][0]["text"] == "Olá mundo ção"


class TestTranscriber:
    def test_invalid_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            Transcriber(model_name="nonexistent")

    @patch("transcriptor.transcriber.WhisperModel")
    def test_init_cpu(self, mock_whisper_model):
        t = Transcriber(model_name="base", device="cpu")
        assert t.device == "cpu"
        mock_whisper_model.assert_called_once_with("base", device="cpu", compute_type="int8")

    @patch("transcriptor.transcriber.WhisperModel")
    def test_init_cuda(self, mock_whisper_model):
        t = Transcriber(model_name="small", device="cuda")
        assert t.device == "cuda"
        mock_whisper_model.assert_called_once_with("small", device="cuda", compute_type="float16")

    @patch("transcriptor.transcriber.WhisperModel")
    def test_transcribe_file_not_found(self, mock_whisper_model):
        t = Transcriber(model_name="base", device="cpu")
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            t.transcribe("/nonexistent/audio.mp3")

    @patch("transcriptor.transcriber.WhisperModel")
    def test_transcribe_success(self, mock_whisper_model, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")

        mock_seg1 = MagicMock()
        mock_seg1.start = 0.0
        mock_seg1.end = 2.0
        mock_seg1.text = " Hello "

        mock_seg2 = MagicMock()
        mock_seg2.start = 2.0
        mock_seg2.end = 4.0
        mock_seg2.text = " World "

        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.98

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([mock_seg1, mock_seg2]), mock_info)
        mock_whisper_model.return_value = mock_model

        t = Transcriber(model_name="base", device="cpu")
        result = t.transcribe(audio_file)

        assert result.language == "en"
        assert result.language_probability == 0.98
        assert result.text == "Hello World"
        assert len(result.segments) == 2

    @patch("transcriptor.transcriber.WhisperModel")
    def test_transcribe_with_language(self, mock_whisper_model, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake")

        mock_info = MagicMock()
        mock_info.language = "pt"
        mock_info.language_probability = 0.99

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([]), mock_info)
        mock_whisper_model.return_value = mock_model

        t = Transcriber(model_name="base", device="cpu")
        t.transcribe(audio_file, language="pt")

        mock_model.transcribe.assert_called_once_with(
            str(audio_file), language="pt", beam_size=5, vad_filter=True
        )

    @patch("transcriptor.transcriber.WhisperModel")
    def test_transcribe_auto_language(self, mock_whisper_model, tmp_path):
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake")

        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.90

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([]), mock_info)
        mock_whisper_model.return_value = mock_model

        t = Transcriber(model_name="base", device="cpu")
        t.transcribe(audio_file, language="auto")

        mock_model.transcribe.assert_called_once_with(
            str(audio_file), language=None, beam_size=5, vad_filter=True
        )
