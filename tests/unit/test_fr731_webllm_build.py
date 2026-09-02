"""FR-731 WebLLM browser prompt demo — compiler + page contract tests.

AC-01: build.py compiles critique.yaml (native inline schema) to a
prompt.json whose json_schema preserves constraint fidelity
(ge/le -> minimum/maximum) and whose user_template keeps placeholders
verbatim. F3: the artifact carries no deployment config (model_id).
AC-02: the committed artifact is byte-identical to a rebuild (F5:
sort_keys serialization makes this well-defined).
AC-03/F4: the page defers the weight download to an explicit consent
click and gates on navigator.gpu — checked mechanically.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_PY = REPO_ROOT / "examples" / "webllm-demo" / "build.py"
ARTIFACT = REPO_ROOT / "docs" / "demos" / "webllm" / "prompt.json"
INDEX_HTML = REPO_ROOT / "docs" / "demos" / "webllm" / "index.html"


def _load_build_module():
    """Import build.py by path (directory name contains a hyphen)."""
    spec = importlib.util.spec_from_file_location("webllm_build", BUILD_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def build_mod():
    if not BUILD_PY.exists():
        pytest.fail(f"missing compiler: {BUILD_PY}")
    return _load_build_module()


@pytest.fixture(scope="module")
def payload(build_mod) -> dict:
    return build_mod.build_prompt_json()


@pytest.mark.req("REQ-YG-562")
class TestBuildPromptJson:
    """AC-01 — mechanical compile of prompt YAML to WebLLM contract."""

    def test_artifact_keys_exact(self, payload):
        """F3: no model_id — deployment config must not ride the artifact."""
        assert set(payload) == {"name", "system", "user_template", "json_schema"}

    def test_required_fields(self, payload):
        required = set(payload["json_schema"]["required"])
        assert {"score", "feedback"} <= required
        # defaulted fields are not required
        assert "issues" not in required
        assert "should_refine" not in required

    def test_score_constraints_survive(self, payload):
        """ge/le must reach JSON Schema as minimum/maximum (FR-731 F2)."""
        score = payload["json_schema"]["properties"]["score"]
        assert score["minimum"] == 0.0
        assert score["maximum"] == 1.0

    def test_placeholders_verbatim(self, payload):
        assert "{iteration}" in payload["user_template"]
        assert "{content}" in payload["user_template"]

    def test_system_prompt_carried(self, payload):
        assert "essay" in payload["system"].lower()

    def test_json_directive_appended(self, payload):
        """Kill-criterion root cause (2026-07-15): grammar masking without
        prompt-side JSON steering floods whitespace — WebLLM's own examples
        state the prompt must mention JSON. The directive is part of the
        mechanical compile, not per-prompt hand-tuning."""
        assert "single JSON object" in payload["system"]

    def test_directive_is_schema_agnostic(self, payload):
        """The directive must not encode field names — it is generic
        compile-path output, valid for any prompt with a schema."""
        directive = payload["system"].split("\n")[-1]
        assert "score" not in directive


@pytest.mark.req("REQ-YG-562")
class TestArtifactIdempotence:
    """AC-02 — committed artifact matches rebuild, byte for byte (F5)."""

    def test_artifact_committed(self):
        assert ARTIFACT.exists(), f"missing committed artifact: {ARTIFACT}"

    def test_rebuild_is_noop(self, build_mod, payload):
        assert build_mod.serialize(payload) == ARTIFACT.read_text(encoding="utf-8")

    def test_serialization_deterministic(self, build_mod):
        a = build_mod.serialize(build_mod.build_prompt_json())
        b = build_mod.serialize(build_mod.build_prompt_json())
        assert a == b


@pytest.mark.req("REQ-YG-562")
class TestPageConsentGate:
    """AC-03/F4 — mechanical source inspection of the demo page."""

    @pytest.fixture(scope="class")
    def html(self) -> str:
        if not INDEX_HTML.exists():
            pytest.fail(f"missing page: {INDEX_HTML}")
        return INDEX_HTML.read_text(encoding="utf-8")

    def test_capability_gate_present(self, html):
        assert "navigator.gpu" in html

    def test_engine_creation_inside_click_handler(self, html):
        """Weight download must not start before the user gesture."""
        click = html.find('addEventListener("click"')
        create = html.find("CreateMLCEngine")
        assert click != -1, "no click handler registration found"
        assert create != -1, "no engine creation call found"
        assert create > click, "engine created before consent click handler"

    def test_engine_created_once(self, html):
        assert html.count("CreateMLCEngine") == 1

    def test_size_disclosure_before_download(self, html):
        assert "GB" in html, "model download size must be disclosed"

    def test_no_module_level_model_fetch(self, html):
        """Only the esm.run library import and prompt.json load may precede
        consent; no model artifact URL at module top level."""
        consent = html.find('addEventListener("click"')
        head = html[:consent]
        assert "mlc.ai/models" not in head
        assert "huggingface" not in head.lower()

    def test_temperature_zero(self, html):
        assert "temperature: 0" in html

    def test_max_tokens_bounded(self, html):
        """Degenerate runs must be bounded — the unbounded flood cost 87 s
        per run; upstream json-mode examples all set max_tokens."""
        assert "max_tokens:" in html
