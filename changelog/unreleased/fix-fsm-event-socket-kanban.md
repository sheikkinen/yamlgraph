### Fixed
- Supervisor workers now connect to the shared event socket (`/tmp/statemachine-events.sock`) instead of non-existent per-worker sockets, restoring real-time UI updates.
- Worker naming changed from `_w{N}` to `_{NNN}` (3-digit suffix) to enable Kanban view grouping in the monitoring UI.
- Added `template: true` to all voice coordinator configs for Kanban view support.
- Created `projects/ninchat_voice/chaplain.yaml` manifest for watcher2 multi-project routing.
