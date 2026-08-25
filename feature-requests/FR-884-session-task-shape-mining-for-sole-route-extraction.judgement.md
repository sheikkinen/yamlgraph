# Judgement: FR-884 Chat-Session Task-Shape Mining for Sole-Route Extraction

**Prior art:** FR-362/FR-364 dispositioned in the FR itself (single
governed-run process mining vs multi-day interactive chat surface;
extractor schema reusable). FR-814 (Enforced) extracts a knowledge graph
from the *FR corpus* for the prior-art hook — different corpus (FRs, not
chat sessions), different consumer (duplicate detection, not cost/route
extraction); no overlap. The FR-884 FR itself is the subject of this
judgement, not prior art.

**Verdict:** APPROVED WITH REVISIONS — the investigation target is real, timely, and strategically aligned, but authority activates only after the FR satisfies the measurement raw-read gate, freezes the executable data contract, and hardens the public-repo privacy boundary.

**Reviewed against:** `feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md`; `scripts/vscode/README.md`; `scripts/vscode/ledger.py`; `scripts/vscode/portrait.py`; `scripts/vscode/now.py`; `scripts/extract_copilot_events.py`; `feature-requests/FR-362-copilot-instrumentation-process-mining-poc.md`; `feature-requests/FR-363-per-node-otel-scoping-in-copilot-node.md`; `feature-requests/FR-364-copilot-instrumentation-gap-closure.md`; `feature-requests/FR-853-agent-instrument-registry.md`; `feature-requests/FR-853-agent-instrument-registry.judgement.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.judgement.md`.

## What is sound

The problem is evidenced, not speculative. The FR preserves the invoice totals and model-level overage table (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:34-53`), and the cited diary independently records the same billing table (`docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md:8-27`). The diary also supports the FR's central premise: Fable 5 and GPT-5.6 Sol appear in zero graphs, hooks, or adapters and therefore represent the ungoverned interactive surface (`docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md:44-48`), while governed paths sum to under 10% of spend and 83% of overage flows through interactive sessions (`docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md:50-58`).

The proposed investigation fits existing repo doctrine. The `is_this_a_graph` question already requires agents to consult graph task-shape descriptions before falling back to scripts or subagents (`.github/copilot-instructions.md:133-133`), and FR-853 made that agent-visible through `Task shapes:` graph descriptions rather than a new registry (`feature-requests/FR-853-agent-instrument-registry.md:69-76`, `feature-requests/FR-853-agent-instrument-registry.judgement.md:23-33`). FR-884 supplies the missing empirical side: which interactive shapes recur often enough to justify sole routes (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:96-107`).

The prior-art distinction from FR-362/363/364 is mostly correct. FR-362 mined one governed Copilot run and explicitly kept raw artifacts local under ignored output paths (`feature-requests/FR-362-copilot-instrumentation-process-mining-poc.md:11-15`, `feature-requests/FR-362-copilot-instrumentation-process-mining-poc.md:52-56`); FR-363 scoped OTel per YAMLGraph copilot node (`feature-requests/FR-363-per-node-otel-scoping-in-copilot-node.md:9-15`); FR-364 hardened the normalized event schema for process mining (`feature-requests/FR-364-copilot-instrumentation-gap-closure.md:83-100`). FR-884 is a different surface: editor chat sessions across many days, joined by session id and ranked by cost/frequency/extractability (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:21-26`, `feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:118-147`).

The implementation approach reuses the correct local seams. `scripts/vscode/README.md` documents chatSessions as full request logs with model and token data, debug logs as price-sheet sources, and chronicle as session summaries/files/refs (`scripts/vscode/README.md:73-83`). It also records session UUID as the universal join key across chatSessions, transcripts, resources, debug logs, session memory, and OTel tap (`scripts/vscode/README.md:127-135`). `ledger.py` already parses chatSessions and price sheets into per-model request/token/cost ranges (`scripts/vscode/ledger.py:43-92`, `scripts/vscode/ledger.py:141-157`), so extending `scripts/vscode/` is aligned with existing patterns.

Strategic classification: **Contrib/example investigation**. This is not yet a framework primitive because it produces evidence and candidate proposals, not reusable runtime semantics. It may graduate follow-up framework or sole-route work only after the taxonomy proves recurring, bounded task shapes.

## Required revisions

### R-1: Satisfy the measurement raw-read gate before implementation authority

Move the Phase-0 raw-read requirement from an implementation acceptance criterion into the FR evidence section before enforcement begins. Repo doctrine withholds authority for measurement/metric-tooling FRs until the FR evidences raw-output reads with cited samples and concrete surprising details (`.github/copilot-instructions.md:233-233`), and judge doctrine says missing essential context is an FR defect rather than permission to infer the author's intent (`.github/skills/judge-fr/doctrine.md:16-24`). FR-884 currently plans `K >= 10` raw transcript reads in Phase 0 (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:110-117`) but has not yet recorded the reads. Add a sanitized raw-read evidence table before authority activates: session id hash/pseudonym, sampled stratum, date bucket, task-shape clue, one non-identifying surprising detail, and privacy classification. Do not include transcript excerpts.

