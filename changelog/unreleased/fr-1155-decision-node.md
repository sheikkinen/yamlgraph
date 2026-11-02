---
type: feat
scope: decision
req: REQ-YG-726
---
- **FR-1155 Decision-node primitive with calibration audit**: `type: decision` nodes ask typed questions (`noul`, `choice`, `score`) about a rendered state blob through a provider-agnostic decision-client factory and commit normalized Pydantic answers (probabilities; confidence on choice/score) that graph conditions branch on. Backends: deterministic `mock` (planted rules, keyless) and the vendor's LLM-backed `system_one_adapter` (optional extra `decision`, lazy import). The calibration-audit reducer computes a reliability table and ECE over labeled items as the documented operator onboarding gate for any real provider's confidence. (REQ-YG-726)
