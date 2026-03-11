---
type: feat
scope: promote
req: REQ-YG-069
---
- **FR-110 Promote W014 → E007**: Undeclared `{state.X}` references now emit `severity="error"` with code `E007` (was `W014` warning). `yamlgraph graph lint` exits non-zero on undeclared state refs. (REQ-YG-069)
