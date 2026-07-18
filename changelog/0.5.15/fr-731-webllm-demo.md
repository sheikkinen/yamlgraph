---
type: feat
scope: examples
req: REQ-YG-562
---
- **FR-731 WebLLM Browser Prompt Demo (rung-1 spike)**: `examples/webllm-demo/build.py` compiles the reflexion critique prompt (native inline schema) to `docs/demos/webllm/prompt.json` — constraint fidelity witnessed (`ge/le` → `minimum/maximum`), deterministic serialization, no deployment config in the artifact. `docs/demos/webllm/index.html` runs it against WebLLM in-tab on GitHub Pages: WebGPU gate, consent-gated 0.7 GB weight download, grammar-enforced JSON at temperature 0, raw output always rendered, shape failures loud. (REQ-YG-562)
