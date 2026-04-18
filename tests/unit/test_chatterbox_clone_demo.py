"""FR-236 Chatterbox Voice Cloning demo – unit tests for synthesize_cloned_audio tool.

Tests the Python tool with mocked ChatterboxTTS to verify:
- Correct class used (ChatterboxTTS, not ChatterboxMultilingualTTS)
- generate() called with correct audio_prompt_path
- Output path follows naming convention
- State dict returned with audio_path
- Device selection follows cuda > mps > cpu priority chain
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_mock_torch = MagicMock()
_mock_torch.cuda.is_available.return_value = False
_mock_torch.backends.mps.is_available.return_value = False
_mock_ta = MagicMock()
_mock_chatterbox_tts = MagicMock()


@pytest.fixture(autouse=True)
def _mock_heavy_deps(monkeypatch):
    """Mock torch, torchaudio, chatterbox before each test."""
    monkeypatch.setitem(sys.modules, "torch", _mock_torch)
    monkeypatch.setitem(sys.modules, "torchaudio", _mock_ta)
    monkeypatch.setitem(sys.modules, "chatterbox", MagicMock())
    monkeypatch.setitem(sys.modules, "chatterbox.tts", _mock_chatterbox_tts)


@pytest.mark.req("REQ-YG-235")
class TestSynthesizeClonedAudio:
    """Test synthesize_cloned_audio tool with mocked TTS model."""

    def _make_state(
        self, text: str = "Hello from YAMLGraph", prompt_path: str = "/ref.wav"
    ) -> dict:
        return {"text": text, "voice_prompt_path": prompt_path}

    def test_uses_chatterbox_tts_not_multilingual(self, tmp_path):
        """Must instantiate ChatterboxTTS, not ChatterboxMultilingualTTS."""
        from examples.demos.chatterbox_clone.tools import synthesize_cloned_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        synthesize_cloned_audio(self._make_state(), output_dir=tmp_path / "out")

        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.assert_called_once()
        assert (
            not hasattr(_mock_chatterbox_tts, "ChatterboxMultilingualTTS")
            or not _mock_chatterbox_tts.ChatterboxMultilingualTTS.from_pretrained.called
        ), "Must not use ChatterboxMultilingualTTS"

    def test_generate_called_with_audio_prompt_path(self, tmp_path):
        """generate() must receive audio_prompt_path from state['voice_prompt_path']."""
        from examples.demos.chatterbox_clone.tools import synthesize_cloned_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        state = self._make_state(text="Hello", prompt_path="/voice/ref.wav")
        synthesize_cloned_audio(state, output_dir=tmp_path / "out")

        mock_model.generate.assert_called_once_with(
            "Hello", audio_prompt_path="/voice/ref.wav"
        )

    def test_returns_audio_path_key(self, tmp_path):
        """Result dict must contain 'audio_path' string."""
        from examples.demos.chatterbox_clone.tools import synthesize_cloned_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        result = synthesize_cloned_audio(
            self._make_state(), output_dir=tmp_path / "out"
        )

        assert "audio_path" in result
        assert result["audio_path"].endswith("output.wav")

    def test_output_saved_via_torchaudio(self, tmp_path):
        """Output WAV must be saved with torchaudio.save."""
        from examples.demos.chatterbox_clone.tools import synthesize_cloned_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        wav_tensor = MagicMock()
        mock_model.generate.return_value = wav_tensor
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        _mock_ta.save.reset_mock()
        out = tmp_path / "out"
        synthesize_cloned_audio(self._make_state(), output_dir=out)

        _mock_ta.save.assert_called_once_with(
            str(out / "output.wav"), wav_tensor, 24000
        )

    def test_creates_output_directory(self, tmp_path):
        """Output directory must be created if absent."""
        from examples.demos.chatterbox_clone.tools import synthesize_cloned_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        out = tmp_path / "nested" / "deep" / "out"
        synthesize_cloned_audio(self._make_state(), output_dir=out)

        assert out.exists()

    def test_uses_cuda_when_available(self, tmp_path):
        """Should select cuda when torch.cuda.is_available() returns True."""
        from examples.demos.chatterbox_clone.tools import synthesize_cloned_audio

        _mock_torch.cuda.is_available.return_value = True
        _mock_torch.backends.mps.is_available.return_value = False
        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.reset_mock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        synthesize_cloned_audio(self._make_state(), output_dir=tmp_path / "out")

        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.assert_called_once_with(
            device="cuda"
        )
        _mock_torch.cuda.is_available.return_value = False

    def test_uses_mps_when_cuda_unavailable(self, tmp_path):
        """Should select mps when CUDA absent but MPS available (Apple Silicon)."""
        from examples.demos.chatterbox_clone.tools import synthesize_cloned_audio

        _mock_torch.cuda.is_available.return_value = False
        _mock_torch.backends.mps.is_available.return_value = True
        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.reset_mock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        synthesize_cloned_audio(self._make_state(), output_dir=tmp_path / "out")

        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.assert_called_once_with(
            device="mps"
        )
        _mock_torch.backends.mps.is_available.return_value = False

    def test_falls_back_to_cpu(self, tmp_path):
        """Should fall back to cpu when neither CUDA nor MPS available."""
        from examples.demos.chatterbox_clone.tools import synthesize_cloned_audio

        _mock_torch.cuda.is_available.return_value = False
        _mock_torch.backends.mps.is_available.return_value = False
        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.reset_mock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        synthesize_cloned_audio(self._make_state(), output_dir=tmp_path / "out")

        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.assert_called_once_with(
            device="cpu"
        )


@pytest.mark.req("REQ-YG-235")
class TestChatterboxCloneDemoStructure:
    """Test that demo files exist and are valid."""

    DEMO_DIR = (
        Path(__file__).parent.parent.parent / "examples" / "demos" / "chatterbox_clone"
    )

    def test_graph_yaml_exists(self):
        assert (self.DEMO_DIR / "graph.yaml").exists()

    def test_tools_py_exists(self):
        assert (self.DEMO_DIR / "tools.py").exists()

    def test_readme_exists(self):
        assert (self.DEMO_DIR / "README.md").exists()

    def test_demo_output_log_exists(self):
        assert (self.DEMO_DIR / "demo-output.log").exists()

    def test_graph_yaml_valid(self):
        import yaml

        config = yaml.safe_load((self.DEMO_DIR / "graph.yaml").read_text())
        assert config["name"] == "chatterbox-voice-clone"
        assert "synthesize" in config["nodes"]
        assert config["nodes"]["synthesize"]["type"] == "python"

    def test_graph_state_has_required_keys(self):
        import yaml

        config = yaml.safe_load((self.DEMO_DIR / "graph.yaml").read_text())
        assert "text" in config["state"]
        assert "voice_prompt_path" in config["state"]

    def test_graph_loads(self):
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(str(self.DEMO_DIR / "graph.yaml"))
        assert config is not None
