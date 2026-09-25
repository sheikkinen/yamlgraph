"""FR-1073: ocr_cleanup reports skipped pages from the map failures channel."""

from __future__ import annotations

import pytest

from examples.ocr_cleanup.tools.merger import merge_paragraphs_node


@pytest.mark.req("REQ-YG-692")
def test_skip_report_reads_map_failures() -> None:
    failure = {
        "map": "cleanup_pages",
        "dispatch": None,
        "index": 3,
        "error_type": "TimeoutError",
        "message": "llm timed out",
        "node": "cleanup_pages",
        "tolerated": True,
    }
    result = merge_paragraphs_node(
        {"map_results": [], "map_results_failures": [failure]}
    )

    assert result["skip_report"]["skipped_nodes"] == [
        {
            "node": "cleanup_pages",
            "error": "page index 3: llm timed out",
            "type": "unknown_error",
        }
    ]
