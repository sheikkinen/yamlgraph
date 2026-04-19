---
type: feat
scope: verification
req: REQ-YG-154
---
- **FR-164 Verification Gate Pattern**: Add optional `verification` field to node definitions for silent failure detection. LLM states a falsifiable prediction before acting; runtime compares prediction against actual output using cosine similarity. Includes `VerificationConfig` schema, `verification.py` runtime, LLM node integration, linter checks, and demo example. (REQ-YG-064, REQ-YG-065)
