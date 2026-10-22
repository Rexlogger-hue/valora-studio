/**
 * ====================================================================
 * VALORA AI STUDIO — FRONTEND APPLICATION LOGIC
 * Audio Engine, Real Waveform Visualizer, API Integration & Studio State
 * ====================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  // ------------------------------------------------------------------
  // State & Configuration
  // ------------------------------------------------------------------
  const state = {
    apiKey: localStorage.getItem("valora_api_key") || "",
    currentAudioUrl: null,
    audioBuffer: null,
    waveformPeaks: [],
    audioContext: null,
    isPlaying: false,
    history: JSON.parse(localStorage.getItem("valora_tts_history") || "[]"),
    mediaRecorder: null,
    audioChunks: [],
    recordInterval: null,
    recordSeconds: 0,
    selectedEmotion: "neutral",
    selectedIntensity: 1.0,
  };

  // ------------------------------------------------------------------
  // DOM Elements
  // ------------------------------------------------------------------
  const navTabs = document.querySelectorAll(".nav-tab");
  const tabPanes = document.querySelectorAll(".tab-pane");

  // TTS Elements
  const ttsTextInput = document.getElementById("tts-text-input");
  const charCount = document.getElementById("char-count");
  const voiceSelect = document.getElementById("voice-select");
  const ageSlider = document.getElementById("age-slider");
  const ageValBadge = document.getElementById("age-val-badge");
  const pitchSlider = document.getElementById("pitch-slider");
  const pitchValBadge = document.getElementById("pitch-val-badge");
  const emotionPills = document.querySelectorAll(".emotion-pills .emotion-pill");
  const emotionIntensitySlider = document.getElementById("emotion-intensity-slider");
  const emotionValBadge = document.getElementById("emotion-val-badge");
  const intensityValBadge = document.getElementById("intensity-val-badge");
  const advancedSummaryText = document.getElementById("advanced-summary-text");
  const btnGenerateTts = document.getElementById("btn-generate-tts");
  const btnClearTts = document.getElementById("btn-clear-tts");
  const ttsSpinner = document.getElementById("tts-spinner");
  const ttsMagicIcon = document.getElementById("tts-magic-icon");
  const ttsBtnText = document.getElementById("tts-btn-text");

  // Player Elements
  const mainAudioPlayer = document.getElementById("main-audio-player");
  const btnPlayPause = document.getElementById("btn-play-pause");
  const playIcon = document.getElementById("play-icon");
  const pauseIcon = document.getElementById("pause-icon");
  const playerSeek = document.getElementById("player-seek");
  const timeCurrent = document.getElementById("time-current");
  const timeTotal = document.getElementById("time-total");
  const btnDownloadWav = document.getElementById("btn-download-wav");
  const metricLatency = document.getElementById("metric-latency");
  const metricDuration = document.getElementById("metric-duration");
  const waveformCanvas = document.getElementById("waveform-canvas");
  const waveformPlaceholder = document.getElementById("waveform-placeholder");
  const waveformContainer = document.getElementById("waveform-container");
  const audioReadyTag = document.getElementById("audio-ready-tag");
  const historyList = document.getElementById("history-list");
  const btnClearHistory = document.getElementById("btn-clear-history");

  // Voice Cloning Elements
  const cloneDropzone = document.getElementById("clone-dropzone");
  const cloneFileInput = document.getElementById("clone-file-input");
  const cloneFileName = document.getElementById("clone-file-name");
  const cloneTextInput = document.getElementById("clone-text-input");
  const cloneLangSelect = document.getElementById("clone-lang-select");
  const btnGenerateClone = document.getElementById("btn-generate-clone");
  const cloneSpinner = document.getElementById("clone-spinner");
  const cloneAudioPlayer = document.getElementById("clone-audio-player");
  const btnDownloadClone = document.getElementById("btn-download-clone");

  // STT Elements
  const sttDropzone = document.getElementById("stt-dropzone");
  const sttFileInput = document.getElementById("stt-file-input");
  const sttFileName = document.getElementById("stt-file-name");
  const btnRecordMic = document.getElementById("btn-record-mic");
  const recordDot = document.getElementById("record-dot");
  const recordText = document.getElementById("record-text");
  const recordTimer = document.getElementById("record-timer");
  const sttLangSelect = document.getElementById("stt-lang-select");
  const btnTranscribe = document.getElementById("btn-transcribe");
  const sttSpinner = document.getElementById("stt-spinner");
  const transcriptText = document.getElementById("transcript-text");
  const sttDetectedLang = document.getElementById("stt-detected-lang");
  const btnCopyTranscript = document.getElementById("btn-copy-transcript");
  const segmentsList = document.getElementById("segments-list");

  // Voice Catalog & Search
  const voiceSearchInput = document.getElementById("voice-search-input");
  const voiceCardsGrid = document.getElementById("voice-cards-grid");

  // Settings Modal
  const btnOpenSettings = document.getElementById("btn-open-settings");
  const settingsModal = document.getElementById("settings-modal");
  const btnCloseSettings = document.getElementById("btn-close-settings");
  const btnCancelSettings = document.getElementById("btn-cancel-settings");
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const apiKeyInput = document.getElementById("api-key-input");

  // ------------------------------------------------------------------
  // Helper: Toast Notifications
  // ------------------------------------------------------------------
  function showToast(message, type = "info", duration = 3500) {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(8px)";
      toast.style.transition = "all 0.2s ease";
      setTimeout(() => toast.remove(), 200);
    }, duration);
  }

  function handleRateLimit(retryAfterSeconds, endpointName) {
    let remaining = retryAfterSeconds || 60;
    const toast = document.createElement("div");
    toast.className = "toast toast-warning";
    
    const updateText = () => {
      toast.innerHTML = `<strong>⚠️ Rate Limit (${escapeHtml(endpointName)})</strong> — Reset in ${remaining}s`;
    };
    updateText();

    const container = document.getElementById("toast-container");
    if (container) container.appendChild(toast);

    const timer = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        clearInterval(timer);
        toast.className = "toast toast-success";
        toast.innerHTML = `<strong>✅ Ready</strong> — Rate limit cleared!`;
        setTimeout(() => toast.remove(), 2500);
      } else {
        updateText();
      }
    }, 1000);
  }

  // ------------------------------------------------------------------
  // API Fetch Wrapper
  // ------------------------------------------------------------------
  async function apiFetch(endpoint, options = {}) {
    const headers = options.headers || {};
    if (state.apiKey) {
      headers["X-API-Key"] = state.apiKey;
    }

    const res = await fetch(endpoint, { ...options, headers });
    if (res.status === 429) {
      const errorData = await res.json().catch(() => ({}));
      const retryAfter = errorData.retry_after_seconds || parseInt(res.headers.get("Retry-After") || "60", 10);
      handleRateLimit(retryAfter, endpoint);
      throw new Error(errorData.detail || `Rate limit exceeded. Please retry in ${retryAfter}s.`);
    }
    return res;
  }

  // ------------------------------------------------------------------
  // Theme Toggle
  // ------------------------------------------------------------------
  const btnThemeToggle = document.getElementById("btn-theme-toggle");
  const themeIconSun = document.getElementById("theme-icon-sun");
  const themeIconMoon = document.getElementById("theme-icon-moon");

  function applyTheme(theme) {
    if (theme === "light") {
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
      document.body.classList.remove("dark");
      document.body.classList.add("light");
      if (themeIconSun) themeIconSun.classList.remove("hidden");
      if (themeIconMoon) themeIconMoon.classList.add("hidden");
    } else {
      document.documentElement.classList.remove("light");
      document.documentElement.classList.add("dark");
      document.body.classList.remove("light");
      document.body.classList.add("dark");
      if (themeIconSun) themeIconSun.classList.add("hidden");
      if (themeIconMoon) themeIconMoon.classList.remove("hidden");
    }
    localStorage.setItem("valora-theme", theme);
    // Redraw waveform with new theme colors
    drawRealWaveform();
  }

  function initTheme() {
    const saved = localStorage.getItem("valora-theme") || localStorage.getItem("valora.theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme = saved ? saved : (prefersDark ? "dark" : "light");
    applyTheme(initialTheme);
  }

  if (btnThemeToggle) {
    btnThemeToggle.addEventListener("click", () => {
      const isCurrentlyDark = document.documentElement.classList.contains("dark") ||
        (!document.documentElement.classList.contains("light") && window.matchMedia("(prefers-color-scheme: dark)").matches);
      applyTheme(isCurrentlyDark ? "light" : "dark");
    });
  }

  initTheme();

  // ------------------------------------------------------------------
  // Tab Navigation
  // ------------------------------------------------------------------
  navTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      navTabs.forEach((t) => t.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");

      if (targetId === "voices-tab") renderVoiceCatalog();
    });
  });

  // ------------------------------------------------------------------
  // TTS Controls, Advanced Accordion Summary & Sliders
  // ------------------------------------------------------------------
  function updateAdvancedSummary() {
    if (!advancedSummaryText) return;
    const age = ageSlider ? ageSlider.value : 28;
    const pitch = pitchSlider ? parseFloat(pitchSlider.value).toFixed(1) : "0.0";
    const emotionName = state.selectedEmotion.charAt(0).toUpperCase() + state.selectedEmotion.slice(1);
    advancedSummaryText.textContent = `Age: ${age}y · ${emotionName} (${state.selectedIntensity.toFixed(1)}×) · ${pitch > 0 ? "+" : ""}${pitch}st`;
  }

  emotionPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      emotionPills.forEach((p) => {
        p.classList.remove("active");
        p.setAttribute("aria-checked", "false");
      });
      pill.classList.add("active");
      pill.setAttribute("aria-checked", "true");
      state.selectedEmotion = pill.getAttribute("data-emotion") || "neutral";
      if (emotionValBadge) {
        const cap = state.selectedEmotion.charAt(0).toUpperCase() + state.selectedEmotion.slice(1);
        emotionValBadge.textContent = `${cap} (${state.selectedIntensity.toFixed(2)}×)`;
      }
      updateAdvancedSummary();
    });
  });

  if (emotionIntensitySlider) {
    emotionIntensitySlider.addEventListener("input", (e) => {
      state.selectedIntensity = parseFloat(e.target.value) || 1.0;
      if (intensityValBadge) {
        intensityValBadge.textContent = `${state.selectedIntensity.toFixed(2)}×`;
      }
      if (emotionValBadge) {
        const cap = state.selectedEmotion.charAt(0).toUpperCase() + state.selectedEmotion.slice(1);
        emotionValBadge.textContent = `${cap} (${state.selectedIntensity.toFixed(2)}×)`;
      }
      updateAdvancedSummary();
    });
  }

  if (ttsTextInput && charCount) {
    ttsTextInput.addEventListener("input", () => {
      charCount.textContent = ttsTextInput.value.length.toLocaleString();
    });
  }

  document.querySelectorAll(".prompt-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      if (ttsTextInput) {
        ttsTextInput.value = chip.getAttribute("data-text") || "";
        if (charCount) charCount.textContent = ttsTextInput.value.length.toLocaleString();
        ttsTextInput.focus();
      }
    });
  });

  if (ageSlider && ageValBadge) {
    ageSlider.addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10);
      let label = `${val} yrs`;
      if (val <= 12) label += " (Child)";
      else if (val <= 20) label += " (Youth)";
      else if (val === 28) label += " (Natural)";
      else if (val >= 65) label += " (Senior)";
      ageValBadge.textContent = label;
      updateAdvancedSummary();
    });
  }

  if (pitchSlider && pitchValBadge) {
    pitchSlider.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      pitchValBadge.textContent = `${val > 0 ? "+" : ""}${val.toFixed(1)} st`;
      updateAdvancedSummary();
    });
  }

  if (btnClearTts) {
    btnClearTts.addEventListener("click", () => {
      if (ttsTextInput) {
        ttsTextInput.value = "";
        if (charCount) charCount.textContent = "0";
        ttsTextInput.focus();
      }
    });
  }

  updateAdvancedSummary();

  // ------------------------------------------------------------------
  // Real Waveform Extraction & Rendering (Never Fake)
  // ------------------------------------------------------------------
  function getAudioContext() {
    if (!state.audioContext) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      state.audioContext = new AudioCtx();
    }
    if (state.audioContext.state === "suspended") {
      state.audioContext.resume();
    }
    return state.audioContext;
  }

  async function processRealWaveform(arrayBuffer) {
    try {
      const ctx = getAudioContext();
      // Decode audio data to extract real PCM channels
      const decoded = await ctx.decodeAudioData(arrayBuffer.slice(0));
      state.audioBuffer = decoded;

      const rawData = decoded.getChannelData(0); // Left channel
      const totalSamples = rawData.length;
      const numBars = 80;
      const blockSize = Math.floor(totalSamples / numBars);
      const peaks = [];

      for (let i = 0; i < numBars; i++) {
        let blockStart = blockSize * i;
        let sum = 0;
        for (let j = 0; j < blockSize; j++) {
          sum += Math.abs(rawData[blockStart + j] || 0);
        }
        peaks.push(sum / blockSize);
      }

      // Normalize peaks
      const maxPeak = Math.max(...peaks, 0.01);
      state.waveformPeaks = peaks.map((p) => Math.max(0.12, p / maxPeak));
      drawRealWaveform();
    } catch (err) {
      console.warn("Could not decode audio waveform:", err);
      // Fallback: draw subtle resting line
      state.waveformPeaks = Array(80).fill(0.15);
      drawRealWaveform();
    }
  }

  function drawRealWaveform() {
    if (!waveformCanvas) return;
    const ctx = waveformCanvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = waveformCanvas.getBoundingClientRect();

    waveformCanvas.width = rect.width * dpr;
    waveformCanvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0, 0, w, h);

    if (state.waveformPeaks.length === 0) return;

    const isLight = document.documentElement.classList.contains("light");
    const primaryColor = "#2563eb";
    const playedColor = isLight ? "#2563eb" : "#3b82f6";
    const unplayedColor = isLight ? "rgba(15, 23, 42, 0.16)" : "rgba(255, 255, 255, 0.16)";

    const duration = mainAudioPlayer.duration || 1;
    const currentTime = mainAudioPlayer.currentTime || 0;
    const progress = duration > 0 ? currentTime / duration : 0;

    const numBars = state.waveformPeaks.length;
    const barWidth = Math.max(2, (w / numBars) - 2);
    const gap = (w - numBars * barWidth) / (numBars - 1 || 1);

    for (let i = 0; i < numBars; i++) {
      const peak = state.waveformPeaks[i];
      const barHeight = Math.max(4, peak * (h * 0.76));
      const x = i * (barWidth + gap);
      const y = (h - barHeight) / 2;

      const isPlayed = i / numBars <= progress;
      ctx.fillStyle = isPlayed ? playedColor : unplayedColor;

      // Draw rounded bar
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barHeight, 2);
      ctx.fill();
    }

    // Draw playhead scrubber indicator
    if (progress > 0 && progress < 1) {
      const playheadX = progress * w;
      ctx.strokeStyle = primaryColor;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(playheadX, 4);
      ctx.lineTo(playheadX, h - 4);
      ctx.stroke();
    }
  }

  // Interactive click-to-seek on waveform canvas
  if (waveformContainer) {
    waveformContainer.addEventListener("click", (e) => {
      if (!mainAudioPlayer.src || !mainAudioPlayer.duration) return;
      const rect = waveformContainer.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const pct = Math.max(0, Math.min(1, clickX / rect.width));
      mainAudioPlayer.currentTime = pct * mainAudioPlayer.duration;
      drawRealWaveform();
    });
  }

  // Resize observer for responsive canvas crispness
  window.addEventListener("resize", () => {
    drawRealWaveform();
  });

  // ------------------------------------------------------------------
  // TTS Synthesis Execution
  // ------------------------------------------------------------------
  btnGenerateTts.addEventListener("click", async () => {
    const text = ttsTextInput.value.trim();
    if (!text) {
      showToast("Please enter some text in the script editor.", "warning");
      ttsTextInput.focus();
      return;
    }

    const voicePreset = voiceSelect.value;
    const age = parseInt(ageSlider.value, 10);
    const pitch = parseFloat(pitchSlider.value);

    // UI Loading State
    btnGenerateTts.disabled = true;
    ttsSpinner.classList.remove("hidden");
    ttsMagicIcon.classList.add("hidden");
    ttsBtnText.textContent = "Generating...";
    if (audioReadyTag) {
      audioReadyTag.textContent = "Generating...";
      audioReadyTag.className = "tag-pill tag-blue";
    }
    const startTime = performance.now();

    try {
      const response = await apiFetch("/tts/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          voice_preset: voicePreset,
          age,
          pitch_semitones: pitch !== 0 ? pitch : null,
          emotion: state.selectedEmotion,
          emotion_intensity: state.selectedIntensity,
        }),
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Synthesis failed (${response.status})`);
      }

      const blob = await response.blob();
      const arrayBuffer = await blob.arrayBuffer();
      const audioUrl = URL.createObjectURL(blob);
      const latency = ((performance.now() - startTime) / 1000).toFixed(2);

      // Duration from header or calculated
      const headerDur = response.headers.get("X-Audio-Duration-Seconds");
      const duration = headerDur ? `${parseFloat(headerDur).toFixed(1)}s` : "--";

      metricLatency.textContent = `Latency: ${latency}s`;
      metricDuration.textContent = `Duration: ${duration}`;
      if (audioReadyTag) {
        audioReadyTag.textContent = "Ready";
        audioReadyTag.className = "tag-pill tag-green";
      }

      await loadAudioIntoPlayer(audioUrl, arrayBuffer, text, voicePreset);
      showToast("Speech generated successfully!", "success");
    } catch (err) {
      if (audioReadyTag) {
        audioReadyTag.textContent = "Error";
        audioReadyTag.className = "tag-pill tag-red";
      }
      showToast(err.message, "error", 5000);
    } finally {
      btnGenerateTts.disabled = false;
      ttsSpinner.classList.add("hidden");
      ttsMagicIcon.classList.remove("hidden");
      ttsBtnText.textContent = "Generate speech";
    }
  });

  // ------------------------------------------------------------------
  // Audio Player Engine
  // ------------------------------------------------------------------
  async function loadAudioIntoPlayer(url, arrayBuffer, textTitle, voice) {
    if (state.currentAudioUrl) {
      URL.revokeObjectURL(state.currentAudioUrl);
    }
    state.currentAudioUrl = url;
    mainAudioPlayer.src = url;
    btnPlayPause.disabled = false;
    playerSeek.disabled = false;
    btnDownloadWav.classList.remove("disabled");
    btnDownloadWav.href = url;
    waveformPlaceholder.classList.add("hidden");

    // Process actual waveform from decoded PCM buffer
    await processRealWaveform(arrayBuffer);

    // Add take to session history
    const item = {
      id: Date.now(),
      title: textTitle.slice(0, 36) + (textTitle.length > 36 ? "…" : ""),
      voice: voice.replace("v2/", ""),
      url,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    state.history.unshift(item);
    if (state.history.length > 25) state.history.pop();
    localStorage.setItem("valora_tts_history", JSON.stringify(state.history));
    renderHistory();

    // Auto play preview
    playAudio();
  }

  function playAudio() {
    getAudioContext();
    mainAudioPlayer.play().catch(() => {});
    state.isPlaying = true;
    playIcon.classList.add("hidden");
    pauseIcon.classList.remove("hidden");
  }

  function pauseAudio() {
    mainAudioPlayer.pause();
    state.isPlaying = false;
    playIcon.classList.remove("hidden");
    pauseIcon.classList.add("hidden");
  }

  btnPlayPause.addEventListener("click", () => {
    if (state.isPlaying) pauseAudio();
    else playAudio();
  });

  mainAudioPlayer.addEventListener("timeupdate", () => {
    const cur = mainAudioPlayer.currentTime;
    const dur = mainAudioPlayer.duration || 1;
    playerSeek.value = (cur / dur) * 100;
    timeCurrent.textContent = formatTime(cur);
    timeTotal.textContent = formatTime(dur);
    drawRealWaveform();
  });

  mainAudioPlayer.addEventListener("ended", () => {
    pauseAudio();
    playerSeek.value = 0;
    timeCurrent.textContent = "0:00";
    drawRealWaveform();
  });

  playerSeek.addEventListener("input", (e) => {
    const dur = mainAudioPlayer.duration || 1;
    mainAudioPlayer.currentTime = (e.target.value / 100) * dur;
    drawRealWaveform();
  });

  function formatTime(secs) {
    if (isNaN(secs) || secs < 0) return "0:00";
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  }

  // ------------------------------------------------------------------
  // History Rendering
  // ------------------------------------------------------------------
  function renderHistory() {
    if (!historyList) return;
    if (state.history.length === 0) {
      historyList.innerHTML = `<div class="history-empty">No recent takes yet this session.</div>`;
      return;
    }

    historyList.innerHTML = state.history
      .map(
        (h) => `
        <div class="history-item">
          <div class="min-w-0 flex-1">
            <div class="history-title">${escapeHtml(h.title)}</div>
            <div class="history-meta">${escapeHtml(h.voice)} · ${h.time}</div>
          </div>
          <div class="flex items-center gap-1">
            <button type="button" class="btn btn-secondary btn-xs history-play-btn" data-url="${h.url}" title="Play take">▶</button>
            <a href="${h.url}" download="valora_take_${h.id}.wav" class="btn btn-ghost btn-xs" title="Download WAV">↓</a>
          </div>
        </div>
      `
      )
      .join("");

    historyList.querySelectorAll(".history-play-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const url = btn.getAttribute("data-url");
        if (url) {
          mainAudioPlayer.src = url;
          playAudio();
        }
      });
    });
  }

  if (btnClearHistory) {
    btnClearHistory.addEventListener("click", () => {
      state.history = [];
      localStorage.removeItem("valora_tts_history");
      renderHistory();
    });
  }

  renderHistory();

  // ------------------------------------------------------------------
  // Voice Cloning Controller
  // ------------------------------------------------------------------
  if (cloneDropzone && cloneFileInput) {
    cloneDropzone.addEventListener("click", () => cloneFileInput.click());
    cloneFileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        cloneFileName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
      }
    });
  }

  if (btnGenerateClone) {
    btnGenerateClone.addEventListener("click", async () => {
      const file = cloneFileInput.files[0];
      const text = cloneTextInput.value.trim();
      if (!file) {
        showToast("Please select reference audio for voice cloning.", "warning");
        return;
      }
      if (!text) {
        showToast("Please enter a script for the cloned voice.", "warning");
        cloneTextInput.focus();
        return;
      }

      btnGenerateClone.disabled = true;
      cloneSpinner.classList.remove("hidden");

      try {
        const formData = new FormData();
        formData.append("reference_audio", file);
        formData.append("text", text);
        formData.append("language", cloneLangSelect.value);

        const res = await apiFetch("/tts/clone", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const errJson = await res.json().catch(() => ({}));
          throw new Error(errJson.detail || `Voice cloning failed (${res.status})`);
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        cloneAudioPlayer.src = url;
        btnDownloadClone.classList.remove("disabled");
        btnDownloadClone.href = url;
        cloneAudioPlayer.play().catch(() => {});
        showToast("Voice cloned and synthesized successfully!", "success");
      } catch (err) {
        showToast(err.message, "error", 5000);
      } finally {
        btnGenerateClone.disabled = false;
        cloneSpinner.classList.add("hidden");
      }
    });
  }

  // ------------------------------------------------------------------
  // Speech-to-Text Controller (File + Microphone Recording)
  // ------------------------------------------------------------------
  if (sttDropzone && sttFileInput) {
    sttDropzone.addEventListener("click", () => sttFileInput.click());
    sttFileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        sttFileName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
      }
    });
  }

  // Microphone Recording
  if (btnRecordMic) {
    btnRecordMic.addEventListener("click", async () => {
      if (state.mediaRecorder && state.mediaRecorder.state === "recording") {
        state.mediaRecorder.stop();
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        state.audioChunks = [];
        state.mediaRecorder = new MediaRecorder(stream);

        state.mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) state.audioChunks.push(e.data);
        };

        state.mediaRecorder.onstart = () => {
          recordDot.classList.add("recording");
          recordText.textContent = "Stop Recording";
          recordTimer.classList.remove("hidden");
          state.recordSeconds = 0;
          state.recordInterval = setInterval(() => {
            state.recordSeconds += 1;
            recordTimer.textContent = formatTime(state.recordSeconds);
          }, 1000);
        };

        state.mediaRecorder.onstop = () => {
          clearInterval(state.recordInterval);
          recordDot.classList.remove("recording");
          recordText.textContent = "Record from Microphone";
          recordTimer.classList.add("hidden");
          const audioBlob = new Blob(state.audioChunks, { type: "audio/wav" });
          const recordFile = new File([audioBlob], "microphone_record.wav", { type: "audio/wav" });
          
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(recordFile);
          sttFileInput.files = dataTransfer.files;
          sttFileName.textContent = "Microphone recording ready";
          showToast("Microphone audio captured! Click 'Transcribe Audio'.", "info");
        };

        state.mediaRecorder.start();
      } catch (err) {
        showToast(`Microphone access error: ${err.message}`, "error");
      }
    });
  }

  if (btnTranscribe) {
    btnTranscribe.addEventListener("click", async () => {
      const file = sttFileInput.files[0];
      if (!file) {
        showToast("Please upload an audio file or record from microphone.", "warning");
        return;
      }

      btnTranscribe.disabled = true;
      sttSpinner.classList.remove("hidden");
      transcriptText.innerHTML = '<span class="text-muted">Transcribing audio via Whisper AI...</span>';

      try {
        const formData = new FormData();
        formData.append("file", file);
        if (sttLangSelect.value) {
          formData.append("language", sttLangSelect.value);
        }

        const res = await apiFetch("/stt/transcribe", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const errJson = await res.json().catch(() => ({}));
          throw new Error(errJson.detail || `Transcription failed (${res.status})`);
        }

        const result = await res.json();
        transcriptText.textContent = result.text || "No speech detected in audio.";
        sttDetectedLang.textContent = `Language: ${result.language ? result.language.toUpperCase() : "Detected"}`;

        if (result.segments && result.segments.length > 0) {
          segmentsList.innerHTML = result.segments
            .map(
              (s) => `
              <div class="segment-item">
                <span class="segment-time">${formatTime(s.start)} - ${formatTime(s.end)}</span>
                <span class="segment-text">${escapeHtml(s.text)}</span>
              </div>
            `
            )
            .join("");
        } else {
          segmentsList.innerHTML = `<span class="text-muted text-sm">Full text transcribed.</span>`;
        }

        showToast("Transcription complete!", "success");
      } catch (err) {
        transcriptText.innerHTML = `<span style="color: var(--accent-red);">${escapeHtml(err.message)}</span>`;
        showToast(err.message, "error", 5000);
      } finally {
        btnTranscribe.disabled = false;
        sttSpinner.classList.add("hidden");
      }
    });
  }

  if (btnCopyTranscript) {
    btnCopyTranscript.addEventListener("click", () => {
      const text = transcriptText.textContent;
      if (text) {
        navigator.clipboard.writeText(text);
        showToast("Transcript copied to clipboard!", "success");
      }
    });
  }

  // ------------------------------------------------------------------
  // Voice Catalog Renderer
  // ------------------------------------------------------------------
  async function renderVoiceCatalog() {
    if (!voiceCardsGrid) return;
    try {
      const res = await apiFetch("/tts/voices");
      if (!res.ok) throw new Error("Failed to load voices");
      const data = await res.json();
      const voices = data.voices || [];

      const renderList = (list) => {
        voiceCardsGrid.innerHTML = list
          .map((v) => {
            const id = typeof v === "object" ? v.id : v;
            const name = typeof v === "object" ? v.name : v;
            const lang = typeof v === "object" ? v.language : "Multilingual";
            const tags = typeof v === "object" && v.tags ? v.tags : ["Neural"];
            const initial = name.charAt(0).toUpperCase();

            return `
              <div class="voice-card">
                <div class="voice-card-header">
                  <div class="voice-avatar">${initial}</div>
                  <div>
                    <div class="voice-card-name">${escapeHtml(name)}</div>
                    <div class="voice-card-lang">${escapeHtml(lang)}</div>
                  </div>
                </div>
                <div class="voice-tags">
                  ${tags.map((t) => `<span class="tag-pill">${escapeHtml(t)}</span>`).join("")}
                </div>
                <button class="btn btn-secondary btn-sm select-voice-btn" data-id="${id}" type="button">
                  Use in Studio
                </button>
              </div>
            `;
          })
          .join("");

        voiceCardsGrid.querySelectorAll(".select-voice-btn").forEach((btn) => {
          btn.addEventListener("click", () => {
            const voiceId = btn.getAttribute("data-id");
            if (voiceSelect) {
              voiceSelect.value = voiceId;
            }
            // Switch to TTS Tab
            const ttsTabBtn = document.getElementById("tab-btn-tts");
            if (ttsTabBtn) ttsTabBtn.click();
            showToast(`Voice preset set to ${voiceId}`, "info");
          });
        });
      };

      renderList(voices);

      if (voiceSearchInput) {
        voiceSearchInput.addEventListener("input", (e) => {
          const query = e.target.value.toLowerCase();
          const filtered = voices.filter((v) => {
            const str = typeof v === "object" ? `${v.name} ${v.language} ${v.id}` : v;
            return str.toLowerCase().includes(query);
          });
          renderList(filtered);
        });
      }
    } catch (err) {
      voiceCardsGrid.innerHTML = `<div class="p-4 text-muted">Failed to load voice catalog.</div>`;
    }
  }

  // ------------------------------------------------------------------
  // Settings Modal & API Key
  // ------------------------------------------------------------------
  if (btnOpenSettings && settingsModal) {
    btnOpenSettings.addEventListener("click", () => {
      if (apiKeyInput) apiKeyInput.value = state.apiKey;
      settingsModal.classList.remove("hidden");
    });

    const closeSettings = () => settingsModal.classList.add("hidden");
    if (btnCloseSettings) btnCloseSettings.addEventListener("click", closeSettings);
    if (btnCancelSettings) btnCancelSettings.addEventListener("click", closeSettings);

    if (btnSaveSettings) {
      btnSaveSettings.addEventListener("click", () => {
        state.apiKey = apiKeyInput ? apiKeyInput.value.trim() : "";
        localStorage.setItem("valora_api_key", state.apiKey);
        closeSettings();
        showToast("API Key settings saved!", "success");
      });
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
