#!/bin/bash
# Claude UI Loop — runs until all phases are complete
# Usage: ./scripts/claude-ui-loop.sh [session-id]
# If no session-id provided, creates new sessions automatically

set -e

LOG_DIR="logs"
SESSION_ID="${1:-}"
LOG_FILE="$LOG_DIR/claude-loop-$(date +%Y%m%d-%H%M).log"
TARGET_TIME="04:30"

mkdir -p "$LOG_DIR"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

# Wait until target time
wait_until_target() {
    local target="$TARGET_TIME"
    local now
    now=$(date +%H:%M)
    
    if [[ "$now" < "$target" ]]; then
        local wait_sec=$(( $(date -d "$target" +%s) - $(date +%s) ))
        local wait_min=$(( wait_sec / 60 ))
        log "Sleeping ${wait_min}m until $target..."
        sleep "$wait_sec"
    fi
}

# Commit current state if there are changes
commit_if_dirty() {
    if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
        log "Committing pending changes..."
        git add -A
        git commit -m "WIP: in-progress changes from claude loop" || true
    fi
}

# Check if all phases are done
check_all_done() {
    if grep -q "^\- \[ \] " plan/index_checklist.md 2>/dev/null; then
        return 1  # Not done
    fi
    return 0  # Done
}

# Get next pending phase from checklist
get_next_phase() {
    grep "^\- \[ \] " plan/index_checklist.md | head -1 | sed 's/- \[ \] //' | cut -d' ' -f1
}

# Run claude with retry logic
run_claude() {
    local session="$1"
    local prompt="$2"
    local max_retries=3
    local retry_count=0
    
    while [[ $retry_count -lt $max_retries ]]; do
        log "Running Claude (session: ${session:-(new)}, attempt $((retry_count + 1))/$max_retries)"
        
        if [[ -n "$session" ]]; then
            claude --dangerously-skip-permissions --resume "$session" "$prompt" 2>&1 | tee -a "$LOG_FILE"
        else
            claude --dangerously-skip-permissions "$prompt" 2>&1 | tee -a "$LOG_FILE"
        fi
        
        EXIT_CODE=${PIPESTATUS[0]}
        
        if [[ $EXIT_CODE -eq 0 ]]; then
            log "Claude completed successfully"
            return 0
        else
            retry_count=$((retry_count + 1))
            log "Claude exited with code $EXIT_CODE"
            
            if [[ $retry_count -lt $max_retries ]]; then
                log "Retrying in 30s..."
                sleep 30
            fi
        fi
    done
    
    log "Max retries reached"
    return 1
}

# Main prompt for Claude
build_prompt() {
    cat << 'EOF'
Continue implementing the UI plan. Check plan/index_checklist.md for what's next.

IMPORTANT RULES:
1. We are ONLY doing UI with mocks - NO backend changes
2. If a test fails, FIX it before reporting completion - don't just document the failure
3. Run tests after each component: cd apps/review-workbench && npm test 2>&1 | tail -20
4. If npm test has issues, try: cd apps/review-workbench && npm run build
5. After completing a phase: COMMIT with feat(ui): format, update changelog.md, mark [x] in plan/index_checklist.md

For each phase:
1. Read spec: plan/01_ui/specs/<spec-id>.md
2. Check Migration Notes for legacy code in dev branch
3. Install any missing npm packages: cd apps/review-workbench && npm install <package>
4. Implement atoms first if missing (Tag.tsx, Kbd.tsx, etc.)
5. Implement components in features/ folder
6. Connect to hooks in features/<feature>/api/
7. Run tests and FIX failures - do not skip
8. When done: commit, changelog, mark checklist

Check what's already implemented before creating new files:
- Look in apps/review-workbench/src/components/atoms/
- Look in apps/review-workbench/src/features/

Report: what you did, what tests passed/failed, what's next.
Say DONE when no phases remain (grep "^\- \[ \] " plan/index_checklist.md returns empty).
EOF
}

# ─── Main Loop ────────────────────────────────────────────────────────────────

wait_until_target

log "Starting Claude UI loop..."
log "Session: ${SESSION_ID:-(will create new)}"
log "Log: $LOG_FILE"

ITERATION=0

while true; do
    ITERATION=$((ITERATION + 1))
    log ""
    log "════════════════════════════════════════════════"
    log "Iteration $ITERATION"
    
    # Check if done
    if check_all_done; then
        log "ALL PHASES COMPLETE!"
        break
    fi
    
    # Get what's next
    NEXT=$(get_next_phase)
    log "Next phase: $NEXT"
    
    # Commit any pending changes before starting
    commit_if_dirty
    
    # Build and run prompt
    PROMPT=$(build_prompt)
    run_claude "$SESSION_ID" "$PROMPT"
    
    # After Claude runs, commit if there are new changes
    commit_if_dirty
    
    # Check again
    if check_all_done; then
        log "All phases complete after iteration $ITERATION!"
        break
    fi
    
    log "Phase not complete, waiting 2min before next iteration..."
    sleep 120

done

log "Loop finished! All phases implemented."
