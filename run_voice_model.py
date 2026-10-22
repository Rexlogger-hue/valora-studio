"""
Valora AI - Voice Model Runner (Root Wrapper)
Allows running directly from C:\\Users\\rithy\\Downloads\\ValoraA (1)
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
VALORA_DIR = ROOT_DIR / "ValoraA"
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"

# Auto-use virtual environment Python if available and not already using it
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    cmd = [str(VENV_PYTHON), str(Path(__file__).resolve())] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))

# Ensure ValoraA is in sys.path
if str(VALORA_DIR) not in sys.path:
    sys.path.insert(0, str(VALORA_DIR))

# Re-route to the main runner in ValoraA
if __name__ == "__main__":
    import run_voice_model
    run_voice_model.main()
