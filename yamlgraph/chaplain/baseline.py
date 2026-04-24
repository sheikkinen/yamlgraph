"""Core baseline functionality for FR-277 Watcher2 Baseline Checkpointing.

This module provides functions for:
- Computing deterministic baseline IDs
- Managing baseline rebuild logic
- Summary cache key computation and reuse
- Latest symlink management
- State assembly and import
- Retention policy enforcement
"""

import hashlib
from pathlib import Path
from typing import Any


def compute_baseline_id(manifest: dict, source_files: dict[str, str]) -> str:
    """Compute deterministic BASELINE_ID from manifest and source files.

    Args:
        manifest: Baseline manifest dictionary
        source_files: Dict mapping file paths to content

    Returns:
        64-character SHA256 hash as BASELINE_ID
    """
    # Hash algorithm from FR-277:
    # - Normalize line endings to \n
    # - Expand patterns in sorted path order
    # - Concatenate path + sha256(content) in resolved order
    # - BASELINE_ID = sha256(concatenated_entries + manifest_version)

    concatenated_entries = []

    # Sort file paths for deterministic ordering
    for file_path in sorted(source_files.keys()):
        content = source_files[file_path]

        # Normalize line endings
        normalized_content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Compute content hash
        content_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()

        # Append path + content hash
        concatenated_entries.append(f"{file_path}:{content_hash}")

    # Add manifest version
    manifest_version = manifest.get("manifest_version", 1)

    # Compute final baseline ID
    full_content = (
        "\n".join(concatenated_entries) + f"\nmanifest_version:{manifest_version}"
    )
    baseline_id = hashlib.sha256(full_content.encode("utf-8")).hexdigest()

    return baseline_id


def should_rebuild_baseline(baseline_id: str, baseline_dir: Path) -> bool:
    """Check if baseline needs to be rebuilt.

    Args:
        baseline_id: Computed baseline ID
        baseline_dir: Directory containing baseline artifacts

    Returns:
        True if rebuild needed, False if existing baseline can be reused
    """
    baseline_file = baseline_dir / f"{baseline_id}.json"
    return not baseline_file.exists()


def compute_summary_cache_key(content: str, prompt_version: str, model: str) -> str:
    """Compute deterministic cache key for summary reuse.

    Args:
        content: Source content to summarize
        prompt_version: Summary prompt version identifier
        model: Model name used for summarization

    Returns:
        64-character SHA256 hash as cache key
    """
    cache_input = f"{content}|{prompt_version}|{model}"
    return hashlib.sha256(cache_input.encode("utf-8")).hexdigest()


def resolve_summary_with_cache(
    content: str, cache_key: str, cached_summaries: dict[str, str]
) -> str:
    """Resolve summary using cache or generate new one.

    Args:
        content: Source content to summarize
        cache_key: Computed cache key
        cached_summaries: Dict of cache_key -> summary

    Returns:
        Cached or newly generated summary
    """
    if cache_key in cached_summaries:
        return cached_summaries[cache_key]

    # In real implementation, this would generate new summary via LLM
    # For tests, we return a placeholder
    return f"Generated summary for content: {content[:50]}..."


def update_latest_symlink(baseline_dir: Path, baseline_id: str) -> None:
    """Update latest.json symlink to point to current baseline.

    Args:
        baseline_dir: Directory containing baseline artifacts
        baseline_id: Current baseline ID
    """
    latest_path = baseline_dir / "latest.json"
    target_path = f"{baseline_id}.json"

    # Remove existing symlink if it exists
    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()

    # Create new symlink
    latest_path.symlink_to(target_path)


def assemble_baseline_state(baseline_data: dict[str, Any]) -> dict[str, Any]:
    """Assemble baseline data into namespaced state dict.

    Args:
        baseline_data: Raw baseline data

    Returns:
        Dict with all keys prefixed with 'baseline_'
    """
    state = {}

    # Add baseline_ prefix to all keys
    for key, value in baseline_data.items():
        state[f"baseline_{key}"] = value

    return state


def import_baseline_state(
    existing_state: dict[str, Any], baseline_state: dict[str, Any]
) -> dict[str, Any]:
    """Import baseline state without overwriting non-baseline keys.

    Args:
        existing_state: Current state dict
        baseline_state: Baseline state to import

    Returns:
        Merged state with baseline keys added, non-baseline keys preserved
    """
    merged_state = existing_state.copy()

    # Only add keys that start with baseline_
    for key, value in baseline_state.items():
        if key.startswith("baseline_"):
            merged_state[key] = value
        # Silently skip non-baseline keys to prevent collision

    return merged_state


def apply_retention_policy(baseline_dir: Path, keep_count: int = 5) -> None:
    """Apply retention policy to baseline artifacts.

    Args:
        baseline_dir: Directory containing baseline artifacts
        keep_count: Number of most recent artifacts to keep
    """
    # Find all baseline JSON files
    baseline_files = list(baseline_dir.glob("*.json"))

    # Filter out latest.json symlink
    baseline_files = [f for f in baseline_files if f.name != "latest.json"]

    # Sort by modification time (newest first)
    baseline_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    # Delete files beyond keep_count
    for old_file in baseline_files[keep_count:]:
        old_file.unlink()
