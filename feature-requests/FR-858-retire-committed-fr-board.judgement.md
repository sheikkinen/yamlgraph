# Judgement: FR-858 Retire the Committed FR Board (docs/fr-board.md)

**Prior art:** the sole gate hit is this judgement's own subject FR (`FR-858-retire-committed-fr-board.md`), not independent precedent. External precedent — FR-740 (the board's creator, dispositioned as superseded-in-part per AC-11), FR-179 (de-tracked `CHANGELOG.md` for the same merge-conflict reason; the cure held), and the Scripture convictions `who_reads_this_when` and fr-board F7 — is dispositioned in the FR's own Prior art line and the Reviewed-against list below.

**Verdict:** APPROVED WITH REVISIONS — the deletion is justified by validated stale-cache, hook-tax, and conflict-lock evidence, but authority activates only after the FR folds the CLI/test and reference-scope clarifications below.

**Reviewed against:** `feature-requests/FR-858-retire-committed-fr-board.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/fr-board.md`; `.pre-commit-config.yaml`; `scripts/fr_board.py`; `scripts/tests/test_fr_board.py`; `scripts/vscode/now.py`; `.github/skills/session-introspection/SKILL.md`; `feature-requests/FR-740-fr-pipeline-board.md`; `feature-requests/FR-179-append-only-changelog.md`; `docs/diary/diary-2026-08-30-the-gate-that-asked-me-to-forge-evidence.md`.

## What is sound

The problem is real and materially evidenced. The FR states one consumer event up front (`now.py` reads live state, every FR commit stops paying the hook tax) at `feature-requests/FR-858-retire-committed-fr-board.md:8-10`, and the summary keeps the core distinction clear: retire the committed materialized view, not the parser (`feature-requests/FR-858-retire-committed-fr-board.md:14-16`). Current repository evidence supports the claim: `docs/fr-board.md` is 526 lines and contains 62 `PARSE-FAILURE` rows, matching the refreshed metrics at `feature-requests/FR-858-retire-committed-fr-board.md:91-96`; the active hook remains wired at `.pre-commit-config.yaml:291-296`; `now.py` reads the committed cache in both brief and full modes at `scripts/vscode/now.py:327-330` and `scripts/vscode/now.py:366-373`.

The proposal aligns with repo doctrine. The Scripture says the FR is the source of truth at `.github/copilot-instructions.md:33-35`, and names both governing questions: `who_reads_this_when` says the fr-board's only reader was its own generator at `.github/copilot-instructions.md:125-128`, while `where_is_the_repo_boundary` records the fr-board F7 boundary defect at `.github/copilot-instructions.md:130-132`. FR-740 itself confirms the board was created as generated state plus drift lint (`feature-requests/FR-740-fr-pipeline-board.md:47-53`) and later found that a committed board crossed repo boundaries; the binding F7 resolution made cross-repo views ephemeral and terminal-only (`feature-requests/FR-740-fr-pipeline-board.md:194-201`). FR-858's proposed cure extends that same logic to the own-repo committed cache.

The prior-art disposition is adequate in direction. FR-740's valuable behavior is parser/render/gates/question machinery (`scripts/fr_board.py:88-204`, `scripts/fr_board.py:126-148`) and is already covered by tests for status parsing, active-set scoping, gates schema, DAG output, and missing sibling repos (`scripts/tests/test_fr_board.py:66-164`). FR-858 explicitly keeps that machinery and retires only the cache plus freshness ceremony at `feature-requests/FR-858-retire-committed-fr-board.md:49-58` and `feature-requests/FR-858-retire-committed-fr-board.md:67-68`.

The strategic classification is **pattern/process-tooling deletion**, not a framework primitive. It has one concrete in-repo use case, and an established in-repo precedent: FR-179 removed `CHANGELOG.md` from tracking because the monolithic generated file caused conflicts (`feature-requests/FR-179-append-only-changelog.md:12-20`, `feature-requests/FR-179-append-only-changelog.md:37-45`). The current project instructions record that `CHANGELOG.md` is now generated on demand and not tracked (`CLAUDE.md:347-371`), which is the same artifact-class cure FR-858 proposes.

## Required revisions

### R-1: Replace the ambiguous parser-test criterion with explicit test obligations

Fold this into the FR: the existing parser, active-row, render, gates-schema, and missing-project tests remain protected, but the drift-lint test must be removed or rewritten because the committed board freshness contract is being retired. The current test file explicitly pins drift lint at `scripts/tests/test_fr_board.py:14-15` and exercises `check_board()` at `scripts/tests/test_fr_board.py:143-152`; keeping that test unchanged would preserve the very ceremony the FR deletes. Add a new witness test that `python scripts/fr_board.py` renders to stdout and does not create or modify `docs/fr-board.md`.

### R-2: Specify the retired CLI surface

Fold this into the FR: `scripts/fr_board.py` must have no default write-to-docs path and no active `--check` drift-lint mode after enforcement. The current CLI exposes `--out docs/fr-board.md`, `--check`, and a default write at `scripts/fr_board.py:219-258`; leaving any repo-writing mode in place would contradict the Ideal Result's "computed on demand" claim at `feature-requests/FR-858-retire-committed-fr-board.md:39-45` and the acceptance criterion "pure query (no repo write)" at `feature-requests/FR-858-retire-committed-fr-board.md:62-64`.

### R-3: Narrow "no references remain" to active enforcement references

