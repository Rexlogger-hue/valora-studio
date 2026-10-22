"""
services/tts/edge_ssml.py

SSML generation utility for Microsoft Edge-TTS neural speech synthesis in Valora AI.
Converts plain text and emotion parameters into valid Microsoft Speech Synthesis Markup
Language (SSML), with support for `<mstts:express-as>` emotional styles, degree/intensity
scaling, and fallback mechanisms.
"""

from __future__ import annotations

import html
import logging
from typing import Optional

logger = logging.getLogger("valora.tts.edge_ssml")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Mapping of Valora AI emotions to Microsoft Azure/Edge neural voice express-as styles
EMOTION_TO_STYLE: dict[str, Optional[str]] = {
    "neutral": None,
    "warm": "friendly",
    "confident": "assistant",
    "cheerful": "cheerful",
    "serious": "serious",
    "whisper": "whispering",
    "empathetic": "empathetic",
    "dramatic": "excited",
}


def escape_ssml_text(text: str) -> str:
    """
    Escape special XML characters in text for safe insertion into SSML.

    Args:
        text: Plain input text.

    Returns:
        str: XML-safe escaped text.
    """
    return html.escape(text, quote=True)


def map_emotion_to_style(emotion: Optional[str]) -> Optional[str]:
    """
    Map a Valora AI emotion name to a Microsoft neural voice style string.

    Args:
        emotion: Emotion string (e.g. 'cheerful', 'warm', 'serious').

    Returns:
        Optional[str]: Microsoft express-as style name, or None if neutral/unsupported.
    """
    if not emotion:
        return None
    normalized = emotion.strip().lower()
    return EMOTION_TO_STYLE.get(normalized, None)


def intensity_to_styledegree(intensity: int) -> float:
    """
    Map an integer emotion intensity (0..100) to Microsoft SSML styledegree (0.3..2.0).

    Formula: styledegree = 0.3 + 1.7 * (intensity / 100.0)

    Args:
        intensity: Emotion intensity from 0 to 100.

    Returns:
        float: styledegree value rounded to 2 decimal places.
    """
    clamped = max(0, min(100, int(intensity)))
    degree = 0.3 + 1.7 * (clamped / 100.0)
    return round(degree, 2)


def rate_to_prosody_str(speed: Optional[float]) -> str:
    """
    Convert a speed multiplier (e.g. 1.25) to a prosody rate percentage string.

    Args:
        speed: Speed multiplier (e.g. 0.5 to 2.0). None or 1.0 returns '+0%'.

    Returns:
        str: Formatted prosody rate string (e.g. '+25%', '-10%', '+0%').
    """
    if speed is None or abs(speed - 1.0) < 0.01:
        return "+0%"
    pct = int(round((speed - 1.0) * 100))
    return f"{pct:+d}%"


def build_edge_ssml(
    text: str,
    voice_name: str,
    emotion: Optional[str] = "neutral",
    intensity: int = 45,
    speed: Optional[float] = None,
    lang: str = "en-US",
) -> str:
    """
    Build a complete SSML document for Microsoft Edge-TTS with express-as emotion styling.

    Args:
        text: Plain input text.
        voice_name: Edge neural voice name (e.g. 'en-US-AriaNeural').
        emotion: Emotion name ('neutral', 'warm', 'confident', 'cheerful', etc.).
        intensity: Emotion intensity percentage (0-100).
        speed: Optional playback speed multiplier (0.5 to 2.0).
        lang: XML language tag (defaults to 'en-US').

    Returns:
        str: Well-formed SSML string.
    """
    escaped_text = escape_ssml_text(text)
    style = map_emotion_to_style(emotion)
    rate_str = rate_to_prosody_str(speed)

    if style and intensity > 0 and (emotion and emotion.lower() != "neutral"):
        degree = intensity_to_styledegree(intensity)
        inner_content = f'<mstts:express-as style="{style}" styledegree="{degree}">{escaped_text}</mstts:express-as>'
    else:
        inner_content = escaped_text

    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{lang}">\n'
        f'  <voice name="{voice_name}">\n'
        f'    <prosody rate="{rate_str}" pitch="+0Hz" volume="+0%">\n'
        f"      {inner_content}\n"
        f"    </prosody>\n"
        f"  </voice>\n"
        f"</speak>"
    )
    return ssml


def build_neutral_ssml(
    text: str,
    voice_name: str,
    speed: Optional[float] = None,
    lang: str = "en-US",
) -> str:
    """
    Build a fallback SSML document without express-as emotion tags.

    Args:
        text: Plain input text.
        voice_name: Edge neural voice name.
        speed: Optional playback speed multiplier.
        lang: XML language tag.

    Returns:
        str: Neutral SSML string.
    """
    escaped_text = escape_ssml_text(text)
    rate_str = rate_to_prosody_str(speed)

    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">\n'
        f'  <voice name="{voice_name}">\n'
        f'    <prosody rate="{rate_str}" pitch="+0Hz" volume="+0%">\n'
        f"      {escaped_text}\n"
        f"    </prosody>\n"
        f"  </voice>\n"
        f"</speak>"
    )
    return ssml
