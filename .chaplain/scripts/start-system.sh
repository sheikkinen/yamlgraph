#!/usr/bin/env bash
# start-system.sh — Start the full watcher FSM system (FR-296)
#
# Phases: prerequisites → cleanup → validate+diagrams → start UI → start dispatcher → keep-alive
# The UI must start first (creates event socket), then dispatcher connects to it.
#
# Usage:
#   .chaplain/scripts/start-system.sh [--inbox DIR]
#
# Options:
#   --inbox DIR   Override inbox directory (default: .chaplain/inbox)

set -euo pipefail

# Change to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_DIR=".chaplain/config"
ACTIONS_DIR=".chaplain/actions"
CONFIG_FILES=(
    "$CONFIG_DIR/watcher-dispatcher.yaml"
    "$CONFIG_DIR/watcher-pipeline.yaml"
)
INBOX_DIR=".chaplain/inbox"
UI_PORT=3001
EVENT_SOCKET="/tmp/statemachine-events.sock"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --inbox)
            INBOX_DIR="$2"
            shift 2
            ;;
        --inbox=*)
            INBOX_DIR="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--inbox DIR]"
            exit 1
            ;;
    esac
done

# PIDs tracked for cleanup
UI_PID=""
DISPATCHER_PID=""

# =============================================================================
# CLEANUP FUNCTION
# =============================================================================

cleanup() {
    echo ""
    echo "🛑 Shutting down all services..."

    # Kill by saved PID first
    if [[ -n "$DISPATCHER_PID" ]]; then
        kill "$DISPATCHER_PID" 2>/dev/null || true
        echo "✓ Dispatcher stopped (PID $DISPATCHER_PID)"
    fi

    if [[ -n "$UI_PID" ]]; then
        kill "$UI_PID" 2>/dev/null || true
        echo "✓ Web UI stopped (PID $UI_PID)"
    fi

    # Fallback: kill any spawned pipeline processes
    pkill -f "statemachine .chaplain" 2>/dev/null || true

    # Clean up PID files
    rm -f logs/fsm-ui.pid logs/fsm-dispatcher.pid

    echo "🏁 All services stopped"
    exit 0
}

trap cleanup INT TERM

# =============================================================================
# PHASE 0: PREREQUISITES
# =============================================================================

echo "🚀 Starting Watcher FSM System"
echo "========================================"
echo ""

# Check virtual environment
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    if [[ -f ".venv/bin/activate" ]]; then
        echo "📦 Activating virtual environment..."
        # shellcheck disable=SC1091
        source .venv/bin/activate
    else
        echo "❌ Virtual environment not activated and .venv/ not found"
        echo "   Run: python -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'"
        exit 1
    fi
fi

echo "🔍 Checking requirements..."
for cmd in statemachine statemachine-ui statemachine-validate statemachine-diagrams; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "❌ Required command not found: $cmd"
        echo "   Install with: pip install statemachine-engine"
        exit 1
    fi
done
echo "✓ All required commands available"

for config in "${CONFIG_FILES[@]}"; do
    if [[ ! -f "$config" ]]; then
        echo "❌ Config not found: $config"
        exit 1
    fi
done
echo "✓ Config files present"

if [[ ! -d "$ACTIONS_DIR" ]]; then
    echo "❌ Actions directory not found: $ACTIONS_DIR"
    exit 1
fi
echo "✓ Actions directory present"

mkdir -p logs data "$INBOX_DIR"
echo "✓ Directories ready (logs/, data/, $INBOX_DIR)"
echo ""

# =============================================================================
# PHASE 1: CLEANUP
# =============================================================================

echo "=========================================="
echo "PHASE 1: Cleanup"
echo "=========================================="
echo ""

# Kill by PID files first
for pidfile in logs/fsm-ui.pid logs/fsm-dispatcher.pid; do
    if [[ -f "$pidfile" ]]; then
        kill "$(cat "$pidfile")" 2>/dev/null || true
        rm -f "$pidfile"
    fi
done

# Fallback kill
pkill -f "statemachine .chaplain" 2>/dev/null || true
pkill -f "statemachine-ui.*--project-root" 2>/dev/null || true

