# Judgement: FR-1155 Prompt-cache tokens in `--token-usage`

**Prior art:** [FR-1155-prompt-cache-tokens-in-token-usage.md](FR-1155-prompt-cache-tokens-in-token-usage.md) — the FR this judgement rules on, not precedent; dismissed. [FR-1152-thinking-tokens-in-token-usage.md](FR-1152-thinking-tokens-in-token-usage.md) and its judgement — the accounting precedent this FR follows, dispositioned in the FR's own Prior art line. (Added by the FR author at promotion to satisfy the FR-738 gate; not judge output. Backend: `scripts/judge.sh` copilot, 2026-11-12, round 1.)

**Verdict:** APPROVED WITH REVISIONS — extend the existing accounting boundary as proposed; implementation authority activates only after R-1 and R-2 are folded into the FR.

**Reviewed against:** Committed inputs at `6d6cf2be5af911ee8214ccfabb8e92fc87c234ed`; the consumed paths below have no working-tree diff from that commit.

- `feature-requests/FR-1155-prompt-cache-tokens-in-token-usage.md` (entire FR).
- `feature-requests/FR-1155.research.md` (entire committed spike record; not its uncommitted scripts or `results.json`).
- `docs/research-prompt-caching-2026-11-12.md` (entire desk-research record).
- `feature-requests/FR-1152-thinking-tokens-in-token-usage.md` (entire prior FR).
- `feature-requests/FR-1055-anthropic-prompt-cache-blocks-never-reach-api.md:1-200` and `feature-requests/FR-276.md:1-190` (prior-art evidence).
- `yamlgraph/utils/token_tracker.py` (entire file), `yamlgraph/cli/graph_run_helpers.py:167-180,260-274`, and `yamlgraph/executor_base.py:303-363` (cited implementation seams).
- `tests/unit/test_fr1152_thinking_tokens.py` (entire file) and `tests/unit/test_fr027_execution_safety.py:1090-1165` (cited testing precedent).
- `capabilities/CAP-17-execution-safety-guards.yaml` (entire existing registry entry).
- `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, and `.github/copilot-instructions.md:1-105,190-239` (repo doctrine; the latter also supplied as project instructions).

No author conversation, sibling-repository files, adapter working-tree changes, or uncommitted research artifacts were consumed. This is a draft, not a promoted judgement.

## What is sound

**Strongest case against:** the first consumer could attach its own callback, and introducing provider-version-specific arithmetic into a shared meter risks turning a small feature into another caching subsystem. The proposal answers that objection: the existing framework callback already owns normalised usage accounting, and the spike demonstrates a real missing decomposition, not a speculative optimisation (FR:49-64,95-107; research:40-63). Keeping both counts inside input totals and leaving prices outside YAMLGraph is the smaller solution.

| Rubric criterion | Finding and evidence |
|---|---|
| 1. Scope | Minimal production change: two counters and two conditional suffixes. The separate map-dispatch discussion grants no implementation scope (FR:95-123,138-177). |
| 2. Consistency | The input decomposition and suffix ordering agree across summary, solution, and ACs (FR:35-41,99-110,181-199). The outstanding ambiguity is whether an owed live witness closes FR-1055's verification gap; R-2 resolves it (FR:26-28,205-206). |
| 3. Measurability | Exact summary keys, literal output, registry generation, traceability, and hook exit status are mechanically checkable (FR:181-214). R-1 supplies missing cases needed to distinguish the specified rule from plausible wrong implementations. |
| 4. Feasibility | The callback already reads nested normalised metadata, and the CLI already appends a thinking suffix (`token_tracker.py:64-99`; `graph_run_helpers.py:262-274`). Existing fake-result tests exercise these exact seams without requiring a new import or fixture. The real system-segment builder already puts cache blocks in `SystemMessage.content` (`executor_base.py:348-359`). |
| 5. Architecture alignment | Extend the existing provider-independent accounting boundary, not the Anthropic executor or downstream consumers. Reuse REQ-YG-064/CAP-17; no new capability or provider abstraction is needed (FR:95-114; CAP-17's REQ-YG-064 entry). |
| 6. Single responsibility | Accounting plus a physical cache-hit witness is one concern. Warm-first scheduling, TTL configuration, prices, and consumer migrations remain separate (FR:138-177). No split is required. |
| 7. Strategic classification | **Pattern documentation / existing-abstraction completion**, under the rubric's "existing abstractions suffice" branch: the callback and CLI presentation seam already exist. This authorises filling their missing accounting fields, not inventing a new framework primitive (FR:22-31,125-135; FR-1152, Proposed Solution). |
| 8. Testability | Focused failing tests can be written against the existing handler and `_emit_success_output`, following `test_fr1152_thinking_tokens.py`. RED must fail on missing counters or output, not missing imports. Mixed-TTL and unequal-overlap cases are not yet required by the original ACs (FR:186-199); R-1 closes that gap. |

**Research and precedent gates:** the linked committed records contain genuine alternatives: normalised accounting, raw provider accounting, output-layout changes, and consumer-side pricing, with the two tempting write-arithmetic variants explicitly rejected (FR:125-135). The disagreement with desk-research R0's inline output format is dispositioned rather than silently inherited. `is_this_a_graph` is correctly answered no (FR:127). FR-1152 supplies the accounting/presentation precedent; FR-1055 fixes transport, not accounting; FR-276 supplies segment configuration. The FR reports no rejected precedent in this territory (FR:22-31).

The measurement raw-read gate is satisfied for this narrow meter: two committed call samples identify the surprising zero `cache_creation` despite a 2,927-token write, the 11-to-2,938 normalisation, and the next call's 2,927-token read (`FR-1155.research.md:40-63`). This is substantive evidence beyond a generated aggregate. The map experiment is expressly a semaphore imitation, not evidence that real map dispatch has been verified (research:78-89); no such claim or implementation is authorised here.

## Required revisions

### R-1: Make the acceptance matrix distinguish the complete accounting and display rules

Expand AC-02 with these exact write cases, retaining its current cases:

- `{ephemeral_5m_input_tokens: 300, ephemeral_1h_input_tokens: 700}` gives 1,000.
- `{cache_creation: 1200, ephemeral_5m_input_tokens: 300, ephemeral_1h_input_tokens: 700}` gives 1,200.
- `{cache_creation: 800, ephemeral_5m_input_tokens: 300, ephemeral_1h_input_tokens: 700}` gives 1,000.

The original equal-overlap case cannot distinguish `max` from choosing either representation unconditionally; the two single-TTL cases cannot detect dropping one TTL when both are nonzero (FR:99-105,186-189).

Expand AC-03 to cover `input_token_details: None` itself, not just `None` values inside a dict, and a dict containing only unrelated details. Expand AC-05 with read-only and write-only literal-line assertions: each prints only its positive suffix, omits the zero suffix, and preserves the existing prefix. Retain the both-positive, thinking-plus-cache, and no-cache literal assertions (FR:38,99-110,190-199).

### R-2: Distinguish an implemented witness from a verified live hit

Amend AC-08 and the prior-art claim at FR:26-28 to say:

- Both real calls attach the same tracker as a LangChain callback. Record the first call's write increase and the second call's read increase, not merely an unlabeled final cumulative count. Paste the actual per-call normalised cache details and tracker counts into the FR.
- An API-key skip is **owed**, never a pass. If blocked, record the named blocker in both the FR and PR body; the offline accounting work may complete, but live verification remains open.
- Claim that FR-1055's live-hit gap is closed only after the real witness passes. A skipped or owed witness does not close it.

This preserves the FR's explicit owed option while removing its unconditional closure claim (FR:26-28,115-121,205-206). It does not require a new graph, map benchmark, or mock substitute.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Two cache counters, specified `max` rule, summary keys, and decomposition docstrings in `yamlgraph/utils/token_tracker.py`. |
| D-2 | Independently conditional read/write suffixes after thinking in `yamlgraph/cli/graph_run_helpers.py`. |
| D-3 | Focused offline tests in `tests/unit/test_fr1155_cache_tokens.py`; only the two exact-dict expectations change in `tests/unit/test_fr027_execution_safety.py`. |
| D-4 | Key-guarded two-call witness in `tests/integration/test_fr1155_cache_read_live.py`, using the existing system-segment builder and LLM factory. |
| D-5 | REQ-YG-064/CAP-17 edits in `capabilities/CAP-17-execution-safety-guards.yaml`; regenerated `ARCHITECTURE.md`. |
| D-6 | FR implementation/evidence updates, a `type: feat` changelog fragment with `req: REQ-YG-064`, and a diary entry with **Seed:**. |

Not authorised: warm-first dispatch, map/compiler changes, new graph or prompt artifacts, caching warnings, cache-policy/backend work, new TTL or breakpoint configuration, dollar pricing, downstream consumer edits, `--json`/bench/async-run presentation work, dependency-floor changes, or enforcement-infrastructure changes. Existing callback use from async invocations is not disabled; the exclusion is not permission to introduce different accounting there.

## Revised acceptance criteria

- [ ] AC-01: Original two-result fixture sums 2,927 reads and 2,927 writes; input/output/call counts retain their expected values.
- [ ] AC-02: All original and R-1 write cases pass the exact `max(cache_creation, ephemeral_5m + ephemeral_1h)` rule, treating absent/`None` fields as zero.
- [ ] AC-03: Absent, empty, `None`, unrelated-only, and all-`None` input-detail cases contribute zero without raising.
- [ ] AC-04: Positive cache counts do not increase `total_input_tokens` or `total_tokens`; total remains input plus output. Handler and summary documentation state the decomposition.
- [ ] AC-05: Literal CLI-line assertions cover read-only, write-only, both-positive, thinking-plus-cache, and no-cache output; suffix order is thinking, read, write, with zero cache suffixes absent.
- [ ] AC-06: Focused unit tests use existing callable seams and function-level REQ-YG-064 decorators. A separate RED commit precedes GREEN; the FR records real RED failures attributable to missing behaviour.
- [ ] AC-07: Both existing exact-dict expectations gain the two zero-valued keys; no other edits occur in `test_fr027_execution_safety.py`. The combined three-file targeted unit command from the FR passes.
- [ ] AC-08: The integration test carries REQ-YG-064 and REQ-YG-289 decorators, skips without the key, and otherwise makes exactly two bounded Haiku 5.5 calls with the same nonce-prefixed cached segment through the existing builder. First-call write and second-call read increases are positive and evidenced as specified in R-2, or the witness is explicitly owed in FR and PR with its blocker. Owed never means verified.
- [ ] AC-09: REQ-YG-064 describes cache accounting, the `max` rule, and input decomposition; CAP-17's `fr:` becomes `legacy, FR-027, FR-1152, FR-1155`. Regeneration, strict requirement coverage, changelog fragment, and diary **Seed:** requirements pass.
- [ ] AC-10: `pre-commit run --files <changed files>` passes, subject only to the FR's recorded RED-commit pytest skip. Hook bypasses are not authorised.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| GATE-1 | Fold R-1 and R-2 into the FR before production implementation; preserve the frozen scope above. This draft must pass through the existing promotion process; writing it is not promotion. | GATE |
| GATE-2 | Commit RED and GREEN separately and record their evidence. Preserve the existing thinking tests and run the FR's combined targeted unit command. | GATE |
| GATE-3 | Human spend question: does the operator authorise the two live Haiku calls estimated at under one cent? An estimate and an API key are not spend approval. Without established approval, do not call the paid API; use the explicit owed path. | GATE |
| GATE-4 | Never present a skipped witness, replayed spike, mock, or semaphore imitation as a passing live test or a closed FR-1055 verification gap. | GATE |
| GATE-5 | No changes to hooks, CI, judgement routing, dependencies, other repositories, or caching behaviour. Keep unrelated working-tree changes untouched; merge remains the operator's decision. | GATE |

Authority granted: conditional authority only, after revision folding and judgement promotion, to implement D-1 through D-6; live execution additionally requires GATE-3, and an owed witness leaves live verification open.
