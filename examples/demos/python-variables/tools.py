"""Python tools demonstrating variables: expression resolution (FR-252)."""


def format_greeting(state: dict) -> dict:
    """Format a greeting using pre-resolved variables.

    With variables: support, 'name' and 'style' arrive already
    resolved from state expressions — no manual extraction needed.

    Args:
        state: Contains 'name' and 'style' keys (injected by variables:)

    Returns:
        Dict with formatted greeting
    """
    name = state["name"]
    style = state["style"]

    templates = {
        "formal": f"Dear {name}, it is a pleasure to make your acquaintance.",
        "casual": f"Hey {name}! What's up?",
        "pirate": f"Ahoy, {name}! Avast ye scurvy dog!",
    }

    greeting = templates.get(style, f"Hello, {name}!")
    return {"result": f"{greeting} (style={style})"}
