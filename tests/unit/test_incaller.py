"""Unit tests for Incaller Inbound Voice Call (IC-000).

Tests for REQ-YG-084 through REQ-YG-086.

Note: Uses conftest.py fixture to mock optional dependencies (twilio, elevenlabs,
websockets, httpx) without polluting other tests during collection.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# Define constants for mocked modules - actual mocking done in fixture below
# Note: httpx excluded because TestClient needs it
_MOCK_MODULES = [
    "twilio",
    "twilio.rest",
    "elevenlabs",
    "elevenlabs.realtime",
    "elevenlabs.realtime.scribe",
    "websockets",
    "websockets.sync",
    "websockets.sync.client",
]


@pytest.fixture(autouse=True, scope="module")
def _mock_telco_dependencies():
    """Mock optional telco dependencies for this module only.

    Uses fixture (runs at execution time) instead of module-level code
    (runs at collection time) to avoid polluting other tests.
    """
    import sys
    from enum import Enum

    # Save originals
    originals = {key: sys.modules.get(key) for key in _MOCK_MODULES}

    # Create mock enums for ElevenLabs SDK
    class MockAudioFormat(Enum):
        ULAW_8000 = "ulaw_8000"
        PCM_16000 = "pcm_16000"

    class MockCommitStrategy(Enum):
        VAD = "vad"
        MANUAL = "manual"

    # Install mocks
    for mod in _MOCK_MODULES:
        sys.modules[mod] = MagicMock()

    # Set up elevenlabs.realtime.scribe with proper enums
    sys.modules["elevenlabs.realtime.scribe"].AudioFormat = MockAudioFormat
    sys.modules["elevenlabs.realtime.scribe"].CommitStrategy = MockCommitStrategy

    # Clear any cached imports of incaller/outcaller modules
    to_clear = [
        k
        for k in sys.modules
        if k.startswith("projects.incaller") or k.startswith("projects.outcaller")
    ]
    for k in to_clear:
        del sys.modules[k]

    yield

    # Restore originals
    for key, original in originals.items():
        if original is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = original

    # Clear cached imports again
    to_clear = [
        k
        for k in sys.modules
        if k.startswith("projects.incaller") or k.startswith("projects.outcaller")
    ]
    for k in to_clear:
        del sys.modules[k]


@pytest.mark.req("REQ-YG-084")
class TestAwaitCall:
    """REQ-YG-084: await_call starts HTTP+WS server and blocks until inbound call."""

    def test_missing_stream_url_raises(self) -> None:
        """await_call raises MissingStreamUrlError if VOICE_STREAM_URL not set."""
        from projects.incaller.nodes import twilio_inbound
        from projects.outcaller.nodes.coordinator import MissingStreamUrlError

        # Patch the module-level constant
        with (
            patch.object(twilio_inbound, "VOICE_STREAM_URL", ""),
            pytest.raises(MissingStreamUrlError),
        ):
            twilio_inbound.await_call({})

    def test_timeout_configurable(self) -> None:
        """await_call timeout is configurable via INCALLER_TIMEOUT env var."""
        from projects.incaller.nodes import twilio_inbound

        # Default timeout should be 300s
        assert twilio_inbound.INCALLER_TIMEOUT == 300

    def test_returns_call_info(self) -> None:
        """await_call returns call_info dict with call_sid, stream_sid, caller_number."""
        import threading

        from projects.incaller.nodes import twilio_inbound
        from projects.outcaller.nodes.coordinator import TelcoSession

        # Create mock session that signals connection immediately
        mock_session = MagicMock(spec=TelcoSession)
        mock_session.call_sid = "CA123"
        mock_session.stream_sid = "MZ456"
        mock_session.caller_number = "+358405950430"
        mock_session._ws_connected = threading.Event()
        mock_session._ws_connected.set()  # Already connected

        with (
            patch.object(
                twilio_inbound, "VOICE_STREAM_URL", "https://example.ngrok.io"
            ),
            patch.object(twilio_inbound, "TelcoSession", return_value=mock_session),
            patch.object(twilio_inbound, "set_active_session"),
        ):
            # Skip actual server start
            mock_session.start = MagicMock()

            result = twilio_inbound.await_call({})

        assert "call_info" in result
        assert result["call_info"]["call_sid"] == "CA123"
        assert result["call_info"]["stream_sid"] == "MZ456"
        assert result["call_info"]["caller_number"] == "+358405950430"


@pytest.mark.req("REQ-YG-085")
class TestIncomingWebhook:
    """REQ-YG-085: POST /incoming responds with TwiML <Connect><Stream>."""

    def test_incoming_returns_twiml(self) -> None:
        """POST /incoming returns TwiML with Stream URL."""

        from fastapi.testclient import TestClient

        from projects.incaller import server
        from projects.outcaller.nodes.coordinator import TelcoSession

        mock_session = MagicMock(spec=TelcoSession)
        mock_session.call_sid = None
        mock_session.caller_number = None

        with patch.object(server, "VOICE_STREAM_URL", "https://example.ngrok.io"):
            app = server.create_app(mock_session)
            client = TestClient(app)

            response = client.post(
                "/incoming",
                data={
                    "CallSid": "CA123",
                    "From": "+358405950430",
                    "To": "+358454918222",
                },
            )

        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "<Response>" in response.text
        assert "<Connect>" in response.text
        assert "<Stream" in response.text
        assert "wss://example.ngrok.io/voice" in response.text

    def test_incoming_stores_caller_info(self) -> None:
        """POST /incoming stores caller number in session."""
        from fastapi.testclient import TestClient

        from projects.incaller import server
        from projects.outcaller.nodes.coordinator import TelcoSession

        mock_session = MagicMock(spec=TelcoSession)
        mock_session.call_sid = None
        mock_session.caller_number = None

        with patch.object(server, "VOICE_STREAM_URL", "https://example.ngrok.io"):
            app = server.create_app(mock_session)
            client = TestClient(app)

            client.post(
                "/incoming",
                data={
                    "CallSid": "CA123",
                    "From": "+358405950430",
                    "To": "+358454918222",
                },
            )

        assert mock_session.call_sid == "CA123"
        assert mock_session.caller_number == "+358405950430"


@pytest.mark.req("REQ-YG-086")
class TestReusesOutcaller:
    """REQ-YG-086: Incaller reuses outcaller TTS, STT, probe-recap."""

    def test_speak_imported_from_outcaller(self) -> None:
        """speak function is importable from outcaller."""
        from projects.outcaller.nodes.twilio_call import speak

        assert callable(speak)

    def test_listen_imported_from_outcaller(self) -> None:
        """listen_and_transcribe function is importable from outcaller."""
        from projects.outcaller.nodes.twilio_call import listen_and_transcribe

        assert callable(listen_and_transcribe)

    def test_probe_recap_imported_from_outcaller(self) -> None:
        """probe_recap functions are importable from outcaller."""
        from projects.outcaller.nodes.probe_recap import (
            apply_corrections,
            check_missing,
            extract_answers,
            parse_targets,
        )

        assert callable(parse_targets)
        assert callable(extract_answers)
        assert callable(check_missing)
        assert callable(apply_corrections)

    def test_coordinator_imported_from_outcaller(self) -> None:
        """TelcoSession is importable from outcaller coordinator."""
        from projects.outcaller.nodes.coordinator import (
            TelcoSession,
            get_active_session,
            set_active_session,
        )

        assert callable(TelcoSession)
        assert callable(get_active_session)
        assert callable(set_active_session)


@pytest.mark.req("REQ-YG-084")
class TestIC001SIN1UserRefused:
    """IC-001 SIN-1: extract_answers must propagate user_refused to state."""

    def test_extract_answers_returns_user_refused(self) -> None:
        """extract_answers includes user_refused in return dict when LLM says True."""
        from unittest.mock import MagicMock

        from projects.outcaller.nodes.probe_recap import extract_answers

        # Mock state with minimal required fields
        state = {
            "target_fields": [{"id": "name", "description": "Your name"}],
            "extracted": {"name": None},
            "transcript": "I'm not interested, please take me off your list.",
            "answers": [],
            "prompts_dir": "projects/outcaller/prompts",
        }

        # Mock the execute_prompt to return user_refused=True
        mock_result = MagicMock()
        mock_result.updates = {"name": None}
        mock_result.user_refused = True

        # Patch in yamlgraph.executor since that's where it's imported from
        with (
            patch(
                "yamlgraph.executor.execute_prompt",
                return_value=mock_result,
            ),
            patch(
                "yamlgraph.schema_loader.load_schema_from_yaml",
                return_value=MagicMock(),
            ),
        ):
            result = extract_answers(state)

        # SIN-1: This should include user_refused, but currently doesn't
        assert "user_refused" in result, "extract_answers must return user_refused"
        assert result["user_refused"] is True


@pytest.mark.req("REQ-YG-084")
class TestIC001SIN2GoodbyeRefusedType:
    """IC-001 SIN-2: goodbye_refused prompt should return string, not Pydantic model."""

    def test_goodbye_refused_returns_string(self) -> None:
        """goodbye_refused prompt should return plain string for speak() node."""
        from pathlib import Path

        from yamlgraph.utils.prompts import load_prompt

        # Load the prompt config
        prompts_dir = Path(__file__).parent.parent.parent / "projects/outcaller/prompts"
        config = load_prompt("goodbye_refused", prompts_dir=str(prompts_dir))

        # SIN-2: This prompt has a schema but should NOT (all other next_utterance prompts are plain strings)
        # The presence of a schema causes execute_prompt to return a Pydantic model, not string
        assert config.get("schema") is None, (
            "goodbye_refused should not have a schema - "
            "all next_utterance prompts must return plain strings for speak() node"
        )
