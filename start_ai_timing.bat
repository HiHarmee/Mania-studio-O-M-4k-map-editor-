@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo AI timing is not installed yet. Run setup_ai_timing.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" ai_timing_server.py
pause
