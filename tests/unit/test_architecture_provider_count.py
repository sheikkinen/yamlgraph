"""Tests for ARCHITECTURE.md ↔ code provider count consistency.

FR-121: Ensures the provider count in ARCHITECTURE.md module table matches
the actual ProviderType Literal in llm_factory.py.
"""

import re
from pathlib import Path
from typing import get_args

import pytest

from yamlgraph.utils.llm_factory import ProviderType

# Repository root (two levels up from tests/unit/)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.req("REQ-YG-121")
class TestArchitectureProviderCount:
    """ARCHITECTURE.md must reflect the actual number of LLM providers."""

    def test_module_table_provider_count_matches_code(self) -> None:
        """Provider count in module table must equal len(get_args(ProviderType))."""
        actual_count = len(get_args(ProviderType))

        arch_path = REPO_ROOT / "ARCHITECTURE.md"
        text = arch_path.read_text()

        # Match the module table row for llm_factory.py
        # e.g. "| `utils/llm_factory.py` | Multi-provider LLM factory (8 providers) | 3 |"
        match = re.search(
            r"\|\s*`utils/llm_factory\.py`\s*\|[^|]*\((\d+)\s+providers?\)",
            text,
        )
        assert match, "Could not find llm_factory.py provider count in ARCHITECTURE.md"

        documented_count = int(match.group(1))
        assert documented_count == actual_count, (
            f"ARCHITECTURE.md says {documented_count} providers "
            f"but ProviderType has {actual_count}"
        )

    def test_provider_type_has_expected_providers(self) -> None:
        """Smoke-test: ProviderType contains known providers."""
        providers = set(get_args(ProviderType))
        expected = {
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
        }
        assert providers == expected, (
            f"ProviderType mismatch.\n"
            f"  Missing: {expected - providers}\n"
            f"  Extra:   {providers - expected}"
        )
