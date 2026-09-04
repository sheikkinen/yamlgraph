# Feature Request: reject unsatisfiable multi-value `visibility` in authored-PR discovery

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-09-04
**First consumer / first event:** the operator running the corp
person-profile census (`sheikkinen@<owner>`) on 2026-09-04 — the very
next invocation of `gh_authored_prs_discover` with more than one
visibility class, which today returns zero PRs and blames the author.
**Research:** [FR-966.research.md](FR-966.research.md)
**Prior art:** [FR-962-person-profile-census-authored-prs.md](FR-962-person-profile-census-authored-prs.md) — introduced the adapter; its R-5 created the multi-value `visibility` surface and forbids collecting an unnamed class, a fence this FR keeps rather than relaxes. [FR-939-map-overflow-policy.md](FR-939-map-overflow-policy.md) and [FR-943-census-row-failure-containment.md](FR-943-census-row-failure-containment.md) — population bounds and per-row failure containment in the same pipeline; neither touches query construction, both out of scope. The research record's IDF-ranked retrieval returned FR-534, FR-530, FR-538, FR-545 (dungeon-master "visibility" in the narrative sense) — dismissed as vocabulary collisions with no bearing on GitHub query semantics.

## Summary

`gh_authored_prs_discover` accepts a `visibility` list of two or more
classes, emits one `--visibility` flag per entry, and `gh search prs`
conjoins them into an unsatisfiable query. Every such run returns an
empty population and raises an error that blames the author/owner/since
triple. Reject the cardinality at the input boundary instead.

## Value Statement

An operator who names two visibility classes learns immediately that the
filter cannot match anything, instead of concluding from a loud empty
result that the subject authored no pull requests.

## Problem

`examples/demos/corpus_census/adapters/corpus_adapters.py:241-281`
builds the search argv as:

```python
for vis in visibility:
    argv.extend(["--visibility", vis])
```

`gh` renders repeated `--visibility` flags as conjoined `is:` qualifiers.
A pull request has exactly one visibility, so the intersection is empty
by construction. Measured 2026-09-04 (`author=sheikkinen`,
`owner=<corp>`, `created>=2025-01-01`):

| flags | results |
|---|---|
| `--visibility private` | 258 |
| `--visibility internal` | 0 |
| `--visibility public` | 0 |
| `--visibility private --visibility internal` | 0 |
| `--visibility private,internal` | 0 |

`_parse_visibility` (`corpus_adapters.py:202-239`) validates each entry
against `{"public","private","internal"}` and rejects duplicates, so a
two-element list passes validation and fails at the query layer:
validation is per-entry, the defect is combinational.

The empty-population guard (`corpus_adapters.py:268-274`) then reports
`no PRs for author=... owner=... since=... visibility=[...]`, attributing
the emptiness to the identity triple. The committed corp example in
`examples/demos/person_profile_census/README.md` shipped
`--var visibility='["private","internal"]'`, so the documented corp path
was unexecutable from the day it was committed.

No test covers this. No file under `tests/` names
`gh_authored_prs_discover` or `_parse_visibility`.

## Ideal Result

`visibility` accepts exactly what `gh` can satisfy and nothing more. An
operator naming an impossible filter is told so by name, at the input
boundary, before any network call — and an operator naming a possible
one gets the population that exists. The adapter never emits an argv it
cannot honour, and a test proves the argv shape without touching the
GitHub API.

## Proposed Solution

Enforce cardinality where the input is already validated, in
`_parse_visibility`. The list shape is retained so the FR-892 tool-slot
contract and every existing single-element caller are unchanged; only
the unsatisfiable cardinality is refused.

**Validation order is frozen.** The new check is the *last* statement
before `return`, after the per-entry loop has completed. Every existing
failure keeps its current class and message, and each is reached before
the cardinality check can fire:

| input | existing failure class | unchanged |
|---|---|---|
| malformed JSON string (`"[private"`) | `` `visibility` must be JSON list `` | yes |
| non-list JSON value (`"\"private\""`, `"{}"`) | `` `visibility` must be a non-empty list `` | yes |
| empty list (`"[]"`) | `` `visibility` must be a non-empty list `` | yes |
| non-string entry (`"[1]"`) | `visibility entry must be str` | yes |
| unknown class (`'["secret"]'`) | `unknown visibility` | yes |
| casefold duplicate (`'["private","PRIVATE"]'`) | `duplicate visibility` | yes |

The first two rows are distinct failures and are described distinctly: a
malformed JSON *string* fails at `json.loads`; a well-formed JSON value
that is not a list fails the shape check. Neither is "non-JSON input".

