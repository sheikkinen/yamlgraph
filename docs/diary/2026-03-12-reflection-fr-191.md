## 2026-03-12: Reflection — FR-191 Graduate `plausible_wrong_answer` Trap Description

**Context:** Implemented FR-191, refining the `plausible_wrong_answer` trap in the Scripture Knowledge Graph from variant-specific ("Silent fallback harder to catch than crash") to pattern-general ("Output passes shape check but is semantically wrong → add assertion beyond type validation"). The graduation is based on 4 confirmed diary occurrences (FR-165, FR-164, FR-184, FR-185) spanning silent fallbacks, type-valid-but-wrong LLM output, data structure costumes, and LLM-based deterministic matching.

**Process:** This is the third Knowledge Graph graduation (after FR-189 `downstream_fix` and FR-190 `infrastructure_self_exempt`). The pattern is now well-established: TDD with tests asserting graduated text present, old text removed, and no collateral changes to existing entries. Each graduation also requires updating the sibling test files' expected trap sets — the `partial_remediation` trap that FR-190 identified.

**Trap:** `working_system_inertia` — The original description ("Silent fallback harder to catch than crash") was *true* but incomplete. It named one symptom while the underlying trap is broader. The temptation was to keep it because it was already working. The cure was to inventory the diary evidence and recognize the pattern exceeds the description.

**Heuristic:** When a trap description names a specific variant, check whether diary evidence shows broader manifestation. A description that captures only one variant gives agents a false sense of coverage — itself a `plausible_wrong_answer` about what the trap means.

**Seed:** The graduation pipeline now has three precedents with identical structure. Should this become a templated process — a `yamlgraph graph` that takes diary citations and a proposed description, validates against the Knowledge Graph YAML block, and generates the test file and capability registration automatically?
