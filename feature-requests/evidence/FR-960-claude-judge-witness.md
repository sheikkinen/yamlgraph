# FR-960 Evidence — Claude judge variant witness (authoring proof, live runs, dual-run inventory)

**FR:** [FR-960](../FR-960-claude-judge-variant.md) · **Judgement:** [FR-960 judgement](../FR-960-claude-judge-variant.judgement.md) (R-6 protocol)
**Branch:** `feat/fr-960-claude-judge-variant` · **Host:** Windows 11, Git Bash inside the Claude desktop app's process tree; `copilot` 1.0.82 on PATH; Claude Code 2.1.255 at the MSIX LocalCache path (see FR-959 evidence)

## 1. Authoring proof (judgement C-3, AC-03)

| Field | Value |
|---|---|
| Command | `scripts/author.sh --no-preflight feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md` with `PATH=/c/src/yamlgraph/.venv/Scripts:$PATH`, `YAMLGRAPH_BIN=…/.venv/Scripts/yamlgraph.exe`. The pre-flight was run first, separately, with the venv interpreter (`python scripts/author_preflight.py <brief> --workdir .`): premise `.github/skills/judge-fr/adapters/graph.yaml` exists; commands `yamlgraph`, `yamlgraph`, `python`, `python` resolve; rc 0. `--no-preflight` only skipped the wrapper's second, identical run of that check (its `python3` lookup hits the Windows Store stub on this host). |
| Brief | `feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md`, committed in `9a4ecd76` before the run |
| Run | 2026-09-03 03:38:58Z start; yamlgraph 0.5.23 run id `01a06559-2c61-75a1-9f2b-cea95070459e`; Copilot CLI session `2190105c-3750-456f-9206-c867d1fbd1d6`, model `gpt-5.5`; wrapper verified the report (`author rc=0`) |
| Local report | `tmp/draft-authoring-report.md` — **not committed** (`.github/skills/graph-authoring/SKILL.md:35`); sha256 `ed42ab0f96797f205f9212eec4cdfa0a4937ef2c6fa38ed9afefe2f33d0feee0` |
| Report — Artifacts (quoted) | `.github/skills/judge-fr/adapters/graph.yaml`; `.github/skills/judge-fr/adapters/prompts/judge.yaml` |
| Report — Validation (quoted) | "`yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml` -> passed, 0 issues." · "`yamlgraph graph validate …` -> passed, graph valid with 3 nodes and 5 edges." · "`python -m pytest tests/unit/test_fr960_claude_judge_variant.py -k TestGraphRouting …` -> passed, 4 passed and 8 deselected." · "`python -m pytest tests/unit/test_fr931_sole_route_model_pin.py …` -> passed, 3 passed." |
| Report — Repairs (quoted) | "Initial lint reported `E601` for `select` because passthrough nodes require an explicit `output` mapping. Repaired by adding `output: {}` to the selector node, matching existing committed passthrough precedent." |
| Report — Blocked validation (quoted) | "None." |
| Re-verified by the requesting session | lint 0 issues; validate ok; routing + pin tests 7 passed; `git diff` of the two files matches the brief's target byte-for-byte except the `output: {}` repair and the two header-comment edits the brief allowed |
| Graph commit | `235e2cab` (`feat(judge): FR-960 Claude judge variant …`) — first pass |
| **Second pass** (PR #577 review P3) | Same brief (updated to `model: claude-opus-5`), same command, 2026-09-04 02:39:07Z–02:41:11Z. Local report sha256 `895487f2aae6f12fe81338b6eb0f55fc1f6a9ef596e51cf7a5ea245e6dcf4e3e`. Artifacts (quoted): "`graph.yaml` — authored the `judge_claude` model pin to exact id `claude-opus-5` …"; "`prompts/judge.yaml` — … no content edit was needed". Validation (quoted): lint "No issues found"; validate "VALID; nodes 3, edges 5"; routing "4 passed, 8 deselected"; pin test "3 passed". Repairs (quoted): "restoring the existing `output: {}` on the `select` passthrough node". Blocked validation: "None." Resulting diff: exactly one line (`model: opus` → `model: claude-opus-5` + comment). Graph commit: the commit carrying this row. |
| Limitations | The authoring agent ran under Copilot on this host; it did not execute any judge. The wrapper's own bash tests could not run from pytest here (FR-953 class) and were exercised by hand — see FR-960 Implementation Status. |

## 2. Live runs

### 2.1 Run A — default backend (`copilot`), target FR-961

| Field | Value |
|---|---|
| Target | `feature-requests/FR-961-claude-code-hooks-registration.md` (Status Proposed, unjudged before this run) at commit `235e2cab` |
| Command | `YAMLGRAPH_BIN=…/.venv/Scripts/yamlgraph.exe bash scripts/judge.sh feature-requests/FR-961-claude-code-hooks-registration.md` (no `JUDGE_BACKEND` set → `copilot`) |
| Backend / model | `copilot` · Copilot CLI 1.0.82 · `gpt-5.6-sol` (graph pin) |
| Auth mode | GitHub Copilot seat (unchanged route; FR-959 preflight not involved) |
| Start / end | 2026-09-03T03:43:22Z / 2026-09-03T03:47:42Z |
| Run id / session | yamlgraph run `01a0655d-3bc3-7ade-a34d-bf1e22c8e34a`; Copilot session `cc5b174b-3ba7-496f-80b4-91f80375c474` |
| Artifact | `tmp/draft-judgement-copilot-FR-961-claude-code-hooks-registration.md` — 19,670 bytes, 122 lines, sha256 `4d1ce473f6f69b5d177558c364bb97332e3f225b2a6108ec7de74d81b6e1ef70` (local; kept as `tmp/draft-judgement-copilot-FR-961-…` for the inventory) |
| Verdict line | `**Verdict:** APPROVED WITH REVISIONS - the shared-script, thin-registration direction is sound and cohesive, but authority activates only after runtime provenance, interpreter failure semantics, transcript selection, evidence closure, and the two human decisions are made mechanically unambiguous.` |
| Wrapper output | `judge.sh: draft written: …/tmp/draft-judgement-copilot-FR-961-claude-code-hooks-registration.md (backend=copilot; advisory until human-reviewed)`, rc 0 |
| Coexistence | the pre-FR-960 fixed-name file `tmp/draft-judgement.md` (from the 2026-09-02 FR-960 judgement) was **not** touched by this run — the first live proof that the new naming stops the clobber |

### 2.2 Run B — `JUDGE_BACKEND=claude`, target FR-961

| Field | Value |
|---|---|
| Target | same FR-961 file, same commit `235e2cab` (unchanged between runs) |
| Command | `PATH=<MSIX LocalCache dir>:$PATH YAMLGRAPH_BIN=…/yamlgraph.exe JUDGE_BACKEND=claude bash scripts/judge.sh feature-requests/FR-961-claude-code-hooks-registration.md` |
| Backend / model | `claude` · Claude Code `2.1.255 (Claude Code)` (preflight) · `--model opus` at the time of this run; the alias resolves to `claude-opus-5` on this version (§2.4), and the graph has since been re-authored to pin that exact id |
| Auth mode (FR-959 preflight) | `claude.ai` — log line `[judge_claude] Claude Code 2.1.255 authenticated via claude.ai; executing with timeout=600s` |
| Routing | `yamlgraph.route` event: `{"event": "route", "node": "select", "value": "backend == \"claude\"", "target": "judge_claude"}`; the `judge` (Copilot) node was not visited |
| Start / end | 2026-09-04T02:16:11Z / 2026-09-04T02:22:39Z (6 min 28 s) |
| Run id | `01a06a33-cad7-7983-8b9f-915c711883e0` |
| Argv (from the graph, mocked-equivalent proven by `test_claude_backend_visits_only_judge_claude_with_four_tools`) | `claude -p <prompt> --output-format json --model opus --tools Read,Glob,Grep,Write --allowedTools Read,Glob,Grep,Write --max-turns 40` — no `--dangerously-skip-permissions`, no `--add-dir` |
| Artifact | `tmp/draft-judgement-claude-FR-961-claude-code-hooks-registration.md` — 148 lines, sha256 `96282fa1013217b3da2e184b5fe2ee644c9b1191be2b062f483aa0763980730f`; preserved as [FR-960-run-B-claude-draft-FR-961.md](FR-960-run-B-claude-draft-FR-961.md) |
| Verdict line | `**Verdict:** APPROVED WITH REVISIONS — the defect is real, the chosen class is the minimal one, and the research record clears the FR-890 gate; but authority activates only after the FR proves the guard's allow path does not auto-approve on Claude Code, commits the measurement its coverage re-scope rests on, closes the interpreter seam across all 16 script files rather than the 4 it names, resolves the `unknown`-runtime contradiction, and makes AC-01/AC-03/AC-09 mechanically runnable.` |
| Wrapper output | `judge.sh: draft written: …/tmp/draft-judgement-claude-FR-961-claude-code-hooks-registration.md (backend=claude; advisory until human-reviewed)`, rc 0 |
| Re-entry guard | the agent's final text: "I judged directly, without invoking the judge skill, graph, or any adapter." No nested judge in the log. |
| Coexistence (AC-14) | after run B the Copilot artifact from run A (`4d1ce473…`, 19,670 bytes) and the legacy `tmp/draft-judgement.md` both still exist unchanged — two backends, one FR, two drafts |

### 2.3 Run B' — Run B with `ANTHROPIC_API_KEY=sk-invalid-on-purpose` exported (AC-13)

| Field | Value |
|---|---|
| Command | as run B, prefixed `ANTHROPIC_API_KEY=sk-invalid-on-purpose` |
| Auth mode (preflight) | `claude.ai` — the invalid key never reached the child (FR-959 strip); had it, the CLI would have reported `api_key` and the preflight would have refused before `-p` |
| Start / end | 2026-09-04T02:22:39Z / 2026-09-04T02:28:44Z (6 min 05 s) |
| Run id | `01a06a39-b122-76ea-817b-e3576118f2a5` |
| Artifact | same path as run B (same backend, same FR → **replaced**, as designed); sha256 `91fa5e7cc23c6737e03792b7b417717d21eaa50b541679b5f032d9f1c768853b`; preserved as [FR-960-run-Bprime-claude-draft-FR-961.md](FR-960-run-Bprime-claude-draft-FR-961.md) |
| Verdict line | `**Verdict:** APPROVED WITH REVISIONS` — 11 required revisions, 10 GATE conditions, 3 human questions (the agent's own summary) |
| Outcome | AC-13 holds: the subscription-authenticated result is unchanged in kind (same verdict class, same auth method, rc 0); FR-959's kill criterion did not fire |
| Note | B and B' are two independent Claude judge sessions on identical input and produced different drafts (9 vs 11 revisions; overlapping but not identical findings). This is expected non-determinism and is why the inventory in §3 compares run **A** with run **B** only; B' is the payer witness. |

### 2.4 Model-identity probe (PR #577 review P3)

The `--output-format json` envelope carries a `modelUsage` object keyed by
the exact model ids the session used. One-word probe from the enforcing
session, 2026-09-04, same binary and login as runs B/B':

```
$ claude -p "Reply with the single word pong and nothing else." --output-format json --model opus --tools ""
rc=0  is_error=False  result='pong'  duration_ms=3135
modelUsage keys: ['claude-haiku-4-5-20251001', 'claude-opus-5']
```

`opus` → `claude-opus-5`. The `claude-haiku-4-5-20251001` entry is the
CLI's internal helper model (classification/summaries), not the responding
model. Consequence: the graph pins `model: claude-opus-5` (re-authored via
`scripts/author.sh`, §1 second pass), and the routing test asserts it.
Runs B and B' above executed with the alias; their `--model opus` resolved
to this same id on this same CLI version, which is why they are kept as
witnesses rather than re-run.

## 3. Dual-run inventory (judgement R-6, AC-15)

Items are `CP-n` (Copilot draft, run A) and `CL-n` (Claude draft, run B). Each
carries one disposition — `matched <id>`, `contradicted <id>`, or
`backend-only` — with the draft section and the file:line evidence the draft
itself cites. Both drafts judged the same committed FR-961 at `235e2cab`.

### 3.1 Copilot draft (run A) — inventory

| ID | Section | Claim | Evidence cited by the draft | Disposition |
|---|---|---|---|---|
| CP-V | Verdict | APPROVED WITH REVISIONS; authority after provenance, interpreter semantics, transcript selection, evidence closure, two human decisions | — | _pending run B_ |
| CP-S1 | What is sound | Problem concrete, first consumer named; guards classify Copilot tool names literally | `pre-command-guard.sh:91,114,148,240-241,280-310`; `checks/common.sh:10-13`; `checks/main_write.py:47-50`; `FR-961:8-13,59-85` | _pending_ |
| CP-S2 | What is sound | One parser + two thin registrations beats a copied tree; research has 4 solution classes, preserved dissent, daemon dispositioned, `is_this_a_graph` = no | `FR-961:41-48,167-183,229-243`; `FR-961.research.md:53-73,86-94` | _pending_ |
| CP-S3 | What is sound | Single responsibility: runtime-neutral enforcement layer; sub-parts are coupled prerequisites; no new rule/graph/LLM path | `FR-961:296-305` | _pending_ |
| CP-S4 | What is sound | Feasible: hooks get JSON stdin, Copilot contract has `transcript_path`; scanner/timeline hardcode macOS discovery | `.github/hooks/README.md:45-67`; `reasoning-pattern-check.sh:36-50`; `session-timeline.py:52-73` | _pending_ |
| CP-S5 | What is sound | Classification: contrib/repo-operations integration, not a framework primitive | — | _pending_ |
| CP-S6 | What is sound | Acceptance plan unusually close to executable | `FR-961:249-294` | _pending_ |
| CP-R1 | R-1 | Record the two human decisions (registration scope → committed project; extra events → defer); remove the contradiction between the plan and the trailing questions | `FR-961:118-163,200-204,239,318-331` | _pending_ |
| CP-R2 | R-2 | Runtime provenance from registration (fixed hint e.g. `HOOK_RUNTIME`), never inferred from tool vocabulary; define absent/invalid provenance behaviour; every audit record carries `runtime` | `FR-961:105-110,178-181,206-210` | _pending_ |
| CP-R3 | R-3 | Interpreter resolution must cover every registered Python callsite; `HOOK_PYTHON` authoritative (no fall-through); shell-only `skip/no-interpreter` record; preserve `classify-emit.sh` no-socket fast path | `FR-961:121-149,214-225` | _pending_ |
| CP-R4 | R-4 | Freeze latest-turn selection, outcome enum (`armed`/`pass/no-pattern`/`skip/no-scannable-text`/parse error), `source` enum; bounded reverse-read or measured <5 s gate; PostToolUse arms only | `FR-961:187-198,266-272`; research brief `:85-87` | _pending_ |
| CP-R5 | R-5 | Commit a redacted evidence appendix (hook stdin shapes, transcript lines, measurement method, counts); disposition FR-597, 034, FR-832, FR-841, FR-198 explicitly in Prior art | `FR-961:18-38,86-96,315`; `FR-961.research.md:3-9`; brief `:44-67,113-125` | _pending_ |
| CP-R6 | R-6 | Replace the two-name grep with a table-driven parity matrix (every raw tool, class, path rule, runtime, decision; negative cases incl. Windows separators); prove vocabulary constants live only in `hook_input.py` | `FR-961:249-263` | _pending_ |
| CP-C1..C10 | Conditions | Fold before authority; human diff review; RED first; one parser/one tree; fail-open only with one audit record; provenance registration-derived; coverage claim limited + sentinel timing; no graph/LLM/new event/rule change; redacted fixtures only, never read the real `~/.claude/projects/`; never re-invoke the judge | — | _pending_ |

### 3.2 Claude draft (run B) — inventory

| ID | Section | Claim | Evidence cited by the draft |
|---|---|---|---|
| CL-V | Verdict | APPROVED WITH REVISIONS (R-1..R-9); authority after allow-path witness, committed measurement, interpreter seam across 16 files, `unknown`-runtime contradiction, runnable AC-01/03/09 | — |
| CL-S1 | What is sound | Problem witnessed on the host: no `.claude/**`, no `audit.jsonl` under `.github/hooks/logs/` | directory listings |
| CL-S2 | What is sound | Every sampled evidence citation resolves; the codebase "half-anticipated a second vocabulary" | `common.sh:12,62`; `main_write.py:46-51`; `reasoning-pattern-check.sh:36-50`; `session-timeline.py:52-73`; `pre-command-guard.sh:59,161` |
| CL-S3 | What is sound | Registration is parity, not expansion: `session-briefing.sh` already bound to Copilot `SessionStart` with the same timeout; `memory-advisory.sh` reached transitively | `session-probe.json:9-13`; `session-briefing.sh:16` |
| CL-S4 | What is sound | Research has substance: 4 classes, preserved subtractionist dissent, `is_this_a_graph` no, two self-reported defects (CRLF mismatch, markup leak) | `FR-961.research.md` |
| CL-S5 | What is sound | FR under-claims coverage where FR-883 R-1 demands it (option G) | `FR-961` first-consumer paragraph; option G |
| CL-S6 | What is sound | Classification: extension of an existing enforcement primitive, not a framework primitive | — |
| CL-S7 | What is sound | SPLIT considered and rejected: §5 and §3 are one dependency chain | `FR-961` §3, §5 |
| CL-R1 | R-1 | **Guard's allow path prints `{"decision":"approve"}`; if Claude Code still honours the deprecated key, registering the guard silently pre-approves every tool call.** Emit `{}` for `runtime == claude-code`; add a live AC that the operator prompt still appears | `pre-command-guard.sh:312,416`; `FR-961` §1 |
| CL-R2 | R-2 | Commit the 228-block measurement as an evidence appendix (command, four verbatim thinking texts, one empty block, session ids, date) | `FR-961:315`; `read_raw_output_first` |
| CL-R3 | R-3 | Interpreter seam is 43 occurrences in 16 files, not 4 callers; `session-briefing.sh` is `#!/bin/sh` and cannot source bash `common.sh`; sourcing `common.sh` from `scripts/` re-derives `LOG_DIR` to `.github/logs` (second audit sink); `common.sh` and `pre-command-guard.sh` call literal `python3`. Create POSIX `lib/resolve_python.sh` exporting only `HOOK_PY` | `session-briefing.sh:1`; `common.sh:4,8,33-35,42,76,108`; `pre-command-guard.sh:23,54,105-106,130,149,291` |
| CL-R4 | R-4 | `unknown` runtime is unreachable as written; make the rule three-way (Claude marker → claude-code; known Copilot name → copilot; neither → unknown) and pin unknown+governed-path → deny | `FR-961` §2 |
| CL-R5 | R-5 | `tests/conftest.py:30` executes the `.sh` path directly → AC-01 unrunnable on the Windows first-consumer host; choose a `bash` shim (a) or declare AC-01 macOS-only (b) | `tests/conftest.py:30` |
| CL-R6 | R-6 | AC-03's grep needs `-rn`; state the exact 16-occurrence hit set across three files and the two `case` heads the FR's citation omits | `pre-command-guard.sh:91,114,147-148,240-241,279-282,310`; `main_write.py:46-51`; `common.sh:12` |
| CL-R7 | R-7 | Drop `classify-emit.sh` from the Claude registration: AF_UNIX socket cannot exist on Windows, daemon not activated, forwards tool stream to an LLM classifier (spend/data decision) | `classify-emit.sh:9,44`; `README.md:313,412` |
| CL-R8 | R-8 | AC-09's deny witness must be a live Claude Code `Bash` call refused by the runtime, not piped stdin | `FR-961:71` |
| CL-R9 | R-9 | Freeze the Scripture `### Copilot Hooks` header, token list, and 15-line budget; `.github/copilot-instructions.md` not edited | `.github/copilot-instructions.md:30`; `tests/test_copilot_instructions_hooks_docs_red.py:11,46-58,67` |
| CL-C1..C8 | Conditions | Fold R-1..R-9; RED first and `lib/resolve_python.sh` before `.claude/settings.json`; **no auto-approve (stop if AC-03 fails)**; human diff review incl. settings + allow-path output; fail-closed governed edits; no LLM in hooks and no forwarding to an LLM daemon; single audit sink; adjacent work parked | — |
| CL-Q1..Q3 | Questions for the human | Registration scope (project file recommended); option H timing (defer); classify-emit / FR-425 daemon (explicit spend-and-data decision) | — |

### 3.3 Dispositions

| Copilot item | Claude item | Disposition | Where they differ |
|---|---|---|---|
| CP-V | CL-V | matched | same verdict class; 6 vs 9 revisions |
| CP-S1 | CL-S1, CL-S2 | matched | Claude adds the host-level absence check (no `.claude/**`, no `audit.jsonl`) |
| CP-S2 | CL-S4 | matched | Claude additionally credits the research record's two self-reported defects |
| CP-S3 | CL-S7 | matched | both keep one responsibility; Claude explicitly weighed and rejected SPLIT |
| CP-S4 | CL-S2 | matched | same macOS-glob evidence lines |
| CP-S5 | CL-S6 | matched | contrib/integration vs extension-of-existing-primitive: same class, different words |
| CP-S6 ("acceptance plan unusually close to executable", `FR-961:249-294`) | CL-R5 (`conftest.py:30` runs `.sh` directly; AC-01 unrunnable on the Windows host) | **contradicted** | Copilot praises the ACs as near-executable; Claude shows the RED test cannot execute on the first-consumer host at all |
| CP-R1 | CL-Q1, CL-Q2 | matched | both require the two human decisions; Copilot wants them folded before enforcement, Claude reserves them as questions with the same recommendations |
| CP-R2 (runtime from registration provenance, e.g. `HOOK_RUNTIME`; vocabulary inference forbidden, `FR-961:178-181`) | CL-R4 (keep vocabulary detection, make it three-way with a reachable `unknown`) | **contradicted** | opposite mechanisms for the same defect: Copilot forbids inferring runtime from tool names; Claude repairs the inference. Copilot's C-6 makes this a GATE |
| CP-R3 (resolver on every callsite; `HOOK_PYTHON` authoritative; shell-only skip record; preserve classify-emit fast path) | CL-R3 (43 occurrences/16 files; POSIX lib; `LOG_DIR` split; `sh`-vs-`bash` sourcing) | matched | same finding; Claude names three concrete defects (`#!/bin/sh`, `LOG_DIR`, literal `python3` in `common.sh`) Copilot does not |
| CP-R3 item 4 / CP-R6 (keep `classify-emit.sh` registered; preserve its no-socket fast path; include it in resolver assertions) | CL-R7 (drop `classify-emit.sh` from the Claude registration) | **contradicted** | Copilot assumes the classifier stays registered; Claude removes it as an unwitnessed LLM-forwarding spend/data surface that cannot work on Windows |
| CP-R4 (freeze turn selection; outcome enum; **no criterion may accept both `armed` and a clean outcome**; bounded complexity or measured gate; `FR-961:187-198,266-272`) | CL AC-06 (retains "logs `skip/no-scannable-text` **or** `armed` with `source=text`") | **contradicted** | Copilot names AC-05's "or" a plausible-wrong-answer criterion and forbids it; Claude carries the same "or" forward unchanged |
| CP-R5 (evidence appendix **and** explicit dismissal of FR-597, 034, FR-832, FR-841, FR-198) | CL-R2 (evidence appendix) | matched on the appendix; the prior-art dismissal half is **backend-only (Copilot)** | Claude did not check the research record's five retrieved hits against the FR's Prior art line |
| CP-R6 (table-driven parity matrix; every raw tool/class/path rule/runtime/decision; negative cases; Windows separators) | CL-R6 (fix the grep and pin its exact hit set) | matched | same proxy-check defect; Copilot's remedy is a full matrix, Claude's is an exact search plus the two missed `case` heads |
| — | CL-R1 (allow path `{"decision":"approve"}` may auto-approve on Claude Code) | **backend-only (Claude)** | the highest-severity finding in either draft; the Copilot draft does not mention the guard's stdout on the allow path |
| — | CL-S3 (SessionStart parity via `session-probe.json:9-13`) | backend-only (Claude) | |
| — | CL-R8 (deny witness as a live runtime refusal) | backend-only (Claude) | Copilot's AC-03/AC-05 accept an audit row and stdin fixtures |
| — | CL-R9 (freeze the Scripture hooks section and its pinning test) | backend-only (Claude) | |
| CP-C1..C10 | CL-C1..C8 | matched, except: CP-C6 (provenance registration-derived) ↔ CL-R4 **contradicted** as above; CL-C3 (stop if auto-approve is honoured) and CL-C7 (single audit sink) **backend-only (Claude)**; CP-C9 (never read the operator's real `~/.claude/projects/`) **backend-only (Copilot)** — Claude's R-2 asks to quote four real thinking blocks from that store (redacted) | |

Summary: 11 matched rows, 4 contradicted (CP-S6/CL-R5, CP-R2/CL-R4, CP-R3.4+R6/CL-R7, CP-R4/CL-AC-06), 5 backend-only Claude (CL-R1, CL-S3, CL-R8, CL-R9, CL-C3+C7), 2 backend-only Copilot (CP-R5 prior-art half, CP-C9). The sentinel `no backend-only or contradicted items` does **not** apply. The second judge added something on this FR: CL-R1 is a safety finding about the enforcement layer's allow path that the first judge missed, and CP-R2/CL-R4 is a genuine design disagreement the FR-961 author must resolve rather than fold blindly.

## 4. Signatures (judgement AC-16; a human other than the enforcer)

1. Enforcement-infrastructure diff and route invariants accepted by: `<name>, <date>` — **UNSIGNED**
2. Residual Claude subscription payer boundary (FR-959 §5) accepted for judge execution by: **sheikkinen (repository owner and spend owner), 2026-09-03** — given in the enforcing session after C-8's text and cost were laid out; recorded verbatim by the enforcer: "accepted".

## 5. Limitations

- Signature 1 (§4) is unsigned at the time of writing: the infrastructure diff and route invariants must be accepted by a human other than the enforcer (the PR review is where that happens). The Claude route is therefore **not yet operational** for routine use, even though it has been witnessed.
- Runs B and B' were launched from the enforcing session (a child of the Claude desktop app) with the MSIX binary prepended to `PATH`; an operator shell needs the same `PATH` step (see FR-959 evidence for the two path spellings).
- The drafts are advisory FR-961 material. They are preserved here as raw records for this inventory only; folding any of them into FR-961's judgement is FR-961's business and is not done by FR-960.
- Runs B and B' were executed with `--model opus`; the alias's resolution to `claude-opus-5` was observed afterwards (§2.4) and the graph now pins the exact id. An earlier version of this file claimed the envelope did not expose the id; that was wrong — `modelUsage` does, and the runtime's typed parser simply ignores the key.
- Cost: two full Claude judge sessions (about 6 min each) on the operator's Claude Team subscription, plus one Copilot judge session on the Copilot seat. `total_cost_usd` is notional under subscription and was not captured.
- The inventory (§3) was written by the enforcer, not by a graph; the dual-run comparison graph stays deferred per FR-960's alternatives table (three witnesses before filing).
