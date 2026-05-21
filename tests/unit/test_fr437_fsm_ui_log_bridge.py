"""Unit tests for FR-437 FSM UI activity log bridge."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock

import pytest

from yamlgraph.utils.fsm import emit_ui_activity


@pytest.mark.req("REQ-YG-319")
class TestFr437UiLogBridge:
    def test_noop_when_ui_events_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("UI_EVENTS_ENABLED", raising=False)
        run = MagicMock()
        monkeypatch.setattr("yamlgraph.utils.fsm.ui_log.subprocess.run", run)

        emit_ui_activity("hello")

        run.assert_not_called()

    def test_subprocess_called_when_enabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("UI_EVENTS_ENABLED", "true")
        run = MagicMock()
        monkeypatch.setattr("yamlgraph.utils.fsm.ui_log.subprocess.run", run)

        emit_ui_activity("processing", level="warning", source="graph.node")

        run.assert_called_once()
        args, kwargs = run.call_args
        cmd = args[0]
        assert "statemachine_engine.database.cli" in cmd
        assert "send-event" in cmd
        assert "--target" in cmd and "ui" in cmd
        assert "--type" in cmd and "activity_log" in cmd
        assert "--source" in cmd and "graph.node" in cmd

        payload = cmd[cmd.index("--payload") + 1]
        assert '"message": "processing"' in payload
        assert '"level": "WARNING"' in payload
        assert kwargs["timeout"] == 5

    def test_timeout_is_swallowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("UI_EVENTS_ENABLED", "true")

        def _raise_timeout(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(cmd=["x"], timeout=5)

        monkeypatch.setattr("yamlgraph.utils.fsm.ui_log.subprocess.run", _raise_timeout)

        emit_ui_activity("processing")

    def test_file_not_found_is_swallowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("UI_EVENTS_ENABLED", "true")

        def _raise_not_found(*_args, **_kwargs):
            raise FileNotFoundError("missing")

        monkeypatch.setattr(
            "yamlgraph.utils.fsm.ui_log.subprocess.run", _raise_not_found
        )

        emit_ui_activity("processing")
