"""Retention policy for baseline artifacts."""

import os
from pathlib import Path
from typing import List


def cleanup_old_baselines(baseline_dir: Path, keep_latest: int = 5):
    """
    Cleanup old baseline artifacts, keeping only the latest N.
    
    Args:
        baseline_dir: Directory containing baseline artifacts
        keep_latest: Number of latest artifacts to keep (default: 5)
    """
    baseline_dir = Path(baseline_dir)
    
    # Find all baseline artifact files
    baseline_files = list(baseline_dir.glob("baseline_*.json"))
    
    if len(baseline_files) <= keep_latest:
        # Nothing to cleanup
        return
    
    # Sort by modification time (newest first)
    baseline_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    # Keep the latest N, remove the rest
    files_to_remove = baseline_files[keep_latest:]
    
    for file_path in files_to_remove:
        try:
            file_path.unlink()
        except OSError:
            # Log error but continue cleanup
            pass