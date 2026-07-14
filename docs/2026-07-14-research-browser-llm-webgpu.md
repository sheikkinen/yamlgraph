# Research: Small LLMs in the Browser (WebGPU) — Landscape 2026-07

**Date:** 2026-07-14
**Status:** Research note (no FR attached; seeds at the end)
**Method:** Primary sources fetched 2026-07-14 — WebLLM README/site (v0.2.84),
transformers.js docs, caniuse WebGPU (June 2026 usage data). Numbers marked
~approximate are ballparks from public benchmarks, not measured here.

## Question

Can a useful LLM run entirely client-side in a browser tab on consumer
GPUs — and what would that offer this repo (zero-API-key demos, private
inference, offline pipelines)?

## Answer in one paragraph

Yes, for models up to ~4B parameters at 4-bit quantization. Two mature
runtimes dominate: **WebLLM** (MLC/TVM, WebGPU-only, OpenAI-compatible API,
grammar-enforced JSON mode) and **transformers.js** (ONNX Runtime, WASM-CPU
default with `device: 'webgpu'` opt-in, 100+ architectures incl. ASR/TTS/
embeddings). WebGPU sits at ~85% global availability (June 2026) but is
NOT yet universal: full on Chrome/Edge 113+ and iOS 26 Safari; partial on
macOS Safari (26 Tahoe+) and Firefox (Windows + macOS-26-AS only); off by
default on Linux Chrome. The practical constraints are model download size
(300 MB–2.5 GB) and first-load time, not inference speed.

## Runtimes

### WebLLM (`@mlc-ai/web-llm`, v0.2.84, Apache-2.0, ~18k stars)

- **Stack:** MLC-LLM / Apache TVM compiled to WASM + WebGPU compute
  shaders. Paper: arXiv 2412.15803.
- **API:** OpenAI-compatible (`engine.chat.completions.create`), streaming,
  seeding, logit control.
- **Structured output:** state-of-the-art **JSON mode with custom JSON
  schema**, enforced in the WASM grammar layer — not prompt-begging. This
  is the standout feature for us (Commandment 5: outputs through Pydantic;
  the browser equivalent exists here and only here).
- **Function calling:** WIP/preliminary.
- **Models:** prebuilt registry (`prebuiltAppConfig.model_list`) — Llama 3.x,
  Phi 3, Gemma, Mistral 7B, Qwen 0.5B–7B, Hermes variants; custom models
  via MLC compile flow (`model` weights URL + `model_lib` WASM).
- **Weights caching:** Cache API (default), IndexedDB, OPFS, experimental
  cross-origin storage — second load is instant, first load is the cost.
- **Integrity:** optional SRI hashes per artifact (config/wasm/tokenizer).
- **Threading:** Web Worker / Service Worker engines (model survives page
  navigations); Chrome extension support.
- **Limitation:** WebGPU required — no CPU fallback. No WebGPU = no WebLLM.

### transformers.js (`@huggingface/transformers`)

- **Stack:** ONNX Runtime Web. **WASM CPU by default** (runs everywhere),
  `device: 'webgpu'` opt-in (docs still label WebGPU "experimental").
- **dtype:** `fp32` (WebGPU default), `fp16`, `q8` (WASM default), `q4`.
- **Scope:** far beyond chat — Whisper/Moonshine ASR, TTS (StyleTTS2,
  Supertonic), embeddings, vision, background removal, zero-shot
  classification. Text-gen arch list is current: Qwen3, Gemma 3/3n,
  SmolLM3, LFM2, Phi-3, Llama, ModernBERT, etc.
- **Structured output:** nothing grammar-enforced; JSON is prompt+parse.
- **Fit:** the right tool when the task is a pipeline *component*
  (embed, transcribe, classify) or when CPU fallback matters; WebLLM is
  the right tool when the task is chat/structured generation on GPU.

### Others (surveyed, not primary)

- **wllama** — llama.cpp compiled to WASM; CPU-only, GGUF directly, slower
  but zero WebGPU dependency. Niche: guaranteed-everywhere small models.
- **MediaPipe LLM Inference API** (Google) — Gemma-focused, mobile-web bias.
- **Chrome built-in Prompt API (Gemini Nano)** — model ships with the
  browser (no download), but Chrome-only, model not chooseable, API still
  moving. Watch, don't build on.

## Model landscape for ≤ browser scale (2026-07)

| Model | Params | q4 download | Notes |
|---|---|---|---|
| Qwen3 0.6B | 0.6B | ~0.4 GB | current best sub-1B generalist; thinking-mode toggle |
| Gemma 3 270M / 1B | 0.27–1B | 0.2–0.7 GB | 270M is fine-tune bait, 1B usable chat |
| Llama 3.2 1B / 3B | 1–3B | 0.7–1.9 GB | WebLLM prebuilt (`Llama-3.2-1B-Instruct-q4f16_1-MLC`) |
| SmolLM3 | 3B | ~1.8 GB | HF, multilingual, long-context, fully open recipe |
| Qwen3 1.7B / 4B | 1.7–4B | 1.1–2.3 GB | 4B ≈ old 7B quality; upper edge of comfortable browser delivery |
| Phi-4-mini | 3.8B | ~2.2 GB | strong reasoning per byte |
| LFM2 | 0.35–2.6B | 0.2–1.5 GB | hybrid conv/attention, tuned for on-device latency |
| Mistral 7B class | 7B | ~4.2 GB | works on 16 GB unified-memory Macs; too heavy as a default |

Rule of thumb: q4 weights ≈ **0.55–0.6 GB per B params**, plus KV cache
(context-dependent, hundreds of MB at 8k+). Throughput on Apple-silicon
laptops: ~70–100 tok/s at 1B, ~30–50 at 3–4B, ~15–25 at 7–8B
(~approximate; measure before promising).

## WebGPU availability (caniuse, June 2026 usage)

| Browser | Status |
|---|---|
| Chrome/Edge 113+ desktop | ✅ default (**except Linux** — flag required) |
| Chrome Android | ✅ |
| Safari iOS 26+ | ✅ |
| Safari macOS 26 (Tahoe)+ | 🟡 default only on macOS 26+ |
| Firefox 141+ | 🟡 Windows default; macOS-26 Apple Silicon from 145+; Android ❌ |
| Global | **~85%** of page loads |

Consequence: any browser-LLM feature needs a capability gate
(`navigator.gpu` check) and an honest fallback message — or
transformers.js WASM-CPU fallback for small components.

## Hard constraints (the part demos hide)

1. **First-load download:** 0.4–2.3 GB before the first token. Caching
   (Cache API/OPFS) makes run 2 instant, but run 1 needs progress UI and
   user consent (mobile data!).
2. **Memory:** model + KV cache lives in GPU/unified memory; 8 GB devices
   cap out around 3–4B q4 with modest context.
3. **Cross-origin isolation:** multithreaded WASM (transformers.js CPU
   path) wants COOP/COEP headers; GitHub Pages can't set headers —
   single-thread fallback works but is slower.
4. **No CPU fallback in WebLLM**; no grammar-JSON in transformers.js —
   pick your poison per use case.
5. **Quality floor:** sub-4B models handle classification, extraction,
   summarization, template-following well; multi-step agentic reasoning
   and tool orchestration remain unreliable at this scale (route them
   server-side).

## Relevance to yamlgraph

- **Zero-key demos:** a static GitHub Pages demo running a real yamlgraph
  prompt (e.g. the reflexion critique step) against WebLLM in the visitor's
  browser would be the first "try it without an API key" surface. The
  landing page (FR-729 territory) could carry it.
- **Structured output symmetry:** WebLLM's schema-enforced JSON mode is the
  browser twin of our inline `schema:` blocks — a `prompts/*.yaml` template
  + schema could compile to a WebLLM `response_format` mechanically. The
  three-layer doctrine survives intact: YAML logic, JS presentation,
  browser tool side-effects.
- **Provider angle:** a `provider: webllm` makes no sense server-side
  (Python), but an exported *skill* (`yamlgraph skill export`) targeting a
  JS/browser runtime is a plausible long-range direction — the graph YAML
  is runtime-agnostic; only the executor is Python.
- **Not relevant yet:** running whole graphs client-side (checkpointers,
  map fan-out, tools are Python-bound). Don't confuse a demo surface with
  a port.

## Recommendations

1. **Prototype (0.5 day):** static page + WebLLM + `Qwen3-1.7B` or
   `Llama-3.2-1B` q4f16, one yamlgraph prompt with inline schema rendered
   to `response_format`. Success = valid Pydantic-shape JSON in-browser,
   no server.
2. **Pick WebLLM for generation, transformers.js for components** (ASR,
   embeddings) — don't force one runtime to do both jobs.
3. **Gate on `navigator.gpu`** and show download size before fetching
   weights; cache via OPFS.
