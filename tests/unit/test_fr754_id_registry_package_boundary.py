"""FR-754: package boundary stays free of .chaplain references."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.process


@pytest.mark.req("REQ-YG-001")
def test_id_registry_removed_from_package_and_no_chaplain_refs() -> None:
    """No Python module under yamlgraph/ may reference .chaplain directly."""
    repo_root = Path(__file__).resolve().parents[2]
    old_module = repo_root / "yamlgraph" / "utils" / "id_registry.py"
    assert not old_module.exists(), "yamlgraph/utils/id_registry.py must be removed"

    offenders: list[Path] = []
    for py_file in (repo_root / "yamlgraph").rglob("*.py"):
        if ".chaplain" in py_file.read_text(encoding="utf-8"):
            offenders.append(py_file)

    assert offenders == [], f"Found .chaplain reference(s): {offenders}"
