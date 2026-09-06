# The Chaplain runtime — archived (FR-1012, Phase 2 of FR-1010)

The `.chaplain/` directory held YAMLGraph's autonomous FSM pipeline (dispatcher and
worker, watcher graphs, inquisitor, inbox importer). It last ran on 2026-07-07 and was
removed from `main` on 2026-09-06. Its source is preserved, read-only, as history:

| Identity | Value |
|---|---|
| Tag on this repository | `chaplain-archive` → `0184a73d22500bd2bc678be8374bc4095de4575f` (`PRE`, the last commit with `.chaplain/`, `.chaplain` tree `3b25919cf65438f6d8167c62d4828c0f04215d03`) |
| Archived repository | https://github.com/sheikkinen/yamlgraph-chaplain — **private**, archived (read-only), default branch `main` |
| Split history head | `b31f58492832a2b3c4fdc1cec4e0625f3f0e97e7` (`SPLIT`, `git subtree split -P .chaplain`) |
| Archive head | `cf30d87f120aa16e12b441869c32209073e97fb6` (`ARCHIVE_HEAD`: SPLIT plus one commit prepending the banner to `README.md`) |
| Manifest | `docs/census/chaplain-archive-manifest.txt` — 146 files, sha256 `3d4a77faa5b2db99ad8b48a4c6a24173ed126aa7d4a0882b0a4938813b154b2d`; every file byte-identical to PRE except `README.md` |

Design note (the FSM as it was built and operated): [chaplain-system.md](chaplain-system.md), moved here from `docs/context/` by FR-1013.

The archive is **not a runnable distribution**: `scripts/start-system.sh` climbs `../..`
and expects the parent repository around it. Recover a file with
`git show chaplain-archive:.chaplain/<path>` here, or browse the archived repository.

## What replaced each piece

| Was in `.chaplain/` | Replaced by |
|---|---|
| `inbox/` (untracked sparks) | `proposals/` at the repository root, untracked (FR-1011; feature-request skill) |
| `graphs/fr_triage/` | `graphs/fr_triage/` — FR-745 triage gate (`.github/hooks/scripts/checks/triage_gate.py`) |
| `graphs/world_distill/` | `graphs/world_distill/` — FR-744 world file |
| `graphs/philosopher/` + `lib/diary.py` | `graphs/philosopher/` with a sibling `diary.py` (dormant; broken on `main` before the move, see FR-1011) |
| `lib/finalize_lib.sh` | `scripts/lib/finalize_lib.sh`, sourced by `scripts/finalize_merge.sh` (CAP-38, CAP-45) |
| `id-registry.yaml` + `scripts/id_registry.py` + `validate_id_registry.py` + hook | mechanical enumeration at filing (`max(ids on main + all open PR heads) + headroom`) and FR-701's `validate_capabilities.py::validate_registry()` duplicate gate (FR-1015) |
| watcher FSM (dispatcher, worker, plan/enforce/forensic graphs, actions, config) | the operator-driven loop: `scripts/author.sh`, `scripts/judge.sh`, `scripts/review.sh`, `scripts/outsider.sh`, worktree-per-PR (`scripts/worktree.sh`), human merge (`reference/command-book.md`) |
| `inquisitor.sh` | none — retired |
| `.github/skills/chaplain-ops/`, `scripts/chaplain-prompts/` | none — retired with the runtime |

Census of what was deleted and what was kept: `docs/census/chaplain-test-disposition.md`
(41 test files deleted, 24 capability records retired, 50 items kept), produced by
`scripts/chaplain_census.py`; archive journal `docs/census/chaplain-archive.run.json`
produced by `scripts/chaplain_archive.sh`.
