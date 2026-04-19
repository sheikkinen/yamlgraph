"""CLI tool: synthesise text with an optional voice clone or multilingual model.

Two synthesis paths are available:

**English / Voice Cloning (default, ``--lang en``):**
    Uses ``ChatterboxTTS`` with a reference WAV clip (``--ref``).
    Voice timbre transfers from the reference clip.
    ``--ref`` is required for this path.

**Multilingual (``--lang <code>``):**
    Uses ``ChatterboxMultilingualTTS``.  No reference audio is accepted.
    Known-good language codes: ``fi``, ``sv``, ``de``, ``es``.
    ``--ref`` is incompatible with this path.

Output is always written to ``outputs/chatterbox/speak.wav``.

Usage::

    # English voice cloning (unchanged)
    python examples/demos/chatterbox/speak.py \\
        --ref examples/demos/chatterbox/source.wav "Hello world"

    # Finnish via multilingual model
    python examples/demos/chatterbox/speak.py \\
        --lang fi "Hei maailma"

    # Explicit English (same as omitting --lang)
    python examples/demos/chatterbox/speak.py \\
        --lang en --ref source.wav "Hello world"
"""

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Chatterbox TTS CLI (FR-239). "
            "English path (--lang en, default): ChatterboxTTS + --ref for voice cloning. "
            "Multilingual path (--lang fi/sv/de/es/…): ChatterboxMultilingualTTS, no --ref."
        )
    )
    parser.add_argument("text", help="Text to synthesise")
    parser.add_argument(
        "--ref",
        "-r",
        type=Path,
        default=None,
        help="Path to reference WAV for voice cloning (English path only)",
    )
    parser.add_argument(
        "--lang",
        "-l",
        default="en",
        help=(
            "Language code (default: en). "
            "en → ChatterboxTTS (voice cloning, requires --ref). "
            "Other codes (fi, sv, de, es, …) → ChatterboxMultilingualTTS (no --ref)."
        ),
    )
    args = parser.parse_args()

    if args.lang != "en" and args.ref is not None:
        parser.error("--ref is only supported with --lang en (voice-cloning path)")

    if args.lang == "en" and args.ref is None:
        parser.error("--ref is required for the English voice-cloning path (--lang en)")

    output_dir = Path("outputs/chatterbox")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "speak.wav"

    import torch
    import torchaudio as ta

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )

    if args.lang == "en":
        if not args.ref.exists():
            print(f"Error: reference file not found: {args.ref}", file=sys.stderr)
            sys.exit(1)

        from chatterbox.tts import ChatterboxTTS

        model = ChatterboxTTS.from_pretrained(device=device)
        wav = model.generate(args.text, audio_prompt_path=str(args.ref))
    else:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        model = ChatterboxMultilingualTTS.from_pretrained(device=device)
        wav = model.generate(args.text, language_id=args.lang)

    ta.save(str(output_path), wav, model.sr)
    print(output_path)


if __name__ == "__main__":
    main()
