"""Integration utilities for watcher2 baseline import."""

from pathlib import Path
from typing import List


def prepare_watcher2_import(baseline_dir: Path) -> List[str]:
    """
    Prepare import arguments for watcher2 integration.
    
    Args:
        baseline_dir: Path to baseline directory containing latest.json
        
    Returns:
        List[str]: Command line arguments for --import-state
    """
    latest_path = baseline_dir / "latest.json"
    
    if not latest_path.exists():
        raise FileNotFoundError(f"Baseline artifact not found: {latest_path}")
    
    return ["--import-state", str(latest_path)]