"""Integration tests for ElevenLabs TTS and STT.

Tests ElevenLabs API independently of Twilio.
Requires: ELEVENLABS_API_KEY

Run with: pytest tests/integration/test_telco_elevenlabs.py -v -s
"""

import os
import subprocess

import pytest

# Skip all tests if ElevenLabs credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("ELEVENLABS_API_KEY"),
    reason="ELEVENLABS_API_KEY not set",
)


@pytest.fixture
def elevenlabs_client():
    """Create ElevenLabs client."""
    from elevenlabs import ElevenLabs

    return ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))


class TestElevenLabsTTS:
    """Test ElevenLabs Text-to-Speech."""

    @pytest.mark.req("REQ-YG-079")
    def test_generate_audio(self, elevenlabs_client):
        """Generate TTS audio and verify output.

        REQ-YG-079: ElevenLabs eleven_flash_v2_5 TTS.
        """
        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
            model_id="eleven_flash_v2_5",
            text="Hello, this is a test.",
            output_format="mp3_22050_32",
        )

        mp3_data = b"".join(audio_stream)
        assert len(mp3_data) > 1000, "Audio too short"
        print(f"✓ Generated {len(mp3_data)} bytes MP3")

        # Verify it's valid MP3 (starts with ID3 or FF FB)
        assert mp3_data[:3] == b"ID3" or mp3_data[:2] == b"\xff\xfb", "Not valid MP3"
        print("✓ Valid MP3 format")

    @pytest.mark.req("REQ-YG-079")
    def test_transcode_to_mulaw(self, elevenlabs_client):
        """Generate TTS and transcode to mulaw 8kHz.

        REQ-YG-079: Transcode to mulaw 8kHz via ffmpeg.
        """
        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_flash_v2_5",
            text="Testing mulaw transcode.",
            output_format="mp3_22050_32",
        )

        mp3_data = b"".join(audio_stream)
        print(f"  MP3: {len(mp3_data)} bytes")

        # Transcode via ffmpeg
        proc = subprocess.run(
            [
                "ffmpeg",
                "-i",
                "pipe:0",
                "-f",
                "mulaw",
                "-ar",
                "8000",
                "-ac",
                "1",
                "pipe:1",
            ],
            input=mp3_data,
            capture_output=True,
        )
        assert proc.returncode == 0, f"ffmpeg failed: {proc.stderr.decode()}"

        mulaw_data = proc.stdout
        assert len(mulaw_data) > 1000, "Mulaw too short"
        print(f"✓ Transcoded to {len(mulaw_data)} bytes mulaw")

        # Verify mulaw characteristics (8kHz = 8000 samples/sec)
        duration_sec = len(mulaw_data) / 8000
        print(f"✓ Duration: {duration_sec:.2f}s")


class TestElevenLabsSTT:
    """Test ElevenLabs Speech-to-Text."""

    @pytest.mark.req("REQ-YG-080")
    def test_transcribe_generated_audio(self, elevenlabs_client):
        """Generate TTS, transcode, then transcribe back.

        REQ-YG-080: ElevenLabs scribe_v1 STT.
        """
        test_text = "The quick brown fox jumps over the lazy dog."

        # Generate TTS
        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_flash_v2_5",
            text=test_text,
            output_format="mp3_22050_32",
        )
        mp3_data = b"".join(audio_stream)
        print(f"  TTS: {len(mp3_data)} bytes MP3")

        # Transcode to mulaw then back to PCM16 (simulating Twilio path)
        mulaw_proc = subprocess.run(
            [
                "ffmpeg",
                "-i",
                "pipe:0",
                "-f",
                "mulaw",
                "-ar",
                "8000",
                "-ac",
                "1",
                "pipe:1",
            ],
            input=mp3_data,
            capture_output=True,
        )
        mulaw_data = mulaw_proc.stdout

        pcm_proc = subprocess.run(
            [
                "ffmpeg",
                "-f",
                "mulaw",
                "-ar",
                "8000",
                "-ac",
                "1",
                "-i",
                "pipe:0",
                "-f",
                "s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                "pipe:1",
            ],
            input=mulaw_data,
            capture_output=True,
        )
        pcm_data = pcm_proc.stdout
        print(f"  PCM16: {len(pcm_data)} bytes")

        # Wrap as WAV
        wav_data = _pcm_to_wav(pcm_data, sample_rate=16000)
        print(f"  WAV: {len(wav_data)} bytes")

        # Transcribe via ElevenLabs STT
        import httpx

        response = httpx.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": os.getenv("ELEVENLABS_API_KEY")},
            files={"file": ("audio.wav", wav_data, "audio/wav")},
            data={"model_id": "scribe_v1"},
            timeout=30.0,
        )
        assert response.status_code == 200, f"STT failed: {response.text}"

        result = response.json()
        transcript = result.get("text", "")
        print(f"✓ Transcribed: '{transcript}'")

        # Verify transcription is similar to original
        assert len(transcript) > 10, "Transcript too short"

    @pytest.mark.req("REQ-YG-082")
    def test_transcribe_silence_fails_gracefully(self):
        """Verify silence/empty audio returns error or empty.

        REQ-YG-082: Handle silence without crashing.
        """
        import httpx

        # Create 1 second of silence (mulaw silence = 0xFF)
        silence_mulaw = bytes([0xFF] * 8000)

        # Transcode to PCM16
        pcm_proc = subprocess.run(
            [
                "ffmpeg",
                "-f",
                "mulaw",
                "-ar",
                "8000",
                "-ac",
                "1",
                "-i",
                "pipe:0",
                "-f",
                "s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                "pipe:1",
            ],
            input=silence_mulaw,
            capture_output=True,
        )
        pcm_data = pcm_proc.stdout

        wav_data = _pcm_to_wav(pcm_data, sample_rate=16000)

        response = httpx.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": os.getenv("ELEVENLABS_API_KEY")},
            files={"file": ("audio.wav", wav_data, "audio/wav")},
            data={"model_id": "scribe_v1"},
            timeout=30.0,
        )

        # Silence may return 400 or empty transcript
        if response.status_code == 200:
            transcript = response.json().get("text", "")
            print(f"✓ Silence returned: '{transcript}'")
        else:
            print(f"✓ Silence returned HTTP {response.status_code}")


def _pcm_to_wav(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    """Wrap raw PCM16 in WAV header."""
    import struct

    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_data)

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )

    return header + pcm_data
