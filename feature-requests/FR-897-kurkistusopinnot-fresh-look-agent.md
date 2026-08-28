# Feature Request: FR-897 Kurkistusopinnot Fresh-Look Agent

**Priority:** MEDIUM
**Type:** Feature
**Status:** Judged — approved with revisions folded 2026-08-27
**Effort:** 3 days
**Requested:** 2026-08-27
**First consumer / first event:** the operator preparing the next strategy
conversation about Finnish higher-education taster studies; at that moment the
operator reads a dated evidence dossier and a deliberately contrarian synthesis
before proposing what kurkistusopinnot should become.
**Research:** [FR-897.research.md](FR-897.research.md)
**Judgement:** [FR-897-kurkistusopinnot-fresh-look-agent.judgement.md](FR-897-kurkistusopinnot-fresh-look-agent.judgement.md)

**Prior art:** FR-892 (`corpus_census` discover-extract-map-reduce skeleton and
fail-closed ledger), FR-894 (the six-stage corpus map-reduce contract), the
83-map/11-reduction Mercury run in `examples/surplus/diary-discourse-analysis/`,
FR-205 (`fi_domain_crawl`, useful discovery precedent but not a sufficient
completion contract), and QAA's annual Access to HE data collection across
QAA, UCAS, ESFA, and HESA.

## Summary

Create a retained research instrument under
`examples/surplus/kurkistusopinnot-fresh-look/` that freezes a bounded,
multilingual sample of Finnish university and university-of-applied-sciences
taster-study evidence; maps one typed Mercury-2 reading over each source;
reconciles source identity, evidence layers, coverage, and counts in Python;
maps six orthogonal Mercury-2 perspective memoranda over the reconciled
dossier; and spends one stronger-model call on a final cited synthesis.

The output is not a ranking or an effect evaluation. It is an outside-in
account of what the current category contains, which learner decisions it
serves, where access conditions and institutional incentives conflict, what
published evidence can and cannot support, and which falsifiable hypotheses
deserve a human strategy conversation.

## Value Statement

A higher-education planner gets a fresh, challengeable account grounded in
every collected source rather than one fluent opinion or a search-engine sample,
while the complete source ledger remains available to contradict the synthesis.

## Problem

The closed brief
([fr-897-kurkistusopinnot-fresh-look.md](research-briefs/fr-897-kurkistusopinnot-fresh-look.md))
shows that no dated, source-reconciled account of Finnish kurkistusopinnot exists
in this repository. The vocabulary is unstable: provider pages mix
`kurkistuskurssi`, `tutustumiskurssi`, open higher-education courses, MOOCs,
pathway studies, secondary-school cooperation, study-skills courses, and career
guidance. Treating all of them as one intervention would manufacture a category
before examining it.

A live run of the existing `web-research` graph demonstrated the wrong shape:
it issued several searches, reached its iteration ceiling, retained only the
last query result in state, and timed out in synthesis. It produced activity but
no reconciled report. The generic FR-892 `corpus_census` graph proves the right
coverage boundary, but its shipped map contract is intentionally narrow: one
free-form judgement and one evidence span, with a fixed Haiku model. Encoding
this domain's multidimensional evidence matrix inside that string would make the
deterministic reducer parse prose and would evade rather than reuse its type
contract.

The missing capability is therefore a domain research instrument using the
proven corpus topology, not a new framework primitive and not a generic schema
override for `corpus_census`.

## Ideal Result

One bounded command produces a run-dated folder containing:

1. a source manifest with URL, owner, retrieval time, content hash, source
   layer, institution identity, query provenance, and fetch status;
2. one typed, evidence-spanned primary reading for every fetched source;
3. mechanical reconciliation proving that every frozen source is represented
   exactly once or has an explicit fatal error;
4. six separately attributable perspective memoranda with disagreement intact;
5. a compact Finnish-language fresh-look report whose every substantive claim
   links to source IDs and whose hypotheses state what evidence would falsify
   them; and
6. a run record showing corpus bounds, model pins, call forecast versus actual
   calls, duration, and the three positive-control results.

The operator can move from any synthesis claim back to the exact short source
span that supports it. A missing source layer, failed fetch, unsupported effect
claim, or failed positive control makes the run visibly incomplete; it cannot be
presented as a national census.

## Raw-Output Read Evidence

Read 2026-08-27 before planning. These are concrete source details, not model
summaries of an unseen corpus:

1. **Metropolia's live kurkistuskurssit index** mixes explicit degree/occupation
   probes (`Minustako kätilö?`, `Minustako osteopaatti?`) with generic first aid,
   stress, sustainability, and ecological-values courses. Two English `Peek
   courses` appear in a separate section. The first analytical problem is
   category boundary and language visibility, not course counting.
2. **Vaasa University's 2026-2027 tutustumiskurssit page** says the courses are
   free and online, but registration normally requires online-banking
   credentials, followed by account activation, MFA, and Moodle registration.
   Later credit recognition is described only as optional studies in the same
   degree field. "Online and free" therefore does not exhaust access or
   progression conditions.
3. **Humak's page** opens the courses to anyone, makes them free and pass/fail,
   and promises credit transfer if the learner later starts a Humak degree.
   Exploration, earned credit, and institution-specific recruitment are present
   in one small offer.
4. **TAMK's 9 September 2022 provider reflection** reports that spring
   participants found four courses useful and praised podcasts, but also says a
   self-paced nonstop implementation should include activating meetings, for
   example monthly. Its target group includes second-stage students, people
   without a study place, career changers, unemployed retrainers, and current
   students. Flexibility and supported participation are not synonyms.
5. **Koulutuskuntayhtymä Tavastia's live link hub** says every upper-secondary
   learner would benefit from one higher-education course, while the actual
   price depends on school-provider agreements; some MOOCs are free to consume
   but charge for credit registration. The same page mixes taster, open, MOOC,
   and pathway offers. Geography and institutional partnership can determine
   what "free choice" means.
6. **Lukiolaisbarometri 2024** reports 13,236 respondents from 111 schools and
   says 59% experience studies as mentally burdensome; support needs differ by
   minority status and parents' education or labour-market position. This is
   relevant learner context, not evidence that kurkistusopinnot cause or cure
   those outcomes. Any synthesis that simply recommends more coursework has
   missed the control evidence.
7. **QAA's Access to HE statistics page** confirms annual collection with UCAS,
   ESFA, and HESA to report learner achievements and progress. It is a precedent
   for evidence-layer reconciliation, not evidence that an equivalent Finnish
   outcome dataset currently exists.

## Proposed Solution

### 1. Ownership and delivery boundary

Author one graph through `scripts/author.sh` under
`examples/surplus/kurkistusopinnot-fresh-look/`. Retain it with its public-safe
pilot evidence as a reproducible research instrument, following
`diary-discourse-analysis`.

`projects/opinto_ohjaus/` is a nested Git repository. This FR may name it as the
consumer but must not write, stage, or commit anything inside it. Product
adoption there requires a separate change in that repository.

The new graph reuses these FR-892/FR-894 contracts unchanged: freeze before
inference, collector-owned source IDs, fail-closed reconciliation, one retained
primary row per fetched source, no silent map dropout, and provider/model/run
provenance. It does not reuse the unchanged `corpus_census` executable because
this instrument requires a typed four-field source-reading schema, four distinct
evidence layers, six fixed lens prompts, three domain positive controls, and a
Finnish report renderer. Those requirements cannot be represented by
`corpus_census`'s one free-form judgement plus one evidence span without parsing
model prose in the reducer.

If implementation requires changing `examples/demos/corpus_census/`, YAMLGraph
runtime, tool-slot semantics, a generic prompt/schema override, or provider
support, stop and file a separate researched FR.

### 2. Freeze a bounded source population

A Python collector owns identity and arithmetic. Before the first paid model
call it must:

- load a run-versioned configuration containing Finnish, Swedish, and English
  discovery terms;
- freeze an official list of Finnish universities and universities of applied
  sciences with institution IDs and approved domains;
- execute a fixed query budget per institution and retain every query/result
  pair, including zero-result and error records;
- add a bounded, curated manifest for learner, participation/progression, and
  independent evaluation/research sources;
- normalize and deduplicate URLs, fetch text, record HTTP status, retrieval
  time, content hash, byte count, language, owner, and source layer; and
- reject the run before inference above 96 fetched sources, the declared byte
  budget, or the wall-clock/query ceilings.

The frozen institution authority is the Finnish Ministry of Education and
Culture's lists retrieved on 2026-08-27:

- `https://okm.fi/yliopistot`: 13 universities in the Ministry's
  administrative branch;
