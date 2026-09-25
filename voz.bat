@echo off
REM ============================================================
REM  Estudio por voz de un clic:
REM  transcribe (Whisper) y prepara la correccion en Gemini Web.
REM  El prompt se copia al portapapeles; la respuesta JSON se pega
REM  despues en el Centro de Estudio. O arrastra un audio/.txt sobre este .bat.
REM ============================================================
cd /d "%~dp0"
set "STUDY_PY=%USERPROFILE%\SistemaEstudioRuntime\venv\Scripts\python.exe"
echo Estudio por voz: transcribiendo y corrigiendo...
echo.
call "%STUDY_PY%" corregir_voz.py %*
echo.
echo Pulsa una tecla para cerrar.
pause >nul
