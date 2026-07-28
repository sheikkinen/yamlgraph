# Feature Request: Style-Convert Pipeline (prompt file → restyled prompts)

**Priority:** LOW
**Type:** Feature
**Status:** Judged (APPROVED WITH REVISIONS — folded)
**Effort:** 1 day
**Requested:** 2026-07-28
**First consumer / first event:** A prompt curator who already has a file of
image prompts (e.g. `outputs/image_pipeline/{ts}/prompts.txt`, or a hand-written
`sketches-*.txt`) and wants every prompt rewritten into a single target art
style (e.g. "John William Waterhouse, romantic Pre-Raphaelite oil painting").
First event: they run `yamlgraph graph run examples/style_convert/graph.yaml
--var input_file=... --var target_style="..."` and get a restyled prompts file
on disk.

## Summary

A new example pipeline, `examples/style_convert/`, that reads a prompt file
(one prompt per line), rewrites each prompt's art style into a single target
style via an LLM map node running on **Mistral**, and writes the converted
prompts back out in the same one-per-line format used by `image_pipeline`.

It is a structural mirror of `image_pipeline` with the front replaced: instead
of `generate_concepts → generate_prompts` (invent prompts from a style), it does
`load_prompts → convert_styles` (transform existing prompts to a style). It
**reuses** `image_pipeline`'s `save_prompts_node` unchanged, so its output is
drop-in compatible with `image_pipeline`'s `generate_images` node.

## Value Statement

A curator restyles an entire batch of image prompts into one coherent artistic
voice in a single command, turning a heterogeneous prompt file into a
style-consistent one ready for image generation.

## Problem

`image_pipeline` can only *invent* prompts from a style description; it cannot
take a pre-existing corpus of prompts and *re-skin* them. Users with curated
prompt files (the motivating case: `/Users/sheikki/Documents/prompts/
sketches-2026-07-27.txt`, 18 charcoal/graphite sketch prompts to be converted to
Waterhouse) have no declarative, reproducible path — they resort to ad-hoc
one-off scripts (which, in this session, silently emptied the source file when a
regex mis-parsed the numbering). A first-class YAML graph makes the operation
declarative, testable, and safe (writes to a fresh timestamped output dir, never
in place).

## Ideal Result

`style_convert` is the inverse-front twin of `image_pipeline`: point it at any
prompts file and a target style, and it emits a new prompts file where every
line is the same scene re-rendered in that style — nothing else invented,
nothing dropped, the source untouched. It composes both directions:
`image_pipeline` output feeds `style_convert`, and `style_convert` output feeds
`image_pipeline`'s `generate_images`.

## Proposed Solution

New example directory `examples/style_convert/`:

```
examples/style_convert/
├── graph.yaml
├── prompts/
│   └── convert_style.yaml        # metadata.provider: mistral
├── nodes/
│   ├── __init__.py
│   └── load_prompts.py           # reads input_file → list[str]
└── README.md
```

Pipeline:

```
START → load_prompts (python) → convert_styles (map, llm/mistral) → save_prompts (python, reused) → END
```

`graph.yaml` (shape):

```yaml
name: style-convert
version: "1.0"
description: Convert the art style of every prompt in a file to a target style
prompts_relative: true
prompts_dir: prompts

state:
  input_file: str
  target_style: str
  prompts: list          # raw prompts read from file
  converted: list        # restyled prompts (for save_prompts compatibility)
  prompt_file: str
  output_dir: str

tools:
  load_prompts:
    type: python
    module: examples.style_convert.nodes.load_prompts
    function: load_prompts_node
    description: Read input_file, one prompt per line, into prompts list
  save_prompts:
    type: python
    module: examples.image_pipeline.nodes.save_prompts   # REUSED, UNCHANGED
    function: save_prompts_node
    description: Save restyled prompts to a timestamped prompts.txt

nodes:
  load_prompts:
    type: python
    tool: load_prompts
    state_key: prompts

  convert_styles:
    type: map
    over: "{state.prompts}"
    as: prompt_text
    node:
      type: llm
      prompt: convert_style          # structured schema → {prompt_text: str}
      state_key: converted_one
      variables:
        prompt_text: "{item.prompt_text}"
        target_style: "{state.target_style}"
    collect: prompts        # save_prompts consumes state.prompts
    flatten_output: true
    max_items: 100
    # R-3: NO on_error: skip — fail-fast; a branch failure aborts the run
    #      before save_prompts writes, so N in == N out or nothing written.

  save_prompts:
    type: python
    tool: save_prompts
    state_key: prompt_file
    requires: [prompts]

edges:
  - from: START
    to: load_prompts
  - from: load_prompts
    to: convert_styles
  - from: convert_styles
    to: save_prompts
  - from: save_prompts
    to: END
```

