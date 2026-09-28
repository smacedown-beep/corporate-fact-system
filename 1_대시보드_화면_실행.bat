@echo off
@chcp 65001 >nul
title Corporate Investment FACT System
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"

echo ============================================================
echo   Corporate Investment FACT System
echo   Starting server at http://127.0.0.1:8501 ...
echo ============================================================

python src\dashboard\web_app.py
if errorlevel 1 (
    echo.
    echo [ERROR] Server terminated unexpectedly.
    pause
)
