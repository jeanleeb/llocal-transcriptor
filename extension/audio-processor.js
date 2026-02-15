/**
 * LLocal Transcriptor — AudioWorklet Processor
 *
 * Extracts PCM float32 audio data from the MediaStream and sends it
 * to the main thread via port.postMessage().
 *
 * The AudioContext is configured with sampleRate=16000, so the audio
 * arrives already at 16kHz (required by Whisper).
 */

class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._bufferSize = 4096;
    this._buffer = new Float32Array(this._bufferSize);
    this._bytesWritten = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) {
      return true;
    }

    const channelData = input[0]; // mono channel

    for (let i = 0; i < channelData.length; i++) {
      this._buffer[this._bytesWritten++] = channelData[i];

      if (this._bytesWritten >= this._bufferSize) {
        // Send accumulated buffer
        this.port.postMessage(this._buffer.buffer.slice(0));
        this._bytesWritten = 0;
      }
    }

    return true;
  }
}

registerProcessor("audio-processor", AudioProcessor);
