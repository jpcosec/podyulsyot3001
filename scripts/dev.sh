#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$API_PID" "$UI_PID" 2>/dev/null || true
  wait "$API_PID" "$UI_PID" 2>/dev/null || true
  echo "Done."
}
trap cleanup EXIT INT TERM

# --- Config ---
API_HOST="${PHD2_UI_API_HOST:-127.0.0.1}"
API_PORT="${PHD2_UI_API_PORT:-8010}"
UI_PORT="${PHD2_UI_PORT:-4173}"
export PHD2_UI_ORIGIN="http://${API_HOST}:${UI_PORT}"

# --- API ---
echo "[api] Starting on ${API_HOST}:${API_PORT} ..."
cd "$REPO_ROOT"
python -m src.cli.run_review_api &
API_PID=$!

# --- UI ---
echo "[ui]  Starting on ${API_HOST}:${UI_PORT} ..."
cd "$REPO_ROOT"
npm --prefix apps/review-workbench run dev -- --host "$API_HOST" --port "$UI_PORT" &
UI_PID=$!

echo ""
echo "=== PhD 2.0 Review Workbench ==="
echo "  UI:  http://${API_HOST}:${UI_PORT}"
echo "  API: http://${API_HOST}:${API_PORT}"
echo "  Ctrl+C to stop both."
echo ""

wait
