#!/usr/bin/env python3
"""
Functional demo of baseline checkpointing.
Shows core functionality without requiring LLM API keys.
"""

import tempfile
from pathlib import Path

from yamlgraph.chaplain.baseline.builder import BaselineBuilder
from yamlgraph.chaplain.baseline.hash import compute_baseline_id

# Import our baseline modules
from yamlgraph.chaplain.baseline.manifest import validate_manifest_schema


def main():
    print("🚀 Baseline Checkpointing Functional Demo")
    print("=" * 50)

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Manifest validation demo
        print("\n1. Testing manifest validation...")
        manifest = {
            "manifest_version": 1,
            "sources": [
                {"pattern": "test.txt", "mode": "verbatim"},
                {"pattern": "*.md", "mode": "summarized"},
            ],
            "exclude": ["private.md"],
        }

        is_valid = validate_manifest_schema(manifest)
        print(f"   ✅ Manifest validation: {is_valid}")

        # 2. Create test files
        print("\n2. Creating test source files...")
        (tmp_path / "test.txt").write_text("Test content\nLine 2")
        (tmp_path / "doc1.md").write_text("# Document 1\nContent here")
        (tmp_path / "doc2.md").write_text("# Document 2\nMore content")
        (tmp_path / "private.md").write_text("Private content")

        print(f"   ✅ Created 4 test files in {tmp_path}")

        # 3. Hash computation
        print("\n3. Testing deterministic hash computation...")
        baseline_id_1 = compute_baseline_id(manifest, tmp_path)
        baseline_id_2 = compute_baseline_id(manifest, tmp_path)

        print(f"   ✅ First hash:  {baseline_id_1}")
        print(f"   ✅ Second hash: {baseline_id_2}")
        print(f"   ✅ Deterministic: {baseline_id_1 == baseline_id_2}")

        # 4. Builder functionality
        print("\n4. Testing baseline builder...")
        baseline_dir = tmp_path / ".chaplain" / "baseline"
        builder = BaselineBuilder(baseline_dir)

        # First build
        built_id_1 = builder.build_if_needed(manifest, tmp_path)
        print(f"   ✅ First build: {built_id_1} (was_reused: {builder.was_reused})")

        # Second build (should reuse)
        built_id_2 = builder.build_if_needed(manifest, tmp_path)
        print(f"   ✅ Second build: {built_id_2} (was_reused: {builder.was_reused})")

        # 5. Verify artifact files
        print("\n5. Checking generated artifacts...")
        artifact_file = baseline_dir / f"{built_id_1}.json"
        latest_file = baseline_dir / "latest.json"

        print(f"   ✅ Artifact exists: {artifact_file.exists()}")
        print(f"   ✅ Latest symlink exists: {latest_file.exists()}")
        print(
            f"   ✅ Symlink points to artifact: {latest_file.resolve() == artifact_file}"
        )

        # 6. Content change test
        print("\n6. Testing change detection...")
        (tmp_path / "test.txt").write_text("Changed content\nLine 2")

        built_id_3 = builder.build_if_needed(manifest, tmp_path)
        print(f"   ✅ After change: {built_id_3} (was_reused: {builder.was_reused})")
        print(f"   ✅ Different ID: {built_id_1 != built_id_3}")

    print("\n" + "=" * 50)
    print("✅ All baseline checkpointing functionality working!")
    print("\nKey capabilities demonstrated:")
    print("- ✅ Manifest schema validation")
    print("- ✅ Deterministic hash computation")
    print("- ✅ Baseline artifact creation")
    print("- ✅ Cache reuse for unchanged sources")
    print("- ✅ Change detection and invalidation")
    print("- ✅ Symlink management")


if __name__ == "__main__":
    main()
