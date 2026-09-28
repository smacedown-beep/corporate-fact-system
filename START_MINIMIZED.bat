@echo off
@chcp 65001 >nul
if not "%1"=="min" (
    start /min "" "%~f0" min
    exit
)
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python src\dashboard\web_app.py
