# Feature Request: person-profile census fails closed below a classification-coverage floor and stamps the population on the brief

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-09-04
**Classification:** Contrib/example (FR-983 judgement R-2 — a policy and
rendering correction inside one demo's reducer/render tail)
**First consumer / first event:** the reader of the next
`tmp/*.brief.md` the person-profile census writes — on 2026-09-04 that
reader received a 102-line profile of 147 of 259 PRs with no statement
that 43% of the population was missing.
**Research:** [research-briefs/fr983-map-concurrency-coverage-gate-brief.md](research-briefs/fr983-map-concurrency-coverage-gate-brief.md)
(committed `9a490c8c`, preflight exit 0) and the apportioned in-body
alternatives table below — the FR-890 R-6 record inherited from
[FR-983](FR-983-map-concurrency-and-census-coverage-gate.md), whose
judgement split this deliverable out. The sole research route was down
(ddgs egress) when the parent was filed; the brief is committed for
re-running.
**Prior art:** [FR-983-map-concurrency-and-census-coverage-gate.md](FR-983-map-concurrency-and-census-coverage-gate.md)
[Judged — SPLIT] — the parent incident record; this FR is its
Successor B and inherits its frozen scope verbatim.
[FR-962-person-profile-census-authored-prs.md](FR-962-person-profile-census-authored-prs.md)
— owns the census; its ideal-result item 5 promised "completeness"
enforced before rendering and item 2 a coverage number; completeness
shipped as index presence (`tools.py:454-457`), which `row_failed`
satisfies. This FR makes the number a gate.
[FR-943-census-row-failure-containment.md](FR-943-census-row-failure-containment.md)
— per-row `on_error: skip` → `row_failed` marker; containment is
preserved, its aggregate consequence is what this FR governs.
[FR-895-census-synthesize-tail.md](FR-895-census-synthesize-tail.md) —
`BRIEF_TOP_N = 30` bounded synthesize input and the fabricated-URL scan
in `render_brief`; the header line states the top-N fact because the
line is being written anyway, but no FR-895 selection or scan behaviour
changes. [FR-967-unwitnessed-acceptance-criteria.md](FR-967-unwitnessed-acceptance-criteria.md)
[Halted] — found this demo has no unit tests; the fixtures this FR
adds are the first, and are scoped to the reducer and render tail
only. [FR-984-map-fan-out-max-concurrency.md](FR-984-map-fan-out-max-concurrency.md)
— Successor A; independent, no shared implementation, may land in
either order. No REJECTED FR touches census coverage.

## Summary

`reduce_pr_ledger` computes `classification_coverage = judged / total`
(`tools.py:344`), prints it into the ledger head (`tools.py:481`), and
gates on nothing but index presence. `prepare_brief_input` keeps only
`judged` rows, `synthesize` sees rows and a rubric, `render_brief`
writes the model's text. Add a coverage floor in the reducer — default
`1.0`, an operator-supplied `min_coverage` accepts less — that raises
before any artifact is opened, and a code-written population header as
the first line of the brief, read from reducer-owned counts.

## Value Statement

A reader of the census brief can never again mistake the survivors of
a rate limiter for the footprint; a partial population is either
refused or announced in numbers on line one.

## Problem

From the parent's evidence run (`logs/tt-profile.log`, 2026-09-04):

| observation | value |
|---|---|
| PRs discovered | 259 |
| rows `judged` | 147 |
| rows `row_failed` (429 retries exhausted) | 100 |
| ledger line 8 | `- classification coverage: 56.8%` |
| brief lines mentioning coverage / skip / 429 | 0 |
| exit code | 0 |

The ledger is honest; the brief — the artifact a human reads — is not.
Its `docs 76 / feat 35 / fix 23` skew is over rows chosen by whichever
requests the quota admitted. Every structural check passed
(`plausible_wrong_answer`); the completeness gate checked shape, not
substance (`gate_checks_shape_not_substance`).

## Ideal Result

A census either classifies the whole population it discovered or stops
before writing a brief. When an operator explicitly accepts less, the
first line of the brief says exactly how much less, written by code
from the full-population counts.

## Proposed Solution

All in `examples/demos/person_profile_census/tools.py`; the graph gains
a `min_coverage` variable and nothing else.

**Gate** (after `_canary_gate`, before any path is opened or written —
judgement C-5 / R-4):

```python
floor = _parse_min_coverage(state.get("min_coverage"))   # default 1.0
coverage = rollup["classification_coverage"]
if coverage < floor:
    raise ValueError(
        f"classification coverage {coverage:.1%} below min_coverage "
        f"{floor:.0%}: {failed} of {total} rows row_failed. Pass "
        f"--var min_coverage=<0..1> to accept a partial population."
    )
```

`_parse_min_coverage` accepts `None` → `1.0`, or a number / numeric
string in inclusive `[0.0, 1.0]`; rejects booleans, non-numeric, NaN,
±inf, out-of-range, naming `min_coverage` in the message.

**Header** (`render_brief`; counts from `state["ledger"]["rollup"]`,
never recomputed from the top-N `brief_input`):

```
> Population: {judged}/{total} PRs classified ({coverage:.1%}); {failed} row_failed. Brief synthesized from top {BRIEF_TOP_N} judged rows by delta.
```

written before the model-authored body. The `synthesize` prompt is
untouched; the model is never asked to report coverage.

## Acceptance Criteria

Verbatim from the parent judgement (Successor B), R-7 folded into
AC-B12.

- [ ] AC-B01: RED first: a 10-row reducer fixture with 3 `row_failed`
  rows fails at the default floor `1.0`, passes at
  `min_coverage="0.7"`, and its failure names coverage, floor, failed
  count, and total count.
- [ ] AC-B02: `min_coverage` defaults to `1.0`; booleans, non-numeric
  strings, NaN, infinities, negatives, and values above `1.0` fail
  with `min_coverage` in the diagnostic; inclusive `0.0` and `1.0`
  boundaries are tested.
- [ ] AC-B03: the coverage gate runs after the existing canary and
  before opening or writing ledger, JSONL, run metadata, claims, or
  brief artifacts.
- [ ] AC-B04: a compiled-path witness with 100 of 259 rows failed
  proves `reduce_pr_ledger` raises, `prepare_brief_input`,
  `synthesize`, and `render_brief` do not run, and no output artifact
  exists.
- [ ] AC-B05: when coverage meets the floor, `render_brief` reads
  reducer-owned population statistics rather than bounded
  `brief_input` and writes this exact first-line shape:
  `> Population: {judged}/{total} PRs classified ({coverage:.1%}); {failed} row_failed. Brief synthesized from top {BRIEF_TOP_N} judged rows by delta.`
- [ ] AC-B06: a known-count fixture asserts the exact first line and
  proves the header precedes model-authored content.
- [ ] AC-B07: existing FR-943 witnesses remain green: one attributable
  map failure still becomes one `row_failed` ledger row and does not
  abort fan-out; structural failures remain fatal.
- [ ] AC-B08: person-profile census documentation states the default
  fail-closed behaviour and shows explicit `--var min_coverage=...`
  acceptance of a partial population; smoke output is regenerated
  without corp identifiers.
- [ ] AC-B09: the graph change has the required graph-authoring
  report, lint, and smoke evidence.
- [ ] AC-B10: one capability and REQ (`CAP-263-census-coverage-gate`,
  `REQ-YG-646`, re-verified against `origin/main` at push) cover the
  production branches; every test carries that REQ marker;
  regenerated `ARCHITECTURE.md` and `python scripts/req_coverage.py
  --strict` pass.
- [ ] AC-B11: FR status/implementation record, one `fix` changelog
  fragment, and diary reflection
  (`docs/diary/diary-<date>-reflection-fr-985-<slug>.md`) are committed.
- [ ] AC-B12: operational witness — **authorized by the operator on
  2026-09-04** to run once after both FR-984 and FR-985 are enforced:
  the combined corp census records sanitized configured concurrency,
  429 count, discovered/classified/failed counts, coverage, and
  terminal result (completed, or failed closed at the floor). No corp
  identifier enters the record; deterministic tests remain the
  enforcement gate.

## Alternatives Considered

Apportioned from the parent's research record (rows bearing on
coverage disclosure). Every row carries a probe-produced detail.

