---
type: feat
scope: append-only
req: REQ-YG-161
---
- **FR-178 Append-Only Capability Registry**: Replace hardcoded `CAPABILITIES` dict in `scripts/req_coverage.py` with YAML files under `capabilities/`. New capabilities are added as individual files, validated by `scripts/validate_capabilities.py` pre-commit hook. Eliminates merge conflicts on shared traceability artifacts. (REQ-YG-161)