`prompts/convert_style.yaml` pins Mistral via prompt metadata (same mechanism as
`examples/npc/prompts/scene_describe.yaml`) and (R-2) declares a **structured
schema** whose model carries `prompt_text: str`, so the flattened map output is a
dict `save_prompts_node` can extract — a bare LLM scalar would be wrapped by the
map reducer as `{"_map_index": ..., "value": ...}` and stringified as a dict in
the output file (the `batch_image_prompts` `enrich_prompt.yaml` schema is the
precedent):

```yaml
name: convert_style
description: Rewrite a single image prompt into a target art style
metadata:
  provider: mistral
  temperature: 0.7
schema:
  name: ConvertedPrompt
  fields:
    prompt_text:
      type: str
      description: The original prompt rewritten in the target art style
system: |
  You rewrite image-generation prompts into a target art style. Preserve the
  exact subject, composition, pose, and action. Replace only medium/style/artist
  references with the target style. Output ONLY the rewritten prompt — no
  preamble, no quotes, no numbering.
user: |
  Target style: {{ target_style }}

  Original prompt:
  {{ prompt_text }}

  Rewrite the prompt in the target style:
```

`nodes/load_prompts.py` (R-1 — binding input contract): reads
`state["input_file"]` as UTF-8 text, treats each **nonblank line** as one prompt,
strips **only** a leading decimal enumerator of the form `N. ` (preserving all
other prompt text verbatim), and raises `ValueError` if the file is missing or
yields zero prompts (Commandment 6 — no silent empty). It **never writes** to the
input file. Blank-line paragraph parsing, multi-line prompts, and named-style
lookup tables are explicitly out of scope.

Usage:

```bash
yamlgraph graph run examples/style_convert/graph.yaml \
  --var input_file="/Users/sheikki/Documents/prompts/sketches-2026-07-27.txt" \
  --var target_style="John William Waterhouse, romantic Pre-Raphaelite oil painting" \
  --full
```

## Acceptance Criteria

<!-- Frozen by judgement 2026-07-28 (APPROVED WITH REVISIONS). -->

- [x] AC-01: This FR records the R-1 input contract, R-2 structured-output
      contract, R-3 fail-fast count-preservation contract, and R-4 new
      capability requirement.
- [x] AC-02: `capabilities/CAP-215-style-convert-pipeline.yaml` exists with a new
      `REQ-YG-573` covering the style-convert example, and every new/changed test
      function is tagged with `@pytest.mark.req("REQ-YG-573")`.
- [x] AC-03: `examples/style_convert/graph.yaml` defines the pipeline
      `START -> load_prompts -> convert_styles -> save_prompts -> END`, declares
      `input_file`, `target_style`, `prompts`, `prompt_file`, and `output_dir`,
      uses `prompts_relative: true`, and imports the existing
      `examples.image_pipeline.nodes.save_prompts.save_prompts_node` without
      modifying that node. (Also declares `source_prompts` — see D-B.)
- [x] AC-04: `yamlgraph graph lint examples/style_convert/graph.yaml` passes.
- [x] AC-05: `load_prompts_node` returns the loaded prompts from UTF-8 text with
      one prompt per nonblank line, strips only leading `N. ` decimal enumerators,
      preserves all other prompt text, and raises `ValueError` for missing files
      or inputs that produce zero prompts. **Deviation D-B:** the return key is
      `source_prompts`, not `prompts`, to avoid a count-doubling composition bug.
- [x] AC-06: `load_prompts_node` tests assert the source input file bytes/text are
      unchanged after loading.
- [x] AC-07: `examples/style_convert/prompts/convert_style.yaml` has a structured
      schema with `prompt_text: str`, and prompt instructions that preserve
      subject, composition, pose, and action while replacing only
      medium/style/artist references. **Deviation D-A:** Mistral is pinned on the
      graph node (`convert_styles.node.provider: mistral`), not via prompt
      metadata — the executor ignores `metadata.provider`.
