---
type: feat
scope: examples
req: REQ-YG-627
---
- **FR-901 Shared SMTP Email Tool**: `examples/shared/smtp_email.py` plus an FR-768 manifest send email over SMTP for any graph that has produced text a human should receive — transport only, with no opinion about what it carries. Config is validated before any socket opens, credentials are read at call time (not at import, the defect in the Resend node it supersedes), CR/LF header injection is refused, and every failure raises rather than returning a success-shaped result. (REQ-YG-627)
