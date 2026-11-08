# Levanta la demo en Windows con un solo comando:  .\run-demo.ps1
# Busca un Python 3.12 / 3.11 instalado y ejecuta scripts/run_demo.py.
param([int]$Port = 8000)

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

Write-Host "Usando Python: $python"
& $python "$PSScriptRoot\scripts\run_demo.py" --port $Port
