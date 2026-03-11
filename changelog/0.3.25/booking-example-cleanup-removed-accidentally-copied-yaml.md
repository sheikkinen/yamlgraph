---
type: fix
scope: booking
---
- **Booking Example Cleanup**
  - Removed accidentally copied yamlgraph core library, demo graphs, and demo prompts from `examples/booking/`
  - Fixed `fly.toml` BOOKING_GRAPH_PATH to point to correct file location (`graph.yaml` not `graphs/booking.yaml`)
  - Code formatting fixes (trailing whitespace, import sorting)
