# Judgement: FR-893 Diary Trap Census — Recurrence by Measurement, Not Memory

**Verdict:** APPROVED WITH REVISIONS — the census is a sound repo-process consumer of FR-892, but authority activates only after the FR adds the missing ideal-result section, satisfies the measurement raw-read gate, and freezes the public-artifact privacy contract.

**Reviewed against:** feature-requests/FR-893-diary-trap-census.md; feature-requests/FR-893.research.md; feature-requests/research-briefs/diary-trap-recurrence-census.md; feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md; feature-requests/FR-892-corpus-census-pipeline-injected-adapters.judgement.md; feature-requests/FR-254-diary-index-graph.md; feature-requests/FR-593-story-level-vocabulary-pre-analysis-stage.md; feature-requests/FR-890-research-sole-route-closed-input-alternatives.md; capabilities/CAP-113-chaplain-research-step.yaml; docs/mercury-census/findings.md; docs/mercury-census/canary-diary-census.md; .chaplain/graphs/philosopher/graph.yaml; examples/demos/corpus_census/README.md; examples/demos/corpus_census/tools.py; examples/demos/corpus_census/adapters/corpus_adapters.py; .github/skills/judge-fr/doctrine.md; .github/skills/judge-fr/judgement.template.md; .github/copilot-instructions.md.

## What is sound

The problem is real and well evidenced. The brief states that diary recurrence counting is currently manual and memory-based, biased toward recent/personally witnessed traps, and lacks a mechanism that reads every entry and reports trap frequency with citations (feature-requests/research-briefs/diary-trap-recurrence-census.md:8-21). It also names concrete witnessed incidents: stale `tmp/msg.txt`, line-pinned gate references, heading-consumption edits, and the unbuilt `diary_graduation_pipeline` seed (feature-requests/research-briefs/diary-trap-recurrence-census.md:52-68).

The proposal conforms to existing architecture before extending it. FR-892 already shipped the reusable corpus-census shape as discover -> extract -> cheap map -> LLM-free reducer, with runtime tool binding and ledger outputs (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.md:29-39, 64-95). The implemented demo exposes `--tool discover=...` and `--tool extract=...` binding (examples/demos/corpus_census/README.md:1-14), and its reducer already validates ledger rows, rejects missing findings and error-string judgements, and writes markdown plus JSONL artifacts (examples/demos/corpus_census/tools.py:16-48, 51-96, 103-165). Reusing this skeleton through diary-specific manifests is the minimal path; the FR correctly forbids new graph YAML (feature-requests/FR-893-diary-trap-census.md:67-70).

The research record satisfies the local research gate in substance. It contains five personas, preserves disagreement, dispositions os-infra and subtractionist dissent as constraints, cites FR-892/FR-254/philosopher precedents, and answers `is_this_a_graph` per row (feature-requests/FR-893.research.md:1-17). The canary precommitment independently names the expected answer: per-entry cheap-LLM census over the full diary corpus with deterministic recurrence aggregation, plus vocabulary normalization because trap labels drift (docs/mercury-census/canary-diary-census.md:5-17).

Strategic classification: **Contrib/process automation**, not a new framework primitive. The FR has one primary repo-process use case, and the existing FR-892 abstraction fits it. Its value is high because it makes Scripture graduation evidence measurable, matching the repo process rule that recurrence drives FRs and graduations (.github/copilot-instructions.md:148-171), but it should remain a corpus-census consumer plus deterministic reducer rather than expand the framework.

## Required revisions

### R-1: Add the missing Ideal Result section before Proposed Solution

Insert `## Ideal Result` between `## Problem` and `## Proposed Solution`. It must state the end state in checkable terms: a maintainer can run one bounded diary census, inspect committed `docs/diary/census/` artifacts, and attach a candidate row with label, count, first/last seen, and entry citations to a `.chaplain/inbox` proposal without relying on agent memory. This is required by repo doctrine, which says every plan must state the Ideal Result before Proposed Solution (.github/copilot-instructions.md:229-233).