### R-2: Freeze one measurement window and one executable join contract

Replace the mixed "60-90 days" investigation window with one exact window and timezone, for example "2026-06-26 through 2026-08-25 inclusive, local time." The FR asks for 60-90 days in the investigation question (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:98-99`) but the acceptance threshold uses "last-60-day" token volume (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:176-176`). Also replace `Chronicle DB (session_store_sql)` with a committed executable surface: either extend `scripts/vscode/portrait.py`/a new `scripts/vscode/session_shapes.py` to read `globalStorage/github.copilot-chat/session-store.db` read-only as `portrait.py` already does (`scripts/vscode/portrait.py:58-85`), or explicitly mark chronicle fields unavailable and exclude them from mandatory joins. The enforcer must not depend on the chat-only `session_store_sql` tool because it is not a committed repo script.

### R-3: Fold FR-874's public-repo privacy precedent into the output schema

Strengthen the privacy constraint from "no transcript excerpts" to a mechanical publication rule. FR-874's rejection establishes that this repo is public, workspace-derived data can contain customer-operational facts, and future proposals must verify repo visibility and treat classification as a boundary requirement (`feature-requests/FR-874-cross-device-agent-memory-sync.md:3-30`). FR-884 already acknowledges the public-repo/customer-workspace risk (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:158-164`), but its committed deliverables still include shapes, counts, cost ranges, and `.chaplain/inbox/` proposals (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:139-147`). Revise the FR to require: repo visibility recorded before any committed research artifact; no exact customer/project names, file paths, titles, prompt snippets, or transcript excerpts; aggregation buckets with `session_count < 3` collapsed into `rare/other` in public artifacts; and a meaning-level privacy checklist recorded in the FR before commit.

### R-4: Resolve the classifier-graph optionality contradiction

Make the classifier path either required or forbidden. Phase 2 says sessions are classified with a map-node graph pinned to a cheap model (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:124-130`), while AC-07 says "If a classifier graph is built" (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:183-184`). Because repo doctrine requires YAMLGraph/LLM over complex regex logic (`.github/copilot-instructions.md:31-31`) and `is_this_a_graph` fires for N-items-by-LLM classification (`.github/copilot-instructions.md:133-133`), freeze this as: LLM-assisted bulk classification must use a classifier graph authored via the governed graph-authoring route, with an explicit cheap model pin, lint, smoke record, and sanitized fixture/sample output. Manual classification is allowed only for the Phase-0 raw-read seed and must not be used to claim the 80% token-volume threshold.

### R-5: Make proposal submission safe and non-recursive

