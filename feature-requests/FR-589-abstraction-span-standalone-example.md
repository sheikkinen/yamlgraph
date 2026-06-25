# Feature Request: FR-589 Abstraction-span — standalone YAMLGraph example

**Priority:** MEDIUM
**Type:** Feature (example / research validation)
**Status:** Judged — Authority GRANTED (2026-06-24)
**Effort:** ~1 day (spike-gated; the separation study may KILL the metric)
**Requested:** 2026-06-24
**Supersedes:** FR-588 (rejected — fought the framework with a standalone Python spike)
**Complements:** FR-586 (static W026 prompt-monolith linter)
**Inherits:** the `linter-llm-free` import-linter contract enforced under FR-588 (kept)
**Origin:** `docs/diary/diary-2026-06-24-the-brief-i-would-never-give-a-subagent.md` (Seed)

## Summary

Rebuild the LLM-scored **abstraction-span** metric — "how many *distinct kinds*
of cognitive operation does a prompt ask for in one output?" — the way YAMLGraph
is meant to be built: as a **self-contained example** (`graph.yaml` + a prompt +
two Python tools), runnable with `yamlgraph graph run`, not as a Python script
that imports `execute_prompt`. FR-588 reached for a hand-written spike harness;
that fights the framework's own thesis (60–80% of a workflow belongs in YAML). The
same validation discipline survives intact: the example is **spike-gated** on a
separation test, and KILLs the metric if it cannot reproduce the known
monolith/clean labels.

The metric stays a standalone, on-demand tool. It is **not** wired into the linter
— that boundary is closed permanently and enforced by the `linter-llm-free`
import-linter contract (committed under FR-588, retained here).

## Value statement

A graph author can run one command (`yamlgraph graph run
examples/abstraction_span/graph.yaml`) to get a cheap LLM estimate of a prompt's
abstraction-span — **but only after** the example's own separation gate proves the
score reproduces the existing complexity labels (anchored by the one prompt with a
measured L5 failure rate), so the number carries evidence, not a plausible guess.
And the example itself demonstrates the YAMLGraph map-node + python-tool pattern.

## Judgement (2026-06-24)

**Verdict: Authority GRANTED.** The FR is clear, minimal, and internally
consistent. It corrects FR-588's only defect — a hand-rolled Python spike that
fought the framework's own thesis — by expressing the orchestration in `graph.yaml`
and leaving only file I/O and the deterministic verdict in Python. The hard-won
content FR-588's judgement produced survives intact: the **reproduce-the-hand-labels**
ground-truth honesty (not "predict failure"), the **separation** gate (not Spearman
ρ at n=7), the one-iteration KILL discipline, and the scorer made to pass its own
metric. The `linter-llm-free` import-linter contract is correctly inherited, and the
"no linter integration, permanently" boundary is restated and enforced. This is
aligned rebuilding, not gold-plating: the cost is unchanged (~1 day), the validation
discipline is identical, and the artifact doubles as a `map` + `python-tool`
demonstration of the framework.

**Red Hat — is the pain real?** Yes, conditionally. Static W026 (FR-586) is
schema-shape-blind to the prose monolith; line count does not separate the corpus;
only a semantic span metric ranks by *kind of work*. The FR is honest that the metric
may be noise — and the spike-gate KILLs it on separation failure, keeping the example
as a documented null result. Building a ~1-day spike to settle whether the metric
separates is justified; shipping the score unvalidated would not be.

**Conventions verified against the codebase.** The `state:` block (both
`key: {type, description}` and shorthand forms), the `tools:` block
(`type: python`/`module`/`function`), `type: python` nodes, and `type: map`
(`over`/`as`/`node`/`collect`) all exist as used (`examples/yamlgraph_gen/graph.yaml`,
`examples/plot_modeller/graphs/assign_pre_eff.yaml`, `examples/demos/map/graph.yaml`).

**Corrections required before enforce (do not widen scope):**

1. **Name the REQ-YG ID (blocking — ADR-001 + `changelog-req-gate`).** The FR omits
   the requirement the `separation_verdict` unit test will carry. The verdict logic
   and the map+python-tool orchestration are exercises of *existing* capabilities
   (node execution / tool integration / subgraph-map), not a new one — pin the test
   to an existing `REQ-YG-XXX` from CAP-03 / CAP-05 / CAP-11 rather than minting a
   new CAP. The `feat` changelog fragment's `req:` must reference that same valid ID,
   or the gate blocks the PR.

