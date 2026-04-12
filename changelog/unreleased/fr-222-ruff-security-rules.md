---
type: feat
scope: lint
req: REQ-YG-220
---
- **FR-222 Ruff Security Rules**: Enabled flake8-bandit `S` ruleset in ruff configuration. 7 existing violations (S104, S602, S603, S607, S701) triaged and suppressed with documented noqa confessions (CONF-005–009, CONF-035–036). New security-sensitive code patterns are now automatically flagged at lint time. (REQ-YG-220)
