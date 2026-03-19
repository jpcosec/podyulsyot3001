#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NEO4J_COMPOSE_FILE="${NEO4J_COMPOSE_FILE:-$REPO_ROOT/docker-compose.neo4j.yml}"

API_HOST="${PHD2_UI_API_HOST:-127.0.0.1}"
API_PORT="${PHD2_UI_API_PORT:-8010}"
UI_PORT="${PHD2_UI_PORT:-4173}"
NEO4J_HTTP_PORT="${PHD2_NEO4J_HTTP_PORT:-7474}"
START_NEO4J="${START_NEO4J:-1}"
BOOTSTRAP_SCHEMA="${BOOTSTRAP_SCHEMA:-1}"
STOP_NEO4J_ON_EXIT="${STOP_NEO4J_ON_EXIT:-0}"
WAIT_TIMEOUT_SECS="${WAIT_TIMEOUT_SECS:-90}"

pick_available_port() {
  local start_port="$1"
  local max_tries=20
  local candidate
  local i

  for ((i = 0; i < max_tries; i++)); do
    candidate=$((start_port + i))
    if python - "$candidate" <<'PY'
import socket
import sys

port = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(("127.0.0.1", port))
except OSError:
    raise SystemExit(1)
finally:
    s.close()

raise SystemExit(0)
PY
    then
      echo "$candidate"
      return 0
    fi
  done

  echo "No free port found starting at ${start_port}" >&2
  exit 1
}

API_PORT_SELECTED="$(pick_available_port "$API_PORT")"
UI_PORT_SELECTED="$(pick_available_port "$UI_PORT")"

if [[ "$API_PORT_SELECTED" != "$API_PORT" ]]; then
  echo "[api] Requested port ${API_PORT} is busy, using ${API_PORT_SELECTED}."
fi
if [[ "$UI_PORT_SELECTED" != "$UI_PORT" ]]; then
  echo "[ui] Requested port ${UI_PORT} is busy, using ${UI_PORT_SELECTED}."
fi

API_PORT="$API_PORT_SELECTED"
UI_PORT="$UI_PORT_SELECTED"
export PHD2_UI_API_PORT="$API_PORT"
export PHD2_UI_ORIGIN="http://${API_HOST}:${UI_PORT}"

API_PID=""
UI_PID=""

cleanup() {
  echo ""
  echo "Shutting down dev services..."
  if [[ -n "$API_PID" ]]; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
  fi
  if [[ -n "$UI_PID" ]]; then
    kill "$UI_PID" 2>/dev/null || true
    wait "$UI_PID" 2>/dev/null || true
  fi
  if [[ "$STOP_NEO4J_ON_EXIT" == "1" && "$START_NEO4J" == "1" ]]; then
    docker compose -f "$NEO4J_COMPOSE_FILE" down >/dev/null 2>&1 || true
  fi
  echo "Done."
}
trap cleanup EXIT INT TERM

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

wait_for_http() {
  local url="$1"
  local name="$2"
  local timeout="$3"
  local waited=0

  until curl -fsS "$url" >/dev/null 2>&1; do
    sleep 1
    waited=$((waited + 1))
    if ((waited >= timeout)); then
      echo "Timed out waiting for ${name}: ${url}" >&2
      exit 1
    fi
  done
}

require_cmd python
require_cmd npm
require_cmd curl

if [[ "$START_NEO4J" == "1" ]]; then
  require_cmd docker
  echo "[neo4j] Starting container..."
  docker compose -f "$NEO4J_COMPOSE_FILE" up -d
  echo "[neo4j] Waiting for browser endpoint..."
  wait_for_http "http://${API_HOST}:${NEO4J_HTTP_PORT}" "neo4j" "$WAIT_TIMEOUT_SECS"
fi

if [[ ! -d "$REPO_ROOT/apps/review-workbench/node_modules" ]]; then
  echo "[ui] Installing dependencies..."
  npm --prefix "$REPO_ROOT/apps/review-workbench" install
fi

echo "[api] Starting on ${API_HOST}:${API_PORT} ..."
cd "$REPO_ROOT"
python -m src.cli.run_review_api &
API_PID=$!

echo "[api] Waiting for health endpoint..."
wait_for_http "http://${API_HOST}:${API_PORT}/health" "review api" "$WAIT_TIMEOUT_SECS"

if [[ "$START_NEO4J" == "1" && "$BOOTSTRAP_SCHEMA" == "1" ]]; then
  echo "[neo4j] Bootstrapping schema constraints..."
  curl -fsS -X POST "http://${API_HOST}:${API_PORT}/api/v1/neo4j/bootstrap-schema" >/dev/null
fi

echo "[ui]  Starting on ${API_HOST}:${UI_PORT} ..."
cd "$REPO_ROOT"
npm --prefix apps/review-workbench run dev -- --host "$API_HOST" --port "$UI_PORT" --strictPort &
UI_PID=$!

echo ""
echo "=== PhD 2.0 Full Dev Stack ==="
echo "  UI:     http://${API_HOST}:${UI_PORT}"
echo "  API:    http://${API_HOST}:${API_PORT}"
if [[ "$START_NEO4J" == "1" ]]; then
  echo "  Neo4j:  http://${API_HOST}:${NEO4J_HTTP_PORT}"
fi
echo ""
echo "Environment toggles:"
echo "  START_NEO4J=0         # skip docker start"
echo "  BOOTSTRAP_SCHEMA=0    # skip schema bootstrap call"
echo "  STOP_NEO4J_ON_EXIT=1  # run docker compose down on exit"
echo ""
echo "Ctrl+C stops UI/API (and optionally Neo4j)."

wait
