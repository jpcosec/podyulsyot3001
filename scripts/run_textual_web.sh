#!/bin/bash
# Start textual-web server for browser-based TUI access
# Enables TestSprite and manual browser testing of the Review UI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Starting textual-web server..."
echo "Configuration: textual_web.toml"
echo "URL: http://localhost:8765/review-ui/"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

textual-web --config textual_web.toml
