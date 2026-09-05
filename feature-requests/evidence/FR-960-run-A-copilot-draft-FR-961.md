# Judgement: FR-961 Register the hook enforcement layer for Claude Code

**Verdict:** APPROVED WITH REVISIONS - the shared-script, thin-registration direction is sound and cohesive, but authority activates only after runtime provenance, interpreter failure semantics, transcript selection, evidence closure, and the two human decisions are made mechanically unambiguous.

**Reviewed against:** `feature-requests/FR-961-claude-code-hooks-registration.md`; `feature-requests/FR-961.research.md`; `feature-requests/research-briefs/fr961-claude-code-hooks-port-brief.md`; `feature-requests/research-runs.jsonl`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `feature-requests/TEMPLATE.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `docs/development-process.md`; `.github/hooks/README.md`; `.github/hooks/pre-command-guard.json`; `.github/hooks/post-edit-checks.json`; `.github/hooks/reasoning-pattern-check.json`; `.github/hooks/classify-emit.json`; `.github/hooks/session-probe.json`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/scripts/reasoning-pattern-check.sh`; `.github/hooks/scripts/classify-emit.sh`; `.github/hooks/scripts/checks/common.sh`; `.github/hooks/scripts/checks/main_write.py`; `.github/hooks/scripts/session-timeline.py`; cited prior-art records `FR-163`, `FR-414`, `FR-424-session-timeline`, `FR-425`, `FR-438`, `FR-439`, `FR-440`, `FR-662`, `FR-743`, `FR-767` and its judgement, `FR-877` and its judgement, `FR-883` and its judgement, `FR-951`, `FR-953`, `FR-958`, `FR-959`, and `FR-960`, limited to committed repository content. The uncommitted host transcripts under `~/.claude/projects/` were not consumed under input closure.

## What is sound

The problem is concrete and the first consumer is named. The repository has no Claude Code project registration, while the active guards classify Copilot tool names literally (`FR-961:8-13,59-85`; `pre-command-guard.sh:91,114,148,240-241,280-310`; `checks/common.sh:10-13`; `checks/main_write.py:47-50`). The proposed boundary normalization therefore addresses an observable enforcement gap rather than adding speculative policy.

The architecture follows the repository's one-law boundary rule. One canonical input parser and two thin registrations are smaller and safer than a copied Claude-specific script tree (`FR-961:41-48,167-183,229-243`). The alternatives record contains four genuine solution classes, preserves the subtractionist disagreement, dispositions the graph-shaped daemon, and answers `is_this_a_graph` in the negative (`FR-961.research.md:53-73,86-94`). That is substantive research, not a shape-only table.

The work is one responsibility: make the existing enforcement layer runtime-neutral. Registration, vocabulary normalization, transcript-path normalization, runtime-labelled audit, and interpreter resolution are coupled prerequisites for that same boundary; splitting them would knowingly land a registered but silently ineffective guard. No new rule, registry phrase, deny message, graph, or LLM hot path is required (`FR-961:296-305`).

The plan is feasible with the current surfaces. Hook commands already receive JSON on stdin and the documented Copilot contract already includes `transcript_path` (`.github/hooks/README.md:45-67`). The current scanner and timeline hardcode macOS discovery (`reasoning-pattern-check.sh:36-50`; `session-timeline.py:52-73`), and the current hook scripts contain the exact duplicated Python and tool-name parsing the proposed adapter would remove.

Strategic classification: **contrib/repo-operations integration**, not a YAMLGraph framework primitive. It serves two runtime registrations and closes gaps in an existing repository-local hook abstraction; it does not establish a three-use-case framework API.

The acceptance plan is unusually close to executable: it names concrete files, fixture shapes, denial intents, fallback behavior, documentation, host witnessing, and the mandatory human-review gate (`FR-961:249-294`). The revisions below tighten ambiguous outcomes rather than replacing the design.

## Required revisions

### R-1: Record the two human decisions and remove the unresolved scope contradiction

The Proposed Solution selects committed project registration and defers `Stop` / `UserPromptSubmit` scanning (`FR-961:118-163,200-204,239`), but the FR ends by asking the human to choose those decisions again (`FR-961:318-331`). Fold the human's selections into the FR before enforcement.

