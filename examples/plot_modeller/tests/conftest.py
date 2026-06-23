"""Pytest fixtures path setup for the plot_modeller example.

Inserts the example root on ``sys.path`` at collection time so test modules can
``from nodes.tools import ...`` with a normal top-level import.
"""

from __future__ import annotations

import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent.parent
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))
