"""Root README accuracy contract tests (FR-313)."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
LAST_REVIEWED_LINE = "Last reviewed: 2026-05-03"

EXPECTED_PROVIDERS = (
    "anthropic",
    "azure",
    "deepseek",
    "google",
    "inception",
    "lmstudio",
    "mistral",
    "openai",
    "replicate",
    "vertex",
    "xai",
)


def _read_root_readme() -> str:
    assert README_PATH.exists(), f"Root README missing: {README_PATH}"
    return README_PATH.read_text()


def _provider_row(readme: str) -> str:
    for line in readme.splitlines():
        if line.startswith("| `PROVIDER` |"):
            return line.lower()
    raise AssertionError("README provider row missing: '| `PROVIDER` |'")


@pytest.mark.req("REQ-YG-317")
def test_provider_row_includes_all_supported_providers():
    """Root README provider row must list all supported provider identifiers."""
    row = _provider_row(_read_root_readme())
    missing = [provider for provider in EXPECTED_PROVIDERS if provider not in row]
    assert not missing, f"README provider row missing providers: {missing}"


@pytest.mark.req("REQ-YG-317")
def test_readme_does_not_use_hardcoded_reference_doc_count():
    """Root README must avoid fragile 'all <number> reference docs' phrasing."""
    readme = _read_root_readme()
    assert not re.search(r"all\s+\d+\s+reference docs", readme, flags=re.IGNORECASE)


@pytest.mark.req("REQ-YG-317")
def test_last_reviewed_timestamp_is_present_at_end_of_readme():
    """Root README must end with the explicit review timestamp line."""
    lines = _read_root_readme().rstrip("\n").splitlines()
    assert lines, "README must not be empty"
    assert lines[-1] == LAST_REVIEWED_LINE
