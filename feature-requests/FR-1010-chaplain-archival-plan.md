# Feature Request: Archive the Chaplain runtime (`.chaplain/`) — umbrella plan

**Priority:** MEDIUM
**Type:** Enhancement (subtraction)
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-06). R-1..R-9 folded
below; see [FR-1010-chaplain-archival-plan.judgement.md](FR-1010-chaplain-archival-plan.judgement.md).
R-2 decision recorded (supersede). Grants authority only to file and
independently judge FR-1014, FR-1011, FR-1015, FR-1012, FR-1013 in that
order; no implementation or deletion authority.
**Effort:** 5 phase FRs; this FR is the plan, not an implementation
**Requested:** 2026-09-06
**First consumer / first event:** the next agent session that starts
work in this workspace and reads `scripts/vscode/now.py` output, at the
moment it would otherwise open `.chaplain/README.md` to understand a
runtime that has not run since 2026-07-07. Second consumer: the operator,
at the moment of the next spark, writing to an inbox whose surrounding
directory is a graveyard.
**Research:** in-body dispositioned alternatives table (§ Alternatives
Considered, FR-889 style) — six solution classes with precedent lines and
preserved disagreement, one selected (R-1). `is_this_a_graph`: **no** for
the archival itself (deterministic repository work); **yes** for the
Phase 2 test/CAP disposition census, which reuses
`reference/patterns/corpus-map-reduce.md`. Evidence gathered 2026-09-06
from the live tree; every claim below cites a path or a timestamp.
**Prior art:**
- [FR-276-retire-old-pipeline-scripts.md](FR-276-retire-old-pipeline-scripts.md)
  — retired the pre-FSM pipeline scripts; this FR retires the FSM that
  replaced them. Same shape, larger blast radius.
- [FR-317-retire-obsolete-watcher2-components.md](FR-317-retire-obsolete-watcher2-components.md)
  — partial watcher2 retirement inside `.chaplain/`; this FR completes it
  by removing the directory.
- [FR-465-watcher2-test-cleanup.md](FR-465-watcher2-test-cleanup.md) +
  [FR-466-cap-retirement-support.md](FR-466-cap-retirement-support.md) —
  the `status: retired` mechanism and the test-deletion discipline this
  plan relies on. Reused, not re-invented.
- [FR-927-retire-fr902-lane-guard-hooks.md](FR-927-retire-fr902-lane-guard-hooks.md) — most recent retirement of
  enforcement machinery; precedent that a hook can be deleted, not only
  widened.
- CAP-75 "portable chaplain" — graph-root-relative tool loading **at graph
  scope only** (`capabilities/CAP-75-portable-chaplain.yaml:3-29`). It does
  not make the runtime portable: `start-system.sh:16` computes
  `PROJECT_ROOT=../..` and `:23-24` expect `.chaplain/config`,
  `.chaplain/actions` under the parent repo. The Phase 2 archive is
  therefore **source-only**, not runnable standalone (R-3).
- [FR-180-plan-phase-id-reservation.md](FR-180-plan-phase-id-reservation.md)
  — `.chaplain/id-registry.yaml`. Frozen at `next_cap: 94 / next_req: 246`
  since 2026-04-19 against a live maximum of CAP-263 / REQ-YG-663; its
  validator checks only internal consistency, so the `validate-id-registry`
  pre-commit gate passes vacuously (`gate_checks_shape_not_substance`).
  **Its deletion is NOT authorised by this plan** — see the next three
  entries (R-2).
- [FR-970-load-bearing-atomic-id-allocation.md](FR-970-load-bearing-atomic-id-allocation.md)
  — SPLIT 2026-09-03; its judgement (`:77-80`) explicitly withholds
  authority to delete or retire `.chaplain/id-registry.yaml`,
  `scripts/id_registry.py`, or their tests.
- [FR-975-id-ledger-reservation-protocol.md](FR-975-id-ledger-reservation-protocol.md)
  — APPROVED WITH REVISIONS 2026-09-03, unimplemented; bootstraps the
  canonical ledger **from** the legacy registry (`:125-136`).
