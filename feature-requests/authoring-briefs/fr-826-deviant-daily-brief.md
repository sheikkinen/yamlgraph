# Task Brief: deviant-daily pipeline graph (FR-826, AC-03)

Author the YAMLGraph artifacts for the `deviant-daily` repo — a daily
DeviantArt auto-publish pipeline. FR-826 R-1 freezes this execution
surface: the graph IS the orchestration layer; Python tools exist only
for side effects and are ALREADY IMPLEMENTED AND TESTED (46 green
tests). Do not modify any Python file.

## Target directory (author files here, absolute path)

`/Users/sheikki/Documents/src/deviant-daily/`

Artifacts to author:
1. `/Users/sheikki/Documents/src/deviant-daily/graph.yaml`
2. `/Users/sheikki/Documents/src/deviant-daily/prompts/describe_post.yaml`

## Pipeline (draw → generate → describe → gate → publish)

All node tools are Python functions in `tools/steps.py` of the target
repo (module `tools.steps` — the workflow runs from the repo root, so
plain module paths resolve). Their exact signatures:

- `draw_step(date: str) -> dict` — keys: prompt, source_file, resumed,
  status, date, done. `done=True` means today is already
  published/skipped → the graph must route straight to END
  (idempotent rerun, AC-16).
- `generate_step(prompt: str, date: str) -> dict` — keys: model_name,
  image_path.
- `describe_step(image_path: str, prompt: str) -> dict` — raw describe
  output for the gate.
- `gate_step(description: dict, date: str, prompt: str, source_file: str)
  -> dict` — keys: publish (bool), and either post (dict) or reason.
  `publish=False` → route to END (the skip ledger entry is already
  committed inside the tool).
- `publish_step(post: dict, image_path: str, date: str, prompt: str,
  source_file: str, model_name: str) -> dict` — keys: url, itemid.

## Graph requirements

- `version: "1.0"`, name `deviant-daily`, a one-line description
  naming FR-826.
- `state`: `date: str` (input var, may be empty → tool defaults to
  today UTC), plus one state key per node result (use `any` for
  dicts).
- Five `tool_call` nodes wired to the five functions above, args
  drawn from state as per the signatures (e.g. prompt is
  `{state.drawn.prompt}`, image_path is `{state.generated.image_path}`).
- Conditional routing:
  - after draw: `drawn.done` true → END, else → generate
  - after gate: `gate.publish` true → publish, else → END
- No LLM nodes: the describe LLM call happens inside `describe_step`
  (vision + structured output), which reads the prompt artifact below.
- No checkpointer, no map, no subgraphs — linear with two branches.

## Prompt artifact: prompts/describe_post.yaml

Fields: `name: describe_post`, `description`, `template`. It is
consumed by `tools/vision.py` via `yaml.safe_load(...)["template"]`
with a literal `{original_prompt}` placeholder substituted by Python —
NOT executed as a yamlgraph prompt, so no schema block is needed.

Template content contract (precedent:
`examples/demos/file-hook/prompts/describe_artwork.yaml`, the
sheikkinen mythic voice — adapt, do not copy verbatim):

- Input framing: the image is attached; the original generation
  prompt is: `{original_prompt}` (prompt states intent, image states
  outcome — ground the prose in what is VISIBLE, use the prompt only
  as intent context).
- Structured fields to return (must match this exact field list —
  the Pydantic model `tools.gate.PostDescription` validates them):
  - `title`: poetic, evocative English title; never echo the prompt.
  - `paragraphs`: list of 3-4 atmospheric myth-building paragraphs;
    the FINAL paragraph must end with the exact epigram
    "Be Art. Be Unique."
  - `quote`: one short in-character quote from the artwork's world.
  - `tags`: 8-10 lowercase tags, `[a-z0-9_]+` only (underscores, no
    hyphens, no spaces, no hash marks).
  - `confidence`: exactly one of high | medium | low; high ONLY when
    the image is clearly legible and everything is grounded in
    visible evidence — medium/low gate-skips the day.
  - `mature`: boolean, judged from the IMAGE per DeviantArt policy.
  - `mature_level`: strict | moderate, ONLY when mature=true, else null.
  - `mature_classification`: list from exactly {nudity, sexual, gore,
    language, ideology}, ONLY when mature=true, else empty list.
  - Content DeviantArt forbids outright must be reflected as
    confidence=low (the gate skips it) — never described around.

## Validation contract

- `yamlgraph graph lint <target>/graph.yaml` must pass.
- Smoke: a REAL run performs Replicate generation and a LIVE
  DeviantArt publish — forbidden at authoring time. Record this in
  the report's Blocked validation section: live smoke is deferred to
  the FR-826 AC-14 workflow_dispatch witness. Structural validation
  (`yamlgraph graph info` / compile) should be run instead; note that
  `tools.steps` imports resolve only from the target repo root
  (run info/lint from `/Users/sheikki/Documents/src/deviant-daily`).

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
