# Judgement: FR-961 Register the hook enforcement layer for Claude Code

**Verdict:** APPROVED WITH REVISIONS — the defect is real, the chosen class is the minimal one, and the research record clears the FR-890 gate; but authority activates only after the FR proves the guard's allow path does not auto-approve on Claude Code, commits the measurement its coverage re-scope rests on, closes the interpreter seam across all 16 script files rather than the 4 it names, resolves the `unknown`-runtime contradiction, and makes AC-01/AC-03/AC-09 mechanically runnable.

**Reviewed against:** `feature-requests/FR-961-claude-code-hooks-registration.md`; `feature-requests/FR-961.research.md`; `feature-requests/research-briefs/fr961-claude-code-hooks-port-brief.md` (existence and citation only); `feature-requests/FR-883-block-concealed-refusal-task-alteration.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md` (§ Copilot Hooks, lines 27-34); `CLAUDE.md`; `.github/hooks/README.md`; `.github/hooks/session-probe.json`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/scripts/reasoning-pattern-check.sh`; `.github/hooks/scripts/classify-emit.sh`; `.github/hooks/scripts/session-briefing.sh`; `.github/hooks/scripts/session-timeline.py`; `.github/hooks/scripts/checks/common.sh`; `.github/hooks/scripts/checks/main_write.py`; `.github/hooks/tests/conftest.py`; `.github/hooks/tests/test_copilot_instructions_hooks_docs_red.py`; `.gitignore`; directory listings of `.github/hooks/**` and `.claude/**`.

Not consumed: the author's session transcript, planning notes, or any uncommitted working file. The `~/.claude/projects/…` measurement source cited at FR-961:315 is outside the input closure and outside the repository — see R-2.

## What is sound

**The problem is witnessed, not asserted.** `.claude/**` returns no files; `.github/hooks/logs/` contains only `.gitignore` and `memory-curation-audit.jsonl` — there is no `audit.jsonl`. The claim "zero hook firings, for any agent, ever" on this host is directly checkable and true.

**The evidence citations are accurate.** Every line reference I sampled resolves: `common.sh:12` is the `is_edit_tool` allowlist; `common.sh:62` does already fall back to `file_path`; `main_write.py:46-51` is the `EDIT_TOOLS` set; `reasoning-pattern-check.sh:36-50` is the macOS `workspaceStorage` glob; `session-timeline.py:52-73` is the same glob in `discover_transcript`; `pre-command-guard.sh:59,161` do already parse both `tool_name` and `toolName`. The FR's argument that "the codebase half-anticipated a second vocabulary" is supported by the code it cites.

**The registration is genuinely parity, not expansion.** I checked the one place this could have gone wrong: `session-briefing.sh` looked unregistered until `session-probe.json:9-13` showed it already bound to Copilot's `SessionStart` with `timeout: 8` — the same event and the same timeout the FR proposes. `memory-advisory.sh` is reached transitively at `session-briefing.sh:16`, so it needs no separate entry. The FR's "no second copy of any guard, no rule changes" holds for the surfaces it registers.

**The research record has substance, not shape.** Four solution classes with distinct mechanisms, real precedent lines (in-repo FR-767/FR-425 plus an external one), an explicitly preserved dissent (the subtractionist's delete-it-on-both-runtimes position, carried forward as a binding constraint on the README rather than silently dropped), and `is_this_a_graph` answered in the negative with the yamlgraph-native planner's contrary "yes" localised to the adapter body and dispositioned as class 2. It also volunteers two defects against itself — the CRLF `--verify-promotion` mismatch and the `</anionale> </invoke>` markup leak in the data-process-planner row — rather than repairing the artifact and breaking provenance. That is the FR-890 gate cleared on substance.

**The FR under-claims where FR-883 R-1 demands it.** The first-consumer paragraph states the coverage as visible text plus persisted thinking summaries "and no more", and option G explicitly names the overclaim it is refusing to make. Inheriting a prior judgement's no-overclaim ruling without being told to is the right instinct.

**Strategic classification.** This is not a new framework primitive. It adds a second consumer to an existing enforcement primitive plus one adapter module — extension of an existing abstraction. The FR does not claim more, and the alternatives table correctly refuses to promote the hook boundary into a graph.

**On SPLIT.** I considered it. §5 (interpreter resolution) is arguably a runtime-independent host-portability fix — it is why nothing has ever fired here for *either* agent — and §3's `transcript_path` precedence independently repairs FR-424's macOS-only discovery. But these are not orthogonal concerns; they are one dependency chain to one outcome. Without §5 the registration silently no-ops on the first-consumer host; without §2 the registration approves everything. A split would also produce a fragment whose only witness is "Copilot hooks now fire on Windows", which nobody on this host is positioned to observe. Kept whole, sequenced by C-2 and AC-14.

## Required revisions

### R-1: Witness that the allow path does not auto-approve on Claude Code, and fail safe by default

`pre-command-guard.sh:312` and `:416` print `{"decision":"approve"}` on every clean path. §1 disposes of this in one clause — "ignored on Claude Code, which is the intended behaviour (no auto-approve; normal permission flow)" — resting on "the older top-level `decision: approve|block` PreToolUse form is no longer documented". Undocumented is not unhandled, and deprecated-but-still-honoured is precisely the dangerous case. If that key is still interpreted, registering this guard converts every tool call in every Claude Code session in this repo into a silently pre-approved call and removes the operator's permission prompt. An FR whose purpose is to *add* enforcement must not be able to *remove* the permission boundary by accident, and no current AC would detect it: AC-01 pins the deny path only, AC-02 asserts an audit line (which is written on both paths), AC-09 witnesses a denial.

Fold both halves:

1. Behaviour: when `runtime == "claude-code"`, the guard's clean and not-inspected paths emit `{}` on stdout, never `{"decision":"approve"}`. The `copilot` path is unchanged so existing tests stay green. Audit rows (`pass/not-inspected`, `approve/clean`) are unaffected — this is a stdout change only.
2. Witness: a new AC requiring a live Claude Code session, with the guard registered, in which a permission-requiring `Bash` call still produces the normal operator permission prompt. Record the session id in Implementation Status.

### R-2: Commit the measurement the coverage re-scope rests on

The numbers in Problem §3 — four sessions, 228 thinking blocks, 25 % carrying text, longest 534 chars, "all one-sentence progress summaries" — are load-bearing three times over: they kill FR-438's premise for this runtime, they set AC-08's README wording, and they are the stated reason option I is re-scoped rather than accepted. Their only source is `~/.claude/projects/C--src-yamlgraph/*.jsonl` (FR-961:315): outside the repository, host-local, unverifiable by me under input closure and by any later reviewer. This repo's local judge law requires an evidenced raw read — N cited samples with surprising detail — before a measurement grants authority. The direction of the claim is conservative, which is why this is a revision and not a rejection; but a number that decides whether a safety check survives must be auditable.

Fold an evidence appendix into the FR containing: (a) the exact command or script that produced the four counts, runnable against a `~/.claude/projects/<slug>/` tree; (b) four verbatim `thinking` block texts quoted in full (they are ≤534 chars — redact repo-sensitive strings, never truncate to hide length), plus one empty-text block shown with its `signature` value elided, demonstrating the shape claim; (c) the four session ids and the capture date. AC-10's "measured numbers at ship time" then means re-running (a).

### R-3: Close the interpreter seam across every script, and put `resolve_python()` where `sh` can source it

§5 names four callers. The actual surface is 43 occurrences of `python3` / `.venv/bin/python` across 16 files under `.github/hooks/scripts/` (shebangs included in that count; exclude them from the target set). Three concrete defects make §5 as written non-working:

1. `session-briefing.sh:1` is `#!/bin/sh`. `common.sh` is `#!/usr/bin/env bash` and uses arrays (`FILE_PATHS=()`, line 8) and `[[ ]]`. It cannot be sourced from a POSIX-`sh` script.
2. `reasoning-pattern-check.sh` and `pre-command-guard.sh` do not source `common.sh` today, and `common.sh:4` sets `LOG_DIR="${HOOK_LOG_DIR:-$(dirname "$0")/../../logs}"`. Sourced from a script in `scripts/`, `$0` is the sourcing script, so that resolves to `.github/logs` — silently splitting the audit sink away from `.github/hooks/logs/` in production while tests that set `HOOK_LOG_DIR` stay green. This is the exact shape of the defect the FR exists to fix, reintroduced by the fix.
3. `common.sh` itself calls literal `python3` at lines 33, 34, 35, 42, 76, 108 — the audit writer, the stdin parser and `emit_result`. `pre-command-guard.sh` calls it at 23, 54, 105, 106, 130, 149, 291. §5 lists neither file's internals. Left as-is on this host, the post-edit checks and the audit writer stay on the Windows Store stub, so hooks would appear registered and still write nothing.

Fold: create `.github/hooks/scripts/lib/resolve_python.sh`, POSIX-`sh` compatible, exporting `HOOK_PY` and setting **no other globals** (in particular no `LOG_DIR`). Every script under `.github/hooks/scripts/**` sources it and uses `"$HOOK_PY"`. State that `hook_input.py` and `main_write.py` are invoked as `"$HOOK_PY" <script>`. Add the grep AC in AC-15.

### R-4: Resolve the `unknown` runtime contradiction and pin its fail-closed test

§2 states the detection rule as: `claude-code` when a Claude tool name or `permission_mode` is present, "`copilot` otherwise, `unknown` never approves an edit — fail closed, FR-767 C-5". If the fallback is `copilot`, `unknown` is unreachable and the fail-closed clause is dead text. Fold the three-way rule explicitly:

- Claude marker (Claude tool name, or `permission_mode` present) → `claude-code`
- `tool_name` in the known Copilot list → `copilot`
- neither → `unknown`

and state that `unknown` + a governed path in any of `filePath` / `file_path` / `replacements[]` / `edits[]` / `notebook_path` is denied, with `"runtime": "unknown"` in the audit row. AC-16 pins it.

### R-5: Make AC-01 and AC-04 runnable on the host that witnesses AC-02 and AC-09

`tests/conftest.py:30` runs `subprocess.run([str(script)], …)` — executing the `.sh` path directly. That cannot work on Windows, which has no shebang dispatch; the new `test_fr961_claude_runtime.py` would inherit the same helper and be unrunnable on the very host AC-02 and AC-09 designate as the first consumer. Fold one of two explicit positions:

- **(a)** `conftest.run_hook` gains a `bash` prefix when `os.name == "nt"`, this conftest change is declared in scope, and AC-04's "unchanged" is redefined to mean *fixture payloads and assertions* unchanged — not `conftest.py`; or
- **(b)** AC-01/AC-04/AC-05/AC-06 are declared macOS-run and AC-02/AC-09 the Windows-witnessed pair, with the FR stating plainly that the RED test for this FR never executes on the host it ships for.

(a) is the stronger deliverable. Either way the FR must say which, because a silent choice here decides whether AC-01 is real.

### R-6: Fix AC-03's command and state its expected hit set

`grep -n 'run_in_terminal\|create_file' .github/hooks/scripts` as written errors on a directory — it needs `-rn`. The current hit set is 16 occurrences across exactly three files: `pre-command-guard.sh` (9), `main_write.py` (5), `common.sh` (2), at `pre-command-guard.sh:91,114,147-148,240-241,279-282,310`, `main_write.py:46-51`, `common.sh:12`. The FR's citation list at line 76 omits the two `case` heads (`:147-148`, `:279-280`), which are the actual dispatch allowlists and must convert. Fold the AC as: after the change, `grep -rn 'run_in_terminal\|send_to_terminal\|create_file\|replace_string_in_file\|multi_replace_string_in_file\|apply_patch\|\bBash\b\|\bMultiEdit\b\|\bNotebookEdit\b' .github/hooks/scripts` returns hits only in `checks/hook_input.py` and comment lines.

### R-7: Register only what an acceptance criterion witnesses — dispose of `classify-emit.sh`

§1 binds `classify-emit.sh` to Claude Code `PostToolUse` on the empty matcher, i.e. every tool call, and no AC mentions it. Against it: the FR itself states the FR-425 daemon is not activated (alternatives row D); the script's transport is an `AF_UNIX` DGRAM to `/tmp/statemachine-control-hook-classifier.sock` (`classify-emit.sh:9,44`), which cannot exist on the Windows first-consumer host; and its documented purpose (`README.md:313,412`) is forwarding tool names and redacted command text to an LLM classifier. Sending a Claude Code session's tool stream to an LLM daemon is a spend-and-data decision belonging to the operator, and it is in tension with the FR's own constraint "no LLM in any hook process".

Fold: drop the `classify-emit.sh` entry from `.claude/settings.json` — the FR that activates the daemon can add it with its own witness. If it is kept instead, add an AC witnessing exit 0 with no socket present and record the human's answer to Q-3.

### R-8: Pin AC-09's deny witness to a live tool call

AC-09 reads "with the venv present the guard denies a trailer commit" without naming the path. Fed by piped stdin it only re-proves AC-01 and leaves the deny-shape claim (FR-961:71, that Claude Code honours `hookSpecificOutput.permissionDecision: "deny"` from this script) untested on the runtime. Fold: AC-09's denial must be observed as a Claude Code `Bash` tool call that the runtime refused, with the operator-visible reason text, the `audit.jsonl` row, and the session id recorded in Implementation Status.

### R-9: Freeze the Scripture hooks section

`.github/copilot-instructions.md:30` is the literal header `### Copilot Hooks (.github/hooks/)`, and `tests/test_copilot_instructions_hooks_docs_red.py:11` pins that exact string, with `:46-58` pinning nine required tokens and `:67` capping the section at 15 non-empty lines. A layer that now serves two runtimes invites renaming that header; renaming it breaks the test, and expanding it breaks the budget. AC-12 already routes the Claude-facing pointer to `CLAUDE.md`. Fold an explicit statement that the header text, the token list and the 15-line budget are frozen under this FR and that `.github/copilot-instructions.md` is not edited.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.claude/settings.json` — registration per §1, minus `classify-emit.sh` (R-7), scope per Q-1 |
| D-2 | `.github/hooks/scripts/checks/hook_input.py` — new, stdlib only, sole interpreter of tool names |
| D-3 | `.github/hooks/scripts/lib/resolve_python.sh` — new, POSIX `sh`, exports `HOOK_PY`, sets nothing else (R-3) |
| D-4 | `pre-command-guard.sh`, `checks/common.sh`, `checks/main_write.py` — `tool_class` switch, `HOOK_PY`, claude-code allow-path output (R-1) |
| D-5 | `reasoning-pattern-check.sh` — `transcript_path` precedence, Claude transcript parser, `source` field |
| D-6 | `session-timeline.py` — `discover_transcript` precedence, `runtime` column |
| D-7 | `runtime` key in every `audit.jsonl` writer |
| D-8 | `.github/hooks/tests/test_fr961_claude_runtime.py`; `tests/conftest.py` shim per R-5(a) |
| D-9 | `.github/hooks/README.md` coverage statement; one line in `CLAUDE.md` |
| D-10 | FR evidence appendix (R-2), Implementation Status, one `feat`/`hooks` changelog fragment, one diary reflection |

**Not authorized:** any new rule, registry phrase, deny-message or `reasoning-patterns.json` change; the PostToolUse `decision: "block"` path (option E); a `Stop` or `UserPromptSubmit` scan (option H); deleting the reasoning check on either runtime (option I); activating the FR-425 daemon or extracting guard logic into a graph node (option D); a second script tree under `.claude/` (option B); `PermissionRequest` registration of any kind; changing the sentinel filename or schema, or the `.reasoning-flag-<sid>` one-shot semantics; editing `.github/copilot-instructions.md` (R-9); editing the Copilot `.github/hooks/*.json` registrations; changing `session-timeline.py` or `session-probe.sh` beyond the two functions named in D-6; auto-approving any Claude Code tool call; `.claude/settings.local.json` or `~/.claude/settings.json` as the shipped route unless the human selects it under Q-1; touching `~/.claude/` outside a read of transcript files.

## Revised acceptance criteria

- [ ] AC-01 (RED first): `.github/hooks/tests/test_fr961_claude_runtime.py` feeds Claude Code-shaped stdin (`Bash` with `command`; `Write`/`Edit`/`MultiEdit`/`NotebookEdit` with `file_path`, `old_string`/`new_string`, `edits[]`, `notebook_path`) into `pre-command-guard.sh`, `python-checks.sh`, `yaml-checks.sh`, `markdown-checks.sh` and `main_write.py`, and asserts the same decisions the Copilot fixtures get for the same intents: trailer deny, `--no-verify` deny, multiline `-m` deny, governed-artifact write deny without an armed sentinel, main-checkout edit deny, ruff finding reported. Fails before implementation. Invocation path per R-5.
- [ ] AC-02: `.claude/settings.json` committed with the §1 registration minus `classify-emit.sh`; a fixture session on the Windows host produces an `audit.jsonl` row for a `Bash` PreToolUse carrying `"runtime": "claude-code"` — the first hook firing on this host.
- [ ] AC-03 (**new, R-1**): in a live Claude Code session with the guard registered, a permission-requiring `Bash` call still raises the normal operator permission prompt; the guard's stdout on that call is `{}`. Session id recorded in Implementation Status. If this fails, the FR returns to plan.
- [ ] AC-04: `grep -rn 'run_in_terminal\|send_to_terminal\|create_file\|replace_string_in_file\|multi_replace_string_in_file\|apply_patch\|\bBash\b\|\bMultiEdit\b\|\bNotebookEdit\b' .github/hooks/scripts` returns hits only in `checks/hook_input.py` and comment lines (was AC-03; R-6).
- [ ] AC-05: all existing `.github/hooks/tests/` pass, with fixture payloads and assertions unedited; the only test-harness change permitted is the `conftest.run_hook` shim of R-5(a), and the FR names the platform each suite was run on.
- [ ] AC-06: `reasoning-pattern-check.sh` prefers stdin `transcript_path` and falls back to the `workspaceStorage` glob only when the field is absent; a Claude Code-shaped fixture with the FR-883 phrase `safety envelope` in a `text` block arms `.reasoning-flag-<sid>`; the same phrase under a non-latest `requestId` does not; an empty-`thinking` + clean-`text` turn logs `skip/no-scannable-text` or `armed` with `source=text`, never a parse error; the existing UUID guard at `reasoning-pattern-check.sh:31` still rejects a non-UUID `session_id` before any file access.
- [ ] AC-07: the Copilot transcript fallback still works — `test_reasoning_pattern_check.py` fixtures untouched and green.
- [ ] AC-08: `session-timeline.py` resolves a Claude Code transcript via `transcript_path` and prints the `runtime` column; existing `test_session_timeline.py` green.
- [ ] AC-09: `.github/hooks/README.md` § Active Hooks states Claude Code coverage as "latest turn's persisted thinking summaries and visible text", and nowhere claims private-reasoning coverage for that runtime (FR-883 R-1 / AC-07 precedent). The README title and § How It Works are updated to describe a two-runtime layer.
- [ ] AC-10: `resolve_python()` witnessed on the Windows host — with the venv present, a Claude Code `Bash` tool call carrying a `Co-authored-by` trailer is **refused by the runtime** with the guard's reason text visible to the operator (audit row + session id recorded); with `HOOK_PYTHON=/nonexistent` the hook exits 0 leaving exactly one `skip/no-interpreter` audit row and no denial; hook wall time < 5 s in both (R-8).
- [ ] AC-11 (**new, R-3**): `grep -rn 'python3\|\.venv/bin/python' .github/hooks/scripts` returns hits only in `lib/resolve_python.sh`, in `#!` shebang lines, and in comments/docstrings.
- [ ] AC-12 (**new, R-4**): an unrecognised `tool_name` whose payload carries a governed path in any of `filePath`, `file_path`, `replacements[]`, `edits[]` or `notebook_path` is denied, and the audit row records `"runtime": "unknown"`.
- [ ] AC-13 (**new, R-2**): the FR carries an evidence appendix with the counting command, four verbatim `thinking` texts, one elided-`signature` empty block, the four session ids, and the capture date.
- [ ] AC-14: `docs(fr)` hygiene — Implementation Status records the re-measured thinking-persistence numbers at ship time (via AC-13's command), the fixture session ids from AC-02/AC-03/AC-10, and the platform each test suite ran on; one changelog fragment (`feat`, scope `hooks`); one diary reflection on the "one layer, two runtimes" trap.
- [ ] AC-15: human review before merge (FR-883 R-4) recorded in the PR body; no rule text, registry phrase or deny message changed; `.github/copilot-instructions.md` unmodified (R-9).
- [ ] AC-16: `CLAUDE.md` gains one line pointing at `.github/hooks/README.md` for the hook layer; doctrine stays in `.github/copilot-instructions.md` only.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority inactive until R-1 through R-9 are folded into the FR. | GATE |
| C-2 | AC-01 written and failing before any script is edited; `lib/resolve_python.sh` (D-3) lands and AC-11 passes before `.claude/settings.json` (D-1) is committed — a registration that reaches a stub interpreter is the defect this FR names. | GATE |
| C-3 | No Claude Code tool call may be auto-approved by this layer. If AC-03 shows `{"decision":"approve"}` is honoured, stop and return to plan. | GATE |
| C-4 | Enforcement infrastructure: a human reviews the final diff before merge, and specifically the `.claude/settings.json` contents and the guard's allow-path output. | GATE |
| C-5 | Fail closed on unparseable or unknown-runtime edits to governed paths (FR-767 C-5); fail open with exactly one audit row only for the missing-interpreter case. | GATE |
| C-6 | Deterministic and stdlib-only inside declared timeouts; no LLM invoked in any hook process, and no hook forwarding session content to an LLM daemon. | GATE |
| C-7 | `.github/hooks/logs/` remains the single audit sink for both runtimes; no script may compute a second `LOG_DIR` (R-3 defect 2). | GATE |
| C-8 | Scope is the table above. Adjacent work seen while judging — the `examples/demos/research-route` reducer sanitisation gap noted in the research record, and option H's `Stop`-event scan — is parked for separate FRs, not folded here. | GATE |

**Questions reserved for the human** (not absorbed into this judgement; C-1 is not satisfied until they are answered in the FR):

- **Q-1 — registration scope.** The FR's own question, correctly raised: committed `.claude/settings.json` (project-wide, its recommendation) vs `.claude/settings.local.json` (per-operator, gitignored) vs `~/.claude/settings.json` (host only). I agree the project-scoped file is the parity-preserving choice and note `.gitignore` has no `.claude` entry, so committing it works as written — but this decides whether every future clone of this repo silently executes these hooks, which is the operator's call, not mine.
- **Q-2 — option H timing.** Defer the `Stop`-event scan (the FR's recommendation, and mine: no witnessed incident) vs include it now. Deferred under C-8 unless the human overrides.
- **Q-3 — classify-emit / FR-425 daemon.** R-7 drops it from the registration. If the operator wants Claude Code tool events forwarded to the classifier daemon, that is an explicit spend-and-data decision to record in the FR, and it needs its own AC.

**Authority granted** (on C-1): implement D-1 through D-10 exactly as frozen above — one shared script tree, one new stdin vocabulary adapter, one POSIX interpreter resolver, a `transcript_path`-first reasoning scan with a Claude Code parser, a `runtime` field in the audit trail, and a second thin registration — with no rule, registry, or deny-message change on either runtime, and with the allow path proven not to auto-approve before the registration is trusted.

---

*Advisory draft. Rendered by the Claude judge variant (FR-960) under `.github/skills/judge-fr/doctrine.md`. Not binding until human-reviewed and folded to `feature-requests/FR-961-claude-code-hooks-registration.judgement.md`.*
