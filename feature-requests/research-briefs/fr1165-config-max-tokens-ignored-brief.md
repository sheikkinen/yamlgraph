# Problem brief: the documented graph-level config.max_tokens is read but never applied

**Prior art:** `feature-requests/027-execution-safety-guards.md` (execution safety guards: added `config.max_tokens`
parsing and REQ-YG-060 "max_tokens wired from YAML config/node config
through execute_prompt() to create_llm()"); FR-223 (refactor of
`create_node_function` into phases; node `max_tokens` resolved from
`node_config` then `defaults`); FR-984 / FR-1085 (`config.max_concurrency`,
a graph-level key that is applied).

## Problem statement

`reference/graph-yaml.md` documents a top-level `config:` block whose
`max_tokens` is the "Default max output tokens for LLM calls. Can be
overridden per-node." `GraphConfig.__init__`
(`yamlgraph/compile/graph_loader.py`) stores it as `self.max_tokens`.
No code reads `GraphConfig.max_tokens`: LLM nodes resolve
`node_config.get("max_tokens", defaults.get("max_tokens"))`
(`yamlgraph/node_factory/llm_nodes.py`), and the compiler builds the
effective defaults from `config.defaults` only
(`yamlgraph/compile/node_compiler.py`). A graph that sets
`config: {max_tokens: 4096}` runs every LLM call at the provider default
with no warning.

`git show c96d9e69` (feature request 027) shows the line that stores the value was the
only change to the loader; it was never wired. The feature request 027 tests assert that
`GraphConfig` parses the value (`test_graph_config_max_tokens`) and that a
node-level value reaches the executor, but no test asserts that the
graph-level value reaches an LLM call. CAP-17's REQ-YG-060 claims the
wiring.

A related observation: prompt YAML files may carry a top-level
`max_tokens` (`examples/book_translator/prompts/identify_chapters.yaml`)
that is not documented in `reference/prompt-yaml.md` and is not read.

The question: should a documented graph-level key that has never had an
effect be wired, removed, or refused, and which tests must witness the
chosen contract?

## Classification

judgement/analysis/generation

## Constraints

- No silent no-op configuration (Commandment 6): a key the docs promise
  either takes effect or fails loudly.
- Precedence must be explicit and single-sourced: node value, `defaults`,
  graph `config`, provider default.
- The published JSON schema (`graph-v1.json`) includes `config.max_tokens`.
- Existing graphs in the repo set `defaults.max_tokens` or node
  `max_tokens`; none found setting `config.max_tokens` (git grep at
  `c91e862d`).
- TDD: a test that compiles a graph with `config.max_tokens` and asserts
  the value reaching `create_llm`, without network.

## Witnessed incidents

- Code read 2026-11-14 at `c91e862d`: the only reference to
  `GraphConfig.max_tokens` outside its assignment is in tests.
- `git log -S max_tokens` on `node_compiler.py` and `llm_nodes.py` shows feature request 027 and FR-223 never consumed the graph-level value.
