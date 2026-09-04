# Problem brief: multi-value `visibility` in authored-PR discovery returns an empty population

**Prior art:** FR-962
(`feature-requests/FR-962-person-profile-census-authored-prs.md`)
introduced the adapter, and its judgement
(`feature-requests/FR-962-person-profile-census-authored-prs.judgement.md`,
R-5) required visibility to be an explicit required enum list checked
before any collection crosses the boundary — that revision created the
multi-value surface described here, and its intent (never collect a
class the operator did not name) is the fence this brief inherits.
FR-939 (`feature-requests/FR-939-map-overflow-detection.md`) and
FR-943 (`feature-requests/FR-943-census-row-failure-containment.md`)
govern population overflow and per-row failure containment in the same
census pipeline; neither concerns query construction, and both are out
of bounds. A REJECTED-FR sweep for `gh` and query-construction nouns
found no prior proposal on GitHub search filter composition.

## Problem statement

`gh_authored_prs_discover`
(`examples/demos/corpus_census/adapters/corpus_adapters.py:241-281`)
accepts a required `visibility` JSON list validated against
`{"public","private","internal"}` by `_parse_visibility`
(`corpus_adapters.py:202-239`), then builds the `gh` argv with one flag
per entry:

```python
for vis in visibility:
    argv.extend(["--visibility", vis])
```

`gh search prs` composes repeated `--visibility` flags into a single
conjunctive query. Measured on 2026-09-04 against a real corpus
(`author=sheikkinen`, `owner=terveystalo`, `created>=2025-01-01`):

| flags passed | resulting query fragment | results |
|---|---|---|
| `--visibility private` | `is:private type:pr user:<owner>` | 258 |
| `--visibility internal` | `is:internal ...` | 0 |
| `--visibility public` | `is:public ...` | 0 |
| `--visibility private --visibility internal` | `is:private is:internal` | 0 |
| `--visibility private,internal` | single comma-joined value | 0 |
| no visibility flag | `type:pr user:<owner>` | 258 |

A pull request has exactly one visibility, so any two-element
`visibility` list is an unsatisfiable intersection: the returned
population is empty regardless of the true corpus. The adapter then
raises its empty-population guard (`corpus_adapters.py:268-274`,
`"no PRs for author=... owner=... since=... visibility=[...]"`).

Two consequences follow. First, the message attributes emptiness to the
author/owner/since triple and merely echoes the visibility list, so the
failure reads as "this person authored nothing here" rather than "this
filter cannot match anything"; diagnosis on 2026-09-04 took six manual
`gh` probes. Second, the committed corp invocation in
`examples/demos/person_profile_census/README.md` shipped
`--var visibility='["private","internal"]'` as its documented example,
so the documented corp path could never have produced a ledger. The
validator accepts an input the query layer cannot honour: validation is
per-entry, the failure is combinational.

No test exercises this. Repository-wide, no file under `tests/` names
`gh_authored_prs_discover`, `_parse_visibility`, `reduce_pr_ledger`,
`PRLedgerRow`, or `person_profile_census`; the sibling FR-899 census has
`tests/unit/test_fr899_repo_census.py`.

## Classification

enforcement/latency-critical — a deterministic argv-construction and
input-validation boundary with no LLM in the path.

## Constraints

- The `visibility` input must remain required and explicitly enumerated:
  FR-962 R-5 forbids collecting any visibility class the operator did
  not name. Silently dropping the filter, or defaulting to "all", is out
  of bounds.
- `gh` argv must stay fixed-form and shell-free (`_gh`,
  `corpus_adapters.py`); no string-interpolated query assembly.
- The adapter is shared by the corpus_census family; any change must
  keep the FR-892 tool-slot contract (`args: [source]`, state-driven
  `visibility`) intact.
- Population bounds (`MAX_PRS = 500`, overflow rejection at 501) are
  FR-939/FR-943 territory and must not be redefined here.
- Any behaviour claimed must be witnessed by a test that does not call
  the live GitHub API.

## Witnessed incidents

- 2026-09-04, this repository: planning a corp self-profile run,
  `--visibility private --visibility internal` returned 0 PRs while
  `--visibility private` alone returned 258 for the identical
  author/owner/since triple. A GitHub 403 secondary-rate-limit body
  disclosed the constructed query
  (`q=author:...+created:>=2025-01-01+is:private+type:pr+user:...`),
  which is how the conjunction was identified; without that accidental
  disclosure the argv-to-query mapping is not observable from the
  adapter's own output.
- 2026-09-04, same session: the committed corp example in
  `examples/demos/person_profile_census/README.md` was found to carry
  the two-element list, i.e. the documented invocation was
  unexecutable-by-construction from the day it was committed, and no
  gate detected it.
- 2026-09-02, PR #562: FR-962 merged with all 17 acceptance criteria
  unchecked, including AC-02 ("discovery validates ... required
  `visibility` enum list ... loud empty result"). The empty result is
  loud; the criterion did not require the filter to be satisfiable.
