"""
services/api/routes/tts.py

TTS API routes for Valora AI.

Exposes speech synthesis, voice discovery, health, model, and metrics
endpoints under the `/tts` prefix, built on top of
`services/tts/inference.py`, `services/tts/preprocess.py`, and
`services/tts/config.py`.
"""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from services.api.limiter import limiter

from services.api.dependencies import get_inference_service, get_text_preprocessor
from services.api.schemas import (
    GenerateJSONResponse,
    GenerateRequest,
    HealthResponse,
    MetricsResponse,
    ModelInfoResponse,
    VoicesResponse,
)
from services.api.security import verify_api_key
from services.tts.config import settings
from services.tts.inference import (
    SynthesisRequest,
    TTSInferenceError,
    TTSInferenceService,
)
from services.tts.preprocess import TextPreprocessor, TextValidationError
from services.tts.utils import generate_unique_filename, get_gpu_info, get_logger

logger = get_logger("valora.api.routes.tts")

router = APIRouter(prefix="/tts", tags=["TTS"], dependencies=[Depends(verify_api_key)])

BARK_VOICE_PRESETS: List[str] = [
    "v2/en_speaker_0", "v2/en_speaker_1", "v2/en_speaker_2", "v2/en_speaker_3",
    "v2/en_speaker_4", "v2/en_speaker_5", "v2/en_speaker_6", "v2/en_speaker_7",
    "v2/en_speaker_8", "v2/en_speaker_9",
    "v2/hi_speaker_0", "v2/hi_speaker_1", "v2/hi_speaker_2", "v2/hi_speaker_3",
    "v2/hi_speaker_4", "v2/hi_speaker_5", "v2/hi_speaker_6", "v2/hi_speaker_7",
    "v2/hi_speaker_8", "v2/hi_speaker_9",
    "v2/fr_speaker_0", "v2/fr_speaker_1", "v2/fr_speaker_2", "v2/fr_speaker_3",
    "v2/fr_speaker_4", "v2/fr_speaker_5", "v2/fr_speaker_6", "v2/fr_speaker_7",
    "v2/fr_speaker_8", "v2/fr_speaker_9",
    "v2/ja_speaker_0", "v2/ja_speaker_1", "v2/ja_speaker_2", "v2/ja_speaker_3",
    "v2/ja_speaker_4", "v2/ja_speaker_5", "v2/ja_speaker_6", "v2/ja_speaker_7",
    "v2/ja_speaker_8", "v2/ja_speaker_9",
    "v2/es_speaker_0", "v2/es_speaker_1", "v2/es_speaker_2", "v2/es_speaker_3",
    "v2/es_speaker_4", "v2/es_speaker_5", "v2/es_speaker_6", "v2/es_speaker_7",
    "v2/es_speaker_8", "v2/es_speaker_9",
    "v2/en_in_speaker_0", "v2/en_in_speaker_1",
    "v2/ta_speaker_0", "v2/ta_speaker_1",
    "v2/te_speaker_0", "v2/te_speaker_1",
    "v2/mr_speaker_0", "v2/mr_speaker_1",
    "v2/bn_speaker_0", "v2/bn_speaker_1",
    "v2/gu_speaker_0", "v2/gu_speaker_1",
    "v2/kn_speaker_0", "v2/kn_speaker_1",
    "v2/ml_speaker_0", "v2/ml_speaker_1",
    "v2/pa_speaker_0", "v2/pa_speaker_1",
]

VOICE_LANGUAGE_MAP: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "fr": "French",
    "ja": "Japanese",
    "es": "Spanish",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
}


