@echo off
REM ============================================================
REM  Estudio por voz de un clic, TODO desde el portatil:
REM   1) graba tu narracion (ENTER para parar)
REM   2) transcribe (Whisper) y prepara el análisis en Gemini Web
REM   3) actualiza el grafo y guarda el feedback
REM ============================================================
cd /d "%~dp0"
set "STUDY_PY=%USERPROFILE%\SistemaEstudioRuntime\venv\Scripts\python.exe"
call "%STUDY_PY%" grabar.py --corregir
echo.
echo Pulsa una tecla para cerrar.
pause >nul
