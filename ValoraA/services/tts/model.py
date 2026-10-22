"""
services/tts/model.py

Production-grade Text-to-Speech (TTS) model wrapper for Valora AI.

This version uses Microsoft Edge's neural TTS voices (via the `edge-tts`
library) as the synthesis backend. This is a hosted-API backend, not a
local GPU model -- it requires no CUDA, no local model weights, and no
device placement, which eliminates the entire class of CUDA/CPU device
mismatch issues that local Bark inference was subject to.

This version also adds age-based (or manually specified) pitch shifting
via librosa, so a single synthesized voice can be made to sound younger
or older on demand -- a deterministic DSP transform, not a trained model,
so it works instantly with every voice/language edge-tts supports.

Public interface (class name, method signatures, exception types) is
kept backward compatible with the previous local-Bark implementation:
services/tts/inference.py and everything in services/api/ require NO
changes for existing calls; new `age`/`pitch_semitones` parameters are
additive and optional.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
from pathlib import Path
import subprocess
import threading
import wave
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
try:
    import librosa
except ImportError:
    librosa = None
import numpy as np

try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

try:
    import edge_tts
except ImportError as _import_exc:  # pragma: no cover
    edge_tts = None
    _EDGE_TTS_IMPORT_ERROR = _import_exc
else:
    _EDGE_TTS_IMPORT_ERROR = None

logger = logging.getLogger("valora.tts.model")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class TTSModelError(Exception):
    """Base exception for all TTS model related errors."""


class TTSModelLoadError(TTSModelError):
    """Raised when the TTS backend fails to initialize."""


class TTSSynthesisError(TTSModelError):
    """Raised when speech synthesis fails."""


class TTSDeviceMismatchError(TTSSynthesisError):
    """
    Kept for backward compatibility with callers that catch this
    exception type. Not raised by this hosted-API backend, since there
    is no local device placement involved.
    """


@dataclass(frozen=True)
class SynthesisResult:
    """
    Container for a synthesized speech result.

    Attributes:
        audio: 1-D numpy float32 array of waveform samples, range [-1, 1].
        sample_rate: Sample rate of the audio in Hz.
    """

    audio: np.ndarray
    sample_rate: int

    def to_wav_bytes(self) -> bytes:
        """
        Encode the audio waveform as WAV-formatted bytes.

        Uses Python's built-in `wave` module rather than torchaudio.save(),
        since newer torchaudio releases require the optional `torchcodec`
        backend for WAV encoding, which is not installed. The stdlib
        `wave` module needs no extra dependencies and is a natural fit
        here since we already have PCM sample data.

        Returns:
            bytes: In-memory WAV file content.

        Raises:
            TTSSynthesisError: If encoding fails.
        """
        try:
            # Convert float32 samples in [-1, 1] to 16-bit PCM integers.
            clipped = np.clip(self.audio, -1.0, 1.0)
            pcm_samples = (clipped * 32767.0).astype(np.int16)

            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit = 2 bytes per sample
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(pcm_samples.tobytes())

            buffer.seek(0)
            return buffer.read()
        except Exception as exc:
            raise TTSSynthesisError(f"Failed to encode audio to WAV: {exc}") from exc


def map_age_to_semitones(age: int) -> float:
    """
    Map a human age (in years) to a pitch-shift amount in semitones,
    used to make a synthesized voice sound younger or older.

    Args:
        age: Target apparent age, roughly 1-100.

    Returns:
        float: Semitone shift to apply (positive = higher/younger,
            negative = lower/older). 0.0 at age 28 (neutral baseline).
    """
    age = max(1, min(100, age))
    baseline_age = 28

    if age <= baseline_age:
        # Younger than baseline: shift up, capped at +9 semitones for
        # very young children.
        fraction = (baseline_age - age) / (baseline_age - 1)
        return fraction * 9.0

    # Older than baseline: shift down, capped at -7 semitones for
    # elderly voices.
    fraction = (age - baseline_age) / (100 - baseline_age)
    return -fraction * 7.0


# Indic-Parler-TTS presets and speakers
INDIC_PARLER_SPEAKERS: Dict[str, Dict[str, str]] = {
    "indic_rohit": {
        "speaker": "Rohit",
        "description": "Rohit speaks with an expressive, articulate tone at a steady pace with clean audio quality and natural Hindi pronunciation.",
        "gender": "Male",
        "name": "Rohit Verma (Hindi - AI4Bharat Indic)",
    },
    "indic_divya": {
        "speaker": "Divya",
        "description": "Divya speaks with a melodic, gentle and clear tone at a natural pace with clean audio and authentic Hindi pronunciation.",
        "gender": "Female",
        "name": "Divya Sharma (Hindi - AI4Bharat Indic)",
    },
    "indic_aman": {
        "speaker": "Aman",
        "description": "Aman speaks with a deep, authoritative, and confident baritone with clear pronunciation in Hindi.",
        "gender": "Male",
        "name": "Aman Kapoor (Hindi - AI4Bharat Indic)",
    },
    "indic_rani": {
        "speaker": "Rani",
        "description": "Rani speaks with a calm, warm and friendly narrative tone with pristine audio and natural Hindi cadence.",
        "gender": "Female",
        "name": "Rani Patel (Hindi - AI4Bharat Indic)",
    },
}


class _IndicParlerTTSManager:
    """
    Singleton manager for local AI4Bharat Indic-Parler-TTS model.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.model = None
        self.tokenizer = None
        self.desc_tokenizer = None
        self.device = None
        self.sampling_rate = 44100
        self._is_loaded = False

    @classmethod
    def get_instance(cls) -> _IndicParlerTTSManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def ensure_loaded(self) -> None:
        if self._is_loaded:
            return
        with self._lock:
            if self._is_loaded:
                return
            try:
                import torch
                from transformers import AutoTokenizer
                from parler_tts import ParlerTTSForConditionalGeneration

                model_dir = Path(__file__).resolve().parents[3] / "models" / "indic-parler-tts"
                if not model_dir.exists():
                    model_dir = Path(__file__).resolve().parents[2] / "models" / "indic-parler-tts"

                desc_tok_dir = model_dir / "description_tokenizer"

                if not model_dir.exists():
                    raise TTSModelLoadError(f"Indic-Parler-TTS model directory not found at {model_dir}")

                device = "cuda:0" if torch.cuda.is_available() else "cpu"
                self.device = device
                logger.info("Loading Indic-Parler-TTS model on %s...", device)

                self.model = ParlerTTSForConditionalGeneration.from_pretrained(
                    str(model_dir),
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                ).to(device)
                self.model.eval()

                self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
                desc_tok_path = str(desc_tok_dir) if desc_tok_dir.exists() else "google/flan-t5-large"
                self.desc_tokenizer = AutoTokenizer.from_pretrained(desc_tok_path)
                self.sampling_rate = getattr(self.model.config, "sampling_rate", 44100)
                self._is_loaded = True
                logger.info("Indic-Parler-TTS model loaded successfully (sr=%d, device=%s)", self.sampling_rate, device)
            except Exception as exc:
                logger.exception("Failed to load Indic-Parler-TTS model: %s", exc)
                raise TTSModelLoadError(f"Failed to load Indic-Parler-TTS model: {exc}") from exc

    def synthesize(self, text: str, preset: str, emotion: str = "neutral", speed: Optional[float] = None) -> np.ndarray:
        self.ensure_loaded()
        import torch

        speaker_info = INDIC_PARLER_SPEAKERS.get(preset, INDIC_PARLER_SPEAKERS["indic_rohit"])
        speaker_name = speaker_info["speaker"]
        base_desc = speaker_info["description"]

        emotion_phrase = f" with a {emotion} emotional style" if emotion and emotion != "neutral" else ""
        pace_phrase = f" at {speed:.1f}x pace" if speed and speed != 1.0 else " at a steady pace"
        full_desc = f"{speaker_name} speaks{emotion_phrase}{pace_phrase}. {base_desc}"

        desc_inputs = self.desc_tokenizer(full_desc, return_tensors="pt")
        input_ids = desc_inputs.input_ids.to(self.device)
        attention_mask = desc_inputs.attention_mask.to(self.device)

        prompt_inputs = self.tokenizer(text, return_tensors="pt")
        prompt_input_ids = prompt_inputs.input_ids.to(self.device)
        prompt_attention_mask = prompt_inputs.attention_mask.to(self.device)

        with torch.inference_mode():
            generation = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                prompt_input_ids=prompt_input_ids,
                prompt_attention_mask=prompt_attention_mask,
                do_sample=True,
                temperature=1.0,
                min_length=10,
            )

        audio_arr = generation.cpu().numpy().squeeze()
        if audio_arr.ndim > 1:
            audio_arr = audio_arr[0]

        max_val = np.max(np.abs(audio_arr))
        if max_val > 1.0:
            audio_arr = audio_arr / max_val * 0.98

        return audio_arr.astype(np.float32)


