#!/usr/bin/env bash
# PhD 2.0 Hook Installation Script
# Run this after cloning or to reinstall hooks

set -e

echo "🔧 PhD 2.0: Installing Git hooks..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$SCRIPT_DIR/hooks"

# Copy hooks to .git/hooks
cp "$HOOKS_DIR/commit-msg" .git/hooks/commit-msg
cp "$HOOKS_DIR/pre-push" .git/hooks/pre-push

# Make hooks executable
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-push

echo "✅ PhD 2.0 hooks installed:"
echo "   - commit-msg: Validates message format + TestSprite evidence"
echo "   - pre-push: Runs tests before push"
echo ""
echo "To reinstall: bash scripts/setup_hooks.sh"
