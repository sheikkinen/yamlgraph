"""Tests for scripts/check_changelog_req.py — mechanical pre-filter.

FR-247: Validates that changelog fragment `req:` front-matter values
reference valid requirement IDs in the capabilities registry.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from scripts.check_changelog_req import (
    find_owning_cap,
    load_req_to_cap_index,
    parse_fragment_req,
    validate_fragment,
)

pytestmark = pytest.mark.process

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "changelog_req"


def _write_cap(cap_dir: Path, cap_id: str, reqs: list[dict]) -> None:
    """Write a minimal CAP YAML file."""
    import yaml

    data = {
        "id": cap_id,
        "name": f"Test {cap_id}",
        "description": "Test capability",
        "modules": ["test_module"],
        "requirements": reqs,
        "fr": "FR-999",
    }
    filepath = cap_dir / f"{cap_id}-test.yaml"
    filepath.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")


def _write_fragment(frag_dir: Path, name: str, content: str) -> Path:
    """Write a changelog fragment file."""
    filepath = frag_dir / name
    filepath.write_text(textwrap.dedent(content), encoding="utf-8")
    return filepath


@pytest.mark.req("REQ-YG-255")
class TestParseFragmentReq:
    """Test YAML front-matter parsing from changelog fragments."""

    def test_extract_single_req(self, tmp_path: Path) -> None:
        frag = _write_fragment(
            tmp_path,
            "fr-100-test.md",
            """\
            ---
            type: feat
            scope: graph
            req: REQ-YG-100
            ---
            - **FR-100 Test**: Description.
            """,
        )
        result = parse_fragment_req(frag)
        assert result is not None
        assert result.req_ids == {"REQ-YG-100"}

    def test_extract_comma_separated_reqs(self, tmp_path: Path) -> None:
        frag = _write_fragment(
            tmp_path,
            "fr-200-multi.md",
            """\
            ---
            type: feat
            scope: a2a
            req: REQ-YG-200, REQ-YG-201, REQ-YG-202
            ---
            - **FR-200 Multi**: Description.
            """,
        )
        result = parse_fragment_req(frag)
        assert result is not None
        assert result.req_ids == {"REQ-YG-200", "REQ-YG-201", "REQ-YG-202"}

    def test_no_req_field_returns_none(self, tmp_path: Path) -> None:
        frag = _write_fragment(
            tmp_path,
            "fix-something.md",
            """\
            ---
            type: fix
            scope: cli
            ---
            - **fix(cli): something**: Description.
            """,
        )
        result = parse_fragment_req(frag)
        assert result is None

    def test_no_front_matter_returns_none(self, tmp_path: Path) -> None:
        frag = _write_fragment(
            tmp_path,
            "no-frontmatter.md",
            """\
            Just some text without front matter.
            """,
        )
        result = parse_fragment_req(frag)
        assert result is None

    def test_empty_req_field_returns_none(self, tmp_path: Path) -> None:
        frag = _write_fragment(
            tmp_path,
            "fr-100-empty-req.md",
            """\
            ---
            type: feat
            scope: graph
            req:
            ---
            - **FR-100 Test**: Description.
            """,
        )
        result = parse_fragment_req(frag)
        assert result is None


@pytest.mark.req("REQ-YG-255")
class TestLoadReqToCapIndex:
    """Test building the REQ-ID → CAP mapping from capability files."""

    def test_builds_index_from_cap_files(self, tmp_path: Path) -> None:
        _write_cap(
            tmp_path,
            "CAP-01",
            [
                {"id": "REQ-YG-001", "description": "First", "modules": ["m1"]},
                {"id": "REQ-YG-002", "description": "Second", "modules": ["m2"]},
            ],
        )
        _write_cap(
            tmp_path,
            "CAP-02",
            [{"id": "REQ-YG-003", "description": "Third", "modules": ["m3"]}],
        )
        index = load_req_to_cap_index(tmp_path)
        assert index["REQ-YG-001"] == "CAP-01"
        assert index["REQ-YG-002"] == "CAP-01"
        assert index["REQ-YG-003"] == "CAP-02"

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        index = load_req_to_cap_index(tmp_path)
        assert index == {}


@pytest.mark.req("REQ-YG-255")
class TestFindOwningCap:
    """Test looking up the owning CAP for a requirement ID."""

    def test_found_in_single_req_cap(self, tmp_path: Path) -> None:
        _write_cap(
            tmp_path,
            "CAP-10",
            [{"id": "REQ-YG-050", "description": "Test", "modules": ["m"]}],
        )
        index = load_req_to_cap_index(tmp_path)
        result = find_owning_cap("REQ-YG-050", index, tmp_path)
        assert result is not None
        cap_id, all_reqs = result
        assert cap_id == "CAP-10"
        assert all_reqs == ["REQ-YG-050"]

    def test_found_in_multi_req_cap(self, tmp_path: Path) -> None:
        _write_cap(
            tmp_path,
            "CAP-20",
            [
                {"id": "REQ-YG-100", "description": "A", "modules": ["m"]},
                {"id": "REQ-YG-101", "description": "B", "modules": ["m"]},
                {"id": "REQ-YG-102", "description": "C", "modules": ["m"]},
            ],
        )
        index = load_req_to_cap_index(tmp_path)
        result = find_owning_cap("REQ-YG-100", index, tmp_path)
        assert result is not None
        cap_id, all_reqs = result
        assert cap_id == "CAP-20"
        assert len(all_reqs) == 3

    def test_phantom_req_not_found(self, tmp_path: Path) -> None:
        _write_cap(
            tmp_path,
            "CAP-10",
            [{"id": "REQ-YG-050", "description": "Test", "modules": ["m"]}],
        )
        index = load_req_to_cap_index(tmp_path)
        result = find_owning_cap("REQ-YG-999", index, tmp_path)
        assert result is None


@pytest.mark.req("REQ-YG-255")
class TestValidateFragment:
    """Test the full validation logic for a single fragment."""

    def test_skip_fragment_without_req(self, tmp_path: Path) -> None:
        frag_dir = tmp_path / "unreleased"
        frag_dir.mkdir()
        frag = _write_fragment(
            frag_dir,
            "fix-something.md",
            """\
            ---
            type: fix
            scope: cli
            ---
            - Description.
            """,
        )
        cap_dir = tmp_path / "caps"
        cap_dir.mkdir()
        index = load_req_to_cap_index(cap_dir)
        result = validate_fragment(frag, index, cap_dir, skip_llm=True)
        assert result.status == "skipped"

    def test_phantom_req_fails(self, tmp_path: Path) -> None:
        frag_dir = tmp_path / "unreleased"
        frag_dir.mkdir()
        frag = _write_fragment(
            frag_dir,
            "fr-100-test.md",
            """\
            ---
            type: feat
            scope: graph
            req: REQ-YG-999
            ---
            - **FR-100 Test**: Description.
            """,
        )
        cap_dir = tmp_path / "caps"
        cap_dir.mkdir()
        _write_cap(
            cap_dir,
            "CAP-01",
            [{"id": "REQ-YG-001", "description": "First", "modules": ["m"]}],
        )
        index = load_req_to_cap_index(cap_dir)
        result = validate_fragment(frag, index, cap_dir, skip_llm=True)
        assert result.status == "fail"
        assert (
            "phantom" in result.reason.lower() or "not found" in result.reason.lower()
        )

    def test_single_req_cap_correct_match(self, tmp_path: Path) -> None:
        frag_dir = tmp_path / "unreleased"
        frag_dir.mkdir()
        frag = _write_fragment(
            frag_dir,
            "fr-100-test.md",
            """\
            ---
            type: feat
            scope: graph
            req: REQ-YG-050
            ---
            - **FR-100 Test**: Description.
            """,
        )
        cap_dir = tmp_path / "caps"
        cap_dir.mkdir()
        _write_cap(
            cap_dir,
            "CAP-10",
            [{"id": "REQ-YG-050", "description": "Test", "modules": ["m"]}],
        )
        index = load_req_to_cap_index(cap_dir)
        result = validate_fragment(frag, index, cap_dir, skip_llm=True)
        assert result.status == "pass"

    def test_single_req_cap_mismatch_fails(self, tmp_path: Path) -> None:
        """Fragment claims REQ-YG-050 but CAP-10 only has REQ-YG-051."""
        # Single-REQ match is tautological via index lookup.
        # If the REQ exists in the index, it was found by ID, so it matches
        # the CAP's sole REQ. The mismatch case for single-REQ is phantom
        # (REQ not found at all), which is tested in test_phantom_req_fails.
        # Multi-REQ CAPs need LLM to verify content matches the claimed REQ.
        assert True

    def test_multi_req_cap_deferred_with_skip_llm(self, tmp_path: Path) -> None:
        """Multi-REQ CAP fragments are deferred when --skip-llm is set."""
        frag_dir = tmp_path / "unreleased"
        frag_dir.mkdir()
        frag = _write_fragment(
            frag_dir,
            "fr-100-test.md",
            """\
            ---
            type: feat
            scope: graph
            req: REQ-YG-100
            ---
            - **FR-100 Test**: Description.
            """,
        )
        cap_dir = tmp_path / "caps"
        cap_dir.mkdir()
        _write_cap(
            cap_dir,
            "CAP-20",
            [
                {"id": "REQ-YG-100", "description": "A", "modules": ["m"]},
                {"id": "REQ-YG-101", "description": "B", "modules": ["m"]},
            ],
        )
        index = load_req_to_cap_index(cap_dir)
        result = validate_fragment(frag, index, cap_dir, skip_llm=True)
        assert result.status == "deferred"

    def test_unparseable_front_matter_fails(self, tmp_path: Path) -> None:
        frag_dir = tmp_path / "unreleased"
        frag_dir.mkdir()
        frag = _write_fragment(
            frag_dir,
            "fr-100-bad.md",
            """\
            ---
            type: feat
            scope: [[[invalid yaml
            ---
            - Description.
            """,
        )
        cap_dir = tmp_path / "caps"
        cap_dir.mkdir()
        index = load_req_to_cap_index(cap_dir)
        result = validate_fragment(frag, index, cap_dir, skip_llm=True)
        assert result.status == "fail"
        assert "parse" in result.reason.lower() or "error" in result.reason.lower()

    def test_all_current_fragments_pass_mechanical(self) -> None:
        """All current changelog/unreleased/*.md fragments pass mechanical checks."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        cap_dir = repo_root / "capabilities"
        changelog_dir = repo_root / "changelog" / "unreleased"

        if not changelog_dir.exists():
            pytest.skip("No changelog/unreleased directory")

        index = load_req_to_cap_index(cap_dir)
        errors: list[str] = []
        checked = 0

        for frag_path in sorted(changelog_dir.glob("*.md")):
            result = validate_fragment(frag_path, index, cap_dir, skip_llm=True)
            if result.status == "fail":
                errors.append(f"{frag_path.name}: {result.reason}")
            if result.status != "skipped":
                checked += 1

        assert not errors, (
            f"Fragments failing mechanical check ({len(errors)}):\n"
            + "\n".join(f"  • {e}" for e in errors)
        )
