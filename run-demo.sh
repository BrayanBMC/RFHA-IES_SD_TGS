#!/usr/bin/env bash
# Levanta la demo en macOS/Linux con un solo comando:  bash run-demo.sh
# La app final: bash run-demo.sh --app
set -e
cd "$(dirname "$0")"
PY=$(command -v python3.12 || command -v python3.11 || command -v python3 || command -v python)
[ -z "$PY" ] && { echo "No se encontró Python 3.10+"; exit 1; }
exec "$PY" scripts/run_demo.py "$@"
