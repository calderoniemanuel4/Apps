#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -x ".venv/bin/python" ]]; then
  echo "No se encontro .venv/bin/python. Ejecuta el setup local antes de resetear." >&2
  exit 1
fi

".venv/bin/python" -m app.reset_santander_attempts
