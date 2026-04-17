---
type: fix
scope: vertex
req: REQ-YG-010
---
- **FR-229 Vertex Express mask GOOGLE_API_KEY**: Added four unit tests condemning the root cause where `GOOGLE_API_KEY` in `os.environ` would override the explicit `google_api_key` kwarg during Vertex Express construction; verifies the fix from commit 557b108 is correctly guarded by `_masked_env`. (REQ-YG-010)
