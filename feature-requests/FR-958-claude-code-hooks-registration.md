# Feature Request: FR-958 Register the hook enforcement layer for Claude Code

**Priority:** HIGH
**Type:** Feature (enforcement infrastructure — human-review gate, FR-883 R-4)
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-09-02
**First consumer / first event:** the Claude Code session operating this
repo on the Windows host, at its first `Bash` tool call after
`.claude/settings.json` lands — today that call is approved by nobody.
On Claude Code the reasoning-pattern check covers **visible assistant
text and the short visible thinking summaries the transcript persists**,
not private reasoning; that is the coverage this FR claims and no more.
**Research:** [FR-958.research.md](FR-958.research.md) — FR-890 sole
route, run 2026-09-02 against
[research-briefs/fr958-claude-code-hooks-port-brief.md](research-briefs/fr958-claude-code-hooks-port-brief.md);
dispositioned in the alternatives table below (§ Proposed Solution 6).
**Prior art:** [FR-438-thoughtcrime-hook.md](FR-438-thoughtcrime-hook.md)
— defined the transcript scan and one-shot sentinel against the Copilot
transcript's `reasoningText`; this FR re-scopes that premise for a
runtime that does not persist reasoning.
[FR-439-tone-down-enforcement-terminology.md](FR-439-tone-down-enforcement-terminology.md)
— the neutral names this FR reuses unchanged.
[FR-883-block-concealed-refusal-task-alteration.md](FR-883-block-concealed-refusal-task-alteration.md)
— the current registry and the R-1 no-overclaim / R-4 human-review
rulings this FR inherits. FR-414 (audit trail), FR-440 (pipe-buffer
guard), FR-662 (main-worktree branch guard), FR-767 (graph-authoring
sole-route guard), FR-743 (session briefing), FR-877 (memory advisory)
— the rules being registered; none of them changes. FR-424
(session-timeline join) — its transcript discovery shares the macOS
path defect fixed here. FR-425 (classifier daemon) — Phase 2 of FR-438;
not activated, answers `is_this_a_graph` in the negative for this
boundary. [FR-163-chaplain-inbox-instructions-in-claude-md.md](FR-163-chaplain-inbox-instructions-in-claude-md.md)
— the only prior Claude Code FR; instructions, not enforcement. FR-951
(encoding boundary) and FR-953 (Windows shell) — the host-class defects
that shape the Windows constraints. No REJECTED FR governs multi-runtime
hook registration.

## Summary

Register the existing `.github/hooks/` scripts for Claude Code through
`.claude/settings.json`, normalise the two agents' tool vocabularies in
the one shared input parser, replace the macOS-only transcript glob with
the `transcript_path` both runtimes already supply, teach the
reasoning-pattern scanner the Claude Code transcript shape, stamp the
audit trail with the producing runtime, and make the scripts resolve a
working interpreter on the Windows host. No rule changes. No second copy
of any guard.

## Value Statement

Operators running Claude Code in this repo get the same deterministic
enforcement (trailer block, `--no-verify` block, governed-write guard,
reasoning sentinel, audit trail) that Copilot sessions get, from the same
scripts, so a rule added for one agent is a rule for both.

## Problem

`.github/hooks/README.md` documents "deterministic lifecycle hooks for
VS Code Copilot agent sessions". Claude Code reads hooks from
`.claude/settings.json`, `.claude/settings.local.json`, or
`~/.claude/settings.json`; none exists here. Every Claude Code session
in this repo runs with the Scripture as advisory text only. On the
operator's Windows host `.github/hooks/logs/audit.jsonl` has never been
written: zero hook firings, for any agent, ever.

The contract is already almost shared. Both runtimes deliver
`tool_name`, `tool_input`, `session_id`, `cwd`, `hook_event_name` and
`transcript_path` on stdin, and both accept the
`hookSpecificOutput.permissionDecision` deny shape that
`pre-command-guard.sh:43` emits. Three things do not transfer:

1. **Registration.** Claude Code's schema wraps each event's hooks in a
   matcher group (`{"matcher": "<regex on tool_name>", "hooks": [...]}`)
   and lives in settings, not in a hooks directory.
