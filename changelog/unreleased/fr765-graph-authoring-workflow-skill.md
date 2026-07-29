---
type: feat
scope: skills
req: REQ-YG-423
---
- **FR-765 Graph Authoring Workflow Skill**: New `.github/skills/graph-authoring/`
  workflow skill (SKILL.md + doctrine.md) turning graph creation into a repeatable
  agent procedure — precedent search, smallest-pattern selection, authoring via
  `author-graph`/`author-prompt`, mandatory `yamlgraph graph lint` + smoke
  validation with blocked-command honesty, artifact-closed delegation brief
  (never judge/review routes), and Chaplain escalation rules. Rejects the
  one-shot `examples/yamlgraph_gen` model (FR-763 `workspace_is_not_boundary`
  precedent). Round 2 adds the executable adapter route (judge-fr shape):
  `scripts/author.sh <task-brief.md>` launches a thin copilot-node adapter
  graph that reads the doctrine, authors and validates the files, and writes
  a parseable `tmp/draft-authoring-report.md` artifact verified by existence,
  never exit code. CAP-158/REQ-YG-423 extended; skill promotion tests
  upgraded from presence to substance checks. (REQ-YG-423)
