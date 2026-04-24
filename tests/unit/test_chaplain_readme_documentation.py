#!/usr/bin/env python3
"""Tests for FR-195: Chaplain Documentation

Validates that .chaplain/README.md exists and contains comprehensive
documentation covering watcher2 pipeline architecture and shell library.
"""

import pytest
from pathlib import Path


@pytest.mark.req("REQ-YG-278")
class TestChaplainREADMEExists:
    """Tests that the chaplain README file exists."""

    def test_chaplain_readme_exists(self):
        """.chaplain/README.md should exist."""
        readme_path = Path(".chaplain/README.md")
        assert readme_path.exists(), "chaplain README not found"

    def test_readme_is_readable(self):
        """README should be a readable text file."""
        readme_path = Path(".chaplain/README.md")
        assert readme_path.is_file(), "README should be a file"
        content = readme_path.read_text()
        assert len(content) > 0, "README should not be empty"


@pytest.mark.req("REQ-YG-278")
class TestChaplainREADMEContent:
    """Tests for specific content sections in the chaplain README."""

    @pytest.fixture
    def readme_content(self):
        """Load README content."""
        readme_path = Path(".chaplain/README.md")
        return readme_path.read_text()

    def test_watcher2_pipeline_overview(self, readme_content):
        """README should document watcher2 pipeline architecture."""
        assert "watcher2" in readme_content.lower()
        assert "pipeline" in readme_content.lower()
        # Should mention the main phases
        assert "plan" in readme_content.lower()
        assert "judge" in readme_content.lower()
        assert "enforce" in readme_content.lower()

    def test_shell_library_reference(self, readme_content):
        """README should document shell library tools."""
        # Core worktree operations
        assert "worktree_setup.sh" in readme_content
        assert "worktree_teardown.sh" in readme_content
        assert "preflight.sh" in readme_content
        
        # Git/GitHub integration
        assert "create_pr.sh" in readme_content
        assert "merge_pr.sh" in readme_content
        assert "wait_ci.sh" in readme_content
        assert "post_merge.sh" in readme_content
        
        # Pipeline support
        assert "inbox_sync.sh" in readme_content
        assert "metrics.sh" in readme_content

    def test_usage_examples_section(self, readme_content):
        """README should include usage examples."""
        assert "usage" in readme_content.lower() or "example" in readme_content.lower()
        # Should mention daemon usage
        assert "daemon" in readme_content.lower() or "watcher2.sh" in readme_content

    def test_environment_configuration(self, readme_content):
        """README should document environment variables and configuration."""
        assert "environment" in readme_content.lower() or "config" in readme_content.lower()
        # Should mention some common environment patterns
        assert "variable" in readme_content.lower() or "env" in readme_content.lower()

    def test_troubleshooting_section(self, readme_content):
        """README should include troubleshooting guidance."""
        assert "troubleshoot" in readme_content.lower() or "debug" in readme_content.lower() or "issue" in readme_content.lower()

    def test_architecture_details(self, readme_content):
        """README should explain architecture details."""
        assert "architecture" in readme_content.lower() or "directory" in readme_content.lower()
        # Should mention state management
        assert "state" in readme_content.lower()

    def test_cross_references_to_related_files(self, readme_content):
        """README should reference related files like FR-273."""
        # Should reference the main watcher2 script
        assert "watcher2.sh" in readme_content
        # Should mention .chaplain directory structure
        assert ".chaplain" in readme_content or "chaplain" in readme_content


@pytest.mark.req("REQ-YG-278") 
class TestChaplainREADMEStyle:
    """Tests for documentation style and formatting."""

    @pytest.fixture
    def readme_content(self):
        """Load README content."""
        readme_path = Path(".chaplain/README.md")
        return readme_path.read_text()

    def test_markdown_format(self, readme_content):
        """README should follow markdown format with headers."""
        assert "# " in readme_content, "Should have main headers"
        assert "## " in readme_content, "Should have section headers"

    def test_follows_project_style(self, readme_content):
        """README should follow project markdown style."""
        # Should have proper title
        assert readme_content.startswith("# "), "Should start with main header"
        # Should be well-structured
        assert len(readme_content.split("\n")) > 20, "Should be comprehensive"