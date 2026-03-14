# Diary: FR-109 Batch Image Prompt Generation

**Date:** 2026-03-14
**FR:** FR-109
**Type:** Feature implementation (new example graph)

## Cognitive Process

Straightforward example-graph implementation following established patterns. The key decision was conforming to `prompts_relative: true` instead of the absolute `prompts_dir` path specified in the FR.

## Trap: Boundary Assumption Mismatch

The FR specified `prompts_dir: examples/batch_image_prompts/prompts` (absolute from repo root), matching the storyboard pattern. But the linter resolves this relative to `project_root`, which defaults to `graph_path.parent` when called without explicit root. The storyboard graph has the same latent issue — it also fails lint when called as `lint_graph(path)` without a project root.

The working pattern (`prompts_relative: true` + `prompts_dir: prompts`) is used by bugfix and enforce graphs that actually pass lint in tests. **The FR spec was plausible but wrong** — a classic `plausible_wrong_answer` trap where syntactic correctness hides a runtime boundary mismatch.

## Heuristic

**Test the spec, not just the code.** When a FR provides YAML config, don't copy it verbatim — validate it against the actual resolution logic first. The cheapest bug is the one killed when the spec is written.

## Seed

Should the linter warn when `prompts_dir` uses an absolute-from-root path without `prompts_relative: false` being explicit? The current behavior silently depends on the caller providing `project_root`, which test code often omits. A lint check could surface this ambiguity.
