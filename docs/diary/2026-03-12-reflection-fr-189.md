# Diary: FR-189 — Graduate `downstream_fix` Trap Description

**Date:** 2026-03-12
**FR:** FR-189
**Type:** Doctrine refinement (Knowledge Graph graduation)

## What Happened

FR-189 graduated the `downstream_fix` trap description based on evidence from 3 diary entries (FR-150, FR-172, FR-166). The old description ("Fix at callsite, not utility → avoid double-stripping") described the cure rather than the trap — a subtle inversion that could mislead agents into thinking the text described what to do, not what goes wrong.

The new description ("Guard added where symptom manifests → normalize at entry boundary instead") follows the established trap format: name the trigger, then redirect to the cure. This matches `quick_confidence: "When I feel certain → Judge instead"`.

## Cognitive Process

The change was mechanically simple (one string edit), but the TDD ceremony revealed value: writing the "no other traps changed" and "no cures changed" tests forced a systematic inventory of every Knowledge Graph entry. This is the `boring_enforcement` pattern — boring means the Judgement was good.

**Trap:** `description_inversion` — A trap description that reads as advice (what to do) instead of a hazard (what goes wrong) silently fails its purpose. The reader follows it as a cure rather than recognizing the cognitive trigger.

**Heuristic:** When writing trap descriptions, verify the sentence answers "what am I catching myself doing?" not "what should I do instead?" The trigger must come first.

**Seed:** Could the Philosopher daemon automatically detect description inversions by checking whether trap text matches the `trigger → redirect` format, flagging entries that read as prescriptive rather than diagnostic?
