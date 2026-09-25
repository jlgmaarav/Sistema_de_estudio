@echo off
title IA Physics Study System - Centro de Estudio
echo ========================================================
echo Iniciando Centro de Estudio (Student Hub)...
echo ========================================================
echo.

cd /d "%~dp0"
set "STUDY_PY=%USERPROFILE%\SistemaEstudioRuntime\venv\Scripts\python.exe"
if not exist "%STUDY_PY%" set "STUDY_PY=%~dp0venv\Scripts\python.exe"
if not exist "%STUDY_PY%" set "STUDY_PY=python"
if /I not "%STUDY_PY%"=="python" (
    "%STUDY_PY%" -c "import flask, flask_cors" >nul 2>&1
    if errorlevel 1 set "STUDY_PY=python"
)

echo Lanzando Servidor Web (Flask) en Puerto 5000...
start "Hub Servidor Web" "%STUDY_PY%" app.py

echo Esperando a que levante el servidor...
for /l %%i in (1,1,30) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5000/' -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 goto :server_ready
    timeout /t 1 /nobreak >nul
)

:server_ready

echo Abriendo Centro de Estudio en tu navegador...
start "" http://localhost:5000

echo.
echo Todo en marcha. Abriendo navegador...
ping 127.0.0.1 -n 2 > nul
exit
