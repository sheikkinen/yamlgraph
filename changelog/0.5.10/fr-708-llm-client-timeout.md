---
type: fix
scope: llm
req: REQ-YG-539
---
- **FR-708 LLM Client Request Timeout**: every provider constructor in `llm_providers.py` now bounds provider work at the client boundary — explicit finite request timeout (default `LLM_REQUEST_TIMEOUT=30` s, env-overridable, garbage values raise) and `max_retries=2`, via the wrapper-correct parameter (`request_timeout` for ChatLiteLLM, `timeout` elsewhere); caller kwargs win. New `VERTEX_TRANSPORT=rest|grpc` knob plumbs `transport=` into the google/vertex constructors (both express and ADC branches) — REST honors timeouts via httpx where gRPC-from-Fly hung. A hung endpoint now fails within the timeout with the provider named (FR-705) instead of hanging forever and accumulating transport channels (Fly freeze RCA 2026-07-10). Completes the NC-361 chain: message (705) → witness (706) → wait (707) → work (708). (REQ-YG-539)
