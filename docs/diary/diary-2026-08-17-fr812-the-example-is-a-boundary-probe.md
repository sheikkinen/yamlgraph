# FR-812: The Example Is a Boundary Probe

**Date:** 2026-08-17
**Context:** Enforcing FR-812 (Discord `/hello` slash-command example) in a
session sharing the repo with a live FR-811 session.

## What happened

The judge earned its fee before enforcement started: FR-812's Related section
cited `yamlgraph/executor_async_run.py`, a file that existed when the FR was
authored in this very session — and was moved to
`yamlgraph/observability/async_run.py` by FR-811 *in a parallel session hours
later*. My context window held the stale truth; the judge, reading the tree
fresh, held the current one. `recent_changes_blindness` usually names a
regression trap; here it fired on an FR citation, and the independent-judge
route (never judge in the author's session) is what caught it — the author's
context was precisely the thing that was wrong.

Enforcement then hit the shared-index hazard head-on: REQ-YG-600 required
regenerating ARCHITECTURE.md's generated capabilities section, and
ARCHITECTURE.md carried FR-811's uncommitted hunks. The cure was surgical:
regenerate, split the diff into hunks, `git apply --cached` only the
CAP-239/REQ-YG-600 hunks, and commit the *index* — never `git commit --
<path>`, which snapshots the working tree and would have swept the foreign
work into my commit under my message (the exact `one_session_one_repo`
incident class, avoided by one flag's difference in semantics).

The RED commit also taught a sequencing rule: a `@pytest.mark.req` test cannot
be committed before its registry entry exists — `req-coverage-strict` blocks
the condemning test itself. The registry entry is declarative (spec, not
implementation), so it belongs *with* RED, not GREEN. TDD in a
traceability-gated repo is Red-Green-Refactor where Red includes the
requirement's birth certificate.

## Heuristic

When two sessions share a repo and a generated file must change, the unit of
staging is the hunk, not the file: regenerate → split hunks by ownership
marker (my CAP id) → `git apply --cached` mine → commit the index bare.
And: the req registry entry ships in the RED commit — the gate is right that
an unregistered condemning test is an orphan.

**Seed:** `now.py` shows live sessions and staged files, but the collision
that almost happened here was *unstaged* working-tree overlap on a generated
file. Should the interleave tripwire also flag "two sessions have uncommitted
edits under the same generated artifact" — a `git diff --name-only` cross-check
against sibling sessions' touched files?
