"""
services/translator/engine.py

Production-grade real-time neural translation engine for Valora AI.
Supports Indian regional languages, international languages, script preservation,
caching, auto-language detection, and fault-tolerant provider fallbacks.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

try:
    from services.translator.languages import get_language_capability
except ImportError:
    from ValoraA.services.translator.languages import get_language_capability

logger = logging.getLogger("valora.translator.engine")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class TranslationEngine:
    """
    Robust multi-provider translation engine with caching and automatic failover.
    """

    def __init__(self, cache_size: int = 1000) -> None:
        self.cache_size = cache_size
        self._cache: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    def _normalize_lang_code(self, code: str) -> str:
        """Map locale codes or aliases to standard translation service codes."""
        if not code or code.lower() in ("auto", "detect"):
            return "auto"
        code_clean = code.strip()
        # Handle Indian English
        if code_clean.lower() == "en-in":
            return "en"
        # Handle special language mappings
        mapping = {
            "zh-cn": "zh-CN",
            "zh-hk": "zh-TW",
            "zh-tw": "zh-TW",
            "kok": "gom",  # Konkani in Google
            "or-in": "or",
            "as-in": "as",
            "ne-np": "ne",
            "sa-in": "sa",
            "mai-in": "mai",
            "sd-in": "sd",
            "ks-in": "ks",
            "doi-in": "doi",
            "mni-in": "mni-Mtei",
        }
        low = code_clean.lower()
        if low in mapping:
            return mapping[low]
        # Return prefix if hyphenated (e.g. 'hi-IN' -> 'hi', 'fr-FR' -> 'fr')
        if "-" in code_clean:
            return code_clean.split("-")[0].lower()
        return code_clean.lower()

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "en",
    ) -> Dict[str, Any]:
        """
        Translate speech text from source_lang to target_lang.

        Returns:
            Dict containing:
            - translated_text: str
            - source_lang: str
            - target_lang: str
            - detected_lang: Optional[str]
            - latency_ms: float
            - cached: bool
        """
        text_clean = text.strip()
        if not text_clean:
            return {
                "translated_text": "",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "detected_lang": None,
                "latency_ms": 0.0,
                "cached": False,
            }

        sl = self._normalize_lang_code(source_lang)
        tl = self._normalize_lang_code(target_lang)

        # Check identical language
        if sl != "auto" and sl == tl:
            return {
                "translated_text": text_clean,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "detected_lang": sl,
                "latency_ms": 0.0,
                "cached": True,
            }

        # Check memory cache
        cache_key = (sl, tl, text_clean)
        if cache_key in self._cache:
            res = dict(self._cache[cache_key])
            res["cached"] = True
            return res

        start_time = time.time()
        translated_text = ""
        detected_lang: Optional[str] = None

        # Strategy 1: Direct High-Speed Google GTX Engine
        try:
            translated_text, detected_lang = self._translate_gtx(text_clean, sl=sl, tl=tl)
        except Exception as exc1:
            logger.warning("Primary GTX translation error for '%s' -> '%s': %s", sl, tl, exc1)

            # Strategy 2: deep_translator Google / MyMemory fallback
            try:
                translated_text = self._translate_deep_translator(text_clean, sl=sl, tl=tl)
            except Exception as exc2:
                logger.error("Deep-translator fallback failed: %s", exc2)
                # Strategy 3: Graceful return of original text with notice if complete outage
                translated_text = f"[{text_clean}]"

        latency_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "detected_lang": detected_lang or (sl if sl != "auto" else "unknown"),
            "latency_ms": latency_ms,
            "cached": False,
        }

        # Bounded cache update
        if len(self._cache) >= self.cache_size:
            # Evict first 100 keys
            keys_to_del = list(self._cache.keys())[:100]
            for k in keys_to_del:
                self._cache.pop(k, None)

        self._cache[cache_key] = result
        return result

    def _translate_gtx(self, text: str, sl: str, tl: str) -> Tuple[str, Optional[str]]:
        """Query Google GTX API with sentence preservation and encoding safety."""
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl={urllib.parse.quote(sl)}&tl={urllib.parse.quote(tl)}&dt=t&q={urllib.parse.quote(text)}"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Charset": "utf-8",
            },
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            # data[0] is list of [[translated_chunk, original_chunk, ...]]
            translated_chunks = []
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                for item in data[0]:
                    if isinstance(item, list) and len(item) > 0 and item[0]:
                        translated_chunks.append(str(item[0]))

            translated_text = "".join(translated_chunks) if translated_chunks else text

            detected_lang = None
            if len(data) > 2 and isinstance(data[2], str):
                detected_lang = data[2]

            return translated_text, detected_lang

    def _translate_deep_translator(self, text: str, sl: str, tl: str) -> str:
        """Fallback via deep_translator library."""
        from deep_translator import GoogleTranslator, MyMemoryTranslator

        try:
            src = "auto" if sl == "auto" else sl
            return GoogleTranslator(source=src, target=tl).translate(text)
        except Exception:
            # Try MyMemory
            src = "en" if sl == "auto" else sl
            return MyMemoryTranslator(source=src, target=tl).translate(text)


_engine_instance: Optional[TranslationEngine] = None


def get_translation_engine() -> TranslationEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TranslationEngine()
    return _engine_instance
