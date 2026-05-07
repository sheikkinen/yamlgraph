#!/bin/bash
# FSM Router Example - Startup Script
#
# Bootstraps the full FSM system:
# 1. Loads .env for API keys
# 2. Generates diagrams for the UI
# 3. Starts WebSocket server and Web UI
# 4. Starts the FSM state machine

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    if [ -n "$UI_PID" ]; then
        kill $UI_PID 2>/dev/null || true
    fi
    if [ -n "$FSM_PID" ]; then
        kill $FSM_PID 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

# Load .env if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "📦 Loading environment from $PROJECT_ROOT/.env"
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
else
    echo "⚠️  No .env file found at $PROJECT_ROOT/.env"
    echo "   Make sure MISTRAL_API_KEY (or other LLM keys) are set"
fi

# Activate venv if it exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    echo "🐍 Activating virtual environment"
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

cd "$SCRIPT_DIR"

# Generate diagrams for UI
echo "📊 Generating FSM diagrams..."
mkdir -p docs/fsm-diagrams
statemachine-diagrams config/router.yaml --output-dir docs/fsm-diagrams 2>/dev/null || true

# Create symlink if needed (UI looks for config filename, not machine_name)
if [ ! -L docs/fsm-diagrams/router ] && [ -d docs/fsm-diagrams/query_router ]; then
    ln -s query_router docs/fsm-diagrams/router 2>/dev/null || true
fi

# Start UI in background
echo "🌐 Starting Web UI on http://localhost:3101..."
statemachine-ui --port 3101 --websocket-port 3102 --project-root . &
UI_PID=$!
sleep 2

# Start FSM in background
echo "🚀 Starting FSM Router..."
echo "   Config: config/router.yaml"
echo "   Actions: ./actions"
statemachine config/router.yaml \
    --machine-name query_router \
    --actions-dir "$SCRIPT_DIR/actions" &
FSM_PID=$!

echo ""
echo "✅ FSM Router running!"
echo ""
echo "📡 Send queries with:"
echo "   statemachine-db send-event --target query_router --type new_query --payload '{\"query\": \"Hello!\"}'"
echo ""
echo "🌐 Open UI: http://localhost:3101"
echo ""
echo "🛑 Stop with: Ctrl+C"
echo ""

# Wait for either process to exit
wait $FSM_PID
