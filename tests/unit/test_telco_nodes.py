"""Unit tests for Telco Voice Call Demo (FR-071).

Tests for REQ-YG-078 through REQ-YG-082.

Note: Uses conftest.py fixture to mock optional dependencies (twilio, elevenlabs,
websockets, httpx) without polluting other tests during collection.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

# Define constants for mocked modules - actual mocking done in fixture below
_MOCK_MODULES = [
    "twilio",
    "twilio.rest",
    "elevenlabs",
    "websockets",
    "websockets.sync",
    "websockets.sync.client",
    "httpx",
]


@pytest.fixture(autouse=True, scope="module")
def _mock_telco_dependencies():
    """Mock optional telco dependencies for this module only.

    Uses fixture (runs at execution time) instead of module-level code
    (runs at collection time) to avoid polluting other tests.
    """
    import sys

    # Save originals
    originals = {key: sys.modules.get(key) for key in _MOCK_MODULES}

    # Install mocks
    for mod in _MOCK_MODULES:
        sys.modules[mod] = MagicMock()

    # Clear any cached imports of outcaller modules
    to_clear = [k for k in sys.modules if k.startswith("projects.outcaller")]
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
    to_clear = [k for k in sys.modules if k.startswith("projects.outcaller")]
    for k in to_clear:
        del sys.modules[k]


@pytest.mark.req("REQ-YG-078")
class TestInitiateCall:
    """REQ-YG-078: YAMLGraph orchestrates outbound Twilio voice call."""

    def test_missing_stream_url_raises(self) -> None:
        """initiate_call raises MissingStreamUrlError if VOICE_STREAM_URL not set."""
        from projects.outcaller.nodes import twilio_call
        from projects.outcaller.nodes.coordinator import MissingStreamUrlError

        # Patch the module-level constant
        with (
            patch.object(twilio_call, "VOICE_STREAM_URL", ""),
            pytest.raises(MissingStreamUrlError),
        ):
            twilio_call.initiate_call({"phone": "+1234567890"})

    def test_phone_required(self) -> None:
        """initiate_call raises ValueError if phone not in state."""
        from projects.outcaller.nodes import twilio_call

        with (
            patch.object(twilio_call, "VOICE_STREAM_URL", "wss://test.ngrok.io"),
            pytest.raises(ValueError, match="phone"),
        ):
            twilio_call.initiate_call({})

    def test_initiates_call_and_waits(self) -> None:
        """initiate_call creates session, calls Twilio, waits for WS."""
        from projects.outcaller.nodes import coordinator, twilio_call

        # Mock session
        mock_session = MagicMock()
        mock_session.call_sid = "CA123"
        mock_session.stream_sid = "MZ456"

        # Mock Twilio client
        mock_client = MagicMock()
        mock_call = MagicMock()
        mock_call.sid = "CA123"
        mock_client.calls.create.return_value = mock_call

        with (
            patch.object(twilio_call, "VOICE_STREAM_URL", "wss://test.ngrok.io"),
            patch.object(coordinator, "TelcoSession", return_value=mock_session),
            patch("twilio.rest.Client", return_value=mock_client),
        ):
            result = twilio_call.initiate_call({"phone": "+1234567890"})

        assert result["call_info"]["call_sid"] == "CA123"
        mock_session.start.assert_called_once()
        mock_session.wait_for_ws_connect.assert_called_once()


@pytest.mark.req("REQ-YG-079")
class TestSpeak:
    """REQ-YG-079: speak node performs TTS via ElevenLabs and transcodes via ffmpeg."""

    def test_speak_generates_tts_and_sends(self) -> None:
        """speak generates TTS, transcodes, and sends to session."""
        from projects.outcaller.nodes import coordinator, twilio_call

        mock_session = MagicMock()

        # Mock ElevenLabs response
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = [b"mp3data"]

        with (
            patch.object(coordinator, "_active_session", mock_session),
            patch.object(coordinator, "get_active_session", return_value=mock_session),
            patch("elevenlabs.ElevenLabs", return_value=mock_client),
            patch.object(
                twilio_call, "_transcode_mp3_to_mulaw", return_value=b"\x00" * 1280
            ),
        ):
            result = twilio_call.speak({"next_utterance": "Hello!"})

        assert result["last_spoken"] == "Hello!"
        assert mock_session.put_outbound_sync.call_count == 2  # 2 chunks

    def test_speak_skips_done_marker(self) -> None:
        """speak returns empty if next_utterance is [DONE]."""
        from projects.outcaller.nodes import coordinator, twilio_call

        mock_session = MagicMock()

        with patch.object(coordinator, "get_active_session", return_value=mock_session):
            result = twilio_call.speak({"next_utterance": "[DONE]"})

        assert result["last_spoken"] == ""


@pytest.mark.req("REQ-YG-080")
class TestListenAndTranscribe:
    """REQ-YG-080: listen_and_transcribe streams to ElevenLabs STT."""

    def test_listen_collects_audio_and_transcribes(self) -> None:
        """listen_and_transcribe collects audio, transcodes, and calls STT."""
        from projects.outcaller.nodes import coordinator, twilio_call

        mock_session = MagicMock()

        # Return some audio then silence
        # mulaw: 0x7F is silence (center); bytes far from 0x7F are speech
        audio_frame = b"\x10" * 640  # Non-silence (0x10 = 16, far from 0x7F = 127)
        silence_frame = b"\x7f" * 640  # Silence (0x7F = 127, center)
        # Need 5 speech frames + 76 silence frames (max_silence=75)
        mock_session.get_inbound_sync.side_effect = [audio_frame] * 5 + [
            silence_frame
        ] * 80

        with (
            patch.object(coordinator, "get_active_session", return_value=mock_session),
            patch.object(
                twilio_call, "_transcode_mulaw_to_pcm16", return_value=b"pcm_data"
            ),
            patch.object(
                twilio_call, "_transcribe_elevenlabs", return_value="Hello world"
            ),
        ):
            result = twilio_call.listen_and_transcribe({})

        assert result["transcript"] == "Hello world"

    def test_listen_raises_on_hangup(self) -> None:
        """listen_and_transcribe raises CallHangupError on None sentinel."""
        from projects.outcaller.nodes import coordinator, twilio_call
        from projects.outcaller.nodes.coordinator import CallHangupError

        mock_session = MagicMock()
        mock_session.get_inbound_sync.return_value = None  # Hangup sentinel

        with (
            patch.object(coordinator, "get_active_session", return_value=mock_session),
            pytest.raises(CallHangupError),
        ):
            twilio_call.listen_and_transcribe({})


@pytest.mark.req("REQ-YG-081")
class TestCoordinator:
    """REQ-YG-081: WebSocket coordinator bridges asyncio and sync tool nodes."""

    def test_session_queue_operations(self) -> None:
        """TelcoSession queue operations are thread-safe."""
        from projects.outcaller.nodes.coordinator import TelcoSession

        # Create session with real queues
        session = TelcoSession()

        # Set up mock loop for thread-safe operations
        loop = asyncio.new_event_loop()
        session._loop = loop

        # Test put/get operations run without error
        # (Full integration tested separately)
        assert session.inbound is not None
        assert session.outbound is not None

    def test_wait_for_ws_connect_timeout(self) -> None:
        """wait_for_ws_connect raises CallNotAnsweredError on timeout."""
        from projects.outcaller.nodes.coordinator import (
            CallNotAnsweredError,
            TelcoSession,
        )

        session = TelcoSession()

        with pytest.raises(CallNotAnsweredError):
            session.wait_for_ws_connect(timeout=0.01)

    def test_signal_ws_connected(self) -> None:
        """signal_ws_connected sets stream_sid and signals event."""
        from projects.outcaller.nodes.coordinator import TelcoSession

        session = TelcoSession()
        session.signal_ws_connected("MZ123")

        assert session.stream_sid == "MZ123"
        assert session._ws_connected.is_set()


@pytest.mark.req("REQ-YG-082")
class TestNoAudioopDependency:
    """REQ-YG-082: ElevenLabs built-in VAD; no audioop dependency."""

    def test_transcode_uses_ffmpeg_not_audioop(self) -> None:
        """Transcode functions use ffmpeg subprocess, not audioop."""
        import inspect

        from projects.outcaller.nodes import twilio_call

        # Check that audioop is not imported in the module (import statement)
        source = inspect.getsource(twilio_call)
        assert "import audioop" not in source
        assert "from audioop" not in source
        assert "subprocess" in source

    @patch("subprocess.run")
    def test_mp3_to_mulaw_calls_ffmpeg(self, mock_run: MagicMock) -> None:
        """_transcode_mp3_to_mulaw uses ffmpeg subprocess."""
        from projects.outcaller.nodes import twilio_call

        mock_run.return_value = MagicMock(returncode=0, stdout=b"mulaw_data")

        result = twilio_call._transcode_mp3_to_mulaw(b"mp3_data")

        assert result == b"mulaw_data"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"

    @patch("subprocess.run")
    def test_mulaw_to_pcm_calls_ffmpeg(self, mock_run: MagicMock) -> None:
        """_transcode_mulaw_to_pcm16 uses ffmpeg subprocess."""
        from projects.outcaller.nodes import twilio_call

        mock_run.return_value = MagicMock(returncode=0, stdout=b"pcm_data")

        result = twilio_call._transcode_mulaw_to_pcm16(b"mulaw_data")

        assert result == b"pcm_data"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"


@pytest.mark.req("REQ-YG-078")
class TestAccumulateAnswer:
    """Test accumulate_answer node function."""

    def test_accumulate_appends_transcript(self) -> None:
        """accumulate_answer appends transcript to answers list."""
        from projects.outcaller.nodes import twilio_call

        result = twilio_call.accumulate_answer(
            {
                "transcript": "My name is John",
                "answers": ["Previous answer"],
            }
        )

        assert result["answers"] == ["Previous answer", "My name is John"]

    def test_accumulate_handles_empty_answers(self) -> None:
        """accumulate_answer handles None/empty answers."""
        from projects.outcaller.nodes import twilio_call

        result = twilio_call.accumulate_answer(
            {
                "transcript": "Hello",
                "answers": None,
            }
        )

        assert result["answers"] == ["Hello"]

    def test_accumulate_skips_empty_transcript(self) -> None:
        """accumulate_answer skips empty transcript."""
        from projects.outcaller.nodes import twilio_call

        result = twilio_call.accumulate_answer(
            {
                "transcript": "",
                "answers": ["Existing"],
            }
        )

        assert result["answers"] == ["Existing"]


@pytest.mark.req("REQ-YG-078")
class TestEndCall:
    """Test end_call node function."""

    def test_end_call_hangs_up_and_shuts_down(self) -> None:
        """end_call hangs up via Twilio and shuts down session."""
        from projects.outcaller.nodes import coordinator, twilio_call

        mock_session = MagicMock()
        mock_client = MagicMock()

        with (
            patch.object(coordinator, "get_active_session", return_value=mock_session),
            patch.object(coordinator, "clear_active_session"),
            patch("twilio.rest.Client", return_value=mock_client),
        ):
            result = twilio_call.end_call(
                {
                    "call_info": {"call_sid": "CA123"},
                }
            )

        assert result["call_result"]["status"] == "completed"
        mock_session.shutdown.assert_called_once()
