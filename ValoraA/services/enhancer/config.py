"""
services/enhancer/config.py

Configuration and preset profiles for the Valora AI Voice Enhancement engine.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class EnhancementPreset:
    id: str
    name: str
    description: str
    icon: str
    recommended_for: str
    # Processing parameters (0.0 to 1.0 or specific units)
    strength: float = 0.8
    noise_reduction: float = 0.65
    voice_clarity: float = 0.70
    warmth: float = 0.50
    volume_balancing: float = 0.60
    echo_reduction: float = 0.35
    de_essing: float = 0.55
    highpass_hz: float = 75.0
    target_lufs: float = -16.0
    peak_ceiling_db: float = -1.0


ENHANCEMENT_PRESETS: Dict[str, EnhancementPreset] = {
    "natural": EnhancementPreset(
        id="natural",
        name="Natural Speech",
        description="Transparent background cleanup with gentle rumble filtering and minimal tonal alteration. Preserves organic room feel and raw voice character.",
        icon="fa-feather",
        recommended_for="Voiceovers, audiobooks, personal memos, and clean acoustic environments",
        strength=0.60,
        noise_reduction=0.45,
        voice_clarity=0.40,
        warmth=0.35,
        volume_balancing=0.40,
        echo_reduction=0.20,
        de_essing=0.40,
        highpass_hz=65.0,
        target_lufs=-18.0,
        peak_ceiling_db=-1.0,
    ),
    "podcast": EnhancementPreset(
        id="podcast",
        name="Podcast Master",
        description="Rich broadcast presence, warmth, gentle de-essing, dynamic range control, and industry-standard -16 LUFS loudness mastering.",
        icon="fa-microphone-lines",
        recommended_for="Podcasts, YouTube commentary, narration, and radio shows",
        strength=0.85,
        noise_reduction=0.70,
        voice_clarity=0.75,
        warmth=0.65,
        volume_balancing=0.70,
        echo_reduction=0.40,
        de_essing=0.65,
        highpass_hz=80.0,
        target_lufs=-16.0,
        peak_ceiling_db=-1.0,
    ),
    "interview": EnhancementPreset(
        id="interview",
        name="Interview & Meeting",
        description="Speech-aware leveling balances quieter and louder speakers, suppresses room echo/reverberation, and increases dialogue intelligibility.",
        icon="fa-users-between-lines",
        recommended_for="Multi-speaker panels, Zoom/Teams calls, panel interviews, and lectures",
        strength=0.80,
        noise_reduction=0.75,
        voice_clarity=0.80,
        warmth=0.45,
        volume_balancing=0.85,
        echo_reduction=0.60,
        de_essing=0.50,
        highpass_hz=85.0,
        target_lufs=-18.0,
        peak_ceiling_db=-1.0,
    ),
    "noisy": EnhancementPreset(
        id="noisy",
        name="Noisy Recording",
        description="Aggressive suppression of fans, AC units, traffic hum, and steady background noise. Calibrated for difficult mobile or field recordings.",
        icon="fa-shield-halved",
        recommended_for="Street interviews, cafes, noisy rooms, fan noise, and phone recordings",
        strength=0.92,
        noise_reduction=0.90,
        voice_clarity=0.85,
        warmth=0.40,
        volume_balancing=0.75,
        echo_reduction=0.50,
        de_essing=0.55,
        highpass_hz=90.0,
        target_lufs=-17.0,
        peak_ceiling_db=-1.0,
    ),
}

# Maximum allowed file upload size (in bytes, 150MB)
MAX_UPLOAD_BYTES = 150 * 1024 * 1024

# Supported input file extensions
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".aiff"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
ALL_SUPPORTED_EXTENSIONS = SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS
