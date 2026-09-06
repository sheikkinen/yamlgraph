# The Smoke That Was Already Out

**Date:** 2026-09-06
**FR:** FR-1011 relocate the live parts out of `.chaplain/` (Phase 1 of FR-1010)
**Session:** Claude Code on the Windows host, same session that enforced FR-1014; not the FR author's judge session

## What happened

The relocation itself was the easy part and the route made it honest:
three briefs, three adapter runs, fourteen `R100` renames and a handful
of `R095`–`R098` where the brief asked for path-only comment edits. The
adapter did what the brief said and nothing else — I read every diff
line to be sure, because the doctrine says an agent editing enforcement
or graph artifacts is adversarial input, and that includes the one I
launched.

What cost the day was validation, and three separate times the
validation was wrong about something other than the code.

**The frozen smoke command could not have passed.** FR-1011 froze
`yamlgraph graph run graphs/fr_triage/graph.yaml --var fr_path=<copy of
FR-1011>`. The triage graph appends to *Proposed* FRs only; FR-1011 is
Judged. The command was written by reading the graph's purpose, not its
first guard clause. A witness command is code — it needs the same read
against the source as any other line.

**The missing dependency lived in two interpreters.** `world_distill`
needs `feedparser`, a declared `digest` extra nobody had installed. I
installed it into `.venv`; the adapter's `yamlgraph` is the Python 3.13
global install, so the second run was blocked by the same error. The
environment has as many boundaries as it has interpreters, and "I
installed it" is a claim about one of them.

**The philosopher smoke was already out.** Run 3 failed inside the
graph: `Object of type CopilotResult is not JSON serializable`. The
reflex was to suspect the relocation — the proxy path, the `with_name`
edit, something about `prompts_relative`. I ran the identical command
on the untouched `main` checkout from the old `.chaplain/graphs/` path.
Identical failure, same node, same message. The graph FR-1010 called
"dormant" is not dormant; it is broken, and has been since before anyone
looked. The relocation moved a dead thing faithfully.

## The trap

**Attributing a witness failure to the change because the witness ran
after the change.** Three instances in one FR, none of them about the
relocation: a command that could never pass, a dependency the runner
did not have, a graph that was already failing. Each time the cheapest
move was the one FR-1014's diary already named — run the same
instrument on the unchanged tree — but this FR added a sharper form:
*a smoke test of a dormant component is a discovery, not a regression
check.* Nobody had run the philosopher in months. The first run after
the move was the first run, period. Its failure told me about the
graph, not about the move, and the baseline proved it in eight minutes.

The second lesson is about frozen commands. FR-1011 R-6 asked for
"exact commands" in the acceptance criteria, and that was right — but
exact is not the same as correct. An exact command that was never
executed before it was frozen is a prediction wearing the costume of a
specification. The `Blocked validation` section of the adapter report
is where predictions go to be corrected, and it did its job: three
briefs, each narrower than the last, each honest about what the
previous one got wrong.

## Heuristic

Before freezing a witness command in an FR, run it once — or at
minimum read the guard clauses of the thing it invokes. And when a
smoke fails on a component nobody has run recently, run it on the
untouched tree first: if it fails there too, you have found a defect,
not caused one, and the FR that owns the defect is not the one you are
enforcing.

**Seed:** FR-1010 classified `philosopher` as dormant on the evidence
that nothing called it. It is broken, which no static inventory could
see. Should the Phase 2 census mark each relocated or retained graph
with a *last successful run* date pulled from LangSmith or from the
`tmp/` smoke logs, so that "dormant" and "dead" stop sharing a row?
