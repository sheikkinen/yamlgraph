#!/usr/bin/env bash
# PreToolUse hook: block dangerous terminal patterns.
# 1. Co-authored-by trailers in commits/merges/file writes
# 2. --no-verify flag (safety bypass forbidden by Scripture)
# 3. Multiline git commit -m (use git commit -F ./tmp/msg.txt instead)
# 4. pytest piped to head/tail without tee (output buffering) (FR-440)
# 5. Branch creation in main worktree (FR-662)
# 6. Unsentineled writes to governed graph artifacts (FR-767)
# Audit: logs every tool invocation to JSONL (FR-414)
set -euo pipefail

INPUT=$(cat)

# ── Audit log helper ─────────────────────────────────────────────────
LOG_DIR="${HOOK_LOG_DIR:-$(dirname "$0")/../logs}"
SESSION_ID=""
TOOL_USE_ID=""

audit_log() {
  # args: decision reason detail
  local decision="$1" reason="$2" detail="$3"
  mkdir -p "$LOG_DIR" 2>/dev/null || return 0
  python3 -c "
import json, sys, datetime as dt
entry = {
    'ts': dt.datetime.now(dt.timezone.utc).isoformat(),
    'hook': 'pre-command-guard',
    'tool': sys.argv[1],
    'decision': sys.argv[2],
    'reason': sys.argv[3],
    'detail': sys.argv[4][:500]
}
if sys.argv[5]: entry['session_id'] = sys.argv[5]
if sys.argv[6]: entry['tool_use_id'] = sys.argv[6]
print(json.dumps(entry))
" "${TOOL_NAME:-unknown}" "$decision" "$reason" "$detail" "$SESSION_ID" "$TOOL_USE_ID" >> "$LOG_DIR/audit.jsonl" 2>/dev/null || true
}

emit_deny() {
  local reason_text="$1"
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$reason_text"
  }
}
EOF
}

# ── Parse input (fail-closed) ────────────────────────────────────────
parse_hook_input() {
  python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    inp = d.get('tool_input', d.get('toolInput', d.get('input', {})))
    tool = d.get('tool_name', d.get('toolName', ''))
    cmd = inp.get('command', '') if isinstance(inp, dict) else ''
    detail = json.dumps(inp)[:500] if inp else '{}'
    sid = d.get('session_id', '')
    tuid = d.get('tool_use_id', '')
    cwd = d.get('cwd', '')
    for value in (tool, cmd, detail, sid, tuid, cwd):
        sys.stdout.write(value if isinstance(value, str) else str(value))
        sys.stdout.write('\0')
except Exception:
    sys.exit(1)
"
}

if ! {
  IFS= read -r -d '' TOOL_NAME &&
  IFS= read -r -d '' COMMAND &&
  IFS= read -r -d '' DETAIL &&
  IFS= read -r -d '' SESSION_ID &&
  IFS= read -r -d '' TOOL_USE_ID &&
  IFS= read -r -d '' HOOK_CWD
} < <(printf '%s' "$INPUT" | parse_hook_input 2>/dev/null); then
  TOOL_NAME="unknown"
  audit_log "deny" "parse-error" "JSON parse failed"
  emit_deny "Hook cannot parse input — denying for safety."
  exit 0
fi

# ── Lockdown check ───────────────────────────────────────────────────
LOCKFILE="$LOG_DIR/.lockdown"
if [[ -f "$LOCKFILE" ]]; then
  # Allow only unlock command through
  if [[ "$TOOL_NAME" == "run_in_terminal" || "$TOOL_NAME" == "send_to_terminal" ]] && \
     echo "$COMMAND" | grep -q '\.github/hooks/cmd unlock'; then
    : # fall through to lockdown command handler
  else
    audit_log "deny" "lockdown-active" "$DETAIL"
    emit_deny "LOCKDOWN ACTIVE. All tool calls blocked. User must issue: .github/hooks/cmd unlock"
    exit 0
  fi
fi

# ── Reasoning pattern sentinel check (FR-438, renamed in FR-439) ─────
TC_SENTINEL="$LOG_DIR/.reasoning-flag-$SESSION_ID"
if [[ -n "$SESSION_ID" && -f "$TC_SENTINEL" ]]; then
  TC_DATA=$(cat "$TC_SENTINEL" 2>/dev/null || echo '{}')
  TC_PHRASE=$(echo "$TC_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('phrase',''))" 2>/dev/null || echo "unknown")
  TC_DOCTRINE=$(echo "$TC_DATA" | python3 -c "import json,sys; print(json.load(sys.stdin).get('doctrine',''))" 2>/dev/null || echo "")
  rm -f "$TC_SENTINEL"
  audit_log "deny" "reasoning-pattern" "phrase=$TC_PHRASE"
  emit_deny "⚠ Reasoning pattern flagged\\n\\nFlagged phrase: \\\"$TC_PHRASE\\\"\\n\\nDoctrine: $TC_DOCTRINE\\n\\nThis denial is one-shot. Your next tool call will proceed."
  exit 0
fi

# ── Lockdown command channel ─────────────────────────────────────────
if [[ "$TOOL_NAME" == "run_in_terminal" || "$TOOL_NAME" == "send_to_terminal" ]] && \
   echo "$COMMAND" | grep -q '^\.github/hooks/cmd '; then
  HOOKCTL_CMD=$(echo "$COMMAND" | sed 's/^\.github\/hooks\/cmd //')
  case "$HOOKCTL_CMD" in
    lockdown)
      touch "$LOCKFILE"
      audit_log "deny" "lockdown-set" "lockdown activated"
      emit_deny "Lockdown active — all tool calls will be denied until: .github/hooks/cmd unlock"
      ;;
    unlock)
      rm -f "$LOCKFILE"
      audit_log "deny" "lockdown-clear" "lockdown deactivated"
      emit_deny "Lockdown lifted. Normal operations resumed."
      ;;
    status)
      SUMMARY=$(python3 -c "
import json, collections, pathlib, datetime as dt
logfile = pathlib.Path('$LOG_DIR') / 'audit.jsonl'
if not logfile.exists():
    print('No audit log found.')
else:
    lines = logfile.read_text().strip().splitlines()
    decisions = collections.Counter()
    tools = collections.Counter()
    errors = collections.Counter()
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)
    for line in lines:
        d = json.loads(line)
        decisions[d.get('decision','')] += 1
        tools[d.get('tool','')] += 1
        if d.get('decision') == 'error':
            try:
                ts = dt.datetime.fromisoformat(d.get('ts',''))
            except ValueError:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.timezone.utc)
            if ts >= cutoff:
                errors[d.get('hook','?') + '/' + d.get('reason','?')] += 1
    total = sum(decisions.values())
    dec_str = ', '.join(f'{k}={v}' for k,v in decisions.most_common())
    tool_str = ', '.join(f'{k}={v}' for k,v in tools.most_common(5))
    err_str = ', '.join(f'{k}={v}' for k,v in errors.most_common()) if errors else 'none'
    lockdown = 'YES' if pathlib.Path('$LOCKFILE').exists() else 'no'
    print(f'Audit: {total} total entries. Decisions: {dec_str}. Top tools: {tool_str}. Hook errors (7d): {err_str}. Lockdown: {lockdown}')
" 2>/dev/null)
      audit_log "deny" "lockdown-status" "status requested"
      emit_deny "$SUMMARY"
      ;;
    *)
      audit_log "deny" "lockdown-unknown" "unknown cmd: $HOOKCTL_CMD"
      emit_deny "Unknown command: $HOOKCTL_CMD. Available: lockdown, unlock, status"
      ;;
  esac
  exit 0
fi