Fold this into the FR: the deletion criterion means no active hook, CI, runtime, or skill instruction may require `docs/fr-board.md` or `fr-board-check`; historical records, prior FRs, diaries, and recaps may continue to mention them as provenance. The current wording at `feature-requests/FR-858-retire-committed-fr-board.md:62` is too broad if read literally, because historical doctrine and diary evidence necessarily cite the board (`docs/diary/diary-2026-08-30-the-gate-that-asked-me-to-forge-evidence.md:91-129`, `feature-requests/FR-740-fr-pipeline-board.md:194-201`).

### R-4: Make `now.py` live-state behavior mechanically checkable

Fold this into the FR: `now.py --brief` and the default `now.py` output must no longer print a `docs/fr-board.md` path; they must compute plan state live from `feature-requests/*.md` via `fr_board` functions or a subprocess with explicit failure surfacing. The current code prints the committed path in brief mode at `scripts/vscode/now.py:327-330` and counts table rows from the committed file in full mode at `scripts/vscode/now.py:366-373`; the revised acceptance criteria must name both modes.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `docs/fr-board.md`: remove the committed generated board from tracking. |
| D-2 | `.pre-commit-config.yaml`: remove the active `fr-board-check` hook only. |
| D-3 | `scripts/fr_board.py`: convert the CLI to stdout-only query behavior; preserve parser/render/gates functionality required by FR-740. |
| D-4 | `scripts/tests/test_fr_board.py`: update tests only for retired drift/write behavior and new stdout/no-write behavior; preserve parser, active-set, gates, DAG, and missing-project coverage. |
| D-5 | `scripts/vscode/now.py`: compute plan-state summary live instead of reading `docs/fr-board.md`, in brief and full modes. |
| D-6 | `.github/skills/session-introspection/SKILL.md`: replace the committed-board instruction with the live command or live plan-state source. |
| D-7 | `feature-requests/FR-858-retire-committed-fr-board.md`: fold this judgement's revisions and record enforcement status/decisions. |
| D-8 | `changelog/unreleased/`: add one removal fragment. |
| D-9 | `docs/diary/`: add one metacognitive reflection entry if the resulting PR type triggers the repo diary gate. |

Not authorized: changes to `reference/module-map.md`, `examples/dependency-taxonomy.yaml`, `ARCHITECTURE.md` capability tables, unrelated generated artifacts named as sibling candidates at `feature-requests/FR-858-retire-committed-fr-board.md:124-132`, FR-board priority semantics, status canonicalization policy, gates.yaml schema beyond preserving current validation, new CI gates, judge/review doctrine, graph-authoring routes, chaplain runtime behavior, or any cross-repo board persistence.

## Revised acceptance criteria

- [ ] AC-01: `docs/fr-board.md` is deleted from tracked files.
- [ ] AC-02: `.pre-commit-config.yaml` contains no active `fr-board-check` hook and no active `scripts/fr_board.py --check` entry.
- [ ] AC-03: No active CI workflow, hook, runtime script, or skill instruction requires `docs/fr-board.md`; historical FR/diary/doc provenance references are not part of this absence gate.
- [ ] AC-04: `python scripts/fr_board.py` prints the own-repo board to stdout, exits 0 when gates are valid, and does not create or modify `docs/fr-board.md`.
- [ ] AC-05: `scripts/fr_board.py` no longer exposes active repo-writing or drift-check CLI modes (`--out` / `--check`), while preserving `collect_rows`, `active_rows`, `validate_gates`, `load_gates`, and `render_board` behavior.
- [ ] AC-06: `scripts/tests/test_fr_board.py` continues to cover status parsing, parse-failure preservation, companion exclusion, active-set scoping, gates validation, rendered table/DAG output, and missing-project notices.
- [ ] AC-07: A test covers the new stdout-only CLI/no-write behavior for `scripts/fr_board.py`.
- [ ] AC-08: `scripts/vscode/now.py --brief` reports plan state from live `fr_board` data and does not print a `docs/fr-board.md` path.
- [ ] AC-09: Default `scripts/vscode/now.py` output reports plan state from live `fr_board` data and does not count rows by reading `docs/fr-board.md`.
- [ ] AC-10: `.github/skills/session-introspection/SKILL.md` routes "What's next?" to the live command/source rather than the committed board file.
- [ ] AC-11: FR-740 is dispositioned in FR-858 as superseding the committed cache plus drift gate, while preserving the parser, gates schema, question drafting, active-set scoping, and ephemeral cross-repo stdout view.
- [ ] AC-12: One `changelog/unreleased/` removal fragment records the user-visible retirement.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1 through R-4 are folded into `feature-requests/FR-858-retire-committed-fr-board.md`. | GATE |
| C-2 | The enforcer must not delete or weaken parser/render/gates behavior protected by FR-740 unless a test is explicitly replaced with an equivalent or stronger witness. | GATE |
| C-3 | The enforcer must not satisfy absence checks by editing historical evidence artifacts, diaries, prior FRs, or recaps merely to remove textual mentions of `docs/fr-board.md`. | GATE |
| C-4 | The enforcer must not implement the sibling-candidate retirement list; those artifacts require separate FRs. | GATE |
| C-5 | If `now.py` cannot compute live plan state, it must surface the failure consistently with existing script error patterns rather than silently reverting to stale committed state. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, the enforcer may retire the committed FR board and drift hook, convert `fr_board.py` to stdout-only query behavior, update `now.py` and the session-introspection skill to consume live plan state, update the FR/changelog/diary artifacts, and adjust only the tests necessary to preserve FR-740 behavior while proving the retired cache no longer writes or gates commits.
