# Feature Request: FR-591 — Perspective-to-L5 Conversion Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced (2026-06-25) — provisional encoding contract
**Effort:** 1–2 days
**Requested:** 2026-06-25
**Predecessor:** FR-590 (multi-perspective spike — throwaway harness)
**Siblings:** FR-585 (select-type), FR-587 (snapshot-diff), FR-576 (assign_pre_eff)

## Summary

Promote the FR-590 per-character L5 decomposition from a throwaway Python spike
(`spike_perspective.py`) into a **proper, reusable YAMLGraph graph** that converts
classified beats into two first-class artifacts per character — a **point-of-view
prose account** and its **typed encoding** — and deterministically combines the
encodings into a unified L5. Result analysis (scoring, false-positive attribution)
becomes a **separate post-operation**, not part of the graph. The measurement
driver becomes a **shell script**, not a Python harness.

## Value Statement

The per-character viewpoint is the correct authoring primitive — character arcs are
the seam along which a synopsis is elaborated into a full plot (FR-590 diary). Making
the conversion a real graph turns those viewpoints into invocable, lintable, testable
outputs reusable beyond the L5 metric, and makes the two-stage split (comprehension →
representation) a **diagnosable** pipeline where a value drop is attributable to the
stored prose (wrong comprehension) or the encoding (wrong representation).

## Judgement (2026-06-25)

