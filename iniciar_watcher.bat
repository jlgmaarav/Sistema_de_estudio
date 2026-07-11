@echo off
title IA Physics Study System - Watcher
echo ========================================================
echo Iniciando Watcher para el Sistema de Estudio Asistido por IA...
echo ========================================================
echo Carpeta vigilada: Inbox/
echo Para detener el proceso, cierra esta ventana o pulsa Ctrl+C.
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat
python watcher.py
pause