- [FR-980-id-ledger-route-enforcement.md](FR-980-id-ledger-route-enforcement.md)
  — APPROVED WITH REVISIONS 2026-09-03, unimplemented; AC-11 assigns the
  legacy allocator/validator/hook purge to a separate commit **after** a
  ledger bootstrap witness. This plan does not duplicate that purge.
  Disposition: Phase 2 leaves `id-registry.yaml`, `id_registry.py`,
  `validate_id_registry.py` and the `validate-id-registry` hook in place
  unless the R-2 human decision below supersedes FR-975/FR-980.
- [FR-1011](FR-1011-relocate-chaplain-live-parts.md) sibling finding:
  `scripts/finalize_merge.sh` is **live** — CAP-38/REQ-YG-125 (post-merge
  finalization) and CAP-45/REQ-YG-144 (diary stub) still define it;
  `tests/unit/test_finalize_merge.py` witnesses it. Only CAP-114's
  automatic watcher integration is dead (R-4). The earlier draft of this
  plan proposed deleting the script because it was the sole consumer of
  `.chaplain/lib/finalize_lib.sh`; that reversed the dependency
  direction and is withdrawn.

## Summary

`.chaplain/` is the FSM-based autonomous pipeline (dispatcher + worker,
inbox sync, worktree lifecycle, PR automation, inquisitor, philosopher).
It is not in use: the actual SDLC is `scripts/author.sh` → FR →
`scripts/judge.sh` → worktree-per-PR enforcement → `scripts/review.sh`
→ human merge. That path requires little supervision but is not fully
automatic, and the fully automatic daemon has not run since July.

Three live parts are buried inside the dead directory and must be
extracted first: the proposal inbox (spark capture), the `fr_triage`
graph (FR-745 gate), and the `world_distill` graph (FR-744 world file).
`philosopher` has a real copy in `.chaplain/graphs/` and a stub pointing
at it in `examples/philosopher/`.

This FR is the plan. It authorises nothing by itself; each phase is its
own judged FR with its own witness tests. The phases are ordered so that
every intermediate `main` is fully working.

## Value Statement

Agents and the operator stop paying orientation cost for a runtime
nobody runs; the three live artifacts get canonical homes; ~50 dead
test files and ~23 CAPs stop inflating the census; one hollow gate is
removed.

## Problem

Liveness evidence (all read from the tree on 2026-09-06):

| Signal | Value |
|---|---|
| Dispatcher / worker process | not running (`pgrep` empty) |
| `.chaplain/done/` last write | 2026-07-07 |
| `.chaplain/processing/` | stuck since 2026-05-21 (`gh-432.md`, `gh-433.md`) |
| `.chaplain/inquisitor.log` last entry | 2026-04-21 |
| `.chaplain/id-registry.yaml` last reservation | 2026-04-19 |
| Directory mode | `dr-xr-xr-x` (FR-889 main-write lock) |
| Tracked files | 161 (238 on disk incl. ignored `failed/`, `inbox/`, `__pycache__`) |

Coupling outside the directory:

| Class | Count | Notes |
|---|---|---|
| `tests/**/*.py` referencing `.chaplain` or `inquisitor` | 59 files, ~730 tests | mostly `watcher2` FSM witnesses |
| `capabilities/CAP-*.yaml` | 27 | 4 already `status: retired` |
| Governed-path regexes | 3 | `pre-command-guard.sh:170,187`, `check_authoring_proof.py:25` |
| Hook imports | 1 | `checks/triage_gate.py` imports `.chaplain/graphs/fr_triage/tools.py` |
| Skills | 5 | `chaplain-ops` (whole), `feature-request`, `graph-authoring`, `judge-fr` (lineage comment), `session-introspection` |
| Scripts | 4 | `finalize_merge.sh` (sources `.chaplain/lib/finalize_lib.sh`), `validate_id_registry.py`, `id_registry.py`, `scripts/chaplain-prompts/` |
| Doctrine / docs | ~8 | Scripture "Sermon of the Chaplain" + inbox route, `docs/development-process.md`, `reference/onepager-development-process.md`, `reference/audit-index.md`, `examples/README.md`, `CLAUDE.md`, `ramp/assets/tier2` judge-fr doctrine, `ramp/curation-diffs.md` |