### R-2: Satisfy the measurement raw-output-read gate before authority

Add a `## Raw-output read evidence` section to the FR before enforcement. Because this is a measurement/census FR, the judge doctrine requires evidenced `read_raw_output_first` before authority for metric-tooling plans (.github/skills/judge-fr/doctrine.md:112-117; .github/copilot-instructions.md:229-233). The section must cite at least five raw diary-entry samples and record one concrete surprising detail from each that a generated summary could not prove. At minimum include samples covering the two canary families and the heading-consumption witness, for example the stale `tmp/msg.txt` recurrence in docs/diary/2026-08-25-the-census-taker-reads-its-own-ledger.md:28-33, line-number gate drift in docs/diary/diary-2026-08-26-reflection-fr-892-the-skeleton-learns-to-accept-guests.md:33-36 and :54-56, and heading-consumption edits in docs/diary/diary-2026-08-26-the-pattern-outgrew-its-name.md:37-44.

### R-3: Freeze a public-safe evidence artifact contract

Revise the committed-artifact requirement so public outputs never quote sensitive diary/customer facts. The research brief explicitly constrains public outputs not to surface customer facts quoted inside diary entries (feature-requests/research-briefs/diary-trap-recurrence-census.md:45-46), while the FR currently commits a full ledger plus evidence spans under `docs/diary/census/` (feature-requests/FR-893-diary-trap-census.md:31-40, 76-80, 95). Freeze the artifact split mechanically: committed recurrence tables and inbox proposals may contain canonical label, normalized family, count, entry path, line range or heading, first/last seen, abstention counts, and a short non-sensitive rationale; raw evidence spans either must pass a deterministic redaction/public-safe check before being committed or must remain in an uncommitted run artifact referenced only by summary metadata.

### R-4: Define recurrence counting semantics for canaries

Clarify whether counts mean distinct diary entries, distinct evidence spans, or distinct incidents within an entry. The summary says the aggregator counts across entries and emits entry citations (feature-requests/FR-893-diary-trap-census.md:32-34, 76-80), but AC-04 requires both canary traps to surface with at least three citations each (feature-requests/FR-893-diary-trap-census.md:94), while the line-pinned evidence may include several incidents inside fewer entries (docs/diary/diary-2026-08-26-reflection-fr-892-the-skeleton-learns-to-accept-guests.md:33-36, 54-56). Pick one unit and make the tests enforce it. If the graduation bar is distinct entries, the canary threshold must be expressed as distinct entry citations; if the bar is incidents, the ledger must preserve multiple evidence spans per entry.

### R-5: State the FR-892 dependency as an enforcement gate

Move the Related-line dependency into `Conditions for enforcement`: this FR may enforce only after FR-892 is merged into the branch being enforced, or while explicitly based on the FR-892 branch with its slot-binding and `corpus_census` artifacts present. FR-893 depends on the `corpus_census` graph and adapter convention (feature-requests/FR-893-diary-trap-census.md:67-87, 123-124), and FR-892's judgement freezes the exact surfaces this FR consumes (feature-requests/FR-892-corpus-census-pipeline-injected-adapters.judgement.md:45-88).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Diary discovery manifest/tool under `examples/demos/corpus_census/adapters/` or an adjacent manifest directory, globbing `docs/diary/*.md` or the actual committed diary layout, bounded and sorted |
| D-2 | Diary extraction manifest/tool that reads one diary entry, caps size, preserves item reference, and exposes only content needed by the rubric |
| D-3 | Diary trap/heuristic rubric prompt/config consumed by the existing `examples/demos/corpus_census/graph.yaml`, with typed output for canonical label, evidence span or abstention, and source index/item reference |
| D-4 | LLM-free recurrence aggregator consuming the census JSONL ledger and emitting a public-safe recurrence table under `docs/diary/census/` |
| D-5 | Canary gate for the stale-commit-message-file family and line-pinned-gate family, using the frozen count unit from R-4 |
| D-6 | Draft `.chaplain/inbox/` proposal(s) generated only from canary-valid candidate rows at the graduation threshold |
| D-7 | Thin manual wrapper `scripts/diary_census.sh` with run cost/duration recording |
| D-8 | Deterministic tests, changelog fragment, FR implementation update, and diary reflection |

