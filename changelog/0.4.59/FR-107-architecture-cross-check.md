---
type: feat
scope: architecture
---
- **FR-107 Architecture Cross-Check** (ADR-001): `req_coverage.py --strict` now verifies all requirements exist in `ARCHITECTURE.md`
  - Detects phantom requirements: IDs in `ALL_REQS` missing from architecture table
  - Warning mode (no `--strict`): prints warning, exits zero
  - Strict mode: exits non-zero on undocumented requirements
  - Fixed REQ-YG-105 gap: added to CAP-30 table in `ARCHITECTURE.md`
