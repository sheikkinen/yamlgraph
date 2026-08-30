#!/usr/bin/env bash
# FR-902 Stop hook: fenced checkpoint commit in this session's lane.
#
# Every turn boundary with tree changes becomes a commit on session/<id>
# with Session-Id and Request-Index trailers (R-4). Request-Index is
# derived by replaying the transcript event store — never fabricated;
# a bounded retry then a skip-with-audit covers unflushed stores.
# --no-verify here is the sanctioned fenced-commit exemption (judgement:
# checkpoints are provenance snapshots, not review candidates).
set -uo pipefail

HOOK_REPO="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd -P)" || exit 0
LOG_DIR="${HOOK_LOG_DIR:-$HOOK_REPO/.github/hooks/logs}"
RETRIES="${FR902_RETRIES:-3}"

STDIN=$(cat 2>/dev/null)
SID=""

audit() { # decision reason
    mkdir -p "$LOG_DIR" 2>/dev/null
    printf '{"ts":"%s","hook":"session-checkpoint","decision":"%s","reason":"%s","session_id":"%s"}\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" "$SID" \
        >>"$LOG_DIR/audit.jsonl" 2>/dev/null
}

read -r SID STORE < <(printf '%s' "$STDIN" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('session_id', ''), d.get('transcript_path', ''))
" 2>/dev/null) || exit 0

REC="$LOG_DIR/session-lanes/${SID:-none}.json"
[[ -f "$REC" ]] || exit 0 # session has no lane: not ours to checkpoint

LANE=$(python3 -c \
    "import json,sys; print(json.load(open(sys.argv[1])).get('lane',''))" \
    "$REC" 2>/dev/null) || LANE=""
if [[ -z "$LANE" || ! -d "$LANE" ]]; then
    audit "skip" "lane missing: $LANE"
    exit 0
fi

BRANCH=$(git -C "$LANE" symbolic-ref --short -q HEAD || echo "")
if [[ "$BRANCH" != session/* ]]; then
    audit "reject" "lane HEAD on '$BRANCH', not a session branch"
    exit 1
fi

git -C "$LANE" add -A 2>/dev/null
if git -C "$LANE" diff --cached --quiet 2>/dev/null; then
    exit 0 # nothing to checkpoint
fi

# Request-Index from the event store (bounded wait for flush)
N=""
attempt=0
while :; do
    N=$(python3 -c "
import sys
sys.path.insert(0, '$HOOK_REPO/scripts/vscode')
from session_ledger import replay
doc = replay(sys.argv[1])
print(len(doc.get('requests') or []))
" "$STORE" 2>/dev/null) || N=""
    [[ "$N" =~ ^[0-9]+$ && "$N" -gt 0 ]] && break
    attempt=$((attempt + 1))
    if [[ "$attempt" -gt "$RETRIES" ]]; then
        git -C "$LANE" reset -q 2>/dev/null
        audit "skip" "store not flushed: $STORE"
        exit 0
    fi
    sleep 1
done

MSG=$(mktemp)
printf 'checkpoint(session): turn %s\n\nSession-Id: %s\nRequest-Index: %s\n' \
    "$N" "$SID" "$N" >"$MSG"
if git -C "$LANE" commit --no-verify --quiet -F "$MSG" 2>/dev/null; then
    rm -f "$MSG"
    audit "approve" "turn $N committed"
    exit 0
fi
rm -f "$MSG"
audit "reject" "commit failed at turn $N"
exit 1
