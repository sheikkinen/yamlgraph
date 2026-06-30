"""Token estimation tool for compaction demo (FR-616)."""


def estimate_tokens(state: dict) -> dict:
    """Estimate token count of history using char/4 heuristic.

    Conservative: overestimates slightly so compaction fires early
    rather than late (safety margin ~10%).
    """
    history = state.get("history", [])
    total_chars = sum(len(str(item)) for item in history)
    # char/3.5 slightly overestimates vs tiktoken (safety margin)
    token_estimate = int(total_chars / 3.5)
    return {
        "token_estimate": token_estimate,
        "compaction_count": state.get("compaction_count", 0),
    }
