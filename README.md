# Valora AI — Neural Voice Studio & Speech Platform

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Rexlogger-hue/valora-studio)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)
![Firebase](https://img.shields.io/badge/Firebase-Auth-FFCA28?logo=firebase)
![Audio](https://img.shields.io/badge/Audio-48kHz%20Master-8b5cf6)

> **"Give every voice a presence."**  
> Valora AI is a next-generation neural voice studio featuring high-fidelity speech synthesis, zero-shot voice cloning, dynamic age & pitch transformation, and interactive Web Studio controls.

---

## 🌟 Key Features

- **300+ Neural Voices**: Real-time multi-lingual synthesis across 30+ locales via hosted neural diffusion.
- **AI4Bharat Indic-Parler-TTS**: Native Hindi conversational & expressive audio synthesis.
- **Firebase Google Authentication**: Secure real-time Google Sign-In & Sign-Out with token persistence.
- **Expressive Emotion Matrix**: Fine directability for `cheerful`, `warm`, `confident`, `serious`, `whisper`, `empathetic`, and `dramatic` speech styles with 0–100% intensity control.
- **Age & Pitch Transformation**: Deterministic phase-vocoder DSP shift simulating child to elderly voices (1–100 years).
- **Interactive Web Studio**: Real-time waveform audio player, kinetic grid canvas, and instant lossless WAV exports.

---

## 🚀 Quick Start (Local Run)

### 1. Launch Web Studio & Backend Server (Port 8000)
```powershell
python run.py --server
```
Navigate to `http://127.0.0.1:8000` to open the studio UI.

### 2. Interactive Menu
```powershell
python run.py
```

### 3. Generate Speech via CLI
```powershell
python run.py --text "Welcome to Valora AI Studio." --voice "v2/en_speaker_6" --emotion "cheerful"
```

---

## ☁️ Deployment

### Deploy to Vercel
This repository is configured for immediate deployment on Vercel:
1. Import this repository in [Vercel Dashboard](https://vercel.com/new).
2. Click **Deploy**.
3. All static routes and studio assets are served via Vercel's global edge network.

---

## 📄 License
MIT License. Created by [Rexlogger-hue](https://github.com/Rexlogger-hue).
