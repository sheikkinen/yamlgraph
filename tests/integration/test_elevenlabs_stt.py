"""Integration tests for ElevenLabs STT with TTS-generated fixtures.

These tests make real API calls to ElevenLabs and require:
- ELEVENLABS_API_KEY environment variable
- Audio fixtures in tests/fixtures/audio/

Run with: pytest tests/integration/test_elevenlabs_stt.py -v
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import os
from pathlib import Path

import pytest

# Skip entire module if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("ELEVENLABS_API_KEY"),
    reason="ELEVENLABS_API_KEY not set",
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures/audio"


@pytest.fixture
def api_key() -> str:
    """Get ElevenLabs API key from environment."""
    return os.environ["ELEVENLABS_API_KEY"]


@pytest.fixture
def hello_audio() -> bytes:
    """Load hello.mulaw fixture."""
    return (FIXTURES_DIR / "hello.mulaw").read_bytes()


@pytest.fixture
def claude_audio() -> bytes:
    """Load claude.mulaw fixture."""
    return (FIXTURES_DIR / "claude.mulaw").read_bytes()


@pytest.fixture
def great_audio() -> bytes:
    """Load great.mulaw fixture."""
    return (FIXTURES_DIR / "great.mulaw").read_bytes()


@pytest.mark.integration
@pytest.mark.req("REQ-YG-080")
class TestElevenLabsSTT:
    """REQ-YG-080: ElevenLabs STT integration tests."""

    @pytest.mark.asyncio
    async def test_transcribe_hello(self, api_key: str, hello_audio: bytes) -> None:
        """Transcribe 'Hello' audio fixture."""
        transcript = await self._transcribe_audio(api_key, hello_audio)
        assert "hello" in transcript.lower(), f"Expected 'hello' in: {transcript}"

    @pytest.mark.asyncio
    async def test_transcribe_claude(self, api_key: str, claude_audio: bytes) -> None:
        """Transcribe 'Claude' audio fixture."""
        transcript = await self._transcribe_audio(api_key, claude_audio)
        # Claude might be transcribed as "cloud" or similar
        assert any(
            word in transcript.lower() for word in ["claude", "cloud", "claud"]
        ), f"Expected 'claude' variant in: {transcript}"

    @pytest.mark.asyncio
    async def test_transcribe_great(self, api_key: str, great_audio: bytes) -> None:
        """Transcribe 'Great' audio fixture."""
        transcript = await self._transcribe_audio(api_key, great_audio)
        assert "great" in transcript.lower(), f"Expected 'great' in: {transcript}"

    async def _transcribe_audio(self, api_key: str, audio_data: bytes) -> str:
        """Send audio to ElevenLabs STT and return transcript.

        Uses the same SDK pattern as twilio_call.listen_and_transcribe().
        """
        from elevenlabs import ElevenLabs
        from elevenlabs.realtime.scribe import AudioFormat, CommitStrategy

        client = ElevenLabs(api_key=api_key)

        options = {
            "model_id": "scribe_v2_realtime",
            "audio_format": AudioFormat.ULAW_8000,
            "sample_rate": 8000,
            "commit_strategy": CommitStrategy.VAD,
            "min_speech_duration_ms": 50,  # Accept very short utterances
            "vad_threshold": 0.3,  # Lower threshold for speech detection
        }

        stt = await client.speech_to_text.realtime.connect(options)

        result_holder: list[str] = []
        done = asyncio.Event()

        def on_committed_transcript(data: dict) -> None:
            """Capture transcript when VAD commits."""
            transcript = data.get("text", "")
            if transcript.strip():
                result_holder.append(transcript)
                done.set()

        def on_error(data: dict) -> None:
            """Handle errors."""
            done.set()

        stt.on("committed_transcript", on_committed_transcript)
        stt.on("error", on_error)

        # Send audio in chunks (simulate streaming)
        chunk_size = 640  # 20ms @ 8kHz
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i : i + chunk_size]
            audio_b64 = base64.b64encode(chunk).decode("ascii")
            await stt.send({"audio_base_64": audio_b64})
            await asyncio.sleep(0.02)  # Pace like real-time

        # Send silence frames to trigger VAD end-of-speech
        silence = b"\xff" * chunk_size  # mulaw silence = 0xFF
        for _ in range(25):  # 500ms of silence
            audio_b64 = base64.b64encode(silence).decode("ascii")
            await stt.send({"audio_base_64": audio_b64})
            await asyncio.sleep(0.02)

        # Explicitly commit the transcript
        await stt.commit()

        # Wait for VAD to commit (with timeout)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(done.wait(), timeout=10.0)

        await stt.close()

        return result_holder[0] if result_holder else ""


@pytest.mark.integration
@pytest.mark.req("REQ-YG-080")
class TestSTTRoundTrip:
    """Test TTS -> STT round-trip accuracy."""

    @pytest.mark.asyncio
    async def test_all_fixtures_transcribe(self, api_key: str) -> None:
        """Verify all TTS fixtures transcribe correctly."""
        from elevenlabs import ElevenLabs
        from elevenlabs.realtime.scribe import AudioFormat, CommitStrategy

        fixtures = [
            ("hello.mulaw", "hello"),
            ("claude.mulaw", "claude"),
            ("great.mulaw", "great"),
        ]

        results = []
        for filename, expected in fixtures:
            audio_path = FIXTURES_DIR / filename
            if not audio_path.exists():
                pytest.skip(f"Fixture not found: {audio_path}")

            audio_data = audio_path.read_bytes()

            # Transcribe
            client = ElevenLabs(api_key=api_key)
            options = {
                "model_id": "scribe_v2_realtime",
                "audio_format": AudioFormat.ULAW_8000,
                "sample_rate": 8000,
                "commit_strategy": CommitStrategy.VAD,
            }
            stt = await client.speech_to_text.realtime.connect(options)

            result_holder: list[str] = []
            done = asyncio.Event()

            def on_transcript(
                data: dict,
                holder: list[str] = result_holder,
                event: asyncio.Event = done,
            ) -> None:
                text = data.get("text", "")
                if text.strip():
                    holder.append(text)
                    event.set()

            stt.on("committed_transcript", on_transcript)

            chunk_size = 640
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i : i + chunk_size]
                audio_b64 = base64.b64encode(chunk).decode("ascii")
                await stt.send({"audio_base_64": audio_b64})
                await asyncio.sleep(0.02)

            # Send silence to trigger VAD end-of-speech
            silence = b"\xff" * chunk_size
            for _ in range(25):
                audio_b64 = base64.b64encode(silence).decode("ascii")
                await stt.send({"audio_base_64": audio_b64})
                await asyncio.sleep(0.02)

            # Explicitly commit
            await stt.commit()

            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(done.wait(), timeout=10.0)

            await stt.close()

            transcript = result_holder[0] if result_holder else "(empty)"
            results.append((expected, transcript))

        # Report results
        print("\n=== STT Round-Trip Results ===")
        for expected, transcript in results:
            status = "✓" if expected.lower() in transcript.lower() else "✗"
            print(f"  {status} Expected: {expected!r}, Got: {transcript!r}")

        # Assert all passed
        failures = [
            (exp, got) for exp, got in results if exp.lower() not in got.lower()
        ]
        assert not failures, f"Transcription failures: {failures}"
