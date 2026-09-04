# Feature Request: person-profile census fails closed below a classification-coverage floor and stamps the population on the brief

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-04, [judgement](FR-985-census-coverage-floor-and-population-header.judgement.md)); R-1..R-4 folded below, human-reviewed; authority active for the frozen scope.
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
either order. Authoring brief for the graph edit (judgement R-2):
[authoring-briefs/fr-985-census-coverage-floor-brief.md](authoring-briefs/fr-985-census-coverage-floor-brief.md).
Containment note (judgement R-3): FR-962 reimplemented row containment
in this demo's own reducer (`tools.py:177 _row_failed`); FR-943's tests
exercise the corpus-census reducer, so they are precedent, not a proxy
witness — this FR adds the local one. No REJECTED FR touches census coverage.

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

**Header** (`render_brief`; `judged`, `total`, `coverage`, `failed` from
`state["ledger"]["rollup"]`, never recomputed from the top-N
`brief_input`; `selected = len(state["brief_input"])` is the only field
the bounded input supplies — judgement R-1, so the sentence stays true
when fewer than `BRIEF_TOP_N` rows were judged):

```
> Population: {judged}/{total} PRs classified ({coverage:.1%}); {failed} row_failed. Brief synthesized from {selected} of {judged} judged rows, selected by descending delta (cap {BRIEF_TOP_N}).
```

written before the model-authored body. The `synthesize` prompt is
untouched; the model is never asked to report coverage. The graph gains
exactly one state variable, `min_coverage`, through the governed
authoring route driven by the committed brief
[authoring-briefs/fr-985-census-coverage-floor-brief.md](authoring-briefs/fr-985-census-coverage-floor-brief.md).

## Acceptance Criteria

Revised list from the FR-985 judgement (supersedes the parent's
Successor B list). The former AC-B12 is no longer a criterion — see
"Non-gating observation" below (judgement R-4).

- [ ] AC-01: RED first: a 10-row person-profile reducer fixture with 3
  `row_failed` rows fails at the default floor `1.0`, passes at
  `min_coverage="0.7"`, and its failure names coverage, floor, failed
  count, and total count.
- [ ] AC-02: `min_coverage` defaults to `1.0`; booleans, non-numeric
  strings, NaN, infinities, negatives, and values above `1.0` fail with
  `min_coverage` in the diagnostic; numeric values and numeric strings
  are accepted within inclusive `[0.0, 1.0]`, with both boundaries
  tested.
- [ ] AC-03: the coverage gate runs after the existing canary and before
  constructing, opening, or writing ledger, JSONL, run-metadata, claims,
  rejected-brief, or accepted-brief paths; a canary failure still takes
  precedence over a coverage failure.
- [ ] AC-04: a compiled-path fixture with 100 of 259 rows failed proves
  `reduce_pr_ledger` raises, `prepare_brief_input`, `synthesize`, and
  `render_brief` do not run, and no output artifact is created.
- [ ] AC-05: when coverage meets the floor, `render_brief` obtains
  `judged`, `total`, `coverage`, and `failed` from reducer-owned
  full-population rollup data, obtains only `selected` from
  `len(brief_input)`, and writes this exact first line:
  `> Population: {judged}/{total} PRs classified ({coverage:.1%}); {failed} row_failed. Brief synthesized from {selected} of {judged} judged rows, selected by descending delta (cap {BRIEF_TOP_N}).`
- [ ] AC-06: known-count rendering fixtures below and above the cap
  assert exact first lines for `selected/judged` values `7/7` and
  `30/40`, respectively, and prove the header precedes model-authored
  content.
- [ ] AC-07: a local person-profile containment fixture proves one
  attributable `_error` finding becomes one `row_failed` ledger row
  while judged peers survive when the floor permits partial coverage;
  separate local fixtures prove invalid, missing, duplicate, and
  out-of-range indices plus invalid mechanical bundles remain fatal.
  Relevant FR-943 suites remain green but do not substitute for these
  witnesses.
- [ ] AC-08: person-profile census documentation states the default
  fail-closed behaviour, shows explicit `--var min_coverage=...`
  acceptance of a partial population, explains the population and
  bounded-input header fields, and regenerates smoke output without
  private/corp identifiers.
- [ ] AC-09: FR-985 cites a committed
  [authoring-briefs/fr-985-census-coverage-floor-brief.md](authoring-briefs/fr-985-census-coverage-floor-brief.md);
  the graph edit is produced through the governed authoring route;
  `tmp/draft-authoring-report.md` names the graph and documentation
  artifacts; graph lint passes; the narrow smoke is attempted and its
  exact outcome or blocker is recorded.
- [ ] AC-10: `CAP-263-census-coverage-gate` and `REQ-YG-646`, re-verified
  against `origin/main` at push, cover every changed production branch;
  every new test carries that REQ marker; regenerated `ARCHITECTURE.md`
  and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-11: the FR status and implementation decisions, one `fix`
  changelog fragment, and
  `docs/diary/diary-<date>-reflection-fr-985-<slug>.md` containing a
  `Seed:` are committed.

### Non-gating observation (judgement R-4, C-7)

The operator authorized (2026-09-04) one combined private-corpus run
after **both** FR-984 and FR-985 are enforced, recording sanitized
configured concurrency, 429 count, discovered/classified/failed counts,
coverage, and terminal result (completed, or failed closed at the
floor). It does not gate FR-985 completion, must not run before both
successors land, commits no corp identifier, and claims no
provider-quota improvement. Appended to this record when available.

## Judgement Fold — 2026-09-04

**Verdict: APPROVED WITH REVISIONS** (sole route, `copilot`,
`gpt-5.6-sol`). Authority active after this fold.

| # | Finding | Disposition |
|---|---|---|
| R-1 | "top 30 judged rows" is false whenever fewer than 30 rows were judged — the FR's own `plausible_wrong_answer` on small runs | Header frozen to `{selected} of {judged} … (cap {BRIEF_TOP_N})`; `selected` is the one field from `brief_input`; AC-06 fixtures at `7/7` and `30/40` |
| R-2 | Graph-authoring brief must be committed and cited | Committed at `authoring-briefs/fr-985-census-coverage-floor-brief.md`; AC-09 revised |
| R-3 | FR-962 reimplemented containment locally (`tools.py:177 _row_failed`); FR-943 tests exercise a different reducer | AC-07 now requires a local person-profile containment witness; FR-943 suites are regression only |
| R-4 | AC-B12 coupled acceptance to FR-984 | Removed from criteria; kept as non-gating observation with the operator's authorization intact |

All four verified against the cited files before folding; none
falsified.

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
