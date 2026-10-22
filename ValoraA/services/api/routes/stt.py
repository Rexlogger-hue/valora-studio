"""
services/api/routes/stt.py

Speech-to-Text API routes for Valora AI.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status

from services.api.limiter import limiter
from services.api.security import verify_api_key
from services.stt.inference import get_stt_service
from services.stt.model import STTModelLoadError, STTTranscriptionError

router = APIRouter(prefix="/stt", tags=["STT"], dependencies=[Depends(verify_api_key)])


@router.post(
    "",
    summary="Transcribe uploaded audio to text (alias for /transcribe)",
    include_in_schema=False,
)
@router.post("/transcribe", summary="Transcribe uploaded audio to text")
@limiter.limit("15/minute")
async def transcribe_audio(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    language: Optional[str] = None
):
    """
    Transcribe an uploaded audio file to text.

    Args:
        file: Uploaded audio file (wav, mp3, m4a, etc).
        language: Optional ISO language code to force (e.g. 'en', 'hi').
            Auto-detected if omitted.

    Returns:
        JSON with transcribed text, detected language, and segments.
    """
    service = get_stt_service()
    audio_bytes = await file.read()

    try:
        result = service.transcribe(audio_bytes, language=language)
    except STTModelLoadError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except STTTranscriptionError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return {
        "text": result.text,
        "language": result.language,
        "language_probability": result.language_probability,
        "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in result.segments],
    }


@router.get("/health", summary="STT service health")
async def stt_health():
    return get_stt_service().health_check()