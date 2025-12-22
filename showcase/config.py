"""Centralized configuration for the showcase package.

Provides paths, settings, and environment configuration
used across all modules.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Package root (showcase/ directory)
PACKAGE_ROOT = Path(__file__).parent

# Project root (parent of showcase/)
PROJECT_ROOT = PACKAGE_ROOT.parent

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")

# Directory paths
PROMPTS_DIR = PROJECT_ROOT / "prompts"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DATABASE_PATH = OUTPUTS_DIR / "showcase.db"

# LLM Configuration
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096

# CLI Constraints
MAX_TOPIC_LENGTH = 500
MAX_WORD_COUNT = 5000
MIN_WORD_COUNT = 50
VALID_STYLES = ("informative", "casual", "technical")