### What is still live (must not be deleted)

| Artifact | Consumer | Evidence |
|---|---|---|
| `.chaplain/inbox/` | operator sparks; `feature-request/SKILL.md:88`; `graph-authoring/doctrine.md:116` | 13 items, newest 2026-08-31 |
| `.chaplain/graphs/fr_triage/` | FR-745 triage gate (`checks/triage_gate.py`, `checks/fr-checks.sh:77`) | imported at hook time |
| `.chaplain/graphs/world_distill/` | FR-744 world file; `scripts/vscode/now.py`; `session-introspection/SKILL.md:40` | |
| `.chaplain/graphs/philosopher/` | `tests/unit/test_philosopher.py`; `examples/philosopher/README.md` is a stub that points here. **Dormant**, not live: no consumer outside its tests since the daemon stopped; kept because it is the only implementation of the `diary_graduation_pipeline` seed | `tools.py:371` proxies `.chaplain/lib/diary.py` by `parents[2]/lib/diary.py` — relocation must carry `diary.py` (178 lines, no other live consumer) into `graphs/philosopher/` |
| `.chaplain/lib/finalize_lib.sh` | `scripts/finalize_merge.sh:25` (`source`); CAP-38/REQ-YG-125, CAP-45/REQ-YG-144; `tests/unit/test_finalize_merge.py` | **Live** (R-4). Relocate to `scripts/lib/finalize_lib.sh`; keep `finalize_merge.sh`; update CAP-114 source paths; retire only CAP-114's watcher-automation claim in Phase 2 |

### ID-allocation decision (R-2) — human, recorded here before FR-1012 is filed

> Does Chaplain archival supersede the unimplemented FR-975/FR-980
> ID-ledger program, or must FR-975's bootstrap land first so that
> FR-980's legacy purge (AC-11) — not this plan — deletes
> `.chaplain/id-registry.yaml`, `scripts/id_registry.py`,
> `scripts/validate_id_registry.py` and the `validate-id-registry` hook?

| Option | Consequence for Phase 2 |
|---|---|
| (i) FR-975/FR-980 remain active (**default**) | Phase 2 `git rm -r .chaplain` must **exclude** `id-registry.yaml` — move it to the path FR-975 names for the legacy source, or leave `.chaplain/id-registry.yaml` as the sole surviving file until FR-980 AC-11 purges it. `id_registry.py`, `validate_id_registry.py`, the hook and their tests stay. |
| (ii) Archival supersedes them | Amend FR-975/FR-980 status and their CAP/REQ claims **first** (separate FR), define the replacement for direct Plan/Enforce allocation, then Phase 2 may delete the legacy allocator. |

**Decision (operator, 2026-09-06): (ii) supersede.** Chaplain archival
supersedes the unimplemented FR-975/FR-980 ID-ledger program. Consequence,
per option (ii): a new phase **FR-1015 `docs(fr): supersede FR-975/FR-980
under FR-1010`** is filed and merged **before** FR-1012. It sets both FRs'
Status to `Superseded by FR-1010`, retires their CAP/REQ claims (verify
with `grep -oE 'CAP-[0-9]+|REQ-YG-[0-9]+'` on both FRs at filing — the
2026-09-06 read shows only CAP-170 / REQ-YG-580 referenced), and states
the replacement for direct Plan/Enforce ID allocation. The de-facto
replacement already in force since 2026-04-19 — `max(main + all open PR
heads) + headroom`, mechanically enumerated at filing (`one_session_one_repo`,
`collision_by_increment`) — is named as the contract; FR-1015 may not
introduce a new allocator. FR-1012 may then delete `.chaplain/id-registry.yaml`,
`scripts/id_registry.py`, `scripts/validate_id_registry.py`, the
`validate-id-registry` hook and their tests, under the same census
discipline as every other Phase 2 deletion (AC-09). FR-701's
duplicate-registry validation in `validate_capabilities.py` is untouched
(C-7).

### Inbox pre-check (2026-09-06)

