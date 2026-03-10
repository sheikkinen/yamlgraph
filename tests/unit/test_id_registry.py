"""Unit tests for ID registry functionality.

FR-180: Plan-Phase ID Reservation
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from yamlgraph.utils.id_registry import (
    IdRegistry,
    Reservation,
    format_cap_id,
    format_req_id,
    load_registry,
    reserve_ids,
    save_registry,
    validate_registry,
)


class TestIdRegistry:
    """Tests for IdRegistry model."""

    @pytest.mark.req("REQ-YG-001")  # Config Loading & Validation
    def test_create_empty_registry(self) -> None:
        """Can create an empty registry."""
        registry = IdRegistry(next_cap=65, next_req=161)
        assert registry.next_cap == 65
        assert registry.next_req == 161
        assert registry.reserved == []

    @pytest.mark.req("REQ-YG-001")
    def test_create_registry_with_reservations(self) -> None:
        """Can create registry with existing reservations."""
        registry = IdRegistry(
            next_cap=66,
            next_req=164,
            reserved=[
                Reservation(fr="FR-181", cap=[65], req=[161, 162, 163], note="Test")
            ],
        )
        assert len(registry.reserved) == 1
        assert registry.reserved[0].fr == "FR-181"


class TestReservation:
    """Tests for Reservation model."""

    @pytest.mark.req("REQ-YG-001")
    def test_create_reservation(self) -> None:
        """Can create a reservation."""
        res = Reservation(fr="FR-181", cap=[65], req=[161, 162], note="Widget node")
        assert res.fr == "FR-181"
        assert res.cap == [65]
        assert res.req == [161, 162]
        assert res.note == "Widget node"

    @pytest.mark.req("REQ-YG-001")
    def test_empty_reservation(self) -> None:
        """Can create reservation with no IDs (for tracking only)."""
        res = Reservation(fr="FR-180", note="ID registry mechanism itself")
        assert res.cap == []
        assert res.req == []


class TestLoadRegistry:
    """Tests for load_registry function."""

    @pytest.mark.req("REQ-YG-001")
    def test_load_valid_registry(self) -> None:
        """Can load a valid registry file."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
            f.write("next_cap: 65\nnext_req: 161\nreserved: []\n")
            f.flush()
            path = Path(f.name)

        try:
            registry = load_registry(path)
            assert registry.next_cap == 65
            assert registry.next_req == 161
        finally:
            path.unlink()

    @pytest.mark.req("REQ-YG-004")  # Error Handling
    def test_load_missing_file(self) -> None:
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_registry(Path("/nonexistent/path.yaml"))

    @pytest.mark.req("REQ-YG-004")
    def test_load_invalid_yaml(self) -> None:
        """Raises ValueError for invalid YAML structure."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
            f.write("just a string\n")
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="must be a mapping"):
                load_registry(path)
        finally:
            path.unlink()


class TestReserveIds:
    """Tests for reserve_ids function."""

    @pytest.mark.req("REQ-YG-001")
    def test_reserve_cap_only(self) -> None:
        """Can reserve CAP IDs only."""
        registry = IdRegistry(next_cap=65, next_req=161)
        res = reserve_ids(registry, "FR-181", cap_count=2)

        assert res.cap == [65, 66]
        assert res.req == []
        assert registry.next_cap == 67
        assert registry.next_req == 161  # Unchanged

    @pytest.mark.req("REQ-YG-001")
    def test_reserve_req_only(self) -> None:
        """Can reserve REQ IDs only."""
        registry = IdRegistry(next_cap=65, next_req=161)
        res = reserve_ids(registry, "FR-181", req_count=3)

        assert res.cap == []
        assert res.req == [161, 162, 163]
        assert registry.next_cap == 65  # Unchanged
        assert registry.next_req == 164

    @pytest.mark.req("REQ-YG-001")
    def test_reserve_both(self) -> None:
        """Can reserve both CAP and REQ IDs."""
        registry = IdRegistry(next_cap=65, next_req=161)
        res = reserve_ids(registry, "FR-181", cap_count=1, req_count=3, note="Widget")

        assert res.cap == [65]
        assert res.req == [161, 162, 163]
        assert res.note == "Widget"
        assert registry.next_cap == 66
        assert registry.next_req == 164

    @pytest.mark.req("REQ-YG-001")
    def test_reserve_appends_to_list(self) -> None:
        """Reservation is appended to registry.reserved."""
        registry = IdRegistry(next_cap=65, next_req=161)
        reserve_ids(registry, "FR-181", cap_count=1)
        reserve_ids(registry, "FR-182", req_count=2)

        assert len(registry.reserved) == 2
        assert registry.reserved[0].fr == "FR-181"
        assert registry.reserved[1].fr == "FR-182"

    @pytest.mark.req("REQ-YG-004")
    def test_reserve_negative_count_raises(self) -> None:
        """Raises ValueError for negative counts."""
        registry = IdRegistry(next_cap=65, next_req=161)

        with pytest.raises(ValueError, match="non-negative"):
            reserve_ids(registry, "FR-181", cap_count=-1)

        with pytest.raises(ValueError, match="non-negative"):
            reserve_ids(registry, "FR-181", req_count=-1)


class TestSaveRegistry:
    """Tests for save_registry function."""

    @pytest.mark.req("REQ-YG-001")
    def test_save_and_reload(self) -> None:
        """Can save and reload a registry."""
        registry = IdRegistry(next_cap=66, next_req=164)
        reserve_ids(registry, "FR-181", cap_count=1, req_count=2, note="Test")

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w") as f:
            path = Path(f.name)

        try:
            save_registry(registry, path)
            reloaded = load_registry(path)

            assert reloaded.next_cap == 67
            assert reloaded.next_req == 166
            assert len(reloaded.reserved) == 1
            assert reloaded.reserved[0].fr == "FR-181"
        finally:
            path.unlink()


class TestValidateRegistry:
    """Tests for validate_registry function."""

    @pytest.mark.req("REQ-YG-001")
    def test_valid_empty_registry(self) -> None:
        """Empty registry is valid."""
        registry = IdRegistry(next_cap=65, next_req=161)
        errors = validate_registry(registry)
        assert errors == []

    @pytest.mark.req("REQ-YG-001")
    def test_valid_with_reservations(self) -> None:
        """Registry with valid reservations is valid."""
        registry = IdRegistry(
            next_cap=67,
            next_req=165,
            reserved=[
                Reservation(fr="FR-181", cap=[65, 66], req=[161, 162, 163, 164])
            ],
        )
        errors = validate_registry(registry)
        assert errors == []

    @pytest.mark.req("REQ-YG-004")
    def test_invalid_next_cap_too_low(self) -> None:
        """Detects next_cap lower than max reserved."""
        registry = IdRegistry(
            next_cap=65,  # Should be at least 67
            next_req=165,
            reserved=[Reservation(fr="FR-181", cap=[65, 66], req=[])],
        )
        errors = validate_registry(registry)
        assert any("next_cap" in e and "must be >" in e for e in errors)

    @pytest.mark.req("REQ-YG-004")
    def test_invalid_next_req_too_low(self) -> None:
        """Detects next_req lower than max reserved."""
        registry = IdRegistry(
            next_cap=65,
            next_req=161,  # Should be at least 165
            reserved=[Reservation(fr="FR-181", cap=[], req=[161, 162, 163, 164])],
        )
        errors = validate_registry(registry)
        assert any("next_req" in e and "must be >" in e for e in errors)

    @pytest.mark.req("REQ-YG-004")
    def test_duplicate_cap_ids(self) -> None:
        """Detects duplicate CAP IDs across reservations."""
        registry = IdRegistry(
            next_cap=67,
            next_req=161,
            reserved=[
                Reservation(fr="FR-181", cap=[65], req=[]),
                Reservation(fr="FR-182", cap=[65], req=[]),  # Duplicate!
            ],
        )
        errors = validate_registry(registry)
        assert any("Duplicate CAP-65" in e for e in errors)

    @pytest.mark.req("REQ-YG-004")
    def test_duplicate_req_ids(self) -> None:
        """Detects duplicate REQ IDs across reservations."""
        registry = IdRegistry(
            next_cap=65,
            next_req=163,
            reserved=[
                Reservation(fr="FR-181", cap=[], req=[161]),
                Reservation(fr="FR-182", cap=[], req=[161, 162]),  # 161 is duplicate!
            ],
        )
        errors = validate_registry(registry)
        assert any("Duplicate REQ-YG-161" in e for e in errors)


class TestFormatIds:
    """Tests for ID formatting functions."""

    @pytest.mark.req("REQ-YG-001")
    def test_format_cap_id(self) -> None:
        """CAP IDs formatted with zero-padding."""
        assert format_cap_id(1) == "CAP-01"
        assert format_cap_id(65) == "CAP-65"
        assert format_cap_id(100) == "CAP-100"

    @pytest.mark.req("REQ-YG-001")
    def test_format_req_id(self) -> None:
        """REQ IDs formatted with YG prefix and padding."""
        assert format_req_id(1) == "REQ-YG-001"
        assert format_req_id(161) == "REQ-YG-161"
        assert format_req_id(1000) == "REQ-YG-1000"