2. **Validate the map-item nested access first (cheapest-bug rule).** The proposal
   binds `as: item` and reads `{state.item.text}` — a *dict-field* access on the loop
   variable, where the `map` demo only passes the whole item (`{state.idea}`, a
   string). Confirm the map node resolves `{state.item.text}` before building the
   corpus/prompt; if it does not, restructure `load_corpus`'s output (e.g. pass the
   text directly as the map element) rather than patching downstream. Verify with
   `yamlgraph graph lint` then a `--full` smoke run, reading the
   `Creating LLM: anthropic/claude-haiku-4-5` line as Gate-1 evidence.

3. **Pin the `type: python` node's `state_key` contract.** The granted graph writes
   `state_key: corpus`/`verdict` on python nodes; the reference python node in
   `yamlgraph_gen` relies on the tool's returned dict merging into state. Confirm
   which mechanism the example uses and keep `load_corpus`/`separation_verdict`
   return shapes consistent with it — do not invent a new node contract.

**Frozen scope:** the standalone example exactly as drawn (`graph.yaml` + one inline-
schema scorer prompt + `load_corpus` + `separation_verdict` + manifest-by-path + the
verdict unit test + README + diary). Gate 1 decides GO/KILL. One scorer iteration
only. No linter integration, no build-gating on the score, no prompt-body
duplication, no auto-split. The corrections above are clarifications within this
scope, not additions to it.

## Problem

Two problems, one inherited from FR-588 and one that caused its rejection.

1. **The metric still matters (inherited).** Static W026 (FR-586) keys on declared
   output fields; it is blind to the *prose monolith* — a prompt with a narrow
   schema that nonetheless fuses many kinds of cognitive operation in its
   instructions. Line count does not separate the corpus either (`assign_causality`
   61 lines = `extract_goals` 61; clean `extract_glosses` 58 < monolith
   `extract_agents` 66). A semantic span metric is the only thing that could rank by
   *kind of work*, not size. And an LLM-judged metric is untrusted until validated
   (Scripture: *a plausible wrong answer is harder to catch than a crash*).

2. **FR-588 built it wrong (rejection cause).** FR-588's Stage 2 was a standalone
   `spike_*.py` importing `execute_prompt` and hand-rolling the map loop, the
   structured-output call, and the verdict. That is the anti-pattern YAMLGraph
   exists to remove: orchestration (map over a corpus, call an LLM per item, collect
   results) belongs in `graph.yaml`; only the file I/O and the deterministic verdict
   belong in Python tools. Rebuilding as an example makes the work *also* a
   demonstration of the framework, and keeps the LLM call out of any gate.

## Proposed solution

A standalone example, graph-native, following the plot_modeller/`map`-demo
convention.

```
examples/abstraction_span/
  __init__.py
  graph.yaml              # load → map(score) → verdict
  prompts/
    abstraction_span.yaml # the scorer: single-judgement, inline schema
  nodes/
    __init__.py
    tools.py              # load_corpus(), separation_verdict()
  corpus/
    manifest.yaml         # prompt name -> {path, label: monolith|clean|boundary}
  README.md
  tests/
    test_separation.py    # unit test for the deterministic verdict logic
```

### graph.yaml (the orchestration — YAML, not Python)

```yaml
state:
  corpus:  {type: list, description: "[{name, text, label}] loaded from manifest"}
  scores:  {type: list, description: "collected abstraction-span scores"}
  verdict: {type: dict, description: "{passed, min_monolith, max_clean, gap, table}"}

tools:
  load_corpus:        {type: python, module: examples.abstraction_span.nodes.tools, function: load_corpus}
  separation_verdict: {type: python, module: examples.abstraction_span.nodes.tools, function: separation_verdict}

nodes:
  load:
    type: python
    tool: load_corpus
    state_key: corpus
  score:
    type: map
    over: "{state.corpus}"
    as: item
    node:
      type: llm
      prompt: abstraction_span        # inline schema → {level_count, levels, rationale}
      variables: {prompt_text: "{state.item.text}"}
    collect: scores
  verdict:
    type: python
    tool: separation_verdict
    state_key: verdict
```

- **`abstraction_span.yaml`** — the scorer prompt. Single-judgement (it must pass
  its own metric, span ≤ 2): given `prompt_text`, list each *distinct kind* of
  cognitive operation (repeats of one kind merged), report the count. Carries an
  **inline `schema:`** block (`level_count: int`, `levels: list[str]`,
  `rationale: str`) — structured output declared in YAML, no Python model.
