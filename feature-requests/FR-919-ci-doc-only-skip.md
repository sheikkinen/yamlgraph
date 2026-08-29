# Feature Request: Doc-Only PR Skip for Expensive CI Jobs

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** the next doc-only PR (diary entry, FR
edit, changelog fragment) — its `core-test`, both `test` matrix legs,
and `security` report *skipped* in seconds instead of installing the
full extras set four times.
**Research:** split from [FR-917](FR-917-ci-python-matrix-and-doc-only-skip.md)
per its judgement
([FR-917 judgement](FR-917-ci-python-matrix-and-doc-only-skip.judgement.md),
D-2); in-body dispositioned alternatives table below (5 solution
classes + precedent + preserved disagreement, judgement R-2).
**Prior art:** FR-917 is the split parent (superseded, no authority);
FR-918 is the sibling split covering the orthogonal Python-matrix
concern — job names are unchanged here, so merge order is irrelevant.
No earlier FR addresses CI path filtering.

**is_this_a_graph:** No; this is CI event/path classification in
GitHub Actions, not an LLM pipeline or graph artifact — no map/race/
router shape applies.

## Summary

Every PR runs `core-test`, two matrix `test` legs, and `security`
regardless of what changed. The diary/FR/changelog gates make doc-only
PRs a routine occurrence; each one pays ~4 full dependency installs.
Add path-aware job-level skips that branch protection counts as
passing, without touching tag-release behavior.

## Value Statement

Doc-only PRs complete required checks in seconds; CI minutes go to PRs
that can actually break tests.

## Problem

1. `.github/workflows/workflow.yml` triggers on all `pull_request`
   events with no path awareness before `core-test` or the `test`
   matrix.
2. `.github/workflows/security.yml` likewise runs pip-audit on every
   PR, though its result is a pure function of `pyproject.toml`.
3. Workflow-level `paths-ignore` is not usable: required checks
   (`test (3.11)`, `test (3.12)`) would stay in "Expected" and block
   automation (non-admin) PRs. Only a job-level skip reports a
   `skipped` conclusion, which branch protection treats as passing.
4. Both workflows also run on version tags, and the release chain
   (`build` → `publish` → `create-release`) depends on `test`; any skip
   logic must be provably inert on tag pushes (judgement R-4, C-3).

## Ideal Result

A single mechanical classifier — "does the diff contain any non-Markdown
file?" — gates the expensive jobs in each workflow independently.
Doc-only PRs show all four jobs skipped and merge normally; any PR
touching a non-`.md` file runs everything; tag pushes are structurally
incapable of skipping.

## Path classifier (resolves judgement R-5)

**Definition:** a PR is doc-only iff every changed file matches
`**/*.md`. One glob, no allowlist-of-directories semantics to get wrong
— FRs, diary entries, changelog fragments, and docs prose are all
Markdown. Any non-Markdown file (workflows, graphs, prompts,
capabilities YAML, Python, images in `docs/`) runs the full suite;
false negatives cost one redundant CI run, never a missed test.

Fixture table (glob semantics witnesses):

| Changed files | Expensive jobs |
|---|---|
| `docs/diary/example.md` only | skipped |
| `feature-requests/FR-XXX-example.md` only | skipped |
| `changelog/unreleased/example.md` only | skipped |
| `README.md` only | skipped (root Markdown is doc-only by definition) |
| `.github/workflows/workflow.yml` | runs |
| `prompts/example.yaml` | runs |
| `graphs/example.yaml` | runs |
| `capabilities/CAP-XXX-example.yaml` | runs |
| `docs/img/example.png` only | runs (conservative false negative, accepted) |
| `docs/diary/example.md` + `yamlgraph/example.py` | runs |

## Proposed Solution

Each workflow gets its **own** `changes` job (judgement R-4: jobs
cannot depend across workflows). The gate is
`event != pull_request OR code changed` — non-PR events (tag pushes)
short-circuit to "run", making tag skips structurally impossible.

### `workflow.yml`

```yaml
changes:
  runs-on: ubuntu-latest
  outputs:
    code: ${{ github.event_name != 'pull_request' || steps.filter.outputs.code == 'true' }}
  steps:
    - uses: actions/checkout@v4
      if: github.event_name == 'pull_request'
    - uses: dorny/paths-filter@v3
      if: github.event_name == 'pull_request'
      id: filter
      with:
        filters: |
          code:
            - '!**/*.md'
```

The filter step is guarded by `if: github.event_name ==
'pull_request'` (judgement R-1): on tag pushes the step never
executes, so it cannot fail there — the job output's short-circuit is
the sole non-PR "run" source and the step is inert.

```yaml
core-test:
  needs: changes
  if: needs.changes.outputs.code == 'true'
test:
  needs: changes
  if: needs.changes.outputs.code == 'true'
```

Release chain safety: on tag pushes `github.event_name == 'push'`, so
`changes.outputs.code` is `'true'` by construction and `test` runs;
`build`/`publish`/`create-release` keep their existing `needs: test`
and tag `if:` guards unchanged.

