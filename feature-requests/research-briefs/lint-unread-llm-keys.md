# Problem brief: LLM settings written where yamlgraph never reads them pass lint silently

**Prior art:** FR-1144 (race nodes honour `thinking_budget`, merged #747,
v0.6.3) — its Related section recorded that csap writes `thinking_budget: 0`
under graph `metadata:` and prompt `metadata:`, "and yamlgraph reads neither",
and its judgement (C-4, C-6) forbade linter changes under that authority and
required any linter policy to return as a separate FR. FR-1165 (refuse
unapplied `config.max_tokens` at load, #776) — the most recent precedent for
"a value the user wrote that the runtime does not apply" handled as a
load-time refusal rather than a lint warning. FR-071 / FR-230 (thinking
budget; linter family W071-1..W071-4 in
`yamlgraph/linter/checks_providers.py`, which inspects only `defaults:` and
node configs). FR-165 (no-silent-fallback lint). FR-232 / FR-272 (race node
and router race candidates; `candidates` is typed `list[dict[str, Any]]` and
validation checks only that `provider` or `model` is present).
`GraphConfigSchema` and `ObservabilityConfig` both declare
`model_config = {"extra": "allow"}`; graph `metadata:` is an untyped
free-form block.

## Problem statement

yamlgraph resolves LLM tuning settings (`thinking_budget`, `temperature`,
`max_tokens`, `effort`, `provider`, `model`) from a fixed set of places:
the node and graph `defaults:`; prompt YAML contributes only top-level
`provider` and `model` (`yamlgraph/executor_base.py`). No
code path reads a prompt `metadata:` block or a graph `metadata:` block.
A setting written anywhere else is accepted by the loader,
passes `yamlgraph graph lint` with no finding, and has no runtime effect.
The graph runs, so the defect surfaces only as a behaviour difference that
someone has to notice and attribute: here, Gemini running with its default
thinking on every call, which made it slow enough that the Azure candidate
won about 95% of races.

Two places are open to this:

1. Graph-level `metadata:` and prompt-level `metadata:` carrying a tuning
   key that is not read from that location (`thinking_budget` in either;
   `temperature`, `max_tokens`, `effort` in either).
2. Race and router-race `candidates` entries carrying any key beyond
   `provider` and `model`: the candidate dict is passed through as
   `provider=candidate.get("provider"), model=candidate.get("model")` and
   every other key is discarded.

The question: what mechanism makes an unread LLM setting visible to the
author at the moment they write or validate the graph, without breaking
graphs that use `metadata:` for its legitimate purpose (free-form
annotations that yamlgraph is not meant to read)?

## Classification

enforcement/latency-critical

## Constraints

- Graph `metadata:` is a legitimate free-form annotation block; most keys in
  it must stay silent. Only keys that yamlgraph reads elsewhere as LLM
  settings are in question.
- Prompt YAML top-level `provider` and `model` ARE read and must not be
  flagged. `reference/prompt-yaml.md` documents no `metadata:` block at all,
  so its legitimate contents are undefined; prompt-file linting today
  (`yamlgraph/linter/checks_prompts.py`) treats `metadata.description` as never rendered.
- The set of LLM settings is not static (`effort` arrived in FR-1151,
  `max_tokens` refusal in FR-1165). A hand-copied key list in the linter
  drifts from what `yamlgraph/utils/llm_factory.py`, `yamlgraph/node_factory/llm_nodes.py` and `yamlgraph/node_factory/race_node.py` actually
  resolve.
- Existing csap graphs (pinned `==0.5.25`) must keep loading after a
  yamlgraph upgrade; the csap migration itself is not in scope for
  yamlgraph.
- Linter checks carry a code (W/E + number), a message, and a `fix` string
  (`LintIssue`); each new check needs a witness test with
  `@pytest.mark.req`.
- Three-layer import contract (`.importlinter`): the linter may not import
  node-factory runtime modules that the contract forbids.
- No new runtime behaviour for `thinking_budget` resolution: reading it
  from `metadata:` was explicitly rejected in FR-1144 ("a separate,
  framework-wide FR").

## Witnessed incidents

- csap `a60fb2b9` (2026-11-16): all 18 YAML files that set
  `thinking_budget` set it under `metadata:` — 4 graph files
  (`flex_navigator/graph.yaml`, `flex_navigator/graph_v2.yaml`,
  `post_call/graph.yaml`, `persona_judge/graph.yaml`) and 14 prompt files
  (e.g. `flex_navigator/prompts/classify_intents.yaml`). Zero under
  `defaults:`.
- Same day, yamlgraph `ad5db794`: the graph loader (`yamlgraph/compile/graph_loader.py`) on the three
  flex_navigator/post_call graphs yields `defaults.thinking_budget = None`;
  raw YAML `metadata = {'thinking_budget': 0}`.
- Same day: `yamlgraph graph lint graphs/post_call/graph.yaml` →
  "No issues found"; `graph_v2.yaml` → 26 warnings (W002, W012×12, W017,
  W022, W803×14, W804×2), none mentioning `thinking_budget` or `metadata`.
- Operator report (2026-11-16): all 12 csap LLM nodes are race nodes;
  Gemini runs with default thinking; Azure wins ~95% of races. The report
  attributed the ignored setting only to yamlgraph 0.5.25's race node and
  did not notice the `metadata:` placement.
- FR-1144 (2026-09-30) named the `metadata:` placement as a csap follow-up
  in prose. Seven weeks later the placement is unchanged in all 18 files:
  a note in an FR body reached no author at write time.
