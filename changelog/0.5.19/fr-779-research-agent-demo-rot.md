---
type: fix
scope: examples
req: REQ-YG-581
---
- **FR-779 Research-Agent Demo Rot**: Fixed bare `{query}`/`{scope}` bindings (model received literal placeholders and hallucinated topics) with `{state.*}` paths and state declarations; replaced the unconditional `validate_findings → synthesize_report` edge with a conditional gate so empty findings or low confidence terminate honestly without fabricating a report. Repo-wide demo binding-hygiene sweep test added (CAP-221). (REQ-YG-581)
