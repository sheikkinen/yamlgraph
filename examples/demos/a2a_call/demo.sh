#!/usr/bin/env bash
# FR-253 A2A Call Demo (contrib client)
# Starts a local A2A server (hello-world), then runs a graph that calls it
# via type: python + yamlgraph.contrib.a2a_client.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HELLO_GRAPH="$REPO_ROOT/examples/demos/hello/"
PORT=9240

echo "═══════════════════════════════════════════════════"
echo "  FR-253: A2A Call Demo (contrib client)"
echo "═══════════════════════════════════════════════════"
echo ""

# --- Part 1: Lint the graph ---
echo "🔍 Part 1: Lint the a2a_call graph"
echo "  Command: yamlgraph graph lint examples/demos/a2a_call/graph.yaml"
echo "---"
yamlgraph graph lint "$SCRIPT_DIR/graph.yaml"
echo ""

# --- Part 2: Start A2A server ---
echo "🚀 Part 2: Start hello-world A2A server on port $PORT"
echo "  Command: yamlgraph a2a serve examples/demos/hello/ --port $PORT"
echo "---"

yamlgraph a2a serve "$HELLO_GRAPH" --port "$PORT" 2>/dev/null &
SERVER_PID=$!

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s "http://localhost:$PORT/.well-known/agent-card.json" > /dev/null 2>&1; then
        echo "  ✓ Server ready (PID $SERVER_PID)"
        break
    fi
    sleep 1
done
echo ""

# --- Part 3: Run the a2a_call graph ---
echo "📨 Part 3: Run graph that calls the A2A server"
echo "  Command: yamlgraph graph run examples/demos/a2a_call/graph.yaml --var name=World --var style=casual --full"
echo "---"
yamlgraph graph run "$SCRIPT_DIR/graph.yaml" \
  --var name="World" --var style="casual" --full || true
echo ""

# Cleanup
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo "═══════════════════════════════════════════════════"
echo "  ✓ Demo complete"
echo "═══════════════════════════════════════════════════"
