"""
scripts/fetch_edge_voices.py

Fetch all available neural voices from Microsoft Edge TTS and save
the complete catalog to services/tts/voice_catalog.json.
"""

import asyncio
import json
import logging
from pathlib import Path

import edge_tts

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("valora.fetch_voices")


async def fetch_voices() -> int:
    logger.info("Connecting to Microsoft Edge TTS to fetch full voice catalog...")
    voices = await edge_tts.list_voices()
    
    formatted_voices = []
    for v in voices:
        formatted_voices.append({
            "ShortName": v.get("ShortName"),
            "Locale": v.get("Locale"),
            "Gender": v.get("Gender"),
            "FriendlyName": v.get("FriendlyName"),
            "LocaleName": v.get("LocaleName"),
            "Status": v.get("Status"),
            "SuggestedCodec": v.get("SuggestedCodec"),
            "VoiceTag": v.get("VoiceTag", {}),
        })

    # Sort voices alphabetically by Locale and ShortName
    formatted_voices.sort(key=lambda x: (x.get("Locale", ""), x.get("ShortName", "")))

    output_path = Path(__file__).resolve().parents[1] / "services" / "tts" / "voice_catalog.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(formatted_voices, f, indent=2, ensure_ascii=False)

    logger.info("Successfully fetched and saved %d voices to %s", len(formatted_voices), output_path)
    return len(formatted_voices)


if __name__ == "__main__":
    count = asyncio.run(fetch_voices())
    print(f"\n==========================================")
    print(f" TOTAL EDGE VOICES FOUND AND SAVED: {count}")
    print(f"==========================================\n")
