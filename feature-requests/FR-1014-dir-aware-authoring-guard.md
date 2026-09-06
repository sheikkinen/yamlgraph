# Feature Request: Dir-aware authoring guard for `graphs/` (Phase 0 of FR-1010)

**Priority:** MEDIUM
**Type:** Enhancement (enforcement hardening)
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-06). R-1..R-4 folded
below; see [FR-1014-dir-aware-authoring-guard.judgement.md](FR-1014-dir-aware-authoring-guard.judgement.md).
Implementation authority activates after human review of the judgement
(FR-1010 C-4).
**Effort:** 0.5 day
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 0 of 4; must merge before FR-1011 (FR-1010 C-3)
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

## Judgement (2026-09-06)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1014-dir-aware-authoring-guard.judgement.md](FR-1014-dir-aware-authoring-guard.judgement.md).
R-1 (predicate contract `graphs/<name>/*.yaml`; the draft regex would
have failed its own positive), R-2 (fixture provenance; synthetic flat
path labelled), R-3 (REQ-YG-423 / CAP-158 binding), R-4 (five-class
research, local `is_this_a_graph`, mandatory docs) folded above.
Amended 2026-09-06 by FR-1011's judgement R-1: the `.pre-commit-config.yaml:34`
`files:` selector is the third surface and is in this FR's scope.
