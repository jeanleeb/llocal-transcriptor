"""Tests for transcriptor.ws_server."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from transcriptor.ws_server import (
    DEFAULT_PORT,
    SAMPLE_RATE,
    TranscriptionSession,
    handle_connection,
)


class TestTranscriptionSession:
    def _make_session(self):
        ws = AsyncMock()
        ws.remote_address = ("127.0.0.1", 12345)
        return TranscriptionSession(ws)

    @pytest.mark.asyncio
    async def test_send_json(self):
        session = self._make_session()
        await session.send_json({"type": "status", "state": "ready"})
        session.websocket.send.assert_called_once_with(
            json.dumps({"type": "status", "state": "ready"})
        )

    @pytest.mark.asyncio
    @patch("transcriptor.ws_server.Transcriber")
    async def test_handle_start_valid_model(self, mock_transcriber_cls):
        session = self._make_session()
        await session.handle_start({"model": "base", "language": "auto"})

        assert session.running is True
        assert session.language == "auto"
        mock_transcriber_cls.assert_called_once_with(model_name="base")

        # Should have sent "ready" status
        sent = json.loads(session.websocket.send.call_args[0][0])
        assert sent["type"] == "status"
        assert sent["state"] == "ready"

        # Clean up the process task
        session.running = False
        if session._process_task:
            session._process_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await session._process_task

    @pytest.mark.asyncio
    async def test_handle_start_invalid_model(self):
        session = self._make_session()
        await session.handle_start({"model": "nonexistent"})

        assert session.running is False
        sent = json.loads(session.websocket.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "nonexistent" in sent["message"]

    @pytest.mark.asyncio
    async def test_handle_audio_without_start(self):
        session = self._make_session()
        await session.handle_audio("dGVzdA==")

        sent = json.loads(session.websocket.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "not started" in sent["message"].lower()

    @pytest.mark.asyncio
    @patch("transcriptor.ws_server.Transcriber")
    async def test_handle_audio_valid(self, mock_transcriber_cls):
        session = self._make_session()
        session.running = True
        session.transcriber = MagicMock()

        # Create valid PCM float32 data
        audio = np.zeros(160, dtype=np.float32)
        b64 = base64.b64encode(audio.tobytes()).decode()

        await session.handle_audio(b64)
        assert len(session.audio_buffer) == 1
        np.testing.assert_array_equal(session.audio_buffer[0], audio)

    @pytest.mark.asyncio
    async def test_handle_audio_invalid_base64(self):
        session = self._make_session()
        session.running = True
        session.transcriber = MagicMock()

        await session.handle_audio("not-valid-base64!!!")

        sent = json.loads(session.websocket.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "invalid" in sent["message"].lower()

    @pytest.mark.asyncio
    @patch("transcriptor.ws_server.Transcriber")
    async def test_handle_stop(self, mock_transcriber_cls):
        session = self._make_session()
        session.running = True
        session.transcriber = MagicMock()
        session.audio_buffer = []

        await session.handle_stop()

        assert session.running is False
        sent = json.loads(session.websocket.send.call_args[0][0])
        assert sent["type"] == "status"
        assert sent["state"] == "stopped"

    @pytest.mark.asyncio
    @patch("transcriptor.ws_server.Transcriber")
    async def test_transcribe_buffer(self, mock_transcriber_cls):
        session = self._make_session()
        session.running = True

        # Set up mock transcriber
        mock_seg = MagicMock()
        mock_seg.start = 0.0
        mock_seg.end = 1.0
        mock_seg.text = " Hello world "

        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.95

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([mock_seg]), mock_info)

        session.transcriber = MagicMock()
        session.transcriber.model = mock_model
        session.language = "auto"

        # Add audio to buffer
        audio = np.random.randn(SAMPLE_RATE).astype(np.float32)
        session.audio_buffer = [audio]

        await session._transcribe_buffer()

        # Should have sent transcribing status, transcript, and ready status
        assert session.websocket.send.call_count == 3
        calls = [json.loads(c[0][0]) for c in session.websocket.send.call_args_list]

        assert calls[0]["type"] == "status"
        assert calls[0]["state"] == "transcribing"
        assert calls[1]["type"] == "transcript"
        assert calls[1]["text"] == "Hello world"
        assert calls[1]["segments"][0]["text"] == "Hello world"
        assert calls[2]["type"] == "status"
        assert calls[2]["state"] == "ready"

    @pytest.mark.asyncio
    @patch("transcriptor.ws_server.Transcriber")
    async def test_transcribe_buffer_empty(self, mock_transcriber_cls):
        session = self._make_session()
        session.transcriber = MagicMock()
        session.audio_buffer = []

        await session._transcribe_buffer()
        session.websocket.send.assert_not_called()

    @pytest.mark.asyncio
    @patch("transcriptor.ws_server.Transcriber")
    async def test_transcribe_buffer_too_short(self, mock_transcriber_cls):
        session = self._make_session()
        session.transcriber = MagicMock()
        # Less than 0.1s of audio
        audio = np.zeros(100, dtype=np.float32)
        session.audio_buffer = [audio]

        await session._transcribe_buffer()
        # Should not transcribe, only clear buffer
        session.transcriber.model.transcribe.assert_not_called()


class TestHandleConnection:
    @pytest.mark.asyncio
    async def test_invalid_json(self):
        ws = AsyncMock()
        ws.remote_address = ("127.0.0.1", 12345)
        ws.__aiter__ = lambda self: self
        ws.__anext__ = AsyncMock(side_effect=StopAsyncIteration)

        # Simulate receiving invalid JSON
        messages = ["not json"]

        async def message_iter(self):
            for msg in messages:
                yield msg

        ws.__aiter__ = lambda self: message_iter(self)

        await handle_connection(ws)

        sent = json.loads(ws.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "invalid json" in sent["message"].lower()

    @pytest.mark.asyncio
    async def test_unknown_message_type(self):
        messages = [json.dumps({"type": "unknown_type"})]

        ws = AsyncMock()
        ws.remote_address = ("127.0.0.1", 12345)

        async def message_iter(self):
            for msg in messages:
                yield msg

        ws.__aiter__ = lambda self: message_iter(self)

        await handle_connection(ws)

        sent = json.loads(ws.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "unknown_type" in sent["message"].lower()


class TestServerConfig:
    def test_default_port(self):
        assert DEFAULT_PORT == 9867

    def test_sample_rate(self):
        assert SAMPLE_RATE == 16000
