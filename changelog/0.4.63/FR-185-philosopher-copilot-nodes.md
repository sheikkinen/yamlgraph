---
type: feat
scope: philosopher
req: REQ-YG-185
---
- **FR-185 Philosopher Copilot Nodes**: Migrate `analyze` and `reflect` nodes from `type: llm` to `type: copilot`. Add `Proposal`, `ProposalList`, `DiaryEntry` Pydantic models and `extract_json()` utility. Replace 4-way unwrap cascade with single CopilotResult → Pydantic parse path. (REQ-YG-185)
