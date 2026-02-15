/**
 * LLocal Transcriptor — Offscreen Document
 *
 * Captures tab audio via MediaStream, processes it through an AudioWorklet
 * to extract PCM float32 at 16kHz, and sends chunks over WebSocket to the
 * Python transcription server.
 */

let mediaStream = null;
let audioContext = null;
let websocket = null;
let isCapturing = false;

// --- Base64 encoding for Float32Array ---

function float32ToBase64(float32Array) {
  const bytes = new Uint8Array(float32Array.buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

// --- WebSocket management ---

function connectWebSocket(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      resolve(ws);
    };

    ws.onerror = (err) => {
      reject(new Error("WebSocket connection failed"));
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        // Forward to background service worker
        chrome.runtime.sendMessage({
          source: "offscreen",
          type: message.type,
          text: message.text,
          state: message.state,
          message: message.message,
          segments: message.segments,
          is_partial: message.is_partial,
        });
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onclose = () => {
      if (isCapturing) {
        chrome.runtime.sendMessage({
          source: "offscreen",
          type: "status",
          state: "stopped",
        });
        cleanup();
      }
    };
  });
}

// --- Audio capture ---

async function startCapture(streamId, wsUrl, model, language) {
  try {
    // Get the media stream from the tab
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        mandatory: {
          chromeMediaSource: "tab",
          chromeMediaSourceId: streamId,
        },
      },
    });

    // Connect to WebSocket server
    websocket = await connectWebSocket(wsUrl);

    // Send start message
    websocket.send(JSON.stringify({
      type: "start",
      config: { model, language },
    }));

    // Set up AudioContext with AudioWorklet
    audioContext = new AudioContext({ sampleRate: 16000 });

    await audioContext.audioWorklet.addModule("audio-processor.js");

    const source = audioContext.createMediaStreamSource(mediaStream);
    const workletNode = new AudioWorkletNode(audioContext, "audio-processor");

    workletNode.port.onmessage = (event) => {
      if (!isCapturing || !websocket || websocket.readyState !== WebSocket.OPEN) {
        return;
      }

      const audioData = new Float32Array(event.data);
      const base64Data = float32ToBase64(audioData);

      websocket.send(JSON.stringify({
        type: "audio",
        data: base64Data,
      }));
    };

    source.connect(workletNode);
    workletNode.connect(audioContext.destination);

    isCapturing = true;
  } catch (err) {
    console.error("Capture error:", err);
    chrome.runtime.sendMessage({
      source: "offscreen",
      type: "error",
      message: err.message,
    });
    cleanup();
  }
}

function stopCapture() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({ type: "stop" }));
  }
  // Allow the stop message to be sent before cleanup
  setTimeout(cleanup, 300);
}

function cleanup() {
  isCapturing = false;

  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }

  if (audioContext) {
    audioContext.close().catch(() => {});
    audioContext = null;
  }

  if (websocket) {
    if (websocket.readyState === WebSocket.OPEN) {
      websocket.close();
    }
    websocket = null;
  }
}

// --- Listen for messages from background ---

chrome.runtime.onMessage.addListener((message) => {
  if (message.target !== "offscreen") return;

  if (message.action === "startCapture") {
    startCapture(message.streamId, message.wsUrl, message.model, message.language);
  } else if (message.action === "stopCapture") {
    stopCapture();
  }
});
