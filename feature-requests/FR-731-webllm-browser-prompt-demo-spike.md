# Feature Request: FR-731 WebLLM Browser Prompt Demo — Rung-1 Spike

**Priority:** LOW
**Type:** Spike / Example
**Status:** Judged
**Effort:** 0.5–1 day
**Requested:** 2026-07-14
**Judged:** 2026-07-14 — scope frozen; renumbered from FR-730 (ID collision, recurrence #3 of the allocation race — FR-730-icpc2 landed on origin first, ec98d311 15:44:44 vs 0b809763 15:45:44)
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

- [x] AC-01 RED — unit test: `build.py` on `critique.yaml` emits
      `prompt.json` whose json_schema requires score/feedback fields,
      carries `ge:0/le:1` as `minimum/maximum` on score, and whose
      user_template preserves `{iteration}`/`{content}` placeholders
      verbatim.
- [x] AC-02 — artifact committed; rebuild is a no-op on unchanged prompt
      (idempotence test).
- [x] AC-03 — page gates on `navigator.gpu` and defers the weight download
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

## Judgement (2026-07-14)

**Verdict: APPROVED — with 6 findings.** Prompt shape verified against
`examples/demos/reflexion/prompts/critique.yaml` (score ge/le present,
`{iteration}`/`{content}` placeholders confirmed); CAP-04 REQ inventory
and max REQ id (555) read before pinning.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F0 | **ID collision** — FR-730 was already claimed by icpc2-chapter-inflation (landed origin first, one commit earlier). Recurrence #3 of the allocation race; the validate-capabilities gate covers CAP/REQ ids but not FR ids | Renumbered to **FR-731** at judgement. No external cross-refs existed (research doc, changelog: none). Commit `0b809763`'s message says FR-730 — the rename commit message must note the supersession so `git log --grep=FR-730` stays interpretable |
| F1 | AC-04's kill criterion demands 10 manual runs but the evidence artifact only ≥3 verbatim outputs — the verdict would rest on 7 unrecorded runs | ≥3 verbatim FULL raw outputs stays, but the kill-criterion tally must enumerate **all 10 runs** in spike-evidence.md as one line each (input id, schema-valid y/n, score). A verdict over unrecorded runs is the `gate_checks_shape_not_substance` trap |
| F2 | AC-05 claims a REQ under CAP-04 for "inline-schema → JSON Schema export", but the tested behavior is `Model.model_json_schema()` — Pydantic's own serialization. The framework behavior actually exercised is `load_schema_from_yaml` building a model whose constraints survive to JSON Schema (`ge/le` → `minimum/maximum`) | REQ is justified but must be worded as **constraint fidelity through the inline-schema path** (schema_loader → model → json_schema round-trip preserves ge/le/defaults/required), not as a new "export" capability. New REQ id ≥ 556, verified free at enforce (same race, same check) |
| F3 | `build.py` emits `model_id` into prompt.json, but model choice is a page concern (the compiler knows nothing about WebLLM models); coupling it into the compiled artifact smuggles deployment config into the compile path the spike exists to validate | `prompt.json` carries **only** `{name, system, user_template, json_schema}`. `model_id` is a constant in `index.html`. The artifact then witnesses exactly the claim under test: prompt YAML → portable JSON, nothing else |
| F4 | AC-03's "source-inspection test" is unenforceable as worded (inspection by whom?) | Pin: a unit test greps `index.html` asserting the WebLLM engine-creation call is lexically inside the click handler / behind the consent gate, and that no `fetch(`/model-URL literal sits at module top level. Crude but mechanical — matches the spike's weight class |
| F5 | Idempotence AC-02 ("rebuild is a no-op") requires deterministic serialization — `model_json_schema()` key order is stable in practice but the FR shouldn't rest on "in practice" | build.py writes `json.dumps(..., sort_keys=True, indent=2)`; the idempotence test is then a byte-equality check, and prompt-drift diffs stay minimal |
| F6 | Temperature 0 + q4 1B model: the kill criterion measures grammar enforcement, not model competence — a schema-valid but semantically absurd critique (score 0.97 for gibberish) still PASSES rung 1 | Correct and intentional; pin it explicitly: rung-1 verdict is **schema fidelity only**. spike-evidence.md must carry one sentence acknowledging semantic quality is out of scope, so the research-doc update cannot oversell the rung |

**Scope frozen.** Purge list stands as written (no model picker, no
streaming, no graph execution, no skill-export). Enforce order: AC-01
RED first (build.py compiler test), then AC-02/AC-03 tests, then page,
then the deployed-site evidence run, then AC-05 paperwork.

## Implementation (2026-07-15)

Enforced per judgement. RED fd02a782 (14 condemning tests, REQ-YG-562
registered in CAP-04); GREEN this commit.

- `examples/webllm-demo/build.py` — loads critique.yaml, builds the
  model via `build_pydantic_model`, emits
  `{name, system, user_template, json_schema}` (F3: no model_id);
  `serialize()` uses `sort_keys=True` (F5); `--check` mode verifies
  drift for CI/pre-commit use.
- `docs/demos/webllm/prompt.json` — committed artifact; raw read
  confirmed `minimum: 0.0` / `maximum: 1.0` on score and defaults on
  issues/should_refine before any test asserted it.
- `docs/demos/webllm/index.html` — vanilla ESM, esm.run CDN import;
  `navigator.gpu` gate with honest browser list; consent click owns
  the only `CreateMLCEngine` call (F4 witnessed by lexical test);
  MODEL_ID constant page-side (F3); temperature 0;
  `response_format: {type: json_object, schema}` from the artifact;
  raw output rendered always (F6 disclaimer in the page header);
  shape failures render loud red, never prettified.

AC-04 remains: deployed-site run, 10-run tally (F1), verdict into
this FR, research-doc update. The page ships dark until Pages
deploys it; no framework surface changed.