Each item was checked against code, not FR titles.

| Item | Disposition | Evidence |
|---|---|---|
| capability-domain-activity-heatmap | carry | no FR |
| example-provenance-audit-graph | carry | no FR |
| index-memento-frs-into-prior-art | carry | 40 files in `docs/memento/feature-requests/`; `checks/prior_art.py` never scans it |
| judge-regression-fixture | carry | no FR |
| pin-interpreter-in-measurement-routes | carry | `scripts/research.sh:54` still `command -v yamlgraph` |
| prior-art-self-exclusion-misses-judgement-sibling | carry | `checks/prior_art.py:222` excludes exact path only |
| supersede-disposition-gate | carry | template has only the backward FR-738 gate; this FR is its use case |
| workspace-sediment-audit | carry | no FR; this plan is partly it |
| deviantart-auto-publish-pipeline | drop (stale) | FR-822 spike + FR-826 "Enforced 2026-08-19 — repo live" |
| refactor-pre-command-guard-dispatcher | drop (stale) | guard is 417 lines, 0 python heredocs, per-check modules under `checks/` — FR-889/FR-927, same day |
| research-prompts-contradict-precedent-validator | drop (stale) | `brief-echo` absent from all five persona prompts; `research_tools.py:438` records the demotion as removed |
| deviant-daily-curated-rerun | forward | belongs to `sheikkinen/deviant-daily` |
| `ninchat_voice/` | rm | empty directory since 2026-05-19 |

8 carry · 3 drop · 1 forward · 1 rm. Dropped items remain readable in the
archived repo's history (Phase 2) only if they were ever committed — they
were not (the inbox is untracked); FR-1010's table is their tombstone.

**The inbox is untracked** (`.gitignore:100`; `git ls-files .chaplain/inbox`
empty; absent from every worktree). The physical migration therefore
cannot be a PR-delivered `mv` (R-6). It is an **operator-owned runbook on
the main checkout**, executed before FR-1011 merges and recorded in
FR-1011:

1. `shasum -a 256 .chaplain/inbox/*.md > tmp/inbox-manifest.txt` — freeze
   the 13-item inventory (filenames + hashes).
2. `mkdir -p proposals && cp` the eight carried items to `proposals/`.
3. Confirm the three drops, the one forward (copied to the deviant-daily
   checkout), and `rmdir .chaplain/inbox/ninchat_voice` against the table.
4. `shasum -a 256 -c` on the eight destination files before deleting the
   eight source copies.
5. Paste the manifest (names + hashes, not contents) into FR-1011's
   implementation record. Proposal contents are never committed.

Phase 2 may not remove `.chaplain/` until FR-1011 records this manifest
and the operator confirms `.chaplain/inbox/` is empty (C-5).

## Ideal Result

`.chaplain/` does not exist on `main`. `proposals/` holds
sparks and is the only inbox the skills name. `graphs/fr_triage/`,
`graphs/world_distill/`, `graphs/philosopher/` are ordinary governed
graphs under a dir-aware authoring guard (FR-1014). `scripts/lib/finalize_lib.sh`
serves `scripts/finalize_merge.sh` unchanged. The FSM runtime's source is
preserved, read-only, in an archived GitHub repo whose README states it is
historical source, not a runnable distribution, reachable from one
paragraph in `docs/archive/chaplain.md` and a `chaplain-archive` tag on
`main`. Every CAP that described the runtime says `status: retired`; no
test references a path that does not exist; Scripture names the actual
SDLC, not the daemon. Nothing else about how work gets done changes.

## Proposed Solution

Approach **C′ + B1 + B3** from the alternatives table: harden the guard,
extract the live parts, subtree-split the directory into a source-only
archived repo, remove it from `main`, then sweep doctrine. Four FRs, one
concern each, each leaving `main` fully working, merged in this order
(C-3):

### Phase 0 — FR-1014 `feat(hooks): dir-aware authoring guard for graphs/`

