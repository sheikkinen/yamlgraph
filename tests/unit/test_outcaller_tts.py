"""Unit tests for outcaller TTS mark-based audio completion.

OC-006: Wait for TTS playback completion before ending call.

The issue: speak() streams audio to Twilio outbound queue and returns immediately.
If end_call() hangs up before Twilio finishes playing, caller doesn't hear goodbye.

Solution: Use Twilio mark events to track playback position. After sending audio,
send a mark event and wait for Twilio to echo it back before returning.

REQ-YG-086: TTS playback completion tracking via Twilio mark events.
"""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.req("REQ-YG-086")
class TestTelcoSessionMarks:
    """Tests for TelcoSession mark event handling."""

    def test_session_has_mark_tracking(self) -> None:
        """TelcoSession must have mark tracking infrastructure."""
        from projects.outcaller.nodes.coordinator import TelcoSession

        session = TelcoSession()

        # Must have method to send mark and wait
        assert hasattr(
            session, "send_mark_and_wait"
        ), "TelcoSession needs send_mark_and_wait() to track audio playback"

        # Must have method to signal mark received (called from WS handler)
        assert hasattr(
            session, "signal_mark_received"
        ), "TelcoSession needs signal_mark_received() for WS handler to call"

    def test_send_mark_blocks_until_received(self) -> None:
        """send_mark_and_wait() must block until mark is received or timeout."""
        from projects.outcaller.nodes.coordinator import TelcoSession

        session = TelcoSession()
        session._loop = MagicMock()
        session._loop.call_soon_threadsafe = MagicMock()

        # Start the wait in a thread
        result = {"completed": False, "timed_out": False}

        def wait_for_mark() -> None:
            try:
                session.send_mark_and_wait("test-mark", timeout=0.5)
                result["completed"] = True
            except TimeoutError:
                result["timed_out"] = True

        wait_thread = threading.Thread(target=wait_for_mark)
        wait_thread.start()

        # Small delay to ensure wait started
        time.sleep(0.1)

        # Signal the mark received
        session.signal_mark_received("test-mark")

        wait_thread.join(timeout=1.0)

        assert result[
            "completed"
        ], "send_mark_and_wait should complete when mark received"
        assert not result["timed_out"], "Should not timeout when mark is received"

    def test_send_mark_times_out(self) -> None:
        """send_mark_and_wait() must timeout if mark never received."""
        from projects.outcaller.nodes.coordinator import TelcoSession

        session = TelcoSession()
        session._loop = MagicMock()
        session._loop.call_soon_threadsafe = MagicMock()

        # Should timeout since no mark is ever signaled
        with pytest.raises(TimeoutError):
            session.send_mark_and_wait("never-received", timeout=0.2)


@pytest.mark.req("REQ-YG-086")
class TestTTSWaitsForCompletion:
    """Tests for speak() waiting for audio playback completion."""

    def test_speak_waits_for_mark(self) -> None:
        """speak() must wait for mark event before returning.

        This ensures the caller hears the full utterance before
        the graph proceeds to end_call.
        """
        from unittest.mock import MagicMock

        # Mock the coordinator session
        mock_session = MagicMock()
        mock_session.is_disconnected = False
        mock_session.put_outbound_sync = MagicMock()
        mock_session.send_mark_and_wait = MagicMock()

        with (
            patch(
                "projects.outcaller.nodes.coordinator.get_active_session",
                return_value=mock_session,
            ),
            patch("elevenlabs.ElevenLabs") as mock_elevenlabs,
            patch("subprocess.Popen") as mock_popen,
        ):
            # Mock ffmpeg process
            mock_proc = MagicMock()
            mock_proc.stdin = MagicMock()
            mock_proc.stdout = MagicMock()
            mock_proc.stdout.read = MagicMock(side_effect=[b"audio", b""])
            mock_popen.return_value = mock_proc

            # Mock ElevenLabs
            mock_client = MagicMock()
            mock_client.text_to_speech.convert.return_value = [b"chunk"]
            mock_elevenlabs.return_value = mock_client

            from projects.outcaller.nodes.tts import speak

            # Speak something
            speak({"next_utterance": "Hello goodbye"})

            # Must wait for mark after sending audio
            mock_session.send_mark_and_wait.assert_called_once()
