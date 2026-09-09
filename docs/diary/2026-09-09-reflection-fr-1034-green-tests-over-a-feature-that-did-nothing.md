# Reflection: green tests over a feature that did nothing — FR-1034

**Arc.** A 150-file census classified correctly on a cheap model for $0.04,
then lost its brief to `429 output token limit exceeded`. Root cause was not a
flaky provider: the map and synthesis stages read the same
`{state.provider}`/`{state.model}`, so one knob served two jobs with opposite
shapes. FR-1034 gave the synthesis call its own pair. Approved with three
revisions, enforced through the authoring route, and then found broken by the
demo run after twenty-three unit tests had gone green.

## What the raw record says

- **The feature did nothing, and every test passed.** Census python tools
  return `{state_key: value}` — `reduce_ledger` returns `{"ledger": ...}`,
  `prepare_brief_input` returns `{"brief_input": ...}`. My resolver returned
  the bare `{"provider": ..., "model": ...}`. `brief_llm` was therefore never
  set, `{state.brief_llm.model}` resolved to nothing, and the LLM node
  **silently fell back to the graph defaults**. The log is unambiguous:
  `Creating LLM: anthropic/claude-haiku-4-5` on a run that asked for
  `claude-sonnet-5`. Exit code 0 on the stage. No warning anywhere.
- The tests were green because I wrote them against my belief about the
  contract, not against the contract. Eight of them asserted the wrong return
  shape and agreed with each other.
- The judgement had already caught two things I would otherwise have shipped:
  `tools.py` was at **exactly** 450 lines, so the proposed home for the
  resolver would have broken the ceiling; and `render_brief` stamps
  `run_meta["model"]` from `state.model`, so a working override would have
  written a brief produced by one model and labelled with another.
- A false citation of mine survived my own review and died in the judgement: I
  claimed no default mechanism exists, citing
  `yamlgraph/compile/state_builder.py`. **That file does not exist.** My
  evidence was an empty grep on a wrong path, read as absence of a feature
  rather than absence of a file. The conclusion happened to hold, for a reason
  I had not found (`total=False` in `yamlgraph/models/state_builder.py`).
- `capabilities/` is `-r--r--r--` on main — 245 of 251 files — and
  `main_write.py` fences `chmod` against governed roots precisely so an agent
  cannot unlock it. The Claude Code hooks that would enforce that are not
  configured in this session, so nothing would have stopped me. The work moved
  to a worktree.

## The trap

**`green_over_a_dead_wire`.** Unit tests written by the author of the change
encode the author's model of the interface. When that model is wrong, the tests
do not fail — they agree. Coverage rises, the requirement looks witnessed, and
the feature is inert. The defect is not in any component: the resolver was
correct, the graph was correct, the node wiring was correct. Only the *shape of
the value passed between them* was wrong, and no component owned that shape.

This is `composition_bug` with a specific and nastier property: **the failure
mode was a silent fallback**. The LLM node, finding an unresolvable template,
used the graph defaults instead of raising. So the composition error could not
announce itself even in principle — it produced a plausible successful run with
the wrong model, which is `plausible_wrong_answer` at the wiring layer.

The tell was available and I did not read it. The run log names the model on
every LLM construction. One line — `Creating LLM: anthropic/claude-haiku-4-5` —
falsifies the whole feature, and it was printed the first time I ran the demo.
`read_raw_output_first` applies to a run log exactly as it applies to a model's
output.

## Heuristic

**A feature whose only witness is a test the feature's author wrote against an
interface they did not read is unwitnessed.** For any value crossing a boundary
owned by neither side — a tool's return shape, a node's state key, a template's
resolution target — the witness must be an execution that fails when the value
does not arrive. Not a unit test of the producer, and not a unit test of the
consumer: a run.

Two mechanical consequences:

1. **Read one existing implementation of the contract before writing a new
   one.** Three sibling tools returned `{state_key: value}` in the same file I
   was editing. One `grep -n 'return {"'` would have shown the convention and
   cost five seconds. I inferred the contract from the parameter name instead.
2. **A silent fallback turns a composition bug into a wrong answer.** Where a
   template cannot resolve, the honest behaviour is to raise, not to use a
   default. The default is what made this invisible; without it, the first demo
   run would have failed loudly at the right node instead of three nodes later
   with a misleading message about `brief_llm`.

**Seed:** the LLM node resolves `{state.x.y}` against state and, on failure,
falls back to the graph defaults without a warning. That is the mechanism that
converted a wiring error into a silently wrong model choice, and nothing in the
repository currently detects it. Should an unresolvable node-level
`provider`/`model` template raise instead of defaulting — and how many other
graphs are quietly running on defaults they did not ask for? A one-line grep
for `{state.` in node selection fields across `graphs/` and `examples/` would
size the question before any FR.
