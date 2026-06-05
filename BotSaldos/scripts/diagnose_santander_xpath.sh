#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -x ".venv/bin/python" ]]; then
  echo "No se encontro .venv/bin/python. Ejecuta el setup local antes de diagnosticar." >&2
  exit 1
fi

".venv/bin/python" -m app.diagnose_santander_xpath
