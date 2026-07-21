@echo off
REM ============================================================
REM  Estudio por voz de un clic, TODO desde el portatil:
REM   1) graba tu narracion (ENTER para parar)
REM   2) transcribe (Whisper) y corrige (Claude/Opus)
REM   3) actualiza el grafo y guarda el feedback
REM ============================================================
cd /d "%~dp0"
call venv\Scripts\python.exe grabar.py --corregir
echo.
echo Pulsa una tecla para cerrar.
pause >nul
