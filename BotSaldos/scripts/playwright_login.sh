#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -x ".venv/bin/python" ]]; then
  echo "No se encontro .venv/bin/python. Ejecuta el setup local antes de iniciar login." >&2
  exit 1
fi

if [[ -z "${PLAYWRIGHT_LOGIN_URL:-}" ]]; then
  echo "Falta PLAYWRIGHT_LOGIN_URL. Ejemplo:" >&2
  echo "PLAYWRIGHT_LOGIN_URL='https://portal.example.com/login' ./scripts/playwright_login.sh" >&2
  exit 1
fi

".venv/bin/python" -m app.playwright_login
