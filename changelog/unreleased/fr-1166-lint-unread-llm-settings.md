---
type: feat
scope: linter
req: REQ-YG-730
---
- **FR-1166 Lint LLM settings written where yamlgraph never reads them**: `yamlgraph graph lint` warns with W072 when `thinking_budget`, `temperature`, `max_tokens` or `effort` sits in graph `metadata:` or in the `metadata:` of a prompt a node references (it is never read there; move it to `defaults.<key>` or the node). It warns with W073 when a `race` or router-race candidate carries any key other than `provider` / `model`, naming the node, candidate index and key, with a fix that matches what races actually forward. The setting names are declared once in `yamlgraph/constants.py` (`LLMSetting`). Runtime behaviour is unchanged. (REQ-YG-730)
