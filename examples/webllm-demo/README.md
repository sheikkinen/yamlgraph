# webllm-demo — prompt YAML → WebLLM `response_format` (FR-731)

Rung-1 spike of the browser ladder: proves a yamlgraph prompt with an
inline schema compiles **mechanically** to a WebLLM grammar-enforced
JSON contract — zero API key, zero server.

## What it does

`build.py` loads the reflexion critique prompt
(`examples/demos/reflexion/prompts/critique.yaml`), builds its Pydantic
model through `yamlgraph.schema_loader.build_pydantic_model`, and emits
`docs/demos/webllm/prompt.json`:

```json
{"name", "system", "user_template", "json_schema"}
```

Constraint fidelity is the point: `ge: 0.0 / le: 1.0` on `score`
arrives as `minimum / maximum` in the JSON Schema. No deployment
config rides the artifact — the model id is a constant in the page.

`docs/demos/webllm/index.html` (served by GitHub Pages) runs the
contract against WebLLM (`Llama-3.2-1B-Instruct-q4f16_1-MLC`) in-tab:
WebGPU capability gate, consent-gated ~0.7 GB weight download,
temperature 0, raw model output always rendered, schema violations
loud red.

## Usage

```bash
python examples/webllm-demo/build.py            # write the artifact
python examples/webllm-demo/build.py --check    # verify no drift
```

Rebuild on an unchanged prompt is a byte-level no-op (`sort_keys`
serialization) — prompt drift is visible in `git diff`.

## Scope

This demos a *prompt*, not a graph. The spike verdict is **schema
fidelity only** — semantic quality of the 1B model's critique is out
of scope. Tests: `tests/unit/test_fr731_webllm_build.py` (REQ-YG-562).
