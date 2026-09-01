---
type: feat
scope: skills
req: REQ-YG-636
---

- **FR-948 LAN Copilot delegation channel — scaffold**: `.github/skills/lan-delegate/`
  landed with `SKILL.md` (frozen scope contract per FR-948 judgement C-1..C-7),
  Pydantic `models.py` (19-value `DelegationPolicyStatus` closed enum + phase-invariant
  `LanDelegationResult` + `RemoteCopilotPrerequisites` + `resolve_status()` precedence
  resolver), and 10 typed pre-launch exception classes in `errors.py`
  (`DirtyLocalTreeError`, `MissingReconError`, `StaleReconError`,
  `ReconDisqualifyingFieldError`, `MissingCredentialError`, `UnsafeHostError`,
  `PromptFileError`, `UnsafeRunIdError`, `LocalPathCollisionError`,
  `RecursiveDelegationError`). (REQ-YG-636)