Independent enforcement hardening (R-5), merged **before** relocation.
`pre-command-guard.sh:169` and `check_authoring_proof.py:25` gain
`graphs/.+/graph\.ya?ml$` and `graphs/.+/prompts/[^/]+\.ya?ml$`; the
flat `graphs/[^/]+\.ya?ml$` arm stays; RED witnesses for
`graphs/enforcement/changelog-req-check.yaml`, a dir-style `graph.yaml`,
a dir-style prompt, and a negative (`graphs/README.md`). Human review
before merge (C-4).

### Phase 1 — FR-1011 `refactor(chaplain): relocate live parts`

Path relocation with no graph or finalizer semantic change; the inbox
route's path changes (FR-1011 R-5).

- `mkdir proposals/` in the tree with a `.gitkeep`-free `.gitignore`
  entry; the eight carried inbox items are migrated by the operator
  runbook above, **not** by the PR. Not `feature-requests/inbox/`: the
  `^feature-requests/.*\.md$` patterns in `.pre-commit-config.yaml:280,286`
  would fire `prior-art-gate` and `triage-gate` on sparks that have no
  disposition sections.
- `mv .chaplain/graphs/{fr_triage,world_distill,philosopher} graphs/`
  (dir-style precedent: `graphs/enforcement/`). `.chaplain/lib/diary.py`
  moves to `graphs/philosopher/diary.py` and the proxy path in
  `tools.py:371` becomes `Path(__file__).with_name("diary.py")`. The move
  IS graph authoring per `.github/skills/graph-authoring/doctrine.md` →
  sole route `scripts/author.sh`, lint + smoke each graph from its new
  path.
- `git mv .chaplain/lib/finalize_lib.sh scripts/lib/finalize_lib.sh`;
  `scripts/finalize_merge.sh:25` source path updated; CAP-114 `source:`
  paths updated; `tests/unit/test_finalize_merge.py` green with
  `.chaplain/lib/finalize_lib.sh` absent (R-4).
- Delete the `examples/philosopher/` stub.
- Update consumers: `feature-request/SKILL.md`, `graph-authoring/doctrine.md`,
  `session-introspection/SKILL.md`, `checks/fr-checks.sh`,
  `checks/triage_gate.py` (import path), `scripts/vscode/now.py`,
  `pre-command-guard.sh` and `check_authoring_proof.py`
  (**delete** the `.chaplain/graphs` arm only — FR-1014 already owns the
  widening), Scripture's `.chaplain/inbox/` mention (one line, path only —
  no doctrine change).
- Guard gap found while tracing (FR-1011 § "Guard gap"): the `graphs/`
  and `.chaplain/graphs/` regex arms match flat files only; every
  dir-style graph (`*/graph.yaml`, `*/prompts/*.yaml`) under either root
  — including `graphs/enforcement/` — has never been governed. The fix
  is FR-1014 (Phase 0); the plan records that the `.chaplain` arm was
  vacuous.
- Guard: `.chaplain/inbox/` ceases to exist; a write there fails with
  `ENOENT` from the shell — visible, not silent. No guard grammar is added
  for the old path (FR-889 C-5: the kernel is the barrier). A symlink is
  forbidden (Commandment 8: no shims).
- Inbox is **untracked** (`.gitignore:100`; absent from every worktree).
  Relocation preserves that; the durability/visibility question is filed
  as a spark in `proposals/`, not decided here.
- Tests: path updates in `test_fr_triage.py`, `test_world_distill.py`,
  `test_philosopher.py`, `test_chaplain_graph_compile.py`; new
  `test_fr1011_relocation.py` witnesses (no `.chaplain` literal in live
  consumers; `diary.py` sibling; governed-path predicate).

### Phase 1½ — FR-1015 `docs(fr): supersede FR-975/FR-980 under FR-1010`

Records the R-2 decision in the superseded FRs themselves (Status,
CAP/REQ claim retirement, named replacement contract). Docs-only; judged
independently; merged before FR-1012 so that Phase 2's census can mark
the legacy ID artifacts `delete` with a committed authority behind it.

### Phase 2 — FR-1012 `chore(chaplain): subtree-split and remove runtime`

Filed only after FR-1015 has merged and FR-1011 has merged with its inbox
manifest recorded (C-5). Human review before merge for repo
creation/archive, tag push, mass deletion, hook removal (C-4).

