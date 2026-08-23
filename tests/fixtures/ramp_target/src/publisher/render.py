"""Card rendering (fixture)."""

MAX_EDGE = 1568


def render_card(topic: str, width: int) -> dict:
    width = min(width, MAX_EDGE)
    return {"topic": topic, "width": width, "caption": f"daily: {topic}"}
