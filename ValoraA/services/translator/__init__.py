"""
services/translator package for Valora AI.
"""

from services.translator.engine import TranslationEngine, get_translation_engine
from services.translator.languages import (
    ALL_LANGUAGES,
    GLOBAL_LANGUAGES,
    INDIAN_LANGUAGES,
    get_language_capability,
    list_language_capabilities,
)
from services.translator.tts_stream import SpokenVoiceEngine, get_spoken_voice_engine

__all__ = [
    "TranslationEngine",
    "get_translation_engine",
    "SpokenVoiceEngine",
    "get_spoken_voice_engine",
    "ALL_LANGUAGES",
    "INDIAN_LANGUAGES",
    "GLOBAL_LANGUAGES",
    "get_language_capability",
    "list_language_capabilities",
]
