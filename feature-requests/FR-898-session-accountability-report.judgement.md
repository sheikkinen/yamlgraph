# Judgement: FR-898 Session Accountability Report from Existing Stores

**Prior art:** hook hits are FR-898's own artifact family (FR, research — self-reference, dispositioned by this verdict) and FR-225-a2a-test-coverage (lexical "accountability" match only; unrelated territory). Substantive prior art is dispositioned in the FR's Prior art line and Existing-assets analysis.

**Verdict:** APPROVED WITH REVISIONS — the reporting-first direction is sound and evidenced, but authority activates only after the FR folds in the concrete receipt path, malformed-store semantics, graph-authoring boundary for classification, and prompt-privacy boundary below.

**Reviewed against:** `feature-requests/FR-898-session-accountability-report.md`; `feature-requests/FR-898.research.md`; `feature-requests/research-briefs/session-accountability-record.md`; `docs/diary/2026-08-29-event-log-partial-read-plausible-ledger.md`; `scripts/vscode/session_report.py`; `scripts/vscode/ledger.py`; `.github/skills/session-introspection/SKILL.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.gitignore` (searched for report/prototype exclusions; no relevant entries).

## What is sound

The first consumer is concrete: the operator asks "what did today's sessions do and what did each cost," with prompts, intents, models, repo, and credits named as the first-event output (`feature-requests/FR-898-session-accountability-report.md:8`, `feature-requests/FR-898-session-accountability-report.md:23-26`). The problem is real and narrow: existing tools aggregate daily/model cost or narrative but do not join prompt, intent, model, repo, and cost at session scope (`feature-requests/FR-898-session-accountability-report.md:28-34`, `.github/skills/session-introspection/SKILL.md:35-37`).

The hook deletion is the strongest part of the plan. The FR read the raw platform store and found prompt text, model IDs, credits, titles, timestamps, tokens, and workspace mapping already persisted per request (`feature-requests/FR-898-session-accountability-report.md:38-91`). That satisfies the local measurement/raw-read law, which requires surprising raw samples before authority on measurement tooling (`.github/copilot-instructions.md:115`, `.github/copilot-instructions.md:233`), and it follows `does_the_platform_already_do_this` instead of duplicating platform state (`.github/copilot-instructions.md:126`). The research record preserved disagreement across five personas and prior art (`feature-requests/FR-898.research.md:1-3`, `feature-requests/research-briefs/session-accountability-record.md:3-8`), then the FR dispositioned the originally proposed hook pair as redundant after the later store measurement (`feature-requests/FR-898-session-accountability-report.md:202-222`).

The event-log boundary is correctly identified. The FR names the complete record grammar, last-write-wins replay requirement, and the same-day false ledger that undercounted credits by 3.2x (`feature-requests/FR-898-session-accountability-report.md:51-69`). The diary independently records the causal trap: grep and structural scan produced plausible but wrong totals, while full replay found the correct request count, titles, and credits (`docs/diary/2026-08-29-event-log-partial-read-plausible-ledger.md:12-31`). The prototype demonstrates feasibility by implementing replay, kind 2 insert/delete handling, title recovery, and CSV rendering in stdlib Python (`scripts/vscode/session_report.py:13-15`, `scripts/vscode/session_report.py:45-75`, `scripts/vscode/session_report.py:124-190`).

Strategic classification: **contrib/example**. This is not a framework primitive; it is a repository/operator tool over VS Code Copilot stores, with one named consumer and existing local script precedents (`feature-requests/FR-898-session-accountability-report.md:113-136`, `feature-requests/FR-898-session-accountability-report.md:226-230`). The optional closed-enum classifier, if kept, is an example graph because "for each prompt, classify" fits the map-node task shape and must obey the graph-authoring sole route (`feature-requests/FR-898-session-accountability-report.md:138-150`, `.github/copilot-instructions.md:15`).

## Required revisions

### R-1: Replace the dangling "committed prototype receipt" reference with a concrete artifact and exact assertions

