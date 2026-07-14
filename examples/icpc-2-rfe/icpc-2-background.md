# ICPC-2 Background (Reason for Encounter Focus)

## Sources in hand (FR-722 provenance ledger)

| Local file | Identity | Tier | Notes |
|---|---|---|---|
| `tmp/icpc-wonca-dec16.pdf` (untracked, gitignored) | WONCA "International Classification of Primary Care" introduction leaflet, 5 pages, Dec 2016 (PDF author metadata: Luisa Pettigrew) | 2/4 — official WONCA background, **non-normative** | Episode-of-care rationale, ICPC-vs-ICD positioning, one sample page. Contains NO rubric text, definitions, or inclusion/exclusion terms. Licensing contact: ceo@wonca.net |
| WHO ICPC-2 page | Status + 17-chapter / 7-component structure statement | 2 | https://www.who.int/standards/classifications/other-classifications/international-classification-of-primary-care |

**Tier-1 source located online (2026-07-14):** the Norwegian Directorate of
Health maintains the official ICPC-2e English repository **on behalf of
WICC/WONCA** at
https://www.helsedirektoratet.no/digitalisering-og-e-helse/helsefaglige-kodeverk/icpc/icpc-2e--english-version.
Current normative electronic edition: **ICPC-2e-v7.0** (2018-02-20), a
~290 kB zip in **Excel and ClaML** with per-rubric `short title, inclusion,
exclusion, criteria, consider, note` — exactly the fields the FR-722 catalog
needs. This is Tier 1 (WICC-delegated master). Lookup convenience (Tier 3):
FinnKode browser + API + Excel export at
https://finnkode.helsedirektoratet.no/icpc2/chapter (Norwegian-localized
annual edition; the v7.0 zip is the frozen international English master).

**License:** "ICPC is copyright property of Wonca"; policy at
http://www.ph3c.org/4daction/w3_CatVisu/en/rules-%26-ethics.html?wCatIDAdmin=1101.
Judgement F5 stance unchanged: derive the catalog locally from v7.0
(downloaded to tmp/, untracked), commit only codes + titles + paraphrased
cues + row/page pointers — never the verbatim rubric text. Rows checked
against v7.0 may be marked `provenance_status: verified`.

## What ICPC-2 is
The International Classification of Primary Care, 2nd edition (ICPC-2), is a primary care classification maintained by the WONCA International Classification Committee (WICC) and accepted by WHO in the WHO Family of International Classifications.

ICPC-2 is designed to classify data from primary care encounters, especially:
- reason for encounter (RFE)
- problems and diagnoses managed
- interventions and processes of care
- these elements over time in an episode-of-care structure

## Why RFE matters
RFE captures the patient-side intent for the contact (what the patient presents with or asks for), which is often different from the clinician assessment or final diagnosis. In ICPC-2, separating RFE from diagnosis is a core feature, not a data-entry detail.

Using RFE consistently supports:
- patient-centered documentation
- better primary care analytics (demand patterns, triage, access)
- safer interpretation of symptom-first visits where diagnosis is not yet certain

## Classification structure
WHO describes ICPC-2 as a biaxial classification with:
- 17 chapters (organ/system and domain groupings)
- 7 components in each chapter

The seven components are:
1. symptoms and complaints
2. diagnostic, screening and preventive procedures
3. medication, treatment and procedures
4. test results
5. administrative
6. referrals and other reasons for encounter
7. diseases

Typical chapters include general/unspecified, respiratory, psychological, musculoskeletal, pregnancy and family planning, and social problems.

## Practical classification rules
These are operational rules commonly used in ICPC-2 implementation in primary care.

1. Code the encounter from a primary care perspective.
- Do not force specialist-level detail when it is not clinically established in the encounter.

2. Capture encounter elements separately.
- RFE: patient reason for coming now.
- Process/intervention: what was done.
- Problem/diagnosis: clinician assessment at that time.

3. Be temporally honest.
- Use symptom/complaint coding when uncertainty remains.
- Move to a disease/problem code once diagnosis is sufficiently established.

4. Preserve episode-of-care continuity.
- Link repeat visits for the same health problem in one episode.
- Allow the coding to evolve as certainty changes across visits.

5. Keep patient reason distinct from clinician conclusion.
- Do not overwrite RFE with the diagnosis.
- Both are analytically meaningful and should coexist.

6. Prefer the most specific valid rubric supported by available evidence.
- Avoid over-specification beyond what the encounter supports.

## Suggested minimal data model for an ICPC-2 RFE workflow
For each contact, store at least:
- contact_id
- patient_id
- episode_id
- encounter_datetime
- rfe_code (ICPC-2)
- process_codes (0..n ICPC-2 process codes)
- problem_or_diagnosis_code (0..n ICPC-2 problem codes)
- certainty_state (for local use, optional)

This supports both single-encounter reporting and longitudinal episode analysis.

## Coding quality checklist
Use this quick check during implementation and audit:

- Is RFE coded in patient-facing terms?
- Is diagnosis coded only to the certainty level reached today?
- Are process actions coded separately from diagnosis?
- Is the encounter linked to the correct ongoing episode?
- If diagnosis changed, is the prior symptom-stage history preserved?

## Implementation guidance
- Start with high-volume primary care scenarios (respiratory, musculoskeletal, psychological, preventive care).
- Create local coding examples for common ambiguous cases.
- Run periodic inter-rater consistency checks.
- If mapping to ICD or SNOMED, stabilize ICPC-2 coding rules first, then map.

## Source basis used for this background
Use this source hierarchy when implementing or auditing code:

1. Normative (authoritative for rubric content)
- WONCA WICC-governed ICPC-2 publication content.
- WICC resource hub: https://www.globalfamilydoctor.com/groups/workingparties/wicc.aspx
- WICC ICPC explainer PDF reference: https://www.globalfamilydoctor.com/site/DefaultSite/filesystem/documents/Groups/WICC/International%20Classification%20of%20Primary%20Care%20Dec16.pdf

2. Official status and structural confirmation
- WHO ICPC-2 page (acceptance in WHO-FIC, purpose, structure):
  https://www.who.int/standards/classifications/other-classifications/international-classification-of-primary-care

3. Implementation lookup aids (non-normative)
- ICPC-2 browser: https://icpc2.icpc-3.info/

4. Secondary orientation only (non-authoritative)
- Wikipedia overview: https://en.wikipedia.org/wiki/International_Classification_of_Primary_Care

Practical provenance rule:
- If sources differ, prioritize WONCA WICC official ICPC-2 publication content.
- Treat browser and secondary pages as convenience layers, not final authority.
