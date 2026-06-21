"""DM v3 plot model -- the typed belief lane (FR-560 M1).

A leaf package (FR-560 J4c): imported *by* the v2 chapter-open seam, never the reverse. Public
surface: the schema contract, the pure projections + grounding validator, the floodmark fixtures,
and the report renderer. ``unified-planning`` is optional -- only ``solve_status`` (and the causal
regression) need it; projection, grounding, the seam, and the report run pure.
"""

from __future__ import annotations

from .project import chapter_cast, exclusion_set, ordered_functions, protected_set
from .report import render_report
from .schema import (
    AffectDelta,
    Belief,
    Fluent,
    Function,
    PlanFlaw,
    PlotPlan,
    ValidationResult,
)
from .validate import validate_plan

__all__ = [
    "AffectDelta",
    "Belief",
    "Fluent",
    "Function",
    "PlanFlaw",
    "PlotPlan",
    "ValidationResult",
    "chapter_cast",
    "exclusion_set",
    "ordered_functions",
    "protected_set",
    "render_report",
    "validate_plan",
]
