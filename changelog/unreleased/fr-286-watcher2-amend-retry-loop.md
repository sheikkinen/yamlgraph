---
type: feat
scope: watcher2
req: REQ-YG-310
---
- **FR-286 Watcher2 AMEND Retry Loop**: Implemented iterative revision cycle for AMEND verdicts instead of terminal failure. Judge feedback is now extracted and used to revise feature requests automatically, with up to 2 retry attempts before falling back to handle_failure. SPLIT verdicts remain terminal as before. Adds extract_judge_feedback(), run_revision_step(), handle_amend_verdict() functions and step-revise.yaml graph. (REQ-YG-310)