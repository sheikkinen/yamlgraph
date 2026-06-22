---
type: feat
scope: examples
---
- **FR-563 DM v3 M4a -- author & attach (activate the plot lane)**: turns the dormant v3 plot
  validator into an attachable steering surface. A tolerant boundary parse
  `plot.author.parse_plot_plan(raw)` mirrors `parse_world_state` -- it drops unknown fields and
  off-alphabet functions/atoms from the authoring LLM's JSON and never raises (a hopeless payload
  yields an empty plan). A `plot.author.plot_validate_plan` python node returns
  `{"validation": {"ok", "flaws"}}` merged at the state top level, so the new `plot_plan.yaml`
  graph routes DETERMINISTICALLY on conditional edges (`validation.ok == true/false`), not an LLM
  router, with a `loop_limits`/`loop_exits`-bounded author -> validate -> repair cycle that
  re-prompts with the concrete flaws. Authoring is engine-free: only the four pure checks run,
  never the optional UP solve. `chapter_nav.write_plot_plan` is the sole, GATED owner of
  `doc["plot_plan"]` -- it runs `validate_plan` and raises `InvalidPlotPlan` before committing, so
  the attached-plan contract is un-bypassable -- and attaching a plan brings the FR-560 exclusion
  seam alive (Arnulf excluded at ch3, released at ch6). Authoring half of M4; realize + production
  driver wiring are M4b (FR-564).
