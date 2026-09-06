# Feature Request: Dir-aware authoring guard for `graphs/` (Phase 0 of FR-1010)

**Priority:** MEDIUM
**Type:** Enhancement (enforcement hardening)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 0 of 4; must merge before FR-1011 (FR-1010 C-3)
**First consumer / first event:** FR-1011's `git mv` of
`.chaplain/graphs/fr_triage/` into `graphs/fr_triage/` — the first moment
a dir-style graph enters `graphs/` under a relocation that must run
through `scripts/author.sh`. Without this FR the guard would neither deny
nor require a sentinel for that write, and the FR-767 proof gate would
not see the new files.
**Research:** [FR-1010 § Alternatives Considered](FR-1010-chaplain-archival-plan.md#alternatives-considered-r-1-six-solution-classes)
and [FR-1011 § Guard gap](FR-1011-relocate-chaplain-live-parts.md#guard-gap-verified-2026-09-06-pre-command-guardsh167-171)
— the verified predicate gap is this FR's evidence; the alternatives
table below is its solution-class record.
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
graph artifacts (`graphs/<name>/graph.yaml`, `graphs/<name>/prompts/*.yaml`)
in both `pre-command-guard.sh` and `check_authoring_proof.py`, keep the
flat `graphs/*.yaml` arm, and replace the phantom `.chaplain` fixture in
the Tier-2 witness with real dir-style cases. No other predicate changes.

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
anchors and has the same gap.

## Ideal Result

`governed_path("graphs/fr_triage/graph.yaml")`,
`governed_path("graphs/fr_triage/prompts/triage.yaml")` and
`governed_path("graphs/enforcement/changelog-req-check.yaml")` return
True; `governed_path("graphs/README.md")` and
`governed_path("graphs/fr_triage/tools.py")` return False; the flat arm
still matches `graphs/showcase.yaml`; `check_authoring_proof.py` agrees on
every one of those inputs; the Tier-2 witness parametrises over real
paths and none that never existed.

## Proposed Solution

### RED

`.github/hooks/tests/test_authoring_guard.py`:

- Replace `GOVERNED_CHAPLAIN` with `GOVERNED_DIR = "graphs/enforcement/changelog-req-check.yaml"`
  and add `GOVERNED_DIR_GRAPH = "graphs/fr_triage/graph.yaml"`,
  `GOVERNED_DIR_PROMPT = "graphs/fr_triage/prompts/triage.yaml"` (the
  paths FR-1011 will create — the guard must deny unsentineled writes to
  them *before* they exist, exactly as it does for `GOVERNED_CREATE`).
- Add negatives: `graphs/README.md`, `graphs/fr_triage/tools.py`.
- `test_deny_covers_all_governed_paths` parametrised over the new set →
  RED for the two dir-style positives.

New `tests/unit/test_fr1014_authoring_proof_dir_graphs.py` (Tier 1, tagged
with FR-767's REQ — locate via `grep -l FR-767 capabilities/`; if none
exists, this FR adds none and the test carries CAP-211's REQ as the
nearest sole-route capability, stated explicitly in the PR):

- imports `GOVERNED` from `scripts/check_authoring_proof.py` and asserts
  the same positive/negative table.

### GREEN

`pre-command-guard.sh:169`:

```python
or re.search(r"(^|/)graphs/([^/]+/)*graph\.ya?ml$", p)
or re.search(r"(^|/)graphs/.+/prompts/[^/]+\.ya?ml$", p)
or re.search(r"(^|/)graphs/[^/]+\.ya?ml$", p)
```

`check_authoring_proof.py:23`: the `^`-anchored equivalents. The
`.chaplain/graphs` arm is **left in place** by this FR (FR-1011 deletes
it — one concern per FR). `:187` pre-filter unchanged.

### Witness

`pytest .github/hooks/tests/test_authoring_guard.py tests/unit/test_fr1014_authoring_proof_dir_graphs.py -q`
green; a manual `create_file` payload for `graphs/enforcement/prompts/x.yaml`
through the hook returns `deny` with `author.sh` in the message.

## Acceptance Criteria

- [ ] `governed_path()` and `GOVERNED` return True for
      `graphs/<name>/graph.yaml`, `graphs/<name>/prompts/<p>.yaml`,
      `graphs/enforcement/changelog-req-check.yaml`, `graphs/<flat>.yaml`;
      False for `graphs/README.md`, `graphs/<name>/tools.py`.
- [ ] `.github/hooks/tests/test_authoring_guard.py` contains no path that
      does not exist or is not about to be created by a judged FR;
      `GOVERNED_CHAPLAIN` is gone.
- [ ] RED commit (failing witnesses, `SKIP=pytest`) precedes GREEN commit
      in `git log`.
- [ ] `examples/` arms and the `.chaplain/graphs` arm are byte-identical
      before and after (diff touches only the `graphs/` lines).
- [ ] Human review recorded in this FR before merge (FR-1010 C-4).
- [ ] Changelog fragment `changelog/unreleased/fr-1014-dir-aware-authoring-guard.md`.

## Purge list

- No new governed root; no change to `FR889_GOVERNED_ROOTS`.
- No change to the sentinel mechanism or `author.sh`.
- No deletion of the `.chaplain` arm (FR-1011).

## Alternatives Considered

| Option | Why not |
|---|---|
| Fold into FR-1011 (first-draft option (a)) | FR-1010 R-5: enforcement hardening is a separate responsibility with its own human gate; "pure relocation" and "newly governs `graphs/enforcement/`" are different claims. |
| Add `graphs` to `FR889_GOVERNED_ROOTS` (kernel lock) instead | Would lock `graphs/` on main entirely, including `tools.py` and READMEs; the authoring guard's job is the *sole-route* contract for graph artifacts specifically, not a write barrier. Different instrument. |
| Generic `.+/graph\.ya?ml$` anywhere in the repo | Over-broad: would govern `tmp/`, `projects/`, `ramp/assets/`; FR-767 chose explicit roots deliberately. |
| Leave flat; require FR-1011 to place graphs flat (`graphs/fr_triage.yaml` + shared `prompts/`) | Breaks `prompts_relative: true` layout the three graphs use and the `graphs/enforcement/` precedent. |

## Related

- FR-1010 (plan), FR-1011 (Phase 1, depends on this)
- `.github/hooks/README.md` — PreToolUse contract; one sentence on
  dir-style coverage if it enumerates governed patterns.

## Judgement (pending)
