---
type: fix
scope: fsm
---
- **FR-416 translate_legacy_config event_key passthrough**: `_translate_legacy_config()` in the chaplain adapter now forwards `event_key` to the `params` sub-dict, so `snapshot_params()` reads the correct result key and judge routing succeeds.
