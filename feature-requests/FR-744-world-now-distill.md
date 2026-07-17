# FR-744: World Now — a distill graph feeding docs/world-context.md, referenced by the board

**Status:** Completed
**Type:** Feature (graph + board pointer — the first fit-tested delegation)
**Effort:** 1 day
**Requested:** 2026-07-17
**Judged:** 2026-07-17 — source-fit gap measured (donor feeds are
general-tech; the March exemplar was ecosystem-targeted); placement
corrected by the philosopher's own relocation precedent; AC-05's
meter was pointed at the wrong pipe
**Completed:** 2026-07-17 — the world is fresh; witnesses below
**First consumer / first event:** the philosopher's next graduation
scan (`world_context_path` is its existing, currently starving input);
second consumer: `now.py`'s briefing (`world:` pointer with age).
**Spawned by:** the `builders_never_call` introspection
(2026-07-17) + the fit-over-affordance correction: a generic MCP
registration would sit unused; a tool must fit a task. The task found:
`docs/world-context.md` is **four months stale** (2026-03-13) — the
philosopher has been grounding Scripture-graduation reflections
against a frozen March world. The live digest run (2 runs, 3 minutes)
proved the fetch spine works and surfaced four defects the demo-gates
never caught.

**Prior art:** FR-046 (diary world digest — Implemented; produced the
world-digest diaries that stopped in March) and FR-194 (philosopher
world context — Implemented; the consumer seam). Disposition: this FR
is the *refresh mechanism* both assumed and neither built — 046 made
digests, 194 made the reader, nothing owns keeping the file current.
`examples/daily_digest` (the spine donor — and the defect exhibit:
dependency rot, silent empty success, unthrottled map, unschema'd
rank). FR-700 recap + FR-740 plan-state pointer (the now.py pointer
pattern this extends). `render_claims_as_claims` (the age label IS the
epistemic grade). FR-744-the-first (watcher subscription, killed in
conversation): this FR passes the consumer test that one failed.

## Problem

The doctrine's graduation pipeline reflects "against the world," but
the world file froze in March. Nothing owns refreshing it; the
producer (046's digest) and consumer (194's philosopher) were both
built, the pump between them never was. Meanwhile the first genuine
delegation attempt (2026-07-17) measured why: the digest bit-rotted
unconsumed — missing deps, a 100%-payload-loss run exiting 0, a
529 storm from ~50 unthrottled parallel map calls, and an unschema'd
LLM rank output crashing the template. `builders_never_call` made
mechanical.

## Proposed Solution

1. **`examples/world_distill/`** — daily_digest's fetch/filter spine
   (HN + RSS, dedup DB) feeding ONE distill LLM node that writes
   `docs/world-context.md`: dated header, ecosystem highlights,
   emerging themes, open questions (the format the March file and the
   philosopher already share). No email, no HTML.
2. **Built defect-free by construction** (each measured defect gets a
   witness): inline schema on the distill output (one_law); floor
   check — zero surviving articles RAISES, never writes an empty
   "world" (Commandment 6); map throttle if a map node is used at all
   (prefer batching into the single distill call — one judgement, one
   node, per the prompt contract); deps declared in the example's own
   requirements with an import-time check that names the missing
   package.
3. **`now.py` world pointer:** `world: docs/world-context.md (updated
   N days ago)` — age always displayed; past ~14 days it reads
   `STALE` (the display is the reminder; no scheduler in this FR).
4. **Runbook line in the README/skill:** refresh = one command;
   the philosopher consumes automatically on its next run.

## Acceptance Criteria

- [ ] AC-01 RED: distill output schema + zero-yield raise + dated
      header, fixture-pinned.
- [ ] AC-02: real run writes a fresh `docs/world-context.md`; the
      **raw output read** recorded in this FR (read_raw_output_first —
      N cited details a generated dump could not produce).
- [ ] AC-03: `now.py` world pointer with age + STALE label; witnessed
      in a tool result.
- [ ] AC-04: philosopher smoke: its context-load step reads the fresh
      file (no code change expected — witness only).
- [ ] AC-05: dogfood ledger note — the run's cost from the tap,
      recorded in this FR (the delegation-vs-inline economics, first
      real data point).

## Out of scope (purge list)

- Fixing `examples/daily_digest` itself (its four defects are
  recorded here as exhibits; separate chore/FRs — this FR builds
  clean rather than inheriting).
- Email, HTML, deployment, scheduling/cron (staleness label is the
  scheduler until reaching for it twice proves otherwise).
- Generic MCP registration (fit over affordance — this FR is the
  counter-experiment: one graph, one task shape, one file).
- new now.py sections beyond the one pointer line.

## Questions for the human (as options, or 'none')

None — both consumers are named and wired; cadence deliberately
deferred to the staleness label per the two-strike rule.

## Judgement (2026-07-17)

