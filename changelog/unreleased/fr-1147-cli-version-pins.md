---
type: feat
scope: copilot
req: REQ-YG-641, REQ-YG-679
---
- **FR-1147 Remove CLI version pinning**: the `claude` and `opencode` copilot-node backends no longer accept exactly one vendor release. The per-invocation `--version` preflight now checks the banner shape — `X.Y.Z (Claude Code)` (REQ-YG-641) and `X.Y.Z` (REQ-YG-679), ASCII digits, full string — so a Claude Code or opencode auto-update no longer refuses every call. Foreign products, malformed banners, and non-zero exits still fail before auth/run, now naming the exit code, stdout, and stderr. Auth, environment stripping, argv, envelope, and event-state-machine contracts are unchanged; the `copilot` backend stays unpinned.
