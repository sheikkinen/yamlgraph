# Diary: the copilot-node `remote:` insight — let it emerge

**Date:** 2026-09-01
**Arc:** FR-945 recon → FR-948 delegation channel → *?*

## Observation

Three fold-and-rejudge rounds on FR-948 tightened it from "empirical spike works" to "22 ACs with typed enums, argv integrity contracts, in-memory redaction, full-tree kill primitives, phase invariants, and two named live witnesses." The judge did precision work each round. The FR is closer to green with every fold, not further.

At the tail of that arc, the operator asked whether yamlgraph itself would benefit from a `remote:` parameter on the copilot node — sharing the FR-948 delegation channel as a framework-level primitive.

## The reflection

The answer is yes, and the *value proposition* is much bigger than FR-948 as drafted:

- FR-948 is a **contrib/example skill** (per its own judge classification): one host, one immediate consumer, invoked via a Python CLI. Useful.
- `remote:` on the copilot node would make delegation **native to every yamlgraph agent workflow** — judge/research/review/author/chaplain runs all use copilot nodes; adding one YAML key moves them all to Huutokauppakone.
- The primary consumer of judge/research nodes is the *operator's own supervision loop*. Delegating those nodes keeps the iMac responsive during long enforcement runs — which is the actual pain FR-948 exists to relieve.

The recursive-delegation guard already in FR-948 (`YAMLGRAPH_LAN_DELEGATED=1`) composes cleanly: on the remote, `remote:` in a graph is a no-op. No infinite loop.

The scope split is natural:

| Layer | Role |
|---|---|
| FR-945 recon | Data primitive |
| FR-948 delegate skill | **Channel primitive** — reusable channel |
| Hypothetical FR-949 `remote:` | **Framework consumer** — yamlgraph exploits the channel natively |
| FR-950+ | Fleet, load-balancing, remote graph runs |

## The metacognitive trap I noticed

I wanted to file FR-949 immediately after seeing the shape. The operator's response was better: *"diary entry + Seed, let it emerge. proceed with 948 enforcement — we need investigation results, not more judging."*

Two calibration points I under-weighted:
1. **Speculative FRs are `growth_as_default` wearing an architecture costume.** The reflection above is a genuine architectural direction, but the concrete first consumer, first event, and pain gradient aren't there yet. FR-949 authored today would be my forecast of the value; FR-949 authored after the first painful judge-round-on-iMac is the operator's spark. Different quality.
2. **Investigation results (from FR-948 enforcement) will re-shape the reflection.** The live AC-19/AC-20 witnesses on Huutokauppakone will teach us things about latency, credits, `--add-dir` skill loading, taskkill semantics, network partition behavior. Those observations are the actual input to a well-shaped FR-949 — not my current speculation.

## The heuristic

**`architecture_as_forecast`**: an agent that watches its own work generate a substantial reflection is tempted to freeze it into an FR immediately. But the reflection has no first consumer other than "the LLM that saw the shape." The correct move is to record it and let it be refuted or refined by the next enforcement's evidence. The reflection graduates to an FR when a real spark (not a plausible one) demands it.

This is the same trap as `first_person_tool_horizon` from the Scripture's knowledge graph, but at the FR level instead of the tool level: I want to file an FR because I saw a pattern, not because the operator has a bounded problem needing a bounded solution.

## Seed

**Seed:** when FR-948 lands and the first real supervised judge round runs against Huutokauppakone via `scripts/judge.sh` — at what specific moment does the operator feel the tension that would motivate FR-949? Is it the first time a judge round takes 6 minutes and the iMac stays responsive? The first time two concurrent judges finish faster than one local one used to? Or a different moment entirely — perhaps when the `credits_reported` from one `remote:` node reveals the true per-node cost of a research adapter and makes graph-level budget become obvious?

The moment that answer surfaces is FR-949's first-event. Until then: no forecast, no premature freeze.

## Consequence

Proceed with FR-948 enforcement as designed. Do not draft FR-949 speculatively. Watch the enforcement evidence for the moment the reflection above ceases to be architecture-and-turns-into-necessity.
