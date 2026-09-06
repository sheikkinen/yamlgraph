# Feature Request: Archive the Chaplain runtime (`.chaplain/`) — umbrella plan

**Priority:** MEDIUM
**Type:** Enhancement (subtraction)
**Status:** Proposed
**Effort:** 3 phases, 3 FRs; this FR is the plan, not an implementation
**Requested:** 2026-09-06
**First consumer / first event:** the next agent session that starts
work in this workspace and reads `scripts/vscode/now.py` output, at the
moment it would otherwise open `.chaplain/README.md` to understand a
runtime that has not run since 2026-07-07. Second consumer: the operator,
at the moment of the next spark, writing to an inbox whose surrounding
directory is a graveyard.
**Research:** in-body dispositioned alternatives table (§ Alternatives
Considered, FR-889 style) — three approaches, evidence per row, one
selected. Evidence gathered 2026-09-06 from the live tree; every claim
below cites a path or a timestamp.
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
- CAP-75 "portable chaplain" — the idea that the runtime is a standalone
  artifact. Phase 2 realises it as an archived repo rather than a
  rendered template.
- [FR-180-plan-phase-id-reservation.md](FR-180-plan-phase-id-reservation.md)
  — `.chaplain/id-registry.yaml`. Dispositioned here as dead: frozen at
  `next_cap: 94 / next_req: 246` since 2026-04-19 against a live maximum
  of CAP-263 / REQ-YG-663; its validator checks only internal
  consistency, so the `validate-id-registry` pre-commit gate passes
  vacuously (`gate_checks_shape_not_substance`).

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
archived repo's history (Phase 2).

## Ideal Result

`.chaplain/` does not exist on `main`. `proposals/` holds sparks and is
the only inbox the skills name. `graphs/fr_triage/`,
`graphs/world_distill/`, `graphs/philosopher/` are ordinary governed
graphs under the authoring guard. The FSM runtime lives, runnable and
read-only, in an archived GitHub repo reachable from one paragraph in
`docs/archive/chaplain.md` and a `chaplain-archive` tag on `main`. Every
CAP that described the runtime says `status: retired`; no test
references a path that does not exist; the `validate-id-registry` hook
is gone; Scripture names the actual SDLC, not the daemon. Nothing else
about how work gets done changes.

## Proposed Solution

Approach **C + B1 + B3** from the alternatives table: extract the live
parts, subtree-split the directory into its own archived repo, remove it
from `main`, then sweep doctrine. Three FRs, one concern each, each
leaving `main` fully working.

### Phase 1 — FR-1011 `refactor(chaplain): relocate live parts`

Pure relocation; no behaviour change.

- `mkdir proposals/`; move the 8 carried inbox items there; drop 3, forward
  1, `rm -r ninchat_voice/`. **Not** `feature-requests/inbox/`: the
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
- Delete the `examples/philosopher/` stub.
- Update consumers: `feature-request/SKILL.md`, `graph-authoring/doctrine.md`,
  `session-introspection/SKILL.md`, `checks/fr-checks.sh`,
  `checks/triage_gate.py` (import path), `scripts/vscode/now.py`,
  `pre-command-guard.sh:170,187` and `check_authoring_proof.py:25`
  (**delete** the `.chaplain/graphs` arm), Scripture's `.chaplain/inbox/`
  mention (one line, path only — no doctrine change).
- Guard gap found while tracing (FR-1011 § "Guard gap"): the `graphs/`
  and `.chaplain/graphs/` regex arms match flat files only; every
  dir-style graph (`*/graph.yaml`, `*/prompts/*.yaml`) under either root
  — including `graphs/enforcement/` — has never been governed. FR-1011
  puts the fix (dir-aware `graphs/` arm) before the Judge as option (a)
  with a witness; the plan records that the `.chaplain` arm was vacuous.
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

### Phase 2 — FR-1012 `chore(chaplain): subtree-split and remove runtime`

- `scripts/worktree.sh unlock-main` (FR-889) for the removal commit only.
- `git subtree split -P .chaplain -b chaplain-archive` → push to a new
  repo `sheikkinen/yamlgraph-chaplain` → GitHub "archive repository".