Add the receipt path to the FR and AC-02. The current AC says totals must match "the committed prototype receipt" and that the receipt is cited in the FR, but no artifact path is named in the reviewed FR section (`feature-requests/FR-898-session-accountability-report.md:167-172`). Fold in an exact committed receipt path under `tmp/` only if the enforcement plan deliberately treats it as uncommitted scratch, otherwise under a durable evidence path such as `feature-requests/FR-898.receipt.md`; include command, session file identifier or sanitized fixture source, expected request count, expected per-request final credits for at least the witnessed first turn, total credits, and the mid-session model switch assertion.

Also resolve the apparent credit contradiction: the measured-facts section still calls 69.75795 and 46.77065 "exact per-turn" UI figures (`feature-requests/FR-898-session-accountability-report.md:48-50`), while AC-02 later says those are intermediate figures that an unpatched scan returns and must not be used (`feature-requests/FR-898-session-accountability-report.md:167-172`). Keep one interpretation and demote the other to an explicit discarded observation.

### R-2: Specify malformed/truncated JSONL behavior instead of "tolerated"

Rewrite AC-01/AC-03 so malformed or truncated stores have a mechanically checkable outcome. "Tolerated" is not enough for a reader over event-sourced cost data (`feature-requests/FR-898-session-accountability-report.md:161-166`), especially under the repo law that plausible wrong answers are worse than crashes (`.github/copilot-instructions.md:78`). Required semantics: invalid JSON line, impossible patch path, missing snapshot, and truncated request each produce either (a) a row/session with `unavailable_reason` and excluded-from-total accounting, or (b) a hard error for that requested session; default all-store scans may continue only while reporting skipped sessions and reasons on stderr and in CSV fields. Silent omission is not authorized.

### R-3: Make the closed-enum intent path either in-scope with a graph-authoring receipt or explicitly deferred

The FR summary promises "a classified intent" (`feature-requests/FR-898-session-accountability-report.md:13-19`) and the first event asks for "intents" (`feature-requests/FR-898-session-accountability-report.md:8`), but the base report only includes vendor `generatedTitle` summaries and returns `intent = null` unless `--classify` is used (`feature-requests/FR-898-session-accountability-report.md:138-150`). Choose one path in the FR:

1. Keep classification in FR-898: add a concrete `examples/demos/session-intent/` graph artifact plan, the authoring-route receipt requirement, the closed enum schema contract, and one smoke assertion showing `--classify` merges Pydantic-validated intents into the CSV.
2. Defer classification: rename the base field to `summary`/`generated_title`, remove "classified intent" from the summary and ACs, and create a follow-up FR for closed-enum intent.

Do not leave "optional refinement" as a required AC without an authoring receipt. Graph artifacts are governed by the sole authoring route (`.github/copilot-instructions.md:15`).

### R-4: Add an explicit prompt-privacy boundary for stdout and `--out`

The report intentionally emits verbatim prompts (`feature-requests/FR-898-session-accountability-report.md:44-45`, `feature-requests/FR-898-session-accountability-report.md:127-136`), and the same FR cites implicit `.env` attachment provenance as a motivating witness (`feature-requests/FR-898-session-accountability-report.md:235-237`). The out-of-scope list only says reports are not committed to git (`feature-requests/FR-898-session-accountability-report.md:190-199`), which is not a mechanical guard.

Fold in one explicit policy: either default to verbatim local-only output with a warning and require `--out` to refuse paths inside the repository unless `--allow-repo-output` is passed, or default to redacted prompts with `--verbatim` opt-in. The human privacy/spend owner may choose either; the FR must state the choice before enforcement.

### R-5: Freeze the monthly/anomaly report as separate future work

