"""ID Registry for CAP-XX and REQ-YG-XXX assignment.

FR-180: Plan-Phase ID Reservation

This module provides functions to reserve, validate, and manage capability
and requirement IDs during the Plan and Enforcement phases.

Usage:
    from yamlgraph.utils.id_registry import load_registry, reserve_ids, save_registry

    registry = load_registry()
    reservation = reserve_ids(registry, "FR-181", cap_count=1, req_count=3)
    save_registry(registry)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REGISTRY_PATH = REPO_ROOT / ".chaplain" / "id-registry.yaml"

# Pre-existing IDs that predate the registry
PRE_EXISTING_MAX_CAP = 64
PRE_EXISTING_MAX_REQ = 160


class Reservation(BaseModel):
    """A reservation of CAP and REQ IDs for a specific FR."""

    fr: str = Field(description="Feature request ID, e.g. 'FR-181'")
    cap: list[int] = Field(default_factory=list, description="Reserved CAP IDs")
    req: list[int] = Field(default_factory=list, description="Reserved REQ IDs")
    note: str = Field(default="", description="Optional note about the reservation")


class IdRegistry(BaseModel):
    """The ID registry tracking next available IDs and reservations."""

    next_cap: int = Field(description="Next available CAP ID")
    next_req: int = Field(description="Next available REQ ID")
    reserved: list[Reservation] = Field(
        default_factory=list, description="List of FR reservations"
    )


def load_registry(path: Path = DEFAULT_REGISTRY_PATH) -> IdRegistry:
    """Load and validate the id-registry.yaml file.

    Args:
        path: Path to the registry file.

    Returns:
        Loaded and validated IdRegistry.

    Raises:
        FileNotFoundError: If the registry file doesn't exist.
        ValueError: If the registry file is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Registry must be a mapping, got {type(data).__name__}")

    return IdRegistry.model_validate(data)


def reserve_ids(
    registry: IdRegistry,
    fr_id: str,
    cap_count: int = 0,
    req_count: int = 0,
    note: str = "",
) -> Reservation:
    """Reserve a contiguous range of CAP/REQ IDs for an FR.

    Increments next_cap/next_req and appends to the reserved list.
    The registry object is modified in place.

    Args:
        registry: The registry to reserve IDs from.
        fr_id: Feature request ID (e.g. "FR-181").
        cap_count: Number of CAP IDs to reserve.
        req_count: Number of REQ IDs to reserve.
        note: Optional note about the reservation.

    Returns:
        The Reservation with concrete IDs.

    Raises:
        ValueError: If cap_count or req_count is negative.
    """
    if cap_count < 0 or req_count < 0:
        raise ValueError("cap_count and req_count must be non-negative")

    cap_ids = list(range(registry.next_cap, registry.next_cap + cap_count))
    req_ids = list(range(registry.next_req, registry.next_req + req_count))

    registry.next_cap += cap_count
    registry.next_req += req_count

    reservation = Reservation(fr=fr_id, cap=cap_ids, req=req_ids, note=note)
    registry.reserved.append(reservation)

    return reservation


def save_registry(registry: IdRegistry, path: Path = DEFAULT_REGISTRY_PATH) -> None:
    """Write the updated registry back to YAML.

    Args:
        registry: The registry to save.
        path: Path to write the registry file.
    """
    # Build output with header comments
    header = """# ID Registry for CAP-XX and REQ-YG-XXX assignment
# FR-180: Plan-Phase ID Reservation
#
# - next_cap/next_req are monotonically increasing counters
# - reserved is an append-only list of reservations per FR
# - IDs are reserved during Plan phase and consumed during Enforcement
#
# Pre-existing IDs (CAP-01 through CAP-64, REQ-YG-001 through REQ-YG-160)
# predate this registry and are not tracked here.

"""
    data = registry.model_dump()

    # Manual YAML formatting for cleaner output
    lines = [header]
    lines.append(f"next_cap: {data['next_cap']}")
    lines.append(f"next_req: {data['next_req']}")

    if not data["reserved"]:
        lines.append("reserved: []")
    else:
        lines.append("reserved:")
        for res in data["reserved"]:
            lines.append(f"  - fr: {res['fr']}")
            lines.append(f"    cap: {res['cap']}")
            lines.append(f"    req: {res['req']}")
            if res["note"]:
                lines.append(f"    note: {res['note']!r}")

    lines.append("")  # Trailing newline

    with open(path, "w") as f:
        f.write("\n".join(lines))


def validate_registry(registry: IdRegistry) -> list[str]:
    """Validate registry integrity.

    Checks:
    1. next_cap >= max(all reserved cap IDs) + 1
    2. next_req >= max(all reserved req IDs) + 1
    3. No two reservations claim the same ID

    Args:
        registry: The registry to validate.

    Returns:
        List of error messages (empty = valid).
    """
    errors: list[str] = []

    # Collect all reserved IDs
    all_cap_ids: list[int] = []
    all_req_ids: list[int] = []
    cap_owners: dict[int, str] = {}  # cap_id -> fr_id
    req_owners: dict[int, str] = {}  # req_id -> fr_id

    for res in registry.reserved:
        for cap_id in res.cap:
            all_cap_ids.append(cap_id)
            if cap_id in cap_owners:
                errors.append(
                    f"Duplicate CAP-{cap_id}: claimed by {cap_owners[cap_id]} and {res.fr}"
                )
            else:
                cap_owners[cap_id] = res.fr

        for req_id in res.req:
            all_req_ids.append(req_id)
            if req_id in req_owners:
                errors.append(
                    f"Duplicate REQ-YG-{req_id:03d}: "
                    f"claimed by {req_owners[req_id]} and {res.fr}"
                )
            else:
                req_owners[req_id] = res.fr

    # Check counter consistency
    if all_cap_ids:
        max_cap = max(all_cap_ids)
        if registry.next_cap <= max_cap:
            errors.append(
                f"next_cap ({registry.next_cap}) must be > max reserved CAP ({max_cap})"
            )

    if all_req_ids:
        max_req = max(all_req_ids)
        if registry.next_req <= max_req:
            errors.append(
                f"next_req ({registry.next_req}) must be > max reserved REQ ({max_req})"
            )

    return errors


def format_cap_id(cap_num: int) -> str:
    """Format a CAP number as a string ID.

    Args:
        cap_num: The CAP number (e.g. 65).

    Returns:
        Formatted string (e.g. "CAP-65").
    """
    return f"CAP-{cap_num:02d}"


def format_req_id(req_num: int) -> str:
    """Format a REQ number as a string ID.

    Args:
        req_num: The REQ number (e.g. 161).

    Returns:
        Formatted string (e.g. "REQ-YG-161").
    """
    return f"REQ-YG-{req_num:03d}"
