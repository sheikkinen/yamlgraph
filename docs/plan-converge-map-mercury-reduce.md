# Plan: FR Convergence Check — map(mercury)-reduce evaluation

**Date:** 2026-08-29
**Status:** REFUTED same day — DO NOT BUILD (see §0). Kept as precedent per the
FR-614/FR-737 pattern: a rejected proposal is prior art that future proposals
re-entering this territory must distinguish themselves from.
**Origin:** [research-agentic-sdlc-providers-2026-08-29.md](research-agentic-sdlc-providers-2026-08-29.md)
— Spec Kit's `/converge` (assess codebase vs spec/plan/tasks, append remaining
work as new tasks, repeat until Converged) appeared to be the one published
primitive the FR lifecycle lacks.

## 0. Refutation (re-analysis, 2026-08-29)

1. **`/converge` is a compensating control, not a primitive.** Spec Kit needs
   post-hoc convergence because its spec is the living source of truth and it
   has no merge-blocking traceability gates. Here, convergence is enforced
   continuously: criteria become REQ-tagged tests re-verified by
   `req-coverage-strict` + CI on every commit — strictly stronger than
   periodic re-assessment. Importing `/converge` imports the weaker mechanism
   into the system that has the stronger one.
2. **The FR is an expired contract by design** (`constraint_over_code`):
   durable claims live in Scripture + CAP/REQ + tests; the review graph checks
   the FR against the diff at merge, then the FR retires as a historical
   record. Assessing the current tree against expired contracts re-litigates
   history; the mature move on stale claims is CAP retirement (FR-465/466),
   not convergence machinery.
3. **No named incident for the residual slice** (untested prose criteria
   drifting post-merge) — fails `would_you_use_this` / `value_proposition`.
   The trigger was survey envy: `growth_as_default` in a research costume.
4. **`--emit-inbox` is negative value as scoped**: FR-851's first run produced
   235 partials dominated by an instrument gap; auto-filing detector output
   without a premise gate is the exact `unchallenged_premise` asymmetry the
   Scripture flags for Inquisitor `--propose`.

What survives: nothing requiring an FR. Mercury-as-flag needs no change
(`--provider inception` already works on the FR-860 contract); criteria-mode
auditing waits for a first incident that names it.

---

The original evaluation follows, unmodified, as the record of what was
proposed and why it looked plausible.

**Ideal result:** for any merged FR, one command answers "is every acceptance
criterion actually satisfied in the codebase today?" and files the gaps as
actionable inbox proposals — cheap enough to sweep all recent FRs nightly.

---

## 1. Applicability evaluation: map(mercury)-reduce

Proposed shape: fan out over acceptance criteria with `type: map` +
`provider: inception` (Mercury, default model `mercury-2` per
`yamlgraph/config.py`), reduce verdicts into a convergence report.

| Property | Fit | Notes |
|---|---|---|
| Independence of items | ✅ | Acceptance criteria are judged independently; no cross-criterion state. Native map-reduce shape (`is_this_a_graph`). |
| Bounded per-item context | ✅ *if evidence is pre-gathered* | Mercury cannot explore the repo (llm nodes have no tools). A deterministic Python tool node must build an **evidence bundle** per criterion first: matching tests (`@pytest.mark.req`), changelog fragments, FR Implementation Status section, grep hits for criterion keywords. Normalize at the boundary — the LLM judges a bundle, it does not search. |
| Task difficulty vs model strength | ⚠️ | Per-criterion verdict over a curated bundle is a constrained judgement — within Mercury's reach. But `plausible_wrong_answer` looms: a fast model will happily verdict "satisfied" on shape. Cures: (a) verdict schema requires **cited evidence lines**; (b) empty evidence bundle mechanically caps verdict at `unverifiable` in code, never `satisfied` (junk_drawer_cap pattern — cap at the boundary before the model votes). |
| Throughput economics | ✅ | Mercury's diffusion speed (~5-10x autoregressive) is the whole point: a nightly sweep of ~30 recent FRs × ~6 criteria = ~180 calls is only viable at Mercury cost/latency. This is the correct use of the provider. |
| Reduce step | ✅ | Deterministic Python reduce: aggregate verdicts → report + write `.chaplain/inbox/converge-<fr>.md` proposals for `missing`/`partial` items. No LLM needed in reduce (Spec Kit appends tasks; we append inbox proposals — existing intake, no new lifecycle). |
| Escalation | ✅ (deferred) | Optional second tier: criteria verdicted `missing` get one sonnet re-check before filing, to cut false-positive proposals. Not MVP. |

**Verdict: applicable — and substantially already implemented.** The shape is
genuinely map-reduce and the LLM step must be reduced to bundle-judgement over
deterministically gathered evidence. A design that asks the model to "assess
the codebase" directly is not applicable — that is agent work, not map work.

## 1b. Prior art disposition (checked 2026-08-29)

The proposed pattern already exists as the **requirement-witness-audit stack**
(FR-850 → FR-851 → FR-860), stage for stage:

| Proposed converge stage | Existing implementation |
|---|---|
| Deterministic evidence bundles per claim | `scripts/req_audit_questions.py` constructor + FR-850 coverage-context boundary (hard refusal on missing/poisoned recording — the "cap at the boundary" proposal, already built) |
| `map` + cheap LLM judging bundles, verdict enum | `examples/demos/req_witness_audit/graph.yaml` — `type: map` over batches, haiku-tier, `yes/partial/no`, raw result persisted per batch (`read_raw_output_first` designed in) |
| Deterministic reduce → report | `scripts/req_audit_report.py` — reconciliation + ranked report, git-SHA-stamped artifacts |
| One-command runner + cadence | `scripts/req_audit.sh` (FR-860, monthly) |
| Deterministic pre-ring | `req_coverage.py --strict` (FR-107/145 phantom detection) + `examples/demos/req-cross-check` demo |

