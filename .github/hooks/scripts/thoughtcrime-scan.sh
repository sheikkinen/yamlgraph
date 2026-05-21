#!/usr/bin/env bash
# PostToolUse hook: scan agent transcript for forbidden reasoning patterns.
# Arms a one-shot sentinel that pre-command-guard.sh will consume on next PreToolUse.
# FR-438 Phase 1: keyword-based, no LLM.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${HOOK_LOG_DIR:-$(dirname "$0")/../logs}"
REGISTRY="$SCRIPT_DIR/thoughtcrimes.json"

# ── Audit helper for skip paths ──────────────────────────────────────
audit_skip() {
  local reason="$1" detail="${2:-}"
  mkdir -p "$LOG_DIR"
  printf '{"ts":"%s","hook":"thoughtcrime-scan","decision":"skip","reason":"%s","detail":"%s","session_id":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%S%z)" "$reason" "$detail" "${SESSION_ID:-}" >> "$LOG_DIR/audit.jsonl" 2>/dev/null || true
}

# ── Parse session_id from hook input ──────────────────────────────────
SESSION_ID=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('session_id', d.get('sessionId', '')))
except Exception:
    print('')
" 2>/dev/null) || SESSION_ID=""

# ── Validate session_id as UUID (path traversal guard) ────────────────
if ! echo "$SESSION_ID" | grep -qE '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'; then
  audit_skip "no-session-id" "invalid or empty session_id"
  exit 0
fi

# ── Discover transcript ──────────────────────────────────────────────
TRANSCRIPT=$(python3 -c "
import sys
from pathlib import Path

session_id = sys.argv[1]
base = Path.home() / 'Library' / 'Application Support' / 'Code' / 'User' / 'workspaceStorage'
if not base.is_dir():
    sys.exit(0)
for ws in base.iterdir():
    t = ws / 'GitHub.copilot-chat' / 'transcripts' / f'{session_id}.jsonl'
    if t.is_file():
        print(t)
        sys.exit(0)
" "$SESSION_ID" 2>/dev/null) || exit 0

if [[ -z "$TRANSCRIPT" || ! -f "$TRANSCRIPT" ]]; then
  audit_skip "no-transcript" "transcript not found for session"
  exit 0
fi

# ── Scan latest assistant.message for thoughtcrimes ───────────────────
python3 -c "
import json, sys
from pathlib import Path

transcript_path = sys.argv[1]
registry_path = sys.argv[2]
log_dir = sys.argv[3]
session_id = sys.argv[4]

# Load registry
registry = json.loads(Path(registry_path).read_text())
phrases = registry.get('phrases', [])

# Build flat list of all patterns (primary + variants), case-insensitive
checks = []
for p in phrases:
    pattern = p['pattern'].lower()
    doctrine = p.get('doctrine', '')
    ref = p.get('scripture_ref', '')
    checks.append((pattern, pattern, doctrine, ref))
    for v in p.get('variants', []):
        checks.append((v.lower(), pattern, doctrine, ref))

# Find latest assistant.message
latest_reasoning = ''
latest_content = ''
for line in Path(transcript_path).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        continue
    if entry.get('type') == 'assistant.message':
        data = entry.get('data', {})
        rt = data.get('reasoningText', '')
        ct = data.get('content', '')
        if rt:
            latest_reasoning = rt
        if ct:
            latest_content = ct

# Use reasoningText if available, fall back to content
scan_text = latest_reasoning or latest_content
scan_source = 'reasoningText' if latest_reasoning else 'content'

# No scannable text → audit skip and exit
if not scan_text:
    import datetime as dt
    skip_entry = {
        'ts': dt.datetime.now(dt.timezone.utc).isoformat(),
        'hook': 'thoughtcrime-scan',
        'decision': 'skip',
        'reason': 'no-scannable-text',
        'detail': 'no reasoningText or content in latest assistant.message',
        'session_id': session_id,
    }
    audit_path = Path(log_dir) / 'audit.jsonl'
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, 'a') as f:
        f.write(json.dumps(skip_entry) + '\n')
    sys.exit(0)

# Scan for forbidden phrases
text_lower = scan_text.lower()
for needle, canonical, doctrine, ref in checks:
    if needle in text_lower:
        import datetime as dt
        sentinel = {
            'phrase': canonical,
            'matched': needle,
            'doctrine': doctrine,
            'scripture_ref': ref,
            'session_id': session_id,
            'ts': dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        sentinel_path = Path(log_dir) / f'.thoughtcrime-{session_id}'
        sentinel_path.parent.mkdir(parents=True, exist_ok=True)
        sentinel_path.write_text(json.dumps(sentinel))

        # Audit log
        audit_entry = {
            'ts': dt.datetime.now(dt.timezone.utc).isoformat(),
            'hook': 'thoughtcrime-scan',
            'decision': 'armed',
            'reason': 'thoughtcrime',
            'detail': f'phrase={canonical}, matched={needle}, source={scan_source}',
            'session_id': session_id,
        }
        audit_path = Path(log_dir) / 'audit.jsonl'
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        with open(audit_path, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')

        # First match wins — one sentinel per scan
        break
" "$TRANSCRIPT" "$REGISTRY" "$LOG_DIR" "$SESSION_ID" 2>/dev/null || true

exit 0
