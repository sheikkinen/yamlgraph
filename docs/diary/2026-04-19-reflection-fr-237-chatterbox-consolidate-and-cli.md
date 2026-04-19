# Diary: FR-237 Chatterbox Consolidate and CLI

**Date:** 2026-04-19
**FR:** FR-237-chatterbox-consolidate-and-cli

## What Was Built

Consolidated `chatterbox_clone/` (FR-236) into `chatterbox/` (FR-233) and added a standalone `speak.py` CLI tool. The merge was surgical: `synthesize_cloned_audio` moved into `chatterbox/tools.py` alongside `synthesize_audio`; `graph.yaml` clone was migrated as `clone.yaml` with the module path updated; `chatterbox_clone/` deleted entirely.

## Cognitive Process

**Trap avoided — false_duplicate:** The two `tools.py` files were syntactically similar (both import torch, both call `model.generate`), but semantically distinct (`ChatterboxMultilingualTTS` vs `ChatterboxTTS`, `language_id` kwarg vs `audio_prompt_path`). Merging required preserving both functions completely rather than collapsing them.

**Trap avoided — intent_drift:** The FR explicitly forbids `--lang` in `speak.py` (Judge Issue 2, option b resolution). The test `test_speak_py_has_no_lang_argument` guards this at the source level — checking the file text, not just runtime behavior.

**Pattern reinforced — normalize at the boundary:** The `default output_dir` changed from `outputs/chatterbox-clone` to `outputs/chatterbox` in `synthesize_cloned_audio`. This is a boundary normalization — all output lands in one directory, making it trivially discoverable.

**TDD discipline held:** RED phase confirmed 19 failures before a single production line changed. The test for `test_chatterbox_clone_folder_does_not_exist` was the last to turn green, serving as the forcing function to actually delete the old folder (not just copy).

## Insights

The `speak.py` CLI is a rare case where the YAMLGraph framework is intentionally absent from the implementation. The FR correctly identifies that `graph.yaml` already covers the tool-node use case; `speak.py` exists for users who want one command without a YAML runner. This avoids the `framework_costume` trap — not every workflow needs a graph.

The `TestSpeakCLI` tests use `importlib.util.spec_from_file_location` to load `speak.py` as a module, which avoids `sys.path` manipulation and lets `monkeypatch` intercept `sys.argv` and `chdir` cleanly.

## Seed

If a user has `speak.py` but no `source.wav`, what is the smallest demo path? Could a future FR add a `--generate-ref` flag or a bundled 3-second silence wav that at minimum proves the CLI works end-to-end without a real voice clip?