Constrain the Top-3 `.chaplain/inbox/` deliverable to proposal drafts that contain only sanitized shape labels, aggregate counts/ranges, extractability verdicts, pinned-model recommendation, and first consumer. The FR correctly keeps route implementation out of scope (`feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md:149-154`), but writing to `.chaplain/inbox/` can trigger follow-up automation (`.github/copilot-instructions.md:195-201`). Add a gate that FR-884 may file follow-up proposals but must not implement, author, judge, or review any extracted route, and must not include private transcript-derived specifics in the proposals.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-884-session-task-shape-mining-for-sole-route-extraction.md` revised with R-1 through R-5 before enforcement |
| D-2 | Sanitized raw-read evidence table in the FR or `research/FR-884-raw-read-log.md` with no transcript excerpts |
| D-3 | `scripts/vscode/session_shapes.py` or equivalent stdlib-only read-only extension under `scripts/vscode/` for inventory/join/classification/ranking support |
| D-4 | Optional classifier graph and prompt artifacts, only if authored through the governed graph-authoring route and explicitly model-pinned |
| D-5 | `research/FR-884-session-task-shapes.md` sanitized ranked candidate report |
| D-6 | Up to three sanitized one-paragraph follow-up proposals in `.chaplain/inbox/`, or an explicit "none extractable" section in the research report |
| D-7 | Targeted tests/fixtures for any new or materially changed script logic |
| D-8 | FR implementation-status update and `docs/diary/` reflection for the enforcement session |

Not authorized: implementing any extracted route; repinning `validate-session.yaml`; new telemetry instrumentation; remote telemetry export; committing raw transcripts, transcript excerpts, exact session titles, customer/project names, or local absolute paths; using `session_store_sql` as the only reproducible data-access mechanism; changing judge/review/authoring doctrine; live hooks or PreToolUse nudges; broad writes outside `scripts/vscode/`, `research/`, the FR, optional governed graph artifacts, tests, changelog/capability files if required, and diary reflection.

## Revised acceptance criteria

- [ ] AC-01: The FR records the exact analysis window and timezone and uses that same window for raw-read sampling, token-volume denominator, taxonomy coverage, and candidate ranking.
- [ ] AC-02: Before implementation authority activates, a sanitized raw-read log exists for at least 10 full sessions read end-to-end, including the 5 highest-token sessions in the window plus 5 randomly sampled sessions; each row records a non-identifying surprising detail, sampled stratum, date bucket, and privacy classification, with zero transcript excerpts.
- [ ] AC-03: A stdlib-only read-only script under `scripts/vscode/` inventories chatSessions/debug-log price sheets/audit traces and, if used, chronicle SQLite by session id; missing optional sources are reported as unavailable rather than silently substituting all sessions or dropping them.
- [ ] AC-04: Tests with synthetic fixtures prove the script parses session ids, models, prompt/output tokens, request timestamps, and cost ranges without reading the operator's real VS Code stores.
- [ ] AC-05: The taxonomy contains no more than 12 shapes, each with one-line inclusion criteria and an extractability verdict against the five prompt-contract clauses: one judgement, closed inputs, one validator-covered output shape, stateless, bounded.
- [ ] AC-06: At least 80% of interactive token volume in the frozen window is classified into the taxonomy, or the research report explicitly records the deficit, the unclassified fraction, and why the taxonomy is not stable enough for extraction.
- [ ] AC-07: The ranked candidate table reports sanitized shape label, session count, token/cost range, extractability verdict per clause, existing `Task shapes:` graph overlap, and `builders_never_call` witness rate.
- [ ] AC-08: Public committed artifacts include no transcript excerpts, exact session titles, customer/project names, local absolute paths, or singleton-identifying rows; buckets with `session_count < 3` are collapsed to `rare/other`, and the FR records a completed meaning-level privacy review.
- [ ] AC-09: If LLM-assisted bulk classification is used, the classifier is a YAMLGraph map-style graph authored through the governed graph-authoring route, pins a cheap model explicitly, lints clean, has a smoke record, and writes only sanitized outputs.
- [ ] AC-10: Up to three follow-up proposals are filed to `.chaplain/inbox/` only after passing AC-08; each proposal contains sanitized aggregate evidence, pinned-model recommendation, and first consumer, and implements no route under FR-884. If no candidate clears the extractability bar, the research report states "none extractable" with evidence.
- [ ] AC-11: FR-884 is updated with implementation status, decisions, deviations, exact commands run, and links to committed research/proposal artifacts; a diary reflection is included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the FR before implementation authority activates. | GATE |
| C-2 | Treat all session transcripts, titles, tool outputs, absolute paths, and customer/workspace identifiers as private source material; raw reads and intermediate dumps stay in `tmp/` or outside git. | GATE |
| C-3 | Verify and record repo visibility before committing research output; public-output rows must be sanitized and non-singleton as specified in AC-08. | GATE |
| C-4 | Keep all session stores read-only; tests must use synthetic fixtures, never the operator's real VS Code stores. | GATE |
| C-5 | If graph or prompt artifacts are created or materially modified, use the governed graph-authoring route and honor its lint/smoke/report contract. | GATE |
| C-6 | Do not invoke judge/review routes, implement extracted routes, repin existing production graphs, add telemetry instrumentation, or change hook/CI/doctrine policy under FR-884. | GATE |
| C-7 | Follow-up `.chaplain/inbox/` proposals must be sanitized drafts derived from aggregate evidence only; no transcript-derived specifics or customer-identifying facts may enter the inbox. | GATE |

Authority granted: after revisions are folded into the FR, enforcement may conduct a read-only, privacy-gated session-shape mining investigation, produce sanitized aggregate research, and file sanitized follow-up proposals for separate route-extraction FRs.
