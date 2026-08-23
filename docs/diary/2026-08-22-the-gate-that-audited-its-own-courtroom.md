# 2026-08-22: The Gate That Audited Its Own Courtroom

## Context

Enforcing FR-853 — six description-only metadata edits, an instructions
entry, a diary cross-reference, one witness test. Estimated effort: the
smallest FR of the week. Actual: the demo-gate turned a cosmetic change
into a two-defect excavation.

## What Happened

The demo-proof gate (FR-206/FR-325) demanded live runs of all six demos
whose directories my description edits touched. The reflex was to argue
scope: "description edits can't change behavior; the gate is noise
here." That reflex is `infrastructure_self_exempt` wearing an
efficiency costume. I ran the demos.

Two real defects fell out of runs a scope argument would have skipped:

1. **five-whys leaked its placeholder.** The prompts mixed bare
   `{problem}` with Jinja2 blocks; Jinja2 auto-detection rendered the
   placeholder literally, so the model answered "Problem statement not
   provided" — with exit 0 and a well-formed summary. A textbook
   `plausible_wrong_answer`: every shape check passed, the substance
   was a five-why analysis of a problem nobody stated.
2. **race node emitted no admissible success evidence.** The FR-325
   gate requires a success marker; llm and control nodes log it, the
   race node never did. A race-only demo was structurally incapable of
   proving its own success — the gate's evidence vocabulary and the
   node's logging vocabulary had never been reconciled.

Both fixed TDD (RED 33029143 → prompts via the governed authoring
route; RED 44ae783b → one logging line in race_node.py).

## The Trap Observed: interleaved REDs deadlock the hook

With two RED tests committed and their GREEN files split across two
pending commits, the full-suite pre-commit hook entered a deadlock:
each commit's hook stashed the *other* change's unstaged GREEN files
and failed on the other's RED test. Resolution: SKIP=pytest on the
intermediate commits, full suite as the **terminal witness** on the
final commit of the chain. The Scripture sanctions SKIP=pytest for RED
commits; the generalization is: in a multi-commit chain with
cross-cutting REDs, the suite gate belongs on the chain's last link,
and the chain must not be left unpushed mid-way.

## one_session_one_repo, strike again

A foreign untracked diary file (another session's output, dated
tomorrow) was staged concurrently and swept into my `--only` commit —
`--only` limits the *pathspec*, but a hooks-vs-index race still let it
in. Caught by `git show --stat` audit (the ritual held), removed by
soft reset before push. The audit-after-commit step is not ceremony;
it is the only step that fired.

## Insight

A gate that seems disproportionate to the change is the gate doing its
job: the demo-gate's value realized here was not "proof the demo still
runs" but **forced observation** — the same mechanism as
`read_raw_output_first`. Running the demo IS reading the raw output.
The five-whys bug had been sitting in a committed, previously-"proven"
demo; only a forced fresh run against fresh eyes exposed it. Gates that
force execution find bugs that gates checking diffs never will.

**Heuristic:** when a substance gate blocks a "trivially safe" change,
the cheap move is compliance, not argument — the gate's cost is minutes
and its yield this time was two shipped defects.

**Seed:** The race-node marker bug generalizes: which other node types
(map? subgraph? a2a?) emit no FR-325-recognized success evidence? A
one-off audit — grep each node factory for the success log line, cross
with the gate's marker regex — would either close the class or prove
race was the last member. And inversely: should the gate's marker
vocabulary be a shared constant the node factories import, so the
contract is structural instead of coincidental?
