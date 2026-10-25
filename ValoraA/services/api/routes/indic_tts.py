"""
services/api/routes/indic_tts.py

FastAPI API router for AI4Bharat Indic-Parler-TTS speech synthesis.
Exposes endpoints for:
- Language detection, translation, and Hindi normalization (/process-text)
- Full speech synthesis pipeline with Devanagari transcript return (/synthesize)
- Speaker discovery and sample prompts (/speakers)
- Hardware and model status diagnostics (/status)
- Offline model weights management (/download-weights, /download-status)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from services.indic_tts.engine import (
    DEFAULT_VOICE_DESCRIPTION,
    OFFICIAL_MODEL_ID,
    SAMPLE_PROMPTS,
    SPEAKER_CONFIGS,
    IndicSynthesisResult,
    get_indic_tts_engine,
)
from services.indic_tts.processor import get_speech_input_processor

logger = logging.getLogger("valora.api.routes.indic_tts")

router = APIRouter(prefix="/indic-tts", tags=["AI4Bharat Indic-Parler-TTS"])


class ProcessTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Input text in English, Romanized Hindi, or Devanagari")


class IndicSynthesizeRequest(BaseModel):
    text: Optional[str] = Field(default=None, description="Input text (English, Romanized Hindi, or Devanagari)")
    hindi_text: Optional[str] = Field(default=None, description="Alias for backward compatibility")
    speaker: str = Field(default="Rohit", description="Speaker name (Rohit, Divya, Aman, Rani)")
    voice_description: Optional[str] = Field(default=None, description="Prompt description directing delivery style")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech playback speed multiplier")
    pitch: float = Field(default=0.0, ge=-8.0, le=8.0, description="Pitch shift in semitones")
    temperature: float = Field(default=1.0, ge=0.2, le=2.0, description="Generation sampling temperature")


class DownloadWeightsRequest(BaseModel):
    repo_id: Optional[str] = Field(default=OFFICIAL_MODEL_ID, description="Hugging Face repo id to download")


@router.get("/status", summary="Get Indic-Parler-TTS hardware & model status")
async def get_status() -> Dict[str, Any]:
    """
    Return hardware acceleration status, active engine mode,
    model ID, and local weights availability.
    """
    engine = get_indic_tts_engine()
    return engine.get_hardware_status()


@router.get("/speakers", summary="List Indic-Parler-TTS speakers & sample prompts")
async def list_speakers() -> Dict[str, Any]:
    """
    Return available Hindi speakers with avatars, acoustic styles,
    default directability descriptions, and sample texts.
    """
    return {
        "model_id": OFFICIAL_MODEL_ID,
        "speakers": list(SPEAKER_CONFIGS.values()),
        "sample_prompts": SAMPLE_PROMPTS,
        "default_speaker": "Rohit",
        "default_voice_description": DEFAULT_VOICE_DESCRIPTION,
    }


@router.post("/process-text", summary="Translate or normalize input text to Hindi")
async def process_text(body: ProcessTextRequest) -> Dict[str, Any]:
    """
    Detect input language, translate English to Hindi, transliterate Romanized Hindi,
    and return the verified Hindi transcript ready for speech synthesis.
    """
    processor = get_speech_input_processor()
    try:
        result = processor.process(body.text)
        return {
            "success": True,
            **result,
            "normalized_hindi": result.get("hindi_transcript", ""),
            "language_label": result.get("label", "Hindi"),
            "chunk_count": len(result.get("chunks", [])),
        }
    except Exception as exc:
        logger.exception("Text processing error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text processing error: {str(exc)}",
        ) from exc


@router.post("/synthesize", summary="Synthesize Hindi speech via Indic-Parler-TTS")
async def synthesize_speech(body: IndicSynthesizeRequest) -> Dict[str, Any]:
    """
    Synthesize natural Hindi speech audio from text using Indic-Parler-TTS.
    Accepts English, Romanized Hindi, or Devanagari Hindi.
    """
    input_text = body.text or body.hindi_text
    if not input_text or not input_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input text cannot be empty.",
        )

    engine = get_indic_tts_engine()
    try:
        result: IndicSynthesisResult = await engine.synthesize(
            text=input_text,
            speaker=body.speaker,
            voice_description=body.voice_description,
            speed=body.speed,
            pitch=body.pitch,
            temperature=body.temperature,
        )
        return {
            "success": True,
            "audio_url": result.audio_url,
            "duration_seconds": result.duration_seconds,
            "generation_seconds": result.generation_seconds,
            "rtf": result.rtf,
            "sample_rate": result.sample_rate,
            "speaker": result.speaker,
            "speaker_tagline": result.speaker_tagline,
            "engine_mode": result.engine_mode,
            "device": result.device,
            "input_text": result.input_text,
            "hindi_transcript": result.hindi_transcript,
            "detected_mode": result.detected_mode,
            "language_label": result.language_label,
            "text_preview": result.text_preview,
            "chunks_count": result.chunks_count,
            "waveform": result.waveform,
            "status_markdown": result.status_markdown,
        }
    except Exception as exc:
        logger.exception("Synthesis error in Indic-Parler-TTS: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis error: {str(exc)}",
        ) from exc


@router.post("/download-weights", summary="Download offline PyTorch weights in background")
async def download_weights(body: DownloadWeightsRequest) -> Dict[str, Any]:
    """
    Trigger asynchronous background download of official or mirror model weights.
    """
    engine = get_indic_tts_engine()
    return engine.start_background_download(repo_id=body.repo_id)


@router.get("/download-status", summary="Check offline weights download progress")
async def get_download_status() -> Dict[str, Any]:
    """
    Check current progress of background weights download.
    """
    engine = get_indic_tts_engine()
    return engine.get_hardware_status()["download_status"]
