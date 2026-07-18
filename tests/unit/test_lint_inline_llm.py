"""Tests for inline LLM lint check (FR-047).

Detects scripts with def main() that import LLM execution functions
but NOT graph loading — the code smell of bypassing YAMLGraph's
three-layer architecture.
"""

import tempfile
from pathlib import Path

import pytest


class TestLintInlineLLM:
    """Test inline LLM detection logic."""

    @pytest.mark.req("REQ-YG-073")
    def test_main_with_execute_prompt_no_graph_loader_fails(self):
        """File with main + execute_prompt but no graph loader → FLAG."""
        from scripts.lint_inline_llm import check_file

        code = """
from yamlgraph.executor import execute_prompt

def main():
    result = execute_prompt("prompt.yaml", {"x": 1})
    print(result)

if __name__ == "__main__":
    main()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            result = check_file(Path(f.name))
        assert result is not None, "Should flag inline LLM without graph loader"
        assert "execute_prompt" in result

    @pytest.mark.req("REQ-YG-073")
    def test_main_with_graph_loader_passes(self):
        """File with main + load_graph_config → OK."""
        from scripts.lint_inline_llm import check_file

        code = """
from yamlgraph.compile.graph_loader import load_graph_config, compile_graph

def main():
    config = load_graph_config("graph.yaml")
    graph = compile_graph(config)
    graph.compile().invoke({})

if __name__ == "__main__":
    main()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            result = check_file(Path(f.name))
        assert result is None, "Graph loader import should pass"

    @pytest.mark.req("REQ-YG-073")
    def test_main_with_both_llm_and_graph_loader_passes(self):
        """File with main + execute_prompt + load_graph_config → OK."""
        from scripts.lint_inline_llm import check_file

        code = """
from yamlgraph.executor import execute_prompt
from yamlgraph.compile.graph_loader import load_graph_config, compile_graph

def main():
    # This is a graph runner that also imports executor
    config = load_graph_config("graph.yaml")
    graph = compile_graph(config)
    graph.compile().invoke({})

if __name__ == "__main__":
    main()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            result = check_file(Path(f.name))
        assert result is None, "Both imports should pass"

    @pytest.mark.req("REQ-YG-073")
    def test_main_with_neither_passes(self):
        """File with main + no LLM imports → OK (pure side-effect script)."""
        from scripts.lint_inline_llm import check_file

        code = """
import os
import sys

def main():
    print("Hello, world!")
    os.makedirs("output", exist_ok=True)

if __name__ == "__main__":
    main()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            result = check_file(Path(f.name))
        assert result is None, "No LLM imports should pass"

    @pytest.mark.req("REQ-YG-073")
    def test_no_main_skipped(self):
        """File without def main() → skipped entirely."""
        from scripts.lint_inline_llm import check_file

        code = """
from yamlgraph.executor import execute_prompt

def helper():
    return execute_prompt("prompt.yaml", {})

class SomeClass:
    pass
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            result = check_file(Path(f.name))
        assert result is None, "No main() should skip check"

    @pytest.mark.req("REQ-YG-073")
    def test_async_main_detected(self):
        """async def main() also checked."""
        from scripts.lint_inline_llm import check_file

        code = """
from yamlgraph.executor_async import execute_prompt_streaming

async def main():
    async for token in execute_prompt_streaming("prompt.yaml", {}):
        print(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            result = check_file(Path(f.name))
        assert result is not None, "Should flag async main with inline LLM"

    @pytest.mark.req("REQ-YG-073")
    def test_direct_provider_import_flagged(self):
        """Direct ChatAnthropic import without graph loader → FLAG."""
        from scripts.lint_inline_llm import check_file

        code = """
from langchain_anthropic import ChatAnthropic

def main():
    llm = ChatAnthropic(model="claude-3")
    result = llm.invoke("hello")
    print(result)

if __name__ == "__main__":
    main()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            result = check_file(Path(f.name))
        assert result is not None, "Should flag direct provider import"
        assert "ChatAnthropic" in result

    @pytest.mark.req("REQ-YG-073")
    def test_load_and_compile_recognized(self):
        """load_and_compile is also a valid graph loader import."""
        from scripts.lint_inline_llm import check_file

        code = """
from yamlgraph.executor import execute_prompt
from yamlgraph.compile.graph_loader import load_and_compile

def main():
    graph = load_and_compile("graph.yaml")
    graph.compile().invoke({})

if __name__ == "__main__":
    main()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            result = check_file(Path(f.name))
        assert result is None, "load_and_compile should count as graph loader"


class TestLintInlineLLMCLI:
    """Test CLI interface."""

    @pytest.mark.req("REQ-YG-073")
    def test_scan_returns_zero_on_clean_codebase(self):
        """scan_directory returns 0 when no violations."""
        from scripts.lint_inline_llm import scan_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a clean file
            clean = Path(tmpdir) / "clean.py"
            clean.write_text("""
def main():
    print("hello")

if __name__ == "__main__":
    main()
""")
            violations = scan_directory(Path(tmpdir))
            assert len(violations) == 0

    @pytest.mark.req("REQ-YG-073")
    def test_scan_returns_violations(self):
        """scan_directory returns violations list."""
        from scripts.lint_inline_llm import scan_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a violating file
            bad = Path(tmpdir) / "bad.py"
            bad.write_text("""
from yamlgraph.executor import execute_prompt

def main():
    execute_prompt("x.yaml", {})

if __name__ == "__main__":
    main()
""")
            violations = scan_directory(Path(tmpdir))
            assert len(violations) == 1
            assert "bad.py" in violations[0][0].name