- **Census first (R-7).** A corpus-map-reduce run over the 59 test files
  + 27 CAPs produces `docs/census/chaplain-test-disposition.jsonl`: per
  test file — path, referenced REQs, shared-REQ fan-in (tests outside the
  set marking the same REQ), keep/delete, reason; per CAP — id, current
  status, proposed transition. All eight invariants of
  `reference/patterns/corpus-map-reduce.md:198-223` (identity/coverage
  reconciliation, withheld semantic canary, raw primary outputs
  preserved and read before reduction, `:380-396`). FR-1012 may delete
  only rows marked `delete` in the reviewed artifact.
- `scripts/worktree.sh unlock-main` (FR-889) for the removal commit only.
- `git subtree split -P .chaplain -b chaplain-archive` → push to a new
  repo `sheikkinen/yamlgraph-chaplain` with a README stating **historical
  source, not a runnable distribution** (R-3) → GitHub "archive
  repository".
- `git tag chaplain-archive <pre-removal SHA>` on `main`, pushed.
- `git rm -r .chaplain` — including `id-registry.yaml`; and delete
  `scripts/id_registry.py`, `scripts/validate_id_registry.py`, the
  `validate-id-registry` hook and their tests — **only** as rows marked
  `delete` in the census, with FR-1015 merged as the authority (R-2
  decision (ii)). FR-701's duplicate-registry validation untouched (C-7).
- Delete `.github/skills/chaplain-ops/`, `scripts/chaplain-prompts/`.
  `scripts/finalize_merge.sh` **stays** (C-6).
- `status: retired` + `retired_by: FR-1012` on every CAP the census marks
  for retirement (CAP-114's watcher-automation claim among them; CAP-38
  and CAP-45 stay live). Dead tests deleted **in the same commit**
  (FR-701 gate).
- Sweep `.github/hooks/tests/` (Tier 2, outside `req_coverage`) for
  `.chaplain` path references.
- `docs/archive/chaplain.md`: one paragraph, the tag, the repo URL, its
  archive status, a table "what each piece was replaced by".

### Phase 3 — FR-1013 `docs(doctrine): chaplain sweep`

- Scripture: rename "Sermon of the Chaplain" section heading and the
  proposal-submission route (`.chaplain/inbox/` → `proposals/`);
  `docs/development-process.md`; `reference/onepager-development-process.md`;
  `reference/audit-index.md`; `examples/README.md`; `CLAUDE.md`;
  `ramp/assets/tier2/github/skills/judge-fr/doctrine.md`;
  `ramp/curation-diffs.md`.
- Scripture edits go through the judge, never same-session with the
  detection (`guard_widening_when_caught` at Scripture scale). Human
  review before merge (C-4).

### Sequencing constraint

FR-1014 → FR-1011 → FR-1015 → FR-1012 → FR-1013, each merged before the
next starts (C-3). Each phase FR is judged independently, carries
`**Plan:** FR-1010`, and may not borrow scope from a later phase. A phase
that discovers a further live artifact **stops** and returns to judgement
under C-10 — the plan is the source of truth.

## Acceptance Criteria (R-8; mechanical phase gates)

- [ ] AC-01: `**Research:**` points to committed evidence with six solution
      classes, precedent lines, preserved disagreement, and an explicit
      `is_this_a_graph` answer; the selected approach is a source-only
      archive.
- [ ] AC-02: The live-parts table names every extracted path, including
      `.chaplain/lib/finalize_lib.sh`, its `scripts/finalize_merge.sh`
      consumer, and CAP-38/CAP-45/CAP-114 disposition.
- [ ] AC-03: The R-2 decision line is filled by the operator (**done:
      supersede**); FR-1015 amends FR-975/FR-980 and merges before
      FR-1012; Phase 2 deletes the legacy ID artifacts only as census
      `delete` rows.
- [ ] AC-04: FR-1014, FR-1011, FR-1015, FR-1012, FR-1013 each contain
      `**Plan:** FR-1010`, one phase concern, a human-reviewed judgement,
      and merge in that order.