class _MetricsTracker:
    """
    Thread-safe in-memory tracker for basic request-serving metrics.

    Attributes:
        requests_served: Total number of successfully completed requests.
        total_latency_seconds: Cumulative latency across all requests.
        start_time: Monotonic timestamp when the tracker was created.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.requests_served: int = 0
        self.total_latency_seconds: float = 0.0
        self.start_time: float = time.monotonic()

    def record(self, latency_seconds: float) -> None:
        """
        Record a completed request's latency.

        Args:
            latency_seconds: Time taken to serve the request, in seconds.
        """
        with self._lock:
            self.requests_served += 1
            self.total_latency_seconds += latency_seconds

    def snapshot(self) -> Dict[str, float]:
        """
        Capture a consistent snapshot of current metrics.

        Returns:
            Dict[str, float]: Requests served, average latency, and
                uptime in seconds.
        """
        with self._lock:
            requests_served = self.requests_served
            total_latency = self.total_latency_seconds

        average_latency = (
            total_latency / requests_served if requests_served > 0 else 0.0
        )
        uptime = time.monotonic() - self.start_time

        return {
            "requests_served": requests_served,
            "average_latency_seconds": round(average_latency, 4),
            "uptime_seconds": round(uptime, 2),
        }


_metrics = _MetricsTracker()


def _preprocess_and_join(
    text: str, preprocessor: TextPreprocessor
) -> str:
    """
    Run text through the preprocessing pipeline and rejoin chunks into
    a single normalized string, since chunking is re-applied downstream
    by the inference service.

    Args:
        text: Raw input text.
        preprocessor: The text preprocessor instance.

    Returns:
        str: Normalized text ready for synthesis.

    Raises:
        HTTPException: If the text fails validation.
    """
    try:
        result = preprocessor.preprocess(text)
        return result.normalized_text
    except TextValidationError as exc:
        logger.warning("Text validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input text: {exc}",
        ) from exc


@router.post(
    "",
    summary="Generate speech (alias for /generate)",
    response_class=StreamingResponse,
    include_in_schema=False,
)
@router.post(
    "/generate",
    summary="Generate speech and stream WAV audio",
    response_class=StreamingResponse,
)
@limiter.limit("20/minute")
async def generate_speech(
    request: Request,
    response: Response,
    body: GenerateRequest,
    service: TTSInferenceService = Depends(get_inference_service),
    preprocessor: TextPreprocessor = Depends(get_text_preprocessor),
) -> StreamingResponse:
    """
    Synthesize speech from input text and stream the result as a WAV
    audio response.

    Args:
        request: FastAPI HTTP request (for rate limiting context).
        body: The synthesis request payload (text, voice preset,
            and optional generation parameters).
        service: Injected TTS inference service.
        preprocessor: Injected text preprocessor.

    Returns:
        StreamingResponse: WAV audio content with `audio/wav` media type.

    Raises:
        HTTPException: If validation fails (400) or synthesis fails (500).
    """
    normalized_text = _preprocess_and_join(body.text, preprocessor)

    synthesis_request = SynthesisRequest(
        text=normalized_text,
        voice_preset=body.voice_preset,
        max_new_tokens=body.max_new_tokens,
        language=body.language,
        age=body.age,
        pitch_semitones=body.pitch_semitones,
        emotion=body.emotion or "neutral",
        emotion_intensity=body.emotion_intensity if body.emotion_intensity is not None else 45,
        speed=body.speed,
    )

    try:
        response = await service.synthesize_async(synthesis_request)
    except TTSInferenceError as exc:
        logger.error("Speech generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech generation failed: {exc}",
        ) from exc

    _metrics.record(response.latency_seconds)

    filename = generate_unique_filename(prefix="valora_tts", extension="wav")
    audio_stream = io.BytesIO(response.audio_bytes)

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Audio-Duration-Seconds": f"{response.duration_seconds:.3f}",
        "X-Sample-Rate": str(response.sample_rate),
        "X-Latency-Seconds": f"{response.latency_seconds:.3f}",
        "X-Voice-Preset": response.voice_preset,
    }

    return StreamingResponse(audio_stream, media_type="audio/wav", headers=headers)


@router.post(
    "/generate-json",
    response_model=GenerateJSONResponse,
    summary="Generate speech and return metadata as JSON",
)
@limiter.limit("20/minute")
async def generate_speech_json(
    request: Request,
    response: Response,
    body: GenerateRequest,
    service: TTSInferenceService = Depends(get_inference_service),
    preprocessor: TextPreprocessor = Depends(get_text_preprocessor),
) -> GenerateJSONResponse:
    """
    Synthesize speech from input text and return structured metadata
    without embedding the raw audio bytes in the response body.

    Args:
        request: FastAPI HTTP request (for rate limiting context).
        body: The synthesis request payload.
        service: Injected TTS inference service.
        preprocessor: Injected text preprocessor.

    Returns:
        GenerateJSONResponse: Synthesis metadata (duration, sample rate,
            latency, voice preset, and a generated audio filename).

    Raises:
        HTTPException: If validation fails (400) or synthesis fails (500).
    """
    normalized_text = _preprocess_and_join(body.text, preprocessor)

    synthesis_request = SynthesisRequest(
        text=normalized_text,
        voice_preset=body.voice_preset,
        max_new_tokens=body.max_new_tokens,
        language=body.language,
        age=body.age,
        pitch_semitones=body.pitch_semitones,
        emotion=body.emotion or "neutral",
        emotion_intensity=body.emotion_intensity if body.emotion_intensity is not None else 45,
        speed=body.speed,
    )

    try:
        response = await service.synthesize_async(synthesis_request)
    except TTSInferenceError as exc:
        logger.error("Speech generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech generation failed: {exc}",
        ) from exc

    _metrics.record(response.latency_seconds)

    filename = generate_unique_filename(prefix="valora_tts", extension="wav")
    output_path = settings.OUTPUT_DIR / filename

    try:
        output_path.write_bytes(response.audio_bytes)
    except OSError as exc:
        logger.error("Failed to persist audio file '%s': %s", output_path, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist generated audio file.",
        ) from exc

    return GenerateJSONResponse(
        duration_seconds=response.duration_seconds,
        sample_rate=response.sample_rate,
        latency_seconds=response.latency_seconds,
        voice_preset=response.voice_preset,
        audio_filename=filename,
        chunk_count=response.chunk_count,
    )


VOICE_METADATA_LIST_FALLBACK: List[Dict[str, Any]] = [
    {"id": "indic_rohit", "name": "Rohit Verma (Hindi - AI4Bharat Indic)", "language": "Hindi (India)", "locale": "hi-IN", "gender": "Male", "age": "Adult", "tags": ["Neural", "Indic-Parler-TTS", "Conversational", "Hindi"]},
    {"id": "indic_divya", "name": "Divya Sharma (Hindi - AI4Bharat Indic)", "language": "Hindi (India)", "locale": "hi-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Indic-Parler-TTS", "Expressive", "Melodic", "Hindi"]},
    {"id": "indic_aman", "name": "Aman Kapoor (Hindi - AI4Bharat Indic)", "language": "Hindi (India)", "locale": "hi-IN", "gender": "Male", "age": "Adult", "tags": ["Neural", "Indic-Parler-TTS", "Cinematic", "Deep", "Hindi"]},
    {"id": "indic_rani", "name": "Rani Patel (Hindi - AI4Bharat Indic)", "language": "Hindi (India)", "locale": "hi-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Indic-Parler-TTS", "Storytelling", "Calm", "Hindi"]},
    {"id": "v2/hi_speaker_0", "name": "Swara (Hindi - Neural)", "language": "Hindi (India)", "locale": "hi-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Hindi", "Natural"]},
    {"id": "v2/hi_speaker_1", "name": "Madhur (Hindi - Neural)", "language": "Hindi (India)", "locale": "hi-IN", "gender": "Male", "age": "Adult", "tags": ["Neural", "Hindi", "Warm", "Baritone"]},
    {"id": "v2/en_speaker_6", "name": "Aria (US English)", "language": "English (US)", "locale": "en-US", "gender": "Female", "age": "Adult", "tags": ["Neural", "Clear", "Expressive"]},
    {"id": "v2/en_speaker_0", "name": "Guy (US English)", "language": "English (US)", "locale": "en-US", "gender": "Male", "age": "Adult", "tags": ["Neural", "Conversational", "Deep"]},
    {"id": "v2/en_speaker_1", "name": "Jenny (US English)", "language": "English (US)", "locale": "en-US", "gender": "Female", "age": "Adult", "tags": ["Neural", "Friendly", "Warm"]},
    {"id": "v2/en_speaker_2", "name": "Sonia (British English)", "language": "English (UK)", "locale": "en-GB", "gender": "Female", "age": "Adult", "tags": ["Neural", "British", "Formal"]},
    {"id": "v2/en_speaker_3", "name": "Ryan (British English)", "language": "English (UK)", "locale": "en-GB", "gender": "Male", "age": "Adult", "tags": ["Neural", "British", "Narrative"]},
    {"id": "v2/en_speaker_4", "name": "Natasha (Australian English)", "language": "English (AU)", "locale": "en-AU", "gender": "Female", "age": "Adult", "tags": ["Neural", "Australian", "Bright"]},
    {"id": "v2/en_speaker_5", "name": "Neerja (Indian English)", "language": "English (IN)", "locale": "en-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Indian Accent", "Smooth"]},
    {"id": "v2/en_in_speaker_1", "name": "Prabhat (Indian English)", "language": "English (IN)", "locale": "en-IN", "gender": "Male", "age": "Adult", "tags": ["Neural", "Indian Accent", "Confident"]},
    {"id": "v2/ta_speaker_0", "name": "Pallavi (Tamil)", "language": "Tamil", "locale": "ta-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Tamil", "Expressive"]},
    {"id": "v2/ta_speaker_1", "name": "Valluvar (Tamil)", "language": "Tamil", "locale": "ta-IN", "gender": "Male", "age": "Adult", "tags": ["Neural", "Tamil", "Authoritative"]},
    {"id": "v2/te_speaker_0", "name": "Shruti (Telugu)", "language": "Telugu", "locale": "te-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Telugu", "Melodic"]},
    {"id": "v2/te_speaker_1", "name": "Mohan (Telugu)", "language": "Telugu", "locale": "te-IN", "gender": "Male", "age": "Adult", "tags": ["Neural", "Telugu", "Deep"]},
    {"id": "v2/mr_speaker_0", "name": "Aarohi (Marathi)", "language": "Marathi", "locale": "mr-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Marathi", "Gentle"]},
    {"id": "v2/bn_speaker_0", "name": "Tanishaa (Bengali)", "language": "Bengali", "locale": "bn-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Bengali", "Lyrical"]},
    {"id": "v2/gu_speaker_0", "name": "Dhwani (Gujarati)", "language": "Gujarati", "locale": "gu-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Gujarati", "Crisp"]},
    {"id": "v2/kn_speaker_0", "name": "Sapna (Kannada)", "language": "Kannada", "locale": "kn-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Kannada", "Clear"]},
    {"id": "v2/ml_speaker_0", "name": "Sobhana (Malayalam)", "language": "Malayalam", "locale": "ml-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Malayalam", "Soft"]},
    {"id": "v2/ur_speaker_0", "name": "Gul (Urdu)", "language": "Urdu", "locale": "ur-IN", "gender": "Female", "age": "Adult", "tags": ["Neural", "Urdu", "Soft"]},
    {"id": "v2/ur_speaker_1", "name": "Salman (Urdu)", "language": "Urdu", "locale": "ur-IN", "gender": "Male", "age": "Adult", "tags": ["Neural", "Urdu", "Natural"]},
    {"id": "v2/pa_speaker_0", "name": "Ojas (Indian Accent)", "language": "Indian Accent", "locale": "pa-IN", "gender": "Male", "age": "Adult", "tags": ["Neural", "Energetic"]},
    {"id": "v2/fr_speaker_0", "name": "Denise (French)", "language": "French", "locale": "fr-FR", "gender": "Female", "age": "Adult", "tags": ["Neural", "French", "Elegant"]},
    {"id": "v2/fr_speaker_1", "name": "Henri (French)", "language": "French", "locale": "fr-FR", "gender": "Male", "age": "Adult", "tags": ["Neural", "French", "Classic"]},
    {"id": "v2/ja_speaker_0", "name": "Nanami (Japanese)", "language": "Japanese", "locale": "ja-JP", "gender": "Female", "age": "Adult", "tags": ["Neural", "Japanese", "Anime/Natural"]},
    {"id": "v2/ja_speaker_1", "name": "Keita (Japanese)", "language": "Japanese", "locale": "ja-JP", "gender": "Male", "age": "Adult", "tags": ["Neural", "Japanese", "Friendly"]},
    {"id": "v2/es_speaker_0", "name": "Elvira (Spanish)", "language": "Spanish", "locale": "es-ES", "gender": "Female", "age": "Adult", "tags": ["Neural", "Spanish", "Passionate"]},
    {"id": "v2/es_speaker_1", "name": "Alvaro (Spanish)", "language": "Spanish", "locale": "es-ES", "gender": "Male", "age": "Adult", "tags": ["Neural", "Spanish", "Rich"]},
]

CATALOG_PATH = Path(__file__).resolve().parents[2] / "tts" / "voice_catalog.json"


def _build_voice_metadata() -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Build full voice metadata list and language lookup map from voice_catalog.json.
    """
    if not CATALOG_PATH.exists():
        return VOICE_METADATA_LIST_FALLBACK, dict(VOICE_LANGUAGE_MAP)

    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        voices: List[Dict[str, Any]] = []
        languages: Dict[str, str] = dict(VOICE_LANGUAGE_MAP)

        for v in catalog:
            short_name = v.get("ShortName")
            locale = v.get("Locale", "")
            locale_name = v.get("LocaleName") or locale
            friendly_name = v.get("FriendlyName") or short_name
            gender = v.get("Gender", "Unknown")

            # Extract clean display name (e.g. Aria (English (United States)))
            parts = short_name.split("-")
            clean_name = parts[-1].replace("Neural", "") if len(parts) >= 3 else short_name
            display_name = f"{clean_name} ({locale_name})"

            lang_code = locale.split("-")[0].lower() if locale else "other"
            if locale and locale not in languages:
                languages[locale] = locale_name
            if lang_code and lang_code not in languages:
                languages[lang_code] = locale_name.split(" (")[0]

            tags = ["Neural", gender]
            if "VoiceTag" in v and isinstance(v["VoiceTag"], dict):
                tags.extend(v["VoiceTag"].get("VoicePersonalities", []))

            voices.append({
                "id": short_name,
                "name": display_name,
                "language": locale_name,
                "locale": locale,
                "gender": gender,
                "friendly_name": friendly_name,
                "tags": tags,
            })

        # Also prepend/append legacy presets so they appear in dropdowns
        for legacy in VOICE_METADATA_LIST_FALLBACK:
            if not any(item["id"] == legacy["id"] for item in voices):
                voices.insert(0, legacy)

        return voices, languages
    except Exception as exc:
        logger.warning("Failed to parse voice_catalog.json: %s", exc)
        return VOICE_METADATA_LIST_FALLBACK, dict(VOICE_LANGUAGE_MAP)