- [x] AC-08: A graph-level test with a mocked LLM proves `convert_styles`
      produces `state.prompts` entries compatible with unchanged
      `save_prompts_node`, i.e. the saved `prompts.txt` contains converted prompt
      lines rather than stringified dicts.
- [x] AC-09: A count-preservation test (end-to-end, compiled graph) proves N
      loaded prompts produce exactly N saved prompt lines on success.
- [x] AC-10: A failure-path test proves a conversion branch failure surfaces an
      error entry and error channel instead of silently dropping a prompt.
- [x] AC-11: `examples/style_convert/README.md` documents usage, required
      variables, input contract, output path inherited from the reused save node,
      and round-trip composition with `image_pipeline`.
- [x] AC-12: A changelog fragment exists in `changelog/unreleased/` with `req:`
      set to `REQ-YG-573`.
- [x] AC-13: A diary reflection exists in `docs/diary/`.

## Implementation Notes / Deviations (enforcement, 2026-07-28)

Status: **Enforced.** Example built, 34 unit tests green, real Mistral smoke run
verified (3 prompts → 3 restyled lines). Two deviations from the frozen plan,
both discovered by the mandated smoke run (Commandment 2) and recorded here per
doctrine:

- **D-A — Provider is pinned on the graph node, not prompt metadata.** The plan
  (and AC-07, echoing the judgement's premise) said to pin Mistral via
  `metadata.provider` in `convert_style.yaml`, citing `scene_describe.yaml` as
  precedent. Empirically this is a **no-op**: the executor's
  `_resolve_provider_and_model` reads a top-level `provider` key (or the graph
  node / graph defaults) and never reads `metadata.provider`
  (`yamlgraph/executor_base.py:153-169`). The first smoke run silently fell
  through to env `PROVIDER=deepseek`. Fix: `provider: mistral` is set on the map
  sub-node (`convert_styles.node.provider`), which the executor honors
  (`yamlgraph/node_factory/llm_nodes.py:148`). The prompt `metadata` block was
  removed to avoid dead/misleading config. AC-07 is satisfied in substance
  (Mistral is pinned; structured `prompt_text` schema present) — the pin just
  lives on the graph node. The `scene_describe.yaml` "precedent" is itself
  relying on a decorative-but-ignored metadata block.

- **D-B — Loader writes `source_prompts`, not `prompts`.** AC-05 literally said
  `load_prompts_node` returns `{"prompts": [...]}`. Reusing `prompts` as both the
  loader output and the map `collect: prompts` target **doubled the count**: the
  ordered append-reducer stacked the N converted entries on top of the N raw
  loader entries (smoke showed 3 in → 6 saved). This is the `composition_bug`
  trap — each unit test passed, the assembled system failed. Fix: the loader
  writes `source_prompts`, the map fans out over `{state.source_prompts}` and
  collects into a fresh `prompts` (mirroring `image_pipeline`'s
  `concepts → prompts`). The loader's substantive contract (enumerator strip,
  `ValueError` on missing/empty, source immutability) is unchanged — only the
  output key name changed. A new end-to-end test
  (`TestStyleConvertEndToEnd`) compiles and invokes the real graph with a mocked
  LLM and asserts N-in == N-out, which the reducer-only tests had missed.

## Alternatives Considered

1. **Add a mode flag to `image_pipeline/graph.yaml`** (invent vs. convert) —
   rejected: overloads one graph with a branch, muddies the clean linear
   pipeline, and violates one-concern-per-example. A sibling that *reuses*
   `save_prompts_node` keeps both graphs linear and legible.
2. **One-off Python script** (what this session started with) — rejected: not
   declarative, not tested, and already demonstrated its hazard by silently
   emptying the source file on a regex mis-parse. YAMLGraph + LLM over regex is
   doctrine.
3. **In-place rewrite of the input file** — rejected: destructive and
   irreproducible. Timestamped output dir (inherited from `save_prompts_node`)
   preserves provenance.

## Related

