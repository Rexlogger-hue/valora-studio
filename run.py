"""
Valora AI - Master Launcher & CLI Runner
Supports running from workspace root: C:\\Users\\rithy\\Downloads\\ValoraA (1)

Usage:
  python run.py                   -> Interactive Launcher Menu
  python run.py --server          -> Starts Studio Web UI & Backend Server (http://127.0.0.1:8000)
  python run.py --text "Hello!"   -> Generates TTS speech
  python run.py --clone --ref my_voice.wav --text "Cloning voice" -> XTTS Voice Cloning
  python run.py --transcribe ratelimit_check.wav                  -> Whisper STT Transcription
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
VALORA_DIR = ROOT_DIR / "ValoraA"
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"

# Ensure ValoraA is on sys.path
if str(VALORA_DIR) not in sys.path:
    sys.path.insert(0, str(VALORA_DIR))

os.environ["COQUI_TOS_AGREED"] = "1"


def _ensure_venv():
    """Ensure script runs inside .venv interpreter if available."""
    if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        cmd = [str(VENV_PYTHON), str(Path(__file__).resolve())] + sys.argv[1:]
        sys.exit(subprocess.call(cmd))


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if the given port is already occupied."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def start_api_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Start the FastAPI backend server and Studio Web UI."""
    if is_port_in_use(port, host):
        print(f"\n" + "="*60)
        print(f"  [Port In Use] Port {port} is already active on {host}.")
        print(f"  Valora AI Studio is available at: http://{host}:{port}")
        print(f"  If you wish to restart the server, terminate the running process first.")
        print(f"="*60 + "\n")
        return

    import uvicorn
    print(f"\n" + "="*60)
    print(f"  Starting Valora AI Studio & Backend API Server")
    print(f"  Studio Web UI: http://{host}:{port}")
    print(f"  API Docs:      http://{host}:{port}/docs")
    print(f"="*60 + "\n")
    try:
        uvicorn.run("services.api.main:app", host=host, port=port, reload=reload, app_dir=str(VALORA_DIR))
    except KeyboardInterrupt:
        print("\nValora AI Server stopped cleanly.")


def interactive_menu():
    print("\n" + "="*50)
    print("        VALORA AI - MASTER LAUNCHER")
    print("="*50)
    print("  [1] Start Valora Studio Web UI & Backend (Port 8000) [Default]")
    print("  [2] Generate Speech (Text-to-Speech CLI)")
    print("  [3] Clone Voice (XTTS-v2 with reference audio)")
    print("  [4] Transcribe Audio (Whisper STT)")
    print("  [5] Test GPU / CUDA Status")
    print("  [0] Exit")
    print("="*50)
    
    try:
        choice = input("\nEnter your choice (0-5) [1]: ").strip()
    except EOFError:
        choice = "1"
    except KeyboardInterrupt:
        print("\nExiting Valora AI Launcher.")
        sys.exit(0)
    if not choice:
        choice = "1"
    
    if choice == "1":
        start_api_server()
    elif choice == "2":
        import run_voice_model
        text = input("Enter text to speak (or press Enter for default): ").strip()
        if not text:
            text = "Hello! Your Valora AI voice model is active and running."
        run_voice_model.run_tts(text)
    elif choice == "3":
        import run_voice_model
        ref = input("Enter path to reference audio WAV (default: ValoraA/my_voice.wav): ").strip() or "my_voice.wav"
        text = input("Enter text to clone: ").strip() or "This is my cloned voice running on Valora AI."
        run_voice_model.run_voice_clone(text, ref)
    elif choice == "4":
        import run_voice_model
        audio = input("Enter path to audio file (default: ValoraA/ratelimit_check.wav): ").strip() or "ratelimit_check.wav"
        run_voice_model.run_stt(audio)
    elif choice == "5":
        import torch
        print(f"\nPyTorch Version: {torch.__version__}")
        print(f"CUDA Available:  {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"Device Name:     {torch.cuda.get_device_name(0)}")
            print(f"Device Count:    {torch.cuda.device_count()}")
        print()
    elif choice == "0":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid option. Please choose a number from 0 to 5.")


def main():
    _ensure_venv()
    
    parser = argparse.ArgumentParser(description="Valora AI Master Launcher")
    parser.add_argument("--server", action="store_true", help="Start FastAPI backend server & Studio UI")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="API host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--reload", action="store_true", default=False, help="Enable auto-reload on code changes")
    
    # Model arguments
    parser.add_argument("--text", type=str, default=None, help="Text to synthesize")
    parser.add_argument("--clone", action="store_true", help="Run XTTS voice cloning")
    parser.add_argument("--ref", type=str, default="my_voice.wav", help="Reference audio file for cloning")
    parser.add_argument("--voice", type=str, default="v2/en_speaker_6", help="Voice preset")
    parser.add_argument("--age", type=int, default=None, help="Apparent age (1-100)")
    parser.add_argument("--pitch", type=float, default=None, help="Pitch shift in semitones")
    parser.add_argument("--emotion", type=str, default="neutral", help="Emotion style (neutral, warm, confident, cheerful, serious, whisper, empathetic, dramatic)")
    parser.add_argument("--emotion-intensity", type=int, default=45, help="Emotion intensity (0-100)")
    parser.add_argument("--speed", type=float, default=None, help="Playback speed (0.5 to 2.0)")
    parser.add_argument("--output", type=str, default="outputs/tts/generated_voice.wav", help="Output WAV file path")
    parser.add_argument("--transcribe", type=str, default=None, help="Audio file to transcribe")
    
    args = parser.parse_args()
    
    if args.server:
        start_api_server(host=args.host, port=args.port, reload=args.reload)
    elif args.text:
        import run_voice_model
        run_voice_model.run_tts(
            text=args.text,
            voice=args.voice,
            age=args.age,
            pitch=args.pitch,
            emotion=args.emotion,
            emotion_intensity=args.emotion_intensity,
            speed=args.speed,
            output=args.output
        )
    elif args.clone:
        import run_voice_model
        text = args.text or "This is my cloned voice created with Valora AI neural audio studio."
        run_voice_model.run_voice_clone(
            text=text,
            reference_wav=args.ref,
            output=args.output
        )
    elif args.transcribe:
        import run_voice_model
        run_voice_model.run_stt(audio_file=args.transcribe)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