- `https://okm.fi/ammattikorkeakoulut`: 22 universities of applied sciences in
  the Ministry's administrative branch.

The committed snapshot path is
`examples/surplus/kurkistusopinnot-fresh-look/config/institutions.yaml`. Each of
its 35 in-scope rows must contain a repo-stable ASCII `institution_id`, the
official name, `institution_type`, authority URL, authority retrieval date, and
at least one approved domain derived from the Ministry's institution link.
Aliases require row-level provenance. The snapshot records
Maanpuolustuskorkeakoulu, Poliisiammattikorkeakoulu, and Högskolan på Åland as
explicit out-of-scope adjacent institutions because their governing authorities
fall outside this frozen Ministry population. The in-scope count is derived from
rows with `in_scope: true` and must equal 35. The run records the SHA-256 of the
exact UTF-8 snapshot bytes; a missing field, count mismatch, or checksum mismatch
fails before discovery.

Every institution receives a discovery record. `no_candidate_found`,
`fetch_failed`, and `not_queried` are different states. The instrument may call
the result a national bounded scan only when every frozen institution was
queried; it may call itself a census only if the stronger FR-894 invariants are
actually proved for a defined offer population.

Run labels are mechanical:

- `national bounded scan` requires a discovery record for all 35 in-scope
  institutions and no `not_queried` state;
- `four-layer pilot` additionally requires at least one source in each of
  provider, learner, participation/progression, and evaluation;
- any missing source layer or unqueried institution forces `sample` or
  `incomplete`, never `national bounded scan` or `four-layer pilot`;
- `census` is prohibited unless the run proves all FR-894 invariants for an
  explicitly defined offer population.

Full fetched page text stays under `tmp/`. Committed artifacts retain hashes,
metadata, and short evidence spans only.

### 3. Map typed Mercury source readings

Map one `inception/mercury-2` call at low temperature over each fetched source.
The prompt has one job: extract source-supported observations, not recommend a
policy. Its structured result has four top-level fields:

```yaml
source_index: 17
classification:
  source_layer: provider | learner | participation | evaluation
  offer_families: [taster, open_study, mooc, pathway, secondary_cooperation]
observations:
  - dimension: target_group | decision_moment | delivery | language | access_requirement | price | credit | guidance | equity | progression
    value: "Online-banking credentials are the normal registration route."
    evidence_span: "Ilmoittautumispalvelun käyttöön tarvitaan verkkopankkitunnukset."
evidence_assessment:
  stated_objective: "Support planning of further studies."
  reported_outcome: ""
  evidence_kind: provider_claim | feedback | descriptive_statistic | evaluation | none
  uncertainty: "No participation or progression count is published on this page."
  abstained: false
  abstain_reason: ""
```

Collector-owned identity is authoritative. Model-emitted indexes and all
evidence spans are claims until deterministic reconciliation validates them
against the frozen source text.

### 4. Reconcile and reduce without losing primary evidence

An LLM-free Python boundary must reject unknown or duplicate source indexes,
missing map results, map error rows, evidence spans absent from normalized
source text, invalid enums, and model-supplied totals. It computes institution,
institution-type, language, offer-family, source-layer, query, fetch, and
abstention coverage.

The reducer then builds at most 12 deterministic batches from the primary
readings. A second Mercury-2 map writes one evidence memo per batch. Batch memos
may identify patterns and contradictions but cannot replace the primary rows.

### 5. Ask six genuinely different questions

Map six fixed Mercury-2 lens prompts over the reconciled batch memos:

1. **Learner decision journey:** which uncertainty and decision moment does
   each offer actually serve?
2. **Access and equality:** who pays hidden time, identity, language, geography,
   prerequisite, or guidance costs?
3. **Pedagogical authenticity:** does the learner encounter real study practice
   or mainly institution/occupation description?
4. **System incentives:** where do exploration, recruitment, credit transfer,
   pathway selection, and throughput incentives align or conflict?
5. **Evidence skeptic:** which effect claims are measured, provider-reported,
   merely stated, or absent?
6. **Category challenger:** state the strongest case that `kurkistusopinnot` is
   the wrong unit of analysis and name a better learner-centred unit.

Each memo must cite valid source IDs from at least two source layers, preserve
one contradiction, and express proposals only as falsifiable hypotheses with
the evidence needed to test them. It may abstain when its evidence threshold is
not met.

