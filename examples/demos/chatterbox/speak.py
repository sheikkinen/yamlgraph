"""CLI tool: synthesise text with an optional voice clone.

Two synthesis paths are available:

**English (default, ``--lang en``):**
    Uses ``ChatterboxTTS`` with a reference WAV clip (``--ref``).
    ``--ref`` is required for this path.

**Multilingual (``--lang <code>``):**
    Uses ``ChatterboxMultilingualTTS``.
    Supports 23 languages including ``fi``, ``sv``, ``de``, ``es``.
    Optional ``--ref`` enables zero-shot voice cloning in the target language.

Output is always written to ``outputs/chatterbox/speak.wav``.

Usage::

    # English voice cloning (requires --ref)
    python examples/demos/chatterbox/speak.py \\
        --ref examples/demos/chatterbox/source.wav "Hello world"

    # Finnish with default voice
    python examples/demos/chatterbox/speak.py \\
        --lang fi "Hei maailma"

    # Finnish with voice cloning
    python examples/demos/chatterbox/speak.py \\
        --lang fi --ref source.wav "Hei maailma"
"""

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Chatterbox TTS CLI (FR-239). "
            "English path (--lang en, default): ChatterboxTTS + --ref for voice cloning. "
            "Multilingual path (--lang fi/sv/de/es/…): ChatterboxMultilingualTTS, "
            "optional --ref for zero-shot voice cloning."
        )
    )
    parser.add_argument("text", help="Text to synthesise")
    parser.add_argument(
        "--ref",
        "-r",
        type=Path,
        default=None,
        help="Path to reference WAV for voice cloning (all languages)",
    )
    parser.add_argument(
        "--lang",
        "-l",
        default="en",
        help=(
            "Language code (default: en). "
            "en → ChatterboxTTS (requires --ref). "
            "Other codes (fi, sv, de, es, …) → ChatterboxMultilingualTTS "
            "(optional --ref for voice cloning)."
        ),
    )
    args = parser.parse_args()

    if args.lang == "en" and args.ref is None:
        parser.error("--ref is required for the English voice-cloning path (--lang en)")

    if args.ref is not None and not args.ref.exists():
        print(f"Error: reference file not found: {args.ref}", file=sys.stderr)
        sys.exit(1)

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
        from chatterbox.tts import ChatterboxTTS

        model = ChatterboxTTS.from_pretrained(device=device)
        wav = model.generate(args.text, audio_prompt_path=str(args.ref))
    else:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        model = ChatterboxMultilingualTTS.from_pretrained(device=device)
        ref = str(args.ref) if args.ref else None
        wav = model.generate(args.text, language_id=args.lang, audio_prompt_path=ref)

    ta.save(str(output_path), wav, model.sr)
    print(output_path)


if __name__ == "__main__":
    main()