# ── Check 6: graph-authoring sole route (FR-767) ─────────────────────
# Governed graph artifacts (examples/**/graph.yaml, examples/**/prompts/*.yaml,
# graphs/*.yaml, .chaplain/graphs/*.yaml) may only be written under an armed
# per-run authoring sentinel (scripts/author.sh). Path-based bright line (C-4),
# fail closed on ambiguity (C-5). Sentinel = env token + matching token file.
case "$TOOL_NAME" in
  create_file|replace_string_in_file|multi_replace_string_in_file|apply_patch|run_in_terminal|send_to_terminal)
    AUTHOR_REASON=$(HOOK_INPUT="$INPUT" python3 <<'PYEOF'
import json, os, re, shlex
from pathlib import Path

def deny(msg):
    print(msg)
    raise SystemExit(0)

try:
    d = json.loads(os.environ.get("HOOK_INPUT", "{}"))
except Exception:
    deny("hook input unparseable (fail closed)")
tool = d.get("tool_name", d.get("toolName", ""))
ti = d.get("tool_input", d.get("toolInput", d.get("input", {}))) or {}

def governed_path(path):
    p = str(path).replace("\\", "/").strip()
    return bool(
        re.search(r"(^|/)examples/.+/graph\.ya?ml$", p)
        or re.search(r"(^|/)examples/.+/prompts/[^/]+\.ya?ml$", p)
        or re.search(r"(^|/)graphs/[^/]+\.ya?ml$", p)
        or re.search(r"(^|/)\.chaplain/graphs/[^/]+\.ya?ml$", p)
    )

def sentinel_armed():
    tok = os.environ.get("YAMLGRAPH_AUTHORING_TOKEN", "")
    sf = os.environ.get("YAMLGRAPH_AUTHORING_SENTINEL", "")
    if not tok or not sf:
        return False
    try:
        data = json.loads(Path(sf).read_text())
    except Exception:
        return False
    return data.get("token") == tok

PATHISH = r"[^\s\"';|&<>]+"

def terminal_reason(cmd):
    if not re.search(r"examples/|graphs/|\.chaplain/", cmd):
        return None
    for m in re.finditer(r">>?\s*[\"']?(" + PATHISH + ")", cmd):
        if governed_path(m.group(1)):
            return "shell redirect into governed artifact " + m.group(1)
    for m in re.finditer(r"\btee\s+(?:-a\s+)?[\"']?(" + PATHISH + ")", cmd):
        if governed_path(m.group(1)):
            return "tee into governed artifact " + m.group(1)
    if re.search(r"\bsed\b[^|;&]*\s-i", cmd):
        for m in re.finditer(PATHISH, cmd):
            if governed_path(m.group(0)):
                return "in-place edit of governed artifact"
    for seg in re.split(r"&&|\|\||;|\|", cmd):
        try:
            toks = shlex.split(seg)
        except ValueError:
            toks = seg.split()
        while toks and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):
            toks.pop(0)
        if not toks or toks[0] not in ("cp", "mv", "rsync", "install"):
            continue
        args = [t for t in toks[1:] if not t.startswith("-")]
        if len(args) < 2:
            continue
        dest, sources = args[-1], args[:-1]
        if governed_path(dest):
            return "copy/move onto governed artifact " + dest
        in_tree = re.match(r"(\./)?(examples|graphs|\.chaplain)(/|$)", dest)
        if not in_tree:
            continue
        for s in sources:
            cand = dest.rstrip("/") + "/" + os.path.basename(s.rstrip("/"))
            if governed_path(cand):
                return "copy/move materializes governed artifact " + cand
            sp = Path(s)
            if not sp.exists():
                return ("cannot verify source " + s
                        + " for write into governed tree (fail closed)")
            if sp.is_dir() and (
                list(sp.glob("**/graph.yaml"))
                or list(sp.glob("**/graph.yml"))
                or list(sp.glob("**/prompts/*.yaml"))
            ):
                return "directory copy materializes governed artifacts from " + s
    mentions = any(
        governed_path(m.group(0)) for m in re.finditer(PATHISH, cmd))
    if mentions and re.search(
        r"python3?\s+-c|perl\s+-e|ruby\s+-e|\bopen\(|\.write\(|\bdd\b|\btruncate\b",
        cmd,
    ):
        return "unrecognized write shape touching governed artifact (fail closed)"
    return None

EDIT_TOOLS = {"create_file", "replace_string_in_file",
              "multi_replace_string_in_file", "apply_patch"}
reason = None
if tool in EDIT_TOOLS:
    paths = []
    if isinstance(ti, dict):
        if ti.get("filePath"):
            paths.append(ti["filePath"])
        for r in ti.get("replacements") or []:
            if isinstance(r, dict) and r.get("filePath"):
                paths.append(r["filePath"])
        patch = ti.get("input") or ti.get("patch") or ""
        if isinstance(patch, str):
            paths += re.findall(r"\*\*\* (?:Add|Update|Move to) File: (.+)", patch)
    hits = [p for p in paths if governed_path(p)]
    if hits:
        reason = "file write to governed artifact " + hits[0].replace('"', "")