# Curated legacy list of high-quality Edge neural voices,
# preserving exact preset names for backward compatibility.
LEGACY_VOICE_PRESETS: Dict[str, str] = {
    # English -- various accents
    "v2/en_speaker_6": "en-US-AriaNeural",
    "v2/en_speaker_0": "en-US-GuyNeural",
    "v2/en_speaker_1": "en-US-JennyNeural",
    "v2/en_speaker_2": "en-GB-SoniaNeural",
    "v2/en_speaker_3": "en-GB-RyanNeural",
    "v2/en_speaker_4": "en-AU-NatashaNeural",
    "v2/en_speaker_5": "en-IN-NeerjaNeural",
    "v2/en_in_speaker_0": "en-IN-NeerjaNeural",
    "v2/en_in_speaker_1": "en-IN-PrabhatNeural",

    # Hindi (Indic-Parler-TTS & Edge neural)
    "indic_rohit": "hi-IN-MadhurNeural",
    "indic_divya": "hi-IN-SwaraNeural",
    "indic_aman": "hi-IN-MadhurNeural",
    "indic_rani": "hi-IN-SwaraNeural",
    "v2/hi_speaker_0": "hi-IN-SwaraNeural",
    "v2/hi_speaker_1": "hi-IN-MadhurNeural",
    "v2/hi_speaker_2": "hi-IN-SwaraNeural",
    "v2/hi_speaker_3": "hi-IN-MadhurNeural",

    # Other Indian languages
    "v2/ta_speaker_0": "ta-IN-PallaviNeural",
    "v2/ta_speaker_1": "ta-IN-ValluvarNeural",
    "v2/te_speaker_0": "te-IN-ShrutiNeural",
    "v2/te_speaker_1": "te-IN-MohanNeural",
    "v2/mr_speaker_0": "mr-IN-AarohiNeural",
    "v2/mr_speaker_1": "mr-IN-ManoharNeural",
    "v2/bn_speaker_0": "bn-IN-TanishaaNeural",
    "v2/bn_speaker_1": "bn-IN-BashkarNeural",
    "v2/gu_speaker_0": "gu-IN-DhwaniNeural",
    "v2/gu_speaker_1": "gu-IN-NiranjanNeural",
    "kn-IN-SapnaNeural": "kn-IN-SapnaNeural",
    "v2/kn_speaker_0": "kn-IN-SapnaNeural",
    "v2/kn_speaker_1": "kn-IN-GaganNeural",
    "v2/ml_speaker_0": "ml-IN-SobhanaNeural",
    "v2/ml_speaker_1": "ml-IN-MidhunNeural",
    "v2/ur_speaker_0": "ur-IN-GulNeural",
    "v2/ur_speaker_1": "ur-IN-SalmanNeural",
    "v2/pa_speaker_0": "ur-IN-SalmanNeural",
    "v2/pa_speaker_1": "ur-IN-GulNeural",

    # French
    "v2/fr_speaker_0": "fr-FR-DeniseNeural",
    "v2/fr_speaker_1": "fr-FR-HenriNeural",

    # Japanese
    "v2/ja_speaker_0": "ja-JP-NanamiNeural",
    "v2/ja_speaker_1": "ja-JP-KeitaNeural",

    # Spanish
    "v2/es_speaker_0": "es-ES-ElviraNeural",
    "v2/es_speaker_1": "es-ES-AlvaroNeural",
}


