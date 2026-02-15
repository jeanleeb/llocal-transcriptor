"""WebSocket server for real-time audio transcription."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
from typing import Any

import numpy as np
import websockets
from websockets.asyncio.server import Server, ServerConnection

from transcriptor.config import WHISPER_MODELS
from transcriptor.transcriber import Transcriber

logger = logging.getLogger(__name__)

DEFAULT_PORT = 9867
SAMPLE_RATE = 16000
# Transcribe every N seconds of accumulated audio
CHUNK_DURATION_S = 3.0
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_S)


class TranscriptionSession:
    """Manages a single WebSocket transcription session."""

    def __init__(self, websocket: ServerConnection) -> None:
        self.websocket = websocket
        self.transcriber: Transcriber | None = None
        self.audio_buffer: list[np.ndarray] = []
        self.full_text_parts: list[str] = []
        self.running = False
        self._process_task: asyncio.Task[None] | None = None

    async def send_json(self, data: dict[str, Any]) -> None:
        await self.websocket.send(json.dumps(data))

    async def handle_start(self, config: dict[str, Any]) -> None:
        model_name = config.get("model", "base")
        if model_name not in WHISPER_MODELS:
            await self.send_json({
                "type": "error",
                "message": f"Unknown model '{model_name}'. Available: {', '.join(WHISPER_MODELS)}",
            })
            return

        language = config.get("language", "auto")

        try:
            self.transcriber = Transcriber(model_name=model_name)
            self.language = language
            self.audio_buffer = []
            self.full_text_parts = []
            self.running = True
            self._process_task = asyncio.create_task(self._process_loop())
            await self.send_json({"type": "status", "state": "ready"})
            logger.info("Session started: model=%s, language=%s", model_name, language)
        except Exception as e:
            await self.send_json({"type": "error", "message": str(e)})

    async def handle_audio(self, data_b64: str) -> None:
        if not self.running or self.transcriber is None:
            await self.send_json({
                "type": "error",
                "message": "Session not started. Send 'start' first.",
            })
            return

        try:
            raw = base64.b64decode(data_b64)
            audio_chunk = np.frombuffer(raw, dtype=np.float32)
            self.audio_buffer.append(audio_chunk)
        except Exception as e:
            await self.send_json({"type": "error", "message": f"Invalid audio data: {e}"})

    async def handle_stop(self) -> None:
        self.running = False
        if self._process_task is not None:
            self._process_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._process_task
            self._process_task = None

        # Transcribe remaining audio
        if self.transcriber is not None and self.audio_buffer:
            await self._transcribe_buffer()

        await self.send_json({"type": "status", "state": "stopped"})
        logger.info("Session stopped")

    async def _process_loop(self) -> None:
        """Periodically transcribe accumulated audio."""
        while self.running:
            await asyncio.sleep(CHUNK_DURATION_S)
            if self.audio_buffer:
                await self._transcribe_buffer()

    async def _transcribe_buffer(self) -> None:
        if not self.audio_buffer or self.transcriber is None:
            return

        audio = np.concatenate(self.audio_buffer)
        self.audio_buffer.clear()

        if len(audio) < SAMPLE_RATE * 0.1:
            return

        await self.send_json({"type": "status", "state": "transcribing"})

        try:
            lang_arg = self.language if self.language != "auto" else None
            segments_iter, info = self.transcriber.model.transcribe(
                audio,
                language=lang_arg,
                beam_size=5,
                vad_filter=True,
            )

            segments_data = []
            text_parts = []
            for seg in segments_iter:
                segments_data.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                })
                text_parts.append(seg.text.strip())

            chunk_text = " ".join(text_parts)
            if chunk_text:
                self.full_text_parts.append(chunk_text)

            await self.send_json({
                "type": "transcript",
                "text": chunk_text,
                "segments": segments_data,
                "is_partial": False,
            })
            await self.send_json({"type": "status", "state": "ready"})
        except Exception as e:
            logger.exception("Transcription error")
            await self.send_json({"type": "error", "message": f"Transcription error: {e}"})


async def handle_connection(websocket: ServerConnection) -> None:
    """Handle a single WebSocket connection."""
    session = TranscriptionSession(websocket)
    logger.info("Client connected: %s", websocket.remote_address)

    try:
        async for raw_message in websocket:
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await session.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })
                continue

            msg_type = message.get("type")

            if msg_type == "start":
                await session.handle_start(message.get("config", {}))
            elif msg_type == "audio":
                await session.handle_audio(message.get("data", ""))
            elif msg_type == "stop":
                await session.handle_stop()
            else:
                await session.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    finally:
        if session.running:
            session.running = False
            if session._process_task is not None:
                session._process_task.cancel()


async def start_server(host: str = "localhost", port: int = DEFAULT_PORT) -> Server:
    """Start the WebSocket server."""
    server = await websockets.serve(handle_connection, host, port)
    logger.info("WebSocket server listening on ws://%s:%d", host, port)
    return server


def run_server(host: str = "localhost", port: int = DEFAULT_PORT) -> None:
    """Run the WebSocket server (blocking)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    async def _run() -> None:
        server = await start_server(host, port)
        await server.serve_forever()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Server stopped")
