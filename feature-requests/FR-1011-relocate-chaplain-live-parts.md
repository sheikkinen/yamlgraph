# Feature Request: Relocate the live parts out of `.chaplain/` (Phase 1 of FR-1010)

**Priority:** MEDIUM
**Type:** Enhancement (path relocation with no graph or finalizer semantic change; the inbox route changes path — R-5)
**Status:** Enforced 2026-09-06 on `refactor/fr1011-relocate-chaplain-live-parts` —
RED `878fbac6`+`8ba9fcbd`, GREEN `4ef6d9d9`; **merge blocked** on one item
recorded in § Implementation Record: the philosopher smoke (AC-14 — fails
identically on unchanged main; not a relocation effect; semantic repair
forbidden by C-5, so the AC returns to judgement). The operator inbox
manifest (AC-12) was recorded by PR #614. Judged — APPROVED WITH REVISIONS
(2026-09-06), R-1..R-6 folded below; see
[FR-1011-relocate-chaplain-live-parts.judgement.md](FR-1011-relocate-chaplain-live-parts.judgement.md).
Prerequisite FR-1014 merged as `fec26941` (PR #612, operator `merge`
verdict recorded in FR-1014 AC-14); this judgement human-reviewed by the
merge of PR #611.
**Effort:** 1 day
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 1 of 5; prerequisite FR-1014 **merged** (not merely judged), SHA recorded in § Implementation Record (FR-1010 C-3)
**First consumer / first event:** the pre-commit `triage-gate` hook, on
the first `feature-requests/*.md` commit after this PR merges — it
imports `fr_triage/tools.py` by filesystem path and is the one consumer
that fails loudly if the relocation is wrong. Second: the operator's next
spark, written to `proposals/`.
**Research:** [FR-1010 § Alternatives Considered](FR-1010-chaplain-archival-plan.md#alternatives-considered)
— the in-body dispositioned table that selected this phase's shape; the
live-parts inventory and inbox pre-check in the same FR are this FR's
evidence record.
**Prior art:**
- [FR-196-portable-chaplain.md](FR-196-portable-chaplain.md) — moved
  philosopher **into** `.chaplain/graphs/` from `examples/philosopher/`
  and introduced the `parents[2]/lib/diary.py` proxy. This FR reverses
  the direction and keeps the stub deletion honest: the stub README says
  "current active chaplain graphs live under `.chaplain/graphs/`" —
  after this FR that sentence is false, so the stub goes.
- [FR-745-fr-triage-graph.md](FR-745-fr-triage-graph.md) — `triage_gate.py`
  loads `.chaplain/graphs/fr_triage/tools.py` by absolute path
  (`checks/triage_gate.py:29`). Path updated here; contract unchanged.
- [FR-744-world-now-distill.md](FR-744-world-now-distill.md) — `now.py:487`
  prints the `world_distill` refresh command. Path updated here.
- [FR-767-graph-authoring-sole-route.md](FR-767-graph-authoring-sole-route.md)
  — the governed-path regex has a `.chaplain/graphs` arm
  (`pre-command-guard.sh:170`, `check_authoring_proof.py:25`). The arm is
  deleted here. See "Guard gap" below: the arm never matched dir-style
  graphs, so nothing is lost by deleting it — and nothing was ever
  protected by it.
- [FR-889-os-enforced-main-write-lock.md](FR-889-os-enforced-main-write-lock.md)
  — `.chaplain/` is not in `FR889_GOVERNED_ROOTS` (`worktree.sh:506`) and
  neither is a top-level `proposals/`; the inbox keeps its current write
  semantics on main.

## Summary

Move the three graphs (`fr_triage`, `world_distill`, `philosopher` with
its `diary.py` dependency) from `.chaplain/graphs/` to `graphs/`, move
`.chaplain/lib/finalize_lib.sh` to `scripts/lib/` (its consumer
`scripts/finalize_merge.sh` is live — CAP-38/REQ-YG-125, CAP-45/REQ-YG-144;
FR-1010 R-4), establish `/proposals/` as the new untracked inbox path,
update every Phase 1 live consumer and relocated package document, and
delete the `examples/philosopher/` stub. The eight live sparks are migrated
by the operator on the main checkout (untracked; absent from every
worktree — FR-1010 R-6) as a pre-merge gate, and the manifest is recorded
here.

**Invariant (R-2):** after this FR, no Phase 1 live consumer and no
relocated package documentation points at `.chaplain/graphs`,
`.chaplain/lib/finalize_lib.sh`, or `.chaplain/inbox`. Explicitly
**allowed** residuals: historical records (`feature-requests/`,
`changelog/`, `docs/diary/`, `docs/memento/`), `.github/skills/chaplain-ops/`,
legacy ID-registry surfaces (FR-1015's concern), Phase 2 runtime and
tests, Phase 3 doctrine/reference documents. The residual allowlist is
frozen in § Acceptance Criteria.

## Value Statement

Phase 2 can delete `.chaplain/` without touching a live gate, a live
orientation script, or the operator's inbox.

## Problem

Three live artifacts and one dormant one are physically inside a
directory scheduled for removal (FR-1010 § "What is still live"). The
couplings, by file:line:

| Consumer | Line | Reference |
|---|---|---|
| `.github/hooks/scripts/checks/triage_gate.py` | 29 | `.chaplain/graphs/fr_triage/tools.py` loaded via `spec_from_file_location` |
| `.github/hooks/scripts/checks/fr-checks.sh` | 77 | reminder text: `yamlgraph graph run .chaplain/graphs/fr_triage/graph.yaml` |
| `scripts/vscode/now.py` | 487 | STALE hint: `yamlgraph graph run .chaplain/graphs/world_distill/graph.yaml` |
| `.github/hooks/scripts/pre-command-guard.sh` | 143–145, 170, 187, 267–270, 375 | authoring-contract comment; governed-path regex arm `(^|/)\.chaplain/graphs/[^/]+\.ya?ml$`; pre-filter `examples/|graphs/|\.chaplain/`; denial text; branch-create guidance "submit to `.chaplain/inbox/`" (R-2) |
| `scripts/check_authoring_proof.py` | 8–10, 25 | published contract docstring; same regex arm (R-2) |
| `.pre-commit-config.yaml` | 34 | `authoring-proof` `files:` selector alternative `^\.chaplain/graphs/[^/]+\.ya?ml$` — deleted here **after** FR-1014 has added the dir-aware alternatives (R-1) |
| `.github/skills/feature-request/SKILL.md` | 88–91, 148 | "Write to `.chaplain/inbox/`" |
| `.github/skills/graph-authoring/doctrine.md` | 44, 116 | precedent-search location; "Submit a Chaplain proposal (`.chaplain/inbox/`)" |
| `.github/skills/session-introspection/SKILL.md` | 40 | world file row names the chaplain runtime |
| `.github/copilot-instructions.md` | 163 | `diary_graduation_pipeline` seed: "auto-proposal to `.chaplain/inbox/`" (path mention only) |
| `.chaplain/graphs/philosopher/tools.py` | 261, 364–371 | docstrings name `.chaplain/inbox/` and `.chaplain/lib/diary.py`; `Path(__file__).resolve().parents[2] / "lib" / "diary.py"` — breaks on any move |
| `.chaplain/graphs/philosopher/graph.yaml` | 5, 12, 21 | relocation comment, inbox description, `inbox_dir` comment |
| `.chaplain/graphs/philosopher/README.md` | 8–40 | dead `philosopher.sh` wrapper usage, graph path, inbox path, portability claim, watcher-relative links (R-2) |
| `tests/unit/test_fr_triage.py` | 27 | `TOOLS = REPO / ".chaplain/graphs/fr_triage/tools.py"` |
| `tests/unit/test_world_distill.py` | 27 | `TOOLS = REPO / ".chaplain/graphs/world_distill/tools.py"` |
| `tests/unit/test_philosopher.py` | 21, 401–1344 | ~30 literal `.chaplain/graphs/philosopher/...` paths |
| `tests/unit/test_chaplain_graph_compile.py` | 22, 55 | globs `.chaplain/graphs/**/*.yaml`; asserts `parents[2]/lib/diary.py` |
| `scripts/finalize_merge.sh` | 25 | `source "$REPO_ROOT/.chaplain/lib/finalize_lib.sh"` — live (CAP-38, CAP-45; `tests/unit/test_finalize_merge.py`) |
| `capabilities/CAP-114-automated-post-merge-finalization.yaml` | 8, 15, 23 | `source:` paths name `.chaplain/lib/finalize_lib.sh` |
| `capabilities/CAP-75`, `CAP-205`, `CAP-206` | (see GREEN) | module paths **and** prose assigning the old location; `ARCHITECTURE.md` regenerated via `cap-architecture-sync` (R-2) |
| `.github/hooks/tests/test_authoring_guard.py` | 27 | `GOVERNED_CHAPLAIN = ".chaplain/graphs/pipeline.yaml"` — already replaced by FR-1014; this FR only confirms no `.chaplain` literal remains (Tier 2, outside `req_coverage`) |
| `.gitignore` | 100 | `.chaplain/inbox/` |

Two facts surfaced while tracing that the plan must record:

1. **The inbox is untracked.** `.gitignore:100` ignores it; `git ls-files
   .chaplain/inbox` is empty; the directory does not exist in any
   worktree. Sparks are visible only on the main checkout of one
   machine. This FR keeps the untracked semantics (path relocation only;
   the route's path changes, its durability model does not). The
   physical migration is therefore **not a PR change**: it is the
   operator runbook in FR-1010 § "Inbox pre-check" (freeze 13-item
   SHA-256 manifest → copy 8 → confirm 3 drops / 1 forward / 1 rmdir →
   hash-verify destinations → delete sources), executed on the main
   checkout before this PR merges, with the manifest (names + hashes,
   never contents) pasted into § Implementation Record below. The
   durability/visibility question is filed as a spark of its own
   (`proposals/inbox-is-untracked-and-worktree-invisible.md`, written by
   the operator in the same runbook step).
2. **`philosopher` is dormant, not live.** No consumer outside its own
   tests. Kept and relocated because it is the only implementation of
   the `diary_graduation_pipeline` seed; retiring it is a Phase 2
   decision, recorded in FR-1010.

### Guard gap (verified 2026-09-06, `pre-command-guard.sh:167-171`)

The governed-path predicate is:

```python
re.search(r"(^|/)examples/.+/graph\.ya?ml$", p)
or re.search(r"(^|/)examples/.+/prompts/[^/]+\.ya?ml$", p)
or re.search(r"(^|/)graphs/[^/]+\.ya?ml$", p)
or re.search(r"(^|/)\.chaplain/graphs/[^/]+\.ya?ml$", p)
```

The `graphs/` and `.chaplain/graphs/` arms match only **flat** files one
level down. `.chaplain/graphs/fr_triage/graph.yaml`,
`.chaplain/graphs/*/prompts/*.yaml`, and the existing
`graphs/enforcement/changelog-req-check.yaml` + `graphs/enforcement/prompts/*`
have never been governed. The `.chaplain` arm was vacuous for every graph
that directory actually contains.

**Resolved by FR-1010 R-5 and FR-1011 R-1:** the dir-aware widening is
FR-1014 (Phase 0), independently judged and human-reviewed, **implemented
and merged before** this FR, covering all three surfaces —
`governed_path()`, `GOVERNED`, and the `.pre-commit-config.yaml:34`
`files:` selector (the third surface was found by this FR's judgement and
folded into FR-1014). This FR only deletes the vacuous `.chaplain/graphs`
arm from the three surfaces and the `\.chaplain/` pre-filter token. It
adds no pattern. Option (a) from the first draft is withdrawn. If the
three surfaces do not agree at the recorded FR-1014 merge SHA, authority
remains inactive.

## Ideal Result

`ls .chaplain/graphs` shows only `watcher-*`; `ls .chaplain/lib` shows no
`diary.py` or `finalize_lib.sh`; `ls graphs` shows
`enforcement fr_triage philosopher world_distill`; `ls scripts/lib` shows
`finalize_lib.sh`; `ls proposals` shows nine files on the operator's main
checkout (8 carried + 1 new; untracked); every consumer above points at
the new path; `pytest tests/unit/test_fr_triage.py tests/unit/test_world_distill.py
tests/unit/test_philosopher.py tests/unit/test_chaplain_graph_compile.py
tests/unit/test_finalize_merge.py` is green; `yamlgraph graph lint` and a
smoke run pass for each moved graph from its new location; `git diff
--stat` shows renames, not rewrites, for the moved files.

## Proposed Solution

One PR, two commits (RED, GREEN), routed through `scripts/author.sh`
because `mv` of `graph.yaml`/`prompts/*.yaml` is graph authoring
(`graph-authoring/doctrine.md`; FR-767 sentinel).

### Authoring brief (R-4)

Committed **before** RED as
`feature-requests/authoring-briefs/fr-1011-relocate-chaplain-live-parts-brief.md`
(`graph-authoring/doctrine.md:17-31`): names the three source and
destination graph directories; every moved `prompts/*.yaml`, `tools.py`,
`README.md`; the sibling `diary.py`; every intended path-only edit inside
graph content (`philosopher/graph.yaml:5,12,21`, `tools.py:261,364-371`,
`README.md:8-40`); and the prohibition on semantic graph/prompt rewrites.
`scripts/author.sh <brief>` is the sole route; its
`tmp/draft-authoring-report.md` stays as the adapter artifact and its
`Artifacts`, `Precedent`, `Validation`, `Repairs`, `Blocked validation`
sections are copied verbatim into § Implementation Record with exact
commands and outcomes.

### RED (R-3: assertions, not collection errors)

The RED commit **collects** and fails on assertions that describe the
missing implementation; never `FileNotFoundError`, import failure, or
missing-fixture collection failure. `SKIP=pytest` on the RED commit.

New `tests/unit/test_fr1011_relocation.py`, each test an explicit
existence/content assertion:

- `test_destinations_exist`: `graphs/fr_triage/graph.yaml`,
  `graphs/world_distill/graph.yaml`, `graphs/philosopher/graph.yaml`,
  `graphs/philosopher/diary.py`, `scripts/lib/finalize_lib.sh` exist.
- `test_sources_gone`: the five old paths do not exist.
- `test_live_consumers_name_new_paths`: the frozen live-consumer list
  (table above, minus the allowlist) contains no `.chaplain/graphs`,
  `.chaplain/lib/finalize_lib.sh`, `.chaplain/inbox` literal.
- `test_philosopher_diary_proxy_is_sibling`: `graphs/philosopher/tools.py`
  source contains `with_name("diary.py")` and `graphs/philosopher/diary.py`
  exposes callable `write_diary` (loaded via `spec_from_file_location`
  **after** the existence assertion).
- `test_finalizer_sources_relocated_lib`: `scripts/finalize_merge.sh`
  contains `scripts/lib/finalize_lib.sh` and not `.chaplain/lib`.
- `test_proposals_route_documented`: `feature-request/SKILL.md` contains
  `mkdir -p proposals` and no `.chaplain/inbox`; `.gitignore` contains
  `/proposals/` and not `.chaplain/inbox/`.
- `test_governed_surfaces_have_no_chaplain_arm`: `pre-command-guard.sh`,
  `check_authoring_proof.py`, `.pre-commit-config.yaml` contain no
  `\.chaplain` literal.
- Tagged `@pytest.mark.req("REQ-YG-563", "REQ-YG-564", "REQ-YG-529", "REQ-YG-125")`
  (CAP-206 fr_triage, CAP-205 world_distill, CAP-75 philosopher proxy,
  CAP-38 finalizer) — existing REQs on the smallest witness that exercises
  each; no new CAP.

Existing tests (`test_fr_triage.py:27`, `test_world_distill.py:27`,
`test_philosopher.py:21` + literals, `test_chaplain_graph_compile.py:22,55`)
keep their module-level constants in RED and are moved **with the files
in GREEN**, so RED never trips their collection.

### GREEN

```bash
git mv .chaplain/graphs/fr_triage      graphs/fr_triage
git mv .chaplain/graphs/world_distill  graphs/world_distill
git mv .chaplain/graphs/philosopher    graphs/philosopher
git mv .chaplain/lib/diary.py          graphs/philosopher/diary.py
mkdir -p scripts/lib
git mv .chaplain/lib/finalize_lib.sh   scripts/lib/finalize_lib.sh
git rm -r examples/philosopher
# proposals/ is created by the operator runbook on main; the PR only
# changes .gitignore so the directory is ignored wherever it appears.
```

- `scripts/finalize_merge.sh:25` → `source "$REPO_ROOT/scripts/lib/finalize_lib.sh"`.
- `graphs/philosopher/tools.py:371` → `Path(__file__).with_name("diary.py")`;
  `:261, :364-371` docstrings → `proposals/`, sibling `diary.py`.
- `graphs/philosopher/graph.yaml:5,12,21` comments: drop the `.chaplain`
  paths (path-only; no node/prompt semantic change — brief prohibits).
- `graphs/philosopher/README.md:8-40`: remove the `philosopher.sh`
  wrapper section and watcher-relative links; state the graph path,
  `proposals/` as `inbox_dir`, and the graph-scope portability fact
  (CAP-75) truthfully.
- `checks/triage_gate.py:29` → `"graphs" / "fr_triage" / "tools.py"`
  (`parents[4]` stays; only the segment list changes).
- `checks/fr-checks.sh:77`, `scripts/vscode/now.py:487` → new paths.
- `pre-command-guard.sh:170` delete the `.chaplain/graphs` alternative;
  `:187` pre-filter → `examples/|graphs/`; `:143-145` comment, `:267-270`
  denial text, `:375` branch-create guidance → drop `.chaplain` paths,
  name `proposals/`. `check_authoring_proof.py:8-10` docstring and `:25`
  pattern entry. `.pre-commit-config.yaml:34` delete the
  `^\.chaplain/graphs/[^/]+\.ya?ml$` alternative. **No pattern is added**
  (FR-1014 owns the dir-aware arms and has already merged).
- `capabilities/CAP-205-world-distill.yaml:4,12,25`,
  `CAP-206-fr-triage-graph.yaml:4,14,26`, `CAP-75-portable-chaplain.yaml:8,12,13,29`,
  `CAP-114-automated-post-merge-finalization.yaml:8,15,23`
  — module paths **and** prose that assigns the old location → new
  locations; `python scripts/aggregate_capabilities.py` regenerates
  `ARCHITECTURE.md` (the `cap-architecture-sync` hook enforces agreement).
  Text-only; no REQ change.
- Skills: `feature-request/SKILL.md` §"Submitting" rewritten as
  "Write to `proposals/`" with the executable shape
  `mkdir -p proposals && cat > proposals/<topic>.md << 'EOF' … EOF`
  (R-5: the directory is ignored and may not exist on a fresh checkout);
  remove the "Remote Submission / `chaplain` label" paragraph — the
  importer is the dead runtime. `graph-authoring/doctrine.md:44` →
  `graphs/`; `:116` → `proposals/`; `session-introspection/SKILL.md:40`
  drop the runtime clause.
- `.github/copilot-instructions.md:163`: `.chaplain/inbox/` → `proposals/`
  in the seed string. Path-only; doctrine text unchanged. (Scripture
  wording changes are Phase 3.)
- `.gitignore:100` → **`/proposals/`** (root-anchored, R-5), replacing
  `.chaplain/inbox/`. Witness in a fresh checkout: the documented command
  creates `proposals/<topic>.md`; `git check-ignore -q proposals/<topic>.md`
  exits 0; `git status --porcelain` is empty.
- Inbox migration (R-5, **pre-merge GATE**): operator runbook on main
  (FR-1010 § Inbox pre-check), not this PR. § Implementation Record must
  hold: the 13 names + SHA-256; destination verification for all eight
  carries; the three drops named (`deviantart-auto-publish-pipeline.md`,
  `refactor-pre-command-guard-dispatcher.md`,
  `research-prompts-contradict-precedent-validator.md` — FR-1010's table
  is their tombstone); the one forward (`deviant-daily-curated-rerun.md`
  → deviant-daily checkout); `ninchat_voice/` removed; the new spark
  `inbox-is-untracked-and-worktree-invisible.md` created; `.chaplain/inbox/`
  confirmed empty. Proposal contents remain uncommitted.
- Old path behaviour: `.chaplain/inbox/` ceases to exist on main. A
  write there fails with `ENOENT` from the shell — visible, not silent.
  No guard grammar is added (FR-889 C-5: the kernel is the barrier; the
  guard covers only what the kernel cannot).

### Witness (R-4: three lint commands, three side-effect-contained smokes)

```bash
yamlgraph graph lint graphs/fr_triage/graph.yaml
yamlgraph graph lint graphs/world_distill/graph.yaml
yamlgraph graph lint graphs/philosopher/graph.yaml

cp feature-requests/FR-1011-relocate-chaplain-live-parts.md tmp/fr1011-smoke-fr.md
yamlgraph graph run graphs/fr_triage/graph.yaml --var fr_path=tmp/fr1011-smoke-fr.md
yamlgraph graph run graphs/world_distill/graph.yaml --var date=$(date +%F) --var output_path=tmp/fr1011-world-context.md
mkdir -p tmp/fr1011-diary tmp/fr1011-inbox
yamlgraph graph run graphs/philosopher/graph.yaml --var diary_dir=tmp/fr1011-diary --var inbox_dir=tmp/fr1011-inbox --var date=$(date +%F)
```

Never against committed FR-1010; never overwriting `docs/world-context.md`;
never writing proposals or diary entries into tracked directories. All
three real smokes must succeed before merge (FR-1010 AC-08); a missing
credential is recorded honestly in the adapter report and **blocks** the
merge. `python scripts/vscode/now.py` is an orientation-path witness,
not a `world_distill` smoke. Plus `pytest tests/unit/test_fr1011_relocation.py -q`
and the moved tests' files.

## Acceptance Criteria (R-6: exact commands)

- [ ] Prerequisite: FR-1014 merge SHA and human-review reference recorded
      in § Implementation Record; at that SHA `governed_path()`,
      `GOVERNED`, and `.pre-commit-config.yaml` `files:` agree on the
      FR-1014 truth table.
- [ ] `git diff --name-status -M90% <recorded-base-sha>...HEAD` shows `R`
      (score ≥ 90) for every pair: `.chaplain/graphs/{fr_triage,world_distill,philosopher}/**` →
      `graphs/…`, `.chaplain/lib/diary.py` → `graphs/philosopher/diary.py`,
      `.chaplain/lib/finalize_lib.sh` → `scripts/lib/finalize_lib.sh`.
      Base SHA recorded (immutable), not `main`.
- [ ] `grep -rn '\.chaplain' <frozen live-consumer list>` returns nothing.
      List: `.github/hooks/scripts/checks/{triage_gate.py,fr-checks.sh}`,
      `.github/hooks/scripts/pre-command-guard.sh`, `scripts/check_authoring_proof.py`,
      `.pre-commit-config.yaml`, `scripts/vscode/now.py`, `scripts/finalize_merge.sh`,
      `.github/skills/{feature-request/SKILL.md,graph-authoring/doctrine.md,session-introspection/SKILL.md}`,
      `graphs/{fr_triage,world_distill,philosopher}/**`, `scripts/lib/finalize_lib.sh`,
      `capabilities/CAP-{75,114,205,206}-*.yaml`, `.gitignore`.
- [ ] Residual allowlist for `grep -rln '\.chaplain' .` (excluding
      `tmp/`, `.venv/`, `build/`): only paths under `feature-requests/`,
      `changelog/`, `docs/`, `.github/skills/chaplain-ops/`, `.chaplain/`,
      `scripts/{id_registry.py,validate_id_registry.py,chaplain-prompts/}`,
      `tests/`, `.github/hooks/tests/`, `reference/`, `examples/README.md`,
      `examples/**` (Phase 3), `ramp/`, `CLAUDE.md`, `.github/copilot-instructions.md`
      (Scripture wording, Phase 3). Any other match fails.
- [ ] `pytest tests/unit/test_fr1011_relocation.py tests/unit/test_fr_triage.py tests/unit/test_world_distill.py tests/unit/test_philosopher.py tests/unit/test_chaplain_graph_compile.py tests/unit/test_finalize_merge.py -q`
      green; `pytest tests/unit -q -m "not slow" -n auto` green.
- [ ] `python scripts/req_coverage.py --strict` and
      `python scripts/validate_capabilities.py --strict` exit 0;
      `python scripts/aggregate_capabilities.py` produces no diff
      against committed `ARCHITECTURE.md`.
- [ ] A `feature-requests/*.md` commit in the worktree runs
      `triage-gate` without `FileNotFoundError`.
- [ ] `examples/philosopher/` does not exist.
- [ ] `.gitignore` contains `/proposals/` and not `.chaplain/inbox/`;
      fresh-checkout witness recorded (command creates the file,
      `git check-ignore -q` exits 0, `git status --porcelain` empty).
- [ ] Authoring brief committed; adapter report sections copied into
      § Implementation Record; three lint + three real smoke outcomes
      recorded (R-4).
- [ ] § Implementation Record holds the operator's 13-item manifest
      (names + SHA-256), eight destination hashes verified, three drops
      and one forward named, `ninchat_voice/` removed, new spark created,
      `.chaplain/inbox/` confirmed empty (FR-1010 AC-07). **Merge gate.**
- [ ] FR-1010 live-parts table unchanged. If a further live artifact is
      discovered, enforcement **stops** and both FRs return to judgement
      (FR-1010 C-10) — not "amended while work continues".
- [ ] Human review recorded before merge covering: final hook diff,
      pre-commit selector diff, Scripture path edit, inbox manifest,
      authoring brief + report (R-6; `judge-fr/doctrine.md:98-100` —
      deletion-only diffs to enforcement infrastructure are still
      adversarial input).
- [ ] Changelog fragment `changelog/unreleased/fr-1011-relocate-chaplain-live-parts.md`.

## Purge list (nothing invented)

- No new guard grammar (FR-1014 owns the dir-aware arm).
- No symlink from `.chaplain/inbox/` to `proposals/`.
- No `proposals/README.md` — the feature-request skill is the doc.
- No CAP file; existing REQs cover the relocated graphs and finalizer.
- No PR-side `mv` of untracked inbox files.

## Alternatives Considered

| Option | Why not |
|---|---|
| `feature-requests/inbox/` for sparks | `.pre-commit-config.yaml:280,286` (`^feature-requests/.*\.md$`) would run `prior-art-gate` and `triage-gate` on sparks that by design have no disposition sections. |
| `examples/` for the three graphs | They are process graphs, not demos; `graphs/enforcement/` is the dir-style precedent for process graphs. |
| Widen the `graphs/` regex in this FR (first-draft option (a)) | Withdrawn per FR-1010 R-5: enforcement hardening is a separate responsibility with its own human gate; it is FR-1014 and merges first. |
| Delete `scripts/finalize_merge.sh` as the sole consumer of `finalize_lib.sh` (first draft) | Withdrawn per FR-1010 R-4: CAP-38/CAP-45 define it as live; the dependency direction was reversed. |
| Retire philosopher now | Phase 2 scope; relocating keeps Phase 1 a pure move. |
| Track `proposals/` in git | Changes spark-filing friction (PR per spark) — a design decision, filed as a spark, not smuggled into a relocation. |

## Related

- FR-1010 (plan), FR-1014 (Phase 0, prerequisite — merged), FR-1015
  (supersede FR-975/980), FR-1012 (Phase 2), FR-1013 (Phase 3)

## Implementation Record (2026-09-06, Windows host, branch `refactor/fr1011-relocate-chaplain-live-parts`)

- **FR-1014 merge SHA / human review:** `fec26941` (`fix(hooks): FR-1014 dir-aware authoring guard for graphs/ (#612)`); human review = operator `merge` verdict on PR #612, recorded in FR-1014 AC-14. AC-03 witnessed at that SHA in this worktree: `pytest tests/unit/test_fr1014_authoring_proof_dir_graphs.py -q --no-cov` → 39 passed before any relocation write.
- **Base SHA for the rename check (immutable):** `fec26941`.
- **Commits:** briefs `c1c52958`, RED `878fbac6` (`SKIP=pytest`; 32 failed, 1 passed — all `AssertionError`, no collection/import/fixture failure), RED follow-up `8ba9fcbd` (`SKIP=pytest`; 33 failed — the Path-segment form `".chaplain"` used by `triage_gate.py` had passed vacuously), resume brief `3b0f13ab`, smoke brief amendment `776d321f`, GREEN `4ef6d9d9`.
- **Authoring briefs (D-2):** `feature-requests/authoring-briefs/fr-1011-relocate-chaplain-live-parts-brief.md` (relocations + path-only edits + lint×3 + two smokes), `…-resume-brief.md` (one comment line + the two smokes the first run recorded as blocked), `…-smoke-brief.md` (validation-only: world_distill + philosopher). Split on `scripts/author_preflight.py`'s budget finding (three full-pipeline smokes risk the 900 s backend ceiling). Each run's `tmp/draft-authoring-report.md` is copied verbatim below.
- **Renames (AC-06):** `git diff --name-status -M90% fec26941...HEAD` reports `R100` for every graph, prompt and tool file, `R098` for `diary.py`, `R097` for `philosopher/tools.py`, `R098` for `finalize_lib.sh`, `R095` for `philosopher/graph.yaml`. **Deviation:** `graphs/philosopher/README.md` reports as `D`+`A` (similarity < 90%) because AC-08's truthful rewrite removed the dead `philosopher.sh` usage block, the watcher-relative links and the `.chaplain/` portability claim; the two criteria conflict for that one file and AC-08 was preferred.
- **Lint × 3:** passed in run 1 (`graphs\fr_triage\graph.yaml`, `graphs\world_distill\graph.yaml`, `graphs\philosopher\graph.yaml` → `No issues found`), repeated in runs 2 and 3.
- **Smoke — fr_triage:** run 2, `yamlgraph graph run graphs/fr_triage/graph.yaml --var fr_path=tmp/fr1011-smoke-fr.md --full` on a `tmp/` copy of FR-214 (Proposed) → passed; the copy carries one `## Triage (generated — claims requiring disposition)` heading. (Run 1 was blocked: the FR's frozen command used the committed FR-1011 copy, whose Status is Judged, and the graph appends to Proposed FRs only — the witness command in § Witness was wrong as written.)
- **Smoke — world_distill:** run 3, `yamlgraph graph run graphs/world_distill/graph.yaml --var date=2026-09-06 --var output_path=tmp/fr1011-world-context.md --full` → passed, output 2647 bytes; `docs/world-context.md` untouched. (Runs 1 and 2 were blocked: `feedparser`, a declared `digest` extra, was absent first from `.venv` and then from the Python 3.13 interpreter that provides the adapter's `yamlgraph`; the requesting session installed it in both — an environment change, not a repository change.)
- **Smoke — philosopher: NOT MET.** Run 3: `yamlgraph graph run graphs/philosopher/graph.yaml --var diary_dir=tmp/fr1011-diary --var inbox_dir=tmp/fr1011-inbox --var date=2026-09-06 --full` → `scan` and `analyze` complete, then `❌ Error: Object of type CopilotResult is not JSON serializable`, rc 1. Re-run directly by the session from the relocated path: identical. **Baseline on unchanged `main` (`fec26941`) from `.chaplain/graphs/philosopher/graph.yaml`: identical failure at the same point** (log `philosopher-smoke-main.log`). The dormant graph was already broken; the relocation neither caused nor can fix it — a semantic repair is forbidden by C-5 and out of D-3. AC-14 therefore returns to judgement (C-8 analogue): either FR-1011 accepts lint + compile witnesses for the dormant graph, or a separate FR repairs the philosopher's `CopilotResult` state handling before this merges. The warning `graduation_threshold='{state.graduation_threshold}' KeyError` on both trees is the same defect class (unset state variables).
- **AC-15:** `python .github/hooks/scripts/checks/triage_gate.py` with `feature-requests/FR-1011-…md` staged → rc 0, no `FileNotFoundError`; `scripts/vscode/now.py:487` prints `yamlgraph graph run graphs/world_distill/graph.yaml`.
- **AC-11:** `mkdir -p proposals && echo … > proposals/fr1011-fixture.md; git check-ignore -q proposals/fr1011-fixture.md` → rc 0; `git status --porcelain proposals` → empty; fixture removed.
- **AC-09:** `bash -n scripts/finalize_merge.sh` ok; sourcing `scripts/lib/finalize_lib.sh` exposes `create_changelog_fragment create_diary_stub extract_fr_metadata update_fr_status`; `bash scripts/finalize_merge.sh` prints its usage. `tests/unit/test_finalize_merge.py` and `test_automated_post_merge_finalization.py` fail on this host exactly as on `main` (`bash` resolves to the WSL stub) — 28 failures identical in both trees; CI owns the pytest form.
- **Tests:** `pytest tests/unit/test_fr1011_relocation.py …` — 33 passed; the focused set (`test_fr_triage`, `test_world_distill`, `test_philosopher`, `test_chaplain_graph_compile`, `test_fr382_…`, `test_fr1014_…`) green except `test_daemon_script_executable` (exec bit of `.chaplain/philosopher.sh`, fails identically on `main`). Full `pytest tests/unit -m "not slow" -n auto`: 262 failed / 18 errors on the branch vs 266 / 18 on `main` — `comm` diff: zero branch-only failures after `test_fr382` was repointed; four `main`-only failures are `world_distill` tests that pass once `feedparser` is installed.
- **Gates:** `validate_capabilities.py --strict`, `req_coverage.py --strict`, `aggregate_capabilities.py` (no diff after commit), `aggregate_changelog.py`, `ruff check` on every changed `.py` — green. `noqa_coverage.py --strict` and the Tier-2 hook tests are CI-owed on this host (see FR-1014's record).
- **Guard after cleanup (bash probes):** `graphs/fr_triage/graph.yaml` deny; `examples/demos/hello/graph.yaml` deny; `docs/x.md` approve. Observation: `.chaplain/graphs/watcher-plan/graph.yaml` is also denied — the FR-1014 `(^|/)graphs/[^/]+/[^/]+\.ya?ml$` arm matches `…/graphs/<name>/<file>.yaml` under any parent, so the Phase 2 watcher graphs are governed as a side effect of the dir-aware arm, not of this FR.
- **Inbox manifest (AC-12, C-6): done** (operator, main checkout, merged to main by PR #614) — **done 2026-09-06** as an independent local copy — the step cannot run on a remote device or worktree because the inbox is untracked; it was executed on the iMac main checkout ahead of the PR. 13 items frozen (`shasum -a 256 .chaplain/inbox/*.md`); 8 carries copied and `shasum -c` verified; 3 drops confirmed; 1 forward copied and verified; `ninchat_voice/` removed; new spark written. **Sources kept**: the eight `.chaplain/inbox/*.md` copies remain until this PR merges (untracked files have no recovery path, and `.chaplain/inbox/` "ceases to exist on main" is tied to the merge). Deletion of the sources + `.chaplain/inbox/` confirmed empty is the last runbook step, done at merge time. `proposals/` currently shows as `??` on main because `.gitignore` still ignores `.chaplain/inbox/`, not `/proposals/` — D-9 fixes that; nothing under `proposals/` is ever committed. Contents were not read by the agent; names + hashes only:

| File | SHA-256 | Disposition | Action |
|---|---|---|---|
| `capability-domain-activity-heatmap.md` | `3a04446807017e7795f0da08700e11e624e0ec8a5b79996528cee0227cf561e5` | carry | copied to `proposals/`, hash verified |
| `deviant-daily-curated-rerun.md` | `3d2897c6052c16e8bac3c4f28cb7c8508f1313016fbd54f59edfeb9329066672` | forward | copied to `~/Documents/src/deviant-daily/proposals/`, hash verified |
| `deviantart-auto-publish-pipeline.md` | `2c798c34d893a2c008e950496035b51f069b711f0294eb5e07cf42ed6a9642a7` | drop | not copied — FR-1010 table is the tombstone |
| `example-provenance-audit-graph.md` | `d3fcacc6eba5bbd1d3502edb0ff9fe9f0a319f4e0ef26227328c0a7bd882a533` | carry | copied to `proposals/`, hash verified |
| `index-memento-frs-into-prior-art.md` | `78732721871c95d6dab963edb3723b186325203c844d8e41ac9ef0ffcad69a99` | carry | copied to `proposals/`, hash verified |
| `judge-regression-fixture.md` | `6bb78d71deff6214b5bdff58014a0ec91cb759b8e926d02d54726ace5d643dcf` | carry | copied to `proposals/`, hash verified |
| `pin-interpreter-in-measurement-routes.md` | `cd6a280019e074959e74946c3d6950fadafff81f40002902dc0bf3ce56ec52d2` | carry | copied to `proposals/`, hash verified |
| `prior-art-self-exclusion-misses-judgement-sibling.md` | `c8264965eeb9b57d1c8f4749f3a1318c152f453bcfb217eaa030c1170da6e251` | carry | copied to `proposals/`, hash verified |
| `refactor-pre-command-guard-dispatcher.md` | `05345ae9a02e745ab66105a829a87fe3d1e4348a3d0b0a53f7cef3d74f1bf478` | drop | not copied — FR-1010 table is the tombstone |
| `research-prompts-contradict-precedent-validator.md` | `cbf64548ded8c591d5a9bf9f04abe5b3372c969f9bd6c014bec0c9454ec132e3` | drop | not copied — FR-1010 table is the tombstone |
| `supersede-disposition-gate.md` | `cb14c191d5a1f0446f878ca39dabc6b0e478e5421fdb06807471ef384899c0e0` | carry | copied to `proposals/`, hash verified |
| `workspace-sediment-audit.md` | `a25d471c12fec7c7de1f38556e5c9b09cf54b2ebddf716ef115304558b3e900c` | carry | copied to `proposals/`, hash verified |
| `ninchat_voice/` | — | rm | empty since 2026-05-19; `rmdir` done |
| `inbox-is-untracked-and-worktree-invisible.md` | `ebf15849956b825f9105d18b5c42848c5f216c14e3f5aa9d5ab0a9e19416e0ea` | new spark | written to `proposals/` in the same step |


### Additional consumers found while tracing (path updates, not new live artifacts — C-8 not triggered)

| File | What | Disposition |
|---|---|---|
| `tests/unit/test_automated_post_merge_finalization.py` | hardcodes `FINALIZE_LIB_SH` and asserts the finalizer sources it (CAP-114 witnesses) | repointed to `scripts/lib/finalize_lib.sh` (sixth test file) |
| `tests/unit/test_fr382_chaplain_prompt_caching_scope_red.py` | inventories LLM prompts under `.chaplain/graphs` and expects exactly context-planner + distill_world + triage_fr | inventory spans both roots; expected set adds `graphs/enforcement/prompts/cross_check.yaml` (seventh test file) |
| `.github/hooks/README.md:87`, `.github/skills/graph-authoring/SKILL.md:41` | publish the governed-path list with `.chaplain/graphs/*.yaml` | list updated (enumerating documentation of D-6) |
| `graphs/philosopher/diary.py:3` | docstring "Used by diary_digest and .chaplain workflows" | reworded (not a governed path) |
| `scripts/lib/finalize_lib.sh:14` | usage comment `source .chaplain/lib/finalize_lib.sh` | updated |

### Residual `.chaplain` matches outside the FR's written allowlist (AC-07 second clause)

`grep -rln '\.chaplain' .` (excluding `tmp/`, `.venv/`, `build/`) returns, beyond the allowlisted roots: 30 `capabilities/CAP-*.yaml` describing the watcher/inquisitor/inbox runtime (Phase 2 retirement census) and the generated `ARCHITECTURE.md`; `.gitignore` lines for `.chaplain/{inquisitor.log,state,inbox-fsm,drafts,processing,failed}` (Phase 2); `.github/skills/judge-fr/{MANIFEST.yaml,adapters/graph.yaml,doctrine.md}` lineage notes naming `watcher-plan` (Phase 2/3 doctrine); `pyproject.toml:230` (the `process` marker description); `scripts/fix_bare.sh:8` and `scripts/migrate_capabilities.py:198,275` (historical strings naming the old inbox); `graphs/philosopher/README.md:32` (states that no `.chaplain/` copy claim is made); `CHANGELOG.md` (untracked, generated). None names `.chaplain/graphs/{fr_triage,world_distill,philosopher}`, `.chaplain/lib/finalize_lib.sh`, `.chaplain/lib/diary.py` or `.chaplain/inbox/` (AC-07 first clause — `test_live_consumers_name_new_paths` and `test_relocated_trees_name_no_old_paths`). The written allowlist omitted `capabilities/`, `.gitignore`, `pyproject.toml`, the judge-fr skill and two scripts; recorded here as the enumerated residuals the judgement's AC-07 asks for.

### Decisions and deviations

1. Witness regex narrowed to the judgement's AC-07 forms (`.chaplain/graphs/{fr_triage,world_distill,philosopher}`, the two lib files, `.chaplain/inbox/`, and the Path-segment literal) after the first GREEN pass showed CAP-75 legitimately still listing the watcher graphs under `.chaplain/graphs` and `.gitignore` still listing `.chaplain/inbox-fsm/`.
2. Three briefs instead of one (budget finding); the first run's smoke commands were wrong as frozen (non-Proposed FR; missing optional dependency) — corrected in the resume brief, not by repairing graphs.
3. `changelog/unreleased/fr-1011-relocate-chaplain-live-parts.md` is typed `removal` (the aggregator accepts `feat|fix|removal`; the PR is a `refactor`, so the feat/fix diary and fragment gates do not fire — both artifacts exist anyway per D-10).
4. FR-1014's truth-table rows for `graphs/fr_triage/**` relabelled `exists`; its `test_synthetic_and_fr1011_rows_are_absent` became `test_synthetic_rows_are_absent`.

### Authoring report — run 1 (relocation brief), verbatim

## Artifacts

- `graphs/fr_triage/graph.yaml` (moved from `.chaplain/graphs/fr_triage/graph.yaml`; `R100`)
- `graphs/fr_triage/prompts/triage_fr.yaml` (moved from `.chaplain/graphs/fr_triage/prompts/triage_fr.yaml`; `R100`)
- `graphs/fr_triage/tools.py` (moved from `.chaplain/graphs/fr_triage/tools.py`; `R100`)
- `graphs/world_distill/graph.yaml` (moved from `.chaplain/graphs/world_distill/graph.yaml`; `R100`)
- `graphs/world_distill/prompts/distill_world.yaml` (moved from `.chaplain/graphs/world_distill/prompts/distill_world.yaml`; `R100`)
- `graphs/world_distill/tools.py` (moved from `.chaplain/graphs/world_distill/tools.py`; `R100`)
- `graphs/philosopher/README.md` (moved from `.chaplain/graphs/philosopher/README.md`; `R100`; path-only documentation edits)
- `graphs/philosopher/diary.py` (moved from `.chaplain/lib/diary.py`; `R100`)
- `graphs/philosopher/graph.yaml` (moved from `.chaplain/graphs/philosopher/graph.yaml`; `R100`; path/comment edits only)
- `graphs/philosopher/prompts/analyze.yaml` (moved from `.chaplain/graphs/philosopher/prompts/analyze.yaml`; `R100`)
- `graphs/philosopher/prompts/challenge.yaml` (moved from `.chaplain/graphs/philosopher/prompts/challenge.yaml`; `R100`)
- `graphs/philosopher/prompts/distill.yaml` (moved from `.chaplain/graphs/philosopher/prompts/distill.yaml`; `R100`)
- `graphs/philosopher/prompts/reflect.yaml` (moved from `.chaplain/graphs/philosopher/prompts/reflect.yaml`; `R100`)
- `graphs/philosopher/tools.py` (moved from `.chaplain/graphs/philosopher/tools.py`; `R100`; path-only docstring/load-path edits)
- `graphs/fr_triage/**` and `graphs/world_distill/**` contained no `.chaplain` literals when searched after relocation.

## Precedent

- Primary precedent: the three moved graph packages themselves; the task is relocation of committed artifacts, not new graph design.
- Directory-style graph precedent: `graphs/enforcement/` uses a process graph under `graphs/` with adjacent prompts.

## Validation

- `yamlgraph graph lint graphs\fr_triage\graph.yaml` -> passed: no issues found.
- `yamlgraph graph lint graphs\world_distill\graph.yaml` -> passed: no issues found.
- `yamlgraph graph lint graphs\philosopher\graph.yaml` -> passed: no issues found.
- `mkdir -p tmp` -> satisfied by existing/created `tmp` directory via PowerShell equivalent.
- `cp feature-requests/FR-1011-relocate-chaplain-live-parts.md tmp/fr1011-smoke-fr.md` -> completed via PowerShell equivalent.
- `yamlgraph graph run graphs\fr_triage\graph.yaml --var fr_path=tmp\fr1011-smoke-fr.md --full` -> blocked; see Blocked validation.
- `yamlgraph graph run graphs\world_distill\graph.yaml --var date=2026-09-06 --var output_path=tmp\fr1011-world-context.md --full` -> blocked; see Blocked validation.
- `git status --short` -> reported the directory moves; philosopher files with allowed content edits appeared as `RM`, unchanged moved files appeared as `R`.
- `git diff --cached --name-status -M90% | grep -E '^R'` -> every moved file appeared as `R100`.

## Repairs

- No validation repair was applied. The lints passed, and the smoke failures require inputs or dependencies outside the allowed authoring edits.
- The only content changes were the exhaustive path-only edits named in the brief for `graphs/philosopher/README.md`, `graphs/philosopher/graph.yaml`, and `graphs/philosopher/tools.py`.

## Blocked validation

- `yamlgraph graph run graphs\fr_triage\graph.yaml --var fr_path=tmp\fr1011-smoke-fr.md --full` failed at the append step with the exact error: `FR status is 'judged — approved with revisions (2026-09-06). r-1..r-6 folded' — triage appends to Proposed FRs only`. No semantic repair was made.
- `yamlgraph graph run graphs\world_distill\graph.yaml --var date=2026-09-06 --var output_path=tmp\fr1011-world-context.md --full` failed before execution with the exact error: `Python tool load failed in strict mode (config.tool_load_mode=strict): fetch_ecosystem: world_distill requires 'feedparser' (pip install feedparser); prepare_distill_input: world_distill requires 'feedparser' (pip install feedparser); write_context: world_distill requires 'feedparser' (pip install feedparser)`. No dependency was installed during this authoring run.
- The philosopher real smoke was intentionally not run here because the brief assigns it to `feature-requests/authoring-briefs/fr-1011-relocate-chaplain-live-parts-smoke-brief.md`.

### Authoring report — run 2 (resume brief), verbatim

# Artifacts

- `graphs/philosopher/graph.yaml`

# Precedent

- Used the task brief's named prior art: `graphs/fr_triage/graph.yaml` and `graphs/world_distill/graph.yaml`.
- The authored artifact boundary was limited to the required single comment-line edit in `graphs/philosopher/graph.yaml`; no prompt, node, edge, schema, tool, provider, or model files were edited by this run.

# Validation

- `yamlgraph graph lint graphs/philosopher/graph.yaml` -> passed: `No issues found`.
- `yamlgraph graph lint graphs/fr_triage/graph.yaml` -> passed: `No issues found`.
- `yamlgraph graph lint graphs/world_distill/graph.yaml` -> passed: `No issues found`.
- `mkdir -p tmp; cp feature-requests/FR-214-fix-extract-variables-nested-set.md tmp/fr1011-smoke-fr.md` -> completed, but PowerShell reported `An item with the specified name ...\tmp already exists.` for `mkdir -p tmp`; the copy still proceeded.
- `yamlgraph graph run graphs/fr_triage/graph.yaml --var fr_path=tmp/fr1011-smoke-fr.md --full` -> passed; the graph appended triage content to `tmp/fr1011-smoke-fr.md`.
- `bash -lc 'yamlgraph graph run graphs/world_distill/graph.yaml --var date=$(date +%F) --var output_path=tmp/fr1011-world-context.md --full'` -> failed; see Blocked validation.
- Confirmation: `tmp/fr1011-smoke-fr.md` contains 0 exact `## Triage` headings; it contains one generated heading spelled `## Triage (generated — claims requiring disposition)`.
- Confirmation: `tmp/fr1011-world-context.md` was not written because the world_distill smoke failed.
- Confirmation: `git status --short` shows no paths under `docs/`, `feature-requests/`, or `proposals/`.
- Confirmation: the working tree had many tracked changes before this run; from this run, the only tracked authored path is `graphs/philosopher/graph.yaml`.

# Repairs

- Replaced the requested comment line in `graphs/philosopher/graph.yaml`.
- No validation-driven repair was performed. The brief requires recording lint or smoke failures and stopping without semantic repair or package installation.

# Blocked validation

- Blocked command: `yamlgraph graph run graphs/world_distill/graph.yaml --var date=$(date +%F) --var output_path=tmp/fr1011-world-context.md --full`
- Executed through Bash from PowerShell as: `bash -lc 'yamlgraph graph run graphs/world_distill/graph.yaml --var date=$(date +%F) --var output_path=tmp/fr1011-world-context.md --full'`
- Reason: strict Python tool loading failed because `feedparser` is unavailable to the `yamlgraph` execution environment:
  `Python tool load failed in strict mode (config.tool_load_mode=strict): fetch_ecosystem: world_distill requires 'feedparser' (pip install feedparser); prepare_distill_input: world_distill requires 'feedparser' (pip install feedparser); write_context: world_distill requires 'feedparser' (pip install feedparser)`
- Blocked confirmation: `tmp/fr1011-world-context.md` non-empty output could not be confirmed because the command failed and the file does not exist.
- Failed confirmation: the triage smoke copy does not contain an exact `## Triage` heading; it contains `## Triage (generated — claims requiring disposition)`, so the requested exact-heading count is 0.

### Authoring report — run 3 (validation-only smoke brief), verbatim

# Artifacts

- `tmp/draft-authoring-report.md` - this report.
- `tmp/fr1011-world-context.md` - world_distill smoke output; written and non-empty (2647 bytes).
- `tmp/fr1011-diary/diary-2026-09-02-reflection-fr-954-the-host-that-could-not-see-red.md`
- `tmp/fr1011-diary/diary-2026-09-02-reflection-fr-959-960-the-gate-the-enforcer-cannot-open.md`
- `tmp/fr1011-diary/diary-2026-09-02-the-artifact-with-one-name.md`
- `tmp/fr1011-diary/diary-2026-09-02-the-gatekeeper-locked-inside-the-room.md`
- `tmp/fr1011-diary/diary-2026-09-02-the-inventory-that-counted-only-what-it-could-see.md`
- `tmp/fr1011-diary/diary-2026-09-03-five-investigations-one-boundary.md`
- `tmp/fr1011-diary/diary-2026-09-03-session-recap-business-plans-mcp-boundary.md`
- `tmp/fr1011-diary/diary-2026-09-03-the-five-modules-under-yamlgraph-async-action.md`
- `tmp/fr1011-diary/diary-2026-09-03-the-ledger-files-where-the-pain-is.md`
- `tmp/fr1011-diary/diary-2026-09-03-the-lock-writes-half-a-pull.md`
- `tmp/fr1011-diary/diary-2026-09-03-the-toolbelt-nobody-else-picked-up.md`
- `tmp/fr1011-diary/diary-2026-09-04-reflection-fr-960-two-brains-one-route.md`
- `tmp/fr1011-diary/diary-2026-09-04-reflection-fr-966-the-default-that-looked-like-a-redaction.md`
- `tmp/fr1011-diary/diary-2026-09-04-reflection-fr-967-the-tests-that-were-cited-but-never-written.md`
- `tmp/fr1011-diary/diary-2026-09-04-reflection-fr-982-the-project-that-was-never-created.md`
- `tmp/fr1011-diary/diary-2026-09-04-reflection-fr-984-the-knob-that-was-already-there.md`
- `tmp/fr1011-diary/diary-2026-09-04-reflection-fr-985-the-brief-that-didnt-change.md`
- `tmp/fr1011-diary/diary-2026-09-04-reflection-the-vocabulary-i-searched-with.md`
- `tmp/fr1011-diary/diary-2026-09-04-the-judge-that-never-says-no.md`
- `tmp/fr1011-diary/diary-2026-09-04-the-opening-frame-set-the-prior.md`
- `tmp/fr1011-diary/diary-2026-09-05-the-recap-nobody-outside-could-read.md`
- `tmp/fr1011-diary/diary-2026-09-06-reflection-fr-1005-the-loader-that-kept-no-name.md`
- `tmp/fr1011-diary/diary-2026-09-06-reflection-fr-1014-baseline-before-blame.md`
- `tmp/fr1011-diary/diary-2026-09-06-the-step-that-was-not-in-the-list.md`
- `tmp/fr1011-inbox/` - no files created.

No graph, prompt, tool, documentation, or proposal artifact was authored or repaired.

# Precedent

- Task brief precedent: `graphs/philosopher/graph.yaml`, the relocated graph named by `feature-requests/authoring-briefs/fr-1011-relocate-chaplain-live-parts-smoke-brief.md`.
- Validation-only run; no new graph shape was selected or adapted.

# Validation

- `yamlgraph graph lint graphs\philosopher\graph.yaml` - passed; exit code 0. Output included `graph.yaml - No issues found` and `All graphs passed linting`.
- `yamlgraph graph lint graphs\world_distill\graph.yaml` - passed; exit code 0. Output included `graph.yaml - No issues found` and `All graphs passed linting`.
- `New-Item -ItemType Directory -Force -Path tmp | Out-Null; yamlgraph graph run graphs\world_distill\graph.yaml --var date=2026-09-06 --var output_path=tmp\fr1011-world-context.md --full` - passed; exit code 0.
- `New-Item -ItemType Directory -Force -Path tmp\fr1011-diary,tmp\fr1011-inbox | Out-Null; Copy-Item docs\diary\diary-2026-09-0*.md tmp\fr1011-diary\ -Force; yamlgraph graph run graphs\philosopher\graph.yaml --var diary_dir=tmp\fr1011-diary --var inbox_dir=tmp\fr1011-inbox --var date=2026-09-06 --full` - failed; exit code 1. Output ended with `Error: Object of type CopilotResult is not JSON serializable`.
- `git --no-pager status --short -- docs\diary` - passed; no output, so no new or modified file appeared under `docs/diary/`.
- `git --no-pager status --short -- proposals` - passed; no output, so no new or modified file appeared under `proposals/`.
- `git --no-pager status --short` - completed, but the workspace was not clean: it reported tracked modifications and renames already present in the working tree, including FR-1011 relocation paths. The requested clean tracked-state confirmation was therefore not satisfied by repository status.

# Repairs

- None. The task brief forbids graph, prompt, or tool repairs in this validation-only run.

# Blocked validation

- `New-Item -ItemType Directory -Force -Path tmp\fr1011-diary,tmp\fr1011-inbox | Out-Null; Copy-Item docs\diary\diary-2026-09-0*.md tmp\fr1011-diary\ -Force; yamlgraph graph run graphs\philosopher\graph.yaml --var diary_dir=tmp\fr1011-diary --var inbox_dir=tmp\fr1011-inbox --var date=2026-09-06 --full` - blocked by runtime serialization failure: `Object of type CopilotResult is not JSON serializable`.
- `git --no-pager status --short` cleanliness confirmation - blocked because repository status already contains tracked modifications and renames; no graph or prompt repair was attempted.

### Acceptance criteria — status (judgement AC-01…AC-19)

| AC | Status | Evidence |
|---|---|---|
| AC-01 folded, Type wording | met | header |
| AC-02 FR-1014 merged first, SHA recorded | met | `fec26941`, PR #612 |
| AC-03 three-surface table before deleting the arm | met | 39 passed at `fec26941` in this worktree |
| AC-04 brief committed, cited, forbids semantic rewrites | met | three briefs, `c1c52958` / `3b0f13ab` / `776d321f` |
| AC-05 RED collects, assertion-only, `SKIP=pytest` | met | `878fbac6`, `8ba9fcbd` |
| AC-06 every pair `R` ≥ 90 | met except README | `R095`–`R100`; README `D`+`A` (deviation above) |
| AC-07 live list clean; residuals enumerated | met | witnesses + enumeration above |
| AC-08 philosopher package truthful | met | run 1/2 diffs: comments, docstrings, README |
| AC-09 finalizer sources `scripts/lib`, behaviour unchanged | met (pytest CI-owed) | bash witness; CAP-38/45 untouched |
| AC-10 CAPs + ARCHITECTURE + strict gates | met | gates row |
| AC-11 `/proposals/` ignored, fresh-checkout command works | met | check-ignore rc 0 |
| AC-12 inbox manifest | met | operator runbook on the iMac main checkout, 13 items + SHA-256, merged to main by PR #614 (table above) |
| AC-13 lint × 3 | met | run 1 (repeated 2, 3) |
| AC-14 three real smokes | **2 of 3** | fr_triage run 2, world_distill run 3; philosopher fails identically on main |
| AC-15 triage hook import, `now.py` | met | rc 0; line 487 |
| AC-16 focused + full suite | met on branch-vs-main parity | 0 branch-only failures; 28 platform failures identical |
| AC-17 stub gone, fragment, diary | met | `examples/philosopher/` deleted; fragment; diary (below) |
| AC-18 no new live artifact | met | seven consumer files repointed; none is a new live artifact |
| AC-19 human review of hook/pre-commit deletion, Scripture path edit, report, manifest | **NOT MET yet** | recorded at the PR |

## Judgement (2026-09-06)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1011-relocate-chaplain-live-parts.judgement.md](FR-1011-relocate-chaplain-live-parts.judgement.md).
R-1 (FR-1014 merged, three surfaces incl. `.pre-commit-config.yaml:34`),
R-2 (exact live-path inventory; narrower invariant + allowlist), R-3
(RED fails on assertions, not collection), R-4 (authoring brief; three
safe smokes), R-5 (`/proposals/`; behaviour-change wording; migration
as merge gate), R-6 (exact ACs; human gate) folded above.