else:
    cmd = ti.get("command", "") if isinstance(ti, dict) else ""
    reason = terminal_reason(cmd)

if reason and not sentinel_armed():
    deny(reason.replace('"', ""))
PYEOF
) || AUTHOR_REASON="authoring-guard analyzer error (fail closed)"
    if [[ -n "$AUTHOR_REASON" ]]; then
      audit_log "deny" "authoring-route" "$AUTHOR_REASON"
      emit_deny "Governed graph artifact write denied: ${AUTHOR_REASON}.\\n\\nGraph authoring has a sole route: scripts/author.sh <task-brief.md>\\n(.github/skills/graph-authoring/adapters/README.md). The adapter arms a\\nper-run sentinel; unsentineled writes to examples/**/graph.yaml,\\nexamples/**/prompts/*.yaml, graphs/*.yaml and .chaplain/graphs/*.yaml\\nare denied (FR-767). Do not work around this guard — write a task brief\\nand run the adapter."
      exit 0
    fi
    ;;
esac

# ── Check 7: main-write guard — worktree is the only enforcement write
# path (FR-888). Enforcement-class writes on a MAIN checkout are denied;
# the same write in a linked worktree is allowed. Detection is git
# plumbing (--git-common-dir vs --git-dir), never path heuristics.
# Escape: FR888_ALLOW_MAIN=1 (audited, does not bypass other guards).
case "$TOOL_NAME" in
  create_file|replace_string_in_file|multi_replace_string_in_file|apply_patch|run_in_terminal|send_to_terminal)
    # cheap bash pre-filter: only analyze commands that could write
    # (FR-442 python-invocation budget — clean calls must not pay)
    FR888_RELEVANT=1
    if [[ "$TOOL_NAME" == "run_in_terminal" || "$TOOL_NAME" == "send_to_terminal" ]]; then
      if ! echo "$COMMAND" | grep -qE '>|\btee\b|\bcp\b|\bmv\b|\brsync\b|\binstall\b|\bsed\b|\bdd\b|\btruncate\b|python3? -c|perl -e|ruby -e'; then
        FR888_RELEVANT=0
      fi
    fi
    if [[ "$FR888_RELEVANT" == "1" ]]; then
    HOOK_GUARD_ROOT="${HOOK_GUARD_ROOT:-$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd -P)}"
    FR888_OUT=$(HOOK_INPUT="$INPUT" HOOK_GUARD_ROOT="$HOOK_GUARD_ROOT" python3 <<'PYEOF'
import json, os, re, subprocess, sys
from pathlib import Path

ENFORCE = ("yamlgraph/", "tests/", "scripts/", "capabilities/", ".github/hooks/")
DOCS = ("docs/", "feature-requests/", "changelog/", "research/", "tmp/", "logs/")
PATHISH = re.compile(r"[^\s\"';|&<>=]+/[^\s\"';|&<>]*")

try:
    d = json.loads(os.environ.get("HOOK_INPUT", "{}"))
except Exception:
    d = {}
tool = d.get("tool_name", d.get("toolName", ""))
ti = d.get("tool_input", d.get("toolInput", d.get("input", {}))) or {}
cwd = d.get("cwd", "") or "."

# The guard protects THIS repository only (review PR#476 round 3 P1):
# nested foreign repos are not ours to police. Root computed by the bash
# wrapper from the hook's own location; HOOK_GUARD_ROOT overrides for
# fixtures.
GUARD_ROOT = (
    os.path.realpath(os.environ["HOOK_GUARD_ROOT"])
    if os.environ.get("HOOK_GUARD_ROOT")
    else ""
)

def textual_enforcement(p):
    s = str(p).replace("\\", "/")
    return any(("/" + e) in ("/" + s) or s.startswith(e) for e in ENFORCE) or any(
        ("/" + e.rstrip("/") + "/") in s for e in ENFORCE
    )

def classify(abs_path):
    """Return 'deny' | 'allow' | None (not enforcement-relevant)."""
    p = Path(abs_path)
    probe = p.parent
    while not probe.is_dir() and probe != probe.parent:
        probe = probe.parent
    try:
        out = subprocess.run(
            ["git", "-C", str(probe), "rev-parse", "--path-format=absolute",
             "--git-common-dir", "--git-dir", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode != 0:
            raise RuntimeError(out.stderr)
        common, gitdir, top = out.stdout.splitlines()[:3]
    except Exception:
        # parse error: fail closed only when an enforcement-class target
        # is textually present (R-2)
        return "deny-parse" if textual_enforcement(abs_path) else None
    is_main = os.path.realpath(common) == os.path.realpath(gitdir)
    if not is_main:
        return None  # linked worktree: allowed
    if GUARD_ROOT and os.path.realpath(top) != GUARD_ROOT:
        return None  # foreign repository: not ours to police (round 3 P1)
    try:
        rel = str(Path(os.path.realpath(abs_path)).relative_to(os.path.realpath(top)))
    except ValueError:
        return None
    rel = rel.replace("\\", "/")
    if any(rel == dl.rstrip("/") or rel.startswith(dl) for dl in DOCS):
        return None
    if any(rel == e.rstrip("/") or rel.startswith(e) for e in ENFORCE):
        return "deny"
    return None

def resolve(p):
    p = str(p).strip().strip("'\"")
    return p if os.path.isabs(p) else os.path.join(cwd, p)

EDIT_TOOLS = {"create_file", "replace_string_in_file",
              "multi_replace_string_in_file", "apply_patch"}
escape = os.environ.get("FR888_ALLOW_MAIN", "") == "1"
verdict, target = None, ""

if tool in EDIT_TOOLS:
    paths = []
    if isinstance(ti, dict):
        if ti.get("filePath"):
            paths.append(ti["filePath"])
        for r in ti.get("replacements") or []:
            if isinstance(r, dict) and r.get("filePath"):
                paths.append(r["filePath"])
        patch = ti.get("input") or ti.get("patch") or ""
        if isinstance(patch, str):
            paths += re.findall(r"\*\*\* (?:Add|Update|Delete|Move to) File: (.+)", patch)
    for p in paths:
        c = classify(resolve(p))
        if c in ("deny", "deny-parse"):
            verdict, target = c, p
            break
else:
    cmd = ti.get("command", "") if isinstance(ti, dict) else ""
    if re.match(r"\s*FR888_ALLOW_MAIN=1\b", cmd):
        escape = True

    def write_targets(cmd):
        """Paths a command writes to — targets, not mentions (false-deny guard)."""
        targets = []
        for m in re.finditer(r">>?\s*[\"']?(" + PATHISH.pattern + ")", cmd):
            targets.append(m.group(1))
        for m in re.finditer(r"\btee\s+(?:-a\s+)?[\"']?(" + PATHISH.pattern + ")", cmd):
            targets.append(m.group(1))
        for seg in re.split(r"&&|\|\||;|\|", cmd):
            toks = seg.split()
            # strip env assignments and command wrappers (time/nohup/nice)
            # in any order — review PR#476 round 2 P1: 'time cp …' escaped
            while toks and (
                re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0])
                or toks[0] in ("time", "nohup", "nice")
            ):
                toks.pop(0)
            if toks and toks[0] in ("cp", "mv", "rsync", "install"):
                args = [t for t in toks[1:] if not t.startswith("-")]
                if len(args) >= 2:
                    dest, sources = args[-1], args[:-1]
                    targets.append(dest)
                    # P2 (review PR#476): a directory dest materializes
                    # dest/basename(src) — classify the materialized paths
                    for s in sources:
                        base = os.path.basename(s.rstrip("/"))
                        if base:
                            targets.append(dest.rstrip("/") + "/" + base)
            if toks and toks[0] == "sed" and "-i" in toks:
                targets += [t for t in toks[1:] if "/" in t and not t.startswith("-")]
        # opaque writers: any mentioned path is a potential target
        if re.search(r"python3?\s+-c|perl\s+-e|ruby\s+-e|\bdd\b|\btruncate\b", cmd):
            targets += [m.group(0) for m in PATHISH.finditer(cmd)]
        return targets

    for t in write_targets(cmd or ""):
        c = classify(resolve(t))
        if c in ("deny", "deny-parse"):
            verdict, target = c, t
            break

if verdict and escape:
    print("OVERRIDE\t" + target)
elif verdict:
    print("DENY\t" + verdict + "\t" + target.replace('"', ""))
PYEOF
) || FR888_OUT=""
    fi
    if [[ "${FR888_OUT:-}" == OVERRIDE* ]]; then
      audit_log "approve" "fr888-main-write-override" "cwd=$HOOK_CWD target=${FR888_OUT#OVERRIDE	} tool=$TOOL_NAME"
    elif [[ "${FR888_OUT:-}" == DENY* ]]; then
      FR888_TARGET="${FR888_OUT##*	}"
      audit_log "deny" "fr888-main-write" "cwd=$HOOK_CWD target=$FR888_TARGET tool=$TOOL_NAME"
      emit_deny "Enforcement write to the main checkout denied (FR-888): ${FR888_TARGET}.\\n\\nWork in an FR worktree (executable as written; rename the arc after):\\n  eval \$(scripts/worktree.sh new arc-\$(date +%H%M%S) | tail -1)\\n\\nEscape for genuine main-lane maintenance (audited):\\n  FR888_ALLOW_MAIN=1 <command>\\n(one_session_one_repo — details: feature-requests/FR-888-main-write-guard-worktree-route.md)"
      exit 0
    fi
    ;;
