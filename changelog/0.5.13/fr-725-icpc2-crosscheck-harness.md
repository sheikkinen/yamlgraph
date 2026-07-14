---
type: feat
scope: examples
req: REQ-YG-554
---
- **FR-725 ICPC-2 Labeled Crosscheck Harness (Phase 3)**: six labeled fixtures (the read field runs encoded as rank-tolerant labels with rationales and `valid_for_components`) plus an LLM-free evaluation harness over the per-run archive — `primary_any_of`, `must_include` (any surfaced slot), `must_not_include` (primary/secondary), tri-state low-confidence; loud component-coverage skips; basename-only attribution (stdin never attributed); raw k-of-n agreement with no significance computation. `--runs N` generates fresh runs (slow, key-guarded). Advisory report, no CI gate — baseline numbers documented in the FR gate FR-726. (REQ-YG-554)
