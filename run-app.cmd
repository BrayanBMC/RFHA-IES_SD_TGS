@echo off
rem Levanta la app final (puerto 8001) sin cambiar la politica de ejecucion de PowerShell.
rem Uso:  run-app.cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-demo.ps1" -App %*
