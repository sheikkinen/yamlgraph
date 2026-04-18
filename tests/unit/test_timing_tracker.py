"""Tests for execution timing callback (FR-231 Phase 1, REQ-YG-231).

TDD tests for `ExecutionTimingCallbackHandler` that tracks
per-call and total wall-clock LLM duration.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# ExecutionTimingCallbackHandler unit tests
# =============================================================================


class TestExecutionTimingCallbackHandler:
    """Tests for the timing callback handler."""

    @pytest.mark.req("REQ-YG-231")
    def test_initial_state_is_zero(self):
        """Handler starts with zero duration and zero calls."""
        from yamlgraph.utils.timing_tracker import ExecutionTimingCallbackHandler

        handler = ExecutionTimingCallbackHandler()
        assert handler.total_duration == 0.0
        assert handler.total_calls == 0
        assert handler.call_durations == []

    @pytest.mark.req("REQ-YG-231")
    def test_tracks_single_llm_call_duration(self):
        """on_llm_start/on_llm_end tracks wall-clock duration."""
        from yamlgraph.utils.timing_tracker import ExecutionTimingCallbackHandler

        handler = ExecutionTimingCallbackHandler()
        handler.on_llm_start({}, ["test"])
        time.sleep(0.05)
        handler.on_llm_end(response=MagicMock())

        assert handler.total_calls == 1
        assert handler.total_duration >= 0.04
        assert len(handler.call_durations) == 1
        assert handler.call_durations[0] >= 0.04

    @pytest.mark.req("REQ-YG-231")
    def test_accumulates_multiple_calls(self):
        """Multiple LLM calls accumulate total duration."""
        from yamlgraph.utils.timing_tracker import ExecutionTimingCallbackHandler

        handler = ExecutionTimingCallbackHandler()

        for _ in range(3):
            handler.on_llm_start({}, ["test"])
            time.sleep(0.02)
            handler.on_llm_end(response=MagicMock())

        assert handler.total_calls == 3
        assert handler.total_duration >= 0.05
        assert len(handler.call_durations) == 3

    @pytest.mark.req("REQ-YG-231")
    def test_summary_returns_correct_structure(self):
        """summary() returns dict with total_duration_s, call_count, mean_duration_s."""
        from yamlgraph.utils.timing_tracker import ExecutionTimingCallbackHandler

        handler = ExecutionTimingCallbackHandler()
        handler.on_llm_start({}, ["test"])
        time.sleep(0.02)
        handler.on_llm_end(response=MagicMock())

        summary = handler.summary()

        assert "total_duration_s" in summary
        assert "call_count" in summary
        assert "mean_duration_s" in summary
        assert summary["call_count"] == 1
        assert summary["total_duration_s"] >= 0.01
        assert summary["mean_duration_s"] >= 0.01

    @pytest.mark.req("REQ-YG-231")
    def test_summary_mean_with_multiple_calls(self):
        """Mean duration is total / call_count."""
        from yamlgraph.utils.timing_tracker import ExecutionTimingCallbackHandler

        handler = ExecutionTimingCallbackHandler()

        handler.on_llm_start({}, ["test"])
        time.sleep(0.02)
        handler.on_llm_end(response=MagicMock())

        handler.on_llm_start({}, ["test"])
        time.sleep(0.04)
        handler.on_llm_end(response=MagicMock())

        summary = handler.summary()
        assert summary["call_count"] == 2
        expected_mean = summary["total_duration_s"] / 2
        assert abs(summary["mean_duration_s"] - expected_mean) < 0.01

    @pytest.mark.req("REQ-YG-231")
    def test_summary_zero_calls_safe(self):
        """summary() is safe when no calls made (no division by zero)."""
        from yamlgraph.utils.timing_tracker import ExecutionTimingCallbackHandler

        handler = ExecutionTimingCallbackHandler()
        summary = handler.summary()

        assert summary["call_count"] == 0
        assert summary["total_duration_s"] == 0.0
        assert summary["mean_duration_s"] == 0.0


# =============================================================================
# Factory function tests
# =============================================================================


class TestCreateTimingTracker:
    """Tests for the factory function."""

    @pytest.mark.req("REQ-YG-231")
    def test_create_timing_tracker_returns_handler(self):
        """create_timing_tracker() returns ExecutionTimingCallbackHandler."""
        from yamlgraph.utils.timing_tracker import (
            ExecutionTimingCallbackHandler,
            create_timing_tracker,
        )

        tracker = create_timing_tracker()
        assert isinstance(tracker, ExecutionTimingCallbackHandler)


# =============================================================================
# CLI --timing flag tests
# =============================================================================


class TestTimingCLIFlag:
    """Tests for --timing CLI flag integration."""

    @pytest.mark.req("REQ-YG-231")
    def test_timing_flag_parsed(self):
        """--timing flag should be parsed by CLI."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["graph", "run", "test.yaml", "--timing"])
        assert args.timing is True

    @pytest.mark.req("REQ-YG-231")
    def test_timing_flag_default_false(self):
        """--timing should default to False."""
        from yamlgraph.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["graph", "run", "test.yaml"])
        assert args.timing is False

    @pytest.mark.req("REQ-YG-231")
    def test_build_run_config_injects_timing_callback(self):
        """_build_run_config injects timing callback when --timing is set."""
        from argparse import Namespace

        from yamlgraph.cli.graph_commands import _build_run_config
        from yamlgraph.utils.timing_tracker import ExecutionTimingCallbackHandler

        args = Namespace(
            thread=None,
            recursion_limit=None,
            timeout=None,
            share_trace=False,
            token_usage=False,
            timing=True,
        )

        mock_config = MagicMock()
        mock_config.data = {}
        mock_config.recursion_limit = 50
        mock_config.timeout = None

        with (
            patch("yamlgraph.utils.tracing.create_tracer", return_value=None),
            patch("yamlgraph.utils.tracing.inject_tracer_config"),
        ):
            result = _build_run_config(args, mock_config, {})

        # Result tuple should include timing_tracker
        # Expected: (initial_state, config, tracker, timeout, tracer, share_flag, timing_tracker)
        assert len(result) == 7
        timing_tracker = result[6]
        assert isinstance(timing_tracker, ExecutionTimingCallbackHandler)

    @pytest.mark.req("REQ-YG-231")
    def test_build_run_config_no_timing_by_default(self):
        """_build_run_config returns None timing_tracker when --timing not set."""
        from argparse import Namespace

        from yamlgraph.cli.graph_commands import _build_run_config

        args = Namespace(
            thread=None,
            recursion_limit=None,
            timeout=None,
            share_trace=False,
            token_usage=False,
            timing=False,
        )

        mock_config = MagicMock()
        mock_config.data = {}
        mock_config.recursion_limit = 50
        mock_config.timeout = None

        with (
            patch("yamlgraph.utils.tracing.create_tracer", return_value=None),
            patch("yamlgraph.utils.tracing.inject_tracer_config"),
        ):
            result = _build_run_config(args, mock_config, {})

        assert len(result) == 7
        timing_tracker = result[6]
        assert timing_tracker is None
