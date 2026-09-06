#!/usr/bin/env bash
# FR-1012 Step 1 — source-only archive of .chaplain/ (round-2 R-4, R-5; REQ-YG-666).
#
# Usage: scripts/chaplain_archive.sh --visibility private|public --pre <sha> [--dry-run] [--resume]
#
# Exit 64  usage / missing --visibility or --pre
# Exit 65  preflight: tag chaplain-archive exists (local or origin) and does not match the journal
# Exit 66  preflight: the archive repository exists and does not match the journal
# Exit 67  preflight: --pre not reachable from origin/main, not clean, lacks .chaplain/, or .chaplain tree != manifest tree
# Exit 68  post-condition: archive clone != frozen manifest, or README first line lacks the banner
# Exit 69  journal/remote mismatch on --resume → human reconciliation
#
# Journal docs/census/chaplain-archive.run.json is written atomically BEFORE the first remote
# mutation and after every state transition: tag_created → repo_created → split_pushed →
# readme_committed → verified → archived. --resume accepts an existing tag/repo only when
# journal and remote facts match PRE, SPLIT, visibility and archive identity exactly.
#
# Test hooks (never set by operators): CHAPLAIN_ARCHIVE_GH (gh command), CHAPLAIN_ARCHIVE_REMOTE
# (archive push URL), CHAPLAIN_ARCHIVE_FAIL_AFTER=<state> (exit 99 right after that transition).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="chaplain-archive"
ARCHIVE_REPO="sheikkinen/yamlgraph-chaplain"
ARCHIVE_REMOTE="${CHAPLAIN_ARCHIVE_REMOTE:-https://github.com/${ARCHIVE_REPO}.git}"
GH="${CHAPLAIN_ARCHIVE_GH:-gh}"
JOURNAL="$REPO_ROOT/docs/census/chaplain-archive.run.json"
MANIFEST="$REPO_ROOT/docs/census/chaplain-archive-manifest.txt"
INPUT_MANIFEST="$REPO_ROOT/docs/census/chaplain-disposition-input.jsonl"
DESCRIPTION="Historical source of the YAMLGraph Chaplain FSM runtime (2026-03 -> 2026-09). Not a runnable distribution."
BANNER="> **Historical source, not a runnable distribution.** This repository is the frozen source of the YAMLGraph Chaplain FSM runtime, split from \`sheikkinen/yamlgraph\` at tag \`chaplain-archive\` (FR-1012, Phase 2 of FR-1010). Its scripts expect the parent repository around them and will not run here. Replacements: see \`docs/archive/chaplain.md\` in the parent repository."

VISIBILITY="" PRE="" DRY_RUN=0 RESUME=0
while [ $# -gt 0 ]; do
  case "$1" in
    --visibility) VISIBILITY="${2:-}"; shift 2 ;;
    --pre) PRE="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --resume) RESUME=1; shift ;;
    *) echo "chaplain_archive: unknown argument $1" >&2; exit 64 ;;
  esac
done
case "$VISIBILITY" in private|public) ;; *) echo "chaplain_archive: --visibility private|public is required (FR-1012 R-7: no default)" >&2; exit 64 ;; esac
[ -n "$PRE" ] || { echo "chaplain_archive: --pre <sha> is required" >&2; exit 64; }

