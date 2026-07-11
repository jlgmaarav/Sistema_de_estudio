@echo off
REM Corregir lo nuevo del reMarkable con un doble clic.
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" corregir.py %*
) else (
    python corregir.py %*
)
echo.
pause
