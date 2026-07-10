---
type: feat
scope: demos
req: REQ-YG-531
---
- **FR-700 Timeframe Recap Demo**: `examples/demos/recap/` answers "what changed in this repo since T?" for any git repository — deterministic `type: tool` git collection (portable `git -C`, capped, no reflog syntax, no silent fallbacks), Jinja2 file-kind partitioning in the template, and exactly one LLM judgement producing workstreams, orphan commits (no FR/issue reference; graph/prompt edits without changelog fragments), and hotspots. Mechanizes the Scripture's `changelog_first_diagnostic` cure. (REQ-YG-531)
