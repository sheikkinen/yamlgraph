"""CLI tool: synthesise text with a reference voice clone.

Usage:
    python examples/demos/chatterbox/speak.py \\
        --ref examples/demos/chatterbox/source.wav "Hello world"

Note: Uses ChatterboxTTS (English-focused). Voice timbre transfers from the
reference clip, but pronunciation quality for non-English text may vary.
For true multilingual synthesis use graph.yaml with ChatterboxMultilingualTTS.
"""

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chatterbox voice-clone TTS CLI (FR-237)"
    )
    parser.add_argument("text", help="Text to synthesise")
    parser.add_argument(
        "--ref",
        "-r",
        required=True,
        type=Path,
        help="Path to reference WAV for voice cloning",
    )
    args = parser.parse_args()

    if not args.ref.exists():
        print(f"Error: reference file not found: {args.ref}", file=sys.stderr)
        sys.exit(1)

    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    model = ChatterboxTTS.from_pretrained(device=device)

    output_dir = Path("outputs/chatterbox")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "speak.wav"

    wav = model.generate(args.text, audio_prompt_path=str(args.ref))
    ta.save(str(output_path), wav, model.sr)
    print(output_path)


if __name__ == "__main__":
    main()
