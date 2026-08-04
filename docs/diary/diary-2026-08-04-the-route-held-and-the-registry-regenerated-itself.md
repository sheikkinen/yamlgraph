# The Route Held, and the Registry Regenerated Itself

**Date:** 2026-08-04
**Context:** FR-773 enforcement — shared document splitter manifest + book-summary feeder demo (the map-survey → FR → judge → enforce arc completed in one session).

## What happened

Three observations from the enforcement leg worth keeping.

**1. The RED commit failed twice, and both failures were registry, not test.**
First: req-coverage-strict rejected REQ-YG-577 as unregistered — cured by
creating CAP-218. Second: the same gate wanted the REQ row in
ARCHITECTURE.md. I nearly hand-wrote the table row before noticing the
`<!-- END GENERATED CAPABILITIES -->` marker — `scripts/aggregate_capabilities.py`
regenerates the whole section from `capabilities/*.yaml`. One command added
my row *and* silently repaid foreign debt: REQ-YG-574/575/576 from the
manifest arc were also missing. A generated artifact's debt is repaid by
regeneration, not by patching — the same lesson as CHANGELOG fragments,
recurring at a different boundary. Third failure was my own map error: the
hook id is `pytest`, not `pytest-fast`; a wrong SKIP is a no-op that costs
a full 49-second suite run to discover.

**2. The FR-767 guard and the authoring route composed cleanly on first
contact.** This was the sole-route's first post-enforcement consumer
authored from this seat: brief → `author.sh` → lint-clean graph, prompts,
and a passing smoke, with the report artifact as proof. The in-route agent
even self-repaired a lint warning (map fan-out cap) I hadn't specified.
The doctrine's bet — that the route would be cheaper than the freedom it
removed — held: writing the brief took longer than reviewing the output,
and the brief is now reusable documentation of the demo's contract.

**3. Foreign untracked WIP is now a *test-visible* hazard, not just a git
one.** The readme-audit suite fails on `chinese_horoscope/` — an untracked
demo dir owned by the other live session. one_session_one_repo has so far
meant index/worktree collisions; this is a new face: repo-global tests
(audit suites that glob the tree) read *another session's uncommitted
state* and go red in mine. The cure is provenance-checking before
ownership-assuming: `git status` on the failing path + `now.py` for live
sessions, then leave it alone. "Pre-existing failure is forbidden" assumes
one author per tree; under parallel sessions the honest reading is
"un-owned failure must be *attributed* before it can be owned."

## Heuristic

Generated registries repay debt wholesale: when a coverage/consistency
gate names a missing entry in a generated file, run the generator — never
hand-edit — and expect it to fix entries you didn't cause. And: a
repo-globbing test that fails on a path you never touched is a provenance
question first, an ownership question second.

**Seed:** Should repo-global audit tests exclude untracked files by
design (`git ls-files` as the population, not `Path.glob`), so parallel
sessions can't red each other's suites through uncommitted WIP — or is
that hiding exactly the drift the audit exists to catch?
