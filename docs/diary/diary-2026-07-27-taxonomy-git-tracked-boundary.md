# The taxonomy that failed only where it mattered

**Date:** 2026-07-27
**FR:** FR-763 — example taxonomy scanner must scope discovery to the
git-tracked tree
**Context:** Enforcement of the fix surfaced by the FR-759–762
review-cycle forensic. A `--check` gate that stayed green through four
review rounds on PR #464 turned red the instant it ran on a machine with
local generator outputs.

## The trap: `workspace_is_not_boundary`, in its purest form

`scripts/example_taxonomy_scan.py` discovered example roots with
`os.walk(examples/)`. The filesystem was treated as the source of truth
for "what example roots exist in the repository." But the contract
(FR-762) says *in the repository* — and the repository is the git-tracked
set, not the working tree. The two sets diverge exactly where a developer
has run the generator: `examples/yamlgraph_gen/outputs/*`, gitignored,
each holding a `graph.yaml`, each admitted as a phantom root. 86 phantom
insertions on a dirty checkout; zero on a clean one.

The defect is invisible from inside a clean review worktree. Four rounds
of human-plus-graph review never saw it because review worktrees are
always clean checkouts. The bug lived precisely in the gap between the
reviewer's environment and the developer's — a gap no amount of reading
the diff can close. It is the boundary lesson stated as an environment:
**editor/CI visibility is not repository membership.**

## The cure: ask git, don't model git

The judgement's GATE conditions pre-empted the three tempting wrong
turns, and each was worth its ink:

- **C-1 (normalize at discovery, not post-classification):** the lazy fix
  is to build the full taxonomy and then filter out ignored rows. That
  leaves the poison in the generator — regeneration still *writes*
  phantom rows, it just hides them afterward. Normalizing at the walk
  means the ignored directory never becomes a candidate at all.
- **C-2 (git is the parser):** the seductive wrong turn is to read
  `.gitignore` in Python. Negations, nested ignore files, the fourth
  special case — `regex_fourth_exclusion` wearing a `.gitignore` hat.
  One `git ls-files -z` sidesteps the entire reimplementation.
- **C-3 (fail loud inside a work tree):** a fallback that swallows *all*
  git errors would re-hide the bug the moment git hiccuped. The fallback
  is narrow — "not a work tree" or "git absent" — and every other
  git failure raises.

The implementation cost was threading a `tracked: set[Path] | None`
through nine functions. That breadth is itself a signal: the filesystem
had leaked into every marker check and every import scan. The boundary
wasn't one function; it was a *seam* running through the whole module,
and normalizing it meant naming every place external data entered.

## What made this cheap

Byte-identical verification (AC-05) was the whole proof in one line:
`git diff examples/dependency-taxonomy.yaml` empty after regeneration on
the dirty machine. The committed artifact was generated on a clean
checkout; if my tracked-scoping were even slightly wrong, the diff would
be non-empty. The artifact *is* the test — I did not have to trust the
five unit tests alone; the real repo's own committed output was the
oracle. `read_raw_output_first`, inverted: the raw artifact was already
sitting there as ground truth, and one `diff` ended the investigation.

## Seed

The `--check` gate is not yet wired into pre-commit or CI (the judgement
explicitly deferred that as separate human-reviewed scope). So the very
false-stale failure this FR fixes can only bite a developer who *manually*
runs the scanner — and the phantom-row poison can still be committed by
anyone who regenerates and `git add`s the result without noticing. **If a
gate's whole value is catching drift, but nothing forces it to run before
merge, is it a gate or a footnote?** When FR-763's successor proposes the
pre-commit hook, the pre-mortem question is already written: it shipped,
and a developer regenerated on a dirty tree, committed the byte-identical
output, and — what still broke? (Answer: nothing, now. That is the test
of whether this fix was complete or merely local.)
