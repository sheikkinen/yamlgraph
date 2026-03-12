---
type: feat
scope: ci
req: REQ-YG-185
---
- **FR-187 CI Dependency Security Scan**: Add `.github/workflows/security.yml` running `pip-audit --strict --desc` on every PR and version tag push. Produces `security` required status check for branch protection. Uses PyPA-endorsed OSV database — no API keys required. (REQ-YG-185)
