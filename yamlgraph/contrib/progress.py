"""Progress reporting utilities for YAMLGraph pipelines (FR-044d).

Reports on skipped/failed nodes by reading PipelineErrors from state.
"""

from __future__ import annotations

from yamlgraph.models import PipelineError


class SkipReport:
    """Report on skipped nodes from state errors.

    Reads PipelineError objects from state["errors"] and provides
    human-readable summaries of what was skipped and why.

    Example:
        >>> from yamlgraph.contrib.progress import SkipReport
        >>> report = SkipReport.from_state(state)
        >>> if report.count > 0:
        ...     report.log()
        ...     print(report.summary())
    """

    def __init__(
        self,
        errors: list[PipelineError],
        total_nodes: int | None = None,
    ):
        """Initialize SkipReport.

        Args:
            errors: List of PipelineError objects from state["errors"]
            total_nodes: Optional total node count for X/Y display
        """
        self.errors = errors
        self.total_nodes = total_nodes

    @classmethod
    def from_state(
        cls,
        state: dict,
        node_keys: list[str] | None = None,
    ) -> SkipReport:
        """Build SkipReport from graph state.

        Args:
            state: Graph state dict with optional "errors" key
            node_keys: Optional list of expected state keys (for total count)

        Returns:
            SkipReport instance
        """
        errors = list(state.get("errors") or [])
        total = len(node_keys) if node_keys else None
        return cls(errors=errors, total_nodes=total)

    @property
    def count(self) -> int:
        """Number of skipped/failed nodes."""
        return len(self.errors)

    def summary(self) -> str:
        """Human-readable summary of skips.

        Returns:
            Summary string like "⚠ 2/9 skipped: [scamper: timeout, ...]"
        """
        if not self.errors:
            return "All nodes completed successfully."

        parts = [f"{e.node}: {e.message}" for e in self.errors]
        total_str = f"/{self.total_nodes}" if self.total_nodes else ""
        return f"⚠ {self.count}{total_str} skipped: [{', '.join(parts)}]"

    def log(self) -> None:
        """Log summary at WARNING level."""
        import logging

        logging.getLogger(__name__).warning(self.summary())

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict.

        Returns:
            Dict with skipped_count, total_nodes, skipped_nodes list
        """
        return {
            "skipped_count": self.count,
            "total_nodes": self.total_nodes,
            "skipped_nodes": [
                {
                    "node": e.node,
                    "error": e.message,
                    "type": e.type.value if hasattr(e.type, "value") else str(e.type),
                }
                for e in self.errors
            ],
        }
