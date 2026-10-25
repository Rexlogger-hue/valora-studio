"""
services/api/routes/enhancer.py

FastAPI router for the Valora AI Voice Enhancement engine.
Provides endpoints for media upload, preset configuration, acoustic preview,
synchronous/asynchronous processing, and lossless WAV / high-bitrate MP3 downloads.
"""

from __future__ import annotations

import io
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

try:
    from services.enhancer.config import (
        ALL_SUPPORTED_EXTENSIONS,
        ENHANCEMENT_PRESETS,
        MAX_UPLOAD_BYTES,
    )
    from services.enhancer.processor import get_voice_enhancer
except ImportError:
    from ValoraA.services.enhancer.config import (
        ALL_SUPPORTED_EXTENSIONS,
        ENHANCEMENT_PRESETS,
        MAX_UPLOAD_BYTES,
    )
    from ValoraA.services.enhancer.processor import get_voice_enhancer
from services.tts.utils import get_logger

logger = get_logger("valora.api.enhancer")

router = APIRouter(prefix="/api/enhance", tags=["Voice Enhancement"])

# Temporary cache directory for processed sessions
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENHANCER_CACHE_DIR = BASE_DIR / "data" / "enhanced_sessions"
ENHANCER_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory session registry with TTL for active comparisons
SESSION_CACHE: Dict[str, Dict[str, Any]] = {}
MAX_CACHE_SESSIONS = 50


def _cleanup_old_sessions():
    """Keep in-memory and disk session cache bounded."""
    now = time.time()
    # Remove sessions older than 4 hours
    expired = [
        sid
        for sid, meta in SESSION_CACHE.items()
        if now - meta.get("created_at", now) > 14400
    ]
    for sid in expired:
        SESSION_CACHE.pop(sid, None)
        session_folder = ENHANCER_CACHE_DIR / sid
        if session_folder.exists():
            try:
                for f in session_folder.glob("*"):
                    f.unlink()
                session_folder.rmdir()
            except Exception:
                pass


@router.get("/presets", response_class=JSONResponse)
async def get_presets() -> Dict[str, Any]:
    """
    Return all available audio enhancement presets and default parameters.
    """
    presets_list = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "icon": p.icon,
            "recommended_for": p.recommended_for,
            "strength": p.strength,
            "noise_reduction": p.noise_reduction,
            "voice_clarity": p.voice_clarity,
            "warmth": p.warmth,
            "volume_balancing": p.volume_balancing,
            "echo_reduction": p.echo_reduction,
            "de_essing": p.de_essing,
            "highpass_hz": p.highpass_hz,
            "target_lufs": p.target_lufs,
            "peak_ceiling_db": p.peak_ceiling_db,
        }
        for p in ENHANCEMENT_PRESETS.values()
    ]
    return {
        "success": True,
        "presets": presets_list,
        "default_preset": "podcast",
        "supported_extensions": list(ALL_SUPPORTED_EXTENSIONS),
        "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
    }


