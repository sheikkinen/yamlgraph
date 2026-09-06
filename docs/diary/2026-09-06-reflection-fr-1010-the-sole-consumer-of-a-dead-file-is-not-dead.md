# The Sole Consumer of a Dead File Is Not Dead

**Date:** 2026-09-06
**Trigger:** FR-1010 (chaplain archival plan) judged. Of nine required
revisions, five were factual errors in my inventory — each one a place where
I had followed a link one hop and stopped. PR #611.

## What I got wrong, and the single mechanism

| claim in my draft | what the judge found | how I had arrived at the claim |
|---|---|---|
| `scripts/finalize_merge.sh` is dead — delete it | live: CAP-38/REQ-YG-125, CAP-45/REQ-YG-144, its own test file | it was the *sole consumer* of `.chaplain/lib/finalize_lib.sh`, and the lib was in the dead directory |
| `.chaplain/id-registry.yaml` is dead — delete it | FR-970's judgement withholds deletion; FR-975 bootstraps from it; FR-980 owns the purge | the file was frozen since April; I grepped `capabilities/` but never `feature-requests/` for the path |
| subtree archive stays *runnable* | `start-system.sh:16` computes `PROJECT_ROOT=../..` | CAP-75 is called "portable chaplain"; I took the CAP name as the property |
| `mv .chaplain/inbox/* proposals/` in the PR | inbox is `.gitignore`d, absent from every worktree | I had *already found* this (`.gitignore:100`) and recorded it — then wrote GREEN commands from the worktree anyway |
| guard widening folded into the relocation FR | separate concern; enforcement infra needs its own human gate | it was two lines; the FR was already open |

Five different files, one mechanism: **a property inferred from an adjacent
node instead of read from the node itself.** Dead directory → its lib is dead
→ the lib's consumer is dead. Frozen file → dead. "Portable" in the CAP name
→ portable. Found-a-fact → moved on without letting it rewrite the plan.

The Scripture has `false_duplicate` ("syntactic similarity ≠ semantic
equivalence") and `plausible_wrong_answer`. This is their graph-traversal
form: *adjacency is not inheritance*. A file inside a dead directory is not
thereby dead; a consumer of a dead file is not thereby dead; a file named
"portable" is not thereby portable. Each node has its own CAP/REQ/test
witnesses, and the inventory must read them per node.

## Why the judge saw it and I did not

The judge did not know more than I did. It ran `grep finalize_merge.sh`
across `capabilities/` and found CAP-38. It read `start-system.sh:16`. It
grepped `id-registry` across `feature-requests/` and found three FRs from
three days earlier. Every check was one command I had the tools for and did
not run — because my inventory was *directional*: starting from `.chaplain/`
and walking outward, marking as I went. Walking outward from the dead node
propagates deadness. The judge started from each artifact I proposed to
delete and walked *inward* to its witnesses. Same graph, opposite direction,
opposite conclusion.

## Second finding: the phantom fixture

FR-767's guard witness parametrises over
`GOVERNED_CHAPLAIN = ".chaplain/graphs/pipeline.yaml"`. No such file has ever
existed; every real chaplain graph is `<name>/graph.yaml`, and the regex
matches only flat files. The test passed for fourteen months against a path
shaped like the regex rather than like the repository. `gate_checks_shape_not_substance`
has a test-fixture form: **a fixture shaped by the predicate under test
cannot fail the predicate.** Fixtures must be sampled from the tree
(`git ls-files`) or labelled synthetic; FR-1014 now does both.

## Third finding: the judge route's contract failure

`scripts/judge.sh` exited 65 "contract violated" on FR-1010 because the
graph wrote its artifact to `tmp/draft-judgement-copilot-FR-1010.md` (slug
truncated) while the wrapper expected the full slug. The judgement was
complete and correct. On FR-1014 and FR-1011 the same wrapper exited 0. One
run in three, the proof-of-judgement check failed for a filename reason.
Filed in FR-1010's judgement note, not fixed — but it is the same class as
the fixture: the check tests presence at an expected path, and presence is
what the model got wrong while the substance was right.

## Heuristic

**Read inward, not outward.** For every artifact a subtraction FR proposes to
delete, run three commands *before* writing the disposition:
`grep -l <path> capabilities/`, `grep -l <path> feature-requests/`,
`grep -rl <path> tests/`. Adjacency to a dead thing is not a witness. The
deletion list is the set of artifacts with *zero* live witnesses, not the
set reachable from the dead root.

**Seed:** the judge caught five of five because it walked inward. Could the
inward walk be the *prior-art hook's* default for any FR whose body contains
`git rm`, `delete`, or `retire` — surface every CAP/REQ/test/FR that names
each path in the FR — so the author sees the witness list before the judge
has to? The hook is noun-ranked today; deletion FRs need path-ranked.
