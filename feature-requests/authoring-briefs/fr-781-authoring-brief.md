# Authoring brief: FR-781 file-hook demo graph

Create the governed graph artifacts for the macOS file-hook demo
(judged FR: feature-requests/FR-781-macos-file-hook-example.md,
judgement: feature-requests/FR-781-macos-file-hook-example.judgement.md,
scope D-2). The Python tools, hooks, fixture, and RED test suite
(tests/unit/test_fr781_file_hook.py) already exist — author ONLY:

1. `examples/demos/file-hook/graph.yaml`
2. `examples/demos/file-hook/prompts/describe_artwork.yaml`

## Graph contract (frozen by judgement — do not redesign)

- version "1.0", name file-hook-demo.
- State: `dir: str` (watched folder, passed via --var), `unpaired: list`,
  `results: list`.
- Tools (both `type: python`, module `examples.demos.file-hook.tools` —
  the python-map demo proves hyphenated module paths load):
  - `find_unpaired` → function `find_unpaired` (args: dir). Returns PNGs
    lacking an `.md` twin.
  - `process_artwork` → function `process_artwork`. Describes one PNG via
    the shared vision boundary and publishes fail-safe (gate lives in
    the tool: only confidence "high" writes `<safe-title>.md` + renames).
- Nodes:
  - `scan`: `type: tool_call`, tool `find_unpaired`,
    args `dir: "{state.dir}"` (state binding — FR-779 hygiene: whole-string
    bare placeholders are a defect), `state_key: unpaired`.
  - `process`: `type: map`, `over: "{state.unpaired}"`, `as: file`,
    `collect: results`, sub-node `type: python`, tool `process_artwork`,
    `state_key: result` (follow examples/demos/python-map/graph.yaml).
- Edges: START → scan → process → END.

## Prompt contract (prompts/describe_artwork.yaml)

Consumed by `tools.py::_load_instruction()` which reads the `template`
key — a plain instruction string (no variables). It is NOT executed as
an LLM prompt node; keep it a single `template:` field with `name` and
`description`. Content — the sheikkinen DeviantArt publishing style
(derived from the deviant-working julkaisuohje):

- Poetic, evocative English title (no filename echoes).
- 3–4 atmospheric paragraphs of myth-building prose describing the
  artwork's world, mood, and story — never a dry enumeration of visual
  elements.
- 8–12 lowercase keyword tags.
- One short in-character quote from the artwork's subject.
- End the description with the epigram: "Be Art. Be Unique."
- An honest confidence self-assessment: high | medium | low. Set high
  ONLY when the image is clearly legible and the analysis is grounded;
  anything uncertain must be medium or low (low/medium blocks
  publication — never invent a myth for an image you cannot read).

The structured output schema (title, description, tags, quote,
confidence) is enforced by the shared `ImageDescription` Pydantic model
in examples/shared/vision_tool.py — the prompt must ask for those
fields by name.

## Validation required (doctrine)

- `yamlgraph graph lint examples/demos/file-hook/graph.yaml` clean.
- Smoke: copy `examples/demos/file-hook/fixture.png` into a fresh tmp
  dir and run with PROVIDER=google:
  `yamlgraph graph run examples/demos/file-hook/graph.yaml --var dir=<tmpdir> --full`
  Expect one processed result; a second run must report zero unpaired
  (pairing no-op). Do NOT run against the committed fixture in place —
  the graph renames what it processes.
- These unit tests must pass afterward:
  `pytest tests/unit/test_fr781_file_hook.py -q --no-cov`
  (the process_artwork/graph tests currently fail only because the
  prompt + graph files are missing).

Out of scope: any edit to tools.py, hooks/, tests, yamlgraph/ core, or
the shared vision tool. If the contract cannot be met without touching
those, stop and report.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
