"""Hash utilities for baseline checkpointing."""

import glob
import hashlib
from pathlib import Path
from typing import Any


def normalize_content(content: str) -> str:
    """
    Normalize content by converting all line endings to LF.

    Args:
        content: Raw content string

    Returns:
        str: Normalized content with consistent line endings
    """
    # Convert CRLF and CR to LF for consistent hashing
    return content.replace("\r\n", "\n").replace("\r", "\n")


def hash_file_content(file_path: Path) -> str:
    """
    Compute SHA256 hash of file content after normalization.

    Args:
        file_path: Path to file to hash

    Returns:
        str: SHA256 hex digest of normalized content
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    normalized = normalize_content(content)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_baseline_id(manifest: dict[str, Any], base_path: Path) -> str:
    """
    Compute deterministic baseline ID from manifest and source files.

    Hash algorithm:
    - Normalize line endings to LF
    - Expand patterns in sorted path order
    - Concatenate path + sha256(content) in resolved order
    - BASELINE_ID = sha256(concatenated_entries + manifest_version)

    Args:
        manifest: Manifest dictionary containing sources
        base_path: Base directory for resolving patterns

    Returns:
        str: SHA256 hex digest baseline ID
    """
    entries = []

    # Process sources in deterministic order
    for source in manifest["sources"]:
        pattern = source["pattern"]

        # Expand glob pattern
        if "*" in pattern or "?" in pattern:
            # Use glob to expand pattern
            matches = sorted(glob.glob(str(base_path / pattern)))
            file_paths = [Path(match) for match in matches]
        else:
            # Single file
            file_paths = [base_path / pattern]

        # Process each file
        for file_path in sorted(file_paths):
            if file_path.exists() and file_path.is_file():
                relative_path = file_path.relative_to(base_path)
                content_hash = hash_file_content(file_path)
                entries.append(f"{relative_path}:{content_hash}")

    # Create final hash input
    entries_str = "|".join(entries)
    manifest_version_str = str(manifest["manifest_version"])

    final_input = f"{entries_str}|{manifest_version_str}"
    return hashlib.sha256(final_input.encode("utf-8")).hexdigest()