**Diagnostic identity is frozen.** The conjunction error names the
mechanism, reproduces the list the operator supplied, and states the
remedy. It reports `raw` — the entries in their **original order and
original spelling** — not `canonical`, which is casefolded and therefore
not what the operator typed:

```python
if len(canonical) > 1:
    raise ValueError(
        "gh_authored_prs_discover: `gh search prs` conjoins repeated "
        f"--visibility flags into `is:` qualifiers, so {raw!r} matches "
        "nothing (a pull request has exactly one visibility). Pass one "
        "visibility class and run once per class."
    )
```

The argv loop is left intact: at cardinality one it emits exactly one
flag. The corp example in the demo README is corrected to a single
class.

Research disposition: see the 2026-09-04 amendment in
[FR-966.research.md](FR-966.research.md), which re-surveys the space in
six classes after the judgement found the generated five rows collapsed
to two outcomes. The decisive addition is probe evidence that **no
platform-supported disjunctive query exists** — GitHub returns HTTP 422
with *"Logical operators only apply to text, not to qualifiers"*, and
the parenthesised form returns 200 with zero results, failing silently.
That closes the one route by which the multi-value surface could have
been made honest rather than refused. The surviving dissent (delete the
parameter outright — it is empirically inert on the only real corpus) is
overruled by FR-962 R-5, a doctrine constraint rather than evidence.

## Acceptance Criteria

Superseded by the judgement of 2026-09-04 and restated here as folded.
These eleven criteria are binding; the original seven are withdrawn.

- [x] AC-01: The research record holds four to six genuinely distinct
  solution classes, each with probe evidence, effort-risk, and a
  disposition; disagreement is preserved or its absence stated;
  `is_this_a_graph: no` is retained.
- [x] AC-02: The FR-939 prior-art link resolves to a committed file
  (`FR-939-map-overflow-policy.md`).
- [x] AC-03: A valid `visibility` list of two or more entries raises
  before `_gh` is reached. The message asserts the repeated-flag
  conjunction semantics, contains the parsed list's `repr` in **original
  order and original spelling**, and states the one-class-per-run remedy.
- [x] AC-04: A fail-if-called `_gh` stub proves the rejection precedes
  every GitHub invocation; no test in this FR touches the network.
- [x] AC-05: Existing validation order is witnessed by a test for each
  of: malformed JSON string, non-list JSON value, empty list, non-string
  entry, unknown class, casefold duplicate — each retaining its current
  failure class.
- [x] AC-06: A mixed-case single-element list returns the canonical
  one-element list and produces exactly one `--visibility` flag carrying
  the canonical value in the argv handed to a stubbed `_gh`.
- [x] AC-07: An accepted non-empty `gh` response still converts to the
  existing sorted `<owner>/<repo>#<number>` authored-PR identity shape.
- [x] AC-08: `examples/demos/person_profile_census/README.md` states the
  one-class-per-run constraint and its corp example carries exactly one
  visibility element.
- [x] AC-09: `capabilities/CAP-260-authored-pr-visibility.yaml` registers
  FR-966 and REQ-YG-643; `ARCHITECTURE.md` is regenerated; every new test
  carries `@pytest.mark.req("REQ-YG-643")`; `python scripts/req_coverage.py
  --strict` passes.
- [x] AC-10: The failing cardinality witness is committed before the
  production fix (separate RED and GREEN commits).
- [x] AC-11: A `fix` changelog fragment names FR-966 and REQ-YG-643; this
  FR records implementation status, decisions, and deviations; a diary
  entry with a `Seed:` is added.

## Judgement Fold — 2026-09-04

Verdict: **APPROVED WITH REVISIONS**
([judgement](FR-966-visibility-conjunction-unsatisfiable.judgement.md)).
All four revisions are folded above; authority is therefore live.

| revision | fold |
|---|---|
| R-1 research insufficient (5 rows → 2 outcomes) | Six-class census amended into the research record, including the two classes the judgement named as missing. The disjunctive-query class is rejected **on cited probe evidence** (HTTP 422; parenthesised variant silently returns 0) rather than on assertion. |
| R-2 dangling prior-art link | `FR-939-map-overflow-detection.md` → `FR-939-map-overflow-policy.md`. |
| R-3 validation order and diagnostic identity unfrozen | Order table and diagnostic contract added to Proposed Solution. **Corrected defect in the original draft:** it reported `canonical` (casefolded) while claiming a verbatim echo. The error now reports `raw`. The malformed-JSON-string and non-list-JSON-value failures are now described as the distinct classes they are; the phrase "non-JSON input" is withdrawn. |
| R-4 registry, TDD, changelog, diary | Folded into AC-09 through AC-11; CAP-260 / REQ-YG-643 allocated. |

