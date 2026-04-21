---

## 2026-04-19: Chaplain — Multilingual TTS CLI routing approved

FR-239 was approved after careful scoping of a multilingual TTS feature for the `speak.py` CLI. The design routes English (`--lang en`) through existing `ChatterboxTTS` with voice cloning, while non-English languages use `ChatterboxMultilingualTTS` without cloning support. A key decision: `--ref` becomes optional at parse-time, with runtime validation catching incompatible `--ref + non-en` combinations as clear errors. The implementation stays lean—one file, one flag, one conditional branch—reusing existing tools from `tools.py`. All 9 acceptance criteria are mechanically verifiable. The only gap: a diary entry is required by downstream `diary-gate` before merge, but that's process enforcement, not functionality.

**Seed:** How should the CLI handle graceful degradation when users request voice cloning for unsupported languages—should we auto-fall back to standard multilingual TTS, or is explicit error-and-fail the right UX for this constraint?
