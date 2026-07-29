"""Centralized configuration for the yamlgraph package.

Provides paths, settings, and environment configuration
used across all modules.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


def _locate_env_file(start: Path) -> Path | None:
    """Walk upward from *start* to find .env, stopping at .git directory boundary.

    Worktrees use a .git file instead of a directory, so boundary detection must
    use .is_dir() to keep searching toward the main repo root.
    """
    current = start.resolve()
    while True:
        candidate = current / ".env"
        if candidate.is_file():
            return candidate

        # Stop at real git repository boundary, but not worktree .git files.
        if (current / ".git").is_dir():
            return None

        parent = current.parent
        if parent == current:
            return None
        current = parent


# Package root (yamlgraph/ directory)
PACKAGE_ROOT = Path(__file__).parent

# Working directory (where the user runs the CLI from)
WORKING_DIR = Path.cwd()

# Load environment variables by searching upward from CWD.
_DOTENV_PATH = _locate_env_file(WORKING_DIR)
if _DOTENV_PATH:
    load_dotenv(_DOTENV_PATH)

# Directory paths (relative to working directory)
PROMPTS_DIR = WORKING_DIR / "prompts"
GRAPHS_DIR = WORKING_DIR / "graphs"
OUTPUTS_DIR = WORKING_DIR / "outputs"
DATABASE_PATH = OUTPUTS_DIR / "yamlgraph.db"

# Default graph configuration (demo location)
DEFAULT_GRAPH = WORKING_DIR / "examples" / "demos" / "yamlgraph" / "graph.yaml"

# Execution Safety (FR-027)
DEFAULT_RECURSION_LIMIT = 50
DEFAULT_MAX_MAP_ITEMS = 100

# LLM Configuration
DEFAULT_TEMPERATURE = 0.7

# Default models per provider (override with {PROVIDER}_MODEL env var)
# API keys expected in .env:
#   ANTHROPIC_API_KEY, GOOGLE_API_KEY, MISTRAL_API_KEY, OPENAI_API_KEY,
#   REPLICATE_API_TOKEN, XAI_API_KEY
DEFAULT_MODELS = {
    "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
    "deepseek": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    "google": os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
    "inception": os.getenv("INCEPTION_MODEL", "mercury-2"),
    "lmstudio": os.getenv("LMSTUDIO_MODEL", "qwen2.5-coder-7b-instruct"),
    "mistral": os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
    "openai": os.getenv("OPENAI_MODEL", "gpt-4o"),
    "replicate": os.getenv("REPLICATE_MODEL", "ibm-granite/granite-4.0-h-small"),
    # FR-766: no hard-coded default — a RunPod endpoint serves exactly the
    # model it was deployed with; the factory fails fast on empty model.
    "runpod": os.getenv("RUNPOD_MODEL", ""),
    "vertex": os.getenv("VERTEX_MODEL", "gemini-2.0-flash"),
    "xai": os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning"),
    "azure": os.getenv("AZURE_MODEL", "gpt-4o"),
}

# Retry Configuration
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
RETRY_BASE_DELAY = float(os.getenv("LLM_RETRY_DELAY", "1.0"))  # seconds
RETRY_MAX_DELAY = float(os.getenv("LLM_RETRY_MAX_DELAY", "30.0"))  # seconds

# CLI Constraints - configurable via environment
MAX_TOPIC_LENGTH = int(os.getenv("YAMLGRAPH_MAX_TOPIC_LENGTH", "500"))
MAX_WORD_COUNT = int(os.getenv("YAMLGRAPH_MAX_WORD_COUNT", "5000"))
MIN_WORD_COUNT = int(os.getenv("YAMLGRAPH_MIN_WORD_COUNT", "50"))

# Valid styles - can be extended via environment (comma-separated)
_default_styles = "informative,casual,technical"
VALID_STYLES = tuple(os.getenv("YAMLGRAPH_VALID_STYLES", _default_styles).split(","))

# Input Sanitization Patterns
# Characters that could be used for prompt injection
DANGEROUS_PATTERNS = [
    "ignore previous",
    "ignore above",
    "disregard",
    "forget everything",
    "new instructions",
    "system:",
    "<|",  # Token delimiters
    "|>",
]
