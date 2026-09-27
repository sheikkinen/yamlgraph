# Ramp RTM Derivation Demo

Derives candidate requirements (REQ-XXX) for a target repository from its
own inventory, producing a requirement-traceability-matrix draft for human
review (FR-866).

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/ramp_rtm/graph.yaml

# Run against a target repo
yamlgraph graph run examples/demos/ramp_rtm/graph.yaml \
  --var target=tests/fixtures/ramp_target --full
```

## What It Does

1. Collects the target repo inventory (modules, tests, configs)
2. Derives candidate requirements per module (map node)
3. Identifies coverage gaps (modules with no testable claim)
4. Writes `tmp/ramp/rtm-draft.{md,json}` for human review

## Output

RTM draft with candidate REQ IDs, per-module traceability, and a gap list.
IDs are drafts — the target repo assigns its own namespace on adoption.

## Anthropic and open objects (FR-1125)

This demo runs on Anthropic by the framework's built-in default and is the
showcase for FR-1125. Its `entries` field was `list[dict]` until
2026-09-27. Anthropic's constrained decoding cannot express an object with
unknown keys: the API refuses `additionalProperties: true`, so the SDK
rewrites such an object to `properties: {}` and the model can only answer
`[]`. YAMLGraph now refuses that shape before any call is made, at lint,
compile and bind time, with this diagnostic:

```text
[E017] Prompt 'derive_reqs' (node 'derive/node', model 'provider default'):
field 'entries.items' is an object with no declared properties; Anthropic
constrained decoding reduces it to {} and the model can only answer empty.
Declare its properties with the output_schema form (items: {type: object,
properties: {...}}) or use a provider that accepts open objects.
```

Before (the `fields` form; refused):

```yaml
schema:
  fields:
    entries:
      type: list[dict]
```

After (the `output_schema` form; committed in `prompts/derive_reqs.yaml`):

```yaml
output_schema:
  properties:
    entries:
      type: array
      items:
        type: object
        properties: {req_id: {type: string}, statement: {type: string},
                     witness_tests: {type: array, items: {type: string}},
                     confidence: {type: number}, status: {type: string, enum: [proposed]}}
        required: [req_id, statement, witness_tests, confidence, status]
```

Reproduce the refusal without spending a token: copy the demo to `tmp/`,
put `type: list[dict]` back in the copy's `prompts/derive_reqs.yaml` under a
`schema:` block, and lint it with the provider set explicitly (the resolver
reads `PROVIDER` before its built-in default, and a host `.env` can change
the classification):

```bash
PROVIDER=anthropic yamlgraph graph lint tmp/ramp_rtm/graph.yaml
```

Run the filled form (two calls; both variables set explicitly because the
model is an environment-overridable default):

```bash
PROVIDER=anthropic ANTHROPIC_MODEL=claude-haiku-4-5 yamlgraph graph run examples/demos/ramp_rtm/graph.yaml   --var target=tests/fixtures/ramp_target --full
```

The committed `demo-output.log` is that run from 2026-09-27: two map
branches, five entries, every one carrying `req_id`, `statement`,
`witness_tests`, `confidence` and `status`. The rule and the two schema
forms are documented in
[reference/prompt-yaml.md](../../../reference/prompt-yaml.md) under
"Unconstrainable schema fields on Anthropic".

