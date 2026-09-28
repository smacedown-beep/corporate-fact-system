@echo off
@chcp 65001 >nul
echo Stopping FACT System...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501') do taskkill /f /pid %%a >nul 2>nul
taskkill /f /im python.exe >nul 2>nul
taskkill /f /im pythonw.exe >nul 2>nul
echo FACT System stopped successfully.
timeout /t 2 >nul
exit