fail() { echo "chaplain_archive: $2" >&2; exit "$1"; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# --- journal (atomic write-temp + rename) --------------------------------------------------
journal_get() { python3 -c "import json,sys; d=json.load(open(sys.argv[1])); v=d.get(sys.argv[2],''); print(v if v is not None else '')" "$JOURNAL" "$1" 2>/dev/null || true; }
journal_set() { # key value [key value ...]
  local tmp; tmp="$(mktemp "$JOURNAL.XXXXXX")"
  python3 - "$JOURNAL" "$tmp" "$@" <<'PYEOF'
import json, sys, os
path, tmp, *kv = sys.argv[1:]
d = json.load(open(path)) if os.path.exists(path) else {}
for k, v in zip(kv[::2], kv[1::2]):
    d[k] = v
d.setdefault("transitions", [])
if kv and kv[0] == "state":
    d["transitions"].append({"state": kv[1], "at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()})
json.dump(d, open(tmp, "w", encoding="utf-8"), indent=2)
PYEOF
  mv -f "$tmp" "$JOURNAL"
}
transition() { journal_set state "$1"; echo "chaplain_archive: state → $1"; [ "${CHAPLAIN_ARCHIVE_FAIL_AFTER:-}" = "$1" ] && { echo "chaplain_archive: injected failure after $1" >&2; exit 99; }; return 0; }

# --- preflights (exit 67, 65, 66) ------------------------------------------------------------
cd "$REPO_ROOT"
git fetch -q origin
PRE="$(git rev-parse --verify "$PRE^{commit}" 2>/dev/null)" || fail 67 "--pre is not a commit"
git merge-base --is-ancestor "$PRE" origin/main || fail 67 "PRE $PRE is not reachable from origin/main"
# the script's own outputs (journal, manifest) are the only tolerated dirt
[ -z "$(git status --porcelain -- . ':!docs/census/chaplain-archive.run.json' ':!docs/census/chaplain-archive-manifest.txt')" ] || fail 67 "working tree is not clean"
git cat-file -e "$PRE:.chaplain" 2>/dev/null || fail 67 "PRE has no .chaplain/ tree"
PRE_TREE="$(git rev-parse "$PRE:.chaplain")"
[ -s "$INPUT_MANIFEST" ] || fail 67 "disposition input manifest missing: $INPUT_MANIFEST"
MANIFEST_TREE="$(git rev-parse "$(python3 -c "import json,sys; print(json.loads(open(sys.argv[1]).readline())['source_sha'])" "$INPUT_MANIFEST")":.chaplain 2>/dev/null || true)"
[ "$PRE_TREE" = "$MANIFEST_TREE" ] || fail 67 "PRE .chaplain tree $PRE_TREE != disposition input tree $MANIFEST_TREE"

if [ "$RESUME" -eq 1 ]; then
  [ -f "$JOURNAL" ] || fail 69 "--resume without a journal"
  [ "$(journal_get pre)" = "$PRE" ] || fail 69 "journal PRE $(journal_get pre) != $PRE"
  [ "$(journal_get visibility)" = "$VISIBILITY" ] || fail 69 "journal visibility $(journal_get visibility) != $VISIBILITY"
fi

REMOTE_TAG="$(git ls-remote --tags origin "refs/tags/$TAG" | cut -f1)"
LOCAL_TAG="$(git rev-parse -q --verify "refs/tags/$TAG" 2>/dev/null || true)"
for t in "$REMOTE_TAG" "$LOCAL_TAG"; do
  if [ -n "$t" ]; then
    [ "$t" = "$PRE" ] && [ "$RESUME" -eq 1 ] || fail 65 "tag $TAG already exists at $t and does not match a resumable journal (PRE $PRE)"
  fi
done
repo_exists() { "$GH" repo view "$ARCHIVE_REPO" --json name >/dev/null 2>&1; }
remote_main() { git ls-remote "$ARCHIVE_REMOTE" refs/heads/main 2>/dev/null | cut -f1; }
if repo_exists; then
  # resumable only when the journal claims this repository AND the remote facts match it (R-5, C-6)
  [ "$RESUME" -eq 1 ] && [ -n "$(journal_get state)" ] || fail 66 "repository $ARCHIVE_REPO already exists and no resumable journal claims it"
  vis="$("$GH" repo view "$ARCHIVE_REPO" --json visibility --jq .visibility | tr 'A-Z' 'a-z')"
  [ "$vis" = "$VISIBILITY" ] || fail 69 "remote visibility $vis != journal/requested $VISIBILITY"
fi

# --- manifest from the commit object, archive-relative ---------------------------------------------
build_manifest() {
  git ls-tree -r --name-only "$PRE" -- .chaplain | LC_ALL=C sort | while IFS= read -r p; do
    printf '%s  %s\n' "$(git cat-file blob "$PRE:$p" | sha256sum | cut -d' ' -f1)" "${p#.chaplain/}"
  done
}
mkdir -p "$(dirname "$MANIFEST")"
build_manifest > "$MANIFEST.tmp" && mv -f "$MANIFEST.tmp" "$MANIFEST"
MANIFEST_SHA="$(sha256sum "$MANIFEST" | cut -d' ' -f1)"
FILE_COUNT="$(wc -l < "$MANIFEST" | tr -d ' ')"

echo "chaplain_archive: PRE=$PRE .chaplain tree=$PRE_TREE files=$FILE_COUNT manifest sha256=$MANIFEST_SHA visibility=$VISIBILITY"
if [ "$DRY_RUN" -eq 1 ]; then
  cat <<EOF
chaplain_archive: DRY RUN — no remote mutation. Intended operations, in order:
  1. git tag $TAG $PRE && git push origin refs/tags/$TAG
  2. SPLIT=\$(git subtree split -P .chaplain $PRE)
  3. $GH repo create $ARCHIVE_REPO --$VISIBILITY --description "$DESCRIPTION"
  4. git push $ARCHIVE_REMOTE \$SPLIT:refs/heads/main
  5. clone; prepend banner to README.md (only content change); commit → ARCHIVE_HEAD; push
  6. verify: archive-relative path set == manifest ($FILE_COUNT files), every sha256 equal except README.md, README first line has "not a runnable distribution", $GH repo view shows visibility=$VISIBILITY
  7. $GH repo archive $ARCHIVE_REPO --yes
Journal: $JOURNAL (written before step 1). Manifest: $MANIFEST
EOF
  exit 0
fi

# --- remote mutations, journaled ----------------------------------------------------------------
if [ "$RESUME" -eq 0 ]; then
  [ -f "$JOURNAL" ] && fail 69 "journal exists; use --resume or remove it after human reconciliation"
  journal_set pre "$PRE" pre_tree "$PRE_TREE" visibility "$VISIBILITY" tag "$TAG" archive_repo "$ARCHIVE_REPO" manifest_sha256 "$MANIFEST_SHA" file_count "$FILE_COUNT" started_at "$(now)"
  transition initialized
fi
STATE="$(journal_get state)"
ORDER="initialized tag_created repo_created split_pushed readme_committed verified archived"
after() { case "$STATE" in initialized) return 0 ;; esac; [[ "${ORDER#*$STATE}" == *"$1"* ]]; }

# Resume gate (review of PR #621, P3): every transition the journal claims complete must still be
# true on the remotes before anything is skipped or mutated; an unknown state is never resumable.
verify_resumed_state() {
  case " $ORDER " in *" $STATE "*) ;; *) fail 69 "journal state '$STATE' is not a known state" ;; esac
  if ! after tag_created; then
    [ "$(git ls-remote --tags origin "refs/tags/$TAG" | cut -f1)" = "$PRE" ] || fail 69 "journal says tag_created but origin tag != PRE"
  fi
  if ! after repo_created; then repo_exists || fail 69 "journal says repo_created but $ARCHIVE_REPO is absent"; fi
  if ! after split_pushed; then
    [ -n "$(journal_get split)" ] || fail 69 "journal says split_pushed but records no SPLIT"
    # remote main equals SPLIT only until the banner commit moves it to ARCHIVE_HEAD
    if after readme_committed; then
      [ "$(remote_main)" = "$(journal_get split)" ] || fail 69 "journal says split_pushed but remote main $(remote_main) != SPLIT $(journal_get split)"
    fi
  fi
  if ! after readme_committed; then
    [ -n "$(journal_get archive_head)" ] || fail 69 "journal says readme_committed but records no ARCHIVE_HEAD"
    [ "$(remote_main)" = "$(journal_get archive_head)" ] || fail 69 "journal says readme_committed but remote main $(remote_main) != ARCHIVE_HEAD $(journal_get archive_head)"
  fi
}
[ "$RESUME" -eq 1 ] && verify_resumed_state

