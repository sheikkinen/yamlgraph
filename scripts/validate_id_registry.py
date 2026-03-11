#!/usr/bin/env python3
"""Validate ID registry integrity.

FR-180: Plan-Phase ID Reservation

Usage:
    python scripts/validate_id_registry.py [--strict]

Validates .chaplain/id-registry.yaml:
1. next_cap >= max(all reserved cap IDs) + 1
2. next_req >= max(all reserved req IDs) + 1
3. No two reservations claim the same ID

Exit codes:
- 0: Valid
- 1: Validation errors found
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to path for imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from yamlgraph.utils.id_registry import (  # noqa: E402
    DEFAULT_REGISTRY_PATH,
    load_registry,
    validate_registry,
)


def main() -> int:
    """Main entry point."""
    print("=" * 70)
    print("ID REGISTRY VALIDATION")
    print("=" * 70)
    print()

    if not DEFAULT_REGISTRY_PATH.exists():
        print(f"✅ Registry file not found (expected at {DEFAULT_REGISTRY_PATH})")
        print("   This is OK if FR-180 has not been implemented yet.")
        return 0

    try:
        registry = load_registry()
    except Exception as e:
        print(f"❌ Failed to load registry: {e}")
        return 1

    errors = validate_registry(registry)

    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"  ❌ {error}")
        print()
        print(f"Found {len(errors)} error(s)")
        return 1

    # Summary
    total_reservations = len(registry.reserved)
    total_caps = sum(len(r.cap) for r in registry.reserved)
    total_reqs = sum(len(r.req) for r in registry.reserved)

    print("✅ Registry valid")
    print(f"   next_cap: {registry.next_cap}")
    print(f"   next_req: {registry.next_req}")
    print(f"   {total_reservations} reservation(s)")
    print(f"   {total_caps} CAP ID(s) reserved")
    print(f"   {total_reqs} REQ ID(s) reserved")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
