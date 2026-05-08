# Diary: Skills Export — Constraint vs Description

**Date:** 2026-05-07
**FR:** FR-348
**Context:** Implemented `yamlgraph skill export`, tested activation in Copilot

## What Happened

1. Proposed the Skills standard mapping to YAMLGraph (graphs are already Skills structurally)
2. Filed issue #348 with `chaplain` label — pipeline imported, planned, judged, enforced, and merged autonomously
3. Ran smoke tests — export works: correct structure, deterministic, error handling solid
4. Exported to `.copilot/skills/` — Copilot found the skills but **did not activate them**
5. Created hand-crafted versions with proper framing — still not activated on generic prompts

## Trap Identified: `plausible_wrong_answer`

The export produces technically correct SKILL.md files. They have the right format, valid frontmatter, accurate content. But they fail at their purpose: triggering agent activation.

The output **passes shape check but is semantically wrong** — a SKILL.md that describes what a graph does is not the same as a SKILL.md that constrains how an agent behaves.

## Insight

> **Skills that constrain are adopted. Skills that describe are ignored.**

The agent already believes it can "analyze code" and "write polished content." A description of capability adds no value — the agent skips it. But a *constraint* ("you must write a failing test before fixing") imposes discipline the agent wouldn't apply autonomously.

Working skills encode **behavioral constraints**. Failed skills encode **capability descriptions**.

## Heuristic

> A mechanically-generated skill will always produce descriptions. Constraint-encoding requires authorship — understanding what discipline the agent lacks and imposing it.

**Corollary:** Skill export is scaffolding (structure + schema + references), not a finished artifact. The valuable layer — the constraint framing — must be authored by someone who understands the gap between what the agent *can* do and what it *should* do.

## Pattern: Boundary Application

This is the One Law applied to agent instructions:

> Normalize at the boundary where external data enters.

The SKILL.md is a boundary between the graph's capability and the agent's decision to activate. The export normalizes the *data* (schema, inputs, outputs) but not the *intent* (when and why to activate). Intent is the boundary that matters for agent adoption.

## Decision

Keep the export feature (zero ongoing cost, valid scaffolding). Don't invest in auto-generated triggers or instructional mode. The real product is hand-authored constraint skills backed by YAMLGraph execution — the export just accelerates the boilerplate.

## Seed

> Can a graph's *topology* (loops, conditions, fan-out) encode constraint information that a linear description cannot? A reflexion loop's structure *is* the constraint — "you must iterate until threshold." Could export detect topological patterns and generate constraint-language rather than description-language?
