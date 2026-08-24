"""Tests for FR-879: Image Pipeline v2 — critic-filtered prompts.

Validates score_filter (subprocess contract, Pydantic row validation,
survivor selection, fail-fast paths) and save_report (local full table
vs sanitized committed table). Render reuses v1's generate_images_node.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V2_DIR = REPO_ROOT / "examples" / "image_pipeline_v2"


def _row(sha: str, nll: float, verdict: str, band: str = "in_band") -> str:
    return json.dumps(
        {
            "prompt_sha": sha,
            "register": "<prose>",
            "nll_per_char": nll,
            "truncated": False,
            "band": band,
            "boundary": "pass" if verdict in ("pass", f"band:{band}") else verdict,
            "boundary_reason": "ok",
            "verdict": verdict,
            "ckpt_sha": "c" * 12,
            "corpus_sha": "d" * 12,
            "git_sha": "e" * 40,
        }
    )


def _sha(text: str) -> str:
    import hashlib

    return hashlib.sha1(text.encode(), usedforsecurity=False).hexdigest()[:12]


@pytest.mark.req("REQ-YG-198")
class TestScoreFilter:
    def _run(self, monkeypatch, tmp_path, prompts, stdout_lines, returncode=0):
        from examples.image_pipeline_v2.nodes.score_filter import score_filter_node

        dd = tmp_path / "dd"
        (dd / ".venv" / "bin").mkdir(parents=True)
        (dd / ".venv" / "bin" / "python").touch()
        (dd / "training" / "ckpt").mkdir(parents=True)
        (dd / "training" / "ckpt" / "model.pt").touch()
        (dd / "training" / "ckpt" / "calibration.json").write_text("{}")
        monkeypatch.setenv("DEVIANT_DAILY_DIR", str(dd))

        completed = type(
            "CP",
            (),
            {"returncode": returncode, "stdout": "\n".join(stdout_lines), "stderr": ""},
        )()
        with patch(
            "examples.image_pipeline_v2.nodes.score_filter.subprocess.run",
            return_value=completed,
        ):
            state = {"candidates": {"prompts": prompts}, "top_k": "2"}
            return score_filter_node(state)

    def test_selects_top_k_pass_rows_by_nll(self, monkeypatch, tmp_path):
        prompts = ["alpha prompt", "beta prompt", "gamma prompt"]
        lines = [
            _row(_sha(prompts[0]), 1.2, "pass"),
            _row(_sha(prompts[1]), 0.9, "pass"),
            _row(_sha(prompts[2]), 1.9, "band:too_unlikely", band="too_unlikely"),
        ]
        out = self._run(monkeypatch, tmp_path, prompts, lines)
        assert out["prompts"] == ["beta prompt", "alpha prompt"]
        assert len(out["scored"]) == 3

    def test_zero_survivors_raises(self, monkeypatch, tmp_path):
        prompts = ["alpha prompt"]
        lines = [_row(_sha(prompts[0]), 2.5, "band:too_unlikely", band="too_unlikely")]
        with pytest.raises(RuntimeError, match="zero survivors"):
            self._run(monkeypatch, tmp_path, prompts, lines)

    def test_malformed_row_raises(self, monkeypatch, tmp_path):
        with pytest.raises(ValueError):
            self._run(monkeypatch, tmp_path, ["alpha prompt"], ["{not json"])

    def test_sha_mismatch_raises(self, monkeypatch, tmp_path):
        lines = [_row("f" * 12, 1.0, "pass")]
        with pytest.raises(ValueError, match="sha"):
            self._run(monkeypatch, tmp_path, ["alpha prompt"], lines)

    def test_nonzero_exit_raises(self, monkeypatch, tmp_path):
        with pytest.raises(RuntimeError, match="scorer failed"):
            self._run(monkeypatch, tmp_path, ["alpha prompt"], [], returncode=3)

    def test_missing_clone_fails_fast_with_commands(self, monkeypatch, tmp_path):
        from examples.image_pipeline_v2.nodes.score_filter import score_filter_node

        monkeypatch.setenv("DEVIANT_DAILY_DIR", str(tmp_path / "nope"))
        with pytest.raises(RuntimeError, match="training.train"):
            score_filter_node({"candidates": {"prompts": ["x"]}, "top_k": "2"})

    def test_missing_env_fails_fast(self, monkeypatch):
        from examples.image_pipeline_v2.nodes.score_filter import score_filter_node

        monkeypatch.delenv("DEVIANT_DAILY_DIR", raising=False)
        with pytest.raises(RuntimeError, match="DEVIANT_DAILY_DIR"):
            score_filter_node({"candidates": {"prompts": ["x"]}, "top_k": "2"})


@pytest.mark.req("REQ-YG-198")
class TestSaveReport:
    def test_sanitized_table_has_no_full_text(self, tmp_path, monkeypatch):
        from examples.image_pipeline_v2.nodes import save_report

        monkeypatch.setattr(save_report, "OUTPUT_BASE", tmp_path)
        full_text = "very identifiable full prompt text about lanterns"
        state = {
            "scored": [
                {
                    "prompt": full_text,
                    "prompt_sha": "a" * 12,
                    "register": "<prose>",
                    "nll_per_char": 1.0,
                    "band": "in_band",
                    "boundary_reason": "ok",
                    "verdict": "pass",
                    "selected": True,
                }
            ],
            "prompts": [full_text],
        }
        out = save_report.save_report_node(state)
        sanitized = Path(out["report_file"]).read_text()
        assert "lanterns" not in sanitized
        assert "a" * 12 in sanitized and "in_band" in sanitized
        local = Path(out["local_report_file"]).read_text()
        assert "lanterns" in local

    def test_output_dir_returned(self, tmp_path, monkeypatch):
        from examples.image_pipeline_v2.nodes import save_report

        monkeypatch.setattr(save_report, "OUTPUT_BASE", tmp_path)
        out = save_report.save_report_node({"scored": [], "prompts": []})
        assert Path(out["output_dir"]).is_dir()


@pytest.mark.req("REQ-YG-198")
class TestV2GraphContract:
    def test_no_provider_or_model_overrides(self):
        import yaml

        graph = yaml.safe_load((V2_DIR / "graph.yaml").read_text())
        assert "provider" not in (graph.get("defaults") or {})
        for name, node in graph["nodes"].items():
            assert "provider" not in node, f"node {name} overrides provider"
            assert "model" not in node, f"node {name} overrides model"
        for pf in (V2_DIR / "prompts").glob("*.yaml"):
            pdata = yaml.safe_load(pf.read_text())
            assert "provider" not in pdata and "model" not in pdata

    def test_candidate_prompt_declares_schema(self):
        import yaml

        pdata = yaml.safe_load(
            (V2_DIR / "prompts" / "generate_candidates.yaml").read_text()
        )
        assert "schema" in pdata
        assert "prompts" in pdata["schema"]["fields"]

    def test_v1_untouched_by_v2(self):
        # v2 must not add files into v1's directory
        v1 = REPO_ROOT / "examples" / "image_pipeline"
        assert not (v1 / "graph2.yaml").exists()
        assert (V2_DIR / "graph.yaml").exists()
