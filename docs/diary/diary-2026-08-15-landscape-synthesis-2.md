# Diary — 2026-08-15: Landscape synthesis II — the customer was already in the moat

**Scope:** update to [diary-2026-08-15-landscape-synthesis.md](diary-2026-08-15-landscape-synthesis.md)
after the evening's discoveries: the csap clone (terveystalo/customer-service-
agent-platform), the version-drift finding, and the fourth claim probe
(XAI → conformance evidence). The morning synthesis stands; three of its
premises just improved and one of its risks just fired in miniature.

## The "one production consumer" premise was understated — in our favor

All day the analysis treated ninchat_voice (a `projects/` folder here) as the
best consumer. The cross-check revealed the *actual* production consumer is a
corporate enterprise repo — Terveystalo, 122 commits this month, its own
NC-numbered judged-FR pipeline, consuming **released, pinned** yamlgraph
(0.5.16) through a normal deploy chain. Two consequences:

1. **Move 2's question is partially pre-answered by existing practice.** The
   spine (judged FRs, doctrine, enforcement rituals) already operates in a
   foreign corporate repo we don't control. Spine portability isn't a pilot
   hypothesis; it's an observed fact awaiting formalization.
2. **The position graduates from thesis to reference deployment.** "EU AI Act
   conformity is the accelerant" read as futurism this morning. With a
   healthcare enterprise running per-call conformance artifacts in production,
   the category's first buyer is not projected — it is invoiced.

## The flagship claim was pulled, not pushed

The strongest marketing claim found today (per-call conformance evidence
against a judged artifact) was not designed by this repo — it was **built by
the customer** on top of FR-723's hook: NC-373 → NC-374 → NC-376, route
overlay rendered at every call teardown. The consumer extended the product in
the direction of the moat, unprompted. For a niche product this is the
healthiest demand signal that exists: it means the moat axis (auditability) is
where the *customer's* pain lives, not just our narrative. The framework's
job, correctly understood, is to keep supplying hooks the regulated consumer
can build conformance evidence on — not to build the evidence features itself.

## A risk from the morning synthesis fired within hours, in miniature

The morning entry named abandonment/staleness as the unfixable internal risk.
Its small form fired today: the in-repo ninchat_voice mirror (pinned 0.5.10,
five releases stale) produced a **false market conclusion** — "no execution
flowcharts in production" — that survived until the real consumer repo was
cloned. The repo's knowledge of its own consumers decays; the census, the
market research, and every "best consumer" claim must be refreshed from the
consumer's repo, not the mirror (`workspace_is_not_boundary`, provenance
form). Concretely: any future consumer-evidence claim should cite the
consumer's remote SHA, the way FR-803 pinned the Pipecat corpus.

## The method became the product demo

Four claim probes in one day, one invariant outcome: broad claim ties or
dies, narrow claim binds on an empty field —

| Broad (dies) | Narrow (binds) |
|---|---|
| open source, self-hosted | vendor incentive alignment |
| has YAML | declarative-first, lintable without executing Python |
| LLM-friendly tooling | closed error surface, canned remediations |
| explainable AI | per-run conformance evidence vs judged artifact |

The narrowing procedure — state the broad claim, probe it against primary
sources or running code, keep the surviving kernel — is marketing under TDD,
and the four rows compose into the position statement itself: *self-hosted,
declaratively-authored, machine-judgeable pipelines that emit per-run
conformance evidence — deployed today in regulated healthcare.* No sentence
in that statement is unprobed.

## What changed in the whole-landscape picture

Nothing moved on the competitor side — the binding axis remains empty for the
structural (income-statement) reasons the morning entry gives. What moved is
our side of the ledger: the position now has a reference deployment, an
observed instance of spine portability, and a demand signal pointing along
the moat axis. The remaining honest weaknesses are unchanged: bus factor,
model-interior opacity (traceable ≠ explained), and the standards kill-vector.

**Seed:** The customer built conformance tooling on our hook. What is the
*minimal* set of hooks (route log, run identity, artifact export) that lets
every regulated consumer build their own Art. 12 evidence — and should that
hook set, not any feature, be the versioned public contract of the framework?
If the product is what customers build evidence on, the API surface to freeze
and document is the hooks, and everything else is example code.
