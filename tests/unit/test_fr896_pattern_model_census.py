"""FR-896 witnesses for the pattern_model_census demo artifact."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
import yaml

from examples.demos.pattern_model_census.tools import reduce_ledger

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

DEMO_DIR = Path("examples/demos/pattern_model_census")
GRAPH_PATH = DEMO_DIR / "graph.yaml"


def _good_state(tmp_path: Path) -> dict:
    contents = [
        {
            "_map_index": 0,
            "repo": "/private/raw/path",
            "sha": "abc123",
            "date": "2026-01-15T08:00:00+00:00",
            "subject": "feat: add map-reduce adapter",
            "shortstat": "2 files changed, 10 insertions(+)",
        },
        {
            "_map_index": 1,
            "repo": "/private/raw/path",
            "sha": "def456",
            "date": "2026-04-20T08:00:00+00:00",
            "subject": "fix: pin mercury-2 provider",
            "shortstat": "1 file changed, 3 insertions(+)",
        },
    ]
    return {
        "repo_alias": "fixture-demo",
        "output_path": str(tmp_path / "ledger.md"),
        "contents": contents,
        "pattern_findings": [
            {"_map_index": 0, "pattern": "map-reduce"},
            {"_map_index": 1, "pattern": None},
        ],
        "model_findings": [
            {"_map_index": 0, "model_mentioned": None},
            {"_map_index": 1, "model_mentioned": "mercury-2"},
        ],
    }


class TestPatternModelCensusGraph:
    @pytest.mark.req("REQ-YG-624")
    def test_judge_maps_are_mercury_pinned(self):
        graph = yaml.safe_load(GRAPH_PATH.read_text(encoding="utf-8"))
        for node_name in ("judge_pattern", "judge_model"):
            sub_node = graph["nodes"][node_name]["node"]
            assert sub_node["provider"] == "inception"
            assert sub_node["model"] == "mercury-2"
            assert sub_node["temperature"] == 0

    @pytest.mark.req("REQ-YG-624")
    def test_prompt_schemas_are_single_field_lenses(self):
        pattern = yaml.safe_load((DEMO_DIR / "prompts/judge_pattern.yaml").read_text())
        model = yaml.safe_load((DEMO_DIR / "prompts/judge_model.yaml").read_text())
        assert set(pattern["schema"]["fields"]) == {"pattern"}
        assert set(model["schema"]["fields"]) == {"model_mentioned"}


class TestPatternModelReducer:
    @pytest.mark.req("REQ-YG-624")
    def test_path_guard_rejects_non_tmp_yamlgraph_output(self):
        state = _good_state(Path("tmp"))
        state["output_path"] = "docs/foo.md"
        with pytest.raises(ValueError, match="under tmp"):
            reduce_ledger(state)

    @pytest.mark.req("REQ-YG-624")
    def test_path_guard_allows_tmp_and_summary_omits_private_fields(self, tmp_path):
        state = _good_state(tmp_path)
        result = reduce_ledger(state)["ledger"]
        assert result["rows"] == 4
        md = Path(result["markdown_path"]).read_text(encoding="utf-8")
        assert "| repo_alias | quarter | lens | label | count |" in md
        assert "abc123" not in md
        assert "feat: add map-reduce adapter" not in md
        assert "/private/raw/path" not in md
        rows = [
            json.loads(line)
            for line in Path(result["jsonl_path"])
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        assert len(rows) == len(state["contents"]) * 2
        assert {row["repo_alias"] for row in rows} == {"fixture-demo"}


class TestPatternModelGitTools:
    @pytest.mark.req("REQ-YG-624")
    def test_git_extract_schema_is_metadata_only(self, tmp_path):
        module_path = DEMO_DIR / "tools" / "git_tools.py"
        spec = importlib.util.spec_from_file_location("fr896_git_tools", module_path)
        assert spec is not None and spec.loader is not None
        git_tools = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(git_tools)

        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        (repo / "file.txt").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add mercury-2 route"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        extracted = git_tools.extract({"source": str(repo), "item": sha})
        assert set(extracted) == {"repo", "sha", "date", "subject", "shortstat"}
        assert extracted["sha"] == sha
        assert extracted["subject"] == "feat: add mercury-2 route"
        assert "diff" not in extracted
        assert git_tools.discover({"source": str(repo)}) == [sha]
