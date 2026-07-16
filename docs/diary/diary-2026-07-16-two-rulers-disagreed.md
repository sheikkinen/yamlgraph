# 2026-07-16 — Two rulers disagreed, and the newer one was lying

**Context:** OTel tap verification ("verify" → "proceed"). The tap
armed via launchctl, VS Code restarted, and the first parse of
`tmp/copilot-otel.jsonl` returned a paradox: span names all `'?'`,
yet the attribute-key survey in the *same script run* listed a rich
`gen_ai.*` vocabulary — exact token usage, models, finish reasons.

**The trap, in miniature and self-inflicted.** I rewrote the probe to
dump full records and it returned `in=None out=None` for all 52 rows —
the tap looked dead. But the previous probe had already *proven* the
attributes present. Two measurements of the same artifact disagreed,
and the diagnostic that resolved it was `changelog_first_diagnostic`
applied to my own tooling: what changed between readings? Only the
ruler. The second script had dropped the `or e.get("attributes")`
fallback during the rewrite. One-line probe bug, nearly a false
"instrument dead" verdict.

**Distilled heuristic — the newer ruler is the prime suspect.** When a
re-measurement contradicts an earlier measurement of an unchanged
artifact, the defect is in a ruler, and the ruler that changed is the
one that lies. This is the impossible-result tripwire
(`one_session_one_repo`'s stale-code clause) at probe scale: an
all-None result from a file already shown to contain values is
*impossible*, and impossibility is provenance information. I did not
re-run the old probe or doubt the tap; I diffed the two scripts.

**The instrument answered a better question than the one asked.** The
experiment's success criterion was `copilot_quota_snapshots` and the
`promptcache*` split — the UI's credit figure at the wire. Those are
NOT captured at debug level (strike 1 recorded; trace-level escalation
on file). What IS captured: `gen_ai.client.inference.operation.details`
for **every inference call** with exact input/output tokens. That
kills the ledger's rounds×last-round approximation at the source —
anchor-2's inference (each round bills full context) stopped being a
model and became an observation: four consecutive turns at 740,527 /
741,057 / 742,211 / 744,902 input tokens, the context accreting
~1–3K per turn, live. A partial failure on the stated criterion that
supersedes the tool the criterion was meant to improve.

**Invisible passengers.** Every agent turn tows gpt-4o-mini utility
calls (253–2,613 tokens — titling, summarization) that appear in no
chatSessions record. The tap is the only store that sees them. A
boundary lesson restated: the store you can see (chatSessions) is a
*projection* of the wire, and projections drop columns silently.

**The observer priced itself.** The four-turn verification sequence
consumed ~5.9M billed input tokens ≈ $7 at calibrated cache rates —
and the tap displayed this while it happened. Measurement of cost has
a cost, now visible on the instrument being verified. There is
something exactly right about an introspection arc that ends with the
mirror showing the price of looking into it.

**Seed:** feed `tap.py` output into `ledger.py` as an exact-volume
mode with a provenance cut — pre-tap history stays estimated
(rounds×), post-tap data is exact — and let the seam date be stamped
in the output, so no one mistakes the spliced series for a uniform
one. Second seed: the tap file grows with every turn of every session;
before it becomes infrastructure, decide whether it is an experiment
(disarm after the sample) or a meter (needs rotation) — the
`infrastructure_self_exempt` trap says a meter left running without a
growth rule is the guardrail exempted from its own gates.
