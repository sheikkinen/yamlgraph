# Feature Request: Subtree-split `.chaplain/` to a source-only archive and remove the runtime (Phase 2 of FR-1010)

**Priority:** MEDIUM
**Type:** Enhancement (subtraction; destructive — human gates C-4)
**Status:** Proposed
**Effort:** 2 days (census 0.5, removal 1, verification 0.5)
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 2 of 5; prerequisites FR-1014, FR-1011, FR-1015 **merged**, FR-1011's inbox manifest recorded and `.chaplain/inbox/` confirmed empty (FR-1010 C-3, C-5)
**First consumer / first event:** `scripts/vscode/now.py` and the next
session briefing, at the first session start after merge — `.chaplain/`
no longer appears in any orientation surface, and `req_coverage --strict`
reports a registry without ~27 CAPs describing a runtime nobody runs.
Second: whoever runs `git tag --list chaplain-archive` a year from now.
**Research:** [FR-1010 § Alternatives Considered](FR-1010-chaplain-archival-plan.md#alternatives-considered-r-1-six-solution-classes)
(six classes; §3 source-only subtree archive selected) and
`reference/patterns/corpus-map-reduce.md` (the census contract).
`is_this_a_graph`: **yes** for the disposition census (`for each test
file / CAP, ask the model`); **no** for the split, tag, rm, and CAP status
edits, which are deterministic.
**Prior art:**
- [FR-276-retire-old-pipeline-scripts.md](FR-276-retire-old-pipeline-scripts.md),
  [FR-317-retire-obsolete-watcher2-components.md](FR-317-retire-obsolete-watcher2-components.md)
  — partial retirements inside `.chaplain/`; both required path/doc/CAP/test
  reconciliation in the same change. Same discipline, whole directory.
- [FR-465-watcher2-test-cleanup.md](FR-465-watcher2-test-cleanup.md),
  [FR-466-cap-retirement-support.md](FR-466-cap-retirement-support.md)
  — `status: retired` on CAP files; `req_coverage.py` excludes retired
  CAPs; dead tests deleted in the same commit as the CAP transition so
  FR-701's gate (live mark on retired REQ) never fires between commits.
- [FR-701-capability-registry-consistency-gate.md](FR-701-capability-registry-consistency-gate.md)
  — the gate this FR must satisfy at every commit; **not modified** (C-7).
- [FR-851](FR-851-requirement-witness-audit.md) / `examples/demos/req_witness_audit`
  — the census shape reused here: deterministic constructor → haiku-tier
  map → deterministic reducer with boundary reconciliation; raw results
  persisted before reduction.
- [FR-1015-supersede-id-ledger-under-fr-1010.md](FR-1015-supersede-id-ledger-under-fr-1010.md)
  — the authority under which the legacy ID-registry artifacts become
  `delete` rows.
- [FR-889-os-enforced-main-write-lock.md](FR-889-os-enforced-main-write-lock.md)
  — `.chaplain/` is `dr-xr-xr-x` on the main checkout though not in
  `FR889_GOVERNED_ROOTS` (a residue); `git rm` in a worktree is unaffected,
  but the post-merge `sync` on main must succeed — witnessed in AC.

## Summary

Produce an exact, model-assisted disposition census of every test file and
CAP that references the Chaplain runtime; publish the runtime's history as
a **source-only** archived repository and a tag; then delete `.chaplain/`
and everything the census marks `delete`, retire the CAPs it marks
`retire`, and leave `docs/archive/chaplain.md` as the one paragraph that
says where it went. Every commit in the PR leaves `req_coverage --strict`,
`validate_capabilities --strict`, and the full non-slow unit suite green.

## Value Statement

The registry stops claiming ~27 capabilities and ~50 test files for a
runtime that has not run since 2026-07-07; agents stop paying orientation
cost for it; the FSM's history stays one URL away.

## Problem

After FR-1011 and FR-1015, `.chaplain/` contains only the dead FSM runtime
(`config/`, `actions/`, `lib/watcher/`, `scripts/`, `demos/watcher2-*`,
`graphs/watcher-*`, `inquisitor.sh`, `philosopher.sh`, `id-registry.yaml`,
`done/`, `processing/`, `README.md`) — 161 tracked files. Coupled to it:

| Class | Count (2026-09-06) | Disposition mechanism |
|---|---|---|
| `tests/**/*.py` referencing `.chaplain`/`inquisitor` | 59 files, ~730 tests (minus FR-1011's four relocated files) | census |
| `capabilities/CAP-*.yaml` naming chaplain/watcher/inquisitor/philosopher/inbox/triage/distill | 27 (4 already retired; CAP-75/205/206 relocated by FR-1011, kept) | census |
| `.github/hooks/tests/` (Tier 2) | 1 file — already fixed by FR-1014 | verify only |
| `scripts/` | `id_registry.py`, `validate_id_registry.py`, `chaplain-prompts/` | census (`delete` under FR-1015) |
| `.pre-commit-config.yaml` | `validate-id-registry` hook | delete with its script |
| `.github/skills/chaplain-ops/` | whole skill | delete |
| `.gitignore` | `.chaplain/` entries | delete |

The hazard the census exists for: **shared REQ fan-in**. A CAP may carry a
REQ that a non-chaplain test also marks; retiring the CAP then trips
`req_coverage --strict` (live mark on retired REQ), and deleting the test
without retiring the CAP trips it the other way. Hand-classifying 59 files
× their REQ sets is the `impossibly_large_sequential_task` signal; the
census computes fan-in in code and asks the model only the semantic
question ("does this test witness the runtime, or a still-live behaviour
that happens to mention it?").

## Ideal Result

`git ls-files .chaplain | wc -l` → 0. `git ls-remote --tags origin chaplain-archive`
→ the pre-removal SHA. `gh repo view sheikkinen/yamlgraph-chaplain --json isArchived`
→ `true`, and its README's first line says it is historical source, not a
runnable distribution. `docs/census/chaplain-test-disposition.jsonl` names
every test file and CAP with `keep|delete|retire`, a reason, and REQ
fan-in; the PR deletes exactly the `delete` rows and retires exactly the
`retire` rows. `req_coverage --strict` reports N covered / N total with
no `.chaplain` path anywhere in its output. `docs/archive/chaplain.md`
exists. `scripts/vscode/now.py` prints no `.chaplain` string.

## Proposed Solution

### Step 0 — Census (committed before any deletion; R-7)

A graph under `examples/demos/chaplain_disposition_census/` (authored via
`scripts/author.sh`; precedent `req_witness_audit`):

- **Constructor (deterministic, `tools.py`):** enumerate
  `grep -rlE '\.chaplain|inquisitor|watcher2|philosopher' tests/ --include='*.py'`
  ∪ the 27 CAP files; for each test file extract `@pytest.mark.req` IDs
  (AST, reuse `scripts/req_coverage.py`'s extractor); for each REQ compute
  **fan-in** = number of marking tests *outside* the candidate set; for
  each CAP list its REQs and current `status`. Freeze as
  `tmp/chaplain-census-input.jsonl` with SHA-256 of every file
  (invariants 1, 5, 6).
- **Map (haiku-tier, one call per test file / CAP):** input = file text +
  its REQ/fan-in facts; output typed `{id, verdict: keep|delete|retire,
  reason, cites: [line refs]}`. Verdict rule stated in the prompt: a test
  whose every REQ has fan-in 0 and whose subject is the runtime → `delete`;
  a test marking any REQ with fan-in > 0 → `keep` unless the *test itself*
  only exercises `.chaplain` paths, in which case `delete` **and** flag the
  REQ for manual read; a CAP whose modules are all under `.chaplain/` or
  deleted tests → `retire`.
- **Canary (invariant 8):** two withheld known-truths — one file that is
  certainly `delete` (`tests/unit/test_fr305_watcher_pipeline_v2.py`) and
  one that is certainly `keep` (`tests/unit/test_fr_triage.py`, relocated
  by FR-1011); matched by family (verdict class), not exact reason text.
  Absence of either invalidates the run before any artifact is emitted.
- **Reducer (deterministic):** reconcile model-emitted IDs against the
  constructor's list (invariant 4); any missing result fails the run
  (invariant 7); write `docs/census/chaplain-test-disposition.jsonl` and a
  `.md` summary with counts computed in code; record provider, model, run
  id (invariant 6). Raw map outputs preserved under
  `docs/census/chaplain-test-disposition.raw/` and **read by a human**
  before the reduction is trusted (`read_raw_output_first`; FR-1010 AC-09).

Cost: ~86 items × ~3k tokens × haiku pricing — cents. Hand-classification
is the fallback only if the route is unavailable, and must then satisfy the
same schema.

### Step 1 — Archive (human gate C-4 before push)

```bash
git tag chaplain-archive <pre-removal SHA on main>        # after FR-1015 merge
git push origin chaplain-archive
git subtree split -P .chaplain -b chaplain-archive-src <that SHA>
gh repo create sheikkinen/yamlgraph-chaplain --private --description "Historical source of the YAMLGraph Chaplain FSM runtime (2026-03 → 2026-09). Not runnable standalone."
git push git@github.com:sheikkinen/yamlgraph-chaplain.git chaplain-archive-src:main
# add README.md (first line: "Historical source snapshot — not a runnable distribution."; pointer back to yamlgraph tag + docs/archive/chaplain.md)
gh repo archive sheikkinen/yamlgraph-chaplain --yes
```

Private-vs-public is the operator's call at the gate; the FR defaults to
private. The archive README is the only file added on top of the split.

### Step 2 — Removal (one PR; RED → GREEN; human gate C-4 before merge)

RED (`SKIP=pytest`): `tests/unit/test_fr1012_chaplain_removed.py` asserting
`.chaplain/` absent, `chaplain-ops/` absent, `validate-id-registry` not in
`.pre-commit-config.yaml`, `docs/archive/chaplain.md` present with the tag
and URL, every census `delete` path absent, every census `retire` CAP has
`status: retired` + `retired_by: FR-1012`, and no `.chaplain` string in
`scripts/vscode/now.py` output. Tagged with a REQ of CAP-165
(`watcher2-baseline-dead-code-removal`, the removal-witness precedent) if
its REQ text fits, or, if not, the FR files a one-REQ CAP
`CAP-XXX-chaplain-runtime-retired.yaml` — decided at RED, stated in the PR.

GREEN, in this commit order so every commit is gate-green:

1. CAP `retire` rows → `status: retired`, `retired_by: FR-1012` **and** the
   census `delete` test files removed, **same commit** (FR-465/466 pattern;
   FR-701 gate).
2. `git rm -r .chaplain .github/skills/chaplain-ops scripts/chaplain-prompts scripts/id_registry.py scripts/validate_id_registry.py`;
   remove the `validate-id-registry` hook block; drop `.chaplain/` lines
   from `.gitignore`; `python scripts/aggregate_capabilities.py` →
   `ARCHITECTURE.md`.
3. `docs/archive/chaplain.md`: one paragraph (what it was, when it ran,
   why archived), the tag, the repo URL and archive status, and a
   replacement table (dispatcher → operator + `scripts/author.sh`/`judge.sh`/`review.sh`;
   inbox → `proposals/`; fr_triage/world_distill/philosopher → `graphs/`;
   finalize_lib → `scripts/lib/`; id-registry → enumeration at filing +
   FR-701; inquisitor → none, retired).
4. Changelog fragment `type: removal`.

### Step 3 — Post-merge witness

On the main checkout: `scripts/worktree.sh sync` succeeds (the 555
`.chaplain` dir is gone with the tree; if `git` cannot unlink it, the
recorded fix is `chmod u+w .chaplain` **before** sync — noted in the PR).
`python scripts/vscode/now.py` output contains no `.chaplain`.

## Acceptance Criteria

- [ ] AC-01: `docs/census/chaplain-test-disposition.jsonl` committed
      **before** any deletion commit; every row has `id, verdict, reason,
      reqs, fan_in, cites`; `.run.json` records provider/model/run-id/input
      SHA; both canaries surfaced; raw outputs committed and a human
      read-through recorded in the PR.
- [ ] AC-02: The set of deleted test files == census `delete` rows; the set
      of CAPs transitioned to `retired` == census `retire` rows (checked by
      `test_fr1012_chaplain_removed.py` reading the jsonl).
- [ ] AC-03: `git ls-files .chaplain .github/skills/chaplain-ops scripts/chaplain-prompts scripts/id_registry.py scripts/validate_id_registry.py`
      → empty; `grep -c validate-id-registry .pre-commit-config.yaml` → 0.
- [ ] AC-04: `python scripts/req_coverage.py --strict`,
      `python scripts/validate_capabilities.py --strict`,
      `pytest tests/unit -q -m "not slow" -n auto`, `lint-imports` green
      at **every** commit of the PR (checked via `git rebase -x`).
- [ ] AC-05: `git ls-remote --tags origin chaplain-archive` → the SHA
      recorded in `docs/archive/chaplain.md`.
- [ ] AC-06: `gh repo view sheikkinen/yamlgraph-chaplain --json isArchived -q .isArchived`
      → `true`; a fresh clone's `README.md` first line contains
      "not a runnable distribution"; `git -C <clone> ls-files | wc -l` ==
      161 + 1.
- [ ] AC-07: `docs/archive/chaplain.md` contains the tag, URL, archive
      status, and the replacement table with every row of FR-1010's
      live-parts table accounted for.
- [ ] AC-08: `python scripts/vscode/now.py | grep -c '\.chaplain'` → 0;
      `python scripts/aggregate_capabilities.py` produces no diff.
- [ ] AC-09: Human review recorded in this FR **before** the tag push,
      repo creation, and PR merge (FR-1010 C-4); the FR-1011 inbox manifest
      and empty-inbox confirmation are linked (C-5).
- [ ] AC-10: FR-1010 live-parts table unchanged; any new live artifact
      stops enforcement (C-10).
- [ ] AC-11: Changelog fragment `changelog/unreleased/fr-1012-chaplain-runtime-removed.md`.

## Purge list

- No symlink, stub, or `README.md` left at `.chaplain/`.
- No "deprecated" shim for `validate_id_registry.py`.
- No edits to FR-701's gate.
- No runnable-standalone claim anywhere (FR-1010 C-8).

## Alternatives Considered

| Option | Why not |
|---|---|
| Hand-classify the 59 files | `impossibly_large_sequential_task`; fan-in arithmetic by hand is exactly the error class the census exists to remove. |
| Delete tests first, retire CAPs in a later commit | FR-701's gate is red in between; FR-465 established same-commit. |
| Skip the archive repo, tag only (FR-1010 §2) | Viable; FR-1010 selected §3 for a browsable URL. Zero difference on `main`. |
| Public archive repo | Operator's call at the gate; default private because `done/` and `failed/` are ignored today and the split will carry only tracked files, but the FR texts inside `README`s reference internal FR numbers. |

## Related

- FR-1010 (plan), FR-1011/FR-1014/FR-1015 (prerequisites), FR-1013 (next)
- `reference/patterns/corpus-map-reduce.md`, `examples/demos/req_witness_audit/`

## Judgement (pending)
