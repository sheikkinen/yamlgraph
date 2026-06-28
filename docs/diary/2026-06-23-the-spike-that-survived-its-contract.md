# 2026-06-23 — The spike that survived its own contract

## Context

Enforced FR-570: a falsifiable L4 spike asking whether a Haiku-class model can
classify prose beat glosses into a 16-kind Propp alphabet. The plan had been
written three times (v3→v4→v5) without a single running line. The spike's job
was to produce one number.

It produced **28/35 (0.80)** — a GO, optimistic, pending a blind-corpus re-test.

## The traps I walked into

### 1. The frozen spec lied about the module boundary (module_structure)

The Judgement froze a directory layout: graph in `graphs/`, validator in
`nodes/tools.py`, registered with `path: examples/plot_modeller/nodes/tools.py`.
It compiled cleanly in my head and passed lint. Then `compile_graph` raised:

```
Python tool path not found: .../graphs/examples/plot_modeller/nodes/tools.py
```

The `path:` resolver anchors at the graph's **own directory** and forbids escape
(a security boundary in `_resolve_python_tool_path`). A sibling-of-`graphs/`
tool is unreachable by path. The spec's structure was sound; its *wiring
mechanism* was wrong, and neither the author nor the judge caught it because
**lint validates structure, not tool resolution.** The fix was the established
convention I'd have found by reading one more example: `module:` dotted imports
(`examples.diary_digest.nodes.*`) route through Python's import system and
sidestep the filesystem boundary entirely.

Heuristic: *a frozen spec is frozen at the layer it was reviewed. The judge
reviewed the schema and the data flow; the module-resolution boundary was below
the review's resolution.* Verify tool wiring by compiling, not by linting.

### 2. Silencing a warning broke the build (composition_bug)

Lint warned W012: the `validate` node is in a cycle without a `loop_limits`
entry. I "fixed" it by adding `validate` to `loop_limits`/`loop_exits`. That
wrapped the conditional router's `END` target and LangGraph refused to compile:
`At 'validate' node ... unknown target 'END'`. Each piece was individually
reasonable — the warning is real, the loop_exit syntax is valid — but the
*composition* of a conditional router with a loop-exit wrapper on the same node
produced an unmapped sentinel. The cure was to trust the topology: the loop
re-enters `classify`, so the bound belongs on `classify`. W012 on `validate` is
an accepted advisory. **A warning is advice, not a defect; obeying it blindly
can manufacture the defect it never warned about.**

### 3. The RED very nearly didn't happen

The J1 fix was already in the spec — the validator I first wrote was correct. To
honor the RED→GREEN proof trail I had to *un-write* the fix: revert to the
pre-guard validator, watch three tests fail, commit RED with `SKIP=pytest`, then
restore the guard. The temptation was to skip the theatre and commit the working
code. But the diary's own `test_before_reading` and Commandment 7 are explicit:
the condemning test must exist as RED in the log, or the fix is a hypothesis. The
git log now shows `test: RED J1 crash` → `fix: GREEN J1 guard`. The trail is the
proof.

## What worked

- **The corpus ceiling was declared, not hidden (J2).** Every eval file is
  stamped `self-derived (upper-bound)`. The 0.80 is honest about being an upper
  bound — a KILL here would have been doubly damning, a GO is necessary-not-
  sufficient. The verdict says so out loud.
- **The confusion analysis carried the verdict, not the percentage (J3).** The 7
  errors weren't in the vocabulary pairs the prompt warns about. They clustered
  around cause-vs-outcome (`death → villainy`, `liquidation → victory`). That
  reframes the next move from "shrink the vocabulary" to "add one disambiguation
  note" — a conclusion the bare 0.80 could never have produced.

## Seed

The model confused *outcomes* with their *causes* (a death read as the villainy
that caused it). The 16-kind alphabet encodes events, but plot kinds form a
**causal graph** — `villainy` enables `lack`, `struggle` enables `victory`,
`victory` enables `liquidation`. If L4 received each gloss *with its predecessor
already classified*, would the cause/outcome confusions vanish? Is kind
classification actually a sequence-labeling problem wearing a per-item
classification costume — and if so, does the layered pipeline have the dependency
edges to express that, or did v5 freeze the wrong granularity?