The implementation record asks the Judge to rule on monthly aggregation and anomaly sections as a candidate scope extension (`feature-requests/FR-898-session-accountability-report.md:261-263`). Not authorized. Add it to Out of scope or a follow-up seed. FR-898 authority is for the session/request ledger and its documented CSV seam only.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/vscode/session_ledger.py`: read-only stdlib replay reader over VS Code `chatSessions/*.jsonl`, defaulting to today/this workspace with `--session`, `--window Nh`, `--all-workspaces`, `--csv`, and `--out` only if the privacy policy from R-4 is folded in. |
| D-2 | Unit fixtures and tests for event-log replay, last-write-wins credits, kind 2 insert/delete, generatedTitle recovery, malformed/truncated records, missing credits fallback, workspace-to-repo mapping, CSV schema, and read-only behavior. |
| D-3 | Optional only if R-3 chooses in-scope classification: `examples/demos/session-intent/` graph and prompts authored through the graph-authoring route, plus the `--classify` merge path in `session_ledger.py`. |
| D-4 | Documentation updates: `.github/skills/session-introspection/SKILL.md`, `scripts/vscode/README.md`, `scripts/vscode/ledger.py` docstring correction, and the MAP.md third-anchor closure cited by the FR. |
| D-5 | Changelog fragment in `changelog/unreleased/`. |

Not authorized: lifecycle hooks; daemon/scheduled execution; writing to or normalizing the vendor store; committing generated reports; monthly aggregation; anomaly detection; upgrading `scripts/vscode/ledger.py` to prefer persisted credits; changing judge/review/graph-authoring doctrine; broad VS Code store migration tooling beyond the four record shapes documented in the FR.

## Revised acceptance criteria

- [ ] AC-01: Fixture tests materialize a `chatSessions/*.jsonl` patch log by replaying kind 0 snapshot, kind 1 set, kind 2 insert, and kind 2 splice-delete records with last-write-wins semantics; intermediate `copilotCredits` patches are never summed.
- [ ] AC-02: Fixture tests prove prompt, request timestamp, per-request `modelId`, final `copilotCredits`, prompt/completion token counts, generatedTitle summary, session title, session ID, creation date, and workspace/repo mapping are joined into request rows.
- [ ] AC-03: A fixture with absent `copilotCredits` reports a token-price fallback range from `models.json` and marks the row/session with `unavailable_reason`; it never fabricates a point credit value.
- [ ] AC-04: Malformed/truncated JSONL fixtures exercise the policy selected in R-2: invalid JSON, impossible patch path, missing snapshot, and truncated request are surfaced with explicit reasons or hard errors, never silently omitted from totals.
- [ ] AC-05: Running the tool against the real-store receipt named by R-1 reproduces the committed expected request count, final first-turn credits, total credits, and mid-session model switch by `requests[].modelId`.
- [ ] AC-06: `--csv` emits exactly one header and one row per request across multiple session files, with columns `session_id, session_title, created, workspace, request, request_time, model, credits, prompt_tokens, completion_tokens, elapsed_ms, prompt, summary` plus `intent` only if R-3 keeps classification in scope, and `unavailable_reason` where any cell is unavailable.
- [ ] AC-07: The default report includes replay-recovered per-turn `generatedTitle` values as `summary`; no closed-enum `intent` value is emitted unless the in-scope graph path is chosen and `--classify` passes lint/smoke through the authoring-route receipt.
- [ ] AC-08: Read-only behavior is tested: the tool opens vendor stores without writing to them and writes only to stdout or the approved `--out` target under the R-4 privacy policy.
- [ ] AC-09: Documentation updates add the `session_ledger.py` row to the session-introspection skill, document `scripts/vscode/session_ledger.py`, correct `ledger.py`'s stale "not persisted locally" premise, and close the MAP.md third-anchor finding without changing `ledger.py` attribution behavior.
- [ ] AC-10: A changelog fragment exists in `changelog/unreleased/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1 through R-5 are folded into `feature-requests/FR-898-session-accountability-report.md`. | GATE |
| C-2 | The enforcer must write failing tests before implementation for replay, malformed-store handling, CSV shape, fallback-range behavior, and read-only behavior. | GATE |
| C-3 | No lifecycle hook, daemon, scheduler, or vendor-store write may be added under FR-898. | GATE |
| C-4 | If `examples/demos/session-intent/` or any `graph.yaml`/`prompts/*.yaml` artifact remains in scope, it must be authored through the graph-authoring route and evidenced by its authoring report; direct manual graph writes are not authorized. | GATE |
| C-5 | Verbatim prompt exposure must follow the R-4 human-selected privacy policy; report artifacts must not be committed as generated output. | GATE |
| C-6 | Monthly aggregation, anomaly detection, and `ledger.py` behavioral upgrades require separate FR authority. | GATE |

Authority granted: after the revisions are folded in, implement the read-only `session_ledger.py` report, its tests, its documentation updates, and only the classification graph/merge path if the FR explicitly keeps that path in scope with the required graph-authoring evidence.
