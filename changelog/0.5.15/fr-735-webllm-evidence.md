---
type: feat
scope: examples
---
- **FR-735 WebLLM Demo Evidence Ergonomics**: the FR-731 spike page is now self-evidencing — structured `webllm-load`/`webllm-run` console records, per-run byte-fidelity **Save raw output** downloads (single raw read flows to both Blob and DOM), and a per-session **Download evidence.md** in the FR-731 F1 tally shape with computed `failures: N/M` kill-criterion arithmetic and honest short-session labeling. tok/s never fabricated: usage field → computed proxy labeled `tok/s*` → blank. (Tests under REQ-YG-562, whose primary fragment claim stays with FR-731 — the cross-wiring gate enforces one claimant per REQ.)
