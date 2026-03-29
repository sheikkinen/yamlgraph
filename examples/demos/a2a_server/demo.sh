#!/usr/bin/env bash
# FR-208 A2A Server Demo
# Demonstrates: agent card generation, server start, task send
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HELLO_GRAPH="$REPO_ROOT/examples/demos/hello/"
PORT=9127

echo "═══════════════════════════════════════════════════"
echo "  FR-208: A2A Protocol Server Demo"
echo "═══════════════════════════════════════════════════"
echo ""

# --- Part 1: Agent Card ---
echo "📋 Part 1: Generate Agent Card from graph metadata"
echo "  Command: yamlgraph a2a card examples/demos/hello/"
echo "---"
yamlgraph a2a card "$HELLO_GRAPH"
echo ""

# --- Part 2: Start server and test ---
echo "🚀 Part 2: Start A2A server and send a task"
echo "  Command: yamlgraph a2a serve examples/demos/hello/ --port $PORT"
echo "---"

# Start server in background
yamlgraph a2a serve "$HELLO_GRAPH" --port "$PORT" 2>/dev/null &
SERVER_PID=$!

# Wait for server to be ready
for i in $(seq 1 10); do
    if curl -s "http://localhost:$PORT/.well-known/agent-card.json" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo ""
echo "📡 Fetching Agent Card from running server:"
curl -s "http://localhost:$PORT/.well-known/agent-card.json" | python3 -m json.tool
echo ""

echo ""
echo "📨 Sending message via JSON-RPC (message/send):"
RESPONSE=$(curl -s -X POST "http://localhost:$PORT/" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "demo-msg-1",
        "parts": [{"kind": "text", "text": "name=World style=casual"}]
      }
    }
  }')
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Cleanup
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo "═══════════════════════════════════════════════════"
echo "  ✓ Demo complete"
echo "═══════════════════════════════════════════════════"
