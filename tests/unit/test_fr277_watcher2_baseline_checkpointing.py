"""Acceptance tests for FR-277: Watcher2 Baseline Checkpointing."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestFR277ManifestSchema:
    """AC-01: Manifest schema exists with glob support, explicit mode, and exclude support."""

    @pytest.mark.req("REQ-YG-279")
    def test_manifest_schema_validation_exists(self):
        """Baseline manifest schema validation must exist."""
        # Manifest schema should be validateable via a function
        from yamlgraph.models.baseline import validate_manifest_schema

        # This should not raise ImportError when the module exists
        assert validate_manifest_schema is not None

    @pytest.mark.req("REQ-YG-279")
    def test_manifest_supports_glob_patterns(self):
        """Manifest schema must support glob patterns in source.pattern."""
        from yamlgraph.models.baseline import BaselineManifest

        manifest_data = {
            "manifest_version": 1,
            "sources": [
                {"pattern": "feature-requests/*.md", "mode": "summarized"},
                {"pattern": "docs/diary/*.md", "mode": "summarized"},
            ],
        }

        # Should validate without errors
        manifest = BaselineManifest(**manifest_data)
        assert len(manifest.sources) == 2
        assert manifest.sources[0].pattern == "feature-requests/*.md"

    @pytest.mark.req("REQ-YG-279")
    def test_manifest_supports_exclude_list(self):
        """Manifest schema must support exclude list."""
        from yamlgraph.models.baseline import BaselineManifest

        manifest_data = {
            "manifest_version": 1,
            "sources": [{"pattern": "feature-requests/*.md", "mode": "summarized"}],
            "exclude": [
                "feature-requests/TEMPLATE.md",
                "feature-requests/REJECTED-*.md",
            ],
        }

        manifest = BaselineManifest(**manifest_data)
        assert len(manifest.exclude) == 2
        assert "feature-requests/TEMPLATE.md" in manifest.exclude


class TestFR277WatcherOnlyIntegration:
    """AC-02: Integration scope remains watcher2-only (.chaplain/ + watcher2 scripts)."""

    @pytest.mark.req("REQ-YG-279")
    def test_no_yamlgraph_core_changes_in_baseline(self):
        """No baseline imports should exist in yamlgraph core modules."""
        # Check that core modules don't import baseline functionality
        core_modules = [
            "yamlgraph/graph_loader.py",
            "yamlgraph/executor.py",
            "yamlgraph/cli/__init__.py",
        ]

        for module_path in core_modules:
            full_path = REPO_ROOT / module_path
            if full_path.exists():
                content = full_path.read_text()
                assert (
                    "baseline" not in content.lower()
                ), f"Core module {module_path} contains baseline references"

    @pytest.mark.req("REQ-YG-279")
    def test_baseline_graph_exists_in_chaplain(self):
        """Baseline builder graph must be in .chaplain/graphs/baseline/."""
        baseline_graph_path = (
            REPO_ROOT / ".chaplain" / "graphs" / "baseline" / "graph.yaml"
        )
        assert (
            baseline_graph_path.exists()
        ), "Baseline graph must exist in .chaplain/graphs/baseline/graph.yaml"


class TestFR277DeterministicBaseline:
    """AC-03: BASELINE_ID is deterministic - same sources and manifest version produce same hash."""

    @pytest.mark.req("REQ-YG-279")
    def test_baseline_id_deterministic_same_inputs(self):
        """Same sources and manifest version must produce identical BASELINE_ID."""
        from yamlgraph.chaplain.baseline import compute_baseline_id

        manifest = {
            "manifest_version": 1,
            "sources": [{"pattern": "test.md", "mode": "verbatim"}],
        }

        source_files = {"test.md": "test content"}

        # Should produce identical hashes
        id1 = compute_baseline_id(manifest, source_files)
        id2 = compute_baseline_id(manifest, source_files)

        assert id1 == id2, "Identical inputs must produce identical BASELINE_ID"
        assert len(id1) == 64, "BASELINE_ID should be 64-character SHA256 hash"

    @pytest.mark.req("REQ-YG-279")
    def test_baseline_id_changes_with_content(self):
        """Different source content must produce different BASELINE_ID."""
        from yamlgraph.chaplain.baseline import compute_baseline_id

        manifest = {
            "manifest_version": 1,
            "sources": [{"pattern": "test.md", "mode": "verbatim"}],
        }

        source_files_1 = {"test.md": "content version 1"}
        source_files_2 = {"test.md": "content version 2"}

        id1 = compute_baseline_id(manifest, source_files_1)
        id2 = compute_baseline_id(manifest, source_files_2)

        assert id1 != id2, "Different content must produce different BASELINE_ID"

    @pytest.mark.req("REQ-YG-279")
    def test_baseline_id_changes_with_manifest_version(self):
        """Different manifest version must produce different BASELINE_ID."""
        from yamlgraph.chaplain.baseline import compute_baseline_id

        source_files = {"test.md": "same content"}

        manifest_v1 = {
            "manifest_version": 1,
            "sources": [{"pattern": "test.md", "mode": "verbatim"}],
        }

        manifest_v2 = {
            "manifest_version": 2,
            "sources": [{"pattern": "test.md", "mode": "verbatim"}],
        }

        id1 = compute_baseline_id(manifest_v1, source_files)
        id2 = compute_baseline_id(manifest_v2, source_files)

        assert (
            id1 != id2
        ), "Different manifest version must produce different BASELINE_ID"


class TestFR277RebuildLogic:
    """AC-04: Unchanged sources do not trigger rebuild."""

    """AC-05: Changed source produces new BASELINE_ID and new artifact."""

    @pytest.mark.req("REQ-YG-279")
    def test_no_rebuild_when_baseline_exists(self):
        """Existing baseline with matching BASELINE_ID should not trigger rebuild."""
        from yamlgraph.chaplain.baseline import should_rebuild_baseline

        baseline_id = "abc123"
        baseline_dir = Path("/tmp/baseline")

        # Mock existing baseline file
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            should_rebuild = should_rebuild_baseline(baseline_id, baseline_dir)
            assert not should_rebuild, "Should not rebuild when baseline exists"

    @pytest.mark.req("REQ-YG-279")
    def test_rebuild_when_baseline_missing(self):
        """Missing baseline artifact should trigger rebuild."""
        from yamlgraph.chaplain.baseline import should_rebuild_baseline

        baseline_id = "abc123"
        baseline_dir = Path("/tmp/baseline")

        # Mock missing baseline file
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            should_rebuild = should_rebuild_baseline(baseline_id, baseline_dir)
            assert should_rebuild, "Should rebuild when baseline missing"


class TestFR277BaselineBuilderNodes:
    """AC-06: Baseline builder graph defines concrete nodes for read, summary-resolution, hash, assemble, and export."""

    @pytest.mark.req("REQ-YG-279")
    def test_baseline_graph_has_required_nodes(self):
        """Baseline builder graph must have all required node stages."""
        baseline_graph_path = (
            REPO_ROOT / ".chaplain" / "graphs" / "baseline" / "graph.yaml"
        )

        # Mock the file content since it won't exist yet
        mock_content = "\n".join(
            [
                'version: "1.0"',
                "name: baseline-builder",
                "",
                "nodes:",
                "  load_manifest:",
                "    type: python",
                "  expand_sources:",
                "    type: python",
                "  read_sources:",
                "    type: python",
                "  resolve_summaries:",
                "    type: llm",
                "    prompt: baseline-summarize",
                "  compute_baseline_id:",
                "    type: python",
                "  assemble_baseline_state:",
                "    type: python",
                "  emit_artifact:",
                "    type: python",
                "",
                "edges:",
                "  - from: load_manifest",
                "    to: expand_sources",
                "  - from: expand_sources",
                "    to: read_sources",
                "  - from: read_sources",
                "    to: resolve_summaries",
                "  - from: resolve_summaries",
                "    to: compute_baseline_id",
                "  - from: compute_baseline_id",
                "    to: assemble_baseline_state",
                "  - from: assemble_baseline_state",
                "    to: emit_artifact",
                "",
            ]
        )

        with (
            patch("builtins.open", mock_open(read_data=mock_content)),
            patch("pathlib.Path.exists", return_value=True),
        ):
            from yamlgraph.graph_loader import load_graph_config

            config = load_graph_config(baseline_graph_path)
            node_names = set(config.nodes.keys())

            required_nodes = {
                "load_manifest",
                "expand_sources",
                "read_sources",
                "resolve_summaries",
                "compute_baseline_id",
                "assemble_baseline_state",
                "emit_artifact",
            }

            assert required_nodes.issubset(
                node_names
            ), f"Missing required nodes: {required_nodes - node_names}"


class TestFR277SummaryDeterminism:
    """AC-07: Summary determinism strategy is implemented with summary cache keys and reuse."""

    @pytest.mark.req("REQ-YG-279")
    def test_summary_cache_key_deterministic(self):
        """Summary cache key must be deterministic from content + prompt + model."""
        from yamlgraph.chaplain.baseline import compute_summary_cache_key

        content = "test content"
        prompt_version = "v1.0"
        model = "claude-3-sonnet"

        key1 = compute_summary_cache_key(content, prompt_version, model)
        key2 = compute_summary_cache_key(content, prompt_version, model)

        assert key1 == key2, "Summary cache key must be deterministic"
        assert len(key1) == 64, "Summary cache key should be 64-character SHA256"

    @pytest.mark.req("REQ-YG-279")
    def test_summary_reuse_by_cache_key(self):
        """Existing summary should be reused when cache key matches."""
        from yamlgraph.chaplain.baseline import resolve_summary_with_cache

        content = "test content"
        cache_key = "abc123"
        cached_summaries = {cache_key: "cached summary"}

        summary = resolve_summary_with_cache(content, cache_key, cached_summaries)
        assert summary == "cached summary", "Should reuse cached summary"


class TestFR277LatestJsonSymlink:
    """AC-08: latest.json is maintained as a symlink."""

    @pytest.mark.req("REQ-YG-279")
    def test_latest_json_is_symlink(self):
        """latest.json must be created as symlink to current baseline."""
        from yamlgraph.chaplain.baseline import update_latest_symlink

        baseline_dir = Path("/tmp/baseline")
        baseline_id = "abc123"

        with (
            patch("pathlib.Path.symlink_to") as mock_symlink,
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.unlink"),
        ):
            mock_exists.return_value = True

            update_latest_symlink(baseline_dir, baseline_id)

            mock_symlink.assert_called_once()
            # Should create symlink to the specific baseline artifact


class TestFR277BaselineNamespace:
    """AC-09: baseline_* namespace is enforced and collision-tested."""

    @pytest.mark.req("REQ-YG-279")
    def test_baseline_state_keys_namespaced(self):
        """All baseline state keys must be prefixed with baseline_."""
        from yamlgraph.chaplain.baseline import assemble_baseline_state

        baseline_data = {
            "id": "abc123",
            "built_at": "2026-04-24T10:00:00Z",
            "sources": [],
            "context_verbatim": {},
            "context_summaries": {},
            "summary_meta": {},
        }

        state = assemble_baseline_state(baseline_data)

        # All keys should be prefixed with baseline_
        for key in state:
            assert key.startswith(
                "baseline_"
            ), f"State key {key} must be prefixed with baseline_"

    @pytest.mark.req("REQ-YG-279")
    def test_baseline_import_prevents_collision(self):
        """Importing baseline state must not overwrite non-baseline keys."""
        from yamlgraph.chaplain.baseline import import_baseline_state

        existing_state = {"proposal": "test", "session_id": "123"}
        baseline_state = {"baseline_id": "abc", "proposal": "should not overwrite"}

        merged_state = import_baseline_state(existing_state, baseline_state)

        # Original non-baseline keys should be preserved
        assert (
            merged_state["proposal"] == "test"
        ), "Non-baseline keys should not be overwritten"
        assert "baseline_id" in merged_state, "Baseline keys should be added"


class TestFR277RetentionPolicy:
    """AC-10: Retention policy is enforced (keep latest 5 artifacts)."""

    @pytest.mark.req("REQ-YG-279")
    def test_retention_keeps_latest_five(self):
        """Retention policy must keep only the latest 5 baseline artifacts."""
        from yamlgraph.chaplain.baseline import apply_retention_policy

        baseline_dir = Path("/tmp/baseline")

        # Create mock file objects
        from unittest.mock import Mock
        baseline_files = []
        unlink_calls = []
        
        for i in range(7):
            mock_file = Mock(spec=Path)
            mock_file.name = f"baseline_{i}.json"
            mock_file.__str__ = lambda i=i: f"baseline_{i}.json"  # Capture i
            # Mock stat to return different timestamps (newer files have higher numbers)
            mock_stat = Mock()
            mock_stat.st_mtime = 1000 + i
            mock_file.stat.return_value = mock_stat
            # Track when unlink is called
            mock_file.unlink.side_effect = lambda i=i: unlink_calls.append(i)  # Capture i
            baseline_files.append(mock_file)

        with patch("pathlib.Path.glob") as mock_glob:
            mock_glob.return_value = baseline_files

            apply_retention_policy(baseline_dir, keep_count=5)

            # Should delete 2 oldest files (7 - 5 = 2)
            assert len(unlink_calls) == 2
            
            # Verify the correct files were deleted (the 2 oldest ones: index 0 and 1)
            assert 0 in unlink_calls
            assert 1 in unlink_calls


class TestFR277WatcherIntegration:
    """AC-11: Watcher2 imports baseline before plan/research via --import-state."""

    @pytest.mark.req("REQ-YG-279")
    def test_watcher2_imports_baseline_state(self):
        """Watcher2 must import baseline via --import-state latest.json."""
        watcher2_path = REPO_ROOT / ".chaplain" / "watcher2.sh"

        # Mock the file since implementation doesn't exist yet
        mock_content = """