**Verdict: APPROVED — with the consumer's actual contract measured
and the meter re-aimed.**

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **The philosopher SLURPS the file** (measured: `load_world_context` returns raw text under `world_context`; no parsing). Format coupling is soft — the FR's "format the philosopher shares" overstates the contract | Schema applies to the distill NODE's output envelope only (one_law at the LLM boundary); the FILE contract is just: dated header + prose. AC-01 scope reduced accordingly |
| F2 | **Source fit gap.** The March exemplar's value was ecosystem-targeted (LangGraph releases, LangChain posts, LangSmith case studies); the donor feeds are general-tech (HN top, lobste.rs, dev.to) — a distill over those yields tech-news noise, not grounding for Scripture graduation. FR-046's original scope was explicitly "AI frameworks, LangGraph, Python ecosystem" | Feed list becomes curated ecosystem CONFIG (graph var / data file): framework blogs' RSS + HN filtered by topics; the `websearch` extra (exists in pyproject) is the recorded two-strike escalation if RSS curation can't reach exemplar quality. **AC-02's raw read judges grounding fitness against the March exemplar** — could this content have informed a graduation reflection? — not mere production |
| F3 | 50 articles × full fetched content into one distill call is a bloated prompt for a themes-level output | Distill input = title + source + ≤500-char excerpt per article, one call. Full-content fetch stays for the excerpt source only |
| F4 | **Placement: the philosopher already took this exact journey** — FR-196 relocated it FROM `examples/` TO `.chaplain/graphs/` because it is working doctrine infrastructure, not a demo | `​.chaplain/graphs/world_distill/` from birth; skip the examples detour whose correction is already in the git history |
| F5 | **AC-05's meter is aimed at the wrong pipe**: graph runs bill the Anthropic API directly — the OTel tap sees only Copilot editor sessions and will record nothing | AC-05 reworded: cost from the run's own usage output / LangSmith trace, compared against the inline-agent estimate (≈740K-context tool-call pricing). The comparison is the point, not the instrument |

**Purge confirmations:** daily_digest fixes, email/HTML/deploy,
scheduling, MCP registration — all stay out.

**Scope frozen:** AC-01 (distill envelope schema + zero-yield raise +
dated header, F1-reduced) → AC-02 (real run; raw read judged against
the March exemplar per F2) → AC-03 (now.py pointer + STALE) → AC-04
(philosopher smoke) → AC-05 (economics from run output per F5).
Placement per F4; input cap per F3.

### Questions for the human (as options, or 'none')

None — the feed curation list is an enforce-time editorial choice
within F2's binding shape; everything else is pinned.

## Implementation (2026-07-17)

RED (4 witnesses, REQ-YG-563/CAP-205) → GREEN.
`.chaplain/graphs/world_distill/` per F4: fetch (curated feeds:
langchain blog, simonwillison, huggingface + HN keyword-filtered) →
prepare (F3 cap) → distill (inline schema) → write (dated header).
now.py world pointer with age + STALE-with-refresh-command past 14d.

**Commandment 6 fired in production on run 1:** the distill node
failed (prompt-format defect, below) and `write_context` REFUSED to
overwrite the March world with emptiness — the exact guard whose
absence made the daily_digest ship a polite empty digest. The guard's
first act was protecting the file from its own author's bug.

**Two consumer-UX defects found by consuming (the builders_never_call
mechanism, live):** (1) `messages:` list format silently unsupported —
house prompts use top-level `system:`/`user:` keys; failure mode was
`Node distill failed: 'user'` (KeyError as UX). (2) `module: tools`
import fails from graph dirs — the philosopher precedent uses
`path: tools.py`. Both cost minutes here and would cost a newcomer
hours; both are FR-shaped framework ergonomics (error messages naming
the fix).

**AC-02 raw read (against the March exemplar — clears the bar):**
grok-build open-sourced after secret-upload backlash; Inkling 975B/41B
MoE Apache-2.0; Kimi K3 2.8T with open weights promised 2026-07-27;
Nemotron 3 Embed #1 on RTEB; model routing as a systems problem.
Specific, named, dated — nothing a generated dump could produce. Open
questions land on yamlgraph territory (sandboxing/tool-permission
primitives in YAML; routing/eval primitives across frontier vs open
weights; security regressions as first-class eval cases).

**AC-04:** philosopher's own `load_world_context` loaded the fresh
file (2,909 chars, header 2026-07-17) — no code change, as judged.

**AC-05 economics (F5 — CLI does not log token usage; estimated from
artifact sizes):** one distill call ≈ 5K in / 0.7K out ≈ $0.03 direct
API. The same synthesis done inline by this agent ≈ 3–5 tool calls ×
~740K context ≈ $2–4 at cache rates. **Delegation is ~100× cheaper**
for this shape — the first real data point for the dogfood ledger.
Honest caveat: CLI usage logging absent is itself a gap (LangSmith
trace is the proper source; not wired in this run).

**Deviations:** none of scope.
