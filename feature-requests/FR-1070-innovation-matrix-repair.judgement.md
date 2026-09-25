# Judgement: FR-1070 Innovation matrix repair

**Prior art:** `FR-1070-innovation-matrix-repair.md` is the FR this judgement governs. FR-795, FR-825 and FR-840 match only on "repair"; 034 (novel generator demo) only on "innovation"/"matrix". None concerns this demo.

**Verdict:** REJECTED — the domain fix is witnessed, but the research gate is unmet and the proposed dynamic grid cannot satisfy a static map cap as specified.

**Reviewed against:** `feature-requests/FR-1070-innovation-matrix-repair.md`; `docs/issues-2026-09-24.md`; `yamlgraph/compile/map_compiler.py`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The omitted domain input and hard-coded constraint count are observed (plan sections 1.1 and 2 D9). A non-square 4x3 fixture is a good discriminator for the ID math (FR-1070:50-51), and a real demo smoke is appropriate for checking that the input is used (FR-1070:52-55). Classification: contrib/example repair, not a framework extension.

## Required revisions

### R-1: Re-file with substantive committed research

Compare four to six genuine strategies for ensuring dimensions, map bounds and output counts agree, citing precedent, preserving dissent and answering `is_this_a_graph`. FR-1070:57-62 lists only two dismissed tactics and no graph-fit answer. The plan's incident witness is valuable evidence but not a dispositioned alternatives table under the active research gate.

### R-2: Make grid bounds implementable

FR-1070:43-45 says `max_items` equals the generated product using a state expression or Python-node return. The current map compares item count to a config value (`yamlgraph/compile/map_compiler.py:351-361`); the FR does not establish that an expression can occupy `max_items` or that a node can alter its config. Choose a fixed, explicit upper bound with overflow refusal under FR-939, or file a separately judged dynamic-cap contract; test a product above the bound. Do not claim arbitrary dimensions with an unchanged fixed 25 cap (FR-1070:28-45).

### R-3: Assert semantic completeness rather than count only

Replace `{{ expansions | length }}` alone with a witness that the synthesis either receives all dispatched cell IDs or explicitly reports missing cells; changing "25" to "21" without acknowledging four missing cells still presents a plausible incomplete answer (plan section 1.2 and 7 A.4). Clarify the dependency on a judged failure-channel contract, which FR-1064 has not granted. The four literal occurrences need an exact post-authoring assertion, not just a smoke of one quoted dimension.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Rejected FR-1070 disposition and a researched replacement demo-repair FR |

Not authorized: editing `pipeline.yaml`, prompt YAML, cartesian Python node or compiler under FR-1070.

## Revised acceptance criteria

- [ ] AC-01: Replacement cites committed four-to-six-class research with precedent, dissent and graph-fit answer.
- [ ] AC-02: A 4x3 fixture has 12 unique correct IDs; an above-cap fixture refuses before dispatch, with the cap expressed in a supported form.
- [ ] AC-03: A recorded demo run proves the declared brief reaches dimensions and proves all dispatched IDs reach synthesis or missing IDs are explicitly surfaced.
- [ ] AC-04: Governed YAML changes use `scripts/author.sh` and its own graph's lint/smoke witness.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No demo or compiler edits under FR-1070; a new researched FR needs its own judgement. | GATE |
| C-2 | Do not substitute a smaller reported result count for actual completeness. | GATE |

Authority granted: none under FR-1070.
