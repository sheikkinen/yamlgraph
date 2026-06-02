# Meta Demo

Apply a natural-language **verb** to a code **target** and get back typed output.
The headline is self-reference: point `target` at this graph's own YAML and watch
the framework reason about its own configuration.

## Lineage

In January 2023, Santiago Valdarrama's `meta.js` trick showed that an LLM could be
a general-purpose code transformer driven from the command line:

```bash
node meta 'explain structure' ./meta.js
node meta 'convert to C code' ./meta.js | tee meta.c
```

It was brilliant — and trust-by-default. Model output flowed straight to disk, with
no boundary, no type, and no trace. This demo is the typed, traced upgrade:

| meta.js (2023) | meta demo (YAMLGraph) |
|---|---|
| Hardcoded prompt string | YAML prompt (`prompts/meta_transform.yaml`) |
| Free-text stdout | Typed `MetaResult` (inline schema) |
| `cat`/pipe with no escaping | Shell tool with `shlex.quote` escaping |
| `\| tee meta.c` writes to disk | Output stays in graph state; caller decides |

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/meta/graph.yaml

# Headline: the demo explains its own graph YAML (self-reference)
./examples/demos/meta/demo.sh

# Any verb × any target
./examples/demos/meta/demo.sh "suggest improvements" examples/demos/meta/graph.yaml
./examples/demos/meta/demo.sh "add unit tests" yamlgraph/utils/expressions.py

# Or run directly
yamlgraph graph run examples/demos/meta/graph.yaml \
  --var verb="explain structure" \
  --var target="examples/demos/meta/graph.yaml" --full
```

## How It Works

1. `load` (type: tool) runs the `read_file` shell tool (`cat {file}`) on `target`,
   storing the contents in `state.source`.
2. `transform` (type: llm) applies `state.verb` to `state.source` via the
   `meta_transform` prompt and returns a typed `MetaResult`:
   - `summary` — one paragraph result of applying the verb
   - `findings` — concrete observations/steps
   - `suggested_code` — resulting code (empty for explanatory verbs)

The model is selected via `PROVIDER` / `ANTHROPIC_MODEL` env vars — never hardcoded.

## Verbs to Try

`explain structure`, `suggest improvements`, `add comments`, `create unit tests`,
`convert to C code`, `simplify`, `write documentation`, `find bugs`.
