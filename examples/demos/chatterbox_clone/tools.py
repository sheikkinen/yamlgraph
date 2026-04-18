"""FR-236 Chatterbox voice cloning demo tools."""

from pathlib import Path


def synthesize_cloned_audio(
    state: dict,
    *,
    output_dir: Path | str = Path("outputs/chatterbox-clone"),
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
