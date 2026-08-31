# The Plan That Was Rewritten Eight Times Before a Line of Code

**Date:** 2026-08-31
**Arc:** docs/plan-web-toolkit.md revs 1–8 (PRs #524–#532) + FR-936

## What happened

A web-toolkit plan went through eight full revisions, each a separate
PR-merge cycle, each triggered by an operator correction averaging a few
words: "whats the value added", "fold", "check the sibling repos", "what
does langgraph give natively", "audit the map node". No code was written.
The final revision extracted FR-936 — a hardening FR for the *existing*
map node — meaning roughly half of the flagship component (D, resumable
map) turned out to be fixing code we already had.

## Traps encountered

- **growth_as_default, caught early for once**: rev 1 proposed four new
  components. The value audit (rev 6) and sibling-repo evidence (rev 7)
  reordered them by named consumers; the LangGraph-native research (rev 8)
  then shrank D from "new primitive" to "extend map node + one FR of
  hardening". Each research pass was subtractive. The plan got *smaller*
  as it got better — six of eight revisions removed or demoted scope.
- **does_the_platform_already_do_this fired late but decisively**: `@task`
  checkpointing, `CachePolicy`, Send pending-writes, and `durability`
  modes covered four of D's five requirements natively. One docs-fetch
  session eliminated most of a proposed component. The question should
  have fired at rev 1, not rev 8 — it was in the canon the whole time.
- **read_the_raw_code_before_planning_around_it**: the map-node audit
  (one read of map_compiler.py) found silent truncation and full-state
  Send payloads — defects that would have sabotaged D regardless of how
  well D was designed. Planning a durability layer on top of an unaudited
  fan-out is `downstream_fix` at the architecture scale: the boundary to
  normalize was the existing node, not a new wrapper.

## Heuristic

A plan for building on component X must begin with an audit of X against
its platform's canonical pattern. The audit is cheaper than any design
work it invalidates, and its findings become the prerequisite FR — the
plan's first sequencing row wrote itself (FR-936, size S, no deps).

Second heuristic, on process: eight PR cycles for one document is the
merge-acrobatics tax the operator named as the primary handicap. The
plan-as-conversation-artifact pattern works, but each 5-word steer cost a
full worktree→PR→admin-merge round. A plan under active revision may
belong in a draft PR that accumulates pushes and merges once, when the
operator says fold-and-freeze.

**Seed:** Could `does_the_platform_already_do_this` be mechanized the way
`read_raw_output_first` was — a plan-gate that withholds any "new
primitive" section until the FR cites the platform docs' answer for each
requirement it claims is unmet?
