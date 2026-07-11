@echo off
title Hub de Biblioteca y Proyectos Personales
echo ========================================================
echo Iniciando Hub de Biblioteca y Proyectos Personales...
echo ========================================================
echo.

cd /d "%~dp0"

echo Lanzando Servidor Web de Lectura (Flask) en Puerto 5001...
start "Servidor Biblioteca" cmd /c "call venv\Scripts\activate.bat && python app_biblioteca.py"

echo Esperando 3 segundos a que levante el servidor...
timeout /t 3 /nobreak > nul

echo Abriendo Biblioteca en tu navegador...
start http://localhost:5001

echo.
echo ========================================================
echo ¡Todo en marcha! El servidor se ejecuta en segundo plano.
echo Puedes cerrarlo cuando termines.
echo ========================================================
pause
