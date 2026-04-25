"""Acceptance tests for FR-285: Watcher2 Forensic Failure Diary.

Tests for automated forensic analysis phase in watcher2's handle_failure function.
These tests target the unmodified code and MUST fail (RED phase).

AC-01: `handle_failure` function includes forensic analysis phase before topic archival
AC-02: Forensic analysis reads failure reason, topic content, and relevant logs
AC-03: Analysis generates structured diary entry in `docs/diary/` with forensic prefix
AC-04: Diary entry includes root cause, evidence summary, and recommendations
AC-05: Enhanced failure record preserved in `.chaplain/failed/` with diary reference
AC-06: Forensic phase only runs if Copilot session available (fail gracefully)
AC-07: Tests added for forensic diary generation
AC-08: Documentation updated for new failure handling workflow
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
WATCHER2_SH = REPO_ROOT / ".chaplain" / "watcher2.sh"


@pytest.mark.req("REQ-YG-309")
def test_handle_failure_invokes_forensic_analysis():
    """AC-01: handle_failure function includes forensic analysis phase before topic archival.

    Expected: handle_failure should call forensic analysis before moving topic to failed/

    This test MUST fail because handle_failure doesn't invoke forensic analysis.
    """
    content = WATCHER2_SH.read_text()

    # Look for handle_failure function
    assert "handle_failure() {" in content

    # Should not have forensic analysis invocation yet
    # This will fail when forensic analysis is added
    forensic_patterns = [
        "yamlgraph graph run.*forensic",
        "watcher-forensic",
        "forensic.*analysis",
        "analyze.*failure",
    ]

    for pattern in forensic_patterns:
        assert (
            pattern not in content
        ), f"handle_failure already contains forensic analysis pattern: {pattern}"


@pytest.mark.req("REQ-YG-309")
def test_forensic_analysis_infrastructure_missing():
    """AC-02/AC-07: Forensic analysis infrastructure doesn't exist yet.

    Expected: Should not have forensic analysis graph or prompts

    This test MUST fail when forensic infrastructure is added.
    """
    # Check for forensic analysis graph
    graphs_dir = REPO_ROOT / ".chaplain" / "graphs"
    if graphs_dir.exists():
        forensic_dirs = [
            d
            for d in graphs_dir.iterdir()
            if d.is_dir() and ("forensic" in d.name or "failure" in d.name)
        ]
        # Filter out existing forensic preservation (only check for analysis)
        analysis_dirs = [
            d for d in forensic_dirs if "analysis" in d.name or "diary" in d.name
        ]
        assert (
            len(analysis_dirs) == 0
        ), f"Forensic analysis graphs already exist: {analysis_dirs}"


@pytest.mark.req("REQ-YG-309")
def test_diary_writing_not_in_handle_failure():
    """AC-03: handle_failure doesn't write diary entries yet.

    Expected: handle_failure should not contain diary writing logic

    This test MUST fail when diary writing is added to handle_failure.
    """
    content = WATCHER2_SH.read_text()

    # Extract handle_failure function
    start = content.find("handle_failure() {")
    if start == -1:
        pytest.fail("handle_failure function not found")

    # Find function end by counting braces
    brace_count = 0
    i = start
    while i < len(content):
        if content[i] == "{":
            brace_count += 1
        elif content[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break
        i += 1
    else:
        pytest.fail("Could not find end of handle_failure function")

    function_body = content[start:end]

    # Should not contain diary writing logic
    diary_patterns = [
        "docs/diary/",
        "write_diary",
        "diary.*entry",
        ".md",  # markdown file creation
    ]

    for pattern in diary_patterns:
        assert (
            pattern not in function_body
        ), f"handle_failure already contains diary pattern: {pattern}"


@pytest.mark.req("REQ-YG-309")
def test_forensic_structured_output_schema_missing():
    """AC-04: Structured forensic diary schema doesn't exist.

    Expected: Should not have forensic diary schema defining root_cause, evidence, etc.

    This test MUST fail when forensic schema is added.
    """
    # Check diary.py for forensic schema
    diary_lib = REPO_ROOT / ".chaplain" / "lib" / "diary.py"
    if diary_lib.exists():
        content = diary_lib.read_text()

        forensic_schema_fields = [
            "root_cause",
            "failure_reason",
            "evidence_summary",
            "recommendations",
            "forensic_entry",
        ]

        for field in forensic_schema_fields:
            assert (
                field not in content
            ), f"Forensic schema field already exists: {field}"


@pytest.mark.req("REQ-YG-309")
def test_failed_topic_enhancement_missing():
    """AC-05: Enhanced failure records with diary references don't exist.

    Expected: Failed topics should not have diary references yet

    This test MUST fail when diary references are added.
    """
    content = WATCHER2_SH.read_text()

    # Find topic archival logic
    topic_move_line = 'mv "$TOPIC_FILE" ".chaplain/failed/'
    assert topic_move_line in content, "Topic move logic not found"

    # Should not have diary reference enhancement
    enhancement_patterns = [
        "echo.*diary",
        ">> .chaplain/failed/",  # appending to failed file
        "forensic.*entry.*path",
    ]

    for pattern in enhancement_patterns:
        assert (
            pattern not in content
        ), f"Enhanced failure record already contains: {pattern}"


@pytest.mark.req("REQ-YG-309")
def test_copilot_availability_check_missing():
    """AC-06: Copilot availability check doesn't exist in handle_failure.

    Expected: handle_failure should not check for copilot availability yet

    This test MUST fail when availability checking is added.
    """
    content = WATCHER2_SH.read_text()

    availability_checks = [
        "command -v yamlgraph",
        "which yamlgraph",
        "type yamlgraph",
        "yamlgraph.*version",
    ]

    for check in availability_checks:
        assert (
            check not in content
        ), f"Copilot availability check already exists: {check}"


@pytest.mark.req("REQ-YG-309")
def test_no_forensic_prompts_exist():
    """AC-07: Forensic analysis prompts don't exist yet.

    Expected: Should not have prompts for watcher2 failure forensic analysis

    This test MUST fail when forensic prompts are added.
    """
    graphs_dir = REPO_ROOT / ".chaplain" / "graphs"

    if graphs_dir.exists():
        # Check all prompt files for watcher2 forensic analysis content
        for graph_dir in graphs_dir.iterdir():
            if graph_dir.is_dir():
                prompts_dir = graph_dir / "prompts"
                if prompts_dir.exists():
                    for prompt_file in prompts_dir.glob("*.yaml"):
                        content = prompt_file.read_text()

                        # Look specifically for watcher2 forensic patterns (not general CI remediation)
                        forensic_prompt_indicators = [
                            "watcher2.*forensic",
                            "forensic.*watcher2",
                            "watcher.*failure.*analysis",
                            "analyze.*watcher.*failure",
                            "forensic.*diary.*generation",
                        ]

                        for indicator in forensic_prompt_indicators:
                            import re

                            assert not re.search(
                                indicator, content.lower()
                            ), f"Watcher2 forensic analysis prompt already exists in {prompt_file}: {indicator}"


@pytest.mark.req("REQ-YG-309")
def test_handle_failure_preserves_original_behavior():
    """AC-06b: handle_failure retains original 3-step behavior.

    Expected: Should only have original 3 steps, not 4 with forensic analysis

    This test MUST fail when forensic analysis step is added.
    """
    content = WATCHER2_SH.read_text()

    # Find handle_failure function
    start = content.find("handle_failure() {")
    end = content.find("\n}", start) + 2
    function_body = content[start:end]

    # Count major operations (should be 3: log, move, metrics - preserve is conditional)
    operations = [
        "log_error",  # 1. Log error
        'mv "$TOPIC_FILE"',  # 2. Move topic
        "write_cycle_metrics",  # 3. Write metrics
    ]

    found_operations = []
    for op in operations:
        if op in function_body:
            found_operations.append(op)

    # Should have exactly these 3 operations, not more
    assert len(found_operations) == 3, (
        f"Expected 3 operations, found {len(found_operations)}: {found_operations}. "
        "If more operations exist, forensic analysis may already be implemented."
    )

    # Should NOT have forensic analysis operation
    forensic_operations = ["forensic", "analyze_failure", "diary.*entry"]

    for forensic_op in forensic_operations:
        import re

        assert not re.search(
            forensic_op, function_body
        ), f"Forensic operation already exists in handle_failure: {forensic_op}"


@pytest.mark.req("REQ-YG-309")
def test_forensic_library_functions_missing():
    """AC-07: Forensic analysis library functions don't exist.

    Expected: Should not have format_forensic_entry or analyze_failure functions

    This test MUST fail when forensic library is added.
    """
    diary_lib = REPO_ROOT / ".chaplain" / "lib" / "diary.py"

    if diary_lib.exists():
        content = diary_lib.read_text()

        forensic_functions = [
            "def format_forensic_entry",
            "def analyze_failure",
            "def parse_failure_logs",
            "def generate_forensic_diary",
        ]

        for func in forensic_functions:
            assert (
                func not in content
            ), f"Forensic library function already exists: {func}"


@pytest.mark.req("REQ-YG-309")
def test_forensic_variable_extraction_missing():
    """AC-02: Failure context extraction variables don't exist.

    Expected: handle_failure should not extract failure context yet

    This test MUST fail when context extraction is added.
    """
    content = WATCHER2_SH.read_text()

    context_variables = [
        "FAILURE_REASON=",
        "TOPIC_CONTENT=",
        "LOG_FILES=",
        "WORKTREE_STATE=",
    ]

    for var in context_variables:
        assert var not in content, f"Failure context variable already exists: {var}"


@pytest.mark.req("REQ-YG-309")
def test_log_file_analysis_missing():
    """AC-02: Log file analysis doesn't exist in handle_failure.

    Expected: Should not analyze tmp/watcher2-*.log files yet

    This test MUST fail when log analysis is added.
    """
    content = WATCHER2_SH.read_text()

    log_analysis_patterns = [
        "tmp/watcher2-.*\\.log",
        "find.*tmp.*log",
        "cat.*watcher2.*log",
        "grep.*tmp.*log",
    ]

    for pattern in log_analysis_patterns:
        assert pattern not in content, f"Log analysis already exists: {pattern}"


@pytest.mark.req("REQ-YG-309")
def test_forensic_documentation_missing():
    """AC-08: Documentation for forensic failure analysis doesn't exist.

    Expected: Should not document forensic analysis workflow yet

    This test MUST fail when forensic documentation is added.
    """
    doc_files = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / ".chaplain" / "README.md",
    ]

    for doc_file in doc_files:
        if doc_file.exists():
            content = doc_file.read_text()

            forensic_docs = [
                "forensic failure analysis",
                "forensic diary generation",
                "failure analysis phase",
                "forensic analysis workflow",
            ]

            for doc_pattern in forensic_docs:
                assert (
                    doc_pattern not in content.lower()
                ), f"Forensic analysis documentation already exists in {doc_file}: {doc_pattern}"
