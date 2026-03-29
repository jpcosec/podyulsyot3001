#!/bin/bash
# scripts/postulator.sh - Unified launcher for Postulator 3000

set -e

TARGET_URL=$(python3 -m src.cli.main api start)

# 2. Launch the Job Manager TUI
export LANGGRAPH_API_URL="$TARGET_URL"
echo "  [🚀] Launching Job Manager TUI connecting to $LANGGRAPH_API_URL..."
python3 -m src.cli.main review