esac

# Only inspect run_in_terminal / send_to_terminal tool calls
if [[ "$TOOL_NAME" != "run_in_terminal" && "$TOOL_NAME" != "send_to_terminal" ]]; then
  audit_log "pass" "not-inspected" "$DETAIL"
  echo '{"decision":"approve"}'
  exit 0
fi

# Only block when the command is constructing a commit (git commit, writing msg files)
# Allow legitimate searches (grep, rg, cat, etc.) that merely reference the text
IS_COMMIT_CMD=false
if echo "$COMMAND" | grep -qiE '(git\s+commit|git\s+merge|>>?\s*.*msg|>>?\s*.*commit)'; then
  IS_COMMIT_CMD=true
fi

# Also block echo/printf/cat heredoc piping into files (writing trailer to a file)
if echo "$COMMAND" | grep -qiE '(echo|printf|cat\s*<<).*co-authored-by'; then
  IS_COMMIT_CMD=true
fi

if [[ "$IS_COMMIT_CMD" == "true" ]] && echo "$COMMAND" | grep -qi 'co-authored-by'; then
  audit_log "deny" "co-authored-by" "${COMMAND:0:200}"
  emit_deny "Co-authored-by trailers are forbidden. CI (copilot-trailer-gate) and pre-commit (block-ai-coauthor) will reject them. Remove the trailer before committing."
  exit 0