- `examples/image_pipeline/graph.yaml` — parent pipeline; `save_prompts_node` reused
- `examples/image_pipeline/nodes/save_prompts.py` — reused sink
- `examples/batch_image_prompts/graph.yaml` — prior art for map + collect
- `examples/npc/prompts/scene_describe.yaml` — cited (pre-enforcement) as prior art for `metadata.provider: mistral`; see deviation D-A — that mechanism is a no-op and provider is pinned on the graph node instead
- Motivating input: `/Users/sheikki/Documents/prompts/sketches-2026-07-27.txt`
- Judgement draft: `tmp/draft-judgement.md` (2026-07-28, gpt-5.5 via `scripts/judge.sh`)

## Judgement (2026-07-28)

**Verdict:** APPROVED WITH REVISIONS — sound contrib/example; enforcement
authority activates only after R-1..R-4 are folded (done, this revision).
Rendered via the sole route (`scripts/judge.sh` → YAMLGraph adapter, `gpt-5.5`);
draft archived at `tmp/draft-judgement.md`.

| # | Finding | Resolution (binding, folded) |
|---|---------|------------------------------|
| R-1 | Input format left open as a question while acceptance criteria required `N.` stripping — a contradiction | Binding input contract folded into Proposed Solution + AC-05: each nonblank line = one prompt; strip only leading `N. `; `ValueError` on missing/empty. No paragraph/multiline/named-style parsing. |
| R-2 | `convert_style.yaml` emitted unstructured text → map reducer wraps a bare scalar as `{"_map_index":…, "value":…}`, which `save_prompts_node` stringifies as a dict | Structured schema with `prompt_text: str` folded in (mirrors `batch_image_prompts/enrich_prompt.yaml`); AC-07, AC-08 witness compatibility. |
| R-3 | `on_error: skip` + count-tolerant criteria contradicted the "nothing dropped" ideal (Commandment 6) | `on_error: skip` removed; fail-fast so N in == N out or nothing written; AC-09, AC-10. |
| R-4 | No capability/REQ covers the new example | New `capabilities/CAP-XXX-style-convert-pipeline.yaml` + `REQ-YG-XXX`; AC-02. |

**Purge list:** `on_error: skip` on `convert_styles`; the two open human questions
(both now resolved — input format bound by R-1; `target_style` stays free-form,
no named-style registry); any in-place source-file rewrite.

**Scope frozen** (deliverables D-1..D-10):

| Deliverable | Surface |
|---|---|
| D-1 | This FR revised with R-1 through R-4 |
| D-2 | `capabilities/CAP-XXX-style-convert-pipeline.yaml` with new `REQ-YG-XXX` |
| D-3 | `examples/style_convert/graph.yaml` |
| D-4 | `examples/style_convert/prompts/convert_style.yaml` |
| D-5 | `examples/style_convert/nodes/__init__.py` |
| D-6 | `examples/style_convert/nodes/load_prompts.py` |
| D-7 | `examples/style_convert/README.md` |
| D-8 | Unit tests: loader, prompt metadata/schema, graph structure/lint, map-output compatibility, count preservation, source-file immutability |
| D-9 | Changelog fragment in `changelog/unreleased/` referencing the new REQ |
| D-10 | Diary entry in `docs/diary/` |

**Not authorized:** changes to YAMLGraph core map/compiler behavior; changes to
`examples/image_pipeline/nodes/save_prompts.py` or `examples/image_pipeline/graph.yaml`;
image generation behavior; live Mistral/API tests; named style registries;
multiline/paragraph prompt parsing; destructive in-place source edits; new
dependencies; CI, hook, judge, review, or Scripture changes.

**Conditions for enforcement (all GATE):**

| # | Condition |
|---|-----------|
| C-1 | R-1..R-4 folded into the FR before implementation (satisfied by this revision). |
| C-2 | Do not alter core map behavior to make the example pass; fix at the prompt schema/output boundary. |
| C-3 | Do not alter `save_prompts_node`; reuse unchanged, prove compatibility by tests. |
| C-4 | No `on_error: skip` / partial-output policy for `convert_styles`; output count must equal input count. |
| C-5 | Do not consume or mutate the motivating external file path in tests; temp files/fixtures only. |
| C-6 | No live-provider tests; prove provider via prompt metadata + mocked conversion. |
| C-7 | No CI, hook, judge/review doctrine, or Scripture changes under this FR. |

### Questions for the human (as options, or 'none')

None — both prior open questions were resolved by the judgement (R-1 binds the
input format; `target_style` remains a free-form string, no named-style registry).
