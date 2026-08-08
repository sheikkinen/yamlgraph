#!/usr/bin/env bash
# install-hook.sh (FR-781) — render + install the file-hook launchd agent.
#
# Usage:
#   ./install-hook.sh <watched-dir>                # render, install, load
#   ./install-hook.sh --render-only <watched-dir>  # rendered plist -> stdout (CI-testable)
#
# Render-only prints the plist to stdout and the launchctl commands it
# WOULD run to stderr, without touching ~/Library/LaunchAgents or launchctl.
set -euo pipefail

RENDER_ONLY=0
if [[ "${1:-}" == "--render-only" ]]; then
    RENDER_ONLY=1
    shift
fi

WATCHED_DIR="${1:?usage: install-hook.sh [--render-only] <watched-dir>}"
WATCHED_DIR="$(cd "$WATCHED_DIR" && pwd)"   # absolute — launchd does no expansion

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
TEMPLATE="$SCRIPT_DIR/com.yamlgraph.file-hook.plist.template"
LABEL="com.yamlgraph.file-hook"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"

YAMLGRAPH_BIN="$REPO_ROOT/.venv/bin/yamlgraph"
if [[ ! -x "$YAMLGRAPH_BIN" ]]; then
    YAMLGRAPH_BIN="$(command -v yamlgraph || true)"
fi
if [[ -z "$YAMLGRAPH_BIN" ]]; then
    echo "error: yamlgraph executable not found (.venv/bin/yamlgraph or PATH)" >&2
    exit 1
fi

render() {
    sed -e "s|{{YAMLGRAPH_BIN}}|$YAMLGRAPH_BIN|g" \
        -e "s|{{REPO_ROOT}}|$REPO_ROOT|g" \
        -e "s|{{WATCHED_DIR}}|$WATCHED_DIR|g" \
        "$TEMPLATE"
}

if [[ "$RENDER_ONLY" -eq 1 ]]; then
    render
    {
        echo "render-only: would install to $TARGET"
        echo "render-only: would run: launchctl load $TARGET"
        echo "render-only: uninstall: launchctl unload $TARGET"
    } >&2
    exit 0
fi

render > "$TARGET"
launchctl unload "$TARGET" 2>/dev/null || true
launchctl load "$TARGET"
echo "installed + loaded: $TARGET"
echo "watching: $WATCHED_DIR"
echo "logs: /tmp/$LABEL.log /tmp/$LABEL.err"