### 6. Spend once on synthesis

After code validates all six lens memos, make exactly one
`anthropic/claude-sonnet-4-5` synthesis call. The typed report contains:

- category boundary and vocabulary map;
- observed offer patterns;
- contradictions and unresolved disagreements;
- underserved learner moments or groups, explicitly marked as inference;
- no more than six fresh hypotheses, each with source IDs, confidence,
  counterevidence, and a falsifier;
- an evidence agenda stating what cannot be concluded from public sources; and
- a short strategy-conversation brief in Finnish.

The tail cannot introduce a source ID, count, institution, or effect claim not
present in the reconciled dossier. It cannot rank institutions, issue admission
advice, or use causal language for descriptive evidence.

### 7. Artifact and positive-control contract

Write a run-dated proof folder containing:

- `source-ledger.jsonl` (public-safe source metadata and short spans);
- `dossier.json` (primary readings, batch memos, lens memos, reconciliation);
- `fresh-look.md` (human report linked to source IDs); and
- `run-evidence.txt` (command, git SHA, corpus hash, models, calls, duration,
  ceilings, and validation results).

Three post-run positive controls are withheld from runtime prompts and checked
against typed output:

1. the Vaasa source must expose an identity/platform access requirement rather
   than only `online` and `free`;
2. the Tavastia source must expose at least three distinct offer families rather
   than one synthetic `kurkistus` class; and
3. the Lukiolaisbarometri source must remain learner context, not be promoted to
   direct kurkistusopinnot effect evidence.

Failure of any control invalidates the live pilot. Passing them is necessary,
not proof that the novel hypotheses are true.

## Model and Cost Contract

The maximum paid-call forecast is:

```text
96 source readings + 12 batch memos + 6 lens memos + 1 synthesis = 115 calls
```

All 114 map/reduction calls pin `inception/mercury-2`; only the final synthesis
pins `anthropic/claude-sonnet-4-5`. Discovery, fetching, reconciliation, counts,
coverage, citation validation, canaries, and rendering are LLM-free. The
collector refuses to start inference if its forecast exceeds 115 calls.

## Acceptance Criteria

- [ ] AC-01: The promoted research record passes
  `scripts/research_preflight.py --verify-artifact`; all five solution classes
  are dispositioned in this FR.
- [ ] AC-02: RED first — deterministic failing tests cover source deduplication,
  query/fetch state distinctions, ceiling refusal, missing/duplicate/unknown map
  indexes, invalid evidence spans, map-error rejection, citation reconciliation,
  and all three positive controls.
- [ ] AC-03: The graph and prompts are authored only through
  `scripts/author.sh`; the accepted authoring report records lint and a live
  Mercury smoke over a bounded fixture.
- [ ] AC-04: The collector freezes the 35-row Ministry population at the exact
  path and schema above, validates type/ID/domain/retrieval metadata and
  checksum, records every fixed query and outcome, and refuses inference above
  the frozen source/byte/query/time/call ceilings.
- [ ] AC-05: Every source-reading, batch-memo, and lens-memo node explicitly pins
  `provider: inception`, `model: mercury-2`, and low temperature. The only other
  LLM call is one pinned Sonnet synthesis after reconciliation.
- [ ] AC-06: Source readings use the typed four-field contract above, support
  abstention, and carry exact short spans; tests prove spans are present in the
  normalized fetched source.
- [ ] AC-07: The LLM-free reducer proves one result per fetched source, retains
  all primary rows, computes all counts from the frozen manifest, and fails the
  run on any skipped/error/missing result.
- [ ] AC-08: Six lens memos are present exactly once, cite only valid source IDs
  from at least two source layers or explicitly abstain, preserve disagreement,
  and attach a falsifier to every hypothesis.
- [ ] AC-09: The final report contains the frozen sections, contains no unknown
  source IDs or model-authored totals, distinguishes observation/inference/
  hypothesis, and contains no institution ranking, admission decision, or
  unsupported causal claim.
- [ ] AC-10: Fixture smoke proves count-in equals count-out and artifact
  creation. A bounded live Finnish pilot passes all three positive controls and
  applies the exact `national bounded scan`, `four-layer pilot`, `sample`,
  `incomplete`, and prohibited-`census` rules above.
- [ ] AC-11: No fetched full-page text, personal data, credentials, or private
  learner data is committed; committed exact spans are short and source-linked.
