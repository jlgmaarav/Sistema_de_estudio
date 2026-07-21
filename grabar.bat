@echo off
REM ============================================================
REM  Graba tu voz desde el portatil directo a grabaciones\.
REM  Narra mientras resuelves; pulsa ENTER para parar.
REM  (solo graba; para corregir usa voz.bat o estudiar.bat)
REM ============================================================
cd /d "%~dp0"
call venv\Scripts\python.exe grabar.py
echo.
echo Pulsa una tecla para cerrar.
pause >nul
