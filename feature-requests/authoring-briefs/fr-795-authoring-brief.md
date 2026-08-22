# FR-795 endpoint-probe prompt schema repair

Repair the schema dialect mismatch in exactly one governed artifact:

- Modify `examples/api-discovery/steps/endpoint-probe/prompts/probe.yaml`.
- Do not modify `examples/api-discovery/steps/endpoint-probe/graph.yaml`, any
  other API-discovery artifact, tests, framework files under `yamlgraph/`,
  feature requests, changelog files, or diary files.

Convert the prompt's native `schema:` block to JSON-Schema `output_schema:`.
The output schema must have top-level `type: object` and properties named
`live_endpoints`, `html_pages`, and `verdict_hint`:

- `live_endpoints` is an array whose object items preserve properties `url`
  (string), `status` (integer), `content_type` (string), and `body_preview`
  (string), including their existing descriptions. Require all four item
  properties.
- `html_pages` is an array of strings with its existing description.
- `verdict_hint` is a string with its existing description and is optional by
  omission from the top-level `required` list.
- The top-level `required` list contains only `live_endpoints` and
  `html_pages`.
- Preserve the prompt's system and user text unchanged.

Use `examples/beautify/prompts/analyze.yaml` as the committed precedent for
nested object-array properties in the `output_schema:` dialect. The governing
scope and acceptance criteria are in
`feature-requests/FR-795-endpoint-probe-schema-dialect-repair.md` and its
committed `.judgement.md` companion.

Run and report these validations:

1. `yamlgraph graph lint examples/api-discovery/steps/endpoint-probe/graph.yaml`
2. `.venv/bin/python -c 'from yamlgraph.compile.graph_loader import load_and_compile; load_and_compile("examples/api-discovery/steps/endpoint-probe/graph.yaml")'`
3. Attempt the narrowest meaningful graph smoke with `candidate_urls` and
   `max_iterations`; if credentials or external service access block it,
   record the exact command and concrete reason.

Write `tmp/draft-authoring-report.md` with headings `Artifacts`, `Precedent`,
`Validation`, `Repairs`, and `Blocked validation`. List the modified prompt
path under `Artifacts` and report command outcomes honestly.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