- [ ] AC-12: No file inside the nested `projects/opinto_ohjaus/.git` repository
  is changed. The README names it only as the first downstream consumer.
- [ ] AC-13: Tests carry valid `@pytest.mark.req(...)` markers, requirement
  coverage passes, a changelog fragment and FR implementation record are added,
  the retained instrument is linked from `examples/surplus/README.md`, and a
  diary reflection with a Seed closes the task.

## Deliverables

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/authoring-briefs/fr-897-kurkistusopinnot-fresh-look.md` |
| D-2 | `examples/surplus/kurkistusopinnot-fresh-look/graph.yaml` and YAML prompts |
| D-3 | Collector, reconciliation, batching, canary, and writer tools under the instrument's `nodes/` |
| D-4 | Bounded local fixture plus deterministic unit tests |
| D-5 | Run-dated public-safe live proof: ledger, dossier, report, run evidence |
| D-6 | README and `examples/surplus/README.md` index entry |
| D-7 | Changelog, requirement traceability, FR update, diary reflection |

## Alternatives Considered

| Class | Disposition | Reason |
|---|---|---|
| Unchanged FR-892 `corpus_census` | Architecture selected; direct use rejected | Reuse freeze, collector-owned IDs, fail-closed reconciliation, no-drop ledger, and provenance unchanged. Its one-judgement/one-span Haiku contract cannot type four evidence layers, the four-field source reading, six lens prompts, positive controls, or Finnish rendering. No prose-in-a-cell workaround and no change to the shared demo. |
| Schema/process inventory | Folded | Four evidence layers, explicit absence, source spans, and inventory-before-interpretation become hard contracts. |
| OS process boundary and append-only logging | Folded | External calls and ceilings are durably recorded, but a separate process framework would duplicate graph orchestration. |
| Single-institution, provider-only proof | Folded as fixture; rejected as result | Useful for TDD, but it cannot answer the witnessed national/category question and would reproduce search-sample bias. |
| QAA national reporting model | Precedent only | Proves multi-source annual reconciliation; Finland's public data availability must be measured rather than assumed, and this FR cannot create institutional data-sharing authority. |
| Existing `fi_domain_crawl` | Rejected as owner | It caps ten pages, lets search/fetch failures collapse toward empty output, and ends in one monolithic summary without source reconciliation. Its URL filtering/fetch ideas may be reused after fail-closed repair in the new instrument. |
| Existing `web-research` agent | Rejected | The live witnessed run lost earlier query result sets and timed out in synthesis without a dossier. |
| Manual literature review only | Rejected as completion; retained as audit | Human raw reads define controls and judge hypotheses, but do not prove bounded population coverage or count-in/count-out. |

## Out of Scope

- Surveys, interviews, private learner records, or institution-internal data.
- Causal effectiveness claims, institution rankings, admissions advice, or
  automated decisions about learners.
- A public service, recurring crawler, dashboard, RAG index, or UI.
- Changes to YAMLGraph runtime, map semantics, provider support, generic prompt
  or schema overrides, or the shipped `corpus_census` graph.
- Writing into or committing on behalf of the nested `opinto_ohjaus` repository.
- Treating a bounded public-web scan as a complete national offer census.

## Risks and Stops

- **Search recall:** bounded web discovery cannot prove every offer was found.
  Stop calling the artifact a census; report institution/query coverage.
- **Category contamination:** adjacent open/pathway/MOOC offers may swamp true
  tasters. Preserve multi-label classification and the category-challenger lens.
- **Provider-claim dominance:** public pages mostly describe intent. Keep effect
  evidence empty unless a participation, evaluation, or outcome source supports
  it.
- **Freshness theatre:** six fluent memos can still share one model prior. The
  fixed lenses, source-layer citation floor, forced opposite, falsifiers, and
  human review reduce this risk; they do not eliminate it.
- **Scope growth:** if implementation needs a generic corpus schema override or
  framework change, stop and file a separate researched FR.

## Related

- [FR-897.research.md](FR-897.research.md)
- [Research brief](research-briefs/fr-897-kurkistusopinnot-fresh-look.md)
- [FR-892](FR-892-corpus-census-pipeline-injected-adapters.md)
- [FR-894](FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md)
- `reference/patterns/corpus-map-reduce.md`
- `examples/surplus/diary-discourse-analysis/`
