# Feature Request: FR-730 WebLLM Browser Prompt Demo — Rung-1 Spike

**Priority:** LOW
**Type:** Spike / Example
**Status:** Proposed
**Effort:** 0.5–1 day
**Requested:** 2026-07-14
**Spawned by:** docs/2026-07-14-research-browser-llm-webgpu.md — recommendation
"fund only the first rung": one yamlgraph prompt with inline schema running
against WebLLM in the visitor's browser, zero API key, zero server.
**Related:** FR-723 (reflexion demo lineage), FR-729 (landing page — a live
demo is its natural neighbor), research Seeds 1–2 (skill export --format
webllm; landing page as runtime), CAP-04 (prompt execution), Pages fix
013ff5ae (the site this ships on)

## Summary

A static page, served by the existing GitHub Pages site, that runs the
**reflexion critique prompt** (`examples/demos/reflexion/prompts/critique.yaml`
— inline schema: score/feedback/issues/should_refine with ge/le constraints)
against **WebLLM** (`Llama-3.2-1B-Instruct-q4f16_1-MLC`, ~0.7 GB q4) with
**grammar-enforced JSON schema output**. The user pastes an essay paragraph;
the browser returns schema-valid Critique JSON. No key, no server, no
telemetry.

The spike validates exactly one claim: **a yamlgraph prompt YAML (template +
inline schema) compiles mechanically to a WebLLM `response_format`** — the
load-bearing assumption under research Seeds 1–2 and the browser ladder's
rungs 3–4.

## Value Statement

First "try it without an API key" surface for the project; and a
proven-or-killed compile path before any skill-export or runtime work is
even judged.

## Proposed Solution

### 1. Compiler: `examples/webllm-demo/build.py`

Spike-local script (imports the installed `yamlgraph` package — an example
consuming the library, not new framework surface):

- loads `critique.yaml`, builds the Pydantic model via the existing
  `schema_loader` inline-schema path, emits `prompt.json`:
  `{name, system, user_template, json_schema, model_id}`
  where `json_schema = Model.model_json_schema()` (constraints included).
- Deterministic and idempotent; the artifact is committed. Re-running on an
  unchanged prompt is a no-op (drift visible in `git diff`).

### 2. Page: `docs/demos/webllm/index.html`

- Vanilla JS ESM, `import * as webllm from "https://esm.run/@mlc-ai/web-llm"`
  (CDN precedent from WebLLM docs; no build toolchain, no npm).
- **Capability gate first:** `navigator.gpu` check → honest unsupported
  message naming the browsers that work (research doc matrix).
- **Consent before weight download:** show model id + ~size; load only on
  click; `initProgressCallback` progress bar; second visit hits the Cache
  API.
- Textarea (essay paragraph) → chat completion with
  `response_format: {type: "json_object", schema: <from prompt.json>}`,
  temperature 0 → render parsed fields AND the raw JSON (read the raw
  output, always).
- Client-side shape check mirroring the schema (required fields present,
  `0 ≤ score ≤ 1`) — a failed check renders as a loud red failure, never
  silently prettified (no hedging).

### 3. Evidence artifact

`docs/demos/webllm/spike-evidence.md`: the raw JSON returned by ≥ 3 real
in-browser runs on distinct inputs (pasted verbatim — the FR's raw-output
read), browser/OS/GPU noted, plus observed first-load time and tokens/s.

### Kill criterion (binding)

If schema-valid JSON fails in more than 2 of 10 manual runs at temperature
0, the spike is recorded FAILED in this FR with the raw outputs attached,
and Seeds 1–2 are re-judged against a larger model or killed. A failed
spike that is honestly recorded is a success of the method.

### Out of scope (purge list)

- Model picker, chat history, streaming UI (single-shot completion only).
- Graph execution of any kind (this demos a *prompt*, not a graph).
- `skill export --format webllm` integration (rung 3 — separate FR, only
  if this spike passes).
- Service worker persistence, telemetry, analytics.
- Firefox/Safari workarounds beyond the honest gate message.

## Acceptance Criteria

- [ ] AC-01 RED — unit test: `build.py` on `critique.yaml` emits
      `prompt.json` whose json_schema requires score/feedback fields,
      carries `ge:0/le:1` as `minimum/maximum` on score, and whose
      user_template preserves `{iteration}`/`{content}` placeholders
      verbatim.
- [ ] AC-02 — artifact committed; rebuild is a no-op on unchanged prompt
      (idempotence test).
- [ ] AC-03 — page gates on `navigator.gpu` and defers the weight download
      to an explicit click with size disclosure (source-inspection test:
      no fetch of model artifacts before user gesture).
- [ ] AC-04 — spike-evidence.md with ≥ 3 verbatim raw model outputs,
      schema-valid, from a real browser run on the deployed Pages site;
      kill criterion evaluated and verdict written into this FR.
- [ ] AC-05 — changelog fragment; REQ under CAP-04 (prompt inline-schema →
      JSON Schema export path is the tested framework behavior); diary
      reflection; research doc updated with the spike verdict (the ladder
      doc must not claim an unproven rung).

## Alternatives Considered

- **transformers.js instead of WebLLM:** no grammar-enforced JSON — the
  spike's whole point is schema fidelity; rejected for rung 1.
- **Bundler + npm toolchain:** adds a build system to a repo that has none
  for JS; CDN ESM import is the documented WebLLM path; rejected.
- **Host outside docs/:** Pages already serves docs/ and was fixed today;
  a second hosting surface is entropy; rejected.
- **Qwen3-1.7B for quality:** 2× the download for a spike whose question
  is compile-path validity, not model quality; if the 1B fails the kill
  criterion, the re-judgement considers it.