VOICE_METADATA_LIST, VOICE_LANGUAGES = _build_voice_metadata()


@router.get(
    "/voices",
    response_model=VoicesResponse,
    summary="List available voice presets",
)
async def list_voices() -> VoicesResponse:
    """
    List all available voice presets grouped by language, including
    gender, full locale, and friendly display name.

    Returns:
        VoicesResponse: All supported voice presets and their languages.
    """
    voices, languages = _build_voice_metadata()
    return VoicesResponse(
        voices=voices,
        languages=languages,
        default_voice_preset=settings.TTS_DEFAULT_VOICE_PRESET,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Report TTS inference health",
)
async def tts_health(
    service: TTSInferenceService = Depends(get_inference_service),
) -> HealthResponse:
    """
    Report the health status of the TTS inference service and its
    underlying model.

    Args:
        service: Injected TTS inference service.

    Returns:
        HealthResponse: Structured health information.

    Raises:
        HTTPException: If the health check itself fails unexpectedly.
    """
    try:
        model_health = service.health_check()
    except Exception as exc:
        logger.exception("TTS health check failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {exc}",
        ) from exc

    is_healthy = bool(model_health.get("is_loaded", False))

    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        is_loaded=is_healthy,
        device=model_health.get("device", "unknown"),
        sample_rate=model_health.get("sample_rate", 0),
    )


