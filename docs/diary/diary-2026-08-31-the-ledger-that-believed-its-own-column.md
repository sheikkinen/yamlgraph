# The Ledger That Believed Its Own Column

**Date:** 2026-08-31
**FR:** FR-940 — census judgement normalization + selectable model
**Trap:** gate_checks_shape_not_substance, met twice in one arc

## What happened

The spark census returned 19/106 rows whose `judgement` column carried
the model's whole three-part answer — prose in an enum's chair. The
reducer checked `min_length=1` and error markers: presence, not
substance. The fix was the Scripture's oldest cure applied one column
deep: normalize at the boundary where external data enters. The 19
witnessed strings became a committed fixture; every one repaired to a
clean vocabulary label under a deterministic, LLM-free algorithm —
zero prompt patches, per `two_strike_split`.

## The second trap: the pin that wasn't a variable

The operator asked "is census pinned to mercury-2?" — it was pinned to
haiku, three times, in YAML. Making the model a caller variable
exposed a false belief I held for an hour: that `{state.model}` in
node config already worked, because the storyboard graphs contain that
exact string. Reading the callsite showed it was a *prompt variable*,
not node config — syntactic similarity is not semantic equivalence
(`false_duplicate`). The enablement was a 30-line core change, and the
FR had to be amended mid-enforcement to record the deviation: the
judge's C-5 fence said "no core changes," the operator's "include in
940" overrode it, and the honest move was writing the collision into
the FR rather than smuggling the change past it.

## The third lesson: the interlocked RED

Two RED test sets (census + core) committed under SKIP=pytest
interlock: any later commit that stages only one GREEN half fails the
pytest hook, because pre-commit stashes the unstaged half away. The
stash is not an inconvenience — it is the hook proving the commit, as
staged, is broken. The cure was one combined GREEN commit. Corollary
for lanes: the worktree `.venv` symlinks to main's venv, so hook
pytest needs `PYTHONPATH=$PWD` or it silently imports the main
checkout's modules — an interpreter-provenance failure the
`one_session_one_repo` litany already names for measurement runs, now
witnessed inside pre-commit itself.

## Heuristic

A RED committed under SKIP is a debt with a lien on every subsequent
commit in the lane; plan the GREEN commit boundary at RED-commit time,
not when the hook fires.

**Seed:** the demoted rows now carry frozen reasons
(`unparseable judgement shape`, `label not in vocabulary`). A census
of the demotions themselves — which rubrics produce which failure
class at which rate — would turn the normalization layer into a
prompt-quality instrument. Is the demotion ledger the cheapest rubric
linter we never built?
