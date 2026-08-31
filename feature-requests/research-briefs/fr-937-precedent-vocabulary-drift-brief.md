# Problem brief: two halves of the research route disagree about what counts as an admission of no precedent

**Prior art:** `FR-896-research-route-precedent-traceability.md` froze the
precedent contract this brief re-enters and is the direct territory, described
as current state below rather than as unexamined precedent.
`FR-932-prior-art-retrieval-in-research-route.md` added the retrieval block and
the `none-retrieved` claim the reducer now accepts — also current state.
`FR-890-research-sole-route-closed-input-alternatives.md` established the closed
brief and the persona schema. `FR-933-retry-cannot-recover-deterministic-rejection.md`
concerns retry after a schema rejection, an adjacent failure of the same route
but a different mechanism — distinguished: the failure here is raised by a
python reducer, not by a validator, so no retry path applies.

## Problem statement

The research route's persona prompts and its reducer hold different beliefs
about what a persona may write in the `precedent` column when it has no
committed precedent to cite. Each half is internally consistent. The policy
connecting them is not, and the route dies.

All five persona prompts
(`examples/demos/research-route/prompts/{subtractionist,data_process_planner,os_infra_primitivist,yamlgraph_native_planner,librarian_structure}.yaml`)
carry the same paragraph:

> If the only support for the candidate is the problem brief itself, write the
> literal marker `brief-echo:` followed by what is being restated; the row is
> retained but excluded from scoring.

`examples/demos/research-route/nodes/research_tools.py` does the opposite: on
seeing that marker it raises, the graph exits non-zero, and
`tmp/draft-alternatives.md` is never written. Its docstring records the change
as deliberate — FR-896's demotion was removed because restating the brief as
its own precedent is not precedent, and its stated replacement is a bounded
`none-retrieved` claim, verifiable against the retrieval block the personas
were actually shown. The replacement landed in the reducer. It never reached
the prompts.

The asymmetry is total:

```
grep -l "brief-echo"     prompts/*.yaml  → 5 of 5 personas
grep -l "none-retrieved" prompts/*.yaml  → 0
```

`none-retrieved` is the only value the reducer accepts when retrieval comes
back empty, and no prompt tells any persona that the value exists. A persona
holding no precedent therefore has exactly one instruction available to it,
that instruction is sanctioned in writing by its own system prompt, and
obeying it terminates the run. The accepted escape is unreachable from the
prompt; the reachable one is fatal.

Two properties make this worse than a stale sentence.

It is not probabilistic. One persona out of five taking the instruction is
enough to fail the entire fan-out, and the other four passing does not help.

It is anti-correlated with the value of the run. Retrieval returns nothing
precisely when the subject is novel, and FR-932 recorded that filename-noun
IDF ranking "finds prior art that shares vocabulary and misses prior art that
shares a problem" — so empty retrieval is ordinary, not exceptional. The route
is least able to complete exactly where research is most needed, and most
reliable on subjects the corpus already covers, where it is least needed.

## Classification

judgement/analysis/generation — the question is which half holds the correct
contract and how two artifacts written in different languages are kept in
agreement afterwards. Nothing needs to be quantified and no latency budget
applies.

## Constraints

- `examples/demos/research-route/prompts/*.yaml` and `graph.yaml` are governed
  graph artifacts. Under FR-767 the sole authoring route is
  `scripts/author.sh`, mechanically enforced by the PreToolUse sentinel; they
  cannot be hand-edited.
- FR-896's contract must survive: precedent is rejected, never truncated, and
  a fabricated identifier fails the whole run.
- FR-932's `none-retrieved` claim must stay bounded — a persona may claim it
  only when the retrieval block it was shown was actually empty, verified by
  the reducer against that same block.
- The reducer's failure is raised from a python node, so it is not a
  `ValidationError` and FR-933's feedback retry does not and should not apply.
- The route is the sole research route for the whole repository; any change to
  it changes the input to every subsequent judgement.
- Whatever is chosen must survive the next change to either half. Two artifacts
  in two languages already drifted once without anyone noticing.

## Witnessed incidents

- 2026-08-31: brief
  `feature-requests/research-briefs/operator-coffee-physical-actuation-brief.md`,
  a subject with no committed precedent in the FR corpus. Four personas
  produced valid rows. One wrote `brief-echo: agent knows when the wait is and
  creates it deliberately; operator supervision cost is attention spent on
  windows where no decision is required`. The reducer raised, the graph exited
  1, no artifact was written. Log: `logs/research-coffee.log`.
- Same brief, second run: byte-identical failure, same persona, same string.
  Deterministic at `temperature: 0.0`, so it is not a sampling accident and
  re-running is not a workaround.
- The drift was invisible for the life of the contract change because no
  earlier brief in the route's history had produced an empty retrieval block
  and then reached the reducer. The route had never been exercised on a novel
  subject.
- Related and recorded on the way in: `scripts/research_preflight.py` matches
  the classification enum by naive substring, so a sentence disclaiming a class
  counts as claiming it; and a brief missing a required heading is reported as
  `remove solution-shaped sections`, naming the opposite of the actual fault.
  Both cost a failed run before the route was even entered.

## What is not known

- Which half is authoritative: whether a demoted-but-retained row is still
  wanted, or whether it was genuinely retired and only the prompts lag.
- Whether personas would use `none-retrieved` correctly if told about it, or
  whether it becomes a default escape that hollows out the precedent column.
- Whether the agreement between prompt vocabulary and reducer vocabulary can be
  checked mechanically, given the prompts are prose and the reducer is code.
- Whether other prompt/validator pairs in this route have drifted the same way
  and are simply waiting for their first triggering input.
- Whether an empty retrieval block should reach the personas at all, or whether
  the route should refuse earlier with a clearer fault.

## What a useful answer looks like

A disposition that names which half is authoritative and what makes the other
follow, with the cost and the boundary crossing of each direction stated.
Directions that only improve the error message must be dispositioned as such
rather than counted as fixes. The answer must say what mechanically prevents
the same drift from recurring, and must name its first consumer and the
concrete moment it fires.