**Verdict: Authority GRANTED for the refactor — on a re-scoped encoding contract.**
The *architectural* core is sound and worth doing: promoting the throwaway
`spike_perspective.py` into an outer map-over-agents graph + inner per-agent
subgraph, separating conversion from scoring, storing viewpoints as first-class
outputs, and driving via a shell script. Every primitive is verified to exist:
`type: subgraph` under `type: map` with `input_mapping`/`output_mapping`
(`examples/image_pipeline/graph.yaml`), and `input_mapping: auto` is a supported mode
(`graph_schema.py` `Literal["auto","*"]`; `node_factory/subgraph_nodes.py` — `auto`
copies all parent fields). The two diary-grounded rationales are genuine and
*independent of any metric*: the per-character viewpoint is a reusable **authoring
primitive** (the writers' room), and the two-stage stored-prose pipeline is a
**fault-addressing probe** (comprehension vs representation). That is enough to
justify the graph promotion.

**But the encoding-contract decision at the FR's heart is not sound, and must be
re-scoped before enforce.** This is the binding correction, not a polish note.

1. **Do not freeze "direct `pre_world`+`eff_world`" as the settled contract — it
   re-imposes the wound (PRIMARY, blocking).** FR-591 justifies freezing the direct
   contract on "recall 0.53," but FR-590's own diary
   (`a-perspective-is-a-lens-and-a-probe`) records that *same run* as a **contract
   violation**: `pre_world` came back **81% garbage** — 58 of 108 `at`-FPs, precision
   **0.21** — because telling the model to fill preconditions with "what must already
   be true" re-imposes the precondition-salience reasoning load that the entire
   FR-585/587 arc isolated as *the* wound. The FR conflates **"direct pre+eff held
   recall 0.53" (true)** with **"direct pre+eff is the clean contract" (false)**. Its
   stated mitigation — "lean slices (0–3), no standing-fact restatement" — is a
   **prompt-wording lever against a missing-discrimination defect**, the exact move
   proven futile four times (repo memory `l5-prompt-lever-discrimination-kill`:
   *wording changes how much a model emits; it cannot install a faculty it lacks*).
   The honest option space is a trilemma, not the binary the FR presents:
   (a) direct pre+eff → recall 0.53 but pre_world 81% garbage / precision 0.21;
   (b) eff-only + global `diff_snapshots` pre → recall 0.25 (lossy on partial
   per-agent timelines); (c) the **unsolved** third path (pre_world neither
   model-reasoned nor reconstructed by the lossy global diff). FR-591 picks (a) and
   rejects (b) while never engaging (c). **Resolution required — take (i), since the
   FR elsewhere defers the metric:**
   - (i) Carry the encode contract as **explicitly provisional**
     (recall-preserving, **precision-open**), labeled as such in the
     `encode_perspective` AC and the README, with the pre_world/precision resolution
     deferred to the named ensemble follow-up FR (this FR's own Open Question #4). The
     graph's deliverable is *a reusable, diagnosable pipeline* — NOT a solved L5. Do
     not present "freeze direct" as a settled engineering decision.
   - (ii) Only if FR-591 wants to claim a *settled* contract: it must engage path (c)
     and prove on the bench a per-agent pre_world derivation that drops neither
     participant arrivals (the (b) failure) nor precision (the (a) failure) — which is
     metric work this FR explicitly scopes out, so (i) is the consistent choice.

2. **Frame the value honestly; promotion does not improve the number.** Open
   Question #4 already concedes the metric may be unchanged. Anchor the value solely
   on the reusable authoring primitive + the fault-addressing probe (both real,
   both metric-independent), and drop any implication that a "clean direct encoding
   contract" resolves the L5 wound. Note that FR-590 itself remains in limbo
   (diary: "Gate 1 run 1, KILL authority withheld") with no enforcement-result
   section recorded in the FR — record FR-590's disposition there too, so this FR's
   predecessor reference resolves in the FR record, not only the diary.

3. **`_parse_beats` must be MOVED into `nodes/tools.py`, not "reused" (blocking).**
   It currently lives only in `spike_perspective.py` — the file this FR deletes.
   `parse_perspective` depends on it, so it (and any other spike-only helper it
   needs) must be relocated to `nodes/tools.py`. The Related section's claim that
   `_parse_beats` is in `tools.py` is inaccurate; `_strip_code_fences` and
   `_dedup_fluents` are there, `_parse_beats` is not.

4. **Verify runtime semantics, not only `yamlgraph graph lint` (AC#1 proves schema
   validity only).** Smoke-run one fixture before wiring all five and confirm: (a)
   `input_mapping: auto` on the map-subgraph forwards the *shared* `glosses`
   alongside the per-item `agent` (auto copies parent fields — verify the map path
   does so per item); (b) `output_mapping: {perspectives: perspective}` collects each
   child's `perspective` dict into the parent list with recoverable order
   (`_map_index`); (c) deleting `spike_perspective.py` breaks no remaining importer
   once the `perspective` mode lands in `run.py`.

**Frozen scope:** the graph promotion (outer `perspective_l5.yaml` map-over-agents +
inner `perspective_agent.yaml` subgraph), conversion/scoring separation, the
`spike_perspective.sh` driver replacing the Python harness, viewpoint storage, and
the `combine_perspectives` (dict-shape) + `parse_perspective` tools with their
REQ-YG-020 unit tests. The **encoding contract is provisional and precision-open**;
the L5 metric and the precision/pre_world fix are deferred to the Open-Question-#4
ensemble FR. No new metric claims, no prompt-wording iteration dressed as a contract
fix, `evaluate.py`/`analyze_l5_confusion.py` unchanged.

## Problem

The perspective pipeline exists only as `examples/plot_modeller/spike_perspective.py`
— a throwaway harness that hand-wires `execute_prompt` calls in a Python loop, mixes
the conversion with its own scoring, and stores viewpoints as a side effect. It is:

1. **Not a graph** — it bypasses YAMLGraph entirely (the framework this repo exists to
   demonstrate). The conversion cannot be linted, composed, traced, or reused.
2. **Conflated** — generation and evaluation live in one script, so the verdict (a
   contaminated number) cannot be separated from the artifact (a sound viewpoint).
3. **Lossy under "correction"** — the last spike attempt (eff-only encode + deterministic
   `diff_snapshots` pre-derivation) **regressed recall 0.53 → 0.25** because the diff
   reconstruction is lossy on *partial per-agent* timelines (it only emits a fact at the
   single beat it first appears, and the intra-chapter/late-departure collapses drop
   participant arrivals the ground truth scores). That evidence kills the diff-derivation
   path and argues for a clean, direct encoding contract.

## Inputs

Per genre fixture (`fixtures/ground-truth/<genre>.yaml`), via
`load_glosses_with_kinds` + `_load_gt_agents`:

| Input | Type | Shape | Source |
|-------|------|-------|--------|
| `glosses` | `list[dict]` | `{id, gloss, chapter, kind, subject}`, narrative order | classified beats |
| `agents` | `list[str]` | character names | GT `agents:` block |

The graph receives **only** these two — it isolates L5 (it does not re-extract beats).

## Expected Outputs

The graph must emit **both** the viewpoint and the encoded version, plus the combined L5:

| Output | Type | Shape | Purpose |
|--------|------|-------|---------|
| `perspectives` | `list[dict]` | `{agent, viewpoint, beats}` per agent | self-describing per-character artifact |
| `l5` | `list[dict]` | `{id, pre_world, eff_world, pre_belief, eff_belief}` | unified per-beat L5 (scored) |

- `viewpoint` — first-person, beat-anchored prose (the authoring substrate). Stored to
  `results/l5/perspectives/<genre>/<agent>.md` for inspection.
- `beats` — that agent's typed `{id, pre_world, eff_world}` encoding (the representation).
- `l5` — deterministic union of all agents' `beats` (no LLM, no salience logic).

`perspectives` carrying its own `agent` label makes the output **order-independent** and
keeps the prose joined to its encoding for per-stage error attribution.

## Prompts

Both already exist; this FR fixes their contract.

- **`summarize_perspective.yaml`** (keep): retell the plot from one character's POV, beat-
  anchored `(F1)`, compress travel, narrate only beats the agent touches.
- **`encode_perspective.yaml`** (revise): transcribe the viewpoint into typed per-beat
  fluents for that agent, emitting **`pre_world` and `eff_world` directly** (the run-1
  contract that held recall at 0.53), with lean slices (0–3), token-faithful names, and
  no standing-fact restatement. **Reject** the eff-only variant: its recall-preserving
  promise failed (0.25) because deterministic pre-derivation cannot run on a partial
  single-agent timeline without dropping scored facts.

## Graph

Two graphs — an outer map-over-agents driver and an inner per-agent subgraph (map
supports `type: subgraph` inner nodes, FR-202; `input_mapping: auto` passes the shared
`glosses` alongside the per-item `agent`; the reducer stamps `_map_index` so collect
order is recoverable).

### Outer: `graphs/perspective_l5.yaml`

```yaml
metadata:
  name: perspective-l5
  description: >
    FR-591: convert classified beats into per-character viewpoints + typed
    encodings, then deterministically combine the encodings into unified L5.
prompts_relative: true
prompts_dir: ../prompts

state:
  glosses:      { type: list, description: "Input: classified beats" }
  agents:       { type: list, description: "Input: character names" }
  perspectives: { type: list, description: "Collected {agent, viewpoint, beats}" }
  l5:           { type: list, description: "Output: unified per-beat L5" }

tools:
  combine_perspectives:
    type: python
    module: examples.plot_modeller.nodes.tools
    function: combine_perspectives

nodes:
  per_agent:
    type: map
    over: "{state.agents}"
    as: agent
    node:
      type: subgraph
      graph: perspective_agent.yaml
      input_mapping: auto              # agent (item) + glosses (shared) → child
      output_mapping: { perspectives: perspective }
    collect: perspectives

  combine:
    type: python
    tool: combine_perspectives
    state_key: l5

edges:
  - { from: START, to: per_agent }
  - { from: per_agent, to: combine }
  - { from: combine, to: END }
```

### Inner: `graphs/perspective_agent.yaml`

```yaml
metadata:
  name: perspective-agent
  description: "FR-591: one character → viewpoint prose + typed beat encoding."
prompts_relative: true
prompts_dir: ../prompts

state:
  agent:        { type: str,  description: "Input: this character's name" }
  glosses:      { type: list, description: "Input: classified beats" }
  viewpoint:    { type: str,  description: "POV prose account" }
  encoded_raw:  { type: str,  description: "Raw encode YAML text" }
  perspective:  { type: dict, description: "Output: {agent, viewpoint, beats}" }

tools:
  parse_perspective:
    type: python
    module: examples.plot_modeller.nodes.tools
    function: parse_perspective

nodes:
  summarize:
    type: llm
    prompt: summarize_perspective
    state_key: viewpoint
  encode:
    type: llm
    prompt: encode_perspective
    state_key: encoded_raw
  assemble:
    type: python
    tool: parse_perspective          # {agent, viewpoint, beats: parse(encoded_raw)}
    state_key: perspective

edges:
  - { from: START, to: summarize }
  - { from: summarize, to: encode }
  - { from: encode, to: assemble }
  - { from: assemble, to: END }
```

`combine_perspectives` is adapted to read `beats` from each `{agent, viewpoint, beats}`
dict (currently it takes `list[list[dict]]`); its 8 unit tests update to the dict shape.
A new `parse_perspective(state)` tool returns `{agent, viewpoint, beats}` from the
agent's state (reusing `_parse_beats` + `_strip_code_fences`).

## Post-Operation: Analysis (separate)

Scoring and FP attribution stay **out of the graph**:

- `evaluate.main_l5` (unchanged) — combined world recall + predicate precision vs GT.
- `analyze_l5_confusion.py [--summary]` — FP by `(slice, pred)`.

These are invoked by the shell script *after* the graph writes `results/l5/<genre>.yaml`.

## Spike → Shell Script

Replace `spike_perspective.py` with `examples/plot_modeller/spike_perspective.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
set -a; source .env; set +a
: "${PROVIDER:=anthropic}" "${ANTHROPIC_MODEL:=claude-haiku-4-5}"
# 1. Conversion (the graph): inputs → viewpoints + encodings + combined L5
PROVIDER="$PROVIDER" ANTHROPIC_MODEL="$ANTHROPIC_MODEL" \
  python examples/plot_modeller/run.py --mode perspective
# 2. Analysis (separate post-operation)
python examples/plot_modeller/analyze_l5_confusion.py --summary
```

A `perspective` mode is added to `run.py` (mirrors `assign-pre-eff`): compile
`perspective_l5.yaml`, `app.invoke({"glosses", "agents"})` per genre, write each
agent's `viewpoint` to `perspectives/<genre>/<agent>.md` and `l5` to
`results/l5/<genre>.yaml`, then call `evaluate.main_l5`.

## Acceptance Criteria

- [x] `graphs/perspective_l5.yaml` + `graphs/perspective_agent.yaml` pass `yamlgraph graph lint`.
- [x] `run.py --mode perspective` runs all 5 fixtures, emitting `perspectives` (viewpoint + beats) and `l5`.
- [x] Each agent's viewpoint prose is stored to `results/perspectives/<genre>/<agent>.md`.
- [x] `encode_perspective.yaml` emits `pre_world` + `eff_world` directly — **PROVISIONAL** (recall-preserving, precision-open; the pre_world precision fix is deferred to the Open-Question-#4 ensemble FR, J1). The eff-only+diff path (`agent_eff_to_snapshots`) is removed.
- [x] `combine_perspectives` reads `beats` from `{agent, viewpoint, beats}` records (dual-mode: state dict → `{l5}` as a graph tool, list → per-beat L5 directly); deterministic via `_map_index` sort; unit-tested (REQ-YG-020).
- [x] `parse_perspective` tool unit-tested (REQ-YG-020).
- [x] `spike_perspective.sh` runs the graph then the separate analysis; `spike_perspective.py` deleted.
- [x] `evaluate.py` and `analyze_l5_confusion.py` unchanged (analysis stays separate).
- [x] Diary + changelog fragment (type: feat, scope: plot-modeller, req: REQ-YG-020).

## Enforcement Result (2026-06-25)

Built as frozen, honoring the four binding corrections:

1. **Encode contract carried as PROVISIONAL, not "frozen direct" (J1).**
   `encode_perspective.yaml` emits `pre_world`+`eff_world` directly (the
   recall-preserving run-1 form, ~0.50–0.53) but its header comment + AC#4 + the
   README note label it recall-preserving / **precision-open**, with the
   pre_world precision fix deferred to the ensemble follow-up FR. No "clean
   contract" claim is made.
2. **Value framed honestly; FR-590 disposition recorded** in
   `FR-590-plot-modeller-L5-multi-perspective.md` (KILL authority withheld —
   limbo; superseded as the conversion mechanism by this graph).
3. **`_parse_beats` MOVED into `nodes/tools.py`** (with `parse_perspective`);
   `agent_eff_to_snapshots` (the rejected eff-only+diff helper) and its 4 unit
   tests removed.
4. **Runtime semantics smoke-verified**, not only lint. One fixture
   (`detective-thriller-the-vanished-witness`, 5 agents) ran end-to-end: the
   map forwarded the shared `glosses` + per-item `agent` into each subgraph,
   `output_mapping` collected each child's `perspective`, `combine` unioned 5
   agents into 9 per-beat L5 entries, and 5 viewpoint `.md` files were written.
   Fresh detective world-recall 0.50 (≈ run-1 0.53 — recall preserved);
   predicate precision 0.15 (the precision-open wound, exactly as labeled).

**Deviations from the FR's literal YAML (all semantics-preserving):**

- The outer map uses **explicit** `input_mapping: {agent: agent, glosses: glosses}`
  rather than `auto` — mirrors the proven `examples/image_pipeline/graph.yaml`
  pattern and makes the forwarded fields self-documenting.
- The subgraph sub-node carries `state_key: perspective` so `wrap_for_reducer`
  extracts the clean record; the collected shape is
  `[{_map_index, agent, viewpoint, beats}]` (combine reads `beats` directly).
- The `combine` node relies on `combine_perspectives` being **dual-mode** (state
  dict in → `{"l5": [...]}`), so it needs no `state_key` indirection.
- Viewpoints land in `results/perspectives/<genre>/<agent>.md`.

## Alternatives Considered

| Approach | Why not |
|----------|---------|
| **Two-map + pairing passthrough** (map summarize, zip, map encode) | Order-fragile pairing of `agents[i]↔viewpoints[i]`; map-subgraph yields a self-describing `{agent,…}` dict instead. |
| **Eff-only encode + deterministic `diff_snapshots` pre** | Measured: recall 0.53 → 0.25. Diff reconstruction is lossy on partial per-agent timelines. Rejected on evidence. |
| **Keep the Python spike** | Bypasses the framework; conflates generation with scoring; viewpoints remain side effects, not outputs. |
| **Single monolithic encode (no map)** | Loses per-character framing (the salience filter) and per-stage error attribution. |

## Judgement Notes (for the Judge)

> **Superseded by the Judgement (2026-06-25) above.** Note #1 originally argued
> to *freeze* the direct contract; the Judge's binding correction J1 re-scoped it
> to **provisional / precision-open**. The enforced contract follows the Judgement,
> not this note. Retained for provenance only.

1. **Encoding contract** — direct `pre_world`+`eff_world` (recall 0.53) over eff-only+diff
   (0.25). Cited evidence; ~~freeze direct~~ → **carry as provisional, precision-open (J1)**.
2. **Inner-node shape** — `type: subgraph` under map (FR-202) over two-map pairing, for
   order-independent self-describing output.
3. **Scope boundary** — the graph *converts*; it does not *score*. Evaluation and confusion
   analysis are explicitly out of graph scope (separate post-operation).
4. **Open question** — does promotion to a clean graph change the number at all, or is the
   metric ceiling a property of per-agent democratic tracking (every character tracked
   equally vs a protagonist-centric GT)? The graph makes this measurable; resolving it is a
   *separate* FR (ensemble of FR-587 precision-leaning ∩ FR-590 recall-leaning).

## Related

- `feature-requests/FR-590-plot-modeller-L5-multi-perspective.md` (predecessor spike; disposition recorded)
- `docs/diary/diary-2026-06-25-a-perspective-is-a-lens-and-a-probe.md`
- `examples/plot_modeller/spike_perspective.sh` (shell driver — replaces the deleted Python harness)
- `examples/plot_modeller/nodes/tools.py` (`combine_perspectives`, `parse_perspective`, `_parse_beats`, `_dedup_fluents`)
- `examples/plot_modeller/graphs/{perspective_l5,perspective_agent}.yaml`
- `examples/plot_modeller/prompts/{summarize,encode}_perspective.yaml`
- `yamlgraph/map_compiler.py` (FR-202 map-over-subgraph), `yamlgraph/node_factory/subgraph_nodes.py`
