# Authoring brief: FR-1125 api-discovery — four nodes move to Mistral

Governing FR: feature-requests/FR-1125-refuse-unconstrained-objects-anthropic.md
(ledger `docs/issues-2026-09-27-fr1125-census.md`, second-wave rows for
`examples/api-discovery/prompts/synthesize.yaml` ·
`$defs.SynthesizeOutput_profile.sample_response.anyOf[0]` and
`examples/api-discovery/steps/schema-extract/prompts/{ckan,openapi,unsupported}.yaml`
· `sample_response`; disposition option 2 by operator decision
2026-09-27: `sample_response` is free-form parser metadata with no key
contract, so declaring properties would invent them, which judgement C-7
forbids).

Repository boundary: **this repository**, target files
`examples/api-discovery/graph.yaml` and
`examples/api-discovery/steps/schema-extract/graph.yaml`. No prompt is
edited.

## Task

Modify **exactly two graph files**, adding one line `provider: mistral`
to each named node, with the comment
`# FR-1125: sample_response is an open object; Anthropic constrained decoding cannot express it.`
above it:

1. `examples/api-discovery/graph.yaml` — node `synthesize`.
2. `examples/api-discovery/steps/schema-extract/graph.yaml` — nodes
   `summarize_openapi`, `extract_ckan`, `unsupported_family`.

Nothing else changes in either graph: no edge, tool, state, `defaults`
or `config:` entry. Mistral is the repository's second most used static
provider and accepts open objects under its structured output.

## Validation

- Before the edit, record the complete output of
  `yamlgraph graph lint examples/api-discovery/graph.yaml` and
  `yamlgraph graph lint examples/api-discovery/steps/schema-extract/graph.yaml`;
  after the edit, the identical commands. The after sets must contain
  no E016, E017, W028 or W029.
- `yamlgraph graph validate` on both graphs.
- `python -m pytest tests/unit -k "fr790 or fr791 or fr809 or api_discovery or fr1125" -q --no-cov`
  (these tests compile the two graphs and failed on the runner under the
  Anthropic default).
- No live smoke by brief. Record "no smoke, by brief".

**Prior art:** FR-1125 (governing FR; operator decision in its Judgement
fold); `fr-1125-questionnaire-provider-brief.md` (first option-2
precedent); FR-790/FR-791/FR-809 (the api-discovery graphs' own FRs).
