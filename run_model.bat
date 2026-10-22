@echo off
title Valora AI - Voice Model CLI
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_voice_model.py %*
) else (
    python run_voice_model.py %*
)
pause
