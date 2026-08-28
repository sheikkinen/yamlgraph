"""FR-899 witnesses: org repo census with pinned-Azure delegation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from examples.demos.corpus_census.adapters.corpus_adapters import (
    gh_org_discover,
    gh_repo_extract,
)
from examples.demos.repo_census.tools import (
    PUBLIC_DEMO_ORG,
    preflight,
    prepare_brief_input,
    reduce_repo_ledger,
)

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

DEMO_DIR = Path("examples/demos/repo_census")
GRAPH_PATH = DEMO_DIR / "graph.yaml"

AZURE_VARS = ("AZURE_AI_ENDPOINT", "AZURE_AI_API_KEY", "AZURE_MODEL")


def _completed(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout)


def _blob(**overrides) -> str:
    base = {
        "name": "org/repo-a",
        "description": "a demo repo",
        "pushed_at": "2026-08-01T00:00:00Z",
        "archived": False,
        "language": "Python",
        "readme_head": "hello",
        "contributors": ["alice", "bob"],
    }
    base.update(overrides)
    return json.dumps(base)


def _good_state(tmp_path: Path, **overrides) -> dict:
    state = {
        "items": ["org/repo-a"],
        "contents": [{"value": _blob(), "_map_index": 0}],
        "findings": [
            {
                "_map_index": 0,
                "purpose": "Demonstrates the census pipeline.",
                "evidence_span": "a demo repo",
            }
        ],
        "output_path": str(tmp_path / "ledger.md"),
    }
    state.update(overrides)
    return state


class TestGhAdapters:
    @pytest.mark.req("REQ-YG-626")
    def test_discover_source_grammar_and_fixed_argv(self):
        listing = json.dumps([{"name": "repo-a"}, {"name": "repo-b"}])
        with patch(
            "examples.demos.corpus_census.adapters.corpus_adapters.subprocess.run",
            return_value=_completed(listing),
        ) as run:
            items = gh_org_discover({"source": "someorg:2"})
        argv = run.call_args[0][0]
        assert argv[:3] == ["gh", "repo", "list"]
        assert "someorg" in argv
        assert "--limit" in argv
        assert argv[argv.index("--limit") + 1] == "2"
        assert (
            run.call_args.kwargs.get("shell") is None
            or run.call_args.kwargs["shell"] is False
        )
        assert items == ["someorg/repo-a", "someorg/repo-b"]

    @pytest.mark.req("REQ-YG-626")
    @pytest.mark.parametrize("source", ["", "  ", "org:x", "org:-1", "org:0", ":5"])
    def test_discover_malformed_source_raises(self, source):
        with pytest.raises(ValueError):
            gh_org_discover({"source": source})

    @pytest.mark.req("REQ-YG-626")
    def test_discover_empty_org_raises(self):
        with (
            patch(
                "examples.demos.corpus_census.adapters.corpus_adapters.subprocess.run",
                return_value=_completed("[]"),
            ),
            pytest.raises(ValueError),
        ):
            gh_org_discover({"source": "someorg:5"})

    @pytest.mark.req("REQ-YG-626")
    def test_discover_repo_cap_enforced(self):
        listing = json.dumps([{"name": f"r{i}"} for i in range(3)])
        with patch(
            "examples.demos.corpus_census.adapters.corpus_adapters.subprocess.run",
            return_value=_completed(listing),
        ) as run:
            gh_org_discover({"source": "someorg:9999"})
        argv = run.call_args[0][0]
        assert argv[argv.index("--limit") + 1] == "100"

    @pytest.mark.req("REQ-YG-626")
    def test_discover_gh_failure_surfaces(self):
        with (
            patch(
                "examples.demos.corpus_census.adapters.corpus_adapters.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, ["gh"]),
            ),
            pytest.raises(subprocess.CalledProcessError),
        ):
            gh_org_discover({"source": "someorg:5"})

    @pytest.mark.req("REQ-YG-626")
    @pytest.mark.parametrize("item", ["", "norepo", "a/b/c"])
    def test_extract_malformed_ref_raises(self, item):
        with pytest.raises(ValueError):
            gh_repo_extract({"item": item})

    @pytest.mark.req("REQ-YG-626")
    def test_extract_bundle_keys_and_bounds(self):
        import base64

        meta = json.dumps(
            {
                "description": "d",
                "pushed_at": "2026-08-01T00:00:00Z",
                "archived": False,
                "language": "Python",
            }
        )
        readme = json.dumps({"content": base64.b64encode(b"R" * 10000).decode()})
        contributors = json.dumps([{"login": f"user{i}"} for i in range(9)])

        with patch(
            "examples.demos.corpus_census.adapters.corpus_adapters.subprocess.run",
            side_effect=[
                _completed(meta),
                _completed(readme),
                _completed(contributors),
            ],
        ):
            blob = json.loads(gh_repo_extract({"item": "org/repo-a"}))

        assert set(blob) == {
            "name",
            "description",
            "pushed_at",
            "archived",
            "language",
            "readme_head",
            "contributors",
        }
        assert blob["name"] == "org/repo-a"
        assert len(blob["readme_head"]) <= 3000
        assert blob["contributors"] == [f"user{i}" for i in range(5)]

    @pytest.mark.req("REQ-YG-626")
    def test_extract_missing_readme_yields_marker(self):
        meta = json.dumps(
            {
                "description": "d",
                "pushed_at": "2026-08-01T00:00:00Z",
                "archived": False,
                "language": None,
            }
        )
        with patch(
            "examples.demos.corpus_census.adapters.corpus_adapters.subprocess.run",
            side_effect=[
                _completed(meta),
                subprocess.CalledProcessError(1, ["gh"]),
                _completed("[]"),
            ],
        ):
            blob = json.loads(gh_repo_extract({"item": "org/repo-a"}))
        assert blob["readme_head"] == "readme: none"


class TestAzurePreflight:
    @pytest.mark.req("REQ-YG-626")
    @pytest.mark.parametrize("missing", AZURE_VARS)
    def test_preflight_missing_env_raises(self, monkeypatch, missing):
        for var in AZURE_VARS:
            monkeypatch.setenv(var, "x")
        monkeypatch.delenv(missing)
        with pytest.raises(ValueError, match=missing):
            preflight({})

    @pytest.mark.req("REQ-YG-626")
    def test_preflight_ok(self, monkeypatch):
        for var in AZURE_VARS:
            monkeypatch.setenv(var, "x")
        assert preflight({})["preflight_ok"] is True

    @pytest.mark.req("REQ-YG-626")
    def test_graph_preflight_before_discovery(self):
        graph = yaml.safe_load(GRAPH_PATH.read_text(encoding="utf-8"))
        edges = {(e["from"], e["to"]) for e in graph["edges"]}
        assert ("START", "preflight") in edges
        assert ("preflight", "discover") in edges
        assert ("START", "discover") not in edges


class TestAzurePinning:
    @staticmethod
    def _llm_nodes(graph: dict):
        for name, node in graph["nodes"].items():
            if node.get("type") == "llm":
                yield name, node
            sub = node.get("node")
            if isinstance(sub, dict) and sub.get("type") == "llm":
                yield f"{name}.node", sub

    @pytest.mark.req("REQ-YG-626")
    def test_all_llm_nodes_pinned_azure_no_fallback(self):
        graph = yaml.safe_load(GRAPH_PATH.read_text(encoding="utf-8"))
        llm_nodes = list(self._llm_nodes(graph))
        assert llm_nodes, "graph must contain LLM nodes"
        for name, node in llm_nodes:
            assert node.get("provider") == "azure", f"{name} not pinned to azure"
            assert "fallback_provider" not in node, f"{name} has fallback_provider"
        assert graph.get("defaults", {}).get("provider") == "azure"

    @pytest.mark.req("REQ-YG-626")
    def test_purpose_prompt_judges_only_purpose(self):
        prompt_files = sorted((DEMO_DIR / "prompts").glob("*.yaml"))
        judge = [p for p in prompt_files if "purpose" in p.name or "judge" in p.name]
        assert judge, "purpose-judge prompt missing"
        text = judge[0].read_text(encoding="utf-8").lower()
        for forbidden in (
            "activity",
            "active or",
            "contributor",
            "persons",
            "count the",
            "percentage",
        ):
            assert forbidden not in text, f"prompt instructs LLM on: {forbidden}"


class TestRepoLedgerReducer:
    @pytest.mark.req("REQ-YG-626")
    def test_good_state_writes_artifacts(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AZURE_MODEL", "pinned-deployment")
        result = reduce_repo_ledger(_good_state(tmp_path))["ledger"]
        assert result["rows"] == 1
        jsonl = Path(result["jsonl_path"]).read_text(encoding="utf-8")
        row = json.loads(jsonl.strip())
        assert row["name"] == "org/repo-a"
        assert row["persons"] == ["alice", "bob"]
        assert row["activity"] in {"active", "dormant", "archived"}
        assert row["model"] == "pinned-deployment"
        assert Path(result["markdown_path"]).exists()

    @pytest.mark.req("REQ-YG-626")
    def test_missing_finding_rejected(self, tmp_path):
        state = _good_state(tmp_path, findings=[])
        with pytest.raises(ValueError, match="missing"):
            reduce_repo_ledger(state)

    @pytest.mark.req("REQ-YG-626")
    def test_duplicate_finding_rejected(self, tmp_path):
        state = _good_state(tmp_path)
        state["findings"] = state["findings"] * 2
        with pytest.raises(ValueError, match="duplicate"):
            reduce_repo_ledger(state)

    @pytest.mark.req("REQ-YG-626")
    def test_empty_purpose_rejected(self, tmp_path):
        state = _good_state(tmp_path)
        state["findings"][0]["purpose"] = "  "
        with pytest.raises(ValueError):
            reduce_repo_ledger(state)

    @pytest.mark.req("REQ-YG-626")
    def test_dangling_citation_rejected(self, tmp_path):
        state = _good_state(tmp_path)
        state["findings"][0]["_map_index"] = 7
        with pytest.raises(ValueError):
            reduce_repo_ledger(state)

    @pytest.mark.req("REQ-YG-626")
    def test_malformed_activity_blob_rejected(self, tmp_path):
        blob = json.loads(_blob())
        del blob["pushed_at"]
        state = _good_state(
            tmp_path, contents=[{"value": json.dumps(blob), "_map_index": 0}]
        )
        with pytest.raises(ValueError):
            reduce_repo_ledger(state)


class TestActivityDerivation:
    @pytest.mark.req("REQ-YG-626")
    def test_archived_wins(self, tmp_path):
        state = _good_state(
            tmp_path,
            contents=[{"value": _blob(archived=True), "_map_index": 0}],
        )
        row = json.loads(
            Path(reduce_repo_ledger(state)["ledger"]["jsonl_path"]).read_text().strip()
        )
        assert row["activity"] == "archived"

    @pytest.mark.req("REQ-YG-626")
    def test_active_within_window(self, tmp_path):
        from datetime import UTC, datetime, timedelta

        recent = (datetime.now(UTC) - timedelta(days=179)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        state = _good_state(
            tmp_path, contents=[{"value": _blob(pushed_at=recent), "_map_index": 0}]
        )
        row = json.loads(
            Path(reduce_repo_ledger(state)["ledger"]["jsonl_path"]).read_text().strip()
        )
        assert row["activity"] == "active"

    @pytest.mark.req("REQ-YG-626")
    def test_dormant_outside_window(self, tmp_path):
        from datetime import UTC, datetime, timedelta

        stale = (datetime.now(UTC) - timedelta(days=181)).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = _good_state(
            tmp_path, contents=[{"value": _blob(pushed_at=stale), "_map_index": 0}]
        )
        row = json.loads(
            Path(reduce_repo_ledger(state)["ledger"]["jsonl_path"]).read_text().strip()
        )
        assert row["activity"] == "dormant"

    @pytest.mark.req("REQ-YG-626")
    def test_custom_window(self, tmp_path):
        from datetime import UTC, datetime, timedelta

        pushed = (datetime.now(UTC) - timedelta(days=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = _good_state(
            tmp_path,
            contents=[{"value": _blob(pushed_at=pushed), "_map_index": 0}],
            activity_window_days="30",
        )
        row = json.loads(
            Path(reduce_repo_ledger(state)["ledger"]["jsonl_path"]).read_text().strip()
        )
        assert row["activity"] == "dormant"


class TestPersonsVerbatim:
    @pytest.mark.req("REQ-YG-626")
    def test_llm_finding_cannot_alter_persons(self, tmp_path):
        state = _good_state(tmp_path)
        state["findings"][0]["persons"] = ["mallory"]
        row = json.loads(
            Path(reduce_repo_ledger(state)["ledger"]["jsonl_path"]).read_text().strip()
        )
        assert row["persons"] == ["alice", "bob"]

    @pytest.mark.req("REQ-YG-626")
    def test_persons_order_and_bound(self, tmp_path):
        many = [f"user{i}" for i in range(9)]
        state = _good_state(
            tmp_path, contents=[{"value": _blob(contributors=many), "_map_index": 0}]
        )
        row = json.loads(
            Path(reduce_repo_ledger(state)["ledger"]["jsonl_path"]).read_text().strip()
        )
        assert row["persons"] == many[:5]


class TestBriefTail:
    @pytest.mark.req("REQ-YG-626")
    def test_prepare_brief_input_maps_rows(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AZURE_MODEL", "pinned-deployment")
        ledger = reduce_repo_ledger(_good_state(tmp_path))["ledger"]
        out = prepare_brief_input(
            {
                "ledger": ledger,
                "brief_path": str(tmp_path / "brief.md"),
                "brief_rubric": "overall portfolio",
            }
        )["brief_input"]
        assert out[0]["item_ref"] == "org/repo-a"
        assert out[0]["judgement"] == "Demonstrates the census pipeline."

    @pytest.mark.req("REQ-YG-626")
    def test_fabricated_citation_rejected(self, tmp_path):
        from examples.demos.corpus_census.adapters import census_brief

        rows = [{"item_ref": "org/repo-a", "judgement": "x", "entries": 1}]
        claims = [{"claim_id": "c1", "text": "made up", "citations": ["row:org/ghost"]}]
        result = census_brief.emit_brief(claims, rows, str(tmp_path / "b.md"))
        assert result["accepted"] is False


class TestDataLocality:
    @pytest.mark.req("REQ-YG-626")
    def test_committed_artifacts_pin_public_org(self):
        assert PUBLIC_DEMO_ORG == "sheikkinen"
        auditable = [DEMO_DIR / "README.md", DEMO_DIR / "demo-output.log"]
        for path in auditable:
            assert path.exists(), f"missing committed artifact: {path}"
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                if "source=" in line:
                    assert PUBLIC_DEMO_ORG in line, f"unpinned source in {path}: {line}"
