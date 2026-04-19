"""FR-233/FR-237 Chatterbox TTS demo tools.

FR-237 consolidates chatterbox_clone into this module:
- synthesize_audio: multilingual TTS via ChatterboxMultilingualTTS (FR-233)
- synthesize_cloned_audio: voice cloning via ChatterboxTTS (FR-236, consolidated FR-237)
"""

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


def synthesize_cloned_audio(
    state: dict,
    *,
    output_dir: Path | str = Path("outputs/chatterbox"),
) -> dict:
    """Synthesize text to WAV using ChatterboxTTS with a reference voice clip.

    Uses ChatterboxTTS (chatterbox.tts) — not ChatterboxMultilingualTTS.
    The standard model supports audio_prompt_path for voice cloning;
    see upstream README: https://github.com/resemble-ai/chatterbox

    Args:
        state: Graph state containing 'text' and 'voice_prompt_path'.
        output_dir: Directory for WAV output files.

    Returns:
        Dict with 'audio_path' string.
    """
    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    model = ChatterboxTTS.from_pretrained(device=device)

    text = state["text"]
    voice_prompt_path = state["voice_prompt_path"]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.wav"

    wav = model.generate(text, audio_prompt_path=voice_prompt_path)
    ta.save(str(output_path), wav, model.sr)
    return {"audio_path": str(output_path)}