# Stale artifacts
rm -f "$EVENT_SOCKET"
rm -f data/pipeline.db

echo "✓ Stale processes and artifacts cleaned"
echo ""

# =============================================================================
# PHASE 2: VALIDATE & GENERATE DIAGRAMS
# =============================================================================

echo "=========================================="
echo "PHASE 2: Configuration & Diagrams"
echo "=========================================="
echo ""

echo "🔍 Validating configurations..."
for config in "${CONFIG_FILES[@]}"; do
    if statemachine-validate "$config" 2>&1 | tail -1; then
        :
    else
        echo "❌ Validation failed: $config"
        exit 1
    fi
done
echo ""

echo "📊 Generating FSM diagrams..."
mkdir -p docs/fsm-diagrams
for config in "${CONFIG_FILES[@]}"; do
    statemachine-diagrams "$config" --output-dir docs/fsm-diagrams 2>&1 | grep -E "✅|⚠️|❌" || true
done
echo "✓ Diagrams generated in docs/fsm-diagrams/"
echo ""

# =============================================================================
# PHASE 3: START UI
# =============================================================================

echo "=========================================="
echo "PHASE 3: Starting Web UI"
echo "=========================================="
echo ""

echo "🌐 Starting Web UI on port $UI_PORT..."
statemachine-ui --port "$UI_PORT" --project-root . > logs/fsm-ui.log 2>&1 &
UI_PID=$!
echo "$UI_PID" > logs/fsm-ui.pid

# Wait for event socket
echo "⏳ Waiting for event socket..."
for i in {1..10}; do
    if [[ -S "$EVENT_SOCKET" ]]; then
        echo "✓ Event socket ready: $EVENT_SOCKET"
        break
    fi
    if [[ $i -eq 10 ]]; then
        echo "❌ Event socket not created after 10s"
        echo "   Check logs/fsm-ui.log"
        cleanup
        exit 1
    fi
    sleep 1
done

# Wait for HTTP
echo "⏳ Waiting for UI HTTP..."
for i in {1..10}; do
    if lsof -i :"$UI_PORT" >/dev/null 2>&1; then
        echo "✓ Web UI running on http://localhost:$UI_PORT"
        break
    fi
    if [[ $i -eq 10 ]]; then
        echo "⚠️  UI port $UI_PORT not detected — UI may still be starting"
    fi
    sleep 1
done
echo ""

# =============================================================================
# PHASE 4: START DISPATCHER
# =============================================================================

echo "=========================================="
echo "PHASE 4: Starting Dispatcher"
echo "=========================================="
echo ""

echo "🤖 Starting dispatcher (inbox: $INBOX_DIR)..."
statemachine "$CONFIG_DIR/watcher-dispatcher.yaml" \
    --actions-dir "$ACTIONS_DIR" \
    --initial-context "{\"inbox_dir\":\"$INBOX_DIR\"}" \
    > logs/fsm-dispatcher.log 2>&1 &
DISPATCHER_PID=$!
echo "$DISPATCHER_PID" > logs/fsm-dispatcher.pid

sleep 2
if kill -0 "$DISPATCHER_PID" 2>/dev/null; then
    echo "✅ Dispatcher started (PID: $DISPATCHER_PID)"
else
    echo "❌ Dispatcher failed to start"
    echo "   Check logs/fsm-dispatcher.log"
    cleanup
    exit 1
fi
echo ""

# =============================================================================
# STATUS SUMMARY
# =============================================================================

echo "🎉 System started successfully!"
echo "========================================"
echo "🌐 Web UI:       http://localhost:$UI_PORT  (PID: $UI_PID)"
echo "🤖 Dispatcher:   PID $DISPATCHER_PID  (inbox: $INBOX_DIR)"
echo "📋 UI log:       logs/fsm-ui.log"
echo "📋 Dispatcher:   logs/fsm-dispatcher.log"
echo "🔌 Event socket: $EVENT_SOCKET"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# =============================================================================
# PHASE 5: KEEP-ALIVE
# =============================================================================

while true; do
    sleep 1
done
