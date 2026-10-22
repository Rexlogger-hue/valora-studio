"""
services/tts/voice_library.py

Voice Library manager for Valora AI.
Manages persistent local reference voices for XTTS-v2 voice cloning,
including metadata tracking in manifest.json, soundfile-based audio duration
validation (5-90s), and mandatory consent verification.
"""

from __future__ import annotations

import datetime
import io
import json
import logging
import re
import shutil
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import soundfile as sf

logger = logging.getLogger("valora.tts.voice_library")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

DEFAULT_CONSENT_TEXT = "I confirm that I have the right to use this voice recording."


def _slugify(text: str) -> str:
    """Generate a clean, URL-friendly slug from text."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug or "voice"


class VoiceLibrary:
    """
    Manages saved reference voices on disk and records metadata in manifest.json.
    """

    MIN_DURATION_SECONDS: float = 5.0
    MAX_DURATION_SECONDS: float = 90.0

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            # Default to <project_root>/voice_library
            self.base_dir = Path(__file__).resolve().parents[2] / "voice_library"
        else:
            self.base_dir = Path(base_dir)

        self.manifest_path = self.base_dir / "manifest.json"
        self._lock = threading.Lock()
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Ensure the base storage directory and manifest exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.exists():
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    def _load_manifest(self) -> List[Dict[str, Any]]:
        """Read and return all records from manifest.json."""
        if not self.manifest_path.exists():
            return []
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error("Failed to read voice library manifest: %s", exc)
            return []

    def _save_manifest(self, data: List[Dict[str, Any]]) -> None:
        """Write records to manifest.json atomically."""
        temp_path = self.manifest_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(self.manifest_path)

    def validate_audio(self, audio_bytes: bytes) -> float:
        """
        Validate that the audio bytes form a valid audio file of 5-90s duration.

        Args:
            audio_bytes: Raw audio file content.

        Returns:
            float: Duration in seconds.

        Raises:
            ValueError: If audio is invalid or outside the 5-90 second range.
        """
        if not audio_bytes:
            raise ValueError("Audio data cannot be empty.")

        try:
            with sf.SoundFile(io.BytesIO(audio_bytes)) as sound_file:
                duration = len(sound_file) / float(sound_file.samplerate)
        except Exception as exc:
            raise ValueError(f"Invalid or unsupported audio format: {exc}") from exc

        if duration < self.MIN_DURATION_SECONDS:
            raise ValueError(
                f"Audio duration ({duration:.2f}s) is too short. "
                f"Reference audio must be between {self.MIN_DURATION_SECONDS:.0f} "
                f"and {self.MAX_DURATION_SECONDS:.0f} seconds."
            )
        if duration > self.MAX_DURATION_SECONDS:
            raise ValueError(
                f"Audio duration ({duration:.2f}s) is too long. "
                f"Reference audio must be between {self.MIN_DURATION_SECONDS:.0f} "
                f"and {self.MAX_DURATION_SECONDS:.0f} seconds."
            )

        return duration

    def _generate_unique_slug(self, display_name: str, existing_slugs: set[str]) -> str:
        """Generate a unique slug for a given display name."""
        base_slug = _slugify(display_name)
        candidate = base_slug
        counter = 2
        while candidate in existing_slugs:
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate

    def add_voice(
        self,
        display_name: str,
        language: str,
        audio_bytes: bytes,
        consent_confirmed: bool,
        consent_text_shown: str = DEFAULT_CONSENT_TEXT,
    ) -> Dict[str, Any]:
        """
        Add a reference voice to the library.

        Args:
            display_name: Human-friendly name for the voice.
            language: Language code (e.g. 'en', 'hi', 'fr').
            audio_bytes: WAV/MP3 audio file content.
            consent_confirmed: Must be True to proceed.
            consent_text_shown: The text shown to the user when confirming consent.

        Returns:
            dict: The created voice record.

        Raises:
            ValueError: If consent_confirmed is False or audio validation fails.
        """
        if not consent_confirmed:
            raise ValueError("Consent must be confirmed to save a reference voice.")

        if not display_name or not display_name.strip():
            raise ValueError("display_name must not be empty.")

        duration = self.validate_audio(audio_bytes)

        with self._lock:
            manifest = self._load_manifest()
            existing_slugs = {item.get("slug") for item in manifest}

            slug = self._generate_unique_slug(display_name.strip(), existing_slugs)
            voice_dir = self.base_dir / slug
            voice_dir.mkdir(parents=True, exist_ok=True)

            ref_wav_path = voice_dir / "reference.wav"
            ref_wav_path.write_bytes(audio_bytes)

            added_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

            record: Dict[str, Any] = {
                "slug": slug,
                "display_name": display_name.strip(),
                "language": language.strip() or "en",
                "added_at": added_at,
                "consent_confirmed": True,
                "consent_text_shown": consent_text_shown,
                "duration_seconds": round(duration, 2),
            }

            manifest.append(record)
            self._save_manifest(manifest)
            logger.info("Saved new voice '%s' (slug=%s, duration=%.2fs)", display_name, slug, duration)

            return record

    def list_voices(self) -> List[Dict[str, Any]]:
        """List all voices registered in the library manifest."""
        with self._lock:
            return self._load_manifest()

    def get_voice_path(self, slug: str) -> Optional[Path]:
        """
        Get the path to reference.wav for a given voice slug.

        Args:
            slug: The unique identifier for the voice.

        Returns:
            Path if found and exists, else None.
        """
        with self._lock:
            manifest = self._load_manifest()
            for item in manifest:
                if item.get("slug") == slug:
                    ref_path = self.base_dir / slug / "reference.wav"
                    if ref_path.exists():
                        return ref_path
        return None

    def delete_voice(self, slug: str) -> bool:
        """
        Delete a voice and its files from disk and manifest.

        Args:
            slug: The unique slug of the voice to remove.

        Returns:
            bool: True if voice existed and was deleted, False otherwise.
        """
        with self._lock:
            manifest = self._load_manifest()
            found = False
            updated_manifest = []

            for item in manifest:
                if item.get("slug") == slug:
                    found = True
                else:
                    updated_manifest.append(item)

            if not found:
                return False

            voice_dir = self.base_dir / slug
            if voice_dir.exists():
                shutil.rmtree(voice_dir, ignore_errors=True)

            self._save_manifest(updated_manifest)
            logger.info("Deleted voice with slug '%s'", slug)
            return True


_library_instance: Optional[VoiceLibrary] = None
_library_lock = threading.Lock()


def get_voice_library() -> VoiceLibrary:
    """Retrieve the process-wide VoiceLibrary singleton."""
    global _library_instance
    if _library_instance is None:
        with _library_lock:
            if _library_instance is None:
                _library_instance = VoiceLibrary()
    return _library_instance
