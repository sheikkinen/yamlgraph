---
type: feat
scope: req-audit
req: REQ-YG-609
---
- **FR-860 Scripted Witness-Audit Runner**: `scripts/req_audit.sh` runs the
  FR-851 audit end to end — record (full sequential `COVERAGE_CORE=ctrace`
  framework suite), construct, audit graph, report — fail-fast with per-phase
  logs, a frozen-schema `run-manifest.json` (git SHA, dirty flag, instrument
  line, provider/model, per-phase command/exit/log), and provenance embedded
  in the report header via `req_audit_report.py --run-manifest`. The FR-850
  coverage boundary's hard refusal propagates under `--skip-record`.
  (REQ-YG-609)
