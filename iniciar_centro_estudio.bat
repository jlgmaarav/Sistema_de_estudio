@echo off
title IA Physics Study System - Centro de Estudio
echo ========================================================
echo Iniciando Centro de Estudio (Student Hub)...
echo ========================================================
echo.

cd /d "%~dp0"

echo Sincronizando apuntes desde reMarkable Cloud...
call venv\Scripts\activate.bat && python sync_remarkable.py
echo.

echo Lanzando Servidor Web (Flask) en Puerto 5000...
start "Hub Servidor Web" cmd /c "call venv\Scripts\activate.bat && python app.py"

echo Lanzando Watcher de Archivos (Inbox/)...
start "Hub Watcher de Archivos" cmd /c "call venv\Scripts\activate.bat && python watcher.py"

echo Esperando 3 segundos a que levante el servidor...
timeout /t 3 /nobreak > nul

echo Abriendo Centro de Estudio en tu navegador...
start http://localhost:5000

echo.
echo ========================================================
echo ¡Todo en marcha! Las ventanas en segundo plano están ejecutándose.
echo Puedes cerrarlas cuando termines de estudiar.
echo ========================================================
pause
