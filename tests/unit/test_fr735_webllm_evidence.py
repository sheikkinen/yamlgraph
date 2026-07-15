"""FR-735 WebLLM demo evidence ergonomics — lexical page tests.

Same weight class as FR-731 F4: mechanical source inspection of
docs/demos/webllm/index.html. Judgement pins witnessed here:
F1 tok/s fallback chain, F2 per-session labeling, F3 single
.message.content read flowing to both Blob and DOM, F6 best-effort
GPU info.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "docs" / "demos" / "webllm" / "index.html"


@pytest.fixture(scope="module")
def html() -> str:
    return INDEX_HTML.read_text()


@pytest.mark.req("REQ-YG-562")
class TestConsoleDiagnostics:
    """AC-01 — the console carries structured run records."""

    def test_run_record_logged(self, html):
        assert 'console.log("webllm-run"' in html

    def test_record_carries_raw_chars(self, html):
        assert "raw_chars" in html

    def test_load_diagnostics_logged(self, html):
        assert 'console.log("webllm-load"' in html


@pytest.mark.req("REQ-YG-562")
class TestSaveLinks:
    """AC-02 — byte-fidelity download links."""

    def test_object_url_used(self, html):
        assert "URL.createObjectURL" in html

    def test_download_attribute_present(self, html):
        assert "download" in html

    def test_raw_read_once(self, html):
        """F3: .message.content is read exactly once, into one identifier."""
        assert html.count(".message.content") == 1

    def test_blob_receives_same_identifier(self, html):
        """F3: the Blob is built from the identifier assigned above."""
        assert "const raw = reply.choices[0].message.content" in html
        assert "new Blob([raw]" in html


@pytest.mark.req("REQ-YG-562")
class TestEvidenceBundle:
    """AC-03 — evidence.md in FR-731 F1 shape."""

    def test_tally_table_header(self, html):
        assert "| run | schema_valid | score | ms | tok/s | raw_chars |" in html

    def test_kill_criterion_computed(self, html):
        assert "failures:" in html

    def test_short_session_note(self, html):
        """F2: M < 10 is visible, not deniable."""
        assert "protocol requires 10" in html

    def test_session_id_in_header(self, html):
        """F2: per-session labeling."""
        assert "SESSION_ID" in html


@pytest.mark.req("REQ-YG-562")
class TestMetricsHonesty:
    """F1 — tok/s fallback chain, never fabricated."""

    def test_usage_field_preferred(self, html):
        assert "decode_tokens_per_s" in html

    def test_computed_proxy_labeled(self, html):
        assert "tok/s*" in html


@pytest.mark.req("REQ-YG-562")
class TestGpuInfoBestEffort:
    """F6 — adapter info recorded when available, never blocking."""

    def test_adapter_requested(self, html):
        assert "requestAdapter" in html

    def test_raw_chars_displayed(self, html):
        """Run-1 lesson: a whitespace flood looks empty; the count says
        otherwise."""
        assert 'id="raw-meta"' in html