fi

# ── Check 2: --no-verify bypass ──────────────────────────────────────
# Block git/pre-commit commands using --no-verify. Allow grep/echo that mention it.
if echo "$COMMAND" | grep -qE '(git\s+(commit|push|merge|rebase)|pre-commit)\b' && \
   echo "$COMMAND" | grep -q '\-\-no-verify'; then
  audit_log "deny" "no-verify" "${COMMAND:0:200}"
  emit_deny "--no-verify is forbidden. Scripture: '[--no-verify flag will result in immediate termination]'. Remove the flag and let hooks run."
  exit 0
fi

# ── Check 3: multiline git commit -m ─────────────────────────────────
# Block git commit -m with newlines (causes dquote shell trap).
# Guide: write to ./tmp/msg.txt and use git commit -F ./tmp/msg.txt
# After JSON parsing, \n becomes actual newlines, so check line count.
if echo "$COMMAND" | head -1 | grep -qE 'git\s+commit\s+.*-m\s'; then
  LINE_COUNT=$(echo "$COMMAND" | wc -l | tr -d ' ')
  if [[ "$LINE_COUNT" -gt 1 ]]; then
  audit_log "deny" "multiline-m" "${COMMAND:0:200}"
  emit_deny "Multiline git commit -m triggers dquote shell trap. Write message to ./tmp/msg.txt and use: git commit -F ./tmp/msg.txt"
    exit 0
  fi
fi

