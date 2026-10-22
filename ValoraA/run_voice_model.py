"""
Valora AI - Voice Model CLI Runner & Demo Tool

Usage:
    python run_voice_model.py --text "Hello world! This is my AI voice."
    python run_voice_model.py --text "Cloning my voice now!" --clone --ref my_voice.wav
    python run_voice_model.py --transcribe ratelimit_check.wav
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Ensure project root is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"

# Auto-switch to .venv python if running under an unconfigured Python interpreter
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    cmd = [str(VENV_PYTHON), str(Path(__file__).resolve())] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

os.environ["COQUI_TOS_AGREED"] = "1"


def _resolve_file(file_path: str) -> Path:
    p = Path(file_path).resolve()
    if p.exists():
        return p
    if (SCRIPT_DIR / file_path).exists():
        return (SCRIPT_DIR / file_path).resolve()
    if (SCRIPT_DIR.parent / file_path).exists():
        return (SCRIPT_DIR.parent / file_path).resolve()
    return p


def run_tts(
    text: str,
    voice: str = "v2/en_speaker_6",
    age: int = None,
    pitch: float = None,
    emotion: str = "neutral",
    emotion_intensity: int = 45,
    speed: float = None,
    output: str = "outputs/tts/generated_voice.wav",
):
    from services.tts.inference import get_tts_service, SynthesisRequest
    
    print(f"\n[TTS] Synthesizing speech...")
    print(f"  - Text: \"{text}\"")
    print(f"  - Voice: {voice}")
    print(f"  - Emotion: {emotion} (intensity: {emotion_intensity}%)")
    if age is not None:
        print(f"  - Target Age: {age}")
    if pitch is not None:
        print(f"  - Pitch Shift: {pitch} semitones")
    if speed is not None:
        print(f"  - Speed: {speed}x")
        
    service = get_tts_service()
    service.warm_up()
    
    req = SynthesisRequest(
        text=text,
        voice_preset=voice,
        age=age,
        pitch_semitones=pitch,
        emotion=emotion,
        emotion_intensity=emotion_intensity,
        speed=speed,
    )
    result = service.synthesize(req)
    
    out_path = Path(output)
    if not out_path.is_absolute():
        out_path = SCRIPT_DIR / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(result.audio_bytes)
        
    print(f"[TTS] Generated {result.duration_seconds:.2f}s of audio -> {out_path}\n")
    return out_path


def run_voice_clone(text: str, reference_wav: str, language: str = "en", output: str = "outputs/tts/cloned_output.wav"):
    from services.tts.clone_model import VoiceCloneModel
    
    ref_path = _resolve_file(reference_wav)
    if not ref_path.exists():
        print(f"[ERROR] Reference audio not found: {reference_wav}")
        print(f"  Looked in:\n    - {Path(reference_wav).resolve()}\n    - {SCRIPT_DIR / reference_wav}")
        sys.exit(1)
        
    print(f"\n[Voice Clone] Cloning voice from: {ref_path.name}")
    print(f"  - Reference file: {ref_path}")
    print(f"  - Text: \"{text}\"")
    print(f"  - Language: {language}")
    
    clone_service = VoiceCloneModel()
    clone_service.load()
    
    out_path = Path(output)
    if not out_path.is_absolute():
        out_path = SCRIPT_DIR / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    clone_service.clone_to_file(
        text=text,
        speaker_wav_path=str(ref_path),
        output_path=str(out_path),
        language=language,
    )
    print(f"[Voice Clone] Cloned audio written -> {out_path}\n")
    return out_path


def run_stt(audio_file: str, language: str = None):
    from services.stt.model import SpeechToTextModel
    
    audio_path = _resolve_file(audio_file)
    if not audio_path.exists():
        print(f"[ERROR] Audio file not found: {audio_file}")
        print(f"  Looked in:\n    - {Path(audio_file).resolve()}\n    - {SCRIPT_DIR / audio_file}")
        sys.exit(1)
        
    print(f"\n[STT] Transcribing audio: {audio_path.name}...")
    stt = SpeechToTextModel()
    stt.load()
    
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
        
    result = stt.transcribe(audio_bytes, language=language)
    print(f"\n--- Transcription Result ---")
    print(f"Detected Language: {result.language} (Confidence: {result.language_probability:.2%})")
    print(f"Text: {result.text}\n")
    return result


def main():
    parser = argparse.ArgumentParser(description="Valora AI Voice Model Runner")
    parser.add_argument("--text", type=str, default="Hello! Your Valora AI voice model is active and running.", help="Text to speak")
    parser.add_argument("--clone", action="store_true", help="Run XTTS voice cloning with reference audio")
    parser.add_argument("--ref", type=str, default="my_voice.wav", help="Reference audio file for cloning")
    parser.add_argument("--voice", type=str, default="v2/en_speaker_6", help="Voice preset")
    parser.add_argument("--age", type=int, default=None, help="Apparent age (1-100)")
    parser.add_argument("--pitch", type=float, default=None, help="Pitch shift in semitones")
    parser.add_argument("--emotion", type=str, default="neutral", help="Emotion style (neutral, warm, confident, cheerful, serious, whisper, empathetic, dramatic)")
    parser.add_argument("--emotion-intensity", type=int, default=45, help="Emotion intensity (0-100)")
    parser.add_argument("--speed", type=float, default=None, help="Playback speed (0.5 to 2.0)")
    parser.add_argument("--output", type=str, default="outputs/tts/generated_voice.wav", help="Output WAV file path")
    parser.add_argument("--transcribe", type=str, default=None, help="Path to audio file to transcribe")
    
    args = parser.parse_args()
    
    if args.transcribe:
        run_stt(args.transcribe)
    elif args.clone:
        run_voice_clone(args.text, args.ref, output=args.output)
    else:
        run_tts(
            args.text,
            voice=args.voice,
            age=args.age,
            pitch=args.pitch,
            emotion=args.emotion,
            emotion_intensity=args.emotion_intensity,
            speed=args.speed,
            output=args.output,
        )


if __name__ == "__main__":
    main()
