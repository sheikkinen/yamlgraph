# Judgement: FR-961 Register the hook enforcement layer for Claude Code

**Verdict:** APPROVED WITH REVISIONS — the defect is real (one enforcement layer, two runtimes, one of them unguarded), the chosen shape is the minimal one and the FR-890 research gate is genuinely satisfied; authority activates only after R-1..R-11 are folded into the FR, and the human decisions in § Questions are recorded there.

**Reviewed against:** `feature-requests/FR-961-claude-code-hooks-registration.md`; `feature-requests/FR-961.research.md`; `feature-requests/research-briefs/fr961-claude-code-hooks-port-brief.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md` (§ Conventions, § Copilot Hooks, traps registry, Scripture process); `feature-requests/FR-883-block-concealed-refusal-task-alteration.judgement.md`; and the committed enforcement surface it proposes to change — `.github/hooks/README.md`, `.github/hooks/pre-command-guard.json`, `post-edit-checks.json`, `reasoning-pattern-check.json`, `classify-emit.json`, `session-probe.json`, `.github/hooks/logs/.gitignore`, `.github/hooks/scripts/pre-command-guard.sh`, `reasoning-pattern-check.sh`, `reasoning-patterns.json`, `session-briefing.sh`, `session-timeline.py`, `checks/common.sh`, `checks/main_write.py`, `.github/hooks/tests/` (incl. `test_copilot_instructions_hooks_docs_red.py`), and the absence of any `.claude/` directory in this repo.

