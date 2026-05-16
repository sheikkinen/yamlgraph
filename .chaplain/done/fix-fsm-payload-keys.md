fix(fsm): run_and_dispatch ignores SnapshotParams.payload_keys (#392)

`graph_runner.py` never reads `payload_keys` from `SnapshotParams`. Keys like `prior_messages` and `original_intent` are silently dropped from the dispatched event payload. After `aget_state`, extract listed keys from `state_after.values` into `payload`. Only applies when `run_config` is set (checkpointer path).
