"""Shared test fixtures for yamlgraph tests.

This module provides test-only Pydantic models and fixtures for testing.
These models are intentionally NOT imported from yamlgraph.models to
demonstrate that the framework is truly generic and works with any schema.
"""

import logging
import os
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, Field

from yamlgraph.models import create_initial_state

# Fixture repos are inventory surfaces, not test suites (FR-866).
collect_ignore = ["fixtures/ramp_target"]

# Suppress langsmith client finalizer "Logging error" noise during xdist
# worker shutdown (atexit race: stderr closed before logger.debug fires).
logging.getLogger("langsmith.client").setLevel(logging.WARNING)

# =============================================================================
# Tracing Off at the Session Boundary (FR-982)
# =============================================================================
# yamlgraph.config loads .env at import; a developer's LANGSMITH_TRACING=true
# would otherwise trace every test graph to their LangSmith project and make
# the tracer shell out (get_runtime_environment) underneath subprocess stubs.
# Override rather than delete: python-dotenv never overwrites an existing key,
# so "false" survives any later third-party load_dotenv(). All four aliases
# recognised by langsmith.utils.tracing_is_enabled are covered.

_TRACING_ENV_VARS = (
    "LANGSMITH_TRACING_V2",
    "LANGCHAIN_TRACING_V2",
    "LANGSMITH_TRACING",
    "LANGCHAIN_TRACING",
)

_PROCESS_BOUNDARY_PATTERNS = (
    re.compile(r"\.chaplain"),
    re.compile(r"examples/"),
    re.compile(r"scripts/"),
)
_PROCESS_BOUNDARY_ALLOWLIST: set[str] = set()


@pytest.fixture(autouse=True, scope="session")
def _tracing_off():
    """Force the LangChain/LangSmith tracer off for the whole session."""
    from langsmith.utils import get_env_var

    saved = {k: os.environ.get(k) for k in _TRACING_ENV_VARS}
    for k in _TRACING_ENV_VARS:
        os.environ[k] = "false"
    get_env_var.cache_clear()  # lru_cache: the first read is memoized
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    get_env_var.cache_clear()


# =============================================================================
# GIT_* Environment Sanitization (FR-140)
# =============================================================================
# When pre-commit runs pytest, it injects GIT_DIR, GIT_WORK_TREE, etc.
# These leak into subprocess git calls in tests that create tmp_path repos,
# causing git to operate on the pre-commit context instead of the test repo.
# Stripping at session start follows boundary normalization: sanitize external
# data where it enters the test process.


@pytest.fixture(autouse=True, scope="session")
def _clean_git_env():
    """Strip GIT_* env vars injected by pre-commit to prevent subprocess bleed."""
    git_vars = {k: v for k, v in os.environ.items() if k.startswith("GIT_")}
    for k in git_vars:
        del os.environ[k]
    yield
    os.environ.update(git_vars)


# =============================================================================
# Requirement Traceability Enforcement (ADR-001)
# =============================================================================
# Every test must be linked to a requirement via @pytest.mark.req("REQ-YG-XXX")
# This hook enforces Commandment #10: Preserve and improve the doctrine


def pytest_collection_modifyitems(config, items):
    """Enforce that every test has @pytest.mark.req decorator.

    Implements ADR-001: Requirement Traceability.
    Enforces Commandment #10: Preserve and improve the doctrine.

    Raises:
        pytest.UsageError: If any test lacks @pytest.mark.req marker.
    """
    process_boundary_violations: list[str] = []
    scanned_modules: set[str] = set()

    for item in items:
        path_obj = Path(str(item.fspath))
        try:
            rel_path = path_obj.relative_to(Path.cwd()).as_posix()
        except ValueError:
            rel_path = path_obj.as_posix()
        if not rel_path.startswith("tests/unit/") or rel_path in scanned_modules:
            continue
        scanned_modules.add(rel_path)

        if rel_path in _PROCESS_BOUNDARY_ALLOWLIST:
            continue

        source = path_obj.read_text(encoding="utf-8")
        if not any(pattern.search(source) for pattern in _PROCESS_BOUNDARY_PATTERNS):
            continue

        if "process" not in item.keywords:
            process_boundary_violations.append(rel_path)

    if process_boundary_violations:
        error_msg = (
            f"\n{'=' * 70}\n"
            f"PROCESS BOUNDARY VIOLATION (FR-756)\n"
            f"{'=' * 70}\n"
            f"{len(process_boundary_violations)} unmarked unit module(s) reference"
            f" process boundaries (.chaplain/examples/scripts):\n\n"
            + "\n".join(f"  - {path}" for path in process_boundary_violations)
            + "\n\n"
            f"Add module-level pytestmark = pytest.mark.process or record a"
            f" documented allowlist exception.\n"
            f"{'=' * 70}\n"
        )
        raise pytest.UsageError(error_msg)

    missing = []
    for item in items:
        # Check if the test has the 'req' marker
        if "req" not in item.keywords:
            missing.append(item.nodeid)

    if missing:
        error_msg = (
            f"\n{'=' * 70}\n"
            f"REQUIREMENT TRACEABILITY VIOLATION (ADR-001)\n"
            f"{'=' * 70}\n"
            f"{len(missing)} test(s) missing @pytest.mark.req('REQ-YG-XXX'):\n\n"
            + "\n".join(f"  - {nodeid}" for nodeid in missing)
            + f"\n\n"
            f"Every test must be linked to a requirement in ARCHITECTURE.md.\n"
            f"See: .github/copilot-instructions.md (Commandment #10)\n"
            f"{'=' * 70}\n"
        )
        raise pytest.UsageError(error_msg)