For registration scope, record one of: (a) committed `.claude/settings.json` (**recommended**, because clone-level parity is the stated value), (b) gitignored local registration, or (c) user-level registration. Options (b) or (c) change the stated first consumer and parity objective and require re-judgement. For event scope, record either defer (**recommended**, because no incident witnesses the extra event) or include; inclusion is not authorized here and requires a separate FR. Remove the resolved questions from the enforcement plan and make the selected answers consistent across Summary, Proposed Solution, deliverables, and acceptance criteria.

### R-2: Derive runtime from registration provenance, not recognized tool vocabulary

The FR promises a correct `runtime` on every audit entry (`FR-961:105-110,206-210`) but derives it from known tool names or `permission_mode`, defaulting everything else to Copilot (`FR-961:178-181`). That mislabels Claude Code `SessionStart`, future/unknown Claude tools, and any missing-interpreter record before Python parsing occurs.

Fold an explicit registration-provenance contract into the FR. The Claude registration must supply a fixed runtime hint to every command, such as `HOOK_RUNTIME=claude-code`; the existing Copilot registration path must resolve to `copilot` without inspecting the requested operation. `hook_input.py` must validate the hint against the accepted enum and must never infer producer identity from tool semantics. Define the behavior for absent/invalid provenance: unparseable or unknown edits that may target governed paths deny; non-edit handling preserves the existing guard policy; every emitted audit record carries `runtime`, including parse-error and no-interpreter records.

### R-3: Make interpreter resolution cover every registered Python callsite

The proposed resolver is not yet a complete execution contract. It names four callers (`FR-961:214-225`), while the Claude registration also launches `classify-emit.sh` and all four post-edit scripts (`FR-961:121-149`); those paths and `common.sh` contain many direct `python3` calls. A resolver added only to the named callers would leave registered hooks silently ineffective on the stated Windows host.

Fold the following rules into the FR:

1. Resolve once per hook process, before any Python-dependent parse or audit operation, and use that executable for every Python subprocess on the registered path, including `pre-command-guard.sh`, `reasoning-pattern-check.sh`, `classify-emit.sh`, `session-briefing.sh`, `memory-advisory.sh`, and all `checks/*.sh` calls reached by the Claude registration.
2. Define `$HOOK_PYTHON` as an authoritative test/operator override. If it is set but missing, non-executable, or older than 3.11, do not fall through to the venv or PATH; emit exactly one `skip/no-interpreter` record and exit 0. If it is unset, use the documented ordered search.
3. Emit the no-interpreter record with shell primitives only, because Python is unavailable. Include runtime, hook name, decision, reason, session id when safely extractable without Python, and a bounded detail; do not emit one record per attempted inner call.
4. State whether `classify-emit.sh`'s absent socket remains a no-op before interpreter resolution. Preserve that cheap no-socket fast path.

### R-4: Freeze transcript turn selection, clean-scan output, and complexity

The FR requires `O(latest message)` scanning (`research brief:85-87`) but describes finding the latest `requestId` by reading transcript lines without defining a bounded reverse-read/index strategy (`FR-961:187-198`). AC-05 also permits an empty-thinking, clean-text turn to log either `skip/no-scannable-text` or `armed` (`FR-961:266-272`), although non-empty clean text is scannable and must never arm. This is a plausible-wrong-answer acceptance criterion.

Fold an exact algorithm and outcome table:

1. Validate `transcript_path` as an existing regular file before reading it; stdin path wins, and the legacy Copilot glob is used only when the field is absent.
2. Define "latest Claude assistant turn" by transcript order and one exact grouping key. Collect all `thinking` and `text` blocks for only that turn, independent of block ordering.
3. A matching turn emits `armed` and a top-level `source` enum of `thinking`, `text`, or `thinking+text`; a non-empty clean turn emits `pass/no-pattern` with its source; a turn with neither non-empty thinking nor text emits `skip/no-scannable-text`; malformed input emits a distinct bounded parse/read error outcome. No criterion may accept both armed and clean outcomes.
4. Either specify and test a bounded reverse-read implementation whose work is proportional to the latest turn, or replace the unsupported complexity claim with a measured maximum transcript size and a worst-case under-five-second performance gate. "Read the full session but call it latest-message complexity" is not authorized.
5. Preserve the FR-883 timing boundary: PostToolUse may arm only; the next PreToolUse consumes the one-shot sentinel.

### R-5: Close committed evidence and prior-art disposition gaps

