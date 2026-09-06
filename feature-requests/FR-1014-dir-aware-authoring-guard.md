# Feature Request: Dir-aware authoring guard for `graphs/` (Phase 0 of FR-1010)

**Priority:** MEDIUM
**Type:** Enhancement (enforcement hardening)
**Status:** Enforced 2026-09-06 on `fix/fr1014-dir-aware-guard` — RED
`a79664f0`, GREEN `7661a344`; see § Implementation Record. Judged —
APPROVED WITH REVISIONS (2026-09-06), R-1..R-4 folded below; see
[FR-1014-dir-aware-authoring-guard.judgement.md](FR-1014-dir-aware-authoring-guard.judgement.md).
Judgement human-reviewed by the merge of PR #611 (FR-1010 C-1/C-4);
final hook diff reviewed at PR #612 — operator `merge` verdict
2026-09-06 (AC-14, C-2). Diary:
`docs/diary/diary-2026-09-06-reflection-fr-1014-baseline-before-blame.md`.
**Effort:** 0.5 day
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 0 of 5 (FR-1014 → FR-1011 → FR-1015 → FR-1012 → FR-1013); must merge before FR-1011 (FR-1010 C-3)
**First consumer / first event:** FR-1011's `git mv` of
`.chaplain/graphs/fr_triage/` into `graphs/fr_triage/` — the first moment
a dir-style graph enters `graphs/` under a relocation that must run
through `scripts/author.sh`. Without this FR the guard would neither deny
nor require a sentinel for that write, and the FR-767 proof gate would
not see the new files.
**Research:** § Alternatives Considered below — five solution classes with
precedent and disposition (R-4); the verified predicate gap in
[FR-1011 § Guard gap](FR-1011-relocate-chaplain-live-parts.md#guard-gap-verified-2026-09-06-pre-command-guardsh167-171)
is the evidence record. `is_this_a_graph`: **no** — a deterministic
predicate, test, and documentation correction with no LLM stage or corpus
fan-out.
**Prior art:**
- [FR-767-graph-authoring-sole-route.md](FR-767-graph-authoring-sole-route.md)
  — introduced `governed_path()` (`pre-command-guard.sh:164-171`) and the
  `GOVERNED` tuple (`check_authoring_proof.py:20-25`). Its own Tier-2
  witness fixture is `GOVERNED_CHAPLAIN = ".chaplain/graphs/pipeline.yaml"`
  (`.github/hooks/tests/test_authoring_guard.py:27`) — a flat path that
  never existed; every real `.chaplain` graph is `<name>/graph.yaml`. The
  witness tested a phantom (`gate_checks_shape_not_substance`). This FR
  replaces the phantom with real dir-style paths.
- [FR-889-os-enforced-main-write-lock.md](FR-889-os-enforced-main-write-lock.md)
  C-5 — "the kernel is the barrier; the guard covers only what the kernel
  cannot". `graphs/` is **not** in `FR889_GOVERNED_ROOTS`
  (`scripts/worktree.sh:506`), so the authoring guard is the only barrier
  on `graphs/**` writes; its regex must therefore match what is actually
  there.
- [FR-1010](FR-1010-chaplain-archival-plan.md) R-5 / C-4 — this hardening
  was split out of the relocation FR because enforcement-infrastructure
  changes need their own judgement and human review.

## Summary

Make the `graphs/` arm of the governed-path predicate match dir-style
graph artifacts — the contract is **`graphs/<name>/*.yaml` plus
`graphs/<name>/prompts/*.yaml`** (R-1), not only `graph.yaml` — in all
**three** enforcement surfaces: `pre-command-guard.sh` `governed_path()`,
`check_authoring_proof.py` `GOVERNED`, and the `authoring-proof` hook's
`files:` selector in `.pre-commit-config.yaml:34` (added by FR-1011's
judgement R-1: without it a commit containing only `graphs/<name>/graph.yaml`
never invokes the backstop). Keep the flat `graphs/*.yaml` arm, and
replace the phantom `.chaplain` fixture in the Tier-2 witness with a
provenance-labelled truth table (R-2). No other predicate changes. Docs
that publish the flat-only contract are updated.

## Value Statement

The FR-767 sole-route contract becomes true for every graph under
`graphs/` — today it is false for `graphs/enforcement/` and would be
false for the three graphs FR-1011 relocates.

## Problem

`pre-command-guard.sh:167-171`:

```python
re.search(r"(^|/)examples/.+/graph\.ya?ml$", p)
or re.search(r"(^|/)examples/.+/prompts/[^/]+\.ya?ml$", p)
or re.search(r"(^|/)graphs/[^/]+\.ya?ml$", p)
or re.search(r"(^|/)\.chaplain/graphs/[^/]+\.ya?ml$", p)
```

`examples/` is dir-aware (`.+/graph.yaml`, `.+/prompts/*.yaml`);
`graphs/` and `.chaplain/graphs/` are not (`[^/]+\.ya?ml$` = one flat
file). Consequences, verified 2026-09-06:

| Path | Exists | Governed today |
|---|---|---|
| `graphs/enforcement/changelog-req-check.yaml` | yes | **no** |
| `graphs/enforcement/prompts/*.yaml` | yes | **no** |
| `.chaplain/graphs/fr_triage/graph.yaml` (+ world_distill, philosopher, watcher-*) | yes | **no** |
| `.chaplain/graphs/pipeline.yaml` (the test fixture) | **never** | yes |
| `graphs/showcase.yaml` (fixture `GOVERNED_TOP`) | no such file on main | yes |

`check_authoring_proof.py:20-25` mirrors the same four patterns with `^`
anchors and has the same gap. `.pre-commit-config.yaml:34` (the
`authoring-proof` hook's `files:` selector) is a third copy of the flat
contract: `^graphs/[^/]+\.ya?ml$|^\.chaplain/graphs/[^/]+\.ya?ml$`. A
commit whose only governed additions are dir-style never triggers the
backstop at all — the predicate fix alone would be unreachable.

## Ideal Result

One truth table, shared by the Tier-2 hook witness and the Tier-1 proof
witness, on which `governed_path()` and `GOVERNED` agree row for row:

| Path | Provenance | Governed |
|---|---|---|
| `graphs/enforcement/changelog-req-check.yaml` | exists (`git ls-files --error-unmatch`) | True |
| `graphs/enforcement/prompts/cross_check.yaml` | exists | True |
| `graphs/fr_triage/graph.yaml` | FR-1011 will create | True |
| `graphs/fr_triage/prompts/triage_fr.yaml` | FR-1011 will create | True |
| `graphs/fr1014-flat.yaml` | synthetic (flat-arm contract; no committed flat graph exists) | True |
| `graphs/README.md` | negative | False |
| `graphs/fr_triage/tools.py` | negative | False |
| `graphs/fr_triage/nested/graph.yaml` | negative (depth > 1) | False |
| `graphs/fr_triage/prompts/nested/triage.yaml` | negative (depth > 1) | False |

No synthetic path is cited as evidence of current repository shape (R-2).

## Proposed Solution

### RED

`.github/hooks/tests/test_authoring_guard.py`:

- Remove `GOVERNED_CHAPLAIN`; rename `GOVERNED_TOP` →
  `GOVERNED_FLAT_SYNTHETIC = "graphs/fr1014-flat.yaml"` (R-2); add the
  truth-table constants above with a one-line provenance comment each.
- `test_deny_covers_all_governed_paths` parametrised over the positives;
  a new `test_approve_ungoverned_graphs_dir_paths` over the negatives.
  RED shows all three missing classes fail: direct-child YAML, dir-style
  `graph.yaml`, dir-style prompt YAML.
- Tagged `@pytest.mark.req("REQ-YG-423")` (R-3) — the requirement that
  owns the executable graph-authoring route
  (`capabilities/CAP-158-copilot-skill-promotion.yaml:20`).

New `tests/unit/test_fr1014_authoring_proof_dir_graphs.py` (Tier 1,
`@pytest.mark.req("REQ-YG-423")`): imports `GOVERNED` from
`scripts/check_authoring_proof.py` and asserts the same truth table.

`capabilities/CAP-158-copilot-skill-promotion.yaml`: extend REQ-YG-423's
description and module list with `.github/hooks/scripts/pre-command-guard.sh`
and `scripts/check_authoring_proof.py` (R-3). No new REQ.

### GREEN

`pre-command-guard.sh:169`:

```python
or re.search(r"(^|/)graphs/[^/]+/[^/]+\.ya?ml$", p)
or re.search(r"(^|/)graphs/[^/]+/prompts/[^/]+\.ya?ml$", p)
or re.search(r"(^|/)graphs/[^/]+\.ya?ml$", p)
```

`check_authoring_proof.py:23`: the `^`-anchored equivalents.
`.pre-commit-config.yaml:34`: `files:` gains `^graphs/[^/]+/[^/]+\.ya?ml$`
and `^graphs/[^/]+/prompts/[^/]+\.ya?ml$`. The `.chaplain/graphs` arm in
all three surfaces is **left in place** by this FR (FR-1011 deletes it —
one concern per FR). `:187` pre-filter unchanged.

Docs (R-4, mandatory): `scripts/check_authoring_proof.py:8-10` docstring
and `.github/hooks/README.md:82-86` enumerate `graphs/<name>/*.yaml` and
`graphs/<name>/prompts/*.yaml` alongside flat `graphs/*.yaml`.

### Witness

`pytest .github/hooks/tests/test_authoring_guard.py tests/unit/test_fr1014_authoring_proof_dir_graphs.py -q`
green; a manual `create_file` payload for `graphs/enforcement/prompts/x.yaml`
through the hook returns `deny` with `author.sh` in the message;
`git ls-files --error-unmatch` succeeds for every row labelled "exists";
selector witness: `pre-commit run authoring-proof --files graphs/fr1014-probe/graph.yaml`
(file staged as a temporary addition, then unstaged) invokes the hook —
recorded as command + output in the Implementation Record.

## Acceptance Criteria

- [ ] `governed_path()`, `GOVERNED`, and the `.pre-commit-config.yaml:34`
      `files:` selector agree on every row of the truth table in
      § Ideal Result (the selector is checked with `pre-commit run
      authoring-proof --files <path>` for each positive; a
      `pass_filenames: false` hook still gates on `files:`).
- [ ] RED commit shows the three missing classes failing (direct-child
      YAML, dir-style `graph.yaml`, dir-style prompt); GREEN commit
      follows; both in `git log`.
- [ ] `GOVERNED_CHAPLAIN` is gone; `GOVERNED_FLAT_SYNTHETIC` is labelled
      synthetic; every path labelled "exists" passes
      `git ls-files --error-unmatch`.
- [ ] Both witnesses carry `REQ-YG-423`; CAP-158 lists the two guard
      modules; `req_coverage --strict` and `validate_capabilities --strict`
      green.
- [ ] `examples/` arms and the `.chaplain/graphs` arm are byte-identical
      before and after in all three surfaces (diff touches only the
      `graphs/` lines).
- [ ] `check_authoring_proof.py:8-10` and `.github/hooks/README.md:82-86`
      state the dir-style contract.
- [ ] Human review recorded in this FR before merge (FR-1010 C-4).
- [ ] Changelog fragment `changelog/unreleased/fr-1014-dir-aware-authoring-guard.md`.

## Purge list

- No new governed root; no change to `FR889_GOVERNED_ROOTS`.
- No change to the sentinel mechanism or `author.sh`.
- No deletion of the `.chaplain` arm (FR-1011).

## Alternatives Considered (R-4: five solution classes)

| # | Class | Precedent | Disposition |
|---|---|---|---|
| 1 | **Root-scoped direct-YAML + prompts predicate** (`graphs/<name>/*.yaml`, `graphs/<name>/prompts/*.yaml`, flat kept) | FR-767's `examples/` arms are already dir-aware; `graphs/enforcement/` is the only committed dir-style graph and its spec is not named `graph.yaml` | **Selected** — the smallest change that makes the FR's own positive rows true |
| 2 | Fold into FR-1011 (first-draft option (a)) | FR-1010 R-5 | Rejected — enforcement hardening needs its own human gate; "pure relocation" and "newly governs `graphs/enforcement/`" are different claims |
| 3 | Add `graphs` to `FR889_GOVERNED_ROOTS` (kernel lock) | FR-889 | Rejected — locks `tools.py` and READMEs on main too; the sole-route contract is per-artifact, not a write barrier. Different instrument |
| 4 | Repository-global `.+/graph\.ya?ml$` | — | Rejected — governs `tmp/`, `projects/`, `ramp/assets/`; FR-767 chose explicit roots deliberately |
| 5 | Flatten graph layouts (`graphs/fr_triage.yaml` + shared `prompts/`) so the flat arm suffices | — | Rejected — breaks `prompts_relative: true` used by all three relocating graphs and by `graphs/enforcement/` |

Preserved disagreement: §1 vs the first-draft `([^/]+/)*graph\.ya?ml$`
arm. The draft matched only files literally named `graph.yaml` and would
have failed its own `changelog-req-check.yaml` positive; the judge's
one-directory `[^/]+/[^/]+\.ya?ml$` is broader (any YAML one level down)
and accepts that a stray `graphs/<name>/notes.yaml` becomes governed —
a cost judged smaller than an ungoverned graph spec.

## Related

- FR-1010 (plan), FR-1011 (Phase 1, depends on this)
- `.github/hooks/README.md:82-86` and `scripts/check_authoring_proof.py:8-10`
  — publish the governed-path contract; updated in GREEN.

## Implementation Record (2026-09-06, Windows host, branch `fix/fr1014-dir-aware-guard`)

| Step | Commit | Command | Result |
|---|---|---|---|
| RED | `a79664f0` `test(hooks): FR-1014 RED — dir-style graphs/ paths are ungoverned on all three surfaces` | `pytest tests/unit/test_fr1014_authoring_proof_dir_graphs.py -q --no-cov` | **12 failed, 27 passed** — the 4 positive dir-style rows fail on each of the 3 surfaces (`GOVERNED`, `governed_path()`, `files:` selector); the flat row, all 4 negatives, and the provenance rows pass. Not a fixture/import failure (C-5). |
| RED | same | manual PreToolUse payloads `create_file` for every truth-table row through `bash .github/hooks/scripts/pre-command-guard.sh` | 4 dir-style positives **approve** (the gap); `graphs/fr1014-flat.yaml` deny; 4 negatives approve. |
| GREEN | `7661a344` `fix(hooks): FR-1014 GREEN — dir-aware graphs/ arm on guard, proof script and selector` | same Tier-1 command | **39 passed** |
| GREEN | same | same manual payloads, plus `examples/demos/hello/graph.yaml`, `.chaplain/graphs/pipeline.yaml`, `docs/notes.md` | all 5 positives **deny** with `author.sh` in the reason; all 4 negatives approve; examples/ and .chaplain arms unchanged (deny); ungoverned docs approve. |
| AC-11 | `7661a344` | payload `create_file graphs/enforcement/prompts/x.yaml` | `permissionDecision: deny`, reason names `scripts/author.sh <task-brief.md>`. |
| AC-08 | `7661a344` | `git diff -U0 a79664f0..7661a344 -- .github/hooks/scripts/pre-command-guard.sh scripts/check_authoring_proof.py .pre-commit-config.yaml` | Only added lines are the two `graphs/[^/]+/[^/]+\.ya?ml` and `graphs/[^/]+/prompts/[^/]+\.ya?ml` arms per surface, the two docstring/comment lines that enumerate them, and the selector alternation. `examples/`, `.chaplain/graphs`, terminal pre-filter, sentinel code, denial wording untouched. |
| Selector | `7661a344` | `git add graphs/fr1014-probe/graph.yaml && pre-commit run authoring-proof --files graphs/fr1014-probe/graph.yaml` (probe unstaged and deleted afterwards) | The selector **invoked the hook** (`authoring proof … Failed / Executable .venv/bin/python not found`) — selection witnessed; execution of the entry is impossible on this Windows host (`.venv/Scripts/`, no `.venv/bin/`). The selector regex is additionally asserted row-for-row by `test_authoring_proof_selector_matches_truth_table`. |
| Gates | both | `validate_capabilities.py --strict`, `req_coverage.py --strict`, `aggregate_capabilities.py`, `aggregate_changelog.py`, `ruff check` | all green |
| Suite | `7661a344` | `pytest tests/unit -q --no-cov -m "not slow" -n auto` on the branch **and** on main `6e3bbd66` | Identical 284 platform failures on both (WSL/bash-only tests on Windows); the one branch-only failure (`test_no_req_collision_across_unrelated_frs`) was fixed in GREEN by `CAP-158 fr: FR-446, FR-1014`. |

**Owed by a POSIX host / CI (AC-10, AC-06 Tier-2 half):**
`pytest .github/hooks/tests/test_authoring_guard.py -q --no-cov` cannot run
here — the test execs the bash hook directly (`WinError 193`), a
limitation of the test harness, not of the change. The same payloads were
driven through the hook via `bash` (rows above); the pytest run is owed at
the implementation PR's CI or the mac.
`scripts/noqa_coverage.py --strict` is likewise CI-owed: on Windows it
reports every noqa in the tree as undocumented (backslash paths never
match the forward-slash confession links; main shows 230/230 the same
way). CONF-461 is written in the documented form; the branch count is
231 noqa / 322 confessions, main 230 / 321.

### Decisions and deviations

1. **Marker layout (AC-07).** The Tier-2 file had a module-level
   `pytestmark = REQ-YG-527`; every test in it would have inherited
   CAP-192's requirement, including the FR-1014 witnesses. Replaced by
   per-test decorators: `_REQ_FR767` (REQ-YG-527) on the FR-767 tests,
   `_REQ_FR1014` (REQ-YG-423) on the two truth-table tests. No coverage
   effect: `req_coverage` excludes `.github/hooks/tests`.
2. **Tier-1 witness covers all three surfaces.** Beyond `GOVERNED`, the
   test extracts `def governed_path` from the guard's Python heredoc and
   executes it, and parses the `authoring-proof` `files:` regex from
   `.pre-commit-config.yaml`; AC-02's row-for-row agreement is asserted
   in one place. The `exec` carries a `noqa: S102` (the text being
   executed is the repository's own hook source) — see
   `docs/confessions.md` CONF-461.
3. **`pytest.mark.process`** added to the Tier-1 module: the FR-756
   process-boundary gate requires it for unit modules that read
   `scripts/`.
4. **CAP-158 `fr:`** extended to `FR-446, FR-1014` (repo convention for
   a capability serving several FRs) so the fragment's REQ-YG-423 claim
   passes `test_no_req_collision_across_unrelated_frs`.
5. **Fragment type `fix`** per judgement D-7; FR-1010's phase list named
   the commit `feat(hooks)`. The PR title follows the fragment.
6. **Guard comment** (`pre-command-guard.sh:143-145`) updated as
   enumerating documentation; the denial message text is unchanged
   (judgement: "denial wording except as required by the existing
   assertion").
7. The FR-1010 phase count is five (FR-1015 was added by R-2); the Plan
   line above now says so.

### Acceptance criteria — status

| AC | Status | Evidence |
|---|---|---|
| AC-01 research | met | § Alternatives Considered (five classes), `is_this_a_graph: no` |
| AC-02 three-way agreement | met | `test_hook_and_proof_predicates_agree`, `test_authoring_proof_selector_matches_truth_table`, 39 passed |
| AC-03 provenance | met | `test_exists_rows_are_tracked`, `test_synthetic_and_fr1011_rows_are_absent`; labels on every constant |
| AC-04 RED | met | `a79664f0`, `SKIP=pytest`, 12 failed = 4 dir-style rows × 3 surfaces (direct-child YAML, dir `graph.yaml`, dir prompt); negatives allowed |
| AC-05 authorized arms only | met | AC-08 diff row |
| AC-06 Tier-2 deny/allow | met via `bash` probes; **pytest run owed** (POSIX) | GREEN probe row |
| AC-07 REQ-YG-423 / CAP-158 | met | both witnesses tagged; CAP-158 lists guard, proof script, both witnesses; `ARCHITECTURE.md` regenerated; no witness on CAP-211/REQ-YG-527 |
| AC-08 byte-identical arms | met | diff row |
| AC-09 docs | met | `check_authoring_proof.py` docstring, `.github/hooks/README.md` |
| AC-10 focused tests + req_coverage | Tier-1 met, req_coverage met; **Tier-2 pytest owed** (POSIX) | Gates row |
| AC-11 direct payload | met | AC-11 row |
| AC-12 RED before GREEN, SHAs recorded | met | this table |
| AC-13 fragment | met | `changelog/unreleased/fr-1014-dir-aware-authoring-guard.md`, `aggregate_changelog.py` ok |
| AC-14 human review of final diff | met | Operator verdict `merge` given 2026-09-06 on PR #612 after the review draft (`scripts/review.sh 612`, verdict *Not approved* on P1 diary / P2 this record; both dispositioned in the PR comment). Reviewed enforcement diff: `7661a344` (guard, proof script, selector). The command book records that a `merge` given in the operator sequence is permission to proceed (FR-1007 R-5). |
| AC-15 merges before FR-1011 | pending | FR-1011 not started |

## Judgement (2026-09-06)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1014-dir-aware-authoring-guard.judgement.md](FR-1014-dir-aware-authoring-guard.judgement.md).
R-1 (predicate contract `graphs/<name>/*.yaml`; the draft regex would
have failed its own positive), R-2 (fixture provenance; synthetic flat
path labelled), R-3 (REQ-YG-423 / CAP-158 binding), R-4 (five-class
research, local `is_this_a_graph`, mandatory docs) folded above.
Amended 2026-09-06 by FR-1011's judgement R-1: the `.pre-commit-config.yaml:34`
`files:` selector is the third surface and is in this FR's scope.
