---
type: fix
scope: examples
req: REQ-YG-600
---
- **FR-812 Discord example launch fix**: `bot.py` bootstraps the repo root onto `sys.path` so the documented `python examples/discord_bot/bot.py` invocation works; AC-04 live guild acceptance log recorded in the example README. (REQ-YG-600)
