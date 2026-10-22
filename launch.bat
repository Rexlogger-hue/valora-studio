@echo off
title AI4Bharat Indic-Parler-TTS
cd /d "%~dp0"

echo ================================================================
echo           AI4Bharat Indic-Parler-TTS (Hindi) Launcher
echo ================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Setting up .venv...
    py -3.11 -m venv .venv
    if errorlevel 1 (
        python -m venv .venv
    )
    echo [*] Installing dependencies...
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo [*] Starting Gradio Web Application on http://127.0.0.1:7860 ...
.\.venv\Scripts\python.exe app.py
pause