No chat transcript, planning narrative, or uncommitted note was consumed. Two vendor-behaviour claims (Claude Code's settings/matcher schema; Git Bash as the Windows shell for `command` hooks) lie outside the input closure and are therefore treated as unverified assertions requiring a host witness, not as established fact — see R-1 and C-6.

## What is sound

**The problem is witnessed, not inferred.** `.github/hooks/logs/` contains only `memory-curation-audit.jsonl`; there is no `audit.jsonl` and no `.claude/` directory anywhere in the tree. Every claim the FR makes about the current code holds on inspection: `checks/common.sh:12` allowlists four Copilot edit-tool names; `pre-command-guard.sh:91,114,282,310` gate on `run_in_terminal`/`send_to_terminal`; `pre-command-guard.sh:240-241` and `checks/main_write.py:47-50` repeat the edit-tool set a third and fourth time; `reasoning-pattern-check.sh:36-50` and `session-timeline.py:52-73` hardcode the macOS `workspaceStorage` glob although `transcript_path` is already documented in `README.md:57` as an input field. A Claude Code `Bash` call today is genuinely "not a terminal tool" and falls through every check.

**The chosen solution is the minimal one and is architecturally aligned.** One script tree, one parser, two registrations, with `tool_class` replacing four literal name lists. Option B (a second script tree) is rejected as the defect reproduced by design; option D (graph/daemon in the hot path) is rejected with a real cost argument (graph runtime start inside a 5 s per-tool budget, 31+ shell contract tests moved to a new surface). `is_this_a_graph` is answered — **no** — unanimously in the research record, with the yamlgraph-native planner's dissent correctly localised to the adapter's *body*, not the boundary.

**The FR-890 research gate is met on substance, not shape.** `FR-961.research.md` carries four genuine solution classes with distinct mechanisms, per-class precedent lines (in-repo and external), a preserved disagreement (the subtractionist's delete-the-check position, carried forward as a *binding constraint* on the README claim rather than silently dropped), provenance hashes, and two self-reported artifact defects (CRLF hash mismatch, leaked persona markup) disclosed rather than laundered. This is not `gate_checks_shape_not_substance`.

**The overclaim is pre-empted where FR-883 R-1 demanded it.** The coverage limit ("visible assistant text and the short visible thinking summaries the transcript persists, not private reasoning") is stated in the first-consumer line at FR-961:11-13 — in the header, not a footnote — and option G is explicitly rejected. The FR also refuses to absorb the sentinel-vs-`decision: block` question, keeping one denial mechanism (option E deferred).

**Prior art is dispositioned per the FR-737 precedent rule.** The five filename-noun retrievals are named and dismissed as vocabulary collisions in the research record; FR-438/439/883/414/440/662/767/743/877/424/425/163/951/953 are each given a role; the same-day FR-958/959/960 cluster is separated by boundary (node backend inside a graph vs operator runtime driving the repo) with the renumbering recorded. No REJECTED FR governs the topic.

**Strategic classification:** enforcement-infrastructure registration + adapter — an extension of an existing primitive, not a new one. Correctly *not* a framework primitive (it adds no `yamlgraph/` surface) and correctly not pattern documentation (documentation is the status quo the FR names as the defect, option F).

## Required revisions

### R-1: Witness that a real Claude Code tool call is actually *blocked*, not that a script printed deny JSON

The FR's entire value rests on a claim it never tests end-to-end: that Claude Code honours `hookSpecificOutput.permissionDecision: "deny"` emitted by `pre-command-guard.sh:39-50` and exiting 0. AC-02 witnesses only an audit *line*; AC-09 says "the guard denies a trailer commit", which is satisfiable by piping fixture stdin into the script. If the deny shape or the exit contract is not honoured on this runtime, every hook in this FR becomes a logger and the FR ships zero enforcement while claiming parity.

Replace AC-02 and AC-09's deny clause with a live-session witness: inside a real Claude Code session on the Windows host, attempt (a) a `Bash` call carrying a `Co-authored-by` trailer and (b) a `Write` to a governed graph artifact without the FR-767 sentinel. Record in § Implementation Status, verbatim: the assistant-visible denial text as it appeared, the resolved hook command string, the session id, and the corresponding `audit.jsonl` rows. If Claude Code does not honour the shape, that is a finding to record and the FR returns to plan — it is not a defect to work around silently.

### R-2: Commit the witness evidence; `.github/hooks/logs/*.jsonl` is gitignored

`.github/hooks/logs/.gitignore` excludes `*.jsonl`, `.lockdown`, and `.reasoning-flag-*`. Every AC that says "produces an `audit.jsonl` line" (AC-02) or "leaves exactly one `skip/no-interpreter` audit line" (AC-09) is therefore unverifiable by any reviewer of the PR. State in the FR that each such witness is reproduced **verbatim (one JSON object per line, secrets redacted) in § Implementation Status of this FR**, which is the committed evidence, and that the log file itself is not the deliverable.

### R-3: Cite raw transcript samples, not only aggregates (`read_raw_output_first`, local judge law)

The FR's central re-scoping decision — that FR-438's premise fails on this runtime and the README claim must shrink (option G, AC-08) — rests on "228 thinking blocks, 57 with non-empty text (25 %), longest 534 characters; every non-empty sample reads as a one-sentence progress summary". Those are aggregates and a characterisation. The Scripture's `read_raw_output_first` / `what_does_the_raw_record_say` requires the raw record before the verdict.

Fold into the FR (or a committed `feature-requests/FR-961.evidence.md`): at least **three verbatim non-empty `thinking` blocks** and **two verbatim `text` blocks** from `~/.claude/projects/C--src-yamlgraph/*.jsonl`, each with session id, `requestId`, byte length, and any surprising detail; plus the empty-`thinking`-with-`signature` shape quoted once. Redact paths/secrets, keep the prose intact.

### R-4: Measure registry-phrase hit rate on visible text before scanning it

FR-883 judgement R-3 bound that FR to "binding negative tests for ordinary direct visible refusal and benign policy discussion". FR-961 moves the scan's primary surface from private reasoning to **visible assistant prose**, where the current registry (`reasoning-patterns.json`) contains phrases that occur in ordinary honest narration and in any session that discusses enforcement itself: `pre-existing failure`, `was already broken`, `safer alternative`, `safety envelope`. A session implementing this very FR, or editing `reasoning-patterns.json`, `README.md`, or FR-883, will emit those strings in visible text and arm the sentinel — a self-inflicted denial loop that the Copilot deployment never had.

Required, all three:

1. Report, in § Implementation Status, per-phrase hit counts for all 5 patterns and their variants across the four already-measured sessions, split by block type (`thinking` vs `text`), with each hit's surrounding sentence quoted.
2. Ship `text`-block scanning **disabled by default** (`HOOK_SCAN_VISIBLE_TEXT`, default `0`, thinking-only) unless that measurement shows **zero** benign hits in `text`. State the chosen default and the number that justifies it.
3. Add a negative-test AC (see AC-14 below): benign discussion or quotation of a registry phrase in visible text must not arm the sentinel under the shipped default, and the test asserts the shipped default explicitly.

This does not add or remove a rule (Constraint 1 holds); it fixes the false-positive profile of an unchanged rule on a new surface.

### R-5: Complete the refactor site list and fix AC-03's grep

The FR's § Problem item 2 cites `pre-command-guard.sh:91,114,240-241,282,310` but the file also gates on Copilot tool names at **`:148`** and **`:280`** (`create_file|replace_string_in_file|multi_replace_string_in_file|apply_patch|run_in_terminal|send_to_terminal)` case arms), and `checks/common.sh:50` special-cases `apply_patch` inside the path extractor. List all of them; every one moves to `tool_class`.

AC-03's command `grep -n 'run_in_terminal\|create_file' .github/hooks/scripts` is not runnable as written — no `-r`, and the argument is a directory. Replace with `grep -rn` and pin the expected result (hits only inside `checks/hook_input.py` and comments).

### R-6: The `.claude/settings.json` matcher is a second place tool names are interpreted — pin it

§ 1 registers the post-edit checks behind `"matcher": "Write|Edit|MultiEdit|NotebookEdit"`. That regex is a literal Claude Code tool-name list living outside `hook_input.py`, which directly contradicts AC-03's objective, and it will silently rot the day a runtime tool is renamed or added. AC-03's grep does not search `.claude/settings.json`, so nothing catches it.

Fold: keep the matcher (the empty-matcher alternative costs four extra process starts on every tool call, which the 5 s Windows budget cannot afford), and add a test asserting the matcher's alternation set is **exactly** the Claude Code edit-tool names in `hook_input.py`'s map, so the two cannot drift. Extend AC-03's grep to cover `.claude/settings.json` and `.github/hooks/*.json`.

### R-7: Decide the doctrine surface — the Scripture section is titled "Copilot Hooks" and its header is machine-pinned

`.github/copilot-instructions.md:30` reads `### Copilot Hooks (.github/hooks/)`, and `.github/hooks/tests/test_copilot_instructions_hooks_docs_red.py:11` asserts that exact string, with a ≤15 non-empty-line cap (`test_ac03_hooks_subsection_is_concise`). `.github/hooks/README.md:1-3` likewise declares the layer to be "for VS Code Copilot agent sessions". Shipping a second runtime while both documents say the layer is Copilot-only leaves the doctrine describing a false surface, and AC-12 (a CLAUDE.md pointer) does not touch either.

Fold as an explicit deliverable: rename the section to `### Agent Hooks (.github/hooks/)`, update `SECTION_HEADER` in `test_copilot_instructions_hooks_docs_red.py` in the same commit, keep the body ≤15 non-empty lines and all nine required tokens, and add one line naming `.claude/settings.json` as the Claude Code registration. Update `README.md`'s title and opening sentence to "agent sessions (VS Code Copilot, Claude Code)". This is a scope/label correction, not a rule change — AC-11's "no rule text change" survives it, and the FR must say so.

### R-8: `resolve_python()` must be reachable from every caller, including a `#!/bin/sh` script

§ 5 says `session-briefing.sh` "calls it instead of their private literals", but `session-briefing.sh:1` is `#!/bin/sh` (not bash), does not source `common.sh`, and invokes `memory-advisory.sh` via `sh` at line 16. A bash-only function in `common.sh` is not callable from either.

Specify the mechanism: `resolve_python()` is POSIX-sh compatible and lives in a sourceable file both `sh` and `bash` callers can `.`-source, and enumerate every call site to be converted — `session-briefing.sh:7-8`, `memory-advisory.sh`, `reasoning-pattern-check.sh:21,37,58`, `pre-command-guard.sh:23,54,105,106,129` and any other `python3` literal, and `common.sh:33-35,42,76,108`. Note the FR must not touch `.pre-commit-config.yaml`'s `.venv/bin/python` references (out of scope, R-11 park).

### R-9: State what happens when a hook exceeds its timeout

The FR declares timeouts (5 s guard, 10 s checks) but never says what the runtime does when the PreToolUse guard exceeds 5 s on this host, where every parse forks a Windows Python process under Git Bash. If timeout means the tool proceeds, the guard fails **open** — which contradicts § Constraints ("fail closed on unparseable edits to governed paths") and the README's "Fail-closed" contract (README:216-218) precisely in the slowest, most loaded sessions.

Fold: state the observed timeout behaviour (witnessed, per R-1's live session), and replace AC-09's single "< 5 s" sample with a distribution — max and p95 guard wall time over the fixture session's tool calls, recorded in § Implementation Status. If timeout is fail-open, say so plainly in README as a known limit of this runtime.

### R-10: Specify `runtime: unknown` semantics as a table, not a clause

§ 2 says `unknown` "never approves an edit — fail closed, FR-767 C-5", which is under-specified for the guard's actual decision space (`pass`/`approve`/`deny`/`error`). Give the full matrix: for each `(runtime ∈ {copilot, claude-code, unknown}) × (tool_class ∈ {terminal, edit, read/other})`, the decision when the target is a governed path and when it is not. An unrecognised tool name carrying a governed `file_path` must deny; an unrecognised tool name with no path must log `pass/not-inspected`, not deny, or every future vendor tool addition halts the session.

### R-11: Fix the false premise in Question 2 and park the adjacent findings

§ Questions item 2 asserts "Evidence arrives with AC-05's measurement of how often the FR-883 phrases appear in `text` at all" — AC-05 is a fixture test and measures nothing about the real corpus. Restate: the measurement is R-4 item 1; Question 2 is answered from it, not from AC-05.

Park explicitly as out of scope, each with a named follow-on: (a) the `.pre-commit-config.yaml` `.venv/bin/python` references; (b) the research-route reducer sanitisation gap that leaked `</anionale> </invoke>` into `FR-961.research.md`; (c) the CRLF/LF `--verify-promotion` mismatch (FR-951 class, already parked with FR-955); (d) option H's `Stop`/`UserPromptSubmit` scan.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.claude/settings.json` — new, project scope, exactly the events in § 1 (PreToolUse guard on `""`; PostToolUse edit checks on the pinned matcher; PostToolUse reasoning + classify on `""`; SessionStart briefing). Scope decision per Q-1 |
| D-2 | `.github/hooks/scripts/checks/hook_input.py` — new, stdlib only, sole interpreter of tool names; returns `(runtime, tool_class, command, paths, session_id, tool_use_id, cwd, transcript_path)`; normalises `\` → `/` |
| D-3 | `pre-command-guard.sh` (`:91,114,148,240-241,280,282,310`), `checks/common.sh` (`:12,50`), `checks/main_write.py` (`:46-51`) — switch literal name lists to `tool_class` |
| D-4 | `reasoning-pattern-check.sh` — stdin `transcript_path` first, macOS glob as fallback; second parser for the Claude Code shape; `source` field records `thinking` / `text` / `thinking+text`; `HOOK_SCAN_VISIBLE_TEXT` default per R-4 |
| D-5 | `session-timeline.py:52-73` — same transcript precedence; `runtime` column |
| D-6 | `audit.jsonl` — one new key `runtime`; no other format change |
| D-7 | `resolve_python()` (POSIX sh) + conversion of the `python3` / `.venv/bin/python` literals listed in R-8 |
| D-8 | `.github/hooks/tests/test_fr961_claude_runtime.py` + Claude-shaped fixtures; matcher-parity test (R-6); negative-scan test (R-4.3); `test_copilot_instructions_hooks_docs_red.py` header constant (R-7) |
| D-9 | Docs: `.github/hooks/README.md`, `.github/copilot-instructions.md` § hooks (R-7), one `CLAUDE.md` pointer line, one `changelog/unreleased/` fragment (`feat`, scope `hooks`), one `docs/diary/` reflection |

**Not authorized by this FR:**

- Any new rule, registry phrase, variant, doctrine text, or deny-message wording change.
- Registering `session-probe.sh` for Claude Code, or any Claude Code event beyond `PreToolUse` / `PostToolUse` / `SessionStart` — no `Stop`, `UserPromptSubmit`, `PreCompact`, `SubagentStop`, `PermissionRequest`, `Notification` (option H stays deferred).
- Claude Code's PostToolUse `decision: "block"` feedback path (option E).
- Any change to the sentinel: format, `.reasoning-flag-<sid>` name, one-shot semantics, session-UUID regex.
- Deleting or disabling the reasoning-pattern check on Copilot (option I as deletion); Copilot's `reasoningText` path and its fixtures are untouched.
- Activating, starting, or modifying the FR-425 classifier daemon; any LLM call in any hook process.
- A second script tree, a second copy of any guard, or any `.github/hooks/*.json` change beyond none.
- Emitting `{"decision":"approve"}` semantics or any auto-approve on Claude Code — the allow path stays the runtime's normal permission flow.
- Broader Windows portability work: `.pre-commit-config.yaml`, `scripts/`, CI, or the research route's CRLF handling.
- Any change to `yamlgraph/` framework code — this FR adds no framework surface.

## Revised acceptance criteria

- [ ] **AC-01 (RED first):** `.github/hooks/tests/test_fr961_claude_runtime.py` drives a **shared intent table** (one row per enforced intent: trailer commit, `--no-verify`, multiline `-m`, pytest pipe without `tee`, main-worktree branch creation, governed-path write without sentinel, ruff finding, oversize file) through both vocabularies — Copilot-shaped and Claude-shaped stdin (`Bash`+`command`; `Write`/`Edit`/`MultiEdit`/`NotebookEdit` with `file_path`, `old_string`/`new_string`, `edits[]`, `notebook_path`) — into `pre-command-guard.sh`, `python-checks.sh`, `yaml-checks.sh`, `markdown-checks.sh`, `main_write.py`, and asserts identical `(decision, reason)` for both. Fails today.
- [ ] **AC-02:** `.claude/settings.json` committed with the § 1 registration (scope per Q-1). In a **live** Claude Code session on the Windows host, a `Bash` tool call produces an `audit.jsonl` row with `"runtime": "claude-code"` — the first hook firing on this host — and the row is quoted verbatim in § Implementation Status with its session id.
- [ ] **AC-03 (live deny witness, R-1):** In the same live session, (a) a `Bash` call carrying a `Co-authored-by` trailer and (b) an unsentineled `Write` to a governed graph artifact are **refused by the runtime**. § Implementation Status records, verbatim: the denial text as the assistant saw it, the resolved hook command string, and the two `audit.jsonl` deny rows. If the runtime does not honour the deny shape, the FR records the finding and returns to plan.
- [ ] **AC-04:** `hook_input.py` is the only place tool names are interpreted: `grep -rn 'run_in_terminal\|send_to_terminal\|create_file\|replace_string_in_file\|multi_replace_string_in_file\|apply_patch\|"Bash"\|"Write"\|MultiEdit' .github/hooks/scripts .claude/settings.json .github/hooks/*.json` returns hits only inside `checks/hook_input.py`, inside comments, and inside the `.claude/settings.json` matcher pinned by AC-05.
- [ ] **AC-05:** A test asserts the `.claude/settings.json` PostToolUse matcher's alternation set equals exactly `hook_input.py`'s Claude Code edit-tool set (drift-proof, R-6).
- [ ] **AC-06:** All existing `.github/hooks/tests/` pass with **no fixture edits** — the Copilot vocabulary is a subset of the map — with the sole exception of `test_copilot_instructions_hooks_docs_red.py:11`'s `SECTION_HEADER` constant, changed in the same commit as the doctrine heading (R-7).
- [ ] **AC-07:** `reasoning-pattern-check.sh` prefers stdin `transcript_path` and falls back to the macOS glob only when absent. A Claude Code-shaped transcript fixture with a registry phrase in a scanned block arms `.reasoning-flag-<sid>`; the same phrase in a **non-latest** `requestId` does not; an empty-`thinking` + clean-`text` turn logs `skip/no-scannable-text` or `armed` with the correct `source`, never a parse error; a malformed line is skipped, not fatal.
- [ ] **AC-08 (negative scan, R-4.3):** Under the shipped default, benign quotation or discussion of a registry phrase in a `text` block — e.g. an assistant turn editing `reasoning-patterns.json` or narrating this FR — does **not** arm the sentinel. The test asserts the shipped `HOOK_SCAN_VISIBLE_TEXT` default explicitly, so flipping it fails the test.
- [ ] **AC-09:** The Copilot transcript fallback still works: `test_reasoning_pattern_check.py` fixtures untouched and green.
- [ ] **AC-10:** `session-timeline.py` resolves a Claude Code transcript via `transcript_path` and prints the `runtime` column; existing `test_session_timeline.py` stays green.
- [ ] **AC-11 (interpreter, R-8/R-9):** `resolve_python()` is POSIX-sh sourceable and used by every call site listed in R-8. Witnessed on the Windows host: with the venv present the live deny of AC-03 fires; with `HOOK_PYTHON=/nonexistent` the guard exits 0 leaving exactly one `{"decision":"skip","reason":"no-interpreter"}` row (quoted in § Implementation Status) and does not block the session. Guard wall time is reported as **max and p95** across the AC-02 session's tool calls, with the declared timeout's failure mode stated.
- [ ] **AC-12 (evidence, R-3/R-4.1):** § Implementation Status (or `FR-961.evidence.md`) carries ≥3 verbatim non-empty `thinking` blocks, ≥2 verbatim `text` blocks, one empty-`thinking`+`signature` sample, and per-phrase registry hit counts over the four measured sessions split by block type, with each hit's sentence quoted. The chosen `HOOK_SCAN_VISIBLE_TEXT` default cites that number.
- [ ] **AC-13:** `.github/hooks/README.md` and `.github/copilot-instructions.md` § hooks describe the layer as serving both runtimes, name `.claude/settings.json`, and state Claude Code coverage as "the latest turn's persisted thinking summaries and visible text" — nowhere claiming private-reasoning coverage for that runtime (FR-883 AC-07 precedent). The Scripture body stays ≤15 non-empty lines with all nine tokens plus the new registration path.
- [ ] **AC-14:** `runtime: unknown` matrix (R-10) is documented in `README.md` and covered by tests: unknown tool name + governed path → deny; unknown tool name, no path → `pass/not-inspected`.
- [ ] **AC-15:** `CLAUDE.md` gains one line pointing at `.github/hooks/README.md` for the hook layer; doctrine stays in `copilot-instructions.md` only.
- [ ] **AC-16 (hygiene):** One changelog fragment (`feat`, scope `hooks`); one diary reflection (the "one layer, two runtimes" trap); § Implementation Status records the fixture session id, the measured numbers at ship time, and every deviation from this judgement.
- [ ] **AC-17 (gate):** Human review of the full diff before merge (FR-883 R-4), recorded in the PR body, together with the Q-1..Q-3 answers as folded into the FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1..R-11 are folded into the FR and Q-1..Q-3 are answered in it by a human. | GATE |
| C-2 | Human review of the diff before merge — this is enforcement infrastructure (FR-883 R-4); no self-merge. | GATE |
| C-3 | RED first: the AC-01 parity suite and the AC-08 negative test are committed failing before any script changes. | GATE |
| C-4 | No rule, phrase, variant, doctrine sentence, deny-message wording, or sentinel format/name/semantics change. Doc heading/scope corrections (R-7) are permitted and are not rule changes. | GATE |
| C-5 | Every existing `.github/hooks/tests/` fixture stays byte-unchanged; the only permitted test-source edit is the `SECTION_HEADER` constant (R-7). Any other required fixture edit means the mapping is not a superset — stop and re-judge. | GATE |
| C-6 | Vendor-behaviour claims (deny-shape honoured, Git Bash shell, `$CLAUDE_PROJECT_DIR` interpolation, settings merge, matcher regex, timeout semantics) are unproven until witnessed on the host per AC-02/AC-03/AC-11. A claim that survives only as documentation citation may not be asserted as fact in README or the FR. | GATE |
| C-7 | Fail-closed on unparseable writes to governed paths (FR-767 C-5) survives the refactor for both runtimes; the only permitted fail-open is the missing-interpreter case, and it must leave its audit row. | GATE |
| C-8 | No LLM, network call, or daemon dependency in any hook process; stdlib only; `.github/hooks/logs/` remains the single sink. | GATE |
| C-9 | Scope stays inside the D-1..D-9 table. Anything on the "not authorized" list — option E, option H, FR-425 activation, further Windows portability, `.pre-commit-config.yaml` — is a separate FR. | GATE |
| C-10 | Visible-text scanning ships disabled unless R-4's measurement shows zero benign hits; the number and the default are recorded in the FR. | GATE |

### Questions for the human (must be answered in the FR before authority activates)

- **Q-1 — Registration scope.** Committing `.claude/settings.json` means every clone that opens this repo in Claude Code executes local shell scripts from the working tree. That is a security-relevant decision belonging to a human, not to the judge or the author. Options: (a) commit at project scope (the FR's recommendation — parity is the point, and per-operator opt-in recreates the silent-runtime gap on the next clone); (b) `.claude/settings.local.json`, gitignored, documented in README; (c) user-level `~/.claude/settings.json`, no repo record. Whichever is chosen, the FR must also record — witnessed, not assumed — what a *fresh clone* does on first session: silent activation or an approval prompt.
- **Q-2 — Visible-text scanning default.** Answered by R-4's measurement, but the disposition is the human's: ship `text` scanning on (accepting the false-positive profile documented in R-4) or off pending evidence.
- **Q-3 — Option H timing.** Confirm the deferral of the `Stop`/`UserPromptSubmit` scan (recommended: no witnessed incident), or file it as its own FR.

**Authority granted:** on fold of R-1..R-11 and human answers to Q-1..Q-3, the enforcer may build exactly D-1..D-9 — one committed Claude Code registration, one stdlib tool-vocabulary/transcript adapter, the `tool_class` conversion of the four existing name lists, the `transcript_path` precedence fix and Claude transcript parser, the `runtime` audit key, POSIX-sh interpreter resolution, the parity/negative/matcher tests, and the documentation corrections — and nothing else; merge requires the human review gate of C-2.

---

*Advisory draft — Claude judge variant (FR-960). Not authoritative until human-reviewed and folded.*
