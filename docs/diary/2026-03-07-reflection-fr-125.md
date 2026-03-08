## 2026-03-07: Chaplain — FR-125: Pipeline Finalize with Critical Bugs

The planning phase successfully resolved FR numbering conflicts (FR-124 taken, renumbered to FR-125) and fixed all four initial judgement issues: corrected grep/awk patterns, eliminated duplication, removed dead references, and replaced non-portable sed syntax. However, the judge revealed two blocking bugs that halt implementation: an off-by-one error in CHANGELOG insertion logic that places entries in second position instead of first, and a static description that produces meaningless changelog entries instead of extracting the FR summary. Two non-blocking issues were also identified. The feature was moved back to inbox for amendments, highlighting the value of rigorous verification before execution.

**Seed:** How can we detect insertion-logic off-by-one errors earlier in the planning phase—through test cases, visual simulation, or architectural guardrails?
