"""Python tools for map-timeout demo (FR-069)."""

import time


def slow_task(state: dict) -> dict:
    """Simulate a task with variable duration.

    Items with delay > timeout will be terminated and reported as errors.

    Args:
        state: Must contain 'task' key with {name, delay_seconds}

    Returns:
        Dict with 'result' key containing task outcome
    """
    task = state["task"]
    name = task["name"]
    delay = task["delay_seconds"]

    time.sleep(delay)

    return {
        "result": {
            "name": name,
            "status": "completed",
            "duration": delay,
        }
    }
