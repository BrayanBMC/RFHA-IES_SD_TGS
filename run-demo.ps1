# Levanta la demo (o la app final) en Windows con un solo comando:
#   .\run-demo.ps1            demo en el puerto 8000
#   .\run-demo.ps1 -App       app final en el puerto 8001
#   .\run-demo.ps1 -Port 8010 otro puerto
# Busca un Python 3.12 / 3.11 instalado y ejecuta scripts/run_demo.py.
param([int]$Port = 0, [switch]$App)

$candidates = @(
    "$env:LOCALAPPDATA\Python\pythoncore-3.12-64\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
)
$python = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $python) {
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $python) {
    Write-Host "No se encontró Python. Instala Python 3.12 desde https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

$arguments = @("$PSScriptRoot\scripts\run_demo.py")
if ($App) { $arguments += "--app" }
if ($Port -gt 0) { $arguments += @("--port", $Port) }

Write-Host "Usando Python: $python"
& $python @arguments
