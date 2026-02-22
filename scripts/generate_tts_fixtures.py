#!/usr/bin/env python3
"""Generate TTS audio fixtures for integration tests.

Creates mulaw 8kHz audio files matching Twilio's format.
Requires ELEVENLABS_API_KEY environment variable.
"""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# Load from project .env if exists
load_dotenv(Path(__file__).parent.parent / "projects/outcaller/.env")

FIXTURES_DIR = Path(__file__).parent.parent / "tests/fixtures/audio"
# Longer phrases to ensure VAD detects speech reliably
PHRASES = [
    ("hello", "Hello there, how are you?"),
    ("claude", "My name is Claude, nice to meet you."),
    ("great", "That sounds great, thank you very much."),
]


def generate_fixture(
    client: ElevenLabs, name: str, phrase: str, output_path: Path
) -> None:
    """Generate mulaw 8kHz audio file for a phrase."""
    print(f"Generating: {name} ({phrase}) -> {output_path.name}")

    # Get MP3 from ElevenLabs
    audio_stream = client.text_to_speech.convert(
        voice_id="JBFqnCBsd6RMkjVDRZzb",  # George voice
        model_id="eleven_flash_v2_5",
        text=phrase,
        output_format="mp3_22050_32",
    )

    # Collect MP3 chunks
    mp3_data = b"".join(audio_stream)

    # Convert to mulaw 8kHz via ffmpeg
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            "pipe:0",
            "-f",
            "mulaw",
            "-ar",
            "8000",
            "-ac",
            "1",
            str(output_path),
        ],
        input=mp3_data,
        capture_output=True,
    )

    if proc.returncode != 0:
        print(f"ffmpeg error: {proc.stderr.decode()}", file=sys.stderr)
        sys.exit(1)

    print(f"  Created: {output_path} ({output_path.stat().st_size} bytes)")


def main() -> None:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    client = ElevenLabs(api_key=api_key)

    for name, phrase in PHRASES:
        output_path = FIXTURES_DIR / f"{name}.mulaw"
        generate_fixture(client, name, phrase, output_path)

    print(f"\nGenerated {len(PHRASES)} fixtures in {FIXTURES_DIR}")


if __name__ == "__main__":
    main()
