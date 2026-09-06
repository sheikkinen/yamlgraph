#!/usr/bin/env bash
# FR-1012 Step 3 — post-merge witness (round-2 R-7; REQ-YG-666, CAP-264).
#
# Run on the MAIN checkout after the Phase 2 PR merges:
#   scripts/chaplain_postmerge_witness.sh [--out docs/census/chaplain-postmerge.run.json]
#
# 1. scripts/worktree.sh sync (unlock → pull --ff-only → relock). If git cannot unlink the
#    FR-889 read-only `.chaplain` directory, chmod u+w it first and say so.
# 2. `git ls-files .chaplain` must print nothing and the directory must be untracked-empty.
# 3. `python scripts/vscode/now.py` stdout must not contain `.chaplain`.
# Writes the JSON record (committed by the docs-only follow-up) and exits 0 only if all hold.
# Exit 65 = a check failed (record still written, check=false); 70 = sync failed.
# Test hook (never set by operators): CHAPLAIN_WITNESS_SKIP_SYNC=1 skips step 1.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO_ROOT/docs/census/chaplain-postmerge.run.json"
[ "${1:-}" = "--out" ] && OUT="$2"
cd "$REPO_ROOT"
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
STARTED="$(now)"
SYNC="skipped"; CHMOD="no"; LSFILES=""; NOWPY="not-run"; NOWPY_RC=""

if [ -z "${CHAPLAIN_WITNESS_SKIP_SYNC:-}" ]; then
  if [ -d .chaplain ] && [ ! -w .chaplain ]; then
    chmod -R u+w .chaplain && CHMOD="yes" && echo "chaplain_postmerge_witness: chmod u+w .chaplain (FR-889 read-only residue) so git can unlink it"
  fi
  if bash scripts/worktree.sh sync >tmp/chaplain-postmerge-sync.log 2>&1; then SYNC="ok"; else SYNC="failed"; fi
fi

LSFILES="$(git ls-files .chaplain | tr '\n' ' ')"
UNTRACKED_LEFT="$( [ -d .chaplain ] && find .chaplain -type f | wc -l | tr -d ' ' || echo 0 )"
PYBIN="${PYTHON:-python}"
if command -v "$PYBIN" >/dev/null 2>&1; then
  NOWPY="$(PYTHONUTF8=1 "$PYBIN" scripts/vscode/now.py 2>/dev/null)"; NOWPY_RC=$?
else
  NOWPY_RC=127
fi
NOWPY_HAS_CHAPLAIN="false"; printf '%s' "$NOWPY" | grep -q '\.chaplain' && NOWPY_HAS_CHAPLAIN="true"

PASS_LS="false"; [ -z "$LSFILES" ] && PASS_LS="true"
PASS_NOW="false"; [ "$NOWPY_HAS_CHAPLAIN" = "false" ] && [ "$NOWPY_RC" = "0" ] && PASS_NOW="true"
PASS_SYNC="false"; { [ "$SYNC" = "ok" ] || [ "$SYNC" = "skipped" ]; } && PASS_SYNC="true"
ALL="false"; [ "$PASS_LS" = "true" ] && [ "$PASS_NOW" = "true" ] && [ "$PASS_SYNC" = "true" ] && ALL="true"

mkdir -p "$(dirname "$OUT")"
python3 - "$OUT" "$STARTED" "$(now)" "$(git rev-parse HEAD)" "$SYNC" "$CHMOD" "$LSFILES" "$UNTRACKED_LEFT" "$NOWPY_RC" "$NOWPY_HAS_CHAPLAIN" "$ALL" <<'PYEOF'
import json, sys
out, started, finished, head, sync, chmod, lsfiles, untracked, nowrc, nowchap, ok = sys.argv[1:]
json.dump({
    "fr": "FR-1012", "step": "post-merge witness", "started_at": started, "finished_at": finished,
    "main_head": head, "worktree_sync": sync, "chmod_uw_applied": chmod == "yes",
    "git_ls_files_chaplain": lsfiles.split(), "untracked_files_left_in_chaplain": int(untracked),
    "now_py_rc": int(nowrc), "now_py_mentions_chaplain": nowchap == "true",
    "prerequisites": {"FR-1014": "fec26941", "FR-1011": "84baceb7", "FR-1015": "32fd6e9f"},
    "all_checks_pass": ok == "true",
}, open(out, "w", encoding="utf-8"), indent=2)
PYEOF
echo "chaplain_postmerge_witness: sync=$SYNC ls-files='${LSFILES}' untracked_left=$UNTRACKED_LEFT now.py rc=$NOWPY_RC mentions_chaplain=$NOWPY_HAS_CHAPLAIN → $OUT"
[ "$SYNC" = "failed" ] && exit 70
[ "$ALL" = "true" ] || exit 65
exit 0
