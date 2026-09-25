@echo off
REM ============================================================
REM  Transcribe una grabacion a texto con Whisper (local, gratis)
REM  - Doble clic: transcribe el audio MAS NUEVO de grabaciones\
REM  - O arrastra un archivo de audio sobre este .bat
REM ============================================================
cd /d "%~dp0"
set "STUDY_PY=%USERPROFILE%\SistemaEstudioRuntime\venv\Scripts\python.exe"
echo Transcribiendo con Whisper...
echo (la primera vez descarga el modelo, ~1.6 GB, una sola vez)
echo.
call "%STUDY_PY%" transcribir.py %*
echo.
echo Pulsa una tecla para cerrar.
pause >nul
