#!/bin/bash
# Hook Classifier — FSM Daemon Launcher
# Follows the ninchat_voice/start-fsm.sh pattern exactly.
#
# Usage:
#   ./start-classifier.sh          # Start the classifier daemon
#   ./start-classifier.sh --debug  # Start with debug logging

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COORDINATOR_NAME="hook-classifier"
COORDINATOR_CONFIG="$SCRIPT_DIR/config/hook-classifier.yaml"
ACTIONS_DIR="$SCRIPT_DIR/actions"
LOG_DIR="$SCRIPT_DIR/logs"
SOCK_PATH="/tmp/statemachine-control-${COORDINATOR_NAME}.sock"
mkdir -p "$LOG_DIR"

# Activate venv (two levels up from examples/demos/hook-classifier/)
VENV_ACTIVATE="$SCRIPT_DIR/../../../.venv/bin/activate"
if [[ -f "$VENV_ACTIVATE" ]]; then
    source "$VENV_ACTIVATE"
fi

# Parse args
DEBUG_FLAG=""
for arg in "$@"; do
    case "$arg" in
        --debug) DEBUG_FLAG="--debug" ;;
    esac
done

# Kill lingering process from previous run
pkill -f "statemachine.*${COORDINATOR_NAME}" 2>/dev/null || true
sleep 0.5

# Cleanup trap
cleanup() {
    echo "🛑 Shutting down hook classifier..."
    pkill -f "statemachine.*${COORDINATOR_NAME}" 2>/dev/null || true
    echo "✓ Stopped"
}
trap cleanup EXIT

# Start FSM engine (canonical pattern from ninchat_voice/start-fsm.sh)
echo "⚙️  Starting hook classifier daemon..."
statemachine "$COORDINATOR_CONFIG" \
    --machine-name "$COORDINATOR_NAME" \
    --actions-dir "$ACTIONS_DIR" \
    $DEBUG_FLAG \
    > "$LOG_DIR/classifier.log" 2>&1 &
ENGINE_PID=$!
sleep 2

if kill -0 $ENGINE_PID 2>/dev/null; then
    # chmod 0600 on control socket (required acceptance criterion)
    if [[ -S "$SOCK_PATH" ]]; then
        chmod 0600 "$SOCK_PATH"
        echo "✓ Hook classifier started (PID: $ENGINE_PID)"
        echo "  Socket: $SOCK_PATH (mode 0600)"
        echo "  Log: $LOG_DIR/classifier.log"
    else
        echo "⚠ Engine started but socket not found at $SOCK_PATH"
        echo "  PID: $ENGINE_PID"
        echo "  Log: $LOG_DIR/classifier.log"
    fi
else
    echo "❌ Failed to start. Check: $LOG_DIR/classifier.log"
    tail -20 "$LOG_DIR/classifier.log" 2>/dev/null
    exit 1
fi

# Wait for engine (blocks until stopped)
wait $ENGINE_PID
