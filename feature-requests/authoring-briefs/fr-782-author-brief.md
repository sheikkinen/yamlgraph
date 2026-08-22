# Task brief — FR-782 self-portrait example: graph + synthesis prompt

Author the two governed artifacts for the FR-782 self-portrait example:

- `examples/demos/self-portrait/graph.yaml`
- `examples/demos/self-portrait/prompts/synthesize_portrait.yaml`

Do NOT create, modify, or delete any other file (the Python tools,
fixture, tests, and README already exist and are out of scope).

## Context

The example extracts the user's people/topics/locations/contacts from a
local macOS PersonalizationPortrait SQLite database, resolves Wikidata
topic labels, and synthesizes an **agent-first** self-portrait. Personal
data egress is the central boundary: a deterministic payload file is
written and hashed BEFORE any provider call, an interrupt gate previews
it, and a verification node re-reads the file and proves byte-for-byte
identity before synthesis.

Governing feature request: `feature-requests/FR-782-user-self-portrait-example.md`
(read it — the frozen JSON contract and consent semantics live there).

## Existing tool module (already committed, do not modify)

`examples/demos/self-portrait/tools.py`, graph-relative
(`type: python`, `path: tools.py`). Each function takes the full state
dict and returns a partial state update:

| function | returns (state keys) |
|---|---|
| `prepare_run` | `db_path`, `output_dir`, `portrait_date`, `auto_approve` (normalized bool) |
| `extract_sources` | `extraction` |
| `enrich_topics` | `enriched` |
| `build_synthesis_payload` | `payload`, `consent`, `consent_summary` |
| `verify_consent` | `payload_json` (raises unless the payload file is byte-identical to the preview) |
| `render_portrait` | `outputs` (needs `portrait` + `payload` in state) |
| `render_extraction_only` | `outputs` (consent declined path) |

## Required graph shape

- `name: self-portrait`
- `checkpointer: {type: memory}` (the interrupt requires one)
- `prompts_relative: true`, `prompts_dir: prompts`
- `defaults`: provider `anthropic`, model `claude-sonnet-4-5`, temperature `0.3`
- State fields (all of them): `db_path: str`, `output_dir: str`,
  `portrait_date: str`, `auto_approve: bool`, `extraction: dict`,
  `enriched: dict`, `payload: dict`, `consent: dict`,
  `consent_summary: str`, `consent_answer: str`, `payload_json: str`,
  `portrait: dict`, `outputs: dict`
- Nodes, in this order:
  1. `prepare` — python, tool `prepare_run`
  2. `extract` — python, tool `extract_sources`
  3. `enrich` — python, tool `enrich_topics`
  4. `build_payload` — python, tool `build_synthesis_payload`
  5. `confirm_egress` — `type: interrupt`, `message: "{consent_summary}"`,
     `state_key: consent_prompt`, `resume_key: consent_answer`
  6. `verify_payload` — python, tool `verify_consent`
  7. `synthesize` — `type: llm`, `prompt: synthesize_portrait`,
     `state_key: portrait`, variables: `payload_json: "{state.payload_json}"`
  8. `render` — python, tool `render_portrait`
  9. `render_denied` — python, tool `render_extraction_only`
- Edges:
  - `START → prepare → extract → enrich → build_payload`
  - from `build_payload`: conditional — `auto_approve == true` goes to
    `verify_payload`; `auto_approve == false` goes to `confirm_egress`
  - from `confirm_egress`: conditional — `consent_answer == 'yes'` goes to
    `verify_payload`; otherwise (`consent_answer != 'yes'`) goes to
    `render_denied`
  - `verify_payload → synthesize → render → END`
  - `render_denied → END`

## Required prompt shape

`prompts/synthesize_portrait.yaml`, an inline-schema structured prompt:

- system: a portrait synthesizer writing FOR AN AI AGENT that will load
  the result as system context. Factual, evidence-grounded, no invention
  beyond the supplied JSON; say "unknown" rather than guessing. The data
  is the user's own device record, handed to the user's own agents.
- user: takes one variable `payload_json` — the exact JSON payload —
  and asks for the portrait sections.
- `schema` with `name: SelfPortrait` and exactly these fields:
  - `identity` (str) — who the user appears to be: languages, home base
  - `social_graph` (list[str]) — inner circle with the evidence for each
  - `expertise` (list[str]) — technical/professional/personal interests
  - `geography` (str) — home base and travel pattern
  - `rhythms` (str) — observable rhythms, or "unknown" when unsupported
  - `evolution` (str) — what is rising and what is fading (score decay)
  - `agent_briefing` (str) — written in second person TO a future agent:
    how to work with this user, what to assume, what never to re-ask
- Note in the user template that absent supplementary sources must be
  reported as unknown, never inferred.

## Validation to run

```bash
yamlgraph graph lint examples/demos/self-portrait/graph.yaml
yamlgraph graph validate examples/demos/self-portrait/graph.yaml
python -m pytest tests/unit/test_fr782_self_portrait.py -q --no-cov
```

A grounded fixture smoke run (real LLM, synthetic data) is run by the
requesting session afterwards — do not run it here.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
