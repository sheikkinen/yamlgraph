---
type: feat
scope: countrangeclaim
req: REQ-YG-155
---
- **FR-166 CountRangeClaim Pydantic Model**: Replace loose `int` variables in count range verification with a validated `CountRangeClaim` Pydantic model. Inverted ranges (min > max) now fail at parse time. `VerificationViolation.details` populated with structured claim data. (REQ-YG-155)
