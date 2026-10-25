"""
services/indic_tts/processor.py

Intelligent multilingual language handler and Hindi text normalizer
for AI4Bharat Indic-Parler-TTS.

Pipeline:
User text -> Language & script detection -> Translation / Transliteration / Normalization -> Natural Hindi Sentence Chunking -> Indic-Parler-TTS

Handles:
1. English input -> Natural, conversational Hindi translation.
2. Hindi in Devanagari -> Preserved, cleaned, and punctuation-normalized.
3. Romanized Hindi (Hinglish e.g. "aap kaise ho") -> Accurate Devanagari transliteration ("आप कैसे हो").
4. Mixed Hindi & English -> Preserves brand names, technical terms, and proper nouns.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("valora.indic_tts.processor")

# Common Romanized Hindi (Hinglish) keyword vocabulary for robust script classification
HINGLISH_VOCAB = {
    "aap", "ap", "kaise", "kaisa", "kaisi", "ho", "hai", "hain", "kya", "mera", "meri", "mere",
    "mujhe", "tum", "tumhara", "tumhari", "hum", "hamara", "hamari", "accha", "achha", "theek",
    "shukriya", "dhanyawad", "baat", "karo", "karenge", "karna", "kar", "rahe", "raha", "rahi",
    "namaste", "namaskar", "namastey", "kaun", "kahan", "kab", "kyun", "kyu", "madad", "kaam",
    "dost", "dosto", "sab", "sabhi", "bhai", "yaar", "lekin", "aur", "bhi", "yeh", "woh", "voh",
    "aaj", "kal", "abhi", "kripya", "bahut", "bohot", "thoda", "zaroor", "bolo", "boliye"
}


def is_devanagari_char(char: str) -> bool:
    """Check if character falls within the Devanagari Unicode block."""
    return 0x0900 <= ord(char) <= 0x097F


def count_devanagari_chars(text: str) -> int:
    """Count number of Devanagari characters in text."""
    return sum(1 for c in text if is_devanagari_char(c))


def transliterate_to_devanagari(text: str) -> str:
    """
    Transliterate Romanized Hindi (Hinglish) text into natural Devanagari script.
    Uses Google Input Tools API with fault-tolerant fallback.
    """
    clean_text = text.strip()
    if not clean_text:
        return ""

    try:
        url = (
            "https://inputtools.google.com/request?text="
            + urllib.parse.quote(clean_text)
            + "&itc=hi-t-i0-und&num=1"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 1 and data[0] == "SUCCESS":
                candidates = data[1]
                if candidates and isinstance(candidates, list) and len(candidates) > 0:
                    cand_list = candidates[0]
                    if len(cand_list) > 1 and cand_list[1] and len(cand_list[1]) > 0:
                        res = cand_list[1][0]
                        if res and isinstance(res, str):
                            return res.strip()
    except Exception as exc:
        logger.warning("Google Input Tools transliteration notice: %s. Using direct phonetic fallback.", exc)

    return clean_text


def normalize_hindi_punctuation(text: str) -> str:
    """
    Normalize punctuation for Hindi speech synthesis:
    - Replace ASCII periods at end of declarative sentences with Hindi danda (।)
    - Ensure clean spacing before and after dandas and commas
    - Retain question marks (?) and exclamation marks (!) for expressive intonation
    """
    if not text:
        return ""

    t = text.strip()
    # Replace multiple spaces
    t = re.sub(r"[ \t]+", " ", t)

    # Replace periods following Devanagari text with danda
    t = re.sub(r"([\u0900-\u097F]+)\s*\.", r"\1।", t)

    # Ensure danda at end of sentence if no trailing punctuation exists
    if t and not re.search(r"[।॥\?!;\.]$", t):
        t = t + "।"

    return t


def split_hindi_into_conversational_chunks(text: str, max_chunk_len: int = 140) -> List[str]:
    """
    Split Hindi text at natural grammatical boundaries (dandas, question marks, commas, conjunctions)
    to prevent unnatural cut-offs and respect the neural model's attention window.
    """
    text = text.strip()
    if not text:
        return []

    # First split at major sentence boundaries (।, ॥, ?, !, newlines)
    raw_sentences = re.split(r"([।॥\?!;\n]+)", text)
    sentences: List[str] = []
    current_sentence = ""

    for part in raw_sentences:
        if not part:
            continue
        if re.match(r"^[।॥\?!;\n]+$", part):
            current_sentence += part
            if current_sentence.strip():
                sentences.append(current_sentence.strip())
            current_sentence = ""
        else:
            current_sentence += part

    if current_sentence.strip():
        sentences.append(current_sentence.strip())

    # Pack sentences into chunks within max_chunk_len
    chunks: List[str] = []
    current_chunk = ""

    for sent in sentences:
        if not current_chunk:
            current_chunk = sent
        elif len(current_chunk) + len(sent) + 1 <= max_chunk_len:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk)
            current_chunk = sent

    if current_chunk:
        chunks.append(current_chunk)

    # For chunks still exceeding max_chunk_len, split at commas or Hindi conjunctions
    final_chunks: List[str] = []
    conjunction_pattern = r"(\s+(?:और|तथा|लेकिन|किंतु|परंतु|क्योंकि|जिससे|ताकि)\s+)"

    for chunk in chunks:
        if len(chunk) <= max_chunk_len:
            final_chunks.append(chunk)
            continue

        # Split by comma or conjunction
        subparts = re.split(conjunction_pattern, chunk)
        sub_chunk = ""
        for part in subparts:
            if not part:
                continue
            if not sub_chunk:
                sub_chunk = part
            elif len(sub_chunk) + len(part) <= max_chunk_len:
                sub_chunk += part
            else:
                if sub_chunk.strip():
                    final_chunks.append(sub_chunk.strip())
                sub_chunk = part

        if sub_chunk.strip():
            final_chunks.append(sub_chunk.strip())

    return final_chunks if final_chunks else [text]


class IndicSpeechInputProcessor:
    """
    Unified input processor for Hindi speech bot:
    Converts English, Romanized Hindi, and mixed inputs into verified,
    punctuation-normalized Hindi transcripts ready for Indic-Parler-TTS.
    """

    def __init__(self):
        try:
            from services.translator.engine import get_translation_engine
            self.translator = get_translation_engine()
        except Exception:
            self.translator = None

    def process(self, raw_text: str) -> Dict[str, Any]:
        """
        Analyze input text, determine script/language, and produce natural Hindi transcript.
        """
        text = (raw_text or "").strip()
        if not text:
            return {
                "input_text": "",
                "hindi_transcript": "",
                "detected_mode": "empty",
                "label": "Empty Input",
                "chunks": [],
            }

        total_chars = len(text)
        deva_count = count_devanagari_chars(text)
        alpha_chars = [c for c in text if c.isalpha()]
        words = re.findall(r"[a-zA-Z]+", text.lower())

        # 1. Direct Devanagari Hindi
        # If over 35% of characters or 60% of alphabetic characters are Devanagari
        is_devanagari = (deva_count >= 3 and (deva_count / max(1, total_chars)) > 0.3) or (
            len(alpha_chars) > 0 and (deva_count / len(alpha_chars)) > 0.5
        )

        if is_devanagari:
            normalized_hi = normalize_hindi_punctuation(text)
            chunks = split_hindi_into_conversational_chunks(normalized_hi)
            return {
                "input_text": text,
                "hindi_transcript": normalized_hi,
                "detected_mode": "hindi_devanagari",
                "label": "Direct Hindi (Devanagari)",
                "chunks": chunks,
            }

        # 2. Check for Romanized Hindi (Hinglish)
        hinglish_matches = [w for w in words if w in HINGLISH_VOCAB]
        hinglish_ratio = len(hinglish_matches) / max(1, len(words))

        # Check translation service language detection
        detected_lang = "unknown"
        translated_text = ""
        if self.translator is not None:
            try:
                res = self.translator.translate(text, source_lang="auto", target_lang="hi")
                detected_lang = res.get("detected_lang", "unknown")
                translated_text = res.get("translated_text", "")
            except Exception as e:
                logger.warning("Translator lookup exception: %s", e)

        # Criteria for Romanized Hindi:
        # - Explicit Hinglish words found
        # - OR Google detects source as 'hi' while in Latin script
        is_romanized_hindi = (
            (len(hinglish_matches) >= 2)
            or (len(words) <= 4 and len(hinglish_matches) >= 1)
            or (hinglish_ratio >= 0.3)
            or (detected_lang == "hi" and deva_count == 0)
        )

        if is_romanized_hindi:
            devanagari_translit = transliterate_to_devanagari(text)
            # If transliteration succeeded in producing Devanagari characters
            if count_devanagari_chars(devanagari_translit) > 0:
                normalized_hi = normalize_hindi_punctuation(devanagari_translit)
                chunks = split_hindi_into_conversational_chunks(normalized_hi)
                return {
                    "input_text": text,
                    "hindi_transcript": normalized_hi,
                    "detected_mode": "romanized_hindi",
                    "label": "Romanized Hindi Transliterated",
                    "chunks": chunks,
                }

        # 3. English or Code-Mixed Input -> Translate into Natural Conversational Hindi
        if translated_text and count_devanagari_chars(translated_text) > 0:
            final_hi = normalize_hindi_punctuation(translated_text)
            chunks = split_hindi_into_conversational_chunks(final_hi)
            mode = "mixed_code_switch" if len(hinglish_matches) > 0 else "english_translation"
            label = "Mixed Hindi-English Translated" if mode == "mixed_code_switch" else "English to Hindi Translation"
            return {
                "input_text": text,
                "hindi_transcript": final_hi,
                "detected_mode": mode,
                "label": label,
                "chunks": chunks,
            }

        # Fallback transliteration
        fallback_hi = normalize_hindi_punctuation(transliterate_to_devanagari(text))
        chunks = split_hindi_into_conversational_chunks(fallback_hi)
        return {
            "input_text": text,
            "hindi_transcript": fallback_hi,
            "detected_mode": "fallback",
            "label": "Phonetic Normalization",
            "chunks": chunks,
        }


# Global Singleton Handle
_processor_instance: Optional[IndicSpeechInputProcessor] = None


def get_speech_input_processor() -> IndicSpeechInputProcessor:
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = IndicSpeechInputProcessor()
    return _processor_instance
