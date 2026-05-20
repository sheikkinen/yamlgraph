#!/usr/bin/env bash
# PostToolUse hook: fire-and-forget DGRAM to classifier daemon.
# Activation: add classify-emit.json to .github/hooks/
# Deactivation: remove classify-emit.json
# FR-425 Phase B
set -euo pipefail

INPUT=$(cat)
CLASSIFIER_SOCK="${HOOK_CLASSIFIER_SOCK:-/tmp/statemachine-control-hook-classifier.sock}"
[[ -S "$CLASSIFIER_SOCK" ]] || exit 0

# Parse tool name, command, session_id from hook input in one pass
PARSED=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    inp = d.get('toolInput', d.get('tool_input', d.get('input', {})))
    tool = d.get('toolName', d.get('tool_name', 'unknown'))
    cmd = inp.get('command', '') if isinstance(inp, dict) else ''
    sid = d.get('sessionId', d.get('session_id', ''))
    print(json.dumps({'tool': tool, 'command': cmd, 'session_id': sid}))
except Exception:
    sys.exit(1)
" 2>/dev/null) || exit 0

TOOL_NAME=$(echo "$PARSED" | python3 -c "import json,sys; print(json.load(sys.stdin)['tool'])")
COMMAND=$(echo "$PARSED" | python3 -c "import json,sys; print(json.load(sys.stdin)['command'])")
SESSION_ID=$(echo "$PARSED" | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")

# Redact secrets before sending to LLM
_redacted_cmd=$(echo "$COMMAND" | sed -E 's/(KEY|TOKEN|SECRET|PASSWORD|PASSPHRASE)=[^ ]*/\1=REDACTED/gi')

python3 -c "
import json, socket, sys
envelope = json.dumps({
    'type': 'tool_event',
    'payload': {
        'tool': sys.argv[1],
        'command': sys.argv[2][:500],
        'session_id': sys.argv[3],
        'ts': sys.argv[4],
    }
})
s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
s.sendto(envelope.encode(), sys.argv[5])
" "$TOOL_NAME" "$_redacted_cmd" "$SESSION_ID" "$(date -u +%Y-%m-%dT%H:%M:%S+00:00)" "$CLASSIFIER_SOCK" 2>/dev/null &
exit 0
