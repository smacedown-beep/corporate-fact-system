@echo off
@chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python src\core\orchestrator.py
pause