### `security.yml`

Identical independent `changes` job and the same `if:` on the pip-audit
job. Same tag-push short-circuit.

### Human review gate (judgement R-6, C-4)

Workflow edits are enforcement infrastructure: the operator explicitly
reviews the diff before it lands. No branch-protection mutation is
needed — job names are unchanged, and skipped required checks pass.

## Acceptance Criteria

- [ ] `workflow.yml` and `security.yml` each have their own `changes`
      job; expensive jobs gate on it (AC-06).
- [ ] Witness doc-only PR (touching only a `docs/diary/*.md` file):
      `core-test`, both `test` legs, and `security` show *skipped*;
      PR reports mergeable with required checks satisfied; run link
      cited.
- [ ] Witness mixed PR (md + non-md): full suite runs; run link cited.
- [ ] Tag-release proof (AC-07): the shipped YAML carries
      `if: github.event_name == 'pull_request'` on the
      `dorny/paths-filter` step in BOTH workflows (step-safe, not only
      output-safe — judgement R-1), the gate expression short-circuits
      on `github.event_name != 'pull_request'` — both cited by line —
      and the first post-merge tag push shows `test`, `build`, and
      `security` executed; run link recorded in this FR.
- [ ] Fixture table above matches the shipped glob (single `!**/*.md`
      filter) — no drift between prose and YAML (AC-08).
- [ ] Operator has explicitly reviewed both workflow diffs (AC-09).
- [ ] Changelog fragment (`ci` scope) + diary reflection.

## Alternatives Considered

Five genuine solution classes, dispositioned. Precedent: no prior FR
in `feature-requests/` addresses CI path filtering (grep `paths-filter
| paths-ignore` returns only FR-917 lineage); GitHub's own
troubleshooting doc for required checks + path filtering is the
external precedent for rejecting class 1. Preserved disagreement: the
directory-allowlist class (2) is *more expressive* (could skip on
non-md doc assets like `docs/img/*.png`) and a reasonable reviewer
could prefer it; it loses here on glob-semantics risk, not
capability — revisit if the png false-negative cost ever materializes.

| Alternative | Disposition |
|---|---|
| 1. Workflow-level `paths-ignore` | REJECTED — required checks stay "Expected", blocking automation PRs; only job-level skips report a passing-equivalent conclusion. |
| 2. Directory allowlist (`docs/**`, `changelog/**`, `feature-requests/**`) | REJECTED (disagreement preserved above) — dorny filters OR their globs, so multi-glob negation lists mis-classify (a root `.md` matches `!docs/**` → "code"); the single `!**/*.md` glob has no such trap and covers the same files. |
| 3. Shared `changes` job reused by `security.yml` | REJECTED — cross-workflow `needs` does not exist (parent judgement R-4). |
| 4. Hand-rolled `git diff` step | REJECTED — reimplements base-ref resolution across PR/push/tag events; `dorny/paths-filter@v3` is pinned and widely audited. |
| 5. `[skip ci]` commit tags | REJECTED — author-discretionary; path facts are mechanical. |
| Also skipping `commitlint`/gates | OUT OF SCOPE — cheap jobs; the diary/changelog gates must run precisely on doc PRs. |

## Related

- [FR-917](FR-917-ci-python-matrix-and-doc-only-skip.md) (parent, split)
- [FR-917 judgement](FR-917-ci-python-matrix-and-doc-only-skip.judgement.md) (R-4, R-5, R-6, AC-05–AC-09, C-3)
- FR-918 (sibling: matrix refresh — independent; merge order irrelevant,
  job names unchanged by this FR)
- [.github/workflows/workflow.yml](../.github/workflows/workflow.yml),
  [.github/workflows/security.yml](../.github/workflows/security.yml)

## Judgement (date)

See [FR-919-ci-doc-only-skip.judgement.md](FR-919-ci-doc-only-skip.judgement.md) (2026-08-30): APPROVED WITH REVISIONS. Both revisions (R-1 step-safe filter guard, R-2 research substance) folded 2026-08-30 before enforcement.

## Implementation Status (2026-08-30)

Enforced same day:

- `workflow.yml`: `changes` job added; `core-test` and `test` gated on
  `needs.changes.outputs.code == 'true'`. The `dorny/paths-filter@v3`
  step (and its checkout) carry `if: github.event_name ==
  'pull_request'` — step-safe on tag pushes (R-1); the job output
  short-circuits to `'true'` for non-PR events, so the release chain
  (`test` → `build` → `publish` → `create-release`) cannot skip.
- `security.yml`: independent `changes` job, same gate on the pip-audit
  job (AC-06).
- Changelog fragment: `changelog/unreleased/fr-919-ci-doc-only-skip.md`.

**Pending operator actions (human review gate, AC-09):**

1. Review both workflow diffs before landing on `main`.
2. Cite the witness runs here: one doc-only PR (all four jobs skipped,
   mergeable), one mixed PR (full suite), and the first post-merge tag
   push (`test`, `build`, `security` executed).