2. **Tool vocabulary.** The guard (`pre-command-guard.sh:91,114,240-241,
   282,310`), the post-edit dispatcher (`checks/common.sh:12`) and the
   main-write guard (`checks/main_write.py:47-50`) allowlist Copilot's
   `run_in_terminal` / `create_file` / `replace_string_in_file` /
   `multi_replace_string_in_file` / `apply_patch`, with `filePath` and
   `replacements[]`. Claude Code sends `Bash`, `Write`, `Edit`,
   `MultiEdit`, `NotebookEdit`, with `file_path`, `old_string`,
   `new_string`, `edits[]`. A Claude Code `Bash` call is currently
   "not a terminal tool" and a `Write` is "not an edit": every check
   falls through to approve.
3. **Transcript.** `reasoning-pattern-check.sh:36-50` globs
   `~/Library/Application Support/Code/User/workspaceStorage/*/GitHub.copilot-chat/transcripts/<sid>.jsonl`
   and reads `assistant.message.data.reasoningText`. Claude Code writes
   `~/.claude/projects/<slug>/<sid>.jsonl` with `type: "assistant"`
   lines, one per content block, grouped by `requestId`, whose blocks
   are `thinking` / `text` / `tool_use`. Measured on this host (four
   sessions, 228 thinking blocks): 25 % carry text, longest 534 chars,
   all one-sentence progress summaries. The rest persist a `signature`
   and an empty string. FR-438's premise — private reasoning is
   observable at the hook boundary — is false for this runtime. Its
   shipped `content` fallback is what remains.

A fourth, host-level obstacle: the scripts call `python3` (on this host
the Windows Store 3.10 stub) and several hardcode `.venv/bin/python`
(the venv here is `.venv/Scripts/python.exe`). They would run under Git
Bash, and several would exit 0 having done nothing.

## Ideal Result

One `.github/hooks/scripts/` tree, two thin registrations. A tool call
from either agent reaches the same guard, is classified by the same
canonical vocabulary, is logged to the same audit file with a `runtime`
field, and is denied with the same message. The reasoning-pattern check
reads whatever transcript the runtime hands it, scans the latest
assistant turn's thinking text and visible text, and its documentation
states exactly that. On a host without a resolvable interpreter the
hooks leave one audit line saying so and get out of the way. The
Copilot tests stay green untouched; a parallel Claude Code fixture set
proves parity rule by rule.

## Proposed Solution

