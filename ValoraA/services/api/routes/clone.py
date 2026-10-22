"""
services/api/routes/clone.py

Voice cloning API routes for Valora AI (XTTS-v2 based, optional feature).
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import FileResponse

from services.api.limiter import limiter
from services.api.security import verify_api_key
from services.tts.clone_model import VoiceCloneError
from services.tts.inference import get_voice_clone_service
from services.tts.voice_library import VoiceLibrary, get_voice_library

router = APIRouter(prefix="/tts", tags=["Voice Cloning"], dependencies=[Depends(verify_api_key)])

CONSENT_REQUIRED_MESSAGE = "You must confirm you have the right to use this voice recording before it can be saved."


@router.post("/voices/library", summary="Save a reference voice to the local library")
@limiter.limit("10/minute")
async def add_library_voice(
    request: Request,
    response: Response,
    display_name: str = Form(...),
    language: str = Form(default="en"),
    consent_confirmed: bool = Form(...),
    audio: UploadFile = File(...),
    library: VoiceLibrary = Depends(get_voice_library),
):
    """
    Upload and save a reference audio recording to the local Voice Library.

    Requires explicit confirmation of usage rights (consent_confirmed=True).
    Audio duration must be between 5 and 90 seconds.
    """
    if not consent_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=CONSENT_REQUIRED_MESSAGE,
        )

    audio_bytes = await audio.read()
    try:
        entry = await asyncio.to_thread(
            library.add_voice,
            display_name=display_name,
            language=language,
            audio_bytes=audio_bytes,
            consent_confirmed=consent_confirmed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "slug": entry["slug"],
        "display_name": entry["display_name"],
        "language": entry["language"],
        "duration_seconds": entry["duration_seconds"],
        "added_at": entry["added_at"],
    }


@router.get("/voices/library", summary="List all saved voices in the library")
async def list_library_voices(
    library: VoiceLibrary = Depends(get_voice_library),
) -> List[Dict[str, Any]]:
    """
    List all reference voices currently stored in the local Voice Library.
    """
    voices = await asyncio.to_thread(library.list_voices)
    return [
        {
            "slug": v["slug"],
            "display_name": v["display_name"],
            "language": v["language"],
            "duration_seconds": v["duration_seconds"],
            "added_at": v["added_at"],
        }
        for v in voices
    ]


@router.delete("/voices/library/{slug}", summary="Delete a voice from the library")
async def delete_library_voice(
    slug: str,
    library: VoiceLibrary = Depends(get_voice_library),
):
    """
    Delete a saved reference voice from the local Voice Library.
    """
    deleted = await asyncio.to_thread(library.delete_voice, slug)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice with slug '{slug}' not found in library.",
        )
    return {"status": "deleted", "slug": slug}


@router.post("/clone", summary="Clone a voice from reference audio and synthesize speech")
@limiter.limit("5/minute")
async def clone_voice(
    request: Request,
    response: Response,
    text: str = Form(...),
    language: str = Form(default="en"),
    emotion: str = Form(default="neutral"),
    emotion_intensity: int = Form(default=45),
    reference_audio: Optional[UploadFile] = File(default=None),
    voice_slug: Optional[str] = Form(default=None),
    library: VoiceLibrary = Depends(get_voice_library),
):
    """
    Synthesize speech in the voice of an uploaded reference audio clip
    OR a previously saved voice from the local voice library (voice_slug).

    Args:
        text: Text to synthesize in the cloned voice.
        language: ISO language code (e.g. 'en', 'hi', 'fr').
        emotion: Optional emotion style ('neutral', 'warm', 'cheerful', etc.).
        emotion_intensity: Optional emotion intensity (0..100, default 45).
        reference_audio: Optional 5-90s clean audio sample of the voice to clone.
        voice_slug: Optional slug of a saved voice in the library.

    Returns:
        FileResponse: The generated WAV audio.
    """
    if not reference_audio and not voice_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'reference_audio' file or 'voice_slug' must be provided.",
        )

    service = get_voice_clone_service()
    temp_ref_path: Optional[str] = None

    if voice_slug:
        voice_path = await asyncio.to_thread(library.get_voice_path, voice_slug)
        if not voice_path or not voice_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Voice '{voice_slug}' not found in voice library.",
            )
        ref_path = str(voice_path)
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as ref_file:
            ref_file.write(await reference_audio.read())
            temp_ref_path = ref_file.name
        ref_path = temp_ref_path

    output_path = tempfile.mktemp(suffix=".wav")

    try:
        await asyncio.to_thread(
            service.clone_to_file,
            text=text,
            speaker_wav_path=ref_path,
            output_path=output_path,
            language=language,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
        )
    except VoiceCloneError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        if temp_ref_path:
            Path(temp_ref_path).unlink(missing_ok=True)

    return FileResponse(output_path, media_type="audio/wav", filename="cloned_voice.wav")


@router.get("/clone/health", summary="Voice cloning service health")
async def clone_health():
    return get_voice_clone_service().health_check()