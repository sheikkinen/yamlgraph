---
type: feat
scope: examples
---
- **FR-736 WebLLM Demo Trace Capture**: the spike instrument now records the stimulus, not just the outcome — per-run `run-NN-trace.json` carries the full request/response pair (messages exactly as sent via a single-identifier build, response_format schema, params, finish_reason, usage); evidence.md prints the system prompt as sent (wire fidelity from the same object the request uses), and the tally gains `finish`, `input_chars`, and `input_head` columns so input distinctness and flood-vs-natural-stop are readable from the artifact alone. Standalone by product decision — no LangSmith, no upload, no network.
