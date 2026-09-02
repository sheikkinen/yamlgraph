"""Tests for FR-881: Image Pipeline v3 — local-model generator.

Validates sample_candidates (JSONL subprocess contract, first-k-passer
selection, fail-fast paths), the v3 save_report output path, the v2
output-path regression (judgement R-4), and the no-llm-node graph
contract. Render reuses v1's generate_images_node.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V3_DIR = REPO_ROOT / "examples" / "image_pipeline_v3"


def _candidate(ordinal: int, prompt: str) -> str:
    return json.dumps(
        {
            "record": "candidate",
            "ordinal": ordinal,
            "prompt": prompt,
            "attempts_for_candidate": ordinal,
            "verdict_counts": {"pass": 1},
            "seed": 42,
            "temp": 0.8,
            "top_k": 40,
            "cond": "prose",
            "start": "",
            "ckpt_sha": "c" * 12,
            "corpus_sha": "d" * 12,
            "git_sha": "e" * 40,
        }
    )


def _summary(attempts: int = 12) -> str:
    return json.dumps(
        {
            "record": "summary",
            "attempts": attempts,
            "verdict_counts": {"pass": 10, "shape": 2},
            "seed": 42,
            "temp": 0.8,
            "top_k": 40,
            "cond": "prose",
            "start": "",
            "ckpt_sha": "c" * 12,
            "corpus_sha": "d" * 12,
            "git_sha": "e" * 40,
        }
    )


@pytest.mark.req("REQ-YG-198")
class TestSampleCandidates:
    def _dd(self, tmp_path, monkeypatch) -> Path:
        dd = tmp_path / "dd"
        (dd / ".venv" / "bin").mkdir(parents=True)
        (dd / ".venv" / "bin" / "python").touch()
        (dd / "training" / "ckpt").mkdir(parents=True)
        (dd / "training" / "ckpt" / "model.pt").touch()
        (dd / "prompts").mkdir()
        (dd / "prompts" / "corpus.jsonl").write_text("{}", encoding="utf-8")
        monkeypatch.setenv("DEVIANT_DAILY_DIR", str(dd))
        return dd

    def _run(self, monkeypatch, tmp_path, stdout: str, state: dict | None = None):
        from examples.image_pipeline_v3.nodes.sample_candidates import (
            sample_candidates_node,
        )

        self._dd(tmp_path, monkeypatch)
        completed = type("CP", (), {"returncode": 0, "stdout": stdout, "stderr": ""})()
        with patch(
            "examples.image_pipeline_v3.nodes.sample_candidates.subprocess.run",
            return_value=completed,
        ):
            return sample_candidates_node(
                {"n_candidates": "3", "top_k": "2", "start": "", **(state or {})}
            )

    def test_first_k_passers_selected_in_order(self, monkeypatch, tmp_path):
        stdout = "\n".join(
            [
                _candidate(1, "p one"),
                _candidate(2, "p two"),
                _candidate(3, "p three"),
                _summary(),
            ]
        )
        result = self._run(monkeypatch, tmp_path, stdout)
        assert result["prompts"] == ["p one", "p two"]
        assert [r["selected"] for r in result["scored"]] == [True, True, False]

    def test_summary_recorded(self, monkeypatch, tmp_path):
        stdout = "\n".join([_candidate(1, "p"), _summary(attempts=7)])
        result = self._run(monkeypatch, tmp_path, stdout)
        assert result["gen_summary"]["attempts"] == 7

    def test_missing_env_fails_fast(self, monkeypatch):
        from examples.image_pipeline_v3.nodes.sample_candidates import (
            sample_candidates_node,
        )

        monkeypatch.delenv("DEVIANT_DAILY_DIR", raising=False)
        with pytest.raises(RuntimeError, match="DEVIANT_DAILY_DIR"):
            sample_candidates_node({"n_candidates": "3", "top_k": "2"})

    def test_missing_ckpt_fails_fast(self, monkeypatch, tmp_path):
        from examples.image_pipeline_v3.nodes.sample_candidates import (
            sample_candidates_node,
        )

        dd = self._dd(tmp_path, monkeypatch)
        (dd / "training" / "ckpt" / "model.pt").unlink()
        with pytest.raises(RuntimeError, match="training.train"):
            sample_candidates_node({"n_candidates": "3", "top_k": "2"})

    def test_malformed_json_fails_fast(self, monkeypatch, tmp_path):
        with pytest.raises(RuntimeError, match="JSONL"):
            self._run(monkeypatch, tmp_path, "not json at all\n")

    def test_no_llm_fallback_exists(self):
        source = (V3_DIR / "nodes" / "sample_candidates.py").read_text(encoding="utf-8")
        assert "create_llm" not in source
        assert "execute_prompt" not in source


@pytest.mark.req("REQ-YG-198")
class TestSaveReportV3:
    def _scored(self) -> list[dict]:
        return [
            {
                "ordinal": 1,
                "prompt": "secret full text",
                "prompt_sha": "a" * 12,
                "attempts_for_candidate": 2,
                "selected": True,
                "ckpt_sha": "c" * 12,
                "corpus_sha": "d" * 12,
                "git_sha": "e" * 40,
            }
        ]

    def test_writes_under_v3_output(self, tmp_path, monkeypatch):
        from examples.image_pipeline_v3.nodes.save_report import save_report_node

        monkeypatch.chdir(tmp_path)
        result = save_report_node(
            {
                "scored": self._scored(),
                "gen_summary": {"attempts": 3, "verdict_counts": {}},
            }
        )
        assert "outputs/image_pipeline_v3" in result["output_dir"]
        assert Path(result["report_file"]).exists()

    def test_sanitized_report_has_no_prompt_text(self, tmp_path, monkeypatch):
        from examples.image_pipeline_v3.nodes.save_report import save_report_node

        monkeypatch.chdir(tmp_path)
        result = save_report_node(
            {
                "scored": self._scored(),
                "gen_summary": {"attempts": 3, "verdict_counts": {}},
            }
        )
        assert "secret full text" not in Path(result["report_file"]).read_text(encoding="utf-8")
        assert "secret full text" in Path(result["local_report_file"]).read_text(encoding="utf-8")

    def test_v2_output_path_regression(self):
        """R-4: v2 must keep writing under outputs/image_pipeline_v2."""
        from examples.image_pipeline_v2.nodes.save_report import OUTPUT_BASE

        assert str(OUTPUT_BASE) == "outputs/image_pipeline_v2"


@pytest.mark.req("REQ-YG-198")
class TestGraphContract:
    def test_graph_has_no_llm_node(self):
        graph = yaml.safe_load((V3_DIR / "graph.yaml").read_text(encoding="utf-8"))
        types = {n.get("type") for n in graph["nodes"].values()}
        assert "llm" not in types
        assert "prompts" not in graph or not graph.get("prompts")

    def test_graph_wires_sample_report_render(self):
        graph = yaml.safe_load((V3_DIR / "graph.yaml").read_text(encoding="utf-8"))
        assert {"sample_candidates", "save_report", "generate_images"} <= set(
            graph["nodes"]
        )
