"""Tests for transcriptor.live_transcriber."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np

from transcriptor.audio_capture import SAMPLE_RATE
from transcriptor.live_transcriber import LiveSession, LiveTranscriber
from transcriptor.transcriber import Segment, TranscriptionResult


class TestLiveSession:
    def test_empty_session(self):
        session = LiveSession()
        assert session.segments == []
        assert session.text == ""

    def test_text_joins_segments(self):
        session = LiveSession(
            segments=[
                Segment(start=0.0, end=1.0, text=" Hello "),
                Segment(start=1.0, end=2.0, text=" world "),
            ]
        )
        assert session.text == "Hello world"

    def test_text_skips_empty_segments(self):
        session = LiveSession(
            segments=[
                Segment(start=0.0, end=1.0, text=" Hello "),
                Segment(start=1.0, end=2.0, text="   "),
                Segment(start=2.0, end=3.0, text=" world "),
            ]
        )
        assert session.text == "Hello world"


class TestLiveTranscriber:
    @patch("transcriptor.live_transcriber.AudioCapture")
    @patch("transcriptor.transcriber.WhisperModel")
    def test_process_chunk_adjusts_timestamps(self, mock_whisper_cls, mock_capture_cls):
        lt = LiveTranscriber(model_name="base", device="cpu", chunk_interval=1.0)
        lt._time_offset = 10.0

        # Simulate a transcription result for a chunk
        mock_result = TranscriptionResult(
            segments=[
                Segment(start=0.0, end=1.0, text=" Hello "),
                Segment(start=1.0, end=2.0, text=" World "),
            ],
            language="en",
            language_probability=0.95,
            text="Hello World",
        )
        lt.transcriber.transcribe_audio = MagicMock(return_value=mock_result)

        # 2 seconds of audio at 16kHz
        audio_chunk = np.zeros(SAMPLE_RATE * 2, dtype=np.float32)
        new_segments = lt._process_chunk(audio_chunk)

        assert len(new_segments) == 2
        assert new_segments[0].start == 10.0
        assert new_segments[0].end == 11.0
        assert new_segments[1].start == 11.0
        assert new_segments[1].end == 12.0

        # Time offset should advance by chunk duration (2s)
        assert lt._time_offset == 12.0

    @patch("transcriptor.live_transcriber.AudioCapture")
    @patch("transcriptor.transcriber.WhisperModel")
    def test_process_chunk_accumulates_segments(self, mock_whisper_cls, mock_capture_cls):
        lt = LiveTranscriber(model_name="base", device="cpu")

        result1 = TranscriptionResult(
            segments=[Segment(start=0.0, end=1.0, text=" A ")],
            language="en",
            language_probability=0.9,
            text="A",
        )
        result2 = TranscriptionResult(
            segments=[Segment(start=0.0, end=1.0, text=" B ")],
            language="en",
            language_probability=0.9,
            text="B",
        )
        lt.transcriber.transcribe_audio = MagicMock(side_effect=[result1, result2])

        chunk = np.zeros(SAMPLE_RATE, dtype=np.float32)  # 1 second
        lt._process_chunk(chunk)
        lt._process_chunk(chunk)

        assert len(lt.session.segments) == 2
        assert lt.session.text == "A B"

    @patch("transcriptor.live_transcriber.AudioCapture")
    @patch("transcriptor.transcriber.WhisperModel")
    def test_process_chunk_updates_language(self, mock_whisper_cls, mock_capture_cls):
        lt = LiveTranscriber(model_name="base", device="cpu")

        result = TranscriptionResult(
            segments=[Segment(start=0.0, end=1.0, text=" Olá ")],
            language="pt",
            language_probability=0.97,
            text="Olá",
        )
        lt.transcriber.transcribe_audio = MagicMock(return_value=result)

        chunk = np.zeros(SAMPLE_RATE, dtype=np.float32)
        lt._process_chunk(chunk)

        assert lt.session.language == "pt"
        assert lt.session.language_probability == 0.97

    @patch("transcriptor.live_transcriber.AudioCapture")
    @patch("transcriptor.transcriber.WhisperModel")
    def test_run_stops_on_keyboard_interrupt(self, mock_whisper_cls, mock_capture_cls):
        mock_capture = MagicMock()
        mock_capture_cls.return_value = mock_capture
        mock_capture.read.return_value = np.array([], dtype=np.float32)

        lt = LiveTranscriber(model_name="base", device="cpu", chunk_interval=0.1)

        # Stop after a short time
        def stop_soon():
            time.sleep(0.3)
            lt.stop()

        t = threading.Thread(target=stop_soon)
        t.start()

        session = lt.run()
        t.join()

        mock_capture.start.assert_called_once()
        mock_capture.stop.assert_called_once()
        assert session.segments == []

    @patch("transcriptor.live_transcriber.AudioCapture")
    @patch("transcriptor.transcriber.WhisperModel")
    def test_run_calls_on_update(self, mock_whisper_cls, mock_capture_cls):
        mock_capture = MagicMock()
        mock_capture_cls.return_value = mock_capture

        # First read returns audio, second returns empty
        audio_chunk = np.zeros(SAMPLE_RATE * 2, dtype=np.float32)
        mock_capture.read.side_effect = [audio_chunk, np.array([], dtype=np.float32)]

        lt = LiveTranscriber(model_name="base", device="cpu", chunk_interval=0.05)

        result = TranscriptionResult(
            segments=[Segment(start=0.0, end=1.0, text=" test ")],
            language="en",
            language_probability=0.9,
            text="test",
        )
        lt.transcriber.transcribe_audio = MagicMock(return_value=result)

        callback = MagicMock()

        def stop_after_callback(*args):
            callback(*args)
            lt.stop()

        t = threading.Thread(target=lambda: time.sleep(0.2) or lt.stop())
        t.start()

        lt.run(on_update=stop_after_callback)
        t.join()

        if callback.called:
            call_args = callback.call_args
            segments, full_text = call_args[0]
            assert len(segments) == 1
            assert segments[0].text == " test "

    @patch("transcriptor.live_transcriber.AudioCapture")
    @patch("transcriptor.transcriber.WhisperModel")
    def test_skips_short_chunks(self, mock_whisper_cls, mock_capture_cls):
        mock_capture = MagicMock()
        mock_capture_cls.return_value = mock_capture

        # Return very short audio (< 0.5s)
        short_audio = np.zeros(int(SAMPLE_RATE * 0.1), dtype=np.float32)
        mock_capture.read.return_value = short_audio

        lt = LiveTranscriber(model_name="base", device="cpu", chunk_interval=0.05)
        lt.transcriber.transcribe_audio = MagicMock()

        def stop_soon():
            time.sleep(0.2)
            lt.stop()

        t = threading.Thread(target=stop_soon)
        t.start()
        lt.run()
        t.join()

        # transcribe_audio should not have been called for short chunks
        lt.transcriber.transcribe_audio.assert_not_called()
