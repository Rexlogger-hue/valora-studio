@echo off
title Valora AI - Backend API Server
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py --server
) else (
    python run.py --server
)
pause
