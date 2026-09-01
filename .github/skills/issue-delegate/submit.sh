#!/usr/bin/env bash
# submit.sh — FR-949 control-side delegation submission (AC-06, REQ-YG-637).
#
# Usage:
#   submit.sh --task judge|research --payload <repo-relative.md>
#             [--repo owner/name] [--max-credits N]
#   submit.sh --check-worker
#
# Typed refusals (non-zero, actionable stderr):
#   2 usage / malformed options   5 HEAD not on fetched remote default
#   3 recursion (YAMLGRAPH_DELEGATED=1)   6 invalid/missing payload
#   4 dirty tree                  7 runner offline   8 bundle drift
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
COMMS_REPO="${YAMLGRAPH_COMMS_REPO:-sheikkinen/yamlgraph-delegation}"
# The normalizer run must not dirty the tree it is about to check.
export PYTHONDONTWRITEBYTECODE=1

die() { local code=$1; shift; echo "submit.sh: $*" >&2; exit "$code"; }

# --- option parsing ---------------------------------------------------------
TASK="" PAYLOAD="" REPO="sheikkinen/yamlgraph" MAX_CREDITS=60 CHECK_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --task) TASK="${2:?}"; shift 2 ;;
    --payload) PAYLOAD="${2:?}"; shift 2 ;;
    --repo) REPO="${2:?}"; shift 2 ;;
    --max-credits) MAX_CREDITS="${2:?}"; shift 2 ;;
    --check-worker) CHECK_ONLY=1; shift ;;
    *) die 2 "unknown option: $1" ;;
  esac
done

# Recursion guard: a delegated payload must never submit further delegations.
if [ "${YAMLGRAPH_DELEGATED:-0}" = "1" ]; then
  die 3 "refusing to submit from a delegated context (YAMLGRAPH_DELEGATED=1)"
fi

# --- worker health + bundle drift (runs for both modes) ---------------------
check_runner() {
  gh api "repos/$COMMS_REPO/actions/runners" | python3 -c '
import json, sys
data = json.load(sys.stdin)
online = [r for r in data.get("runners", [])
          if r.get("status") == "online"
          and any(lb.get("name") == "delegate" for lb in r.get("labels", []))]
print(f"delegate runners online: {len(online)}")
sys.exit(0 if online else 1)
' || die 7 "no online runner with label 'delegate' in $COMMS_REPO"
}

check_drift() {
  local pairs=(
    "delegate.yml:.github/workflows/delegate.yml"
    "models.py:.github/delegate/models.py"
    "worker.py:.github/delegate/worker.py"
    "windows_job.ps1:.github/delegate/windows_job.ps1"
  )
  local drifted=0
  for pair in "${pairs[@]}"; do
    local src="${pair%%:*}" rel="${pair#*:}"
    local local_sha remote_sha
    local_sha=$(git hash-object "$SCRIPT_DIR/$src")
    remote_sha=$(gh api "repos/$COMMS_REPO/contents/$rel" | python3 -c \
      'import json,sys; print(json.load(sys.stdin)["sha"])')
    if [ "$local_sha" != "$remote_sha" ]; then
      echo "drift: $rel (local $local_sha != deployed $remote_sha)" >&2
      drifted=1
    else
      echo "ok: $rel"
    fi
  done
  [ "$drifted" -eq 0 ] || die 8 "deployed comms bundle drifted from canonical — run sync-worker.sh and review (GATE C-2)"
}

if [ "$CHECK_ONLY" -eq 1 ]; then
  check_runner
  check_drift
  echo "worker healthy, bundle in sync — no submission performed"
  exit 0
fi

# --- submission validation ---------------------------------------------------
case "$TASK" in
  judge|research) ;;
  *) die 2 "--task must be judge|research (got: '${TASK}')" ;;
esac
[ -n "$PAYLOAD" ] || die 2 "--payload is required"

# Same normalizer as the worker (AC-05/AC-06).
python3 "$SCRIPT_DIR/worker.py" validate-payload "$TASK" "$PAYLOAD" \
  || die 6 "payload refused by worker normalizer: $PAYLOAD"

if [ -n "$(git status --porcelain)" ]; then
  die 4 "working tree is dirty — commit or stash before submitting"
fi

git fetch origin --quiet
git remote set-head origin --auto >/dev/null 2>&1 || true
DEFAULT_REF=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)
if ! git merge-base --is-ancestor HEAD "$DEFAULT_REF"; then
  die 5 "HEAD is not pushed to the remote default branch ($DEFAULT_REF)"
fi
SHA=$(git rev-parse HEAD)

git cat-file -e "HEAD:$PAYLOAD" 2>/dev/null \
  || die 6 "payload not committed at HEAD: $PAYLOAD"

check_runner
check_drift

# --- submit -------------------------------------------------------------------
BODY="Delegation request (FR-949).

\`\`\`yaml
schema_version: 1
task: $TASK
repo: $REPO
sha: $SHA
payload: $PAYLOAD
max_reported_credits: $MAX_CREDITS
\`\`\`
"

gh issue create \
  --repo "$COMMS_REPO" \
  --title "delegate: $TASK $PAYLOAD" \
  --label delegate \
  --body "$BODY"
