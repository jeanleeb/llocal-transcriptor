"""Tests for transcriptor.audio_capture."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from transcriptor.audio_capture import SAMPLE_RATE, AudioCapture, AudioDevice, list_audio_devices


def _make_mock_sd():
    """Create a mock sounddevice module."""
    return MagicMock()


class TestListAudioDevices:
    @patch("transcriptor.audio_capture._import_sd")
    def test_returns_only_input_devices(self, mock_import_sd):
        mock_sd = _make_mock_sd()
        mock_import_sd.return_value = mock_sd
        mock_sd.query_devices.return_value = [
            {"name": "Mic", "max_input_channels": 2, "default_samplerate": 44100.0},
            {"name": "Speakers", "max_input_channels": 0, "default_samplerate": 48000.0},
            {"name": "Line In", "max_input_channels": 1, "default_samplerate": 48000.0},
        ]
        devices = list_audio_devices()
        assert len(devices) == 2
        assert devices[0] == AudioDevice(
            index=0, name="Mic", max_input_channels=2, default_samplerate=44100.0
        )
        assert devices[1] == AudioDevice(
            index=2, name="Line In", max_input_channels=1, default_samplerate=48000.0
        )

    @patch("transcriptor.audio_capture._import_sd")
    def test_empty_when_no_inputs(self, mock_import_sd):
        mock_sd = _make_mock_sd()
        mock_import_sd.return_value = mock_sd
        mock_sd.query_devices.return_value = [
            {"name": "Speakers", "max_input_channels": 0, "default_samplerate": 44100.0},
        ]
        assert list_audio_devices() == []

    @patch("transcriptor.audio_capture._import_sd")
    def test_empty_device_list(self, mock_import_sd):
        mock_sd = _make_mock_sd()
        mock_import_sd.return_value = mock_sd
        mock_sd.query_devices.return_value = []
        assert list_audio_devices() == []


class TestAudioCapture:
    def test_read_returns_empty_when_no_audio(self):
        capture = AudioCapture()
        audio = capture.read()
        assert len(audio) == 0
        assert audio.dtype == np.float32

    def test_read_returns_buffered_audio(self):
        capture = AudioCapture()
        chunk1 = np.ones((100, 1), dtype=np.float32)
        chunk2 = np.full((50, 1), 0.5, dtype=np.float32)
        capture._buffer.put(chunk1)
        capture._buffer.put(chunk2)

        audio = capture.read()
        assert len(audio) == 150
        assert audio.dtype == np.float32
        np.testing.assert_array_equal(audio[:100], 1.0)
        np.testing.assert_array_equal(audio[100:], 0.5)

    def test_read_clears_buffer(self):
        capture = AudioCapture()
        capture._buffer.put(np.ones((100, 1), dtype=np.float32))
        capture.read()
        assert capture._buffer.empty()
        # Second read returns empty
        assert len(capture.read()) == 0

    def test_callback_puts_copy_in_buffer(self):
        capture = AudioCapture()
        data = np.ones((80, 1), dtype=np.float32)
        capture._callback(data, 80, None, None)
        assert not capture._buffer.empty()
        buffered = capture._buffer.get()
        np.testing.assert_array_equal(buffered, data)

    @patch("transcriptor.audio_capture._import_sd")
    def test_start_creates_stream_with_correct_params(self, mock_import_sd):
        mock_sd = _make_mock_sd()
        mock_import_sd.return_value = mock_sd

        capture = AudioCapture(device=5)
        capture.start()

        mock_sd.InputStream.assert_called_once()
        kwargs = mock_sd.InputStream.call_args[1]
        assert kwargs["samplerate"] == SAMPLE_RATE
        assert kwargs["channels"] == 1
        assert kwargs["dtype"] == "float32"
        assert kwargs["device"] == 5
        mock_sd.InputStream.return_value.start.assert_called_once()

    @patch("transcriptor.audio_capture._import_sd")
    def test_start_default_device(self, mock_import_sd):
        mock_sd = _make_mock_sd()
        mock_import_sd.return_value = mock_sd

        capture = AudioCapture()
        capture.start()
        kwargs = mock_sd.InputStream.call_args[1]
        assert kwargs["device"] is None

    @patch("transcriptor.audio_capture._import_sd")
    def test_stop_closes_stream(self, mock_import_sd):
        mock_sd = _make_mock_sd()
        mock_import_sd.return_value = mock_sd
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        capture = AudioCapture()
        capture.start()
        capture.stop()

        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()
        assert capture._stream is None

    def test_stop_noop_when_not_started(self):
        capture = AudioCapture()
        capture.stop()  # should not raise

    @patch("transcriptor.audio_capture._import_sd")
    def test_context_manager(self, mock_import_sd):
        mock_sd = _make_mock_sd()
        mock_import_sd.return_value = mock_sd
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        with AudioCapture() as capture:
            assert capture._stream is not None

        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()
