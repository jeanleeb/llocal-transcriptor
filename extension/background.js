/**
 * LLocal Transcriptor — Background Service Worker
 *
 * Manages:
 * - Offscreen document lifecycle
 * - Tab audio capture (chrome.tabCapture)
 * - Message relay between popup ↔ offscreen
 */

const WS_URL = "ws://localhost:9867";

let isRecording = false;
let currentModel = "base";
let currentLanguage = "auto";
let fullTranscript = "";

// --- Offscreen document management ---

async function hasOffscreenDocument() {
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ["OFFSCREEN_DOCUMENT"],
  });
  return contexts.length > 0;
}

async function createOffscreenDocument() {
  if (await hasOffscreenDocument()) {
    return;
  }
  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["USER_MEDIA"],
    justification: "Capture tab audio for real-time transcription",
  });
}

async function removeOffscreenDocument() {
  if (await hasOffscreenDocument()) {
    await chrome.offscreen.closeDocument();
  }
}

// --- Tab capture ---

async function startCapture(model, language) {
  currentModel = model;
  currentLanguage = language;

  // Get the active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) {
    throw new Error("No active tab found");
  }

  // Get a media stream ID for the tab
  const streamId = await chrome.tabCapture.getMediaStreamId({
    targetTabId: tab.id,
  });

  // Create offscreen document
  await createOffscreenDocument();

  // Tell offscreen to start capturing
  chrome.runtime.sendMessage({
    target: "offscreen",
    action: "startCapture",
    streamId,
    wsUrl: WS_URL,
    model,
    language,
  });

  isRecording = true;
}

async function stopCapture() {
  // Tell offscreen to stop
  chrome.runtime.sendMessage({
    target: "offscreen",
    action: "stopCapture",
  });

  isRecording = false;

  // Give offscreen time to clean up before removing
  setTimeout(async () => {
    await removeOffscreenDocument();
  }, 500);
}

// --- Message handling ---

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Messages from popup
  if (message.action === "start") {
    startCapture(message.model, message.language)
      .then(() => sendResponse({ success: true }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true; // async response
  }

  if (message.action === "stop") {
    stopCapture()
      .then(() => sendResponse({ success: true }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.action === "getState") {
    sendResponse({
      isRecording,
      transcript: fullTranscript,
      model: currentModel,
      language: currentLanguage,
    });
    return false;
  }

  // Messages from offscreen (transcription results)
  if (message.source === "offscreen") {
    if (message.type === "transcript") {
      if (message.text && message.text.trim()) {
        fullTranscript += (fullTranscript ? " " : "") + message.text.trim();
      }
    }
    // Forward to popup
    chrome.runtime.sendMessage({
      type: message.type,
      text: message.text,
      state: message.state,
      message: message.message,
      segments: message.segments,
      is_partial: message.is_partial,
    });
    return false;
  }

  return false;
});
