"""Acceptance tests for FR-277: Watcher2 Baseline Checkpointing."""

import json

import pytest

# These imports make the API available for future watcher2 integration
import yamlgraph.chaplain.baseline  # noqa: F401
from yamlgraph.chaplain.baseline import (  # noqa: F401
    BaselineBuilder,
    BaselineState,
    BaselineSummaryMeta,
    SummaryCache,
    build_baseline_state,
    cleanup_old_baselines,
    load_baseline_graph,
    prepare_watcher2_import,
    validate_manifest_schema,
)
from yamlgraph.chaplain.baseline.hash import (  # noqa: F401
    compute_baseline_id,
    hash_file_content,
    normalize_content,
)


@pytest.mark.req("REQ-YG-310")
class TestWatcher2BaselineCheckpointing:
    """FR-277: Watcher2 baseline checkpointing with deterministic hash-based invalidation."""

    def test_manifest_schema_validation(self, tmp_path):
        """AC-1: Manifest schema exists with glob support (pattern), explicit mode, and exclude support."""
        # This should import the manifest validator

        manifest_data = {
            "manifest_version": 1,
            "sources": [
                {"pattern": "ARCHITECTURE.md", "mode": "verbatim"},
                {"pattern": "feature-requests/*.md", "mode": "summarized"},
            ],
            "exclude": ["feature-requests/TEMPLATE.md"],
        }

        # Should validate successfully
        result = validate_manifest_schema(manifest_data)
        assert result is True

    def test_integration_scope_watcher2_only(self, tmp_path):
        """AC-2: Integration scope remains watcher2-only (.chaplain/ + watcher2 scripts), no yamlgraph core changes."""
        # Verify baseline functionality is isolated to .chaplain/ directory

        builder = BaselineBuilder(tmp_path / ".chaplain" / "baseline")
        assert str(builder.base_path).endswith(".chaplain/baseline")

        # Should not affect yamlgraph core modules
        import yamlgraph.executor
        import yamlgraph.graph_loader

        # Core modules should not have baseline dependencies
        assert not hasattr(yamlgraph.graph_loader, "baseline")
        assert not hasattr(yamlgraph.executor, "baseline")

    def test_baseline_id_deterministic(self, tmp_path):
        """AC-3: BASELINE_ID is deterministic: same sources and manifest version produce the same hash."""

        # Create test files with known content
        (tmp_path / "file1.txt").write_text("content1\n")
        (tmp_path / "file2.txt").write_text("content2\n")

        manifest = {
            "manifest_version": 1,
            "sources": [
                {"pattern": "file1.txt", "mode": "verbatim"},
                {"pattern": "file2.txt", "mode": "verbatim"},
            ],
        }

        # Same manifest and files should produce identical baseline IDs
        baseline_id_1 = compute_baseline_id(manifest, tmp_path)
        baseline_id_2 = compute_baseline_id(manifest, tmp_path)

        assert baseline_id_1 == baseline_id_2
        assert len(baseline_id_1) == 64  # SHA256 hex length

    def test_unchanged_sources_no_rebuild(self, tmp_path):
        """AC-4: Unchanged sources do not trigger rebuild."""

        # Create baseline directory structure
        baseline_dir = tmp_path / ".chaplain" / "baseline"
        baseline_dir.mkdir(parents=True)

        # Create test source file
        source_file = tmp_path / "source.txt"
        source_file.write_text("stable content\n")

        builder = BaselineBuilder(baseline_dir)
        manifest = {
            "manifest_version": 1,
            "sources": [{"pattern": "source.txt", "mode": "verbatim"}],
        }

        # First build should create artifact
        baseline_id_1 = builder.build_if_needed(manifest, tmp_path)
        assert (baseline_dir / f"{baseline_id_1}.json").exists()

        # Second build with unchanged source should reuse existing
        baseline_id_2 = builder.build_if_needed(manifest, tmp_path)
        assert baseline_id_1 == baseline_id_2
        assert builder.was_reused  # Flag indicating reuse occurred

    def test_changed_source_new_baseline_id(self, tmp_path):
        """AC-5: Changed source produces new BASELINE_ID and new artifact."""

        baseline_dir = tmp_path / ".chaplain" / "baseline"
        baseline_dir.mkdir(parents=True)

        source_file = tmp_path / "source.txt"
        source_file.write_text("original content\n")

        builder = BaselineBuilder(baseline_dir)
        manifest = {
            "manifest_version": 1,
            "sources": [{"pattern": "source.txt", "mode": "verbatim"}],
        }

        # First build
        baseline_id_1 = builder.build_if_needed(manifest, tmp_path)

        # Modify source content
        source_file.write_text("changed content\n")

        # Second build should produce different baseline ID
        baseline_id_2 = builder.build_if_needed(manifest, tmp_path)
        assert baseline_id_1 != baseline_id_2

        # Both artifacts should exist
        assert (baseline_dir / f"{baseline_id_1}.json").exists()
        assert (baseline_dir / f"{baseline_id_2}.json").exists()

    def test_baseline_builder_graph_structure(self, tmp_path):
        """AC-6: Baseline builder graph defines concrete nodes for read, summary-resolution, hash, assemble, and export."""
        graph_path = tmp_path / ".chaplain" / "graphs" / "baseline" / "graph.yaml"
        graph_path.parent.mkdir(parents=True)

        # Load the baseline builder graph

        graph_config = load_baseline_graph()

        required_nodes = {
            "load_manifest",
            "expand_sources",
            "read_sources",
            "resolve_summaries",
            "compute_baseline_id",
            "assemble_baseline_state",
            "emit_artifact",
        }

        actual_nodes = set(graph_config.nodes.keys())
        assert required_nodes.issubset(
            actual_nodes
        ), f"Missing nodes: {required_nodes - actual_nodes}"

    def test_summary_determinism_cache_keys(self, tmp_path):
        """AC-7: Summary determinism strategy is implemented with summary cache keys and reuse."""

        cache = SummaryCache(tmp_path / "summary_cache.json")

        source_content = "This is test content for summarization."
        summary_prompt_version = "v1.0"
        summary_model = "anthropic/claude-3-haiku-20240307"

        # First call should generate and cache summary
        summary_1 = cache.get_or_generate_summary(
            source_content, summary_prompt_version, summary_model
        )
        assert summary_1 is not None
        assert cache.cache_hit is False

        # Second call with same inputs should return cached summary
        summary_2 = cache.get_or_generate_summary(
            source_content, summary_prompt_version, summary_model
        )
        assert summary_1 == summary_2
        assert cache.cache_hit is True

    def test_latest_json_symlink(self, tmp_path):
        """AC-8: latest.json is maintained as a symlink."""

        baseline_dir = tmp_path / ".chaplain" / "baseline"
        baseline_dir.mkdir(parents=True)

        builder = BaselineBuilder(baseline_dir)

        # Create a baseline artifact
        baseline_id = "test_baseline_123abc"
        artifact_path = baseline_dir / f"{baseline_id}.json"
        artifact_path.write_text('{"baseline_id": "test_baseline_123abc"}')

        # Update latest symlink
        builder.update_latest_symlink(baseline_id)

        latest_path = baseline_dir / "latest.json"
        assert latest_path.is_symlink()
        assert latest_path.resolve() == artifact_path

    def test_watcher2_imports_baseline_via_import_state(self, tmp_path):
        """AC-9: Watcher2 imports baseline before plan/research via --import-state."""

        # Create baseline artifact
        baseline_dir = tmp_path / ".chaplain" / "baseline"
        baseline_dir.mkdir(parents=True)

        baseline_data = {
            "baseline_id": "test_123",
            "baseline_context_verbatim": {"ARCHITECTURE.md": "# Architecture\n"},
            "baseline_context_summaries": {"diary": "Recent developments..."},
        }

        artifact_path = baseline_dir / "latest.json"
        artifact_path.write_text(json.dumps(baseline_data))

        # Prepare import for watcher2
        import_args = prepare_watcher2_import(baseline_dir)

        assert "--import-state" in import_args
        assert str(artifact_path) in import_args

    def test_baseline_namespace_enforcement(self, tmp_path):
        """AC-10: baseline_* namespace is enforced and collision-tested."""

        # Mock state with potential collision
        existing_state = {
            "baseline_id": "existing_value",  # This should cause collision
            "proposal": "Some proposal content",
        }

        baseline_data = {
            "baseline_id": "new_baseline_123",
            "baseline_context_verbatim": {"doc": "content"},
        }

        with pytest.raises(ValueError, match="baseline_* namespace collision"):
            build_baseline_state(baseline_data, existing_state)

    def test_retention_policy_latest_5_artifacts(self, tmp_path):
        """AC-11: Retention policy is enforced (keep latest 5 artifacts)."""

        baseline_dir = tmp_path / ".chaplain" / "baseline"
        baseline_dir.mkdir(parents=True)

        # Create 8 baseline artifacts with different timestamps
        baselines = []
        for i in range(8):
            baseline_id = f"baseline_{i:03d}"
            artifact_path = baseline_dir / f"{baseline_id}.json"
            artifact_path.write_text(f'{{"baseline_id": "{baseline_id}"}}')
            baselines.append(artifact_path)

        # Run retention cleanup
        cleanup_old_baselines(baseline_dir, keep_latest=5)

        # Should keep only the latest 5
        remaining = list(baseline_dir.glob("baseline_*.json"))
        assert len(remaining) == 5

        # Verify correct ones were kept (latest 5)
        remaining_names = {f.name for f in remaining}
        expected = {
            "baseline_003.json",
            "baseline_004.json",
            "baseline_005.json",
            "baseline_006.json",
            "baseline_007.json",
        }
        assert remaining_names == expected

    def test_deterministic_hash_generation_normalization(self, tmp_path):
        """AC-12: Tests covering deterministic hash generation with content normalization."""

        # Test line ending normalization
        content_crlf = "line1\r\nline2\r\n"
        content_lf = "line1\nline2\n"

        normalized_crlf = normalize_content(content_crlf)
        normalized_lf = normalize_content(content_lf)

        assert normalized_crlf == normalized_lf

        # Test deterministic hashing
        test_file = tmp_path / "test.txt"
        test_file.write_text("content\r\nwith\r\nmixed\r\nlines")

        hash_1 = hash_file_content(test_file)
        hash_2 = hash_file_content(test_file)

        assert hash_1 == hash_2
        assert len(hash_1) == 64  # SHA256 hex

    def test_baseline_state_schema_validation(self, tmp_path):
        """AC-13: Baseline export contains required schema fields."""

        # Test minimum required fields
        baseline_data = {
            "baseline_id": "test_123abc",
            "baseline_manifest_version": "1",
            "baseline_built_at": "2026-04-25T22:59:00Z",
            "baseline_sources": [{"path": "test.txt", "hash": "abc123"}],
            "baseline_context_verbatim": {"doc": "content"},
            "baseline_context_summaries": {"notes": "summary"},
            "baseline_summary_meta": {
                "notes": {
                    "model": "claude",
                    "prompt_version": "v1",
                    "summary_key": "key123",
                }
            },
            "baseline_warnings": [],
        }

        # Should validate successfully
        baseline_state = BaselineState(**baseline_data)
        assert baseline_state.baseline_id == "test_123abc"
        assert len(baseline_state.baseline_sources) == 1

        # Test missing required field
        incomplete_data = baseline_data.copy()
        del incomplete_data["baseline_id"]

        with pytest.raises(ValueError):
            BaselineState(**incomplete_data)
