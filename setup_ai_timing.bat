@echo off
setlocal
cd /d "%~dp0"

set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 (
  call :find_py 12
  if not defined PY_CMD call :find_py 11
  if not defined PY_CMD call :find_py 13
  if not defined PY_CMD call :find_default_py
)

if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 (
    for /f "tokens=1,2" %%A in ('python -c "import sys; print(sys.version_info[0], sys.version_info[1])" 2^>nul') do (
      if "%%A"=="3" set "PY_CMD=python"
    )
  )
)

if not defined PY_CMD (
  echo No usable Python 3 runtime was found.
  echo Install Python 3.11 or 3.12, then run this setup again.
  pause
  exit /b 1
)

echo Using %PY_CMD%
if not exist ".venv\Scripts\python.exe" (
  %PY_CMD% -m venv .venv
  if errorlevel 1 goto venv_failed
)

if not exist ".venv\Scripts\python.exe" goto venv_failed

call ".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
call ".venv\Scripts\python.exe" -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto failed
call ".venv\Scripts\python.exe" -m pip install beat-this
if errorlevel 1 goto failed

echo.
echo Setup complete. Run start_ai_timing.bat to launch the local AI timing service.
pause
exit /b 0

:find_py
for /f "tokens=1,2" %%A in ('py -3.%1 -c "import sys; print(sys.version_info[0], sys.version_info[1])" 2^>nul') do (
  if "%%A %%B"=="3 %1" set "PY_CMD=py -3.%1"
)
exit /b 0

:find_default_py
for /f "tokens=1,2" %%A in ('py -3 -c "import sys; print(sys.version_info[0], sys.version_info[1])" 2^>nul') do (
  if "%%A"=="3" set "PY_CMD=py -3"
)
exit /b 0

:venv_failed
echo.
echo Could not create .venv using %PY_CMD%.
echo Confirm that this Python installation is usable and that this folder is writable.
goto failed

:failed
echo.
echo Setup failed. Check the error above and see AI_TIMING_SETUP.md.
pause
exit /b 1