- `git tag chaplain-archive <pre-removal SHA>` on `main`.
- `git rm -r .chaplain`; delete `.github/skills/chaplain-ops/`,
  `scripts/chaplain-prompts/`, `scripts/validate_id_registry.py`,
  `scripts/id_registry.py` and the `validate-id-registry` hook,
  `scripts/finalize_merge.sh` (sole consumer of `finalize_lib.sh`;
  operator merges via `gh pr merge`), `.chaplain/inquisitor.sh` goes with
  the directory.
- `status: retired` + `retired_by: FR-1012` on every CAP whose subject is
  the runtime (~23 of the 27; the 4 already retired are left as-is).
  FR-701's gate rejects live marks on retired REQs, so the dead tests are
  deleted **in the same commit**.
- The 59-file keep/delete disposition is produced by a corpus-map-reduce
  census (59 × ~2k tokens, cheap-map tier; `reference/patterns/corpus-map-reduce.md`),
  committed as `docs/census/chaplain-test-disposition.jsonl`, then applied.
  Hand-classification is the fallback, not the default (`is_this_a_graph`).
- Sweep `.github/hooks/tests/` (Tier 2, outside `req_coverage`) for
  `.chaplain` path references.
- `docs/archive/chaplain.md`: one paragraph, the tag, the repo URL, a
  table "what each piece was replaced by".

### Phase 3 — FR-1013 `docs(doctrine): chaplain sweep`

- Scripture: rename "Sermon of the Chaplain" section heading and the
  proposal-submission route (`.chaplain/inbox/` → `proposals/`);
  `docs/development-process.md`; `reference/onepager-development-process.md`;
  `reference/audit-index.md`; `examples/README.md`; `CLAUDE.md`;
  `ramp/assets/tier2/github/skills/judge-fr/doctrine.md`;
  `ramp/curation-diffs.md`.
- Scripture edits go through the judge, never same-session with the
  detection (`guard_widening_when_caught` at Scripture scale).

### Sequencing constraint

Phase 1 must merge before Phase 2 starts; Phase 2 before Phase 3. Each
phase FR is judged independently and cites this FR as its plan. A phase
that discovers a fourth live artifact amends **this** FR's live-parts
table before proceeding — the plan is the source of truth.

## Acceptance Criteria (for this umbrella FR)

- [ ] Live-parts table and inbox disposition table above are accepted as
      the frozen inventory; Phase FRs may only add rows via amendment here.
- [ ] Approach C + B1 + B3 is the selected path; A is rejected with the
      rationale in the alternatives table.
- [ ] FR-1011, FR-1012, FR-1013 are filed with `**Plan:** FR-1010` in their
      headers and scope limited to their phase.
- [ ] This FR's Status moves to `Completed` only when FR-1013 merges.

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

## Alternatives Considered

| # | Approach | Evidence | Disposition |
|---|---|---|---|
| A | Tombstone in place: `ARCHIVED` banner, retire CAPs, delete their tests, leave files | Smallest diff. Leaves 161 dead tracked files under a 555-locked dir; vulture/jscpd entropy; live inbox stays inside a graveyard; Commandment 8 violated | **Rejected** |
| B | Extract live parts → `git rm` → doc sweep; recoverability via tag + git history | Cleanest `main`. Runtime not runnable without a checkout of the tag | **Selected for B1 (relocate) and B3 (doc sweep)** |
| C | `git subtree split` to `sheikkinen/yamlgraph-chaplain` (archived), then B | Runtime stays runnable standalone (CAP-75's intent); one extra repo; same `main` end state as B | **Selected for the removal step** |

## Related

- `.github/skills/chaplain-ops/SKILL.md` — to be deleted in Phase 2
- `docs/diary/diary-2026-07-29-the-mass-is-not-where-it-looks.md` — the
  sediment observation that this plan partially answers
- `reference/patterns/corpus-map-reduce.md` — Phase 2 census contract
- Session memory of the 2026-09-06 inventory: every count above is
  reproducible with `grep -rlE '\.chaplain|inquisitor' tests/ --include='*.py' | wc -l`
  and `ls capabilities | grep -iE 'chaplain|watcher|inquisitor|philosopher|inbox|triage|distill'`

## Judgement (pending)
