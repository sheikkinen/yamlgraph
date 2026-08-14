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
    for value in (tool, cmd, detail, sid, tuid):
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
  IFS= read -r -d '' TOOL_USE_ID
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

audit_log "approve" "clean" "${COMMAND:0:200}"
echo '{"decision":"approve"}'
exit 0