The exact Claude payload/transcript shape and the 228-block measurement are essential to the adapter and coverage claim, but their cited source is an uncommitted external path (`FR-961:86-96,315`; research brief:44-67,113-125). Input closure therefore provides assertions about the evidence, not the evidence itself. Add a committed, redacted evidence appendix containing: one representative Claude hook stdin object for each relevant lifecycle shape; representative assistant transcript lines showing request grouping and empty/non-empty `thinking` plus `text`; the measurement command/method; aggregate counts; and no private or sensitive content. Tests may reuse minimized fixtures derived from that appendix.

The research record also says its five retrieved noun hits are dismissed in the FR's Prior art line (`FR-961.research.md:3-9`), but the FR's Prior art section does not name FR-597, 034, FR-832, FR-841, or FR-198 (`FR-961:18-38`). Add one explicit dismissal clause for each retrieved hit, even when the reason is the same vocabulary collision, as required by the repository's FR-938 precedent rule.

### R-6: Replace proxy checks with a complete parity matrix

AC-03 greps only two Copilot names and allows comment hits (`FR-961:261-263`), so it cannot prove that `hook_input.py` is the sole vocabulary interpreter. AC-01 names several scripts but does not define every tool-by-intent result, and it omits the registered classifier path from normalization/resolver assertions (`FR-961:249-257`).