4. Re-check Firefox/Safari defaults quarterly — the 🟡 cells above are the
   moving parts.

## Seeds

- **Seed 1:** `yamlgraph skill export --format webllm` — compile a prompt
  YAML (template + inline schema) into a self-contained browser demo page.
  Would make every `examples/demos/*` prompt a zero-key playable artifact.
- **Seed 2:** the landing page's "Start Building in Minutes" section could
  *be* the runtime: type a topic, watch a 1B model run the hello graph
  in-tab. Marketing that is also a conformance test of prompt portability.
- **Seed 3:** icpc-2-rfe-style classification at 0.6–1.7B in-browser —
  is a q4 Qwen3-1.7B good enough for the RFE cluster step? A crosscheck
  harness (FR-725 pattern) could answer this without any server cost.

## Reflection: could yamlgraph itself run in the browser?

*(Appended 2026-07-14, same day.)*

### The framing that decides the answer

yamlgraph is two artifacts with opposite portability:

1. **The contract** — graph YAML + prompt YAML + inline schemas. Pure
   data, runtime-agnostic, machine-defined (`schema export`, FR-009).
   Trivially portable.
2. **The engine** — Python: LangGraph compilation, executor,
   checkpointers, tools. Not portable, and not worth chasing.

Scripture already states the asymmetry (`constraint_over_code`: "the
constraint is irreplaceable, the code is regenerable"). A browser story
is a second *regeneration* of the same contract — never a port.

### Four paths, ascending cost

**Path 1 — browser as presentation layer (exists today).**
FastAPI + `run_graph_streaming_native` + HTMX is the shipped NPC pattern.
The browser renders; Python executes. The boring, correct answer for
products.

**Path 2 — authoring playground (cheap; portability already certified).**
Two subsystems are *contractually* browser-safe, by gates written for
other reasons:

- the **linter** — the `linter-llm-free` import-linter contract
  guarantees no executor/LLM/network dependency;
- **mermaid_export** (FR-723) — pure stdlib+yaml by acceptance criterion.

Both run under Pyodide unmodified. A static page: paste graph YAML → lint
findings + rendered map. No new architecture. Insight worth keeping: the
enforcement contracts double as **portability certificates** — a module
whose import boundary is gated is a module whose deployment surface is
known.

**Path 3 — single-prompt demos via WebLLM (Seed 1 above).**
Prompt template + inline schema → WebLLM `response_format` is a
mechanical compile; grammar-enforced JSON is the browser twin of
Commandment 5. Demos *prompts*, not graphs.

**Path 4 — a micro-runtime for a declared subset (the honest "graphs
in browser").** Node-type triage:

| Portable naturally | Portable with work | Not portable |
|---|---|---|
| `llm`, `router` (WebLLM) | `python` (→ JS callables) | `tool`/shell (sandbox) |
| `map` = `Promise.all`, `race` = `Promise.race` | checkpointing (OPFS/IndexedDB) | `copilot`, `a2a` |
| `interrupt` — *more* natural in a browser than a CLI | `subgraph` | |
| expression routing + loop limits (small grammar) | | |

The runtime is small (~hundreds of lines of TS) because the semantics are
frozen in YAML and 4,900 tests. The real cost is **conformance**: a second
implementation drifts unless gated. The cure is already built: run the
same fixture graphs in both runtimes and diff their route.jsonl with
`graph export --diff` — FR-723's route log is accidentally a
runtime-independent execution trace format, and the empty diff is the
cross-runtime witness.

### The trap to name

`framework_costume` in reverse: claiming "yamlgraph runs in the browser"
when a *subset* runs. The doctrine-compliant claim is capability-scoped —
a `browser-safe` lint profile that verifies a graph uses only the portable
subset. Generate-or-gate the claim; never hand-write it (the FR-729
lesson, applied prospectively).

### Verdict

Yes — as a ladder, not a leap. Path 1 exists; Path 2 is nearly free and
useful now; Path 3 is a small FR; Path 4 waits for a second consumer
(NC-372's graduation criterion).

- **Seed 4:** Pyodide playground page — lint + mermaid render of pasted
  graph YAML; the two contractually-pure modules are the MVP.
- **Seed 5:** `browser-safe` lint profile — mechanical verification that
  a graph uses only the portable node subset; prerequisite for ever
  claiming Path 4.
- **Seed 6:** cross-runtime conformance = same fixtures, both runtimes,
  `graph export --diff` on their route logs; adopt before the first line
  of any JS runtime is written.
