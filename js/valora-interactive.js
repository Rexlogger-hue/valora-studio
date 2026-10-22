/**
 * ====================================================================
 * VALORA AI — CINEMATIC INTERACTIVE COMPONENT CONTROLLER
 * Hero Sandbox, A/B Comparator, Emotion Matrix, Voice Library,
 * Age/Pitch Transformer, API Code Switcher & Ambient Audio.
 * ====================================================================
 */

(function () {
  // ------------------------------------------------------------------
  // 1. Web Audio Ambient Soundscape Generator
  // ------------------------------------------------------------------
  let audioCtx = null;
  let masterGain = null;
  let isSoundOn = false;

  function initAmbientAudio() {
    if (audioCtx) return;
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    audioCtx = new AudioContextClass();
    masterGain = audioCtx.createGain();
    masterGain.gain.setValueAtTime(0, audioCtx.currentTime);

    // Deep Sub Oscillator (55Hz)
    const osc1 = audioCtx.createOscillator();
    osc1.type = "sine";
    osc1.frequency.setValueAtTime(55, audioCtx.currentTime);

    // Harmonic Texture (110.2Hz)
    const osc2 = audioCtx.createOscillator();
    osc2.type = "triangle";
    osc2.frequency.setValueAtTime(110.2, audioCtx.currentTime);

    // Sweeping Filter
    const filter = audioCtx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(360, audioCtx.currentTime);

    const lfo = audioCtx.createOscillator();
    lfo.frequency.setValueAtTime(0.09, audioCtx.currentTime);
    const lfoGain = audioCtx.createGain();
    lfoGain.gain.setValueAtTime(180, audioCtx.currentTime);
    lfo.connect(lfoGain);
    lfoGain.connect(filter.frequency);

    const g1 = audioCtx.createGain();
    g1.gain.setValueAtTime(0.3, audioCtx.currentTime);
    const g2 = audioCtx.createGain();
    g2.gain.setValueAtTime(0.1, audioCtx.currentTime);

    osc1.connect(g1);
    osc2.connect(g2);
    g1.connect(filter);
    g2.connect(filter);
    filter.connect(masterGain);
    masterGain.connect(audioCtx.destination);

    osc1.start();
    osc2.start();
    lfo.start();
  }

  function toggleSound() {
    if (!audioCtx) initAmbientAudio();
    if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();

    const btn = document.getElementById("nav-sound-toggle-btn");
    const label = document.getElementById("nav-sound-toggle-label");

    if (isSoundOn) {
      if (masterGain) masterGain.gain.setTargetAtTime(0, audioCtx.currentTime, 0.4);
      isSoundOn = false;
      if (btn) btn.classList.remove("active");
      if (label) label.textContent = "SOUND OFF";
    } else {
      if (masterGain) masterGain.gain.setTargetAtTime(0.25, audioCtx.currentTime, 0.5);
      isSoundOn = true;
      if (btn) btn.classList.add("active");
      if (label) label.textContent = "SOUND ON";
    }
  }

  // ------------------------------------------------------------------
  // 2. Synthesize Synthetic Tone / Preview Helper
  // ------------------------------------------------------------------
  function playSyntheticTone(freq = 220, duration = 1.8, type = "sine") {
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      const ctx = new AC();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(freq * 0.95, ctx.currentTime + duration);

      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch (e) {
      console.warn("Audio synthesis error:", e);
    }
  }

  // ------------------------------------------------------------------
  // 3. Hero Sandbox Logic
  // ------------------------------------------------------------------
  function initHeroSandbox() {
    const textInput = document.getElementById("sandbox-text-input");
    const voiceSelect = document.getElementById("sandbox-voice-select");
    const emotionSelect = document.getElementById("sandbox-emotion-select");
    const intensitySlider = document.getElementById("sandbox-intensity-slider");
    const intensityVal = document.getElementById("sandbox-intensity-val");
    const btnPlay = document.getElementById("btn-sandbox-play");
    const statusText = document.getElementById("sandbox-status-text");

    if (intensitySlider && intensityVal) {
      intensitySlider.addEventListener("input", (e) => {
        intensityVal.textContent = parseFloat(e.target.value).toFixed(1) + "x";
      });
    }

    if (btnPlay) {
      btnPlay.addEventListener("click", async () => {
        const text = textInput ? textInput.value.trim() : "Valora AI - Sound Without Gravity";
        const voice = voiceSelect ? voiceSelect.value : "v2/en_speaker_6";
        const emotion = emotionSelect ? emotionSelect.value : "confident";
        const intensity = intensitySlider ? parseFloat(intensitySlider.value) : 1.2;

        btnPlay.disabled = true;
        if (statusText) statusText.textContent = "Synthesizing...";

        try {
          // Attempt real API generation via FastAPI backend
          let res = await fetch("/tts/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              text,
              voice_preset: voice,
              emotion,
              emotion_intensity: intensity,
            }),
          }).catch(() => null);

          if (!res || !res.ok) {
            res = await fetch("/tts", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                text,
                voice_preset: voice,
                emotion,
                emotion_intensity: intensity,
              }),
            }).catch(() => null);
          }

          if (res.ok) {
            const blob = await res.blob();
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);
            audio.play();
            if (statusText) statusText.textContent = "Playing synthesis";
            audio.onended = () => {
              if (statusText) statusText.textContent = "Ready";
              btnPlay.disabled = false;
            };
          } else {
            // Fallback tone
            playSyntheticTone(260, 2.0, "triangle");
            if (statusText) statusText.textContent = "Preview tone active";
            setTimeout(() => {
              if (statusText) statusText.textContent = "Ready";
              btnPlay.disabled = false;
            }, 2000);
          }
        } catch (e) {
          playSyntheticTone(260, 2.0, "triangle");
          if (statusText) statusText.textContent = "Ready";
          btnPlay.disabled = false;
        }
      });
    }
  }

  // ------------------------------------------------------------------
  // 4. Voice Cloning Split-Screen A/B Comparator
  // ------------------------------------------------------------------
  function initCloningComparator() {
    const cardOrig = document.getElementById("deck-orig");
    const cardClone = document.getElementById("deck-clone");
    const btnPlayOrig = document.getElementById("btn-play-orig");
    const btnPlayClone = document.getElementById("btn-play-clone");
    const canvasOrig = document.getElementById("wave-orig-canvas");
    const canvasClone = document.getElementById("wave-clone-canvas");

    function drawDummyWave(canvas, color) {
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      const w = canvas.width = canvas.offsetWidth;
      const h = canvas.height = canvas.offsetHeight;
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = color;
      const bars = 44;
      const barW = (w / bars) - 2;
      for (let i = 0; i < bars; i++) {
        const barH = (Math.sin(i * 0.3) * 0.4 + 0.5) * (h * 0.8);
        ctx.fillRect(i * (barW + 2), (h - barH) / 2, barW, barH);
      }
    }

    drawDummyWave(canvasOrig, "rgba(255, 255, 255, 0.45)");
    drawDummyWave(canvasClone, "rgba(59, 130, 246, 0.75)");

    if (btnPlayOrig) {
      btnPlayOrig.addEventListener("click", () => {
        if (cardOrig) cardOrig.classList.add("active");
        if (cardClone) cardClone.classList.remove("active");
        playSyntheticTone(220, 2.2, "sine");
      });
    }

    if (btnPlayClone) {
      btnPlayClone.addEventListener("click", () => {
        if (cardClone) cardClone.classList.add("active");
        if (cardOrig) cardOrig.classList.remove("active");
        playSyntheticTone(220.5, 2.2, "triangle");
      });
    }
  }

  // ------------------------------------------------------------------
  // 5. Emotion Node Matrix
  // ------------------------------------------------------------------
  function initEmotionNodes() {
    const nodes = document.querySelectorAll(".btn-emotion-node");
    const readout = document.getElementById("emotion-active-readout");
    const slider = document.getElementById("emotion-matrix-slider");
    const sliderVal = document.getElementById("emotion-matrix-slider-val");

    nodes.forEach((node) => {
      node.addEventListener("click", () => {
        nodes.forEach((n) => n.classList.remove("active"));
        node.classList.add("active");
        const emotionName = node.getAttribute("data-emotion") || "Warm";
        if (readout) readout.textContent = emotionName.toUpperCase();
        playSyntheticTone(240 + Math.random() * 40, 1.2, "sine");
      });
    });

    if (slider && sliderVal) {
      slider.addEventListener("input", (e) => {
        sliderVal.textContent = parseFloat(e.target.value).toFixed(1) + "x";
      });
    }
  }

  // ------------------------------------------------------------------
  // 6. Voice Library Preview Buttons
  // ------------------------------------------------------------------
  function initVoicePreviews() {
    const previewBtns = document.querySelectorAll(".btn-voice-preview");
    const freqs = { Aria: 280, Christopher: 130, Emma: 260, Marcus: 145 };

    previewBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const voice = btn.getAttribute("data-voice") || "Aria";
        const f = freqs[voice] || 220;
        playSyntheticTone(f, 1.6, "triangle");
      });
    });
  }

  // ------------------------------------------------------------------
  // 7. Voice Transformation Chain
  // ------------------------------------------------------------------
  function initTransformChain() {
    const chainNodes = document.querySelectorAll(".chain-node");
    const freqs = { youthful: 320, natural: 240, mature: 180, authoritative: 140, whisper: 400 };

    chainNodes.forEach((node) => {
      node.addEventListener("click", () => {
        chainNodes.forEach((n) => n.classList.remove("active"));
        node.classList.add("active");
        const mode = node.getAttribute("data-mode") || "natural";
        const f = freqs[mode] || 240;
        playSyntheticTone(f, 1.5, mode === "whisper" ? "sine" : "triangle");
      });
    });
  }

  // ------------------------------------------------------------------
  // 8. Developer API Code Switcher
  // ------------------------------------------------------------------
  const CODE_SNIPPETS = {
    python: `<span class="kw">import</span> valora

client = valora.<span class="fn">Client</span>(api_key=<span class="str">"val_live_..."</span>)

audio = client.tts.<span class="fn">generate</span>(
    text=<span class="str">"Welcome to the next dimension of neural speech."</span>,
    voice=<span class="str">"aria"</span>,
    emotion=<span class="str">"confident"</span>,
    intensity=<span class="num">1.2</span>
)

audio.<span class="fn">save</span>(<span class="str">"output.wav"</span>)`,

    javascript: `<span class="kw">import</span> { ValoraClient } <span class="kw">from</span> <span class="str">"@valora/sdk"</span>;

<span class="kw">const</span> valora = <span class="kw">new</span> <span class="fn">ValoraClient</span>({ apiKey: <span class="str">"val_live_..."</span> });

<span class="kw">const</span> stream = <span class="kw">await</span> valora.tts.<span class="fn">generate</span>({
  text: <span class="str">"Welcome to the next dimension of neural speech."</span>,
  voice: <span class="str">"aria"</span>,
  emotion: <span class="str">"confident"</span>,
  intensity: <span class="num">1.2</span>
});

<span class="kw">await</span> stream.<span class="fn">pipeToFile</span>(<span class="str">"output.wav"</span>);`,

    curl: `<span class="fn">curl</span> -X POST https://api.valora.ai/v1/tts/generate \\
  -H <span class="str">"Authorization: Bearer val_live_..."</span> \\
  -H <span class="str">"Content-Type: application/json"</span> \\
  -d '{
    <span class="str">"text"</span>: <span class="str">"Welcome to the next dimension of neural speech."</span>,
    <span class="str">"voice"</span>: <span class="str">"aria"</span>,
    <span class="str">"emotion"</span>: <span class="str">"confident"</span>,
    <span class="str">"intensity"</span>: <span class="num">1.2</span>
  }' \\
  --output output.wav`,
  };

  function initApiTabs() {
    const tabs = document.querySelectorAll(".api-tab-btn");
    const codePre = document.getElementById("code-display");
    const copyBtn = document.getElementById("btn-copy-code");

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        const lang = tab.getAttribute("data-lang") || "python";
        if (codePre) {
          codePre.innerHTML = CODE_SNIPPETS[lang] || CODE_SNIPPETS.python;
        }
      });
    });

    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        const rawCode = `import valora\n\nclient = valora.Client(api_key="val_live_...")\n\naudio = client.tts.generate(\n    text="Welcome to the next dimension of neural speech.",\n    voice="aria",\n    emotion="confident",\n    intensity=1.2\n)\n\naudio.save("output.wav")`;
        navigator.clipboard.writeText(rawCode).then(() => {
          copyBtn.textContent = "COPIED!";
          setTimeout(() => (copyBtn.textContent = "COPY"), 2000);
        });
      });
    }
  }

  // ------------------------------------------------------------------
  // Initialize All Components on DOM Ready
  // ------------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", () => {
    initHeroSandbox();
    initCloningComparator();
    initEmotionNodes();
    initVoicePreviews();
    initTransformChain();
    initApiTabs();

    const soundBtn = document.getElementById("nav-sound-toggle-btn");
    if (soundBtn) {
      soundBtn.addEventListener("click", toggleSound);
    }
  });
})();
