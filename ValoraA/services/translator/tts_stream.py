"""
services/translator/tts_stream.py

High-performance neural text-to-speech engine for spoken translation playback.
Supports Indian regional voices, international locales, pitch, rate, and audio streaming.
"""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Dict, Optional, Tuple

import edge_tts

try:
    from services.translator.languages import get_language_capability
except ImportError:
    from ValoraA.services.translator.languages import get_language_capability

logger = logging.getLogger("valora.translator.tts")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class SpokenVoiceEngine:
    """
    Synthesizes translated speech into natural regional or international voices.
    """

    def __init__(self, cache_size: int = 500) -> None:
        self.cache_size = cache_size
        self._cache: Dict[Tuple[str, str, str], bytes] = {}

    def _resolve_voice(self, target_lang: str, voice_override: Optional[str] = None) -> str:
        """Resolve suitable neural voice from user override or language registry."""
        if voice_override and voice_override.strip():
            return voice_override.strip()

        cap = get_language_capability(target_lang)
        if cap and cap.default_voice:
            return cap.default_voice

        # Generic fallbacks
        code = (target_lang or "en").lower().split("-")[0]
        fallbacks = {
            "hi": "hi-IN-MadhurNeural",
            "ta": "ta-IN-PallaviNeural",
            "te": "te-IN-ShrutiNeural",
            "bn": "bn-IN-TanishaaNeural",
            "mr": "mr-IN-AarohiNeural",
            "gu": "gu-IN-DhwaniNeural",
            "kn": "kn-IN-SapnaNeural",
            "ml": "ml-IN-SobhanaNeural",
            "pa": "pa-IN-GurpreetNeural",
            "ur": "ur-IN-GulNeural",
            "ne": "ne-NP-HemkalaNeural",
            "en": "en-US-JennyNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
            "de": "de-DE-KatjaNeural",
            "it": "it-IT-ElsaNeural",
            "pt": "pt-BR-FranciscaNeural",
            "ar": "ar-SA-ZariyahNeural",
            "zh": "zh-CN-XiaoxiaoNeural",
            "ja": "ja-JP-NanamiNeural",
            "ko": "ko-KR-SunHiNeural",
            "ru": "ru-RU-SvetlanaNeural",
        }
        return fallbacks.get(code, "en-US-JennyNeural")

    async def synthesize(
        self,
        text: str,
        target_lang: str = "en",
        voice: Optional[str] = None,
        rate_pct: int = 0,
        pitch_hz: int = 0,
    ) -> Tuple[bytes, str]:
        """
        Synthesize text into MP3 audio bytes.

        Returns:
            Tuple[audio_bytes, voice_name_used]
        """
        clean_text = text.strip()
        if not clean_text:
            return b"", ""

        selected_voice = self._resolve_voice(target_lang, voice)

        # Format rate and pitch for edge-tts (e.g. '+10%', '-5Hz')
        rate_str = f"{rate_pct:+d}%" if rate_pct != 0 else "+0%"
        pitch_str = f"{pitch_hz:+d}Hz" if pitch_hz != 0 else "+0Hz"

        cache_key = (clean_text, selected_voice, f"{rate_str}_{pitch_str}")
        if cache_key in self._cache:
            return self._cache[cache_key], selected_voice

        try:
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=selected_voice,
                rate=rate_str,
                pitch=pitch_str,
            )
            chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])

            audio_bytes = b"".join(chunks)

            # Update cache
            if len(self._cache) >= self.cache_size:
                keys = list(self._cache.keys())[:50]
                for k in keys:
                    self._cache.pop(k, None)

            self._cache[cache_key] = audio_bytes
            return audio_bytes, selected_voice

        except Exception as exc:
            logger.error("Spoken voice synthesis failed with voice %s: %s", selected_voice, exc)
            raise


_voice_engine_instance: Optional[SpokenVoiceEngine] = None


def get_spoken_voice_engine() -> SpokenVoiceEngine:
    global _voice_engine_instance
    if _voice_engine_instance is None:
        _voice_engine_instance = SpokenVoiceEngine()
    return _voice_engine_instance