VOICE_CATALOG_PATH = Path(__file__).resolve().parent / "voice_catalog.json"


def load_voice_presets() -> Dict[str, str]:
    """
    Load the complete voice preset dictionary combining legacy aliases
    and the dynamic catalog from voice_catalog.json.
    """
    presets = dict(LEGACY_VOICE_PRESETS)

    if not VOICE_CATALOG_PATH.exists():
        return presets

    try:
        with open(VOICE_CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        lang_counts: Dict[str, int] = {}
        for item in catalog:
            short_name = item.get("ShortName")
            locale = item.get("Locale", "")
            if not short_name:
                continue

            # Allow direct lookup by ShortName
            presets[short_name] = short_name

            # Generate auto-indexed aliases per language e.g. v2/de_speaker_0
            lang_code = locale.split("-")[0].lower() if locale else "voice"
            idx = lang_counts.get(lang_code, 0)
            
            # Find next available index that doesn't conflict with legacy presets
            while f"v2/{lang_code}_speaker_{idx}" in LEGACY_VOICE_PRESETS:
                idx += 1
                
            alias = f"v2/{lang_code}_speaker_{idx}"
            if alias not in presets:
                presets[alias] = short_name
            lang_counts[lang_code] = idx + 1
    except Exception as exc:
        logger.warning("Failed to load voice_catalog.json: %s", exc)

    return presets


VOICE_PRESETS: Dict[str, str] = load_voice_presets()


class TextToSpeechModel:
    """
    Reusable, production-ready wrapper around Microsoft Edge's neural
    TTS voices for the Valora AI voice platform.

    This class handles:
        - Async-to-sync bridging (edge_tts is asyncio-native; our
          synthesize() interface is synchronous, matching the previous
          local-model contract used throughout the codebase).
        - Voice preset resolution (maps Bark-style preset names used
          elsewhere in the codebase, e.g. "v2/en_speaker_6", to Edge
          neural voice names, e.g. "en-US-AriaNeural").
        - MP3 -> WAV/PCM conversion via pydub+ffmpeg, since edge_tts
          returns MP3-encoded audio and the rest of the pipeline
          (SynthesisResult, WAV streaming) expects a numpy waveform.
        - Age-based or manual pitch shifting via librosa, so any voice
          can be made to sound younger or older on demand.
        - Robust error handling and structured logging.

    Example:
        tts = TextToSpeechModel()
        tts.load()
        result = tts.synthesize("Hello, welcome to Valora AI.", age=10)
        wav_bytes = result.to_wav_bytes()
    """

    DEFAULT_MODEL_NAME: str = "edge-tts"
    DEFAULT_VOICE_PRESET: str = "v2/en_speaker_6"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: Optional[str] = None,
        use_fp16: bool = True,
    ) -> None:
        """
        Initialize the TTS model wrapper.

        Args:
            model_name: Kept for interface compatibility; unused (no
                local model weights are loaded for this backend).
            device: Kept for interface compatibility; unused (synthesis
                happens via a remote API call, not local compute).
            use_fp16: Kept for interface compatibility; unused.
        """
        self.model_name: str = model_name
        # Kept as attributes so health_check()/callers that read
        # `.device` don't break; always reports "api" since there is no
        # local compute device involved in this backend.
        self.device: str = "api"
        self.use_fp16: bool = False

        self._sample_rate: int = 24000
        self._is_loaded: bool = False
        self._load_lock = threading.Lock()

        logger.info("TextToSpeechModel initialized (backend=edge-tts, model=%s)", self.model_name)

    @property
    def is_loaded(self) -> bool:
        """Whether the TTS backend has been verified available."""
        return self._is_loaded

    @property
    def sample_rate(self) -> int:
        """Sample rate (Hz) of audio produced by this backend."""
        return self._sample_rate

    def load(self) -> None:
        """
        Verify the edge-tts backend is available. No model weights are
        downloaded or loaded -- this simply confirms the `edge_tts`
        package is importable and the async bridge functions correctly.

        Raises:
            TTSModelLoadError: If the edge_tts package is unavailable or
                a connectivity check fails.
        """
        if self._is_loaded:
            logger.debug("Backend already verified; skipping re-check.")
            return

        with self._load_lock:
            if self._is_loaded:
                return

            logger.info("Initializing TTS backend 'edge-tts'...")

            if edge_tts is None:
                raise TTSModelLoadError(
                    f"edge_tts package is not installed: {_EDGE_TTS_IMPORT_ERROR}. "
                    f"Install it with: pip install edge-tts"
                )

            try:
                # Lightweight connectivity check: synthesize one short
                # word and confirm we get audio bytes back.
                self._run_async(self._synthesize_mp3("Ready.", VOICE_PRESETS[self.DEFAULT_VOICE_PRESET]))
                self._is_loaded = True
                logger.info(
                    "TTS backend 'edge-tts' verified successfully (sample_rate=%d Hz).",
                    self._sample_rate,
                )
            except Exception as exc:
                self._is_loaded = False
                logger.exception("Failed to verify TTS backend 'edge-tts'.")
                raise TTSModelLoadError(f"Failed to initialize edge-tts backend: {exc}") from exc

    def unload(self) -> None:
        """
        Reset the backend's loaded state. No local resources to release
        for this API-based backend, but kept for interface compatibility.
        """
        with self._load_lock:
            self._is_loaded = False
            logger.info("TTS backend 'edge-tts' marked as unloaded.")

    @staticmethod
    def _run_async(coro):
        """
        Run an async coroutine from synchronous code, safely, even when
        called from a thread that already has a running event loop (as
        is the case when this is invoked from within FastAPI's async
        lifespan/startup handler, which runs on uvicorn's event-loop
        thread).

        WHY A SEPARATE THREAD: asyncio tracks "is a loop currently
        running" per OS thread, not per loop object. If the calling
        thread already has a running loop (e.g. uvicorn's loop during
        startup), neither asyncio.run() nor loop.run_until_complete()
        can start a second loop on that same thread -- both raise
        RuntimeError regardless of which loop instance is used. Running
        the coroutine on a brand-new thread (which has no loop of its
        own) avoids this conflict entirely, at the cost of a small
        thread-creation overhead per call.

        Args:
            coro: The coroutine to run to completion.

        Returns:
            Any: The coroutine's return value.

        Raises:
            Exception: Re-raises whatever exception the coroutine itself
                raised, preserving the original traceback context.
        """
        result_box: dict = {}

        def _runner() -> None:
            try:
                result_box["result"] = asyncio.run(coro)
            except BaseException as exc:  # noqa: BLE001
                result_box["error"] = exc

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        thread.join()

        if "error" in result_box:
            raise result_box["error"]
        return result_box.get("result")

    _unsupported_styles: set[tuple[str, str]] = set()

    @staticmethod
    async def _collect_stream_audio(communicator: edge_tts.Communicate) -> bytes:
        """Helper to collect and return raw audio bytes from edge_tts communicator stream."""
        audio_chunks = bytearray()
        async for chunk in communicator.stream():
            if chunk.get("type") == "audio":
                audio_chunks.extend(chunk.get("data", b""))
        return bytes(audio_chunks)

    @staticmethod
    def _mp3_to_pcm(mp3_bytes: bytes, sample_rate: int = 24000) -> np.ndarray:
        """Decode MP3 bytes to float32 PCM numpy array [-1, 1] using ffmpeg or pydub."""
        try:
            process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-v", "error",
                    "-i", "pipe:0",
                    "-f", "s16le",
                    "-ac", "1",
                    "-ar", str(sample_rate),
                    "pipe:1",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            out, err = process.communicate(input=mp3_bytes)
            if process.returncode == 0 and out:
                return np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception as exc:
            logger.debug("Direct ffmpeg pipe decoding encountered: %s; trying pydub...", exc)

        if AudioSegment is not None:
            segment = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
            segment = segment.set_channels(1).set_frame_rate(sample_rate)
            samples = np.array(segment.get_array_of_samples(), dtype=np.float32)
            return samples / 32768.0

        raise TTSSynthesisError("Failed to decode MP3 audio to PCM samples.")

    @classmethod
    async def _synthesize_mp3(
        cls,
        text: str,
        edge_voice: str,
        emotion: str = "neutral",
        emotion_intensity: int = 45,
        speed: Optional[float] = None,
    ) -> bytes:
        """
        Call the edge-tts API directly with clean plain text and prosody rate parameter.

        Args:
            text: Text to synthesize.
            edge_voice: Edge neural voice identifier (e.g. 'en-US-AriaNeural').
            emotion: Emotion name ('neutral', 'warm', 'cheerful', etc.).
            emotion_intensity: Intensity percentage (0..100).
            speed: Optional playback speed multiplier.

        Returns:
            bytes: Raw MP3-encoded audio.

        Raises:
            TTSSynthesisError: If no audio data is returned after all attempts.
        """
        from services.tts.edge_ssml import rate_to_prosody_str

        rate_str = rate_to_prosody_str(speed)

        # Primary synthesis with requested voice and rate
        try:
            communicator = edge_tts.Communicate(text=text, voice=edge_voice, rate=rate_str)
            audio = await cls._collect_stream_audio(communicator)
            if audio:
                return audio
        except Exception as exc:
            logger.warning(
                "edge-tts synthesis failed for voice '%s' (rate=%s): %s. Retrying with default voice...",
                edge_voice,
                rate_str,
                exc,
            )

        # Fallback to default voice
        default_voice = VOICE_PRESETS.get(cls.DEFAULT_VOICE_PRESET, "en-US-AriaNeural")
        if edge_voice != default_voice:
            try:
                communicator = edge_tts.Communicate(text=text, voice=default_voice, rate=rate_str)
                audio = await cls._collect_stream_audio(communicator)
                if audio:
                    return audio
            except Exception as exc:
                logger.error("Fallback synthesis with default voice '%s' also failed: %s", default_voice, exc)

        raise TTSSynthesisError(
            f"edge-tts returned no audio data for voice '{edge_voice}'."
        )

    def _resolve_voice(self, preset: str) -> str:
        """
        Resolve a Bark-style voice preset name to an Edge neural voice
        identifier, falling back to the default voice with a warning if
        the preset is unrecognized.

        Args:
            preset: Voice preset identifier (e.g. 'v2/en_speaker_6').

        Returns:
            str: The corresponding Edge neural voice name.
        """
        if preset in VOICE_PRESETS:
            return VOICE_PRESETS[preset]

        logger.warning(
            "Unrecognized voice preset '%s'; falling back to default preset '%s'.",
            preset,
            self.DEFAULT_VOICE_PRESET,
        )
        return VOICE_PRESETS[self.DEFAULT_VOICE_PRESET]

    def synthesize(
        self,
        text: str,
        voice_preset: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        age: Optional[int] = None,
        pitch_semitones: Optional[float] = None,
        emotion: str = "neutral",
        emotion_intensity: int = 45,
        speed: Optional[float] = None,
    ) -> SynthesisResult:
        """
        Synthesize speech audio from input text using edge-tts with SSML emotion styling.

        Args:
            text: The input text to convert to speech. Must be non-empty.
            voice_preset: Optional voice preset identifier (Bark-style
                naming, e.g. 'v2/en_speaker_6'). Falls back to the
                default preset if not provided or unrecognized.
            max_new_tokens: Unused for this backend (kept for interface
                compatibility with local-model callers).
            age: Optional target apparent age (1-100). If provided, the
                synthesized voice's pitch is shifted to sound younger or
                older, via map_age_to_semitones(). Ignored if
                pitch_semitones is also provided.
            pitch_semitones: Optional direct pitch shift in semitones,
                for advanced/manual control. Takes precedence over `age`
                if both are provided.
            emotion: Emotion name ('neutral', 'warm', 'cheerful', etc.).
            emotion_intensity: Intensity percentage (0-100).
            speed: Optional playback speed multiplier (e.g. 0.5 to 2.0).

        Returns:
            SynthesisResult: Waveform and sample rate of the generated speech.

        Raises:
            ValueError: If the input text is empty or invalid.
            TTSModelLoadError: If the backend is not loaded and auto-load fails.
            TTSSynthesisError: If synthesis fails for any reason.
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input 'text' must be a non-empty string.")

        if not self._is_loaded:
            logger.warning("Backend not loaded prior to synthesize(); loading now.")
            self.load()

        preset = voice_preset or self.DEFAULT_VOICE_PRESET

        # Check if requested preset is an AI4Bharat Indic-Parler-TTS voice
        if preset in INDIC_PARLER_SPEAKERS or preset.startswith("indic_"):
            try:
                manager = _IndicParlerTTSManager.get_instance()
                samples = manager.synthesize(text=text, preset=preset, emotion=emotion, speed=speed)
                sr = manager.sampling_rate

                shift_semitones = pitch_semitones if pitch_semitones is not None else (
                    map_age_to_semitones(age) if age is not None else None
                )
                if shift_semitones is not None and abs(shift_semitones) > 0.01 and librosa is not None:
                    samples = librosa.effects.pitch_shift(y=samples, sr=sr, n_steps=shift_semitones)

                logger.info(
                    "Synthesized %.2f seconds with Indic-Parler-TTS for preset %s (sr=%d Hz).",
                    len(samples) / float(sr),
                    preset,
                    sr,
                )
                return SynthesisResult(audio=samples.astype(np.float32), sample_rate=sr)
            except Exception as exc:
                logger.warning(
                    "Indic-Parler-TTS synthesis failed (%s), falling back to Edge neural Hindi voice: %s",
                    preset,
                    exc,
                )
                is_female = INDIC_PARLER_SPEAKERS.get(preset, {}).get("gender") == "Female"
                preset = "hi-IN-SwaraNeural" if is_female else "hi-IN-MadhurNeural"

        edge_voice = self._resolve_voice(preset)

        try:
            mp3_bytes = self._run_async(
                self._synthesize_mp3(
                    text=text,
                    edge_voice=edge_voice,
                    emotion=emotion,
                    emotion_intensity=emotion_intensity,
                    speed=speed,
                )
            )

            # Convert MP3 -> PCM waveform via ffmpeg or pydub
            samples = self._mp3_to_pcm(mp3_bytes, self._sample_rate)

            # Apply age-based (or manual) pitch shifting, if requested.
            # This is a deterministic DSP transform (librosa's phase-vocoder
            # based pitch shift), not a neural model -- it works instantly
            # on any voice/language edge-tts produces, with no training
            # and no GPU required.
            shift_semitones = pitch_semitones if pitch_semitones is not None else (
                map_age_to_semitones(age) if age is not None else None
            )
            if shift_semitones is not None and abs(shift_semitones) > 0.01:
                if librosa is not None:
                    samples = librosa.effects.pitch_shift(
                        y=samples,
                        sr=self._sample_rate,
                        n_steps=shift_semitones,
                    )
                    logger.info("Applied pitch shift of %.2f semitones (age=%s).", shift_semitones, age)
                else:
                    logger.warning("librosa is not installed; skipping pitch shift.")

            logger.info(
                "Synthesized %.2f seconds of audio for text of length %d chars (voice=%s, emotion=%s, intensity=%d).",
                len(samples) / float(self._sample_rate),
                len(text),
                edge_voice,
                emotion,
                emotion_intensity,
            )

            return SynthesisResult(audio=samples.astype(np.float32), sample_rate=self._sample_rate)

        except (ValueError, TTSModelLoadError):
            raise
        except Exception as exc:
            logger.exception("TTS synthesis failed for input text of length %d.", len(text))
            raise TTSSynthesisError(f"TTS synthesis failed: {exc}") from exc

    def synthesize_to_wav_bytes(
        self,
        text: str,
        voice_preset: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        age: Optional[int] = None,
        pitch_semitones: Optional[float] = None,
        emotion: str = "neutral",
        emotion_intensity: int = 45,
        speed: Optional[float] = None,
    ) -> bytes:
        """
        Convenience method: synthesize speech and return WAV-encoded bytes.

        Args:
            text: The input text to convert to speech.
            voice_preset: Optional voice preset identifier.
            max_new_tokens: Unused for this backend.
            age: Optional target apparent age (1-100) for pitch shifting.
            pitch_semitones: Optional direct pitch shift in semitones.
            emotion: Emotion name ('neutral', 'warm', etc.).
            emotion_intensity: Intensity percentage (0-100).
            speed: Optional playback speed multiplier.

        Returns:
            bytes: WAV-encoded audio content.
        """
        result = self.synthesize(
            text=text,
            voice_preset=voice_preset,
            max_new_tokens=max_new_tokens,
            age=age,
            pitch_semitones=pitch_semitones,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            speed=speed,
        )
        return result.to_wav_bytes()

    def health_check(self) -> dict:
        """
        Report the current health/status of the TTS backend.

        Returns:
            dict: Status information suitable for a FastAPI health endpoint.
        """
        return {
            "model_name": self.model_name,
            "is_loaded": self._is_loaded,
            "device": self.device,
            "cuda_available": False,
            "sample_rate": self._sample_rate,
            "backend": "edge-tts (hosted)",
        }

    def __repr__(self) -> str:
        return f"TextToSpeechModel(backend='edge-tts', is_loaded={self._is_loaded})"