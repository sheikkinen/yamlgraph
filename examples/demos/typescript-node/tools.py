"""Tools for the TypeScript subprocess JSON demo."""


def compose_greeting(state: dict) -> dict:
    """Return deterministic JSON-friendly state for Node.js integration tests."""
    name = state["name"]
    style = state["style"]
    return {
        "result": {
            "message": f"Hello, {name}!",
            "style": style,
            "channel": "typescript-node",
        }
    }
