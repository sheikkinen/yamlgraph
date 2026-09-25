"""Map sub-node for interrupt_loop_end.yaml (FR-1073: a passthrough sub-node
is not a supported map sub-node type and failed silently before the map
result contract surfaced it)."""


def plan_item(state: dict) -> dict:
    return {"plan": state["item"]}
