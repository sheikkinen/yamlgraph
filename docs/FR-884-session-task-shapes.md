# FR-884 Session Task-Shape Report (D-5)

**Window:** 2026-06-26..2026-08-25 Europe/Helsinki. **Corpus:** 74 interactive
sessions, **652M prompt tokens** after fork-prefix dedupe (350 duplicated
turns removed across 2 fork groups). **Classifier:** yamlgraph map+reduce
([examples/demos/session-shapes](../examples/demos/session-shapes/README.md)),
pinned `anthropic/claude-haiku-4-5`, authored via the sole route.
**Coverage: 74/74 sessions = 100% of window token volume classified (AC-06 ≥80% met).**
Token attribution uses per-session shape-mix fractions — treat shares as
estimates (fractions are model judgements; tokens conflate cache reads).
Buckets with fewer than 3 primary sessions are collapsed to *rare/other*
(AC-08).

## Ranked shape table (AC-07)

| Shape | Sessions (primary) | Token share | Prompt-contract clauses (1 judgement / closed / validated / stateless / bounded) | Existing `Task shapes:` overlap | Verdict |
|---|---|---|---|---|---|
| enforce-fr | 21 | 55.0% (~359M) | ✗ / ✗ / ✗ / ✗ / ✗ — multi-judgement, stateful, open-ended tool use | none (agentic core) | NOT extractable as a whole; its embedded deploy-watch/status micro-turns are (see below) |
| judge-fr | 9 | 18.5% (~120M) | ✓ / ✓ / ✓ / ✓ / ✓ | **already extracted** — judge graph, pinned gpt-5.5 | **Adoption gap, not construction gap** — the `builders_never_call` witness in cost form: a governed route existed while 18.5% of premium tokens judged interactively |
| plan-fr | 14 | 13.3% (~87M) | ✗ / ✗ / partial / ✓ / ✗ — ideation is human-in-loop by design | fr_triage graph (partial) | Not extractable; the human dialogue IS the value. Sub-shape "FR skeleton from decided brief" is graph-shaped but low volume |
| deploy-watch | 3 | 6.3% (~41M) | no judgement at all — pure polling | none | **Top construction candidate**: zero-LLM watcher; every poll/merge/check micro-turn in a mega-session pays full context for a yes/no |
| incident-forensics | 4 | 4.9% (~32M) | ✓ / ✓ (SID-keyed sources) / ✓ / ✓ / ✓ | none (two ad-hoc scripts born mid-incident in the raw read) | **Construction candidate**: evidence-gather + timeline assembly graph |
| docs-drafting | 4 | 0.2% (~1M) | ✓ / ✓ / partial / ✓ / ✓ | none | Extractable but cheap already — low priority by volume |
| rare/other (5 shapes × <3 sessions: test-orchestration, introspection, review-pr, backlog-ops, repo-ops) | 9 | 1.5% (~10M) | mixed | review graph exists (review-pr); recap graph exists (backlog-ops) | Below action threshold this window; review/recap adoption already underway |
| research | 9 | 0.4% (~2M) | ✗ open-ended | world_distill (partial) | Many sessions, negligible tokens — short explorations; leave interactive |

## The three findings that matter

1. **The premium interactive surface is ~87% enforce+judge+plan.** Of that,
   judge (18.5%) already has a pinned sole route — the cheapest intervention
   in this report is routing discipline, not new construction.
2. **The micro-turn tax is real and measurable.** Deploy-watch is only 6.3%
   as a *primary* shape, but the raw read (see
   [FR-884-raw-read-log.md](FR-884-raw-read-log.md)) showed poll/merge/check
   turns *inside* enforce sessions costing 200K–700K prompt tokens each.
   A watcher that answers outside the session attacks both buckets.
3. **Forensics extraction has organic precedent**: two evidence shapes were
   scripted mid-incident by the operator during the window. The pattern
   (SID-keyed gather → join → timeline) is closed-input, one-output —
   graph-shaped.

## `builders_never_call` witness rate

Of the 12 shapes, 4 had an existing governed instrument during the window
(judge, review, recap, world_distill). Token volume that flowed interactively
through those 4 shapes anyway: **~121M of 652M ≈ 19%** — almost entirely
judge-fr. Constructing new routes without an adoption mechanism would repeat
this: **every proposal below names its adoption trigger, not just its graph.**

## Proposals filed (D-6)

Converted to full FRs 2026-08-25 (inbox drafts superseded and withdrawn):

1. [FR-885](../feature-requests/FR-885-deploy-watch-outside-session.md) — zero-LLM rollout
   watcher; first consumer: any enforce session awaiting CD.
2. [FR-886](../feature-requests/FR-886-judge-route-adoption-nudge.md) — mechanical nudge when
   interactive judging is detected; first consumer: the next "judge NNN" turn.
3. [FR-887](../feature-requests/FR-887-forensics-evidence-timeline-graph.md) — SID-keyed evidence+timeline
   assembly graph; first consumer: the next production-incident session.