@router.post("/process", response_class=JSONResponse)
async def process_audio(
    file: UploadFile = File(..., description="Uploaded audio or video media file"),
    preset: str = Form("podcast", description="Enhancement preset: natural, podcast, interview, or noisy"),
    strength: Optional[float] = Form(None),
    noise_reduction: Optional[float] = Form(None),
    voice_clarity: Optional[float] = Form(None),
    warmth: Optional[float] = Form(None),
    volume_balancing: Optional[float] = Form(None),
    echo_reduction: Optional[float] = Form(None),
    de_essing: Optional[float] = Form(None),
    highpass_hz: Optional[float] = Form(None),
    target_lufs: Optional[float] = Form(None),
    preview_mode: Optional[bool] = Form(False),
    preview_duration: Optional[float] = Form(30.0),
) -> Dict[str, Any]:
    """
    Process an uploaded audio or video recording through the acoustic enhancement pipeline.
    """
    _cleanup_old_sessions()

    # Validate filename and format
    original_filename = file.filename or "uploaded_recording.wav"
    ext = Path(original_filename).suffix.lower()
    if ext not in ALL_SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{ext}'. Supported audio/video formats: {', '.join(sorted(ALL_SUPPORTED_EXTENSIONS))}",
        )

    # Read uploaded content
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {exc}",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    # Build overrides dictionary
    overrides = {}
    if strength is not None:
        overrides["strength"] = strength
    if noise_reduction is not None:
        overrides["noise_reduction"] = noise_reduction
    if voice_clarity is not None:
        overrides["voice_clarity"] = voice_clarity
    if warmth is not None:
        overrides["warmth"] = warmth
    if volume_balancing is not None:
        overrides["volume_balancing"] = volume_balancing
    if echo_reduction is not None:
        overrides["echo_reduction"] = echo_reduction
    if de_essing is not None:
        overrides["de_essing"] = de_essing
    if highpass_hz is not None:
        overrides["highpass_hz"] = highpass_hz
    if target_lufs is not None:
        overrides["target_lufs"] = target_lufs

    enhancer = get_voice_enhancer()
    session_id = f"enh_{uuid.uuid4().hex[:12]}"
    session_dir = ENHANCER_CACHE_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Run real acoustic enhancement pipeline
        result = enhancer.enhance(
            file_input=content,
            preset_id=preset,
            overrides=overrides,
            preview_mode=bool(preview_mode),
            preview_duration=float(preview_duration or 30.0),
        )

        sr = result["sample_rate"]
        enhanced_audio = result["enhanced_audio"]
        original_audio = result["original_audio"]

        # Save cached WAV and MP3 files on disk for streaming and download
        orig_wav_path = session_dir / "original.wav"
        enh_wav_path = session_dir / "enhanced.wav"
        enh_mp3_path = session_dir / "enhanced.mp3"

        orig_wav_bytes = enhancer.export_audio_bytes(original_audio, sr, "wav")
        enh_wav_bytes = enhancer.export_audio_bytes(enhanced_audio, sr, "wav")
        enh_mp3_bytes = enhancer.export_audio_bytes(enhanced_audio, sr, "mp3")

        orig_wav_path.write_bytes(orig_wav_bytes)
        enh_wav_path.write_bytes(enh_wav_bytes)
        enh_mp3_path.write_bytes(enh_mp3_bytes)

        # Store in session registry
        clean_base_name = Path(original_filename).stem
        SESSION_CACHE[session_id] = {
            "session_id": session_id,
            "created_at": time.time(),
            "original_filename": original_filename,
            "clean_base_name": clean_base_name,
            "sample_rate": sr,
            "channels": result["channels"],
            "duration": result["duration_seconds"],
            "preset": result["preset_used"],
            "preview_mode": result["preview_mode"],
            "input_metrics": result["input_metrics"],
            "output_metrics": result["output_metrics"],
            "processing_time": result["processing_time_seconds"],
            "dir": str(session_dir),
        }

        return {
            "success": True,
            "session_id": session_id,
            "filename": original_filename,
            "clean_base_name": clean_base_name,
            "duration_seconds": result["duration_seconds"],
            "sample_rate": sr,
            "channels": result["channels"],
            "preset_used": result["preset_used"],
            "preview_mode": result["preview_mode"],
            "input_metrics": result["input_metrics"],
            "output_metrics": result["output_metrics"],
            "processing_time_seconds": result["processing_time_seconds"],
            "original_url": f"/api/enhance/audio/{session_id}/original",
            "enhanced_url": f"/api/enhance/audio/{session_id}/enhanced?format=wav",
            "enhanced_mp3_url": f"/api/enhance/audio/{session_id}/enhanced?format=mp3",
            "download_wav_url": f"/api/enhance/audio/{session_id}/download?format=wav",
            "download_mp3_url": f"/api/enhance/audio/{session_id}/download?format=mp3",
        }

    except Exception as exc:
        logger.exception("Voice enhancement failed for file %s: %s", original_filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio enhancement processing failed: {exc}",
        )


@router.get("/audio/{session_id}/download")
async def download_enhanced(
    session_id: str,
    format: str = "wav",
):
    """
    Download the enhanced audio file with a clean descriptive filename.
    """
    session_meta = SESSION_CACHE.get(session_id)
    session_dir = ENHANCER_CACHE_DIR / session_id

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Enhancement session expired or not found.")

    base_name = session_meta.get("clean_base_name", "recording") if session_meta else "recording"
    fmt = format.lower().strip(".")

    if fmt == "mp3":
        file_path = session_dir / "enhanced.mp3"
        filename = f"{base_name}-enhanced.mp3"
        media_type = "audio/mpeg"
    else:
        file_path = session_dir / "enhanced.wav"
        filename = f"{base_name}-enhanced.wav"
        media_type = "audio/wav"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Enhanced audio file not found on server.")

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/audio/{session_id}/{track_type}")
async def get_audio_track(
    session_id: str,
    track_type: str,
    format: str = "wav",
):
    """
    Stream either 'original' or 'enhanced' audio for comparison playback.
    """
    if track_type == "download":
        return await download_enhanced(session_id=session_id, format=format)

    session_dir = ENHANCER_CACHE_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enhancement session expired or not found. Please re-enhance your audio.",
        )

    fmt = format.lower().strip(".")
    if track_type == "original":
        target_file = session_dir / "original.wav"
        media_type = "audio/wav"
    elif track_type == "enhanced":
        if fmt == "mp3":
            target_file = session_dir / "enhanced.mp3"
            media_type = "audio/mpeg"
        else:
            target_file = session_dir / "enhanced.wav"
            media_type = "audio/wav"
    else:
        raise HTTPException(status_code=400, detail="Invalid track type. Use 'original' or 'enhanced'.")

    if not target_file.exists():
        raise HTTPException(status_code=404, detail="Requested audio track file not found.")

    return FileResponse(
        target_file,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        },
    )