# =============================================================================
# Test-Only Pydantic Models (Fixtures)
# =============================================================================
# These replicate demo model structures but are defined here to prove
# the framework is generic and doesn't depend on demo-specific schemas.
# Named with "Fixture" suffix to avoid pytest collection warnings.


class FixtureGeneratedContent(BaseModel):
    """Test fixture for generated content."""

    title: str = Field(description="Title of the generated content")
    content: str = Field(description="The main generated text")
    word_count: int = Field(description="Approximate word count")
    tags: list[str] = Field(default_factory=list, description="Relevant tags")


class FixtureAnalysis(BaseModel):
    """Test fixture for content analysis."""

    summary: str = Field(description="Brief summary of the content")
    key_points: list[str] = Field(description="Main points extracted")
    sentiment: str = Field(description="Overall sentiment")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")


class FixtureToneClassification(BaseModel):
    """Test fixture for tone classification."""

    tone: str = Field(description="Detected tone: positive, negative, or neutral")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(description="Explanation for the classification")


class FixtureDraftContent(BaseModel):
    """Test fixture for draft content."""

    content: str = Field(description="The draft content")
    version: int = Field(default=1, description="Draft version number")


class FixtureCritique(BaseModel):
    """Test fixture for critique output."""

    score: float = Field(ge=0.0, le=1.0, description="Quality score 0-1")
    feedback: str = Field(description="Specific improvement suggestions")
    issues: list[str] = Field(
        default_factory=list, description="List of identified issues"
    )
    should_refine: bool = Field(
        default=True, description="Whether refinement is needed"
    )


class FixtureGitReport(BaseModel):
    """Test fixture for git report."""

    title: str = Field(description="Report title")
    summary: str = Field(description="Executive summary")
    key_findings: list[str] = Field(description="Main findings")
    recommendations: list[str] = Field(default_factory=list, description="Suggestions")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_generated_content() -> FixtureGeneratedContent:
    """Sample generated content for testing."""
    return FixtureGeneratedContent(
        title="Test Article",
        content="This is test content about artificial intelligence. " * 20,
        word_count=100,
        tags=["test", "ai"],
    )


@pytest.fixture
def sample_analysis() -> FixtureAnalysis:
    """Sample analysis for testing."""
    return FixtureAnalysis(
        summary="This is a test summary of the content.",
        key_points=["Point 1", "Point 2", "Point 3"],
        sentiment="positive",
        confidence=0.85,
    )


@pytest.fixture
def sample_state(sample_generated_content, sample_analysis) -> dict:
    """Complete sample state for testing."""
    state = create_initial_state(
        topic="artificial intelligence",
        style="informative",
        word_count=300,
        thread_id="test123",
    )
    state["generated"] = sample_generated_content
    state["analysis"] = sample_analysis
    state["final_summary"] = "This is the final summary."
    state["current_step"] = "summarize"
    return state


@pytest.fixture
def empty_state() -> dict:
    """Initial empty state for testing."""
    return create_initial_state(
        topic="test topic",
        style="casual",
        word_count=200,
    )


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Temporary output directory for testing."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_llm_response():
    """Mock LLM that returns predictable responses."""

    def _create_mock(response_content: str | dict = "Mocked response"):
        mock = MagicMock()
        mock_response = MagicMock()
        mock_response.content = response_content
        mock.invoke.return_value = mock_response
        return mock

    return _create_mock


@pytest.fixture
def mock_structured_llm(sample_generated_content, sample_analysis):
    """Mock LLM with structured output support."""

    def _create_mock(model_type: str):
        mock = MagicMock()
        if model_type == "generate":
            mock.invoke.return_value = sample_generated_content
        elif model_type == "analyze":
            mock.invoke.return_value = sample_analysis
        else:
            mock.invoke.return_value = "Mocked summary"
        return mock

    return _create_mock
