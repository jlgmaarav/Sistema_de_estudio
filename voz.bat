@echo off
REM ============================================================
REM  Estudio por voz de un clic:
REM  transcribe (Whisper) y corrige (Claude) la grabacion mas
REM  nueva de grabaciones\, actualiza el grafo y guarda el
REM  feedback. O arrastra un audio/.txt sobre este .bat.
REM ============================================================
cd /d "%~dp0"
echo Estudio por voz: transcribiendo y corrigiendo...
echo.
call venv\Scripts\python.exe corregir_voz.py %*
echo.
echo Pulsa una tecla para cerrar.
pause >nul
