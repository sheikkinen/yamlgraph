"""FR-233/FR-237 Chatterbox TTS demo – unit tests.

Tests synthesize_audio (FR-233) and synthesize_cloned_audio (FR-237 consolidation)
tools with mocked Chatterbox models, plus TestSpeakCLI for the speak.py CLI tool.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Create mock modules so tools.py can be imported without torch/chatterbox
_mock_torch = MagicMock()
_mock_torch.cuda.is_available.return_value = False
_mock_torch.backends = MagicMock()
_mock_torch.backends.mps = MagicMock()
_mock_torch.backends.mps.is_available.return_value = False
_mock_ta = MagicMock()
_mock_chatterbox_mtl = MagicMock()
_mock_chatterbox_tts = MagicMock()


@pytest.fixture(autouse=True)
def _mock_heavy_deps(monkeypatch):
    """Mock torch, torchaudio, chatterbox before each test."""
    monkeypatch.setitem(sys.modules, "torch", _mock_torch)
    monkeypatch.setitem(sys.modules, "torchaudio", _mock_ta)
    monkeypatch.setitem(sys.modules, "chatterbox", MagicMock())
    monkeypatch.setitem(sys.modules, "chatterbox.mtl_tts", _mock_chatterbox_mtl)
    monkeypatch.setitem(sys.modules, "chatterbox.tts", _mock_chatterbox_tts)


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

    def test_clone_yaml_exists(self):
        assert (self.DEMO_DIR / "clone.yaml").exists()

    def test_clone_yaml_valid(self):
        import yaml

        config = yaml.safe_load((self.DEMO_DIR / "clone.yaml").read_text())
        assert config["name"] == "chatterbox-voice-clone"
        assert "synthesize" in config["nodes"]
        assert config["nodes"]["synthesize"]["type"] == "python"

    def test_clone_yaml_module_points_to_chatterbox(self):
        import yaml

        config = yaml.safe_load((self.DEMO_DIR / "clone.yaml").read_text())
        tool_key = list(config["tools"].keys())[0]
        assert config["tools"][tool_key]["module"] == "examples.demos.chatterbox.tools"

    def test_speak_py_exists(self):
        assert (self.DEMO_DIR / "speak.py").exists()

    def test_speak_py_has_no_lang_argument(self):
        source = (self.DEMO_DIR / "speak.py").read_text()
        assert "--lang" not in source

    def test_chatterbox_clone_folder_does_not_exist(self):
        clone_dir = self.DEMO_DIR.parent / "chatterbox_clone"
        assert not clone_dir.exists(), "chatterbox_clone/ should have been deleted"


@pytest.mark.req("REQ-YG-235")
class TestSynthesizeClonedAudio:
    """Test synthesize_cloned_audio tool (now in chatterbox/tools.py — FR-237)."""

    def _make_state(
        self, text: str = "Hello from YAMLGraph", prompt_path: str = "/ref.wav"
    ) -> dict:
        return {"text": text, "voice_prompt_path": prompt_path}

    def test_uses_chatterbox_tts_not_multilingual(self, tmp_path):
        """Must instantiate ChatterboxTTS, not ChatterboxMultilingualTTS."""
        from examples.demos.chatterbox.tools import synthesize_cloned_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        synthesize_cloned_audio(self._make_state(), output_dir=tmp_path / "out")

        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.assert_called_once()

    def test_generate_called_with_audio_prompt_path(self, tmp_path):
        """generate() must receive audio_prompt_path from state['voice_prompt_path']."""
        from examples.demos.chatterbox.tools import synthesize_cloned_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        state = self._make_state(text="Hello", prompt_path="/voice/ref.wav")
        synthesize_cloned_audio(state, output_dir=tmp_path / "out")

        mock_model.generate.assert_called_once_with(
            "Hello", audio_prompt_path="/voice/ref.wav"
        )

    def test_generate_called_without_language_id(self, tmp_path):
        """generate() must NOT receive language_id kwarg."""
        from examples.demos.chatterbox.tools import synthesize_cloned_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        synthesize_cloned_audio(self._make_state(), output_dir=tmp_path / "out")

        call_kwargs = mock_model.generate.call_args[1]
        assert "language_id" not in call_kwargs

    def test_returns_audio_path_key(self, tmp_path):
        """Result dict must contain 'audio_path' string."""
        from examples.demos.chatterbox.tools import synthesize_cloned_audio

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
        from examples.demos.chatterbox.tools import synthesize_cloned_audio

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
        from examples.demos.chatterbox.tools import synthesize_cloned_audio

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        out = tmp_path / "nested" / "deep" / "out"
        synthesize_cloned_audio(self._make_state(), output_dir=out)

        assert out.exists()

    def test_uses_cuda_when_available(self, tmp_path):
        """Should select cuda when torch.cuda.is_available() returns True."""
        from examples.demos.chatterbox.tools import synthesize_cloned_audio

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
        """Should select mps when CUDA absent but MPS available."""
        from examples.demos.chatterbox.tools import synthesize_cloned_audio

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
        from examples.demos.chatterbox.tools import synthesize_cloned_audio

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


@pytest.mark.req("REQ-YG-238")
class TestSpeakCLI:
    """Test speak.py CLI tool (FR-237)."""

    SPEAK_PY = (
        Path(__file__).parent.parent.parent
        / "examples"
        / "demos"
        / "chatterbox"
        / "speak.py"
    )

    def _run_main(self, argv: list[str]):
        """Import and call speak.main() with patched sys.argv."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("speak", self.SPEAK_PY)
        module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module

    def test_exits_with_code_1_when_ref_not_found(self, tmp_path):
        """speak.py must exit 1 when --ref path does not exist."""
        import subprocess
        import sys

        result = subprocess.run(
            [
                sys.executable,
                str(self.SPEAK_PY),
                "--ref",
                str(tmp_path / "nonexistent.wav"),
                "Hello",
            ],
            capture_output=True,
            text=True,
            env={**__import__("os").environ},
        )
        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_generate_called_without_language_id(self, tmp_path, monkeypatch):
        """model.generate() must be called without language_id kwarg."""
        ref_wav = tmp_path / "ref.wav"
        ref_wav.write_bytes(b"RIFF")

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_wav = MagicMock()
        mock_model.generate.return_value = mock_wav
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        import sys as _sys

        monkeypatch.setattr(
            _sys, "argv", ["speak.py", "--ref", str(ref_wav), "Hello world"]
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("speak", self.SPEAK_PY)
        module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        monkeypatch.chdir(tmp_path)
        with patch("builtins.print"):
            module.main()

        call_kwargs = mock_model.generate.call_args[1]
        assert "language_id" not in call_kwargs

    def test_generate_called_with_audio_prompt_path(self, tmp_path, monkeypatch):
        """model.generate() must receive audio_prompt_path matching --ref."""
        ref_wav = tmp_path / "ref.wav"
        ref_wav.write_bytes(b"RIFF")

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model

        import sys as _sys

        monkeypatch.setattr(
            _sys, "argv", ["speak.py", "--ref", str(ref_wav), "Hello world"]
        )
        monkeypatch.chdir(tmp_path)

        import importlib.util

        spec = importlib.util.spec_from_file_location("speak", self.SPEAK_PY)
        module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with patch("builtins.print"):
            module.main()

        mock_model.generate.assert_called_once_with(
            "Hello world", audio_prompt_path=str(ref_wav)
        )

    def test_output_written_to_outputs_chatterbox_speak_wav(
        self, tmp_path, monkeypatch
    ):
        """Output WAV must be written to outputs/chatterbox/speak.wav."""
        ref_wav = tmp_path / "ref.wav"
        ref_wav.write_bytes(b"RIFF")

        mock_model = MagicMock()
        mock_model.sr = 24000
        mock_model.generate.return_value = MagicMock()
        _mock_chatterbox_tts.ChatterboxTTS.from_pretrained.return_value = mock_model
        _mock_ta.save.reset_mock()

        import sys as _sys

        monkeypatch.setattr(_sys, "argv", ["speak.py", "--ref", str(ref_wav), "Test"])
        monkeypatch.chdir(tmp_path)

        import importlib.util

        spec = importlib.util.spec_from_file_location("speak", self.SPEAK_PY)
        module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with patch("builtins.print"):
            module.main()

        save_path = _mock_ta.save.call_args[0][0]
        assert save_path.endswith("outputs/chatterbox/speak.wav")
