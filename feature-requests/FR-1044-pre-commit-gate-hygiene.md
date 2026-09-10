# Feature Request: Pre-commit gate hygiene — hooks that mutate the tree, version-skewed formatter, line-keyed noqa ledger

**Priority:** MEDIUM
**Type:** Bug
**Status:** SPLIT — no implementation authority
([judgement](FR-1044-pre-commit-gate-hygiene.judgement.md), round 1, 2026-09-10).
Only the planning artifacts D-1…D-5 may be produced under this verdict; the
three successors are unfiled pending the operator decision recorded below.
**Effort:** 1 day
**Requested:** 2026-09-10
**First consumer / first event:** any agent committing a Python edit above an
existing `# noqa` line — the next such commit on main after this lands is the
first event; the witnessed one is PR #652 (nine commit attempts, six full
unit-suite runs, for two substantive changes).
**Research:** in-body dispositioned alternatives table below (FR-889-style
equivalent record). The problem is fully enumerated from one incident log;
a five-persona fan-out would generate alternatives to defects whose fix is
already determined by the hook contract.
**Prior art:** [FR-460](FR-460-cap-architecture-auto-sync.md) — introduced the
`cap-architecture-sync` hook and the test that now mutates the tree; this FR
keeps the hook, fixes the test. [FR-179](FR-179-append-only-changelog.md) — the
"autofix then re-check" hook shape (ruff-format pattern) this FR extends to the
noqa ledger. [FR-1034](FR-1034-census-brief-model-selection.md) (#645) — the
hand-placed `REQ-YG-674/675` rows that the regenerated table removed; no
change to that FR's substance.

## Summary

Four pre-commit gates produced retry loops in PR #652 that were unrelated to
the code being committed. Each is a gate defect, not a workflow defect:

| # | gate | defect | attempts lost |
|---|---|---|---|
| 1 | `pytest (unit only)` | `test_aggregate_script_exits_zero` calls `aggregate_capabilities.main()` without `--dry-run` → rewrites `ARCHITECTURE.md` during the test run → pre-commit reports "files were modified by this hook" and fails | 2 (+1 confusing `req_coverage` "modified" on the restored stash) |
| 2 | `ruff-format` | hook pinned `v0.8.6`; `constraints/*.txt` pins `ruff==0.16.0`; the two format `assert x, (msg)` differently, so every editor-side `ruff format` is undone by the hook | 1 |
| 3 | `noqa_coverage --strict` | confessions are keyed on exact `#L<n>`; inserting lines above any `# noqa` invalidates every entry below it; the fix is manual arithmetic across N entries. CONF-127..132 are stale duplicates of CONF-133..138 left by an earlier drift | 1 |
| 4 | `cap-architecture-sync` | `ARCHITECTURE.md` on main disagreed with `capabilities/` (rows hand-placed by #645), so the first regeneration in any branch produces an unrelated diff | 1 commit |

## Value Statement

Agents and the operator stop paying ~90 s and a log re-read per retry for
gate failures that no code change can prevent.

## Problem

Witnessed on 2026-09-10, PR #652 branch `chorecensus-sessions`:

- Attempt 1: pytest failed on a real (env-pollution) defect — informative.
- Attempt 2: `noqa_coverage` failed; eight `#L` refs shifted by +9.
- Attempt 3: pytest passed (6685) but the suite rewrote `ARCHITECTURE.md` →
  "Stashed changes conflicted with hook auto-fixes… Rolling back".
- Attempt 4: `ruff-format` (0.8.6) re-wrapped assertions that venv ruff
  (0.16.0) had just formatted.
- Attempt 5: `req_coverage` reported "files were modified" — the
  `ARCHITECTURE.md` write from attempt 3 resurfacing.
- Attempt 6: pytest rewrote `ARCHITECTURE.md` again.
- Attempts 7–9: three commits succeeded (regen, test fix, adapter).

Six full unit-suite runs; four of them on unchanged Python under test.

## Ideal Result

A commit attempt fails only when the staged change is wrong. Hooks are
idempotent on a clean tree, agree with the developer environment, and
autofix what they can compute.

## Proposed Solution

### 1. The FR-460 test must not write the repo

`test_aggregate_script_exits_zero` runs `main()` with `sys.argv` patched to
include `--dry-run` (the flag already exists at
`scripts/aggregate_capabilities.py:162`). Witness: the test asserts
`ARCHITECTURE.md` bytes are identical before and after the call. A second,
separate test asserts `main()` (no flag) is idempotent on a synced tree —
i.e. `--dry-run` output equals the committed section — so drift is caught
as a failing test instead of a hook-side write.

### 2. Pin one ruff

`.pre-commit-config.yaml` `ruff-pre-commit` `rev` becomes the version in
`constraints/` (`v0.16.0` today). Witness: a unit test parses both files
and asserts equality, so the next bump cannot skew them. The one-time
repo-wide reformat that the bump produces lands as its own `style:` commit
(`mixed_commits_erode_auditability`).

### 3. noqa ledger: autofix line refs, then check

`scripts/noqa_coverage.py --fix` realigns `#L<n>` for a file when the file's
current `# noqa` set and the ledger's entries for that file match one-to-one
by `(code, order)`; any other shape (added/removed noqa, code change) is left
for `--strict` to report as today. The hook becomes two entries in the
ruff/ruff-format shape: `noqa_coverage --fix` (modifies files, fails once)
then `noqa_coverage --strict`. Stale duplicate entries CONF-127..132 are
deleted in the same change. Witness: fixture ledger + file with N lines
inserted above → `--fix` rewrites refs and `--strict` passes; fixture with
a *new* noqa → `--fix` changes nothing and `--strict` fails.

### 4. `ARCHITECTURE.md` is generated, never hand-edited between markers

Already landed as `7348d9cb` in #652 (regenerated from `capabilities/`).
This FR adds no code for it; item 1's idempotency test is the guard.

### Alternatives considered

| alternative | disposition |
|---|---|
| `scripts/ship.sh` auto-retry on "files were modified by this hook" | rejected: wraps the defect; `infrastructure_self_exempt` — the gate must be right, not tolerated |
| Move the pytest hook to `pre-push` to cut the 90 s per attempt | refused in this FR: a Commandment 7 policy change, not a defect; four wasted runs disappear once items 1–3 stop the retries |
| Key confessions on `(file, code)` only, drop line numbers | rejected: two same-code noqa in one file become indistinguishable; the autofix keeps the line as the identity and repairs it |
| Loosen `noqa_coverage` to warn | rejected: `detection_without_enforcement` |

## Acceptance Criteria

- [ ] `pytest tests/unit/test_fr460_cap_architecture_auto_sync.py` leaves `git status` clean on a synced tree (witness test).
- [ ] `--dry-run` output equals committed `ARCHITECTURE.md` section on main (idempotency test).
- [ ] `ruff-pre-commit` rev == `constraints/` ruff version; test enforces.
- [ ] `noqa_coverage.py --fix` realigns shifted refs; `--strict` still fails on new/removed noqa (two fixture tests).
- [ ] `.pre-commit-config.yaml` runs `--fix` before `--strict`.
- [ ] CONF-127..132 removed; `--strict` passes on main.
- [ ] `@pytest.mark.req` tags; changelog fragment (`fix`, scope `hooks`).
- [ ] Witness run: one commit that inserts a line above a `# noqa` in `tests/unit/test_llm_factory.py` passes pre-commit on the first attempt.

## Judgement fold (round 1, 2026-09-10)

Verdict **SPLIT**. Authority for every surface named in "Proposed Solution" is
withheld. Dispositions:

| # | Revision | Disposition |
|---|---|---|
| R-1 | Refile as three single-responsibility successors | **Accepted, unfiled.** Blocked on the operator decision below: three successors × (research + judge + doc PR + implementation PR) is the FR-1013 shape ("process outgrew the change", REJECTED 2026-09-06). |
| R-2 | Substantive research record per successor | **Accepted.** The in-body table has dispositions but no solution-class labels, no per-class precedent, no preserved disagreement, no `is_this_a_graph` answer. `scripts/research.sh` per successor. |
| R-3 | Human decision on first-invocation policy | **Open — operator input required.** Must a line-shift-only commit pass pre-commit on attempt 1, or is one fix-and-restage cycle acceptable? Under `fail_fast: true` an autofix hook that rewrites an unstaged ledger cannot deliver attempt-1 success; the AC and the hook design contradict each other until this is answered. |
| R-4 | Drop removed-noqa detection from repair scope | **Accepted.** Correct reading of `scripts/noqa_coverage.py:172-183` — strict compares codebase → ledger only, never ledger → codebase. The original AC claimed a detection that does not exist. |
| R-5 | Causal no-write witness, not a byte/`git status` proxy | **Accepted.** `aggregate_capabilities.py` rewrites identical bytes on a synced tree, so both proxies pass while the write still happens. The witness must fail when the write boundary is reached. |
| R-6 | Freeze the ruff source, surface and witness | **Accepted.** Source of truth `constraints/dev-py312.txt`; `v`-prefix normalised in the equality test; the one-time reformat is its own `style:` commit. |
| R-7 | Exact requirement IDs, not "`@pytest.mark.req` tags" | **Accepted.** |

**One factual correction to the judgement (not a revision refused on preference).**
The Consistency row and C-6 state that `ARCHITECTURE.md` still carries the
hand-placed rows and that `7348d9cb` is not landed. Both were evaluated at this
branch's base, which was one commit behind `origin/main`. Witness, after
merging `origin/main` (`abc0e677`, PR #652 squash-merged 2026-09-10 15:57Z):
`python scripts/aggregate_capabilities.py` (real run, not `--dry-run`) leaves
`git status` empty — generated content and `capabilities/` agree on main today.
The SHA `7348d9cb` is indeed not an ancestor (squash rewrote it); its *content*
is. C-6 is therefore satisfied by the base refresh, and item 4 of the Proposed
Solution stays a no-code item. The SPLIT itself, and R-1…R-7, stand unchanged.

## Related

- PR #652 (incident), #645 (hand-placed rows), `scripts/noqa_coverage.py`,
  `scripts/aggregate_capabilities.py`, `tests/unit/test_fr460_cap_architecture_auto_sync.py`,
  `.pre-commit-config.yaml` L5–6, L90–92, L283–286.