@router.get(
    "/model",
    response_model=ModelInfoResponse,
    summary="Report model and device information",
)
async def model_info(
    service: TTSInferenceService = Depends(get_inference_service),
) -> ModelInfoResponse:
    """
    Report details about the loaded TTS model and compute device.

    Args:
        service: Injected TTS inference service.

    Returns:
        ModelInfoResponse: Model name, CUDA availability, GPU name,
            sample rate, and load status.
    """
    model_health = service.health_check()
    gpu_info = get_gpu_info()

    cuda_available = bool(gpu_info.get("cuda_available", False))
    gpu_name = "N/A"
    if cuda_available:
        devices = gpu_info.get("devices") or []
        if devices:
            gpu_name = devices[0].get("name", "Unknown GPU")

    return ModelInfoResponse(
        model_name=model_health.get("model_name", settings.TTS_MODEL_NAME),
        cuda_available=cuda_available,
        gpu_name=gpu_name,
        sample_rate=model_health.get("sample_rate", 0),
        is_loaded=bool(model_health.get("is_loaded", False)),
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Report service metrics",
)
async def metrics(
    service: TTSInferenceService = Depends(get_inference_service),
) -> MetricsResponse:
    """
    Report operational metrics for the TTS service, including request
    volume, average latency, uptime, and model status.

    Args:
        service: Injected TTS inference service.

    Returns:
        MetricsResponse: Aggregated service metrics.
    """
    snapshot = _metrics.snapshot()
    model_health = service.health_check()

    return MetricsResponse(
        requests_served=snapshot["requests_served"],
        average_latency_seconds=snapshot["average_latency_seconds"],
        uptime_seconds=snapshot["uptime_seconds"],
        model_status="loaded" if model_health.get("is_loaded", False) else "not_loaded",
    )