"""FR-233 Chatterbox TTS demo tools."""

from pathlib import Path


def synthesize_audio(
    state: dict,
    *,
    output_dir: Path | str = Path("outputs/chatterbox"),
) -> dict:
    """Synthesize translations to WAV files using Chatterbox Multilingual.

    Args:
        state: Graph state containing translations list.
        output_dir: Directory for WAV output files.

    Returns:
        Dict with audio_paths list.
    """
    import torch
    import torchaudio as ta
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    translations = state.get("translations", [])
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxMultilingualTTS.from_pretrained(device=device)

    audio_paths: list[str] = []
    for item in translations:
        lang = item["lang"]
        text = item["translation"]
        wav = model.generate(text, language_id=lang)
        path = output_dir / f"{lang}.wav"
        ta.save(str(path), wav, model.sr)
        audio_paths.append(str(path))

    return {"audio_paths": audio_paths}
