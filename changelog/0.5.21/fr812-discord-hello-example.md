---
type: feat
scope: examples
req: REQ-YG-600
---
- **FR-812 Discord `/hello` Slash-Command Example**: `examples/discord_bot/` gateway bot executes the unmodified hello demo graph from a guild-scoped slash command via `load_and_compile_async` + `run_graph_async`; pure adapter slice (options→state, greeting→embed, correlated errors) unit-tested with zero network. (REQ-YG-600)