### 1. Registration: `.claude/settings.json` (committed, project scope)

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.github/hooks/scripts/pre-command-guard.sh", "timeout": 5 }
      ] }
    ],
    "PostToolUse": [
      { "matcher": "Write|Edit|MultiEdit|NotebookEdit", "hooks": [
        { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.github/hooks/scripts/checks/python-checks.sh", "timeout": 10 },
        { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.github/hooks/scripts/checks/yaml-checks.sh", "timeout": 10 },
        { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.github/hooks/scripts/checks/markdown-checks.sh", "timeout": 5 },
        { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.github/hooks/scripts/checks/fr-checks.sh", "timeout": 5 }
      ] },
      { "matcher": "", "hooks": [
        { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.github/hooks/scripts/reasoning-pattern-check.sh", "timeout": 5 },
        { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.github/hooks/scripts/classify-emit.sh", "timeout": 5 }
      ] }
    ],
    "SessionStart": [
      { "hooks": [
        { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.github/hooks/scripts/session-briefing.sh", "timeout": 8 }
      ] }
    ]
  }
}
```

The guard runs on every tool (empty matcher) because lockdown and the
armed sentinel must deny *any* next call, as they do for Copilot. The
`session-probe.sh` FR-743 probe is not registered; its question ("do
these events fire, what arrives") is answered by AC-02's fixture run.
Contract facts checked against the Claude Code hooks documentation on
2026-09-02: hooks from user, project and local settings are *merged*,
not overridden; `matcher` is a regex on `tool_name` and an empty string
matches every tool; `timeout` is in seconds; `${CLAUDE_PROJECT_DIR}` is
available to `command`; exit 2 blocks with stderr as the reason, and
the `hookSpecificOutput.permissionDecision` shape (`allow` / `deny` /
`ask`) is the current PreToolUse contract — the guard's existing
`{"decision":"approve"}` on the allow path is ignored on Claude Code,
which is the intended behaviour (no auto-approve; normal permission
flow). The older top-level `decision: approve|block` PreToolUse form is
no longer documented; AC-01 pins the deny path only.

### 2. One canonical tool vocabulary

Add `.github/hooks/scripts/checks/hook_input.py` (stdlib only), the
single place that reads hook stdin and returns
`(runtime, tool_class, command, paths, session_id, tool_use_id, cwd,
transcript_path)`:

| canonical `tool_class` | Copilot `tool_name` | Claude Code `tool_name` | path fields read |
|---|---|---|---|
| `terminal` | `run_in_terminal`, `send_to_terminal` | `Bash` | — (`command`) |
| `edit` | `create_file`, `replace_string_in_file`, `multi_replace_string_in_file`, `apply_patch` | `Write`, `Edit`, `MultiEdit`, `NotebookEdit` | `filePath`, `file_path`, `replacements[].filePath`, `edits[]` (parent `file_path`), `notebook_path`, patch headers |
| `read` / `other` | everything else | everything else | — |

`runtime` is derived from the vocabulary actually seen (`claude-code`
when a Claude tool name or `permission_mode` field is present,
`copilot` otherwise, `unknown` never approves an edit — fail closed,
FR-767 C-5). `pre-command-guard.sh`, `common.sh` and `main_write.py`
switch from their literal name lists to `tool_class`. Every existing
Copilot test passes unchanged because the mapping is a superset.

### 3. Transcript adapter for the reasoning-pattern check

`reasoning-pattern-check.sh` reads `transcript_path` from stdin first
and only falls back to the Copilot workspaceStorage glob when the field
is absent (Copilot builds that predate the field). `session-timeline.py`
`discover_transcript` gains the same precedence. The scanner grows a
second parser:

- Copilot: latest `assistant.message` → `reasoningText` else `content`
  (unchanged).
- Claude Code: latest `requestId` among `type: "assistant"` lines →
  concatenation of that turn's `thinking` texts, then its `text`
  blocks. Both are scanned; the audit `source` field records
  `thinking`, `text`, or `thinking+text`.

The one-shot sentinel, the UUID guard, and the `.reasoning-flag-<sid>`
name are untouched. Claude Code's PostToolUse `decision: "block"` path
is **not** used in this FR: it would show the doctrine one call earlier
but the sentinel already delivers the denial, and one mechanism is
easier to witness than two (brief constraint 4; option E below).

### 4. Audit trail carries the runtime

Every `audit.jsonl` entry gains `"runtime": "copilot" | "claude-code"`.
`session-timeline.py` prints it. Nothing else in the log format changes
(FR-414 consumers keep working; new key only).

### 5. Interpreter resolution on Windows

`common.sh` gains `resolve_python()`: `$HOOK_PYTHON` → `.venv/bin/python`
→ `.venv/Scripts/python.exe` → `python3` → `python`; a result older than
3.11 or absent writes one audit line `{"decision":"skip","reason":
"no-interpreter"}` and exits 0 (fail-open with evidence, FR-877
pattern). `session-briefing.sh`, `memory-advisory.sh`,
`reasoning-pattern-check.sh` and `pre-command-guard.sh` call it instead
of their private `python3` / `.venv/bin/python` literals. The scripts
remain bash; on Windows, Claude Code runs shell-form `command` hooks
under Git Bash (PowerShell only when Git Bash is absent), and offers an
exec form (`args: []`) that bypasses the shell — the shell form is used
here so the scripts stay identical for both agents (pinned by AC-09 on
this host). `file_path` values arrive with backslashes on Windows; the
adapter normalises separators before matching governed-path globs.

### 6. Alternatives (dispositioned record, FR-889 style)

| class | mechanism | precedent | cost / risk | disposition |
|---|---|---|---|---|
| A. Shared scripts + thin second registration + vocabulary adapter | §§1–5 above | Research route: os-infra-primitivist and data-process-planner converged on this class (x2); librarian's external precedent, AxonFlow's Claude Code integration (two registrations, one guard logic, tool-vocabulary mapping at the adapter). In-repo: the FR-767 guard already parses both `tool_name`/`toolName`; `common.sh:62` already reads `file_path` as a fallback — the codebase half-anticipated a second vocabulary | Medium: one parser touches three enforcement scripts; mitigated by the Copilot suite staying green and a parity fixture set | **CHOSEN** |
| B. Separate `.claude/hooks/` script tree | Copy the scripts, edit names | none in repo | Drift: the defect this FR names, reproduced by design | REJECTED |
| C. Point `.claude/settings.json` at `.github/hooks/*.json` | Reuse the Copilot JSON files | — | Different schema (matcher groups); Claude Code cannot load them | REJECTED — not possible |
| D. Hooks as a yamlgraph graph / FR-425 daemon in the hot path | Route hook stdin through the classifier daemon, or (yamlgraph-native planner's variant) extract the guard logic into a deterministic `python` graph node fed by per-runtime marshalling adapters | FR-425 (Phase 2 of FR-438); `examples/demos/hook_classifier/graph.yaml` | 5 s budget with a graph runtime start per tool call; no LLM in the hot path (FR-883 constraint); daemon not activated; would move 31+ shell contract tests onto a new surface; `is_this_a_graph`: **no** for the boundary — the adapter *body* becomes a stdlib module (§2), not a node | REJECTED for this boundary; FR-425 stays the async Phase 2 |
| E. Drop the sentinel on Claude Code; use PostToolUse `decision: block` feedback | Immediate doctrine text after the scan, no deny | Claude Code hook docs | Advisory only — the agent may proceed; two mechanisms to witness; brief constraint keeps the sentinel | REJECTED as a replacement; may be *added* by a later FR with evidence |
| F. Rely on `CLAUDE.md` instructions | Status quo | FR-163 | Instructions are the untrusted boundary the hooks exist to back-stop | REJECTED — it is the defect |
| G. Port the reasoning scan unchanged and describe it as reasoning coverage | Same scanner, same README claim | FR-438 § Research | Overclaim: 75 % of thinking blocks persist no text on this runtime; FR-883 R-1 forbids exactly this | REJECTED — coverage statement re-scoped (first-consumer line) |
| H. Add a Claude Code `Stop` / `UserPromptSubmit` scan of the final assistant message | Extra scan surface Copilot lacks | Claude Code event list | New surface, no witnessed incident yet | DEFERRED — out of scope; noted for a follow-on |
| I. Delete the reasoning-pattern check on both runtimes | Retire FR-438/883 as a no-goal because its premise fails on Claude Code | Research route: subtractionist dissent; FR-883 R-1 | Removes a check that works on Copilot (`reasoningText` present) and still has the `content` fallback on Claude Code; the FR-885 phrases are witnessed registry evidence | REJECTED as deletion; **accepted as re-scoping** — the dissent becomes AC-08's binding constraint on the README claim (preserved disagreement, see research record) |

`is_this_a_graph`: no. Registration is a settings file the runtime
reads before any node exists; the adapter is a stdin parser inside a
5 s budget. The graph-shaped construct (FR-425) sits behind the
sentinel asynchronously and is unchanged.

## Acceptance Criteria

- [ ] AC-01 (RED first): `.github/hooks/tests/test_fr958_claude_runtime.py`
      feeds Claude Code-shaped stdin (`Bash` with `command`, `Write` /
      `Edit` / `MultiEdit` / `NotebookEdit` with `file_path`) into
      `pre-command-guard.sh`, `python-checks.sh`, `yaml-checks.sh`,
      `markdown-checks.sh`, `main_write.py`; asserts the same
      decisions the Copilot fixtures get for the same intents
      (trailer deny, `--no-verify` deny, multiline `-m` deny, governed
      write deny without sentinel, ruff finding reported). Fails today.
- [ ] AC-02: `.claude/settings.json` committed with the registration in
      §1; a fixture session on the Windows host produces an
      `audit.jsonl` line for a `Bash` PreToolUse with
      `"runtime": "claude-code"` — the first hook firing on this host.
- [ ] AC-03: `hook_input.py` is the only place tool names are
      interpreted; `grep -n 'run_in_terminal\|create_file' .github/hooks/scripts`
      returns hits only inside that module (and comments).
- [ ] AC-04: all existing `.github/hooks/tests/` pass unchanged (no
      fixture edits; the Copilot vocabulary is a subset of the map).
- [ ] AC-05: `reasoning-pattern-check.sh` uses stdin `transcript_path`
      when present; a Claude Code-shaped transcript fixture with the
      FR-883 phrase `safety envelope` in a `text` block arms
      `.reasoning-flag-<sid>`; the same phrase in a *non-latest*
      requestId does not; an empty-`thinking` + clean-`text` turn logs
      `skip/no-scannable-text` or `armed` with `source=text`, never a
      parse error.
- [ ] AC-06: the Copilot transcript path fallback still works (existing
      `test_reasoning_pattern_check.py` fixtures untouched and green).
- [ ] AC-07: `session-timeline.py` resolves a Claude Code transcript via
      `transcript_path` and prints the `runtime` column.
- [ ] AC-08: `.github/hooks/README.md` § Active Hooks states the
      coverage on Claude Code as "latest turn's persisted thinking
      summaries and visible text"; nowhere does it claim private
      reasoning coverage for that runtime (FR-883 AC-07 precedent).
- [ ] AC-09: `resolve_python()` witnessed on the Windows host: with the
      venv present the guard denies a trailer commit; with
      `HOOK_PYTHON=/nonexistent` it exits 0 and leaves exactly one
      `skip/no-interpreter` audit line; hook wall time < 5 s in both.
- [ ] AC-10: `docs(fr)` hygiene — this FR's Implementation Status
      records the measured thinking-persistence numbers at ship time
      and the fixture session id; one changelog fragment (`feat`,
      scope `hooks`); one diary reflection (the "one layer, two
      runtimes" trap).
- [ ] AC-11: human review before merge (FR-883 R-4) recorded in the PR
      body; no rule text, registry phrase, or deny message changes.
- [ ] AC-12: `CLAUDE.md` gains one line pointing at
      `.github/hooks/README.md` for the hook layer; doctrine stays in
      `copilot-instructions.md` only.

## Constraints

- No new rule, no registry change, no deny-message change: registration
  and adaptation only (option G is the boundary).
- Deterministic, stdlib-only, inside the declared timeouts; no LLM in
  any hook process (FR-883 constraint carried forward).
- Fail closed on unparseable edits to governed paths (FR-767 C-5); fail
  open with an audit line only for the missing-interpreter case.
- `.github/hooks/logs/` remains the single sink; the `.gitignore`
  there already covers the sentinel and JSONL files.

## Related

- `.github/hooks/README.md`, `.github/hooks/*.json` (Copilot registration)
- `.github/hooks/scripts/pre-command-guard.sh:43-79,91-120,230-250`
- `.github/hooks/scripts/reasoning-pattern-check.sh:36-50,53-140`
- `.github/hooks/scripts/checks/common.sh:12,33-66`
- `.github/hooks/scripts/checks/main_write.py:47-50`
- `.github/hooks/scripts/session-timeline.py:52-73`
- `~/.claude/projects/C--src-yamlgraph/*.jsonl` (measurement source, 2026-09-02)
- [FR-958.research.md](FR-958.research.md), [research brief](research-briefs/fr958-claude-code-hooks-port-brief.md)

### Questions for the human (as options, or 'none')

1. **Registration scope.** Commit `.claude/settings.json` (project,
   applies to every clone — *recommended*: parity is the point) vs
   `.claude/settings.local.json` documented in README (per-operator
   opt-in, gitignored) vs user-level `~/.claude/settings.json` (host
   only, no repo record). Evidence: FR-889 routes all agents through
   the same worktree discipline; per-operator opt-in would recreate
   the silent-runtime gap on the next clone.
2. **Option H timing.** Defer the `Stop`-event scan (recommended: no
   witnessed incident) vs include it now as the Claude Code substitute
   for the missing reasoning surface. Evidence arrives with AC-05's
   measurement of how often the FR-883 phrases appear in `text` at all.