Frozen scope: D-1 FR + research fold; D-2 the cardinality guard in
`corpus_adapters.py` only; D-3 `tests/unit/test_fr966_authored_pr_visibility.py`;
D-4 the demo README; D-5 CAP-260 + regenerated `ARCHITECTURE.md`; D-6 one
`fix` changelog fragment; D-7 one diary entry. Nothing else is
authorised — in particular not a scalar `visibility`, not multi-query
union semantics, not Pydantic or any shared validation abstraction, and
no graph or prompt artifact (C-5: this is not graph authoring).

## Alternatives Considered

| Candidate | Class | Verdict | Why |
|---|---|---|---|
| Cardinality guard in `_parse_visibility` (adopted) | boundary-rejection | pursue | Two lines at the boundary that already validates; keeps list shape and the FR-892 contract. |
| Change `visibility` to a bare string | schema-reshape | rejected | Breaks the slot contract and every caller; the same safety is available without the churn. |
| Ask GitHub for `private OR internal` in one query | platform-disjunction | rejected on probe | HTTP 422 — *"Logical operators only apply to text, not to qualifiers."* The parenthesised form returns 200 with 0 results: accepted, treated as free text, silently empty. Offering it would reproduce the very failure under repair. |
| Run the query once per class and union the results | multi-query union | rejected; recorded as the only live successor | Converts an operator's impossible request into a different, possible one. FR-962 R-5 requires the operator to name what is collected, so an honest union needs per-row provenance the reduce contract lacks. That is a capability, not a bug fix. |
| Delete the `visibility` parameter entirely | subtraction | rejected — **surviving dissent** | Measured: omitting the flag returns 258, identical to `--visibility private`; the filter is inert on the only real corpus. Overruled by FR-962 R-5, which made the parameter required so the operator must *name* the class. A doctrine constraint, not an evidential one — recorded so the argument survives. |
| Pydantic `model_validator` on a new input model | validation-framework | rejected | Introduces a model to express one length check in a function whose entire body is validation. |

Preserved disagreement: the generated census returned five `pursue` rows
and no dissent, which the judgement correctly read as insufficient
breadth rather than a strong signal. The amended census surfaces one
genuine dissent (subtraction) and one class killed by evidence rather
than by preference (platform disjunction).

## Implementation Status — 2026-09-04

Enforced on branch `feat/fr966-census-defects`.

| Commit | Content |
|---|---|
| `c9319cb5` | FR-966 and FR-967 filed with folded judgements |
| `a91d96b0` | RED — cardinality witness fails, nine sibling classes pass |
| `0d3c75fe` | GREEN — guard, README, changelog fragment, demo proofs |

RED evidence: 2 failed, 9 passed. The failure printed the unsatisfiable
argv itself, which is the defect stated in the language of the tool:
`--visibility private --visibility internal`. GREEN evidence: 48 passed
across the FR-966 and FR-899 suites; `scripts/req_coverage.py --strict`
exits 0.

Decisions taken during enforcement:

- The guard reports `raw` rather than `canonical`, so the operator reads
  back the spelling and order they typed. Casefolding happens before the
  count, so `["Private", "private"]` collapses to one element and is
  accepted — a duplicate is not a conjunction.
- The guard sits after the per-entry loop, so every existing failure
  class still fires first and keeps its message. Cardinality is the last
  check because it is the only one that can be true of a fully valid list.

Deviations from the frozen scope: none. One condition fired.

**C-6 stop condition fired.** Regenerating the demo proof required by
`demo-proof-check` revealed that `reduce_pr_ledger` resolves
`azure_model` from `os.environ["AZURE_MODEL"]` when the state key is
absent. The public smoke path renames `azure_model` to `smoke_model`, so
the key is always absent there and the reducer records whatever the
operator's `.env` holds — on a corp machine, the Azure deployment name,
written into an artifact committed to a public repository. Unsetting the
variable does not help: `yamlgraph/config.py` calls `load_dotenv` at
import and restores it inside the process. The proof was generated with
`AZURE_MODEL='none-public-smoke'` as an override, which is the only
mechanism that works.

That surface is outside D-1 through D-7, so this FR did not touch it.
The correction is FR-967 D-1 AC-13 (the reduce boundary must raise rather
than record an unrelated environment variable), confirmed by the operator
on 2026-09-04. The already-published identifiers were dispositioned by
the operator the same day as diary-record-only.

## Related

- `examples/demos/corpus_census/adapters/corpus_adapters.py:202-281`
- `examples/demos/person_profile_census/README.md`
- [FR-967-unwitnessed-acceptance-criteria.md](FR-967-unwitnessed-acceptance-criteria.md) — the sibling FR covering why this defect shipped untested; this FR fixes the defect, that one closes the hole.
