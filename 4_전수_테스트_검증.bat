@echo off
@chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python -m unittest discover -s tests -p "test_*.py"
pause