# ── Check 4: pytest piped to head/tail without tee ───────────────────
# pytest output piped directly to head/tail buffers everything → agent
# sees no output until pytest exits, masking hangs and slow tests.
# Require tee for streaming: pytest ... 2>&1 | tee logs/run.log
if echo "$COMMAND" | grep -qE 'pytest\b' && \
   echo "$COMMAND" | grep -qE '\|\s*(head|tail)\b' && \
   ! echo "$COMMAND" | grep -qE '\|\s*tee\b'; then
  audit_log "deny" "pipe-buffer" "${COMMAND:0:200}"
  emit_deny "pytest piped to head/tail buffers all output until exit — hangs and failures are invisible.\\n\\nUse tee for streaming:\\n  pytest ... 2>&1 | tee logs/run.log\\n\\nThen inspect separately:\\n  tail -20 logs/run.log"
  exit 0
fi

# ── Check 5: branch creation in main worktree (FR-662) ───────────────
# Agents must not create branches in the main worktree.
# Isolation goes through chaplain worktrees, not local branches.
# Allow: git branch -d (delete), git branch --list, git branch -a, queries
if echo "$COMMAND" | grep -qE 'git\s+(checkout\s+-b|switch\s+-c|branch\s+[^-])'; then
  if ! echo "$COMMAND" | grep -qE 'git\s+branch\s+(-d|-D|--delete|--list|-a|-r|--merged|--no-merged|--contains|--no-contains|--sort|--show-current)'; then
    audit_log "deny" "branch-create" "${COMMAND:0:200}"
    emit_deny "Branch creation in main worktree is forbidden. Single-developer workflow: commit to main.\\n\\nFor isolated work, submit to .chaplain/inbox/ — the chaplain creates worktrees.\\nFor isolated manual work: scripts/worktree.sh new <name>\\n\\nTo delete stale branches: git branch -d <name>"
    exit 0
  fi
fi

# ── Check 7: ramp spike-end detector (FR-869) — warn-only, forever ───
# Plain foreign-cwd commits only; never changes the decision.
# Detector-local git usage is read-only (diff --cached); no repo mutation.
RAMP_W1=""
RAMP_W2=""
case "$COMMAND" in
  "git commit"*)
    RAMP_ROOT=""
    if [[ -n "${HOOK_CWD:-}" && -d "${HOOK_CWD:-}" ]]; then
      RAMP_D=$(cd "$HOOK_CWD" 2>/dev/null && pwd -P) || RAMP_D=""
      while [[ -n "$RAMP_D" && "$RAMP_D" != "/" ]]; do
        if [[ -e "$RAMP_D/.git" ]]; then RAMP_ROOT="$RAMP_D"; break; fi
        RAMP_D=$(dirname "$RAMP_D")
      done
    fi
    OWN_ROOT=$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd -P) || OWN_ROOT=""
    # Foreign plain repo only: worktree .git-files and this repo are skipped.
    if [[ -n "$RAMP_ROOT" && -d "$RAMP_ROOT/.git" && "$RAMP_ROOT" != "$OWN_ROOT" ]]; then
      if [[ -f "$RAMP_ROOT/.ramp-declined" ]]; then
        audit_log "warn" "ramp-declined" "$RAMP_ROOT"
      elif [[ ! -s "$RAMP_ROOT/.git/hooks/pre-commit" ]]; then
        RAMP_W1="⚠ this repo has no pre-commit hooks — scripts/ramp.sh <repo> --tier 1 exists"
        audit_log "warn" "ramp-unenforced" "$RAMP_ROOT"
        if git -C "$RAMP_ROOT" diff --cached -- '.github/workflows/*.yml' '.github/workflows/*.yaml' 2>/dev/null \
           | grep '^+' | grep -v '^+++' | grep -qE 'schedule:|secrets\.'; then
          RAMP_W2="⚠ this commit takes an unenforced repo live"
          audit_log "warn" "ramp-spike-end" "$RAMP_ROOT"
        fi
      fi
    fi
    ;;
esac
if [[ -n "$RAMP_W1" ]]; then echo "$RAMP_W1" >&2; fi
if [[ -n "$RAMP_W2" ]]; then echo "$RAMP_W2" >&2; fi

audit_log "approve" "clean" "${COMMAND:0:200}"
echo '{"decision":"approve"}'
exit 0
