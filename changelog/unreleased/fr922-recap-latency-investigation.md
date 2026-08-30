---
type: fix
scope: tests
req: REQ-YG-531
---
- **FR-922 Recap Latency Investigation**: Measured the recap bare-repo integration test across four controlled samples (12.95s–78.35s); the reported 283s did not reproduce. LangSmith child-run traces show 99.4% of wall time in the single `synthesize` LLM call and 0.25s across all deterministic nodes. The live REQ-YG-531 witness was kept rather than skipped. (REQ-YG-531)
