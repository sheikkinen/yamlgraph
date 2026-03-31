---
type: fix
scope: providers
req: REQ-YG-010
---
- **Fix Vertex AI Deprecation**: Migrate `provider: vertex` from deprecated `ChatVertexAI` (`langchain-google-vertexai`) to `ChatGoogleGenerativeAI(vertexai=True)` (`langchain-google-genai`). Eliminates deprecation warning and removes the `[vertex]` optional extra since `langchain-google-genai` is already a core dependency. (REQ-YG-010)