Fold a table-driven contract into the FR and tests. Enumerate every accepted raw tool name, canonical class, path extraction rule, runtime, consumer, and expected decision for both runtimes. Include all paths in Copilot `replacements[]`, Claude `edits[]`, notebook paths, and every `apply_patch` Add/Update/Move header. Add negative cases for malformed JSON, unknown edit tools, missing path, multiple paths where one is governed, and Windows separators. Replace the narrow grep with a repository test or exact search that proves all raw Copilot and Claude vocabulary constants outside fixtures/docs live only in `hook_input.py`; consumers may use only canonical classes and normalized fields. Existing Copilot fixtures must remain byte-unchanged, while new parity tests prove equivalent intent produces equivalent decisions.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-961-claude-code-hooks-registration.md`: fold R-1 through R-6, implementation status, host witness, decisions, and deviations. |
| D-2 | Committed, project-scoped `.claude/settings.json`, conditional on the human selecting the recommended registration scope. |
| D-3 | `.github/hooks/scripts/checks/hook_input.py`: stdlib-only canonical payload parser, runtime-provenance validator, tool-class mapper, and path normalizer. |
| D-4 | Existing hook scripts needed to consume the canonical parser and resolved interpreter: `pre-command-guard.sh`, `reasoning-pattern-check.sh`, `classify-emit.sh`, `session-briefing.sh`, `memory-advisory.sh`, `checks/common.sh`, registered `checks/*.sh`, and `checks/main_write.py`. |
| D-5 | `.github/hooks/scripts/session-timeline.py`: explicit transcript-path precedence and runtime rendering. |
| D-6 | `.github/hooks/tests/`: new Claude payload/transcript fixtures, parity matrix, runtime provenance, interpreter resolution, transcript selection, sentinel, audit, and timing witnesses; existing Copilot fixtures remain unchanged. |
| D-7 | A committed redacted FR-961 evidence appendix containing the minimum payload/transcript structures and measurement method required by R-5. |
| D-8 | `.github/hooks/README.md` and one `CLAUDE.md` pointer: exact two-runtime registration, coverage, interpreter, audit, and failure contracts. |
| D-9 | One `changelog/unreleased/` hooks feature fragment and one `docs/diary/` reflection. |

Not authorized: new enforcement rules or registry phrases; deny-message changes; new hook events, including `Stop` or `UserPromptSubmit`; private-reasoning coverage claims for Claude Code; removal or semantic expansion of the one-shot sentinel; activation or modification of the FR-425 classifier daemon/graph; new YAMLGraph graphs or prompts; a second Claude-specific guard tree; automatic installation of Python, Git Bash, Claude Code, or user-level settings; changes to judge/review/graph-authoring doctrine or routes; weakening fail-closed governed-edit behavior; changes to unrelated Copilot hook behavior.

## Revised acceptance criteria

- [ ] AC-01: The human records committed project registration and deferral of extra hook events, or the FR re-enters judgement for any other selection.
- [ ] AC-02: `.claude/settings.json` validates against the runtime-accepted structure, uses anchored edit-tool matchers, registers only the frozen events/scripts, and supplies explicit `claude-code` runtime provenance to every command.
- [ ] AC-03: A Windows Claude Code fixture session produces a `Bash` PreToolUse audit line with `runtime=claude-code`; the FR records the redacted fixture session id and command result.
- [ ] AC-04: `hook_input.py` alone maps all raw runtime tool names and fields into the frozen canonical schema; a mechanical search/test rejects duplicate vocabulary interpretation in executable hook code.
- [ ] AC-05: A table-driven parity suite proves equivalent Copilot and Claude intents yield equivalent decisions for trailer, `--no-verify`, multiline `-m`, governed writes, main-write protection, and post-edit findings across every named edit tool and multi-path shape.
- [ ] AC-06: Malformed/unknown edit payloads, absent paths, and mixed safe/governed multi-path payloads cannot silently approve a potentially governed write.
- [ ] AC-07: Runtime identity comes from registration provenance, not tool names; all audit outcomes include the validated runtime, including pass, deny, parse error, transcript skip/error, and no-interpreter.
- [ ] AC-08: With `HOOK_PYTHON` unset, interpreter resolution follows `.venv/bin/python`, `.venv/Scripts/python.exe`, `python3`, then `python`, accepting only executable Python 3.11+.
- [ ] AC-09: With valid `HOOK_PYTHON`, every Python subprocess on each registered hook path uses that executable; with invalid explicit `HOOK_PYTHON`, the hook exits 0 and appends exactly one shell-produced `skip/no-interpreter` audit record without falling through.
- [ ] AC-10: `classify-emit.sh` preserves the absent-socket fast path and uses the canonical parser/resolved interpreter only when emission is possible.
- [ ] AC-11: `reasoning-pattern-check.sh` prefers a valid stdin `transcript_path`, falls back to legacy Copilot discovery only when absent, and preserves UUID-bound sentinel isolation.
- [ ] AC-12: Claude fixtures prove exact latest-turn grouping across interleaved thinking/text/tool blocks; earlier request matches do not arm; latest clean text logs `pass/no-pattern`; empty text logs `skip/no-scannable-text`; matching sources are reported by the frozen top-level enum.
- [ ] AC-13: Transcript scanning satisfies the revised bounded-complexity contract and completes under five seconds at the documented worst-case fixture size on the Windows host.
- [ ] AC-14: Existing Copilot reasoning-path fallback fixtures and all other `.github/hooks/tests/` pass without fixture edits.
- [ ] AC-15: `session-timeline.py` accepts explicit transcript path data, retains legacy discovery fallback, and renders runtime in both text and JSON output with fixture tests.
- [ ] AC-16: `.github/hooks/README.md` states Claude coverage only as the latest turn's persisted thinking summaries and visible text; no private-reasoning or first-tool-prevention claim remains.
- [ ] AC-17: The committed evidence appendix contains the redacted structural samples, measurement method, and aggregate transcript counts; the Prior art line explicitly dispositions all five research-retrieved hits.
- [ ] AC-18: The FR records implementation status, Windows timing and live hook witness, changelog fragment, diary reflection, `CLAUDE.md` pointer, and human review of the final enforcement diff.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-6 are folded into the FR and the human records the two scope decisions. | GATE |
| C-2 | Human review of the final diff is mandatory before merge because hooks and runtime registration are enforcement infrastructure. | GATE |
| C-3 | RED parity, malformed-input, interpreter, transcript, audit, and timing witnesses must precede production changes. | GATE |
| C-4 | One canonical parser and one shared script tree only; no runtime-specific rule copy may be introduced. | GATE |
| C-5 | Missing interpreter may fail open only with exactly one bounded audit record; ambiguous governed edits remain fail closed. | GATE |
| C-6 | Runtime provenance must be registration-derived and present on every new audit entry; vocabulary inference is forbidden. | GATE |
| C-7 | Claude Code coverage claims are limited to persisted summaries and visible text, and sentinel timing remains PostToolUse arm -> next PreToolUse deny. | GATE |
| C-8 | No graph, LLM hot path, classifier-daemon activation, new event, rule text, registry phrase, or deny-message change may enter this FR. | GATE |
| C-9 | Tests and committed evidence must contain only redacted/minimized fixtures; no test may read the operator's real `~/.claude/projects/` store. | GATE |
| C-10 | Do not invoke another judge, the judge adapter, the judge graph, or YAMLGraph while enforcing this judgement. | GATE |

Authority granted: after the revisions and human gates are folded, enforcement may add the committed Claude Code registration and adapt the existing hook layer for two-runtime parsing, transcript discovery, runtime-labelled audit, and Windows interpreter resolution within the frozen surfaces above.
