"""
services/tts/clone_model.py

Voice cloning wrapper for Valora AI, using Coqui XTTS-v2.

This is a separate, optional model from the default edge-tts backend
(services/tts/model.py). It is lazily loaded on first use to avoid
consuming GPU memory or startup time unless voice cloning is actually
requested.

NOTE: XTTS-v2 is distributed under the Coqui Public Model License
(CPML), which is free for non-commercial use. Commercial use requires
a separate license from Coqui (licensing@coqui.ai).
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Optional

os.environ["COQUI_TOS_AGREED"] = "1"

import torch

logger = logging.getLogger("valora.tts.clone_model")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class VoiceCloneError(Exception):
    """Raised when voice cloning fails."""


class VoiceCloneModel:
    """
    Lazily-loaded wrapper around Coqui XTTS-v2 for voice cloning.

    Example:
        clone = VoiceCloneModel()
        clone.load()
        clone.clone_to_file(
            text="Hello, this is my cloned voice.",
            speaker_wav_path="reference.wav",
            output_path="output.wav",
        )
    """

    MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"

    def __init__(self) -> None:
        self.device: str = "cuda" if torch.cuda.is_available() else "cpu"
        self._tts = None
        self._is_loaded = False
        self._load_lock = threading.Lock()
        self._patch_applied = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def _apply_audio_loader_patch(self) -> None:
        """
        Patch XTTS's internal audio loader to use soundfile instead of
        torchaudio's torchcodec-based loader, which has a known,
        unresolved DLL-loading bug on Windows (see meta-pytorch/torchcodec
        issues #912, #998, #1131, #1233). soundfile is a stable dependency
        already used elsewhere in this project.
        """
        if self._patch_applied:
            return

        import soundfile as sf
        import torchaudio.functional as AF
        from TTS.tts.models import xtts as xtts_module

        def patched_load_audio(audiopath: str, sampling_rate: int) -> torch.Tensor:
            audio_np, source_sample_rate = sf.read(audiopath, dtype="float32", always_2d=False)
            if audio_np.ndim > 1:
                audio_np = audio_np.mean(axis=1)
            audio = torch.from_numpy(audio_np).unsqueeze(0)
            if source_sample_rate != sampling_rate:
                audio = AF.resample(audio, source_sample_rate, sampling_rate)
            audio = torch.clamp(audio, -1, 1)
            return audio

        xtts_module.load_audio = patched_load_audio
        self._patch_applied = True
        logger.info("Applied soundfile-based audio loader patch for XTTS.")

    def load(self) -> None:
        """
        Load the XTTS-v2 model. Idempotent and thread-safe. Downloads
        model weights (~2GB) on first run.

        Raises:
            VoiceCloneError: If loading fails.
        """
        if self._is_loaded:
            return

        with self._load_lock:
            if self._is_loaded:
                return

            try:
                self._apply_audio_loader_patch()

                from TTS.api import TTS

                logger.info("Loading XTTS-v2 voice cloning model onto device '%s'...", self.device)
                self._tts = TTS(self.MODEL_NAME).to(self.device)
                self._is_loaded = True
                logger.info("XTTS-v2 voice cloning model loaded successfully.")
            except Exception as exc:
                self._is_loaded = False
                logger.exception("Failed to load XTTS-v2 voice cloning model.")
                raise VoiceCloneError(f"Failed to load voice cloning model: {exc}") from exc

    def clone_to_file(
        self,
        text: str,
        speaker_wav_path: str,
        output_path: str,
        language: str = "en",
        emotion: str = "neutral",
        emotion_intensity: int = 45,
    ) -> Path:
        """
        Synthesize speech in the voice of the given reference audio with optional
        emotion prosody macro adjustments.

        Args:
            text: Text to synthesize.
            speaker_wav_path: Path to a reference audio file (10-30s of
                clean speech) to clone the voice from.
            output_path: Path to write the resulting WAV file to.
            language: ISO language code (e.g. 'en', 'hi', 'fr', 'es').
            emotion: Optional emotion style ('neutral', 'warm', 'cheerful', etc.).
            emotion_intensity: Optional emotion intensity (0..100).

        Returns:
            Path: The path the audio was written to.

        Raises:
            ValueError: If text is empty.
            VoiceCloneError: If cloning fails.
        """
        if not text or not text.strip():
            raise ValueError("text must be a non-empty string.")

        if not self._is_loaded:
            self.load()

        try:
            self._tts.tts_to_file(
                text=text,
                speaker_wav=speaker_wav_path,
                language=language,
                file_path=output_path,
            )

            # Apply subtle emotion DSP macro if non-neutral and intensity > 0
            if emotion and emotion.lower() != "neutral" and emotion_intensity > 0:
                try:
                    import librosa
                    import soundfile as sf
                    import numpy as np

                    audio, sr = sf.read(output_path)
                    w = float(max(0, min(100, emotion_intensity))) / 100.0
                    emo = emotion.lower().strip()
                    pitch_shift = 0.0
                    time_stretch_rate = 1.0

                    if emo == "cheerful":
                        pitch_shift = w * 1.5
                        time_stretch_rate = 1.0 + (w * 0.08)  # slightly faster
                    elif emo == "serious":
                        pitch_shift = -w * 1.2
                        time_stretch_rate = 1.0 - (w * 0.08)  # slightly slower
                    elif emo == "whisper":
                        pitch_shift = -w * 0.8
                        # Subtle gain reduction and soften dynamics
                        audio = audio * (1.0 - w * 0.3)
                    elif emo == "dramatic":
                        pitch_shift = w * 0.8
                        time_stretch_rate = 1.0 - (w * 0.06)  # slightly slower for drama
                    elif emo in ("warm", "empathetic"):
                        pitch_shift = w * 0.4  # tiny pitch lift
                        time_stretch_rate = 1.0 - (w * 0.04)  # small slower
                    elif emo == "confident":
                        time_stretch_rate = 1.0 + (w * 0.05)  # slight speed lift

                    if abs(pitch_shift) > 0.05:
                        audio = librosa.effects.pitch_shift(y=audio, sr=sr, n_steps=pitch_shift)
                    if abs(time_stretch_rate - 1.0) > 0.02:
                        audio = librosa.effects.time_stretch(y=audio, rate=time_stretch_rate)

                    sf.write(output_path, audio, sr)
                    logger.info(
                        "Applied XTTS emotion macro for '%s' (pitch_shift=%.2f st, rate=%.2f, intensity=%d%%)",
                        emo,
                        pitch_shift,
                        time_stretch_rate,
                        emotion_intensity,
                    )
                except Exception as dsp_exc:
                    logger.warning("XTTS emotion post-processing skipped due to error: %s", dsp_exc)

            return Path(output_path)
        except Exception as exc:
            logger.exception("Voice cloning synthesis failed.")
            raise VoiceCloneError(f"Voice cloning failed: {exc}") from exc

    def health_check(self) -> dict:
        return {
            "is_loaded": self._is_loaded,
            "device": self.device,
            "model": self.MODEL_NAME,
        }