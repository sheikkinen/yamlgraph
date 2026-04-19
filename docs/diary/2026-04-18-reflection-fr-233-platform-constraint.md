# Diary: FR-233 Chatterbox TTS — Platform Constraint Discovery

**Date:** 2026-04-18
**FR:** FR-233

## Cognitive Process

After merging FR-233 (Chatterbox TTS demo), post-merge verification on an Intel Mac (x86_64) revealed that the demo cannot run on this platform. The `chatterbox-tts` package requires `torch==2.6.0`, which has no macOS Intel wheel — PyTorch dropped Intel Mac support after 2.2.x.

## Trap: Assumption of Universal Installability

The FR was written and CI'd on a supported platform. The demo-output.log was produced there. The Intel Mac failure only surfaced during local verification — a platform assumption baked silently into the dependency chain.

## Insight

**Dependency platform constraints are boundary conditions.** A package that installs everywhere in CI may silently fail on a developer's machine. The failure manifests downstream (demo crashes) rather than at install time (no `torch==2.6.0` wheel error — it falls back to incompatible version), making it harder to diagnose.

## Heuristic

When adding a heavy ML dependency, explicitly verify and document minimum platform requirements at FR time — before implementation. Platform constraints belong in the README and FR, not discovered post-merge.

## Seed

Should `pyproject.toml` extras include platform markers (e.g., `chatterbox-tts; sys_platform != "darwin" or platform_machine == "arm64"`) to fail fast with a clear message on unsupported platforms rather than installing an incompatible torch version silently?
