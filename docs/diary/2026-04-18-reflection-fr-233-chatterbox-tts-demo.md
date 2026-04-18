# Diary: FR-233 Chatterbox TTS Demo

**Date:** 2026-04-18
**FR:** FR-233
**Type:** Reflection

## Cognitive Process

The task was to build a demo producing binary artifacts (WAV audio) from a YAMLGraph pipeline — a first for the framework which has only generated text outputs.

## Trap: Framework Costume

Initial instinct was to embed TTS logic into the graph YAML as a custom node type. But Chatterbox TTS is a heavy ML model with CUDA detection, model loading, and binary I/O — none of which belong in the declarative graph layer. The correct boundary: graph handles LLM translation (text→text), a Python tool handles synthesis (text→WAV). This keeps the three-layer pattern clean.

## Insight: Binary Artifacts as Side Effects

Audio files are side effects, not state. The `synthesize_audio` tool writes to disk and returns a path string — the graph state only carries the path, never the binary payload. This is the correct pattern for any future multimedia output (images, PDFs, video).

## Heuristic

> When a pipeline produces non-text artifacts, keep the artifact as a side effect in Layer 3 (tools) and pass only metadata (paths, URIs) through graph state.

## Seed

Could YAMLGraph define a generic `artifact` state type that tracks provenance (which node produced it, when, what tool) and supports automatic cleanup or archival? This would formalize the pattern for all binary outputs.
