---
type: feat
scope: router
req: REQ-YG-271
---
- **FR-272 Router Node Race Candidates**: `router` nodes now accept an optional `candidates:` list (same schema as `race`). When present, the prompt is fired to all candidates concurrently; the first valid result drives routing resolution. Losers are cooperatively cancelled via asyncio. `provider:` + `candidates:` is a compile-time error. Timeout falls back to `default_route` (or raises if `on_error: fail`). `_race_winner` metadata recorded in state. Single-provider routers unchanged. (REQ-YG-271)
