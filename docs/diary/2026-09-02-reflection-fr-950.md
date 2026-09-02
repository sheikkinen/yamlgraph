# 2026-09-02 — Reflection FR-950: the anchor that drifts while the gate sleeps

## The arc

A routine "git pull, run tests" on the main checkout produced 5 red tests.
None was a product regression. Two were local residue (stale `__pycache__`
namespace ghost, venv not on PATH), one was the FR-889 lock working as
designed, and two were genuine main defects that had slipped through:
CAP-198's `fr:` attribution missing FR-950, and FR-950's own fork-capability
test breaking the interpreter on CPython 3.14.

## Traps encountered

**Gate checks shape, not lifetime.** The noqa-confession gate validates
file+line anchors — but only when the file containing the noqa is touched.
Editing lines *above* a confessed noqa in the same file, or editing the
confessed file from a *different* PR, silently drifts every anchor below the
edit. CONF-373 pointed at L288 while the noqa lived at L312; CONF-375 pointed
at L138 vs L141. The drift was created by FR-950's own merge — the gate that
guards confession accuracy cannot fire on the commits that invalidate it.
This is `gate_checks_shape_not_substance` with a temporal twist: the shape
was correct *at confession time* and decayed afterward.

**Simulating a platform by deleting an os attribute is a boundary lie.**
FR-950's test deleted `os.register_at_fork` to simulate Windows. On CPython
3.14 POSIX, stdlib `asyncio` and `random` call `os.register_at_fork` at
import behind an `os.fork` guard — so the deletion broke the interpreter,
not the seam under test. The real Windows boundary is `hasattr(os, 'fork')`
being false *everywhere consistently*; deleting one attribute creates a
chimera runtime no real platform exhibits. The cure applied: pre-import all
dependencies, then delete, so only yamlgraph's own import-time guard — the
actual seam — sees the absence.

**The docs-path merge skipped the matrix.** The CAP-198 attribution defect
merged through a path-filtered CI run that never executed
`test_no_req_collision_across_unrelated_frs`. A capability YAML edit is not
"docs" to the test suite even when it is "docs" to the path filter — the
path filter's taxonomy and the test suite's coverage domain are different
partitions of the same tree.

## Heuristics

- Line-number anchors in prose (confessions, judgements, FR citations) decay
  under every edit above them; a gate that validates them must run on every
  PR touching the *anchored* file, not just the *anchoring* one — or anchors
  should cite symbols, not lines.
- When a test simulates a platform by mutating the runtime, enumerate what
  else in the import universe consumes the mutated surface *on the current
  interpreter version* before trusting the simulation.

**Seed:** Could the noqa-confession gate re-validate ALL anchors repo-wide
on every PR (cheap: one grep pass), turning silent anchor decay into a
same-PR fix — and should judgement/FR line citations get the same treatment,
or should all three switch from line anchors to content anchors (quoted
snippet match) that survive reflow?