Not authorized: auto-graduation; direct Scripture edits; daemon/watch mode; cross-project diary sweeps; migration or rewrite of diary-index; modification of `.chaplain/graphs/philosopher`; new or materially modified graph YAML or prompt YAML outside the graph-authoring route; generic census framework changes beyond what FR-892 already authorized; enforcement-infrastructure changes without human review.

## Revised acceptance criteria

- [ ] AC-01: RED first — failing tests cover recurrence aggregation before implementation: grouping by canonical label, preserving citations, threshold filtering, label-without-citation rejection, abstention rows excluded from counts, and canary failure.
- [ ] AC-02: FR text includes the required `## Ideal Result` and `## Raw-output read evidence` sections before enforcement; the raw-read section cites at least five diary-entry samples with concrete details, including both canary families.
- [ ] AC-03: Diary discovery and extraction manifests/tools bind to the unchanged FR-892 `corpus_census` graph; the full committed diary corpus run uses only manifests plus rubric/config and no new graph YAML.
- [ ] AC-04: The rubric output schema requires canonical label, evidence span, item reference/source index, confidence, abstention marker, and abstention reason; prompt/config includes diary-index vocabulary as normalization hints and requires abstention when no named trap/heuristic is present.
- [ ] AC-05: The recurrence aggregator is LLM-free; deterministic tests prove grouping, threshold counts, citation preservation, first/last seen calculation, label-without-citation rejection, public-safe artifact output, and abstention rows passing through uncounted.
- [ ] AC-06: Canary gate fails loudly on a fixture ledger missing either known-truth family; the real full-corpus run surfaces stale-commit-message-file and line-pinned-gate according to the R-4 count unit and records the observed counts/citations in the FR implementation record.
- [ ] AC-07: Committed artifacts under `docs/diary/census/` include the census ledger or public-safe derivative, recurrence table, and run evidence with model, prompt/config version, cost, duration, corpus bounds, and git SHA/provenance.
- [ ] AC-08: At least one real graduation-candidate draft is written to `.chaplain/inbox/` only after the canary gate passes; the draft includes canonical label, count, entry citations, and a statement that graduation judgement remains outside this FR.
- [ ] AC-09: Changelog fragment, requirement/capability wiring if new tests require it, `@pytest.mark.req(...)` on new tests, FR status/update notes, and diary reflection are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-5 are folded into FR-893. | GATE |
| C-2 | FR-892's slot-binding and `corpus_census` artifacts must be present on the enforcement branch before this FR runs; otherwise enforcement stops. | GATE |
| C-3 | No new or materially modified graph YAML or prompt YAML is authorized unless routed through the graph-authoring adapter and backed by `tmp/draft-authoring-report.md`; the preferred implementation is manifests/config plus code reducer only. | GATE |
| C-4 | Public committed artifacts must not expose sensitive diary/customer facts; raw evidence spans require deterministic redaction/public-safety validation or must remain uncommitted. | GATE |
| C-5 | The aggregator is deterministic and LLM-free; no LLM call may participate in grouping, thresholding, canary validation, or proposal emission. | GATE |
| C-6 | Candidate proposals may be generated, but Scripture edits and auto-graduation are forbidden under this FR. | GATE |
| C-7 | Any changes to hooks, CI, judge/review doctrine, or Chaplain runtime behavior require explicit human review before merge. | GATE |

Authority granted: after the required revisions are folded into FR-893, the enforcer may build the diary-specific corpus-census manifests/rubric binding, deterministic recurrence aggregator, public-safe census artifacts, canary gate, and draft inbox proposal generation within the frozen scope above.

**Prior art:** dispositioned in FR-893 header (FR-892/254/593 positive precedent; philosopher graph untouched).
