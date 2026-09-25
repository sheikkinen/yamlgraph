---
type: fix
scope: map
req: REQ-YG-692
---
- **FR-1073 Map result contract**: a `type: map` node now compiles to four nodes: a dispatch node, the per-item sub-node, an account node (`_map_<name>_account`) and a join (`_map_<name>_join`). A failed branch never enters `collect`. Each failure lands as a typed `MapFailure` record in `failures` (default `<collect>_failures`); a failure the sub-node's `on_error: skip` does not tolerate also adds one `PipelineError` to `errors`. The account node counts every dispatched index against that dispatch's token and writes a `MapVerdict`; the join then raises `MapCompletenessError` when successes plus tolerated failures fall below `min_success`, which is strict by default and takes an `int` count or a `float` fraction. Overlapping runs of the same map raise `MapAccountingError`. Seventeen example consumers no longer read `_error` from collected results; census reducers read `failures` instead. Seven graphs move their unread map-level `on_error` into the sub-node, and `map-timeout` declares `min_success: 2`. (REQ-YG-692)
