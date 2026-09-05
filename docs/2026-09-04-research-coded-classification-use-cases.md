# Coded Classification — Use-Case Research

**Date:** 2026-09-04
**Type:** Research (no FR authorized; no implementation proposed here)
**Pattern:** `reference/patterns/coded-classification.md` (PROVEN, two instances)
**Instances:** `examples/icpc-2-rfe` (FR-722→730), `examples/cwe-classifier` (FR-733/734)
**Relation to prior work:** `docs/2026-09-02-brainstorm-business-use-cases.md`
ranked the whole example corpus commercially and gave coded classification
three rows (N11 CPV, N12 chart-of-accounts, N13 ESCO — ranks 20, 24, 31) plus
two verticals of the same machinery (#2 CodingProof, #6 incident census). This
document does not re-rank those. It screens the *vocabulary space* the pattern
can reach and asks a different question: which candidates would teach us
something the two existing instances did not.

---

## 1. The screen

The pattern doc states three prerequisites. Field evidence from the two
instances, plus one candidate that fails in an informative way, adds three
more gates that turn out to dominate cost and learning:

| Gate | Question | Where it came from |
|---|---|---|
| G1 Definitional catalog | authoritative per-code title + inclusion/exclusion terms, versioned, parseable | pattern doc |
| G2 Clusterable facet | a natural grouping giving <= ~100 clusters | pattern doc |
| G3 Extractive evidence | the justification is quotable from the input | pattern doc |
| **G4 Gold economics** | does a public labeled corpus exist, or must we author fixtures? | **CWE (FR-733): "the fixture-labeling economics of law 6 collapse to near zero when the domain has a public gold corpus"** |
| **G5 Rule surface** | does the standard ship its own coding rules, and are they live in-population? | **ICPC rule 3 mechanized; CWE abstraction chains measured "nearly vacuous" (384 Base / 9 Variant / 6 Class)** |
| **G6 Independence** | is an item's correct code independent of the other items' codes? | **MTG (section 3.4) — the pattern doc omits this gate entirely; both instances satisfy it by accident** |

**G6 is a silent precondition, not a new idea.** The 09-02 doc's map-reduce
reflection lists it first ("items are independent — no cross-item state during
the map"), but `reference/patterns/coded-classification.md` does not state it
among its three prerequisites, because ICPC rubrics and CWE categories never
interact. It took a compounding domain to make the omission visible. Any
candidate must be screened on it before the other five.

G4 is the sharpest reordering lever. ICPC-2 required hand-authored synthetic
fixtures in three languages with mandatory rationale; CWE inherited NVD gold
labels for free. Any candidate with a public gold corpus starts an entire
phase ahead, and G4 is *invisible* in a purely commercial ranking — which is
why the ordering below differs from the 09-02 table.

G5 is the anti-hype gate. FR-733's own lesson was to **measure the rule's live
surface before billing it as a centerpiece**. A vocabulary with elaborate
printed rules that never fire in-population buys nothing.

---

## 2. Two pattern shapes not yet named

The existing instances both classify *free prose* into codes. Two variants
reuse the whole machinery with a different input side, and both are
self-labeling.

### Shape A — Vocabulary crosswalk (code -> code)

Map a local/proprietary terminology onto a standard: local lab test names ->
LOINC, local chart of accounts -> statutory chart, in-house defect taxonomy ->
CWE, supplier part categories -> UNSPSC. The "free text" is the local label
plus whatever context the source system carries; evidence spans quote the
source label and its own definition. G4 is satisfied by **existing published
crosswalks** — labs, ministries and standards bodies publish mapping tables,
so gold data is a download.

Why it matters: crosswalk authoring is a known expensive manual task with a
named owner (terminology services), and the abstention/evidence contract is
exactly what makes a proposed mapping reviewable rather than trusted.

### Shape B — Temporal recoding (version bump)

When a vocabulary versions, every holder of coded back-catalogue must recode:
ICD-10 -> ICD-11, NACE Rev.2 -> Rev.2.1, CWE 4.x bumps, OIICS 2.01 -> 3.0.
The vocabulary itself ships official mapping tables — again free gold — and
the residue (codes with 1:n or no mapping) is precisely the reviewable
exception queue the pattern already produces.

Why it matters for this repo's doctrine: a version bump is a **dated first
event with a budget attached**, which is what every FR here is required to
name and what the census products in the 09-02 doc struggle to produce.

---

## 3. Candidate vocabularies, screened

### 3.1 Passes all six gates — strongest

**C1 — OIICS occupational injury/illness coding.** Free-text injury
narratives -> Occupational Injuries and Illnesses Classification System event
codes. NIOSH, the NASA Tournament Lab and Topcoder ran a 2018 auto-coding
competition releasing **229,820 labeled records** over **48 event codes in 7
categories**; published baseline accuracy 81%, internal winner 87%, external
winner 89% (BERT/ALBERT ensembles). US BLS/CDC vocabulary, free, with
published selection and coding rules.

- G1 free and parseable; G2 **7 categories is a near-perfect fan-out** — an
  order of magnitude cheaper per input than ICPC's 38 clusters; G3 narratives
  are short and the causation phrase is quotable; G4 six figures of gold, free;
  G5 OIICS ships explicit selection rules.
- **The unique prize: an external accuracy number.** Both current instances
  report *agreement* and the pattern doc explicitly warns "agreement is not
  accuracy". OIICS is the only candidate found that offers a published SOTA to
  measure the pattern against on the same data. That is a claim the pattern
  currently cannot make in public.

**C2 — EuroVoc / EUR-Lex subject indexing.** Legal documents -> EuroVoc
descriptors (~6,700, hierarchically organised into microthesauri = the
clusters). Gold: JRC-Acquis (~23,000 documents, ~6 descriptors average,
parallel across 22 official EU languages) and EURLEX57K (57,000 acts annotated
by the EU Publications Office).

- G1 free thesaurus with scope notes; G2 microthesauri; G3 partial — subject
  indexing is more judgement than extraction, so this is the candidate that
  *tests* how much law 3 degrades; G4 excellent; G5 weak (indexing conventions,
  not coding rules).
- **The unique prize: language invariance becomes measurable.** ICPC-2
  discovered cross-lingual hazard by accident — "a German compound noun
  lexically primed the wrong chapter's cluster" — from hand-translated
  fixtures. EuroVoc gives the same document in 22 languages with the same gold
  labels, turning a one-off anecdote into a quantified property. Multi-label
  by construction also stresses the reducer's secondary tier, which ICPC-2
  barely exercises.

**C3 — LOINC crosswalk (Shape A).** Local lab test names + units + specimen ->
LOINC. Six-axis structure gives natural clusters; published mapping sets give
gold; the task has a named owner and real cost.

**C8 — Regulatory applicability ("does this apply to us?").** An entity,
product, system or activity description -> the provisions that apply, each with
quoted evidence. Instances: EU AI Act (prohibited / Annex III high-risk / Art.
6(3) derogation), NIS2 (Annex I-II sectors × size thresholds), MDR Annex VIII
device classification, GDPR Art. 9 special-category processing, CRA, DORA,
CSRD/ESRS.

- G1 **exceptional** — EUR-Lex publishes consolidated legal text free, in 24
  languages, with structured article/annex/point numbering, and the definitions
  are legally binding rather than editorial. G2 yes: annexes and rule families.
  G3 yes: the evidence is quoted from the *submitted description*, which is
  also the artefact a reviewer would challenge. G4 weak-to-partial (below).
  G5 **maximal — this is the pattern's best G5 domain by a wide margin.**
- **MDR Annex VIII is the sharpest single instance found.** It ships **22
  numbered classification rules in four groups** — non-invasive (1-4), invasive
  (5-8), active (9-13), special (14-22) — and an implementing rule in Chapter
  II: *if several rules, or several sub-rules within a rule, apply, the
  strictest one resulting in the higher classification governs*. Four groups is
  a **smaller fan-out than any other candidate**, and practitioner guidance
  describes the method as: land on a rule in the first three families, then walk
  Rules 14-22 as a **second pass**, comparing the class each produces and
  letting the higher govern. That is the pattern's own topology — bounded map,
  deterministic reduce with a precedence rule — written into EU law.
- **New law it would force (three items):**
  1. **A conditional verdict tier.** Both instances use
     match / partial_match / not_applicable. Applicability needs
     `applies` / `does_not_apply` / **`applies_if`**, where the third carries an
     *unresolved predicate* ("if the intended purpose includes monitoring vital
     physiological parameters"). Its payload is a question for a human, not a
     confidence value — something no current tier can express.
  2. **Negative determinations need positive evidence.** ICPC's prompt says
     "omit rubrics that are plainly irrelevant"; the reducer discards negatives.
     In compliance the *out-of-scope* finding is the valuable one and must cite
     the exclusion or derogation that produces it. The pattern currently throws
     away exactly the output this domain buys.
  3. **A second reduce shape: ordinal aggregation.** ICPC and CWE reduce to a
     *ranked code list* via demotion. MDR reduces to a **single ordinal grade
     via max() over rule outcomes**. Same map, different reducer algebra —
     probably a family, not a special case.
- G4 is the open question and the reason this is research, not a proposal.
  There is no public "description -> applicable articles" corpus. Two partial
  sources are worth checking before anything is authored: EUDAMED device
  registrations pair manufacturer-declared risk class with intended-purpose
  text (self-declared, noisy, but public and large), and the MDCG borderline
  and classification manual ships worked examples. **Neither is verified —
  treat as a hypothesis to test, not a finding.**
- Liability framing is non-negotiable: output is a reviewable draft with
  citations and an exception queue, never a determination. The pattern's
  abstention + evidence + human-veto contract already fits; this must be
  explicit in any FR.
- Dogfood available: the 09-02 doc's N1 notes the whitepaper maps AI Act
  articles to repo mechanisms **by hand today**.

**C9 — Tabletop RPG rules adjudication (D&D 5e).** A narrated player action or
described situation -> the applicable rules, conditions and procedures, with the
narration quoted as evidence. "I grab his wrist and twist" -> Grapple
(contested check), Restrained condition, and the rules that govern each.

- G1 yes and unusually clean: **SRD 5.1 (27 Jan 2023) and SRD 5.2 (22 Apr 2025)
  are both released by Wizards of the Coast under CC-BY-4.0, irrevocably.**
  Conditions carry exact numbered effect bullets; spells have structured fields
  (casting time, range, components, duration). G2 yes, several small facets:
  14 conditions, 8 spell schools, 13 damage types, 18 skills, action types.
  G3 strongly yes — the narration *is* the input. G5 yes: "specific beats
  general" is a stated design principle, and advantage/disadvantage
  cancellation and condition-stacking are explicit precedence rules.
- G4 **strong, and of a different species.** FIREBALL (ACL 2023) holds nearly
  **25,000 real D&D sessions and 153,829 turns** captured from Discord play via
  the Avrae bot, pairing natural-language narration with **true game state and
  the executable commands actually run**. The ground truth is therefore *what
  the game engine actually did* — mechanical execution, not human annotation.
- **New law it would force (three items):**
  1. **Law 1 has two halves, and only one is universal.** "Catalog is a
     generated artifact, **never committed**" is stated as one law, but the
     no-commit half is motivated purely by Wonca licensing. Under CC-BY-4.0 the
     catalog *may* be committed with attribution, while the *generated*
     half — verified vs provisional provenance — still earns its keep. The law
     should be split so the licensing-contingent part is labelled as such.
  2. **A new gold species: engine-executed truth.** Human-annotated gold drifts
     between annotators; an executed command does not. It is also narrower —
     it covers only what players chose to mechanize. Worth naming in law 6
     alongside labeled corpora, because the failure modes differ.
  3. **The publishable instance.** ICPC-2 can never ship a public demo with
     real data (licensed vocabulary, clinical caveats); CWE can partly. D&D is
     **zero-stakes with a free vocabulary and a public corpus**, so the
     instance, its fixtures and full transcripts can all be published. The
     09-02 doc names the missing "Proclaim" stage (N16); this is the cheapest
     way to fill it with something runnable rather than a specification.
- Bonus: **SRD 5.1 -> 5.2 is a real version bump with an official relationship**
  (5.2 carries the 2024 rules and exists to help creators migrate), so C9 also
  supplies a free Shape B test alongside the base task.
- Repo consumer: `examples/dungeon_master` is the largest example and sits at
  09-02 rank 30 as judged scope-cut dead weight. A rules-lookup classifier is a
  component it could consume — which converts rank 30 into the *named consumer
  with a dated first event* that repo doctrine requires before topology work.

### 3.2 Passes, high commercial value, expensive gold

**C4 — MedDRA adverse-event coding (pharmacovigilance).** Verbatim
adverse-event text -> MedDRA Preferred Terms. Highest hallucination
intolerance of any candidate (regulatory submissions), SOC hierarchy and
Standardised MedDRA Queries give clusters, licensed vocabulary so **law 1 is
mandatory rather than optional**. Gold is proprietary to sponsors; G4 fails
publicly, which makes this a customer-data engagement, not a research vehicle.

**C5 — ICD-10/ICD-11 clinical coding.** The obvious CodingProof continuation
(09-02 rank #2). WHO vocabulary with inclusion/exclusion terms, chapters as
clusters, and an official ICD-10 -> ICD-11 mapping (Shape B). Public gold
exists only under credentialed access (MIMIC-class discharge summaries under a
data use agreement), so G4 is "conditional, with paperwork".

**C6 — MITRE ATT&CK technique mapping.** Threat reports -> techniques.
Tactics are the clusters, free vocabulary with rich descriptions, and MITRE
publishes report-to-technique mappings as gold. Closest sibling to the
existing CWE instance, which is both its strength (copy-adapt is cheap) and
its weakness — it would likely produce **no new law**, and the pattern doc's
rule-of-two is already satisfied.

**C7 — Patent CPC classification.** Every granted patent carries
examiner-assigned CPC codes, so gold is essentially unlimited and free, and
CPC ships definitions. Fails G2 hard at full depth (hundreds of thousands of
subclasses) — viable only truncated to subclass level, which is a different
and easier task than the one practitioners actually need.

### 3.3 Instructive failures — worth recording so they are not re-proposed

| Candidate | Fails | Why |
|---|---|---|
| **CPV procurement codes** (09-02 N11) | G1 | CPV is largely **title-only** — no inclusion/exclusion terms per code. Without definitional text the cluster brief degenerates to a name list and law 2's closed-list guard is all that remains. This is a real weakness in an idea already ranked 20th, and it was not previously noted. |
| **SNOMED CT (full)** | G2 | Hundreds of thousands of active concepts with no facet that yields <= ~100 clusters; it is a description-logic ontology, not a chaptered classification. The pattern doc's "SNOMED-subset" hedge is doing load-bearing work — only a curated subset qualifies. |
| **Sentiment / intent / open moderation taxonomies** | G1 | No authoritative definitional catalog; the taxonomy is the vendor's opinion, so there is nothing to reconcile claims against and the reducer's caps become guesses. |
| **Free-text topic tagging, open vocabulary** | G1+G3 | Explicitly out of scope per "what does not transfer". |
| **Chart-of-accounts assignment** (09-02 N12) | G5 | Passes G1-G4 but the statutory rules are org-specific policy rather than a shipped standard, so law 5 has almost no surface. Confirms the 09-02 verdict ("audit-grade evidence is the only wedge") from the pattern side. |

---

### 3.4 The boundary case — Magic: The Gathering

MTG looks like the ideal candidate and is the most instructive failure in this
document. It has a definitional catalog of tens of thousands of unique Oracle
cards (free via Scryfall's bulk `Oracle Cards` export, refreshed every 12
hours), the most elaborate rulebook in commercial existence (the Comprehensive
Rules, free and numbered to four levels), per-card official rulings, and
therefore the strongest G1 and G5 of anything screened. It fails on **G6**,
the gate nobody had written down.

**Why it fails.** The defining difficulty of MTG is exactly the compounding the
pattern forbids: a card's meaning is a function of the other cards in play.
The layer system (CR 613) exists *because* continuous effects must be applied
in a fixed order with dependency resolution (CR 613.8); state-based actions
(CR 704) re-evaluate the board continuously; and the golden rule (CR 101) lets
card text override the rules themselves. A per-item judgement cannot be
correct in isolation, which is precisely law 2's assumption.

**But MTG is not one task, and the sub-tasks screen differently.** This is the
useful part — the decomposition is the finding, not the verdict:

| Sub-task | Verdict |
|---|---|
| **Deck legality** (format legality, 4-of limit, singleton, colour identity) | **Anti-use-case.** A deterministic database join. G3 is *vacuous* — nothing is inferred, so there is nothing to quote. An LLM here adds only liability. |
| **Keyword / ability tagging** from Oracle text | **Already solved by a parser.** Scryfall derives keywords mechanically. Free gold here is a *warning sign*: when the gold was produced by a parser rather than a judgement, the task does not need a model. Worth adding to G4 as a corollary. |
| **Rules-question adjudication** — which Comprehensive Rules are in play | **Fits, partially.** CR sections cluster cleanly, G5 is maximal, and "which rules are implicated" is genuinely what a judge determines first. |
| **Board-state resolution** — what actually happens | **Out of scope.** Requires ordered layer application with dependency resolution: an interpreter, not a reducer. |
| **Deck audit** (card × declared strategy role) | **Fits with graceful degradation.** Most cards' role is locally determinable; the interaction-dependent ones fall out as the exception queue rather than as silent errors. |
| **Combo detection** | **Fits — but as a different pattern.** Map over card *pairs*: a 100-card Commander deck is 4,950 pairs, bounded. That is the cross-product census shape the 09-02 doc already named, not coded classification. Gold exists: Commander Spellbook holds 30,000+ curated combos behind an open REST API. |

**The finding that generalises: a reduce ladder.** Extending R8, the candidates
sort by what their reducer has to do:

1. **Rank** — sort and demote a candidate list (ICPC, CWE). Proven.
2. **Ordinal max** — aggregate rule outcomes into one grade (MDR, C8). Plausible, untested.
3. **Interpreter** — apply effects sequentially until the state stops changing (MTG). **Outside the pattern.**

This converts the doc's vague "anything where items interact (use FSM or a
sequential loop)" into a testable criterion: **can the reduce be written
without iterating to a fixed point?** If it needs a fixed point, it is an
interpreter and belongs to a different pattern. That test is cheap to apply
during screening and currently does not exist.

**A licensing bonus that settles the law-1 split.** C9 argued law 1 has two
halves and only the *generated* half is universal. MTG supplies the opposing
pole **from the same publisher**: the Wizards Fan Content Policy explicitly
forbids verbatim copying and reposting of Wizards IP and names Magic cards,
so the catalog must be generated locally from Scryfall and can never be
committed — while D&D SRD 5.1/5.2 under CC-BY-4.0 may be. One publisher, two
vocabularies, opposite obligations, identical machinery. That is the cleanest
available evidence for splitting the law.

### 3.4.1 Second pass on MTG — where the sub-tasks route

The G6 failure above is narrower than "MTG is out of scope". Screened against
the *whole* pattern library rather than this one pattern, MTG's practical
questions route to three different patterns, and one of them is the repo's
least-instantiated. Three framings were examined: adjusting an ongoing game,
building a deck from a declared strategy, and inventing new strategies.

**Cross-cutting asset: MTG has an outcome oracle.** Every other candidate in
this document has *label* gold — a human or a parser said what the right code
was. 17Lands publishes public CSV datasets (`17lands.com/public_datasets`):
GameData with per-game outcomes, DraftData with pools and picks, plus replay
data and an established tooling ecosystem. Tournament results supply the same
for Constructed. This is a **third gold species: outcome-labeled**, and it is
the strongest available, because it measures whether advice was *good* rather
than whether it *agreed*.

It needs its own discipline, exactly parallel to law 6's "agreement is not
accuracy": **outcome is not correctness.** A single game is dominated by
variance, so attributing a result to one decision at n=1 is causally invalid;
and 17Lands reflects the *player population* — largely non-expert — so it
measures what typical players did, not optimal play. Valid in aggregate, never
per-decision.

**Cross-cutting constraint: much of MTG's judgement is already solved
statistically.** Per-card win rates are published and draft overlays already
display them. The MTG keyword-tagging finding therefore generalises into a
design rule: **where a statistic exists, the model must not produce the
number.** Its remaining job is what statistics cannot do — explaining,
reasoning about *this* pool or board rather than the population average, and
handling states too rare to have data.

| Sub-task | Routes to | Verdict |
|---|---|---|
| **Sideboarding** (between games) | this pattern, per-deck catalog | **Best in-game fit.** Closed vocabulary is the player's own 75 cards — a catalog *generated from the decklist*, so law 1 applies cleanly. Happens between games, so no real-time constraint and no hidden-state math. Evidence is quoted game-1 observation plus card text. G6 holds well enough: per-slot judgements are largely independent and the deck-level arithmetic (stays 60, sideboard <= 15, swaps balance) is exactly what a deterministic reducer is for. |
| **Mulligan decision** | this pattern | **Best outcome-oracle research vehicle.** A binary keep/bounce decision against a large outcome-labeled corpus — the cheapest place to test whether outcome gold works at all before betting anything larger on it. |
| **Limited draft pick** | this pattern | **Cleanest gate profile in MTG.** Each pick is one item with a **closed 15-card candidate list** (the pack), bounded pre-gathered context (the pool), extractable evidence, no rules interpreter and no hidden information at pick time. **G6 holds**: the pool is *input context*, not another item's code — compounding is absorbed by the context bundle, which is what the pattern prescribes. Subject to the statistics rule: ratings already exist and are better computed statistically, so the model's contribution is pool-specific synergy reasoning and abstention. |
| **Deck construction from a strategy** | **schema-driven extraction** | **Strongest MTG fit overall, and not this pattern.** The loop maps exactly: declare target shape (role budget) -> observe current shape (curve, pips, role counts — Python) -> compute delta (arithmetic) -> reduce delta (the LLM's *only* job: propose candidates for one named gap from a Scryfall-filtered closed pool, Oracle text quoted) -> verify convergence (re-check plus `interrupt` approval). The naive "AI deckbuilder" is inverted: code identifies the gap, the model proposes for it, code validates legality and counts. The target shape must be **declared, not inferred** — published archetype budgets are community opinion and fail G1 — which is what that pattern already requires. Would be its second instance. |
| **Threat assessment** ("what in their 75 beats my board") | cross-product census | Map over pairs (my board × their probable list). Not classification. |
| **Metagame census** | corpus map-reduce | **The only one of the three framings buildable today with existing machinery.** Reduce is *counting* over tournament decklists; the model only names and describes archetypes. Two snapshots gives the temporal-census drift report. |
| **Open-niche detection** | cross-product census | Archetype × archetype matchup matrix: find what beats the top three and is under-represented. The matrix is arithmetic; the model proposes *why*. |
| **Combo discovery** | cross-product census | Carries a clean falsifiable experiment: can it **rediscover held-out Commander Spellbook combos it was never shown?** 30,000+ curated combos make that a real test rather than a demo. |
| **In-game line selection** | FSM-as-conductor + a rules engine | **Out.** Needs the layer interpreter, hidden information and adversarial modelling. The rules engine does the state math and the model stays away from the numbers. |
| **Novel strategy synthesis** | nothing here | **Out.** Strategy invention is generative; this library is analytic. It can produce a strategy *brief* — the open niche, the matchup math, the candidate cards — but cannot validate one, because validation means playing games. Limited has retroactive validation via 17Lands; Constructed has none, so the oracle is deferred to the human and to later results. Legitimate as an exception-queue posture, but it must be stated rather than implied. |

**Revised disposition.** Do not build an MTG *coded-classification* instance
for rules adjudication — that remains the worked negative example the pattern
doc's "what does not transfer" section lacks. But the earlier "document it and
move on" was too broad: MTG fails **this** pattern while fitting three others,
and it contributes the outcome-labeled gold species plus two discipline rules
that apply to every candidate in this document. If a domain this ill-suited to
the pattern still routes cleanly to three siblings, the more useful artefact is
not a list of fits and misses but a **routing table** — which is what a pattern
library is for.

If any MTG work is ever authorized, the order is: metagame census (buildable
now), draft pick advisor (cleanest gates, tests the outcome oracle on a bounded
task), deck-shape convergence loop (best pattern fit, second instance for
schema-driven extraction), sideboard advisor (a neat law-1 variant), combo
rediscovery (cheap and falsifiable). Never in-game line selection.

---

## 4. Research questions the candidates would settle

Ordered by how much they would change the pattern doc.

**R1 — Does the pattern beat published SOTA, and at what cost per item?**
Only C1 can answer. Success criterion is not "beats 89%" — it is a defensible
number *plus* evidence spans, abstention, and coverage arithmetic that a BERT
ensemble cannot produce. If accuracy lands materially below SOTA, the honest
product claim narrows to auditability, and the pattern doc should say so.

**R2 — Is per-cluster fan-out a calibration mechanism?**
Confidence is uncalibrated in both instances ("within-rank tie-break only,
never a threshold"). The fan-out generates structure the instances currently
discard: how many clusters proposed a code, whether it recurred across k runs,
whether cluster verdicts conflicted. With a large gold corpus these become
testable calibration features. A calibrated abstention threshold would be the
single biggest upgrade to the pattern's product story, because it converts
"exception queue" from a design choice into a tunable cost dial.

**R3 — How far does law 3 degrade without extraction?**
C2 is judgement-heavy indexing. The doc asserts that losing extractable
evidence "loses law 3's strongest guard" but has never measured it. Running
one instance where evidence is weakly extractive would put a number on the
boundary of the pattern's applicability.

**R4 — Is language invariance a property or an accident?**
C2's 22-language parallel gold turns the ICPC German-compound anecdote into a
measurement. If cluster priming is systematic, that is new law: brief
rendering may need to be language-aware, which no instance currently does.

**R5 — Does a third instance force the extraction?**
FR-734 recorded the first concrete extraction motivation — the two
`_align_span` copies have diverged (CWE gained multi-block interior-omission
repair with local re-anchoring; ICPC is still single-block). A third instance
makes the rule-of-two argument moot and the shared-library FR judgeable. C1 is
the cheapest third instance (7 clusters, free gold, free vocabulary), so it
doubles as the forcing function for a decision already parked.

**R7 — Is the verdict tier itself domain-dependent?**
C8 needs `applies_if` with an unresolved predicate; C9 needs "applies with a
DM ruling required". Both are the same missing thing: a verdict whose payload
is a *question*, not a score. If two unrelated domains need it, the three-value
tier inherited from ICPC is an artefact of ICPC, not a law — and the pattern
doc currently presents it as settled.

**R8 — Is there a second reducer algebra?**
ICPC and CWE both reduce to a ranked list by demotion. MDR reduces to an
ordinal grade by max(). If ordinal aggregation is a family rather than a
one-off, the pattern has two reduce shapes and law 4's "demote-never-drop"
needs an ordinal sibling. C8 is the only candidate that tests this.

**R9 — Is the fixed-point test the real boundary of the pattern?**
Section 3.4 proposes that a domain leaves the pattern exactly when its reduce
needs to iterate to a fixed point. The claim is derived from one domain and is
cheap to falsify: apply it retroactively to the refuted ideas in the 09-02
doc's section 6 and to `/converge`, and see whether it predicts the verdicts
that were already reached independently. If it does, it belongs in the pattern
doc as a screening question; if it does not, it is a nice-sounding rule with
one data point.

**R6 — Do the shapes in section 2 actually reuse the machinery?**
Both Shape A and Shape B are asserted here, not demonstrated. The cheap test
is Shape B on a vocabulary already in the repo: run CWE 4.20 -> a later CWE
release using MITRE's own mapping notes as gold. It reuses an existing catalog
builder and would validate or kill the shape in a session.

---

## 5. Consolidated: the law these candidates would add

Sections 2-4 discover new law candidate by candidate, which buries it. Six
items, collected so the pattern doc's diff is visible in one place. None is
authorized here; each names the candidate that would pay for it.

| # | Proposed law or amendment | Forced by | Status |
|---|---|---|---|
| L1 | **A conditional verdict tier.** `applies` / `does_not_apply` / **`applies_if`**, the third carrying an unresolved predicate whose payload is a question for a human, not a confidence value. | C8, and independently C9 (a DM ruling is the same shape) | Two unrelated domains need it, so the three-value tier is probably an artefact of ICPC (R7) |
| L2 | **Negative determinations need positive evidence.** ICPC omits irrelevant rubrics and the reducer discards negatives; in compliance the out-of-scope finding is the deliverable and must cite the exclusion or derogation producing it. | C8 | Direct contradiction of current prompt discipline, not an extension |
| L3 | **Ordinal aggregation as a second reducer algebra.** ICPC and CWE reduce to a ranked list by demotion; MDR reduces to a single grade by max() over rule outcomes. | C8 | Likely a family, not a special case (R8) |
| L4 | **Law 1 splits in two.** The *generated artifact* half (provenance: verified vs provisional) is universal; *never committed* is licensing-contingent. | C9 and C10 together | Strongest evidence in the document: one publisher supplies both poles — D&D SRD 5.1/5.2 is CC-BY-4.0 committable, MTG's Fan Content Policy forbids redistribution |
| L5 | **A second gold species: engine-executed truth.** Ground truth taken from what a system actually did, not what an annotator said. No annotator drift; narrower coverage. Belongs in law 6 beside labeled corpora. | C9 (FIREBALL's Avrae commands) | Different failure modes from human annotation, so it needs its own paragraph |
| L6 | **G6 plus the fixed-point test.** State item independence as a prerequisite, and add the screening question: can the reduce be written without iterating to a fixed point? Rank → ordinal max → interpreter, where the pattern owns the first two. | C10 | The only item that is a pure documentation edit; gated on R9 |
| L7 | **A third gold species: outcome-labeled.** Ground truth taken from whether the advice *won*, not from a label at all (17Lands GameData, tournament results). Strongest species available — it measures goodness, not agreement. Carries its own discipline rule: **outcome is not correctness**, because a single result is dominated by variance and population data reflects typical rather than optimal play. Valid in aggregate, never per-decision. | C10 (§3.4.1) | Extends L5's paragraph rather than replacing it; the "never per-decision" clause is the load-bearing half |
| L8 | **Statistic precedence.** Where a published statistic already answers the question, the model must not produce the number — its job shrinks to what statistics cannot do: explaining, reasoning about the specific instance rather than the population average, and handling states too rare to have data. | C10 (§3.4.1), generalised from the MTG keyword-parser finding | Applies to every candidate, not just MTG; the sharpest available defence against dressing up a lookup as a judgement |

Two observations from the collection itself:

- **L1, L2 and L3 all come from C8.** A single candidate would force three
  amendments, which is a stronger argument for building it than its rank-1
  yield score — and also the reason to be suspicious: one domain producing
  three laws may mean the domain is a poor fit rather than a rich one. R7 and
  R8 exist to tell those apart.
- **L4, L5 and L6 cost nothing to adopt.** They are corrections to how the
  pattern doc states what it already knows, discovered by screening rather
  than by building. They should not wait on any instance.

---

## 6. Ranking

Sorted by research yield (what the pattern learns), with commercial value as
the tiebreak — the inverse emphasis of the 09-02 document, deliberately.

| # | Candidate | Yield | Cost | Why here |
|---|---|---|---|---|
| 1 | **C8 Regulatory applicability (MDR Annex VIII)** | very high | medium | Forces three new laws (R7, R8, negative evidence); 4 clusters; strongest G5 of any candidate; commercially adjacent to 09-02 ranks #1/#3/#4. Held off rank 1 only by unverified G4 |
| 2 | **C1 OIICS** | very high | low | Only external-accuracy comparison available; 7 clusters; six figures of free gold; forces R5. Cheapest high-yield run |
| 3 | **C9 D&D 5e rules** | high | low | Free irrevocable vocabulary, 153,829 turns of engine-executed gold, zero stakes, publishable in full, and a repo consumer at 09-02 rank 30. Splits law 1 |
| 4 | **C2 EuroVoc** | high | medium | Settles R3 and R4; 22-language gold is unique; multi-label stresses the secondary tier |
| 5 | **R6 via CWE version bump** | medium | very low | Validates Shape B inside an existing instance; a session, not an FR arc |
| 6 | **C5 ICD-10/11** | medium | high | Commercially first (09-02 rank #2) but gold needs a data use agreement; the version bump is a dated buying event |
| 7 | **C4 MedDRA** | low research / very high commercial | high | Customer engagement, not a research vehicle; law 1 mandatory |
| 8 | **C3 LOINC crosswalk** | medium | medium | Best Shape A proof with a named owner and real cost |
| 9 | **C6 ATT&CK** | low | low | Cheap but likely teaches nothing new — too close to CWE |
| 10 | **C7 CPC patents** | low | medium | Unlimited gold, but only a truncated and unrealistic task passes G2 |

Not ranked, deliberately:

| Candidate | Disposition |
|---|---|
| **C10 MTG rules adjudication** | Fails G6. Document as the worked negative example (section 3.4); do not build. |
| **C10a MTG combo detection** | Genuinely viable with 30,000+ combos of public gold, but it is **cross-product census**, not coded classification. Route it to that pattern rather than this one. Carries a falsifiable test: rediscovery of held-out combos. |
| **C10b MTG deck legality** | Anti-use-case: deterministic, no judgement, no evidence to quote. Worth naming so nobody proposes it. |
| **C10c MTG draft pick** | Cleanest gate profile in MTG and it *does* pass G6 (§3.4.1) — unranked only because the pick ratings already exist statistically, so L8 caps the model's contribution to synergy reasoning and abstention. |
| **C10d MTG sideboarding** | Passes on a per-deck generated catalog (the player's own 75). Best in-game fit; unranked because it has no research yield beyond validating L7. |
| **C10e MTG deck construction** | Best MTG fit of all and **belongs to schema-driven extraction**, not here. Would be that pattern's second instance. Routed, not ranked. |

The two second-pass candidates displace most of the first pass. Both were
reachable from the pattern doc's own "fits" list and neither was on it, which
is itself a finding: the list enumerates *taxonomies* and therefore misses
domains where the controlled vocabulary is a **rulebook** — statute or game
rules — rather than a classification. Rulebooks score highest on G5, the gate
the pattern's own law 5 says pays best.

---

## 7. Recommended next moves

1. **Verify C8's G4 before anything else.** One afternoon: does EUDAMED expose
   intended-purpose text alongside declared risk class in bulk, and how noisy
   is manufacturer self-declaration? This single unknown decides whether the
   highest-yield candidate is buildable or blocked. Cheapest question in the
   document with the largest consequence.
2. **C1 (OIICS) as instance three regardless.** Free vocabulary, free
   six-figure gold corpus, published SOTA to measure against, 7 clusters. It is
   simultaneously the cheapest instance and the only external accuracy check
   available, and it does not depend on step 1.
3. **Pair it with R2 (calibration).** The gold corpus is large enough to fit
   and validate an abstention threshold; do not run a large corpus and then
   discard the calibration data.
4. **C9 (D&D) as the public reference instance, not as research first.** Its
   research yield is real but its distinctive value is that it is the only
   instance that can be published whole — code, catalog, fixtures, transcripts.
   Sequence it after C1 so there is a third instance's worth of law to show off.
5. **R6 as a one-session spike** — Shape B on a CWE version bump reuses an
   existing builder and either earns the shape a paragraph in the pattern doc
   or deletes it from this document.
6. **Add G6 and the fixed-point test to the pattern doc.** This is the only
   recommendation here that is a documentation edit rather than a build, and it
   is the highest value per hour in the document: the pattern's stated
   prerequisites currently admit MTG, and its "what does not transfer" section
   has no worked example. Both gaps close with one short section and the
   section 3.4 material. Subject to R9 first — the test is derived from a
   single domain.
7. **Record the G1 failure for CPV** wherever N11 is next considered; an idea
   ranked on market size is being screened out on vocabulary structure, and
   that reasoning should not have to be rediscovered.
8. **Do not build C6 (ATT&CK)** on cheapness alone. The rule of two is
   satisfied; a third instance is worth building only if it stresses a law,
   and ATT&CK is a copy-adapt of CWE with a different noun.

**Seed 1:** every gate in section 1 except G4 is a property of the
*vocabulary*. G4 is a property of the *world* — whether someone already paid
humans to label a corpus. If gold economics dominate instance cost this
heavily, the pattern's real selection rule is "follow the labeled corpora", and
the honest catalog to maintain next to the pattern doc is not a list of
taxonomies but a list of public gold sets.

**Seed 2:** C8 and C9 are a statute and a game rulebook, and they scored first
and third. Both are **rulebooks rather than classifications** — vocabularies
whose authors wrote down the adjudication procedure, not just the labels. Law 5
says mechanizing the standard's own rules "beats any heuristic about model
behavior"; if that is true, the pattern's best domain is not taxonomies at all,
and `coded-classification` may be the wrong name for it.

**Seed 3:** seed 2 wants rulebooks; MTG is the most rule-dense rulebook
available and is out of scope. The two facts together say the axis is not rule
*density* but rule *composition*: the pattern wants a rulebook whose rules are
evaluated **independently and then aggregated**, and breaks on one whose rules
are evaluated **against each other**. MDR's "strictest rule governs" aggregates;
MTG's layers compose. If that is the real axis, then G5 and G6 are not two
gates but two ends of one measurement, and screening a candidate means asking a
single question: *how do this standard's own rules combine?*

**Seed 4:** this document was written to screen candidates *for one pattern*,
and its most reusable output turned out to be §3.4.1 — a table saying which
sibling pattern each MTG sub-task belongs to, including "none of them". The
worst-fitting candidate produced the most routing information, because a domain
only reveals where the boundaries are when it crosses several of them. If that
holds for the next domain too, the missing artefact beside
`reference/patterns/` is not a better index (that gap is now closed) but a
**screening procedure** — gates, the fixed-point test, statistic precedence,
gold species — that takes an arbitrary domain and names the pattern, or names
nothing. The pattern library currently describes destinations and has no router.

---

## Sources for external claims

- OIICS competition, dataset size and accuracy figures: NIOSH/NASA Tournament
  Lab/Topcoder 2018 injury-narrative NLP competition; public dataset mirror at
  `huggingface.co/datasets/mayerantoine/injury-narrative-coding`; OIICS at
  `wwwn.cdc.gov/wisards/oiics/`.
- EuroVoc size, JEX/JRC-Acquis and EURLEX57K: JRC EuroVoc Indexer JEX
  (arXiv 1309.5223); "Extreme Multi-Label Legal Text Classification: A case
  study in EU Legislation" (arXiv 1905.10892).
- MDR Annex VIII rule count, the four rule groups and the "strictest rule
  applies" implementing rule (Annex VIII Chapter II), plus the described
  two-pass practice for Rules 14-22: TUV SUD Annex VIII reference, BSI
  Compliance Navigator MDR slides, and practitioner guides
  (`meddeviceguide.com`, `zechmeister-solutions.com`).
- FIREBALL dataset size (nearly 25,000 sessions, 153,829 turns), Avrae-captured
  true game state and executable commands: "FIREBALL: A Dataset of Dungeons and
  Dragons Actual-Play with Structured Game State Information", ACL 2023
  (arXiv 2305.01528); data at `huggingface.co/datasets/lara-martin/FIREBALL`,
  code at `github.com/zhudotexe/FIREBALL`.
- SRD 5.1 released under CC-BY-4.0 on 2023-01-27 and SRD 5.2 on 2025-04-22,
  irrevocably: `media.wizards.com/2023/downloads/dnd/SRD_CC_v5.1.pdf`,
  D&D Beyond SRD page, Wikimedia Commons SRD v5.2 (2025).
- Scryfall bulk data (the `Oracle Cards` export, one card per Oracle ID,
  refreshed every 12 hours): `scryfall.com/docs/api/bulk-data`. The card count
  is stated only as "tens of thousands" because the searches did not confirm a
  figure — do not quote a number without checking.
- Commander Spellbook (30,000+ combos, PostgreSQL + Django REST API, open
  source): `commanderspellbook.com`,
  `github.com/SpaceCowMedia/commander-spellbook-backend`.
- 17Lands public datasets (CSV GameData with per-game outcomes, DraftData with
  pools and picks, replay data, per event type): `17lands.com/public_datasets`;
  tooling at `github.com/oelarnes/spells` (Polars) and the `mtgr` R package.
  **Not verified:** the licence and permitted-use terms of those datasets, or
  whether tournament decklist aggregators permit bulk use. Both matter before
  any MTG work and neither was checked.
- Wizards Fan Content Policy forbidding verbatim copying and reposting of
  Wizards IP, naming Magic cards:
  `company.wizards.com/en/legal/fancontentpolicy`.
- MTG Comprehensive Rules structure is cited from general knowledge — the layer
  system at CR 613, dependency at 613.8, state-based actions at 704, golden
  rule at 101. **Verify the numbering against the current CR release** before
  quoting it anywhere load-bearing; the sections are stable but the numbering
  has moved historically.
- MedDRA, LOINC, ICD, CPV, SNOMED CT and CPC properties are stated from
  general knowledge of those vocabularies and should be verified against
  current license terms and release structure before any FR is authored.
- **Unverified and load-bearing:** EUDAMED as a gold source for C8 (whether
  intended-purpose text is available in bulk alongside declared risk class),
  and the MDCG borderline/classification manual as a worked-example corpus.
  Step 1 of section 7 exists to settle these.
