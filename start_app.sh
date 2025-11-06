#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -f "$VENV_DIR/bin/python" ]; then
  echo "[setup] Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
  echo "[setup] Upgrading pip..."
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  echo "[setup] Installing dependencies..."
  "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

source "$VENV_DIR/bin/activate"
export FLASK_APP=app.py
exec python "$SCRIPT_DIR/app.py"