- **`load_corpus`** — Python tool (Layer-3 file I/O, sanctioned): reads
  `corpus/manifest.yaml`, loads each referenced prompt's text, returns
  `[{name, text, label}]`. Manifest references the live plot_modeller prompts by
  path (single source of truth; no duplicated prompt bodies) plus their labels.
- **`separation_verdict`** — Python tool (deterministic compute, no LLM): given the
  collected scores + labels, computes the separation test and returns the verdict
  dict + a printable ranking table. This is the Gate, expressed as code so it is
  testable and never calls a model.

### Run

```bash
PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 \
  yamlgraph graph run examples/abstraction_span/graph.yaml --full
```

## Acceptance criteria

- [ ] **Gate 1 — separation (decides the whole FR).** Running the graph scores all
      7 corpus prompts and the `verdict` node reports PASS only when every labelled
      monolith (`assign_pre_eff`, `assign_causality`, `assign_affects`,
      `extract_agents`) scores **strictly above both clean prompts**
      (`extract_glosses`, `classify_kinds`) — `min(monolith) > max(clean)`, gap ≥ 1
      level — with `extract_goals` landing between, and the one measured-failure
      prompt (`assign_pre_eff`, FR-585) in the top band. Verify the
      `Creating LLM: anthropic/claude-haiku-4-5` log line. If any monolith fails to
      clear both clean prompts, or a clean prompt scores into the monolith band →
      the LLM cannot reproduce the hand tagging → **KILL**: keep the example but mark
      it a documented null result; static W026 stands. Do not retune the scorer
      prompt more than once (FR-584 fourth-iteration-ritual lesson).
- [ ] The scorer prompt is single-judgement (passes its own abstraction-span ≤ 2)
      and declares structured output via an **inline `schema:`** block.
- [ ] Orchestration (map over corpus, per-item LLM call, collect) lives entirely in
      `graph.yaml`; Python contains only `load_corpus` (I/O) and
      `separation_verdict` (pure compute). No `execute_prompt` import in the example.
- [ ] `separation_verdict` has a unit test (`@pytest.mark.req`) with synthetic
      score inputs proving PASS and KILL paths — the verdict logic is tested without
      an LLM.
- [ ] Run output (the ranking table + verdict) committed as a measurement artifact;
      `demo-output.log` if placed under `examples/demos/`.
- [ ] README documents the command, the ground-truth labels, and the Gate.
- [ ] Diary reflection added.

## Stop rule

If Gate 1's separation fails, **the LLM cannot reproduce the hand
abstraction-tagging** — keep the example as a documented null result, keep static
W026, and record it in the diary (a metric that does not separate is a finding, not
a failure). Do not ship a score that launders an unvalidated guess. One scorer
iteration only.

## Out of scope (explicit)

- **No linter integration — permanently.** The metric is a standalone example only.
  The `linter-llm-free` import-linter contract (`.importlinter`, FR-588) stays; any
  future in-linter scoring must amend that contract in the open.
- **No build-gating on the LLM score.** The verdict is advisory; it gates only this
  FR's GO/KILL decision, never a merge.
- **No prompt-body duplication.** The corpus manifest references the live
  plot_modeller prompt files; it does not copy their text.
- **No auto-fix / auto-split**, and **no generalization to graph nodes** (future
  direction noted in the Seed only).

## Alternatives considered

- **FR-588's standalone Python spike** — rejected: hand-rolls orchestration that
  belongs in `graph.yaml`, imports `execute_prompt`, and demonstrates nothing about
  the framework. The graph-native example is the same validation with less Python
  and a reusable artifact.
- **Inline the corpus prompt texts into the example** — rejected: duplicates the
  plot_modeller prompts (entropy; two sources of truth). Manifest-by-path keeps one.
- **Pydantic `output_model` in Python instead of inline `schema:`** — rejected:
  inline schema keeps the contract in YAML where the framework wants it (CLAUDE.md
  Option A), so the example has zero Python schema code.

## Related

- `feature-requests/FR-588-llm-scored-prompt-abstraction-span.md` (rejected predecessor; its Judge analysis + linter-llm-free enforcement are inherited)
- `feature-requests/FR-586-prompt-monolith-linter-check.md` (static W026; the complement and label source)
- `feature-requests/FR-585-plot-modeller-L5-salience-gate-decode.md` (the abstraction-span hand-decomposition; the one measured-failure anchor)
- `examples/demos/map/graph.yaml` (the map-node convention this example follows)
- `docs/diary/diary-2026-06-24-the-brief-i-would-never-give-a-subagent.md` (the Seed)
