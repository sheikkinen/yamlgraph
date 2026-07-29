# The Mass Is Not Where It Looks

**Date:** 2026-07-29
**Context:** Continuation of "The Proposal I Never Made" — operator question: is codebase size getting in the way; should we clean up?

## The measurement (raw record first)

Asked "is the codebase too big," visibility says yes: 5,667 tracked
files, a 580 MB working tree beyond them. But `inventory_by_visibility`
is a named trap — rank by incident density, not mass. So, the split:

| Stratum | Size | Recent incidents caused |
|---|---|---|
| Framework core (`yamlgraph/`) | 135 files | ~0 |
| Tests / capabilities / reference | 487 + 198 + 43 files | 0 |
| Process record (diary 1,124, FRs 760, changelog 949) | ~2,800 files | 0 (append-only; it IS the value) |
| Examples (35 apps + 83 demos) | 1,588 files | 2 (FR-763 phantom roots; README-audit gate tripped by one stray draft) |
| Workspace sediment (untracked) | `projects/` 580 MB with **10+ nested .git repos**, `tmp/` 129 MB incl. worktrees, stale `langgraph_showcase.egg-info` from the pre-rename era, `build/`, `outputs/`, `vectorstore/` | 3+ (`workspace_is_not_boundary`, fr-board F7, `one_session_one_repo` interleaves) |
| Derived-doc duplication (skills layer) | was 3 overlapping entry points | 1 (discovery overlap, retired today) |

Five-plus incidents from sediment and duplication; approximately zero
from the size of the code. The framework is *small* — 135 files
producing everything else. What has mass is the exhaust (deliberate,
valuable, append-only) and the sediment (accidental, valueless,
incident-generating).

## The insight

"Should we clean up" is two questions wearing one sentence:

1. **Is the tracked codebase bloated?** No. Core is tiny; the gates
   (vulture, jscpd, radon, file-size, import-linter) already police it
   continuously. The process record is the paid-for knowledge estate —
   deleting diary entries or FRs would be burning the incident record
   that `constraint_over_code` says is the irreplaceable part.
2. **Is the workspace dragging?** Yes, measurably. Every incident in
   the table's bottom half came from matter that is *in the tree but
   not of the repo*: nested repos, worktrees, generated outputs, stale
   metadata under the project's former name. Agents pay this cost on
   every glob, taxonomy scan, semantic search, and destructive-op
   boundary check. Yesterday's README-audit failure was this class:
   one untracked draft directory broke a merge gate.

The trap name for the felt sense "5,667 files = too big" is
`inventory_by_visibility` pointed at ourselves. The cure is the same
ranking we apply to reimplementation triage: mass that generates
incidents gets cleaned; mass that encodes knowledge gets kept and
indexed; mass that witnesses gates (examples) gets *triaged by which
gate it witnesses* — an example that witnesses no CAP/REQ and no demo
is an app that rode along, not a witness.

## The heuristic

**Clean the sediment, keep the sermon.** Cleanup targets in priority
order of incident yield: (1) foreign trees out of the workspace
(`projects/` nested repos belong outside or in a declared multi-root
boundary); (2) ephemeral quarantine (`tmp/` drafts and worktrees get a
retention rule); (3) stale generated artifacts (`build/`, old
egg-info, `outputs/`); (4) example triage by witness-mapping, not age;
(5) continued CAP claim retirement (FR-465/466 precedent). Non-targets:
diary, FRs, changelog — append-only by doctrine.

## Seed

The gates police tracked code but nothing polices the *workspace*:
could a `workspace-hygiene` check (pre-commit or `now.py` sibling)
inventory untracked mass — nested `.git` dirs, stale egg-info names,
tmp age, generated dirs under tracked example trees — and report drift
the way `fr_board.py` reports FR drift? The boundary inventory that
`workspace_is_not_boundary` prescribes before destructive ops could run
continuously instead of being remembered at the moment of danger.
