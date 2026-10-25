"""
services/api/routes/translator.py

FastAPI routes for Live Voice & Multilingual Translation in Valora AI.
Provides language capability queries, real-time text translation, spoken voice
synthesis streaming, and speech recognition fallback.
"""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse, Response as FastAPIResponse, StreamingResponse
from pydantic import BaseModel, Field

try:
    from services.translator.engine import get_translation_engine
    from services.translator.languages import (
        ALL_LANGUAGES,
        get_language_capability,
        list_language_capabilities,
    )
    from services.translator.tts_stream import get_spoken_voice_engine
except ImportError:
    from ValoraA.services.translator.engine import get_translation_engine
    from ValoraA.services.translator.languages import (
        ALL_LANGUAGES,
        get_language_capability,
        list_language_capabilities,
    )
    from ValoraA.services.translator.tts_stream import get_spoken_voice_engine

logger = logging.getLogger("valora.api.translator")

router = APIRouter(prefix="/translator", tags=["Live Translator"])


# =============================================================================
# SCHEMAS
# =============================================================================
class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Speech text to translate")
    source_lang: str = Field("auto", description="Source language code (e.g. 'hi', 'en', 'auto')")
    target_lang: str = Field("en", description="Target language code (e.g. 'ta', 'te', 'es')")
    segment_id: Optional[str] = Field(None, description="Client segment tracker to prevent duplicates")


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Translated text to speak")
    target_lang: Optional[str] = Field("en", description="Target language code for voice resolution")
    lang: Optional[str] = Field(None, description="Alias for target_lang")
    voice: Optional[str] = Field(None, description="Specific neural voice identifier (optional)")
    speed: Optional[float] = Field(1.0, description="Playback speed (0.5 to 2.0)")
    rate_pct: int = Field(0, ge=-50, le=100, description="Speech rate adjustment (-50% to +100%)")
    pitch_hz: int = Field(0, ge=-50, le=50, description="Pitch shift in Hz (-50Hz to +50Hz)")


# =============================================================================
# ROUTES
# =============================================================================
@router.get("/languages", response_class=JSONResponse)
async def get_supported_languages() -> Dict[str, Any]:
    """
    Return all verified Indian regional and global language capabilities,
    including locales, native scripts, writing direction, and neural voices.
    """
    caps = list_language_capabilities()
    all_list = caps.get("indian", []) + caps.get("global", [])
    return {
        "success": True,
        "languages": all_list,
        "categories": caps,
        "indian": caps.get("indian", []),
        "global": caps.get("global", []),
        "total_languages": len(all_list),
        "count": len(all_list),
        "indian_languages_count": len(caps.get("indian", [])),
        "global_languages_count": len(caps.get("global", [])),
    }


@router.post("/translate", response_class=JSONResponse)
async def translate_text(req: TranslateRequest) -> Dict[str, Any]:
    """
    Translate live spoken dialogue from source language to target language.
    Preserves original native script and text layout.
    """
    engine = get_translation_engine()
    res = engine.translate(
        text=req.text,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
    )

    # Resolve target script direction (LTR vs RTL)
    tgt_cap = get_language_capability(req.target_lang)
    direction = tgt_cap.direction if tgt_cap else "ltr"

    return {
        "success": True,
        "segment_id": req.segment_id,
        "original_text": req.text,
        "translated_text": res["translated_text"],
        "source_lang": res["source_lang"],
        "target_lang": res["target_lang"],
        "detected_lang": res["detected_lang"],
        "direction": direction,
        "latency_ms": res["latency_ms"],
        "cached": res["cached"],
    }


@router.get("/speak")
async def stream_spoken_translation(
    text: str,
    target_lang: Optional[str] = "en",
    lang: Optional[str] = None,
    voice: Optional[str] = None,
    speed: Optional[float] = 1.0,
):
    """
    Direct streaming GET endpoint for HTML5 Audio playback.
    Synthesizes and streams audio/mpeg binary in real time.
    """
    resolved_lang = lang or target_lang or "en"
    effective_rate = int((speed - 1.0) * 100) if speed else 0

    voice_engine = get_spoken_voice_engine()
    try:
        audio_bytes, voice_used = await voice_engine.synthesize(
            text=text,
            target_lang=resolved_lang,
            voice=voice,
            rate_pct=effective_rate,
            pitch_hz=0,
        )

        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio generated.")

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "X-Voice-Used": voice_used,
                "Cache-Control": "public, max-age=86400",
            },
        )
    except Exception as exc:
        logger.error("TTS spoken voice synthesis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis error: {exc}",
        )


@router.post("/speak")
async def speak_translation(req: SpeakRequest):
    """
    Synthesize translated text into spoken audio in the selected regional voice.
    Returns audio_url for streaming or direct audio/mpeg bytes.
    """
    resolved_lang = req.lang or req.target_lang or "en"
    rate = req.rate_pct
    if req.speed and req.speed != 1.0 and not req.rate_pct:
        rate = int((req.speed - 1.0) * 100)

    voice_engine = get_spoken_voice_engine()
    try:
        audio_bytes, voice_used = await voice_engine.synthesize(
            text=req.text,
            target_lang=resolved_lang,
            voice=req.voice,
            rate_pct=rate,
            pitch_hz=req.pitch_hz,
        )

        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Text was empty or failed to generate audio.")

        import urllib.parse
        encoded_text = urllib.parse.quote(req.text)
        audio_url = f"/api/translator/speak?text={encoded_text}&target_lang={resolved_lang}"
        if req.voice:
            audio_url += f"&voice={urllib.parse.quote(req.voice)}"
        if req.speed:
            audio_url += f"&speed={req.speed}"

        return JSONResponse({
            "success": True,
            "audio_url": audio_url,
            "voice_used": voice_used,
            "mime_type": "audio/mpeg",
            "bytes_length": len(audio_bytes),
        })
    except Exception as exc:
        logger.error("TTS spoken voice synthesis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis error: {exc}",
        )


@router.post("/transcribe", response_class=JSONResponse)
async def transcribe_audio_chunk(
    file: UploadFile = File(...),
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fallback server-side speech recognition for browsers without Web Speech API.
    """
    try:
        from services.stt.inference import get_stt_service
    except ImportError:
        from ValoraA.services.stt.inference import get_stt_service

    service = get_stt_service()
    audio_bytes = await file.read()

    try:
        result = service.transcribe(audio_bytes, language=language)
        return {
            "success": True,
            "text": result.text,
            "language": result.language,
            "language_probability": result.language_probability,
        }
    except Exception as exc:
        logger.warning("Server-side transcription fallback error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {exc}",
        )
