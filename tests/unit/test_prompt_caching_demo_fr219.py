"""Acceptance tests for FR-219: Anthropic Prompt Caching Demo with System Segments.

These tests define the contract that the enforce phase must satisfy.
All tests must FAIL on the current unmodified codebase (RED phase).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

DEMO_PATH = "examples/demos/prompt-caching"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "examples"
    / "demos"
    / "prompt-caching"
)


class TestPromptCachingDemoStructure:
    """Test demo directory structure and files exist (AC-1, AC-7)."""

    @pytest.mark.req("REQ-YG-302")
    def test_demo_directory_exists(self) -> None:
        """Demo directory exists at examples/demos/prompt-caching/."""
        assert DEMO_DIR.exists(), f"Demo directory {DEMO_DIR} must exist"
        assert DEMO_DIR.is_dir(), f"{DEMO_DIR} must be a directory"

    @pytest.mark.req("REQ-YG-302")
    def test_graph_yaml_exists(self) -> None:
        """Graph config file exists."""
        graph_file = DEMO_DIR / "graph.yaml"
        assert graph_file.exists(), "graph.yaml must exist in demo directory"

    @pytest.mark.req("REQ-YG-302")
    def test_prompts_directory_exists(self) -> None:
        """Prompts directory exists with required prompt files."""
        prompts_dir = DEMO_DIR / "prompts"
        assert prompts_dir.exists(), "prompts/ directory must exist"
        assert (prompts_dir / "analyze.yaml").exists(), "prompts/analyze.yaml must exist"
        assert (prompts_dir / "reflect.yaml").exists(), "prompts/reflect.yaml must exist"

    @pytest.mark.req("REQ-YG-302")
    def test_readme_exists(self) -> None:
        """README.md explaining caching behavior exists."""
        readme_file = DEMO_DIR / "README.md"
        assert readme_file.exists(), "README.md must exist in demo directory"

    @pytest.mark.req("REQ-YG-302")
    def test_demo_output_log_exists(self) -> None:
        """demo-output.log proving execution exists."""
        demo_log = DEMO_DIR / "demo-output.log"
        assert demo_log.exists(), "demo-output.log must exist proving successful execution"


class TestGraphConfiguration:
    """Test graph.yaml configuration (AC-1, AC-7)."""

    @pytest.mark.req("REQ-YG-303")
    def test_graph_loads_successfully(self) -> None:
        """Graph config loads via yamlgraph."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(f"{DEMO_PATH}/graph.yaml")
        assert config.name == "prompt-caching-demo"

    @pytest.mark.req("REQ-YG-303")
    def test_uses_anthropic_provider(self) -> None:
        """Graph uses provider: anthropic."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(f"{DEMO_PATH}/graph.yaml")
        assert config.provider == "anthropic", "Demo must use Anthropic provider for caching"

    @pytest.mark.req("REQ-YG-303")
    def test_has_two_llm_nodes(self) -> None:
        """Graph has exactly 2 LLM nodes (analyze, reflect)."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(f"{DEMO_PATH}/graph.yaml")
        
        llm_nodes = [node for node in config.nodes if node.type == "llm"]
        assert len(llm_nodes) == 2, "Demo must have exactly 2 LLM nodes"
        
        node_names = {node.name for node in llm_nodes}
        assert node_names == {"analyze", "reflect"}, "LLM nodes must be named 'analyze' and 'reflect'"

    @pytest.mark.req("REQ-YG-303")
    def test_follows_cache_demo_pattern(self) -> None:
        """Demo follows existing cache demo structure patterns."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(f"{DEMO_PATH}/graph.yaml")
        
        # Should use prompts_relative like cache demo
        assert config.prompts_relative is True, "Demo should use prompts_relative: true"
        assert config.prompts_dir == "prompts", "Demo should use prompts_dir: prompts"


class TestPromptSystemSegments:
    """Test prompt files use system_segments with cache: true (AC-2, AC-6)."""

    @pytest.mark.req("REQ-YG-304")
    def test_analyze_prompt_has_system_segments(self) -> None:
        """analyze.yaml uses system_segments with cache: true."""
        analyze_path = DEMO_DIR / "prompts" / "analyze.yaml"
        
        with open(analyze_path) as f:
            prompt_config = yaml.safe_load(f)
        
        assert "system_segments" in prompt_config, "analyze.yaml must use system_segments"
        segments = prompt_config["system_segments"]
        assert isinstance(segments, list), "system_segments must be a list"
        assert len(segments) >= 1, "Must have at least one system segment"
        
        # Check for cached segment
        cached_segments = [seg for seg in segments if seg.get("cache") is True]
        assert len(cached_segments) >= 1, "Must have at least one segment with cache: true"

    @pytest.mark.req("REQ-YG-304")
    def test_reflect_prompt_has_system_segments(self) -> None:
        """reflect.yaml uses system_segments with cache: true."""
        reflect_path = DEMO_DIR / "prompts" / "reflect.yaml"
        
        with open(reflect_path) as f:
            prompt_config = yaml.safe_load(f)
        
        assert "system_segments" in prompt_config, "reflect.yaml must use system_segments"
        segments = prompt_config["system_segments"]
        assert isinstance(segments, list), "system_segments must be a list"
        assert len(segments) >= 1, "Must have at least one system segment"
        
        # Check for cached segment
        cached_segments = [seg for seg in segments if seg.get("cache") is True]
        assert len(cached_segments) >= 1, "Must have at least one segment with cache: true"

    @pytest.mark.req("REQ-YG-304")
    def test_prompts_have_identical_cached_segments(self) -> None:
        """Both prompts share identical cached system segments for cache reuse."""
        analyze_path = DEMO_DIR / "prompts" / "analyze.yaml"
        reflect_path = DEMO_DIR / "prompts" / "reflect.yaml"
        
        with open(analyze_path) as f:
            analyze_config = yaml.safe_load(f)
        with open(reflect_path) as f:
            reflect_config = yaml.safe_load(f)
        
        analyze_cached = [seg for seg in analyze_config["system_segments"] if seg.get("cache") is True]
        reflect_cached = [seg for seg in reflect_config["system_segments"] if seg.get("cache") is True]
        
        assert len(analyze_cached) > 0, "analyze.yaml must have cached segments"
        assert len(reflect_cached) > 0, "reflect.yaml must have cached segments"
        
        # At least one cached segment should be identical between prompts
        analyze_cached_content = {seg["content"] for seg in analyze_cached}
        reflect_cached_content = {seg["content"] for seg in reflect_cached}
        
        shared_content = analyze_cached_content & reflect_cached_content
        assert len(shared_content) > 0, "Prompts must share at least one identical cached segment"

    @pytest.mark.req("REQ-YG-304")
    def test_prompts_use_inline_schema(self) -> None:
        """Prompts use inline schema format, not separate Python models."""
        analyze_path = DEMO_DIR / "prompts" / "analyze.yaml"
        reflect_path = DEMO_DIR / "prompts" / "reflect.yaml"
        
        with open(analyze_path) as f:
            analyze_config = yaml.safe_load(f)
        with open(reflect_path) as f:
            reflect_config = yaml.safe_load(f)
        
        assert "schema" in analyze_config, "analyze.yaml must have inline schema"
        assert "name" in analyze_config["schema"], "analyze schema must have name field"
        assert "fields" in analyze_config["schema"], "analyze schema must have fields"
        
        assert "schema" in reflect_config, "reflect.yaml must have inline schema"
        assert "name" in reflect_config["schema"], "reflect schema must have name field"
        assert "fields" in reflect_config["schema"], "reflect schema must have fields"


class TestDocumentationUpdates:
    """Test reference documentation is updated (AC-5)."""

    @pytest.mark.req("REQ-YG-305")
    def test_prompt_yaml_reference_has_system_segments(self) -> None:
        """reference/prompt-yaml.md documents system_segments field."""
        ref_file = Path(__file__).resolve().parent.parent.parent / "reference" / "prompt-yaml.md"
        
        with open(ref_file) as f:
            content = f.read()
        
        assert "system_segments" in content, "prompt-yaml.md must document system_segments"
        assert "cache:" in content, "prompt-yaml.md must document cache field"
        assert "anthropic" in content.lower() or "Anthropic" in content, "Must document Anthropic-specific behavior"

    @pytest.mark.req("REQ-YG-305")
    def test_readme_explains_caching_benefits(self) -> None:
        """Demo README.md explains caching behavior and benefits."""
        readme_path = DEMO_DIR / "README.md"
        
        with open(readme_path) as f:
            content = f.read()
        
        # Check for key concepts
        assert "cache" in content.lower(), "README must mention caching"
        assert "anthropic" in content.lower(), "README must mention Anthropic"
        assert "system_segments" in content, "README must mention system_segments"
        assert any(word in content.lower() for word in ["cost", "performance", "benefit"]), \
            "README must explain benefits"


class TestDemoExecutionProof:
    """Test demo execution proof exists (AC-4)."""

    @pytest.mark.req("REQ-YG-306")
    def test_demo_output_log_contains_execution_proof(self) -> None:
        """demo-output.log contains evidence of successful execution."""
        demo_log = DEMO_DIR / "demo-output.log"
        
        with open(demo_log) as f:
            content = f.read()
        
        # Check for execution indicators
        assert "analyze" in content.lower(), "Log must show analyze node execution"
        assert "reflect" in content.lower(), "Log must show reflect node execution" 
        assert any(word in content for word in ["✓", "success", "completed"]), \
            "Log must show successful execution"

    @pytest.mark.req("REQ-YG-306")
    def test_demo_log_shows_anthropic_usage(self) -> None:
        """demo-output.log shows evidence of Anthropic API usage."""
        demo_log = DEMO_DIR / "demo-output.log"
        
        with open(demo_log) as f:
            content = f.read()
        
        # Should contain evidence of Anthropic provider usage
        assert "anthropic" in content.lower() or "claude" in content.lower(), \
            "Log must show evidence of Anthropic/Claude usage"