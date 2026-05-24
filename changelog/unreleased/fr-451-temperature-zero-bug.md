---
type: fix
scope: agent
req: REQ-YG-018
---
- **FR-451 Fahrenheit 451 — Temperature Adjustments**: Fixed `temperature: 0` being treated as falsy and silently falling through to `0.7` default. Agent nodes now correctly respect zero temperature for deterministic outputs. (REQ-YG-018)
