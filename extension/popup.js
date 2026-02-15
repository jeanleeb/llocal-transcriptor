/**
 * LLocal Transcriptor — Popup UI
 *
 * Communicates with background.js via chrome.runtime messages.
 */

const toggleBtn = document.getElementById("toggle-btn");
const copyBtn = document.getElementById("copy-btn");
const clearBtn = document.getElementById("clear-btn");
const transcriptText = document.getElementById("transcript-text");
const statusIndicator = document.getElementById("status-indicator");
const modelSelect = document.getElementById("model-select");
const languageSelect = document.getElementById("language-select");

let isRecording = false;
let fullTranscript = "";

// --- Status management ---

function setStatus(state, label) {
  statusIndicator.className = "status " + state;
  statusIndicator.textContent = label;
}

function updateUI() {
  if (isRecording) {
    toggleBtn.textContent = "Parar Transcrição";
    toggleBtn.className = "btn btn-stop";
    modelSelect.disabled = true;
    languageSelect.disabled = true;
  } else {
    toggleBtn.textContent = "Iniciar Transcrição";
    toggleBtn.className = "btn btn-start";
    modelSelect.disabled = false;
    languageSelect.disabled = false;
  }

  const hasText = fullTranscript.trim().length > 0;
  copyBtn.disabled = !hasText;
  clearBtn.disabled = !hasText;
}

// --- Transcript rendering ---

function appendTranscript(text) {
  if (!text || !text.trim()) return;

  if (fullTranscript === "") {
    transcriptText.innerHTML = "";
  }

  fullTranscript += (fullTranscript ? " " : "") + text.trim();
  transcriptText.textContent = fullTranscript;
  transcriptText.scrollTop = transcriptText.scrollHeight;
  updateUI();
}

function clearTranscript() {
  fullTranscript = "";
  transcriptText.innerHTML = '<p class="placeholder">A transcrição aparecerá aqui...</p>';
  updateUI();
}

// --- Communication with background ---

function sendMessage(action, data) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ action, ...data }, (response) => {
      resolve(response);
    });
  });
}

// --- Event handlers ---

toggleBtn.addEventListener("click", async () => {
  if (isRecording) {
    // Stop
    const response = await sendMessage("stop");
    if (response && response.success) {
      isRecording = false;
      setStatus("disconnected", "Desconectado");
      updateUI();
    }
  } else {
    // Start
    const model = modelSelect.value;
    const language = languageSelect.value;

    setStatus("connected", "Conectando...");
    const response = await sendMessage("start", { model, language });

    if (response && response.success) {
      isRecording = true;
      setStatus("connected", "Conectado");
      updateUI();
    } else {
      const errorMsg = (response && response.error) || "Failed to connect";
      setStatus("disconnected", "Erro");
      console.error("Start failed:", errorMsg);
    }
  }
});

copyBtn.addEventListener("click", () => {
  if (fullTranscript) {
    navigator.clipboard.writeText(fullTranscript).then(() => {
      const original = copyBtn.textContent;
      copyBtn.textContent = "Copiado!";
      setTimeout(() => {
        copyBtn.textContent = original;
      }, 1500);
    });
  }
});

clearBtn.addEventListener("click", () => {
  clearTranscript();
});

// --- Listen for messages from background ---

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "transcript") {
    appendTranscript(message.text);
    setStatus("connected", "Conectado");
  } else if (message.type === "status") {
    if (message.state === "transcribing") {
      setStatus("transcribing", "Transcrevendo...");
    } else if (message.state === "ready") {
      setStatus("connected", "Conectado");
    } else if (message.state === "stopped") {
      isRecording = false;
      setStatus("disconnected", "Desconectado");
      updateUI();
    }
  } else if (message.type === "error") {
    console.error("Server error:", message.message);
    setStatus("disconnected", "Erro");
  }
});

// --- On popup open, check current state ---

(async () => {
  const response = await sendMessage("getState");
  if (response) {
    isRecording = response.isRecording || false;
    if (response.transcript) {
      fullTranscript = response.transcript;
      transcriptText.textContent = fullTranscript;
    }
    if (isRecording) {
      setStatus("connected", "Conectado");
    }
    if (response.model) {
      modelSelect.value = response.model;
    }
    if (response.language) {
      languageSelect.value = response.language;
    }
    updateUI();
  }
})();
