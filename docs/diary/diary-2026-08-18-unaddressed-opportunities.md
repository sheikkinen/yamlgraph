# Diary: The Unaddressed Opportunities

**Date:** 2026-08-18
**Context:** Companion to `diary-2026-08-18-unasked-questions.md`. That entry
mapped question classes the system cannot generate. This one maps the dual:
value already *paid for* — by incidents, tokens, and discipline — whose
extraction has not begun. Opportunities, unlike questions, must survive
`growth_as_default`: each one below names its first consumer and firing
moment or admits it cannot.

## The unifying shape, stated first

Every gate in this repo enforces that artifacts get *written* — diary-gate,
changelog-gate, demo-gate, req-coverage. **No gate enforces that anything
gets read.** The result is a repo that is asset-rich and consumer-poor:
761 seeds, 1,198 diary entries, 53,082 audit decisions, 729 judged FRs —
write-side infrastructure of industrial quality feeding read-sides that
mostly don't exist. The opportunities are not new things to build. They are
the read-sides of things already built.

## 1. The seed corpus has no harvester

761 `Seed:` lines across 1,198 diary entries. Each was written at the moment
of maximum context — the end of an arc, by the agent that lived it. That is
a pre-filtered, provenance-stamped R&D backlog, and it is write-only.

The bitter joke: `diary_graduation_pipeline` — the mechanism that would
harvest seeds — is *itself an unharvested seed* in the Scripture's seeds
section, alongside four siblings that have sat there through hundreds of FRs.
The seeds section of the Scripture is a monument to this opportunity class.

- **First consumer:** the chaplain inbox (currently 2 items — it has spare
  capacity and an automated pipeline behind it).
- **Firing moment:** recurrence. The Scripture already prescribes the trigger
  ("heuristic appears twice → FR"); nothing detects the twice. Clustering
  761 seeds the way FR-816 clustered FRs would surface recurrences
  mechanically. The extractor pattern exists in `scripts/extract_fr_graph.py`
  — this is an adaptation, not an invention.

## 2. The judge corpus is an eval set nobody evaluates with

729 FRs with frozen verdicts is a labeled dataset. Unextracted value:

- **Judge regression testing.** When the judge's model or prompt changes,
  nothing detects verdict drift. Re-judging a fixed 20-FR sample against
  known verdicts is `are_the_witnesses_one_phenomenon` applied to the judge
  itself. Firing moment: every model upgrade — a named, recurring event that
  currently passes unobserved.
- **Judge distillation.** If a cheap model reproduces the frozen verdicts on
  the fixture, judgement cost drops an order of magnitude. The 40%-of-budget
  fact makes this the highest-leverage cost opportunity in the repo.
- **Verdict-outcome reconciliation** (from the companion entry): `caused_by`
  regression edges in the knowledge graph grade past verdicts for free.

## 3. The knowledge graph found its first reader — now feed the others

Verified today: `prior_art.py` already consumes `fr-knowledge-graph.yaml`.
FR-814 escaped the fr-board fate — it has a consumer. The unaddressed part
is the queue behind it:

- **Judge context packing.** The token-economics analysis (2026-08-17) showed
  3× precedent density is available; the causality-map compression research
  direction is written, validated in outline, and unstarted.
- **Bridge score** (the FR-816 seed, one day old): cross-cluster edge ratio
  identifies architectural-pivot FRs. First consumer: the judge's prior-art
  disposition step, which currently treats all precedent as equal weight.

## 4. audit.jsonl is a behavioral trace, not just an audit trail

53,082 decisions record what agents *actually do* — tool-call sequences,
denial-retry patterns, hook friction points. The previous entry proposed
mining it for gate precision. The larger opportunity: it is the only ground
truth for how doctrine performs in contact with real agent behavior. Where
denials cluster, either agents err systematically (new trap candidate) or
the gate is miscalibrated (retirement candidate). Both outcomes feed
existing pipelines. First consumer: the inquisitor, which currently audits
code but not the enforcement layer's own exhaust.

## 5. The doctrine is the product; the framework is the demo

`constraint_over_code` already states it: the 216 Scripture lines are
irreplaceable, the 21k Python lines are regenerable. YAMLGraph-the-framework
competes in a crowded category (LangGraph wrappers). The governance
apparatus — chaplain, judge doctrine, hook architecture, diary graduation,
traceability spine — has *no category*. Cross-project graduation to
ninchat_voice and statemachine-engine happens by hand today, proving both
demand and the absence of packaging. The operator's thesis ("build for
agents first") has its strongest evidence here, unpublished.

- **First consumer:** the sibling projects, today, manually.
- **Honest caveat:** this is the one entry that flirts with
  `growth_as_default` at ambition scale. The cheapest test is not a product —
  it is extracting the hooks + Scripture into one installable artifact and
  letting ninchat_voice adopt it. If adoption is refused, the opportunity
  was a mirage; that refusal is cheap and informative.

## 6. The MCP surface: prune before promote

100+ graphs registered as Copilot tools. `does_the_tool_fit_or_merely_exist`
already fired on this class. The opportunity is *subtractive*: instrument
which tools are ever invoked, keep the consumed few, retire the rest via
the FR pipeline. The operator expects subtraction proposals unprompted;
this is one.

## Ranking by named pain removed

1. **Judge regression fixture** — model upgrades happen regardless; drift is
   currently invisible. Smallest build, protects the highest-authority
   component.
2. **Seed harvester → chaplain inbox** — turns 761 dead artifacts into
   pipeline input using an extractor pattern that shipped yesterday.
3. **Corpus compression / judge context packing** — research direction
   already written; unblocks 3× precedent density.
4. **Doctrine extraction for siblings** — cheap adoption test before any
   product framing.
5. **MCP pruning** — subtractive, safe, doctrine-aligned.

## Heuristic

**An unaddressed opportunity is a write-side without its read-side.** The
gates guarantee artifacts exist; nothing guarantees they are consumed. The
mechanical test for any proposed artifact — and retroactively for every
existing artifact class — is: name the reader and the firing moment, or
file the retirement. FR-814 passed this test within a day (prior_art.py);
the Scripture's own seeds section has failed it for months.

## Seed

**Seed:** A first-reader gate: every artifact class must demonstrate one
mechanical read within N days of creation or auto-file a retirement proposal
to the chaplain inbox. The knowledge graph found its reader in one day; the
seeds section has waited months. What N separates infrastructure from
sediment — and would the gate itself survive its own rule?
