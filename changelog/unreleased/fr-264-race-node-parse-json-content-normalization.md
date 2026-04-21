---
type: feat
scope: race-node
req: REQ-YG-264
---
- **FR-264 Race Node parse_json & Content Normalization**: Race nodes now normalize `response.content` to string (handles Anthropic list-of-blocks, OpenAI string, None) and support `parse_json: true` for JSON extraction from LLM responses. Content normalization extracted to shared `yamlgraph/utils/content.py`. (REQ-YG-264)