- [ ] AC-05: FR-1014 has RED witnesses for dir-style `graphs/**/graph.yaml`
      and `graphs/**/prompts/*.yaml` governance, retains flat-graph
      behaviour, and is human-reviewed before merge.
- [ ] AC-06: FR-1011 preserves `scripts/finalize_merge.sh` by relocating
      its library; `tests/unit/test_finalize_merge.py` passes with
      `.chaplain/lib/finalize_lib.sh` absent.
- [ ] AC-07: FR-1011 records the operator-confirmed 13-item inbox manifest
      (names + SHA-256), hash-verifies the eight carried items, records
      the three drops and one forward, and confirms `.chaplain/inbox/` is
      empty before Phase 2 starts.
- [ ] AC-08: Lint and real smoke records exist for the three relocated
      `graph.yaml` files; their direct tests and the triage hook import
      pass from the new paths.
- [ ] AC-09: FR-1012 commits `docs/census/chaplain-test-disposition.jsonl`
      satisfying all eight corpus-map-reduce invariants; raw primary
      outputs reviewed; every deleted test/CAP named; shared-REQ fan-in
      reconciled; `req_coverage --strict` green.
- [ ] AC-10: A fresh clone of `sheikkinen/yamlgraph-chaplain` at its
      archived default branch contains the complete source snapshot and a
      README stating it is historical source, not a runnable
      distribution.
- [ ] AC-11: `git ls-remote --tags origin chaplain-archive` resolves to the
      documented pre-removal commit; `docs/archive/chaplain.md` records
      tag, URL, archive status, replacement table.
- [ ] AC-12: After FR-1013, `grep -rn '\.chaplain' --include='*.md' --include='*.py' --include='*.sh' --include='*.yaml' . `
      (excluding `feature-requests/`, `changelog/`, `docs/diary/`,
      `docs/archive/chaplain.md`, `docs/memento/`) returns only
      enumerated, justified residuals.
- [ ] AC-13: This FR moves to `Completed` only after all four phase FRs
      merge in order, the remote tag and archived repo are verified, the
      inbox migration is confirmed, and each phase's implementation
      status is recorded here.

## Human gates (R-9, C-4)

Human review is mandatory, and the reviewed PR is recorded in the phase
FR, before: FR-1014 changes the authoring guard; FR-1012 creates/archives
the GitHub repo, pushes the tag, deletes the runtime and tests, or
removes any pre-commit hook; FR-1013 changes Scripture or the judge
doctrine mirror under `ramp/`. Phase judgements are advisory until then.

## Pre-mortem (`pre_mortem`, run before Phase 1 enforcement)

- Operator muscle memory `echo > .chaplain/inbox/x.md` breaks → `ENOENT`
  is visible; the feature-request skill names `proposals/`; `now.py`
  can print the path. No symlink.
- `fr_triage` / `world_distill` prompts may carry `.chaplain`-anchored
  relative paths or `cwd` assumptions → lint + smoke from the new path is
  the witness, not the `mv` exit code.
- Doc-witness tests assert on strings that vanish
  (`test_chaplain_readme_documentation.py`, `test_concurrency_safety_doc.py`,
  `test_fr748_fr_atlas.py`, `test_knowledge_graph_fr193.py`) → listed
  explicitly in FR-1012, not discovered at RED.
- `triage_gate.py` loads `fr_triage/tools.py` by filesystem path at hook
  time → if Phase 1 lands the graph before the hook path update, every
  FR commit fails; both changes in one commit.
- Retiring a CAP whose REQ is still marked by a *non-chaplain* test
  (shared REQ) → `req_coverage --strict` red; the census must report
  REQ→test fan-in, not only file→chaplain reference.
- Deleting `finalize_merge.sh` "because its lib is in `.chaplain`" →
  caught by the Judge (R-4): the dependency direction was reversed. The
  general form: *sole consumer of a dead file* ≠ *dead*; check the
  consumer's own CAP/REQ before following the link.
- Claiming the subtree archive is runnable → caught by the Judge (R-3):
  `start-system.sh` climbs `../..`. Read the entrypoint before promising
  portability.