if after tag_created; then
  if [ -z "$REMOTE_TAG" ]; then git tag "$TAG" "$PRE" 2>/dev/null || true; git push -q origin "refs/tags/$TAG"; fi
  transition tag_created
fi
if after repo_created; then
  if ! "$GH" repo view "$ARCHIVE_REPO" --json name >/dev/null 2>&1; then
    "$GH" repo create "$ARCHIVE_REPO" "--$VISIBILITY" --description "$DESCRIPTION" >/dev/null
  fi
  transition repo_created
fi
if after split_pushed; then
  SPLIT="$(journal_get split)"
  if [ -z "$SPLIT" ]; then SPLIT="$(git subtree split -P .chaplain "$PRE")"; journal_set split "$SPLIT"; fi
  git push -q "$ARCHIVE_REMOTE" "$SPLIT:refs/heads/main"
  transition split_pushed
fi
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
if after readme_committed; then
  git clone -q "$ARCHIVE_REMOTE" "$WORK/archive"
  if ! head -1 "$WORK/archive/README.md" | grep -q "not a runnable distribution"; then
    { printf '%s\n\n' "$BANNER"; cat "$WORK/archive/README.md"; } > "$WORK/README.new" && mv -f "$WORK/README.new" "$WORK/archive/README.md"
    git -C "$WORK/archive" -c user.name="chaplain_archive" -c user.email="noreply@yamlgraph" commit -q -am "docs: historical-source banner (FR-1012)"
    git -C "$WORK/archive" push -q origin HEAD:main
  fi
  journal_set archive_head "$(git -C "$WORK/archive" rev-parse HEAD)"
  transition readme_committed
