#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCHEDULE="${BOTSALDOS_CRON_SCHEDULE:-0 8 * * *}"
MARKER_START="# BEGIN BotSaldos staging"
MARKER_END="# END BotSaldos staging"
CRON_COMMAND="${SCHEDULE} \"${PROJECT_DIR}/scripts/run_sync.sh\" >> \"${PROJECT_DIR}/logs/cron_stdout.log\" 2>&1"

current_cron="$(mktemp)"
next_cron="$(mktemp)"
trap 'rm -f "${current_cron}" "${next_cron}"' EXIT

crontab -l >"${current_cron}" 2>/dev/null || true

awk \
  -v marker_start="${MARKER_START}" \
  -v marker_end="${MARKER_END}" \
  '
    $0 == marker_start { skip = 1; next }
    $0 == marker_end { skip = 0; next }
    skip != 1 { print }
  ' "${current_cron}" >"${next_cron}"

{
  if [[ -s "${next_cron}" ]]; then
    printf "\n"
  fi
  printf "%s\n" "${MARKER_START}"
  printf "%s\n" "${CRON_COMMAND}"
  printf "%s\n" "${MARKER_END}"
} >>"${next_cron}"

crontab "${next_cron}"

echo "Cron de BotSaldos staging instalado:"
echo "${CRON_COMMAND}"
