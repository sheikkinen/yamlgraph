---
type: feat
scope: examples
---
- **FR-565 DM v3 producer integration (author & attach plot plan)**: wires the
  `plot_plan.yaml` authoring graph into the headless generation pipeline.
  `doc_ops.author_plot_plan(doc, story_dir)` runs the graph (author → validate →
  bounded repair), parses through the tolerant boundary (`parse_plot_plan`), and
  attaches through the gated `write_plot_plan` seam. Triple-validated (J1): graph
  repair loop, `write_plot_plan` gate, `parse_plot_plan` boundary.
  `generate_story(enable_plot_plan=True)` calls it after cast derivation; the
  `--plot-plan` CLI flag and `$PLOT_PLAN` env var activate it.
  `chapter_nav.write_plot_plan` now stores `plan.model_dump()` for JSON
  serialization; `attached_plot_plan` reconstructs via `PlotPlan.model_validate()`.
  Graceful degradation: `InvalidPlotPlan` is caught in `generate_story`, continuing
  without a plan. A book with no plan is byte-for-byte v2 (dormancy invariant).
