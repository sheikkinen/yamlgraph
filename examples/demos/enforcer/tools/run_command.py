"""Run command honeypot tool for the enforcer demo.

Logs the requested command but does not execute it. Captures unmet tool
needs as telemetry — recurring patterns graduate to new task-shaped tools.
"""

import logging

logger = logging.getLogger(__name__)


def run_command(command: str) -> str:
    """Log the requested command and return an error directing to specific tools."""
    logger.info("run_command requested: %s", command)
    return (
        "run_command is not available. Use the specific tools provided: "
        "read_file, search, list_dir, git_log, git_diff, lint, "
        "run_tests, write_file, edit_file."
    )
