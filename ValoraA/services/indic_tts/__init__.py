"""
services/indic_tts/__init__.py
AI4Bharat Indic-Parler-TTS service package for Valora AI.
"""

from services.indic_tts.engine import IndicTTSEngine, get_indic_tts_engine
from services.indic_tts.processor import (
    IndicSpeechInputProcessor,
    get_speech_input_processor,
    split_hindi_into_conversational_chunks,
    transliterate_to_devanagari,
)

__all__ = [
    "IndicTTSEngine",
    "get_indic_tts_engine",
    "IndicSpeechInputProcessor",
    "get_speech_input_processor",
    "split_hindi_into_conversational_chunks",
    "transliterate_to_devanagari",
]
