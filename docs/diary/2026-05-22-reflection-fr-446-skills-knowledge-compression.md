# Diary: FR-446 — Skills as Curated Knowledge Compression

**Date:** 2026-05-22
**FR:** FR-446 — Promote Reference Docs to Copilot Skills
**Commit:** ed84bc56

## What Happened

Promoted 6 reference docs (totaling ~4,800 source lines) into Copilot skills (~1,000 lines total). The task looked mechanical — distill docs into smaller files — but the interesting decisions were about what to *exclude*.

## Trap: Compression Anxiety

The initial `author-graph` skill tried to cover 13 node types with full YAML examples for each. At 278 lines it exceeded the 200-line target. The instinct was to keep everything because "what if someone asks about race nodes?" — but skills aren't reference docs. They're *entry points*. The less-common types (copilot, race, pipeline, subgraph, tool_call, interactive_tool) got compressed into a 6-row table with pointers to the canonical sources.

**Heuristic:** A skill's job is to answer the 80% case immediately and *point to* the 20% case. If you're duplicating the reference doc, you've misunderstood the medium.

## Trap: Scope Creep Through Acceptance Criteria

The original FR included "register skills in copilot-instructions.md `<skills>` block" as an AC item. But VS Code auto-discovers skills from `.github/skills/*/SKILL.md` — the existing `check-langsmith-trace` skill proved this without any registration. The AC item was wrong. This is `gate_checks_shape_not_substance` from the Knowledge Graph: the AC checked for a mechanical action (edit a file) rather than the actual outcome (skill loads on matching query).

The smoke test AC — "ask 'how do I add a node to a graph?' and verify `author-graph` loads" — was the *real* acceptance criterion. Everything else was proxy.

**Heuristic:** The AC that matters is the one the user would notice. If your AC list has items the user wouldn't care about, they're process artifacts, not acceptance criteria.

## Insight: The Judgement Split Was Correct

Splitting `author-graph` from `author-prompt` during rejudgement proved right immediately. Graph authoring (node types, edges, routing) and prompt authoring (schemas, Jinja2, system messages) are triggered by completely different user intents. A combined skill would load 400+ lines of mixed content. The split loads ~200 lines of focused content. This is the `false_duplicate` trap inverted: they looked similar (both are "YAML authoring") but serve different cognitive tasks.

## Seed

**Seed:** Could skills be *generated* from reference docs using a YAMLGraph graph? A `compress-reference` graph could take a reference doc path, extract the procedural core, apply the 200-line budget, and output a SKILL.md. This would make Tier 2 skills trivial and keep skills in sync with their source docs as they evolve. The graph itself would be a demo of YAMLGraph eating its own tail — a framework that generates its own IDE integration.
