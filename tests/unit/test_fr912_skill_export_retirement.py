"""FR-912: the skill/agent export surface is retired.

Witness test for the retirement — the only permitted skill-export mention
under ``tests/`` after the deletion sweep. ``test_fr910_mcp_retirement.py``
is the named sibling exception: it cites the retired MCP export module as
its own retirement witness, not as live advertising.
"""

import importlib.util
import re
import subprocess
from pathlib import Path

import pytest

from yamlgraph.cli import create_parser

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]

DELETED_PATHS = [
    "yamlgraph/export",
    "yamlgraph/export/__init__.py",
    "yamlgraph/export/skill.py",
    "yamlgraph/export/skill_writer.py",
    "yamlgraph/cli/skill_commands.py",
    "reference/skills-export.md",
    "tests/unit/test_fr348_skill_export_red.py",
    "tests/unit/test_fr350_agent_export_red.py",
    "tests/unit/test_fr351_agent_export_red.py",
]

# FR-924: build residue leaves an importable namespace package that neither
# git nor Path.exists() detects.
RETIRED_MODULES = [
    "yamlgraph.export",
    "yamlgraph.export.skill",
    "yamlgraph.export.skill_writer",
    "yamlgraph.cli.skill_commands",
]

LIVE_SURFACE_PATTERN = re.compile(
    r"skill_commands"
    r"|yamlgraph\.export"
    r"|yamlgraph/export"
    r"|cmd_skill_dispatch"
    r"|PackageSkill"
    r"|SkillPackage"
    r"|SkillFormat"
    r"|export_skill"
    r"|write_skill_package"
    r"|write_agent_md_file"
    r"|yamlgraph skill export"
    r"|skills-export\.md"
    r"|agent-md"
    r"|skill-md"
)

SCANNED_SURFACES = [
    "yamlgraph",
    "tests",
    "reference",
    "README.md",
    "ARCHITECTURE.md",
    ".importlinter",
]

# Named non-live exceptions (judgement D-5/AC-05): retirement witnesses, not
# live surface advertising.
EXCEPTED_PATHS = {
    "tests/unit/test_fr912_skill_export_retirement.py",
    "tests/unit/test_fr910_mcp_retirement.py",
}


@pytest.mark.req("REQ-YG-032")
def test_cli_parser_rejects_skill_subcommand():
    """The top-level parser no longer knows the retired ``skill`` subcommand."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["skill", "export", "graph.yaml"])


@pytest.mark.req("REQ-YG-032")
def test_cli_package_has_no_skill_export_wiring():
    source = (REPO_ROOT / "yamlgraph" / "cli" / "__init__.py").read_text(encoding="utf-8")
    assert "cmd_skill_dispatch" not in source
    assert "skill" not in source.lower()


@pytest.mark.req("REQ-YG-428")
@pytest.mark.parametrize("relative_path", DELETED_PATHS)
def test_skill_export_paths_are_untracked(relative_path):
    """AC-01/AC-03/AC-04 ask git, not the filesystem (FR-924)."""
    tracked = subprocess.run(  # noqa: S603  # CONF-442
        ["git", "ls-files", relative_path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert tracked.stdout.strip() == ""


@pytest.mark.req("REQ-YG-428")
@pytest.mark.parametrize("module_name", RETIRED_MODULES)
def test_retired_skill_export_modules_are_not_importable(module_name):
    """Nothing under this checkout resolves the retired module names.

    A sibling worktree sharing one editable install can still resolve the
    name against the main checkout, so the assertion is scoped to origins
    inside ``REPO_ROOT`` — which is where build residue would live.
    """
    try:
        spec = importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        return
    if spec is None or spec.origin is None:
        origins = list(getattr(spec, "submodule_search_locations", None) or [])
    else:
        origins = [spec.origin]
    inside = [o for o in origins if Path(o).is_relative_to(REPO_ROOT)]
    assert inside == []


@pytest.mark.req("REQ-YG-428")
def test_skill_export_capabilities_are_retired():
    for cap in (
        "CAP-142-skill-export.yaml",
        "CAP-143-agent-md-export-tool-scoped-personas.yaml",
    ):
        text = (REPO_ROOT / "capabilities" / cap).read_text(encoding="utf-8")
        assert "status: retired" in text
        assert "RETIRED by FR-912" in text


@pytest.mark.req("REQ-YG-428")
def test_no_live_skill_export_references():
    """AC-05 denylist: the export seam is gone from code, tests, and docs."""
    offenders: list[str] = []
    for surface in SCANNED_SURFACES:
        root = REPO_ROOT / surface
        if not root.exists():
            continue
        paths = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in paths:
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            relative = str(path.relative_to(REPO_ROOT))
            if relative in EXCEPTED_PATHS:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if LIVE_SURFACE_PATTERN.search(text):
                offenders.append(relative)
    assert offenders == []


@pytest.mark.req("REQ-YG-428")
def test_kept_skill_promotion_test_survives():
    """C-3: FR-912 retires the generator, not the hand-authored corpus."""
    assert (REPO_ROOT / "tests" / "unit" / "test_fr446_copilot_skills.py").exists()
    assert (REPO_ROOT / ".github" / "skills").is_dir()
