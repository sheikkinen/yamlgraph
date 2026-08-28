# Authoring task brief — FR-896 research-route traceability wiring

**Prior art:** fr-890-research-route-brief.md authored the route this brief
modifies in place (superseded for these artifacts by FR-896's judged scope);
fr-866-ramp-rtm-brief.md, fix-research-agent-vars-brief.md,
fr-779-green-brief.md, fr-780-green-brief.md are keyword-only matches on
"research"/"brief" — unrelated targets, no overlap.

Governing FR: feature-requests/FR-896-research-route-precedent-traceability.md
(judged APPROVED WITH REVISIONS; scope D-3 persona supply, D-4 librarian pin).
The deterministic Python side (nodes/research_tools.py, scripts/) is already
implemented and tested — this brief covers ONLY the governed graph and prompt
artifacts.

## Target

`examples/demos/research-route/` — modify `graph.yaml` and `prompts/*.yaml`
in place. No new demo directories.

## Task 1 — graph.yaml: committed-context assembler node

- Add a tool entry `collect_committed_context` (type python,
  path `nodes/research_tools.py`, function `collect_committed_context`,
  description: deterministic committed-state grounding block — CAP registry
  one-liners, ARCHITECTURE.md headings, Scripture trap/cure keys).
  The function already exists and takes `repo_root` (defaults to cwd `.`).
- Add state field `committed_context: str`.
- Add a python node `collect_committed_context` with
  `state_key: committed_context`, wired between `collect_graph_shapes`
  and the five-persona fan-out (edges: collect_graph_shapes →
  collect_committed_context → the five personas).
- Pass `committed_context: "{state.committed_context}"` as a variable to
  all five persona prompt nodes (os_infra_primitivist, data_process_planner,
  yamlgraph_native_planner, subtractionist, librarian_research) and to
  librarian_structure.

## Task 2 — persona prompts: closed enums, rationale, precedent contract

For each of `prompts/os_infra_primitivist.yaml`, `prompts/data_process_planner.yaml`,
`prompts/yamlgraph_native_planner.yaml`, `prompts/subtractionist.yaml`,
`prompts/librarian_structure.yaml`:

- In the schema:
  - `solution_class`: description must list the closed enum exactly:
    os-permissions, process-boundary, schema-data, graph-pipeline,
    subtraction, external-method, boundary-enforcement. Free text is
    rejected by the reducer in code.
  - `verdict`: description must list the closed enum exactly: pursue,
    dissent, duplicate. `echo` is reducer-only; a persona claiming it is
    rejected.
  - Add a required `rationale` field (type str): one or two sentences,
    at most 400 characters — why this verdict.
  - Every prose field: state the 400-character ceiling; over-length output
    is rejected, never truncated.
- In the template body:
  - Include the committed-context block: a section rendering
    `{committed_context}` labeled as the committed state of this repository.
  - Precedent contract paragraph: the `precedent` field MUST cite at least
    one committed identifier — an FR number (FR-XXX), a CAP number
    (CAP-XXX), a repo-relative path that exists, or a Scripture trap/cure
    key from the committed context block. If the only support for the
    candidate is the problem brief itself, write the literal marker
    `brief-echo:` followed by what is being restated — the row is then
    retained but excluded from scoring. A fabricated identifier fails the
    whole run.

## Task 3 — librarian role pin (D-4)

`prompts/librarian.yaml` (the agent prompt) and
`prompts/librarian_structure.yaml`:

- Pin the librarian to EXTERNAL precedent reporting only: it reports how
  the world already solves this class of problem (named tools, patterns,
  papers), citing the exact URL as returned by search_web tool results.
  It must NOT propose internal repo designs, gates, or implementation
  plans — that is the other personas' seat. Witnessed drift (2026-08-28):
  the librarian returned a solution-shaped internal design with a novel
  free-text class; the schema now rejects that in code, and the prompt
  must stop inviting it.
- The librarian_structure `solution_class` is constrained to the same
  closed enum (external precedent is typically `external-method`).
- The cited URL must be copied verbatim from the tool results; the reducer
  reconciles it against `librarian_tool_results` and fails closed on
  fabrication.

## Task 4 — brevity phrasing (live-run repair, 2026-08-28)

Witnessed on the first live run: three personas overflowed the 400-character
ceiling on `candidate`/`rationale` and the run failed (correctly — rejection,
never truncation). Character counts are weak instructions for LLMs; word and
sentence caps hold better. In every persona prompt
(os_infra_primitivist, data_process_planner, yamlgraph_native_planner,
subtractionist, librarian_structure):

- Rephrase each prose field description from "At most 400 characters..." to
  "At most 2 short sentences, roughly 40 words (hard cap 400 characters);
  over-length output is rejected, never truncated."
- Add one prominent instruction near the top of the user template body:
  "BREVITY IS MECHANICALLY ENFORCED: every field must stay under 400
  characters — about 40 words. One or two short sentences per field.
  A single over-length field destroys the whole run."

## Task 5 — validation retry on persona nodes (live-run repair 2, 2026-08-28)

Second live run: four of five personas passed; data_process_planner overflowed
`candidate` by a margin. Per two_strike_split, stop rewording — mechanize:

- Add `on_error: retry` and `max_retries: 2` to the five persona LLM nodes
  (os_infra_primitivist, data_process_planner, yamlgraph_native_planner,
  subtractionist, librarian_structure) in graph.yaml. Precedent:
  examples/demos/book-summary/graph.yaml persona nodes.
- In prompts/data_process_planner.yaml only: tighten the `candidate` field
  description to "Name the single change in ONE short sentence (under 30
  words)." Keep the rejection sentence.

## Validation

- `yamlgraph graph lint examples/demos/research-route/graph.yaml` must pass.
- Smoke: the graph must load; a full run requires ANTHROPIC_API_KEY and is
  performed by the requesting session afterwards
  (tests/fixtures/fr890/clean-brief.md is a suitable brief).
- Do not modify nodes/research_tools.py, scripts/, or tests — already done.