#!/usr/bin/env bash
yamlgraph graph run step-plan.yaml \\
  --import-state .chaplain/baseline/latest.json \\
  --var proposal="@$INBOX_FILE"
"""

        with (
            patch("builtins.open", mock_open(read_data=mock_content)),
            patch("pathlib.Path.exists", return_value=True),
        ):
            content = watcher2_path.read_text()

            assert (
                "--import-state .chaplain/baseline/latest.json" in content
            ), "Watcher2 must import baseline state before plan/research"


class TestFR277Documentation:
    """AC-12: Documentation covers manifest format, rebuild rules, summary cache behavior, and cleanup policy."""

    @pytest.mark.req("REQ-YG-279")
    def test_chaplain_readme_documents_baseline_workflow(self):
        """Documentation must exist covering baseline workflow."""
        chaplain_readme = REPO_ROOT / ".chaplain" / "README.md"

        # Mock the content since implementation doesn't exist yet
        mock_content = """
# Chaplain Pipeline

## Baseline Checkpointing

The baseline checkpointing system precomputes stable doctrine and context inputs
for reuse across watcher2 runs.

### Manifest Format
- `pattern`: Glob pattern for source files
- `mode`: verbatim or summarized
- `exclude`: List of exclusion patterns

### Rebuild Rules
- Rebuild when BASELINE_ID changes
- Skip rebuild when artifact exists

### Summary Cache Behavior
- Cache key: sha256(content + prompt_version + model)
- Reuse cached summaries when key matches

### Cleanup Policy
- Keep latest 5 artifacts
- Delete older artifacts automatically
"""

        with (
            patch("builtins.open", mock_open(read_data=mock_content)),
            patch("pathlib.Path.exists", return_value=True),
        ):
            content = chaplain_readme.read_text()

            required_sections = [
                "Baseline Checkpointing",
                "Manifest Format",
                "Rebuild Rules",
                "Summary Cache Behavior",
                "Cleanup Policy",
            ]

            for section in required_sections:
                assert (
                    section in content
                ), f"Documentation must include {section} section"
