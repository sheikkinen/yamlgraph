"""FR-233 Chatterbox TTS demo – unit tests for synthesize_audio tool.

Tests the Python tool with mocked Chatterbox model to verify:
- Correct number of WAV files produced
- Output paths follow naming convention
- State dict returned with audio_paths
- Empty translations handled
- Model device detection
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Create mock modules so tools.py can be imported without torch/chatterbox
_mock_torch = MagicMock()
_mock_torch.cuda.is_available.return_value = False
_mock_ta = MagicMock()
_mock_chatterbox_mtl = MagicMock()


@pytest.fixture(autouse=True)
def _mock_heavy_deps(monkeypatch):
    """Mock torch, torchaudio, chatterbox before each test."""
    monkeypatch.setitem(sys.modules, "torch", _mock_torch)
    monkeypatch.setitem(sys.modules, "torchaudio", _mock_ta)
    monkeypatch.setitem(sys.modules, "chatterbox", MagicMock())
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", _mock_chatterbox_mtl)


@pytest.mark.req("REQ-YG-234")
class TestSynthesizeAudio:
    """Test synthesize_audio tool with mocked TTS model."""

    def _make_state(self, translations: list[dict]) -> dict:
        return {"translations": translations}

    def _sample_translations(self) -> list[dict]:
        return [
            {"lang": "en", "translation": "Hello, this is a test."},
            {"lang": "es", "translation": "Hola, esto es una prueba."},
            {"lang": "fi", "translation": "Hei, tämä on testi."},
            {"lang": "sv", "translation": "Hej, detta är ett test."},
            {"lang": "de", "translation": "Hallo, das ist ein Test."},
        ]

    def test_produces_five_wav_files(self, tmp_path):
        """Each translation should produce a WAV file."""
        from examples.demos.chatterbox.tools import synthesize_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.return_value = (
            mock_model
        )

        state = self._make_state(self._sample_translations())
        result = synthesize_audio(state, output_dir=tmp_path / "out")

        assert len(result["audio_paths"]) == 5
        assert mock_model.generate.call_count == 5

    def test_output_paths_follow_naming_convention(self, tmp_path):
        """Output files should be named {lang}.wav."""
        from examples.demos.chatterbox.tools import synthesize_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.return_value = (
            mock_model
        )

        state = self._make_state(self._sample_translations())
        result = synthesize_audio(state, output_dir=tmp_path / "out")

        paths = result["audio_paths"]
        for lang in ("en", "es", "fi", "sv", "de"):
            expected = str(tmp_path / "out" / f"{lang}.wav")
            assert expected in paths, f"Missing {lang}.wav in {paths}"

    def test_calls_torchaudio_save(self, tmp_path):
        """Each file should be saved via torchaudio.save."""
        from examples.demos.chatterbox.tools import synthesize_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        wav_tensor = MagicMock()
        mock_model.generate.return_value = wav_tensor
        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.return_value = (
            mock_model
        )

        state = self._make_state([{"lang": "en", "translation": "Hi"}])
        _mock_ta.save.reset_mock()
        synthesize_audio(state, output_dir=tmp_path / "out")

        _mock_ta.save.assert_called_once_with(
            str(tmp_path / "out" / "en.wav"), wav_tensor, 24000
        )

    def test_empty_translations_returns_empty_list(self, tmp_path):
        """Empty translations should return empty audio_paths."""
        from examples.demos.chatterbox.tools import synthesize_audio

        mock_model = MagicMock()
        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.return_value = (
            mock_model
        )

        state = self._make_state([])
        result = synthesize_audio(state, output_dir=tmp_path / "out")

        assert result["audio_paths"] == []
        mock_model.generate.assert_not_called()

    def test_creates_output_directory(self, tmp_path):
        """Output directory should be created if it doesn't exist."""
        from examples.demos.chatterbox.tools import synthesize_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.return_value = (
            mock_model
        )

        out = tmp_path / "nested" / "out"
        state = self._make_state([{"lang": "en", "translation": "Test"}])
        synthesize_audio(state, output_dir=out)

        assert out.exists()

    def test_uses_cuda_when_available(self, tmp_path):
        """Should use CUDA when available."""
        from examples.demos.chatterbox.tools import synthesize_audio

        _mock_torch.cuda.is_available.return_value = True
        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.reset_mock()
        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.return_value = (
            mock_model
        )

        state = self._make_state([{"lang": "en", "translation": "Test"}])
        synthesize_audio(state, output_dir=tmp_path / "out")

        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.assert_called_once_with(
            device="cuda"
        )
        _mock_torch.cuda.is_available.return_value = False

    def test_falls_back_to_cpu(self, tmp_path):
        """Should fall back to CPU when CUDA not available."""
        from examples.demos.chatterbox.tools import synthesize_audio

        _mock_torch.cuda.is_available.return_value = False
        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.reset_mock()
        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.return_value = (
            mock_model
        )

        state = self._make_state([{"lang": "en", "translation": "Test"}])
        synthesize_audio(state, output_dir=tmp_path / "out")

        _mock_chatterbox_mtl.ChatterboxMultilingualTTS.from_pretrained.assert_called_once_with(
            device="cpu"
        )


@pytest.mark.req("REQ-YG-234")
class TestChatterboxDemoStructure:
    """Test that demo files exist and are valid."""

    DEMO_DIR = Path(__file__).parent.parent.parent / "examples" / "demos" / "chatterbox"

    def test_graph_yaml_exists(self):
        assert (self.DEMO_DIR / "graph.yaml").exists()

    def test_tools_py_exists(self):
        assert (self.DEMO_DIR / "tools.py").exists()

    def test_prompt_exists(self):
        assert (self.DEMO_DIR / "prompts" / "translate.yaml").exists()

    def test_readme_exists(self):
        assert (self.DEMO_DIR / "README.md").exists()

    def test_graph_yaml_valid(self):
        import yaml

        config = yaml.safe_load((self.DEMO_DIR / "graph.yaml").read_text())
        assert config["name"] == "chatterbox-tts"
        assert "generate" in config["nodes"]
        assert "synthesize" in config["nodes"]
        assert config["nodes"]["generate"]["type"] == "map"

    def test_graph_loads(self):
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(str(self.DEMO_DIR / "graph.yaml"))
        assert config is not None

    def test_prompt_has_schema(self):
        import yaml

        prompt = yaml.safe_load(
            (self.DEMO_DIR / "prompts" / "translate.yaml").read_text()
        )
        assert "schema" in prompt
        assert prompt["schema"]["name"] == "Translation"
        fields = prompt["schema"]["fields"]
        assert "lang" in fields
        assert "translation" in fields