Other precedents: `examples/demos/corpus_census` (map over file corpus with
per-item schema verdicts), `examples/demos/diary_index` (map + llm extraction
over docs/diary/).

**Genuine deltas — the only new scope this plan may claim:**

1. **Unit of assessment.** req-audit grades REQ↔witness-test substance;
   converge grades FR acceptance criterion↔current tree. The uncovered slice
   is criteria that never became REQs — docs, behavioral, and scope statements.
2. **Output routing.** req-audit emits a ranked report for operator triage;
   converge appends gaps as `.chaplain/inbox/` proposals (the Spec Kit
   "append remaining work" primitive) and a CONVERGED/NOT-CONVERGED verdict.
3. **Mercury is a flag, not an architecture.** FR-860 froze the
   `--model/--provider` CLI contract (no env indirection); mercury is
   `--provider inception --model mercury-2`. FR-851 pinned haiku with K-sample
   raw-read evidence; a mercury swap requires the same raw read before any
   aggregate is trusted, and is worthless if mercury's verdicts need haiku
   re-checks anyway — measure first.

Key difference from the existing **review graph** (`scripts/review.sh`): review
judges a PR diff at merge time; converge judges the *current tree* against
frozen scope any time after — complementary, not duplicates. Key difference
from **req_coverage.py**: that proves a tagged test *exists*; converge asks
whether the criterion is *satisfied* (substance_over_presence).

## 2. Pipeline design

```
select_frs (python)      # input: --var fr=FR-XXX | last N merged FRs
  → parse_criteria (python)   # extract Acceptance Criteria checklist items from FR md
  → gather_evidence (python)  # per criterion: req-tagged tests, changelog frags,
                              #   FR impl-status, keyword grep hits → EvidenceBundle
  → judge_criteria (map + llm, provider: inception)
                              # schema: {criterion_id, verdict: satisfied|partial|
                              #   missing|unverifiable, evidence_citations, remaining_work}
  → cap_verdicts (python)     # empty bundle ⇒ unverifiable; citation must exist in bundle
  → reduce_report (python)    # convergence report md + inbox proposals for gaps
```

Convergence condition (Spec Kit parity): report ends `CONVERGED` when zero
`missing`/`partial`; otherwise lists filed proposals.

## 3. Barebones plan (revised: extend the req-audit stack, no new pipeline)

**Topic: criteria-mode constructor**

- `scripts/req_audit_questions.py` — CHANGED (or sibling `converge_questions.py`)
  - `--criteria-mode --fr FR-XXX`: parse Acceptance Criteria checklist items
    from the FR md; per criterion gather evidence (req-tagged tests, changelog
    fragments, FR Implementation Status, keyword grep) into the SAME batch
    format `req_witness_audit` consumes. Empty bundle marked at construction.

**Topic: map graph**

- `examples/demos/req_witness_audit/graph.yaml` — REUSED as-is if the batch
  payload generalizes; a criteria-specific prompt variant only if the FR-851
  prompt's Stage-1 framing measurably distorts verdicts (its known weakness —
  see FR-860 Raw Output Read item 3). Any graph/prompt change goes via
  `scripts/author.sh` (sole route, FR-767) — this plan ships no YAML.

**Topic: reduce + intake**

- `scripts/req_audit_report.py` — CHANGED: `--emit-inbox` writes
  `converge-<fr-slug>.md` proposals to `.chaplain/inbox/` for `missing`/`partial`
  verdicts and prints CONVERGED when none (existing intake contract unchanged).

**Topic: runner**

- `scripts/req_audit.sh` — CHANGED: `--fr FR-XXX` flag wires the three phases
  in criteria mode; model/provider flags unchanged (mercury = flag value).

**Testing (MVP gate):**

1. Unit: criteria parsing on 3 real FR files (checked-in fixtures); empty
   evidence bundle forces `unverifiable` in the report reconciler (condemning
   test first).
2. Smoke: run `req_witness_audit` graph on criteria-mode batches for one
   deliberately-converged FR (expect CONVERGED) and one FR with a known
   retired/partial criterion (expect a proposal file) — `demo-output.log` in
   diff if the demo dir changes (demo-gate).
3. Read raw output: cat K raw verdicts per model (haiku baseline, then mercury
   candidate) before trusting any aggregate (`read_raw_output_first`; the
   Judge's measurement-FR mandate applies — this IS a measurement FR).

## 4. Non-goals / open questions

- Non-goal: replacing review.sh or req_coverage — converge is a third, later
  boundary.
- Non-goal: auto-enforcing gaps; output is proposals, human/chaplain triage.
- Open: criterion granularity — some FRs have prose criteria, not checklists;
  parse_criteria may need a tolerant fallback (whole-section-as-one-criterion)
  rather than a smarter parser (`regex_fourth_exclusion` warning).
- Open: sweep cadence — attach to Inquisitor's ~24h cycle vs on-demand only.
  First consumer question (`would_you_use_this`): on-demand `--fr FR-XXX` is the
  named first trigger; nightly sweep only after the on-demand form proves signal.
- Open: mercury economics — only worth pursuing if the haiku-pinned pipeline is
  actually cost/latency-bound at the intended cadence; FR-851's full 412-REQ run
  already completed on haiku, so the burden of proof is on mercury.

**Next step:** none — refuted, see §0. Do not submit to the inbox; any future
proposal in this territory must disposition this document first.
