"""FR-1104: core-test retired; 3.11 full-extras leg + 3.14 lean leg."""

import tomllib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_PATH = REPO_ROOT / ".github" / "workflows" / "workflow.yml"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _jobs() -> dict:
    return yaml.safe_load(CI_PATH.read_text(encoding="utf-8"))["jobs"]


def _leg_extras() -> dict[str, set[str]]:
    include = _jobs()["test"]["strategy"]["matrix"]["include"]
    return {leg["python-version"]: set(leg["extras"].split(",")) for leg in include}


@pytest.mark.req("REQ-YG-277")
class TestFr1104Matrix:
    def test_core_test_job_retired(self) -> None:
        assert "core-test" not in _jobs()

    def test_matrix_contexts_are_311_and_314(self) -> None:
        matrix = _jobs()["test"]["strategy"]["matrix"]
        assert matrix["python-version"] == ["3.11", "3.14"]

    def test_floor_leg_installs_otel_and_vision(self) -> None:
        assert {"otel", "vision"} <= _leg_extras()["3.11"]

    def test_ceiling_leg_is_lean(self) -> None:
        assert not {"otel", "vision"} & _leg_extras()["3.14"]

    def test_legs_differ_only_by_otel_and_vision(self) -> None:
        extras = _leg_extras()
        assert extras["3.11"] - extras["3.14"] == {"otel", "vision"}
        assert extras["3.14"] <= extras["3.11"]

    def test_install_step_uses_matrix_extras(self) -> None:
        steps = _jobs()["test"]["steps"]
        install = next(s for s in steps if s.get("name") == "Install dependencies")
        assert '".[${{ matrix.extras }}]"' in install["run"]


@pytest.mark.req("REQ-YG-277")
class TestFr1104PackageMetadata:
    def _project(self) -> dict:
        return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]

    def test_requires_python_admits_314(self) -> None:
        assert self._project()["requires-python"] == ">=3.11,<3.15"

    def test_classifiers_cover_311_to_314(self) -> None:
        classifiers = set(self._project()["classifiers"])
        for minor in ("3.11", "3.12", "3.13", "3.14"):
            assert f"Programming Language :: Python :: {minor}" in classifiers
