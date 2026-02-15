"""Audio capture from microphone or system audio using sounddevice."""

from __future__ import annotations

import queue
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    import sounddevice as sd

SAMPLE_RATE = 16_000  # Whisper expects 16 kHz mono float32
CHANNELS = 1
BLOCK_DURATION = 0.5  # seconds per callback block


def _import_sd() -> Any:
    """Lazy-import sounddevice so the module can be loaded without PortAudio."""
    import sounddevice as _sd  # noqa: N812

    return _sd


@dataclass
class AudioDevice:
    """Represents an available audio input device."""

    index: int
    name: str
    max_input_channels: int
    default_samplerate: float


def list_audio_devices() -> list[AudioDevice]:
    """List available audio input devices."""
    sd = _import_sd()
    devices = sd.query_devices()
    result: list[AudioDevice] = []
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            result.append(
                AudioDevice(
                    index=i,
                    name=dev["name"],
                    max_input_channels=dev["max_input_channels"],
                    default_samplerate=dev["default_samplerate"],
                )
            )
    return result


class AudioCapture:
    """Captures audio from an input device in real time.

    Audio is stored in an internal queue and can be retrieved with ``read()``.
    Designed to be used as a context manager::

        with AudioCapture() as capture:
            ...
            audio = capture.read()
    """

    def __init__(self, device: int | None = None) -> None:
        self._device = device
        self._buffer: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: sd.InputStream | None = None

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,  # noqa: ARG002
        time_info: object,  # noqa: ARG002
        status: object,  # noqa: ARG002
    ) -> None:
        """Called by sounddevice for each audio block."""
        self._buffer.put(indata.copy())

    def start(self) -> None:
        """Open the audio stream and start recording."""
        sd = _import_sd()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            device=self._device,
            callback=self._callback,
            blocksize=int(SAMPLE_RATE * BLOCK_DURATION),
        )
        self._stream.start()

    def stop(self) -> None:
        """Stop recording and close the audio stream."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def read(self) -> np.ndarray:
        """Read all buffered audio as a flat float32 array.

        Returns an empty array when no audio is available.
        """
        chunks: list[np.ndarray] = []
        while True:
            try:
                chunks.append(self._buffer.get_nowait())
            except queue.Empty:
                break
        if not chunks:
            return np.array([], dtype=np.float32)
        return np.concatenate(chunks, axis=0).flatten()

    def __enter__(self) -> AudioCapture:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()