| candidate | persona | class | verdict | precedent | is_this_a_graph | effort-risk | rationale |
|---|---|---|---|---|---|---|---|
| Coverage floor in the reducer, default 1.0 | subtractionist | enforcement/latency-critical | ACCEPT | FR-943 containment; Commandment 6 | no | low / low | `tools.py:344` already computes the number and `:481` prints it; the gate is a few lines after `_canary_gate`. Default 1.0 makes a partial population an explicit `--var`, recorded in the invocation. |
| Code-written population header on the brief | subtractionist | enforcement/latency-critical | ACCEPT | FR-962 R-3 "LLM never computes rollups" | no | low / low | Judgement R-4: counts come from reducer-owned `rollup`, not the 30-row `brief_input` — the probe showed `prepare_brief_input` discards non-judged rows (`tools.py:551-553`), so anything derived downstream of it cannot know the total. |
| Ask the synthesize prompt to state coverage | librarian_research | judgement/analysis/generation | REJECT | FR-895 prompt contract | no | low / high | The model never sees the population (`graph.yaml:137-144` passes rows only); it would be asked to invent a number — the exact failure mode the brief exhibits. Coverage is arithmetic; code writes it. |
| Lower `max_items` so the population fits the quota | subtractionist | enforcement/latency-critical | REJECT | FR-939 | no | zero / high | Substitutes the survivors for the whole by construction — the defect this FR exists to make impossible. |
| Gate at `prepare_brief_input` or `render_brief` instead of the reducer | data_process_planner | enforcement/latency-critical | REJECT | — | no | low / medium | By then the ledger and JSONL are already on disk; judgement C-5 requires failure before any artifact write. The reducer is the last LLM-free stage that sees the whole population. |
| Disclose FR-895's top-N truncation as its own gate | subtractionist | enforcement/latency-critical | DEFER | FR-895 | no | low / low | Stated on the header line because the line exists; changing what top-N selects or whether it gates is FR-895 territory and no reader has asked for it. Named, not absorbed. |

## Related

- Parent: [FR-983](FR-983-map-concurrency-and-census-coverage-gate.md) and its [judgement](FR-983-map-concurrency-and-census-coverage-gate.judgement.md) (R-1, R-2, R-4, R-5, R-7, C-5, Successor B AC list)
- Sibling: [FR-984](FR-984-map-fan-out-max-concurrency.md)
- Reducer: `examples/demos/person_profile_census/tools.py:302-347` (rollup), `:360-382` (canary), `:384-` (reducer), `:544-573` (brief input), `:612-` (render)
- Graph: `examples/demos/person_profile_census/graph.yaml:125-150`
- Evidence: `logs/tt-profile.log`, `tmp/tt-profile.md` line 8 (operator-local; corp content, not committed)