- Not enumerating sibling FRs for an artifact I intended to delete
  (FR-970/975/980 on `id-registry.yaml`) → caught by the Judge (R-2).
  Prior-art retrieval is filename-noun ranked; `id-registry` shares no
  noun with `chaplain`. A `grep -l <artifact-path> feature-requests/`
  before dispositioning any deletion is the floor.

## Alternatives Considered (R-1: six solution classes)

| # | Class | Precedent | What it preserves / costs | Disposition |
|---|---|---|---|---|
| 1 | In-place tombstone: `ARCHIVED` banner, retire CAPs, delete their tests, leave 161 files under a 555 dir | — (FR-276 `:81-101` rejected symlink/deprecation preservation for its scripts) | Smallest diff; keeps dead code (Commandment 8), live inbox inside a graveyard, vulture/jscpd entropy | **Rejected** |
| 2 | Tag + history-only deletion: extract live, `git rm`, `chaplain-archive` tag; no external repo | FR-927 (hook machinery deleted, history is the archive) | Cleanest `main`; recovery = checkout tag. No browsable artifact outside git history | Viable; loses only discoverability vs §3 |
| 3 | **Source-only subtree archive** (`git subtree split` → archived repo) + §2 on `main` | CAP-75's portability *intent*, scoped down to source preservation after `start-system.sh:16,23-24` disproved runnability | Same `main` as §2; adds a browsable, linkable snapshot for the archive note; one extra repo | **Selected** (C′) |
| 4 | Runnable standalone archive: adapt `start-system.sh`, package deps, fresh-clone smoke | none — CAP-75 covers graph scope only | Revivable daemon; requires a researched migration FR with a dependency manifest and execution witness | **Deferred to a separate FR if ever wanted**; not an incidental effect of §3 |
| 5 | Extract live artifacts only; retain dormant runtime source on `main` (no deletion) | FR-317 (partial watcher2 retirement) | Zero deletion risk; leaves 27 CAPs and ~50 test files describing a runtime that does not run | **Rejected** — `growth_as_default` inverted: keeping is the risk |
| 6 | Full deletion, no tag, no external repo | — | Minimal ceremony; recovery requires knowing a SHA | **Rejected** — the tag costs nothing and names the boundary |

Preserved disagreement: §2 vs §3 differ only in whether a browsable
snapshot is worth one archived repo. The plan picks §3 because the
archive note in `docs/archive/chaplain.md` can link a URL a reader can
open; a reviewer who values repo count over discoverability would pick
§2 and lose nothing on `main`.

`is_this_a_graph`: the archival is deterministic file operations — **no**.
The 59-file/27-CAP disposition census is `for each item, ask the model`
— **yes**, `reference/patterns/corpus-map-reduce.md`.

## Related

- `.github/skills/chaplain-ops/SKILL.md` — to be deleted in Phase 2
- `docs/diary/diary-2026-07-29-the-mass-is-not-where-it-looks.md` — the
  sediment observation that this plan partially answers
- `reference/patterns/corpus-map-reduce.md` — Phase 2 census contract
- Session memory of the 2026-09-06 inventory: every count above is
  reproducible with `grep -rlE '\.chaplain|inquisitor' tests/ --include='*.py' | wc -l`
  and `ls capabilities | grep -iE 'chaplain|watcher|inquisitor|philosopher|inbox|triage|distill'`

## Judgement (2026-09-06)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1010-chaplain-archival-plan.judgement.md](FR-1010-chaplain-archival-plan.judgement.md).
R-1..R-9 folded above (research classes; FR-970/975/980 disposition + R-2
human decision; source-only archive; `finalize_lib.sh` live; FR-1014
split; operator-owned inbox runbook; exact census; mechanical ACs; human
gates). Conditions C-1..C-10 govern the phase FRs. Judgement route note:
the adapter wrote its artifact to `tmp/draft-judgement-copilot-FR-1010.md`
instead of the requested full-slug path, so `scripts/judge.sh` exited 65
("contract violated") while the judgement itself was complete; recorded
as a spark for the judge route, not fixed here.