fi
if after verified; then
  [ -d "$WORK/archive" ] || git clone -q "$ARCHIVE_REMOTE" "$WORK/archive"
  head -1 "$WORK/archive/README.md" | grep -q "not a runnable distribution" || fail 68 "archive README first line lacks the banner"
  # hash the archive's git blobs, not checked-out files: EOL translation on the host must not fail the compare
  ( cd "$WORK/archive" && git ls-tree -r --name-only HEAD | LC_ALL=C sort | while IFS= read -r p; do printf '%s  %s\n' "$(git cat-file blob "HEAD:$p" | sha256sum | cut -d' ' -f1)" "$p"; done ) > "$WORK/actual.txt"
  diff <(cut -d' ' -f3- "$MANIFEST") <(cut -d' ' -f3- "$WORK/actual.txt") >/dev/null || fail 68 "archive path set differs from the frozen manifest"
  diff <(grep -v '  README.md$' "$MANIFEST") <(grep -v '  README.md$' "$WORK/actual.txt") >/dev/null || fail 68 "archive file hashes differ from the frozen manifest (README.md excepted)"
  "$GH" repo view "$ARCHIVE_REPO" --json visibility --jq .visibility | tr 'A-Z' 'a-z' | grep -qx "$VISIBILITY" || fail 68 "archive repository visibility != $VISIBILITY"
  "$GH" repo view "$ARCHIVE_REPO" --json defaultBranchRef --jq .defaultBranchRef.name | grep -qx main || fail 68 "archive default branch is not main"
  [ "$(remote_main)" = "$(journal_get archive_head)" ] || fail 68 "remote main $(remote_main) != ARCHIVE_HEAD $(journal_get archive_head)"
  transition verified
fi
if after archived; then
  "$GH" repo archive "$ARCHIVE_REPO" --yes >/dev/null
  "$GH" repo view "$ARCHIVE_REPO" --json isArchived --jq .isArchived | grep -qx true || fail 68 "repository not archived"
  journal_set finished_at "$(now)"
  transition archived
fi
echo "chaplain_archive: done — PRE=$PRE SPLIT=$(journal_get split) ARCHIVE_HEAD=$(journal_get archive_head) journal=$JOURNAL"
