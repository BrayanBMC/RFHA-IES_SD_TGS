@echo off
rem Levanta la demo en Windows sin cambiar la politica de ejecucion de PowerShell.
rem Uso:  run-demo.cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-demo.ps1" %*
