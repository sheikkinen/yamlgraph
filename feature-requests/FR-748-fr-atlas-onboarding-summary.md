# FR-748: FR Atlas — the project as told by its FRs, for a new person

**Status:** Completed
**Type:** Feature (new demo: `examples/demos/fr-atlas/`)
**Effort:** 1 day
**Requested:** 2026-07-18
**Judged:** 2026-07-18 — approved; both corpora measured before
authority, one pin protects the FR's own graveyard AC
**First consumer / first event:** a human introducing the project to a
new person via its FR history; first event = the next onboarding
conversation, opened with a generated atlas instead of a repo tour.

## Ideal Result

Any project with a `feature-requests/` folder can produce, on demand,
one readable document that tells a newcomer what the project is through
what it built and why: 8–15 theme arcs ordered by what's alive, each
naming its FRs (verbatim status tags) and the modules it shaped, opened
by a 3-paragraph story of the project, closed by the graveyard — the
rejections that taught the doctrine. The newcomer finishes it knowing
where the bodies are buried and where the work is moving, without
reading 700 files.

## Problem

The FR corpus (~720 files in yamlgraph, ~400 in ninchat_voice) is the
project's true history — decisions, failures, doctrine graduations —
but it is query-blind for a newcomer: no grouping, no narrative, no map
from themes to modules. Existing tools cover other axes:
`scripts/fr_board.py` (FR-740) shows FRs *in motion*;
`examples/demos/recap` (FR-700) shows a *time window* of git motion;
FR-737's hook retrieves *point* precedents. Nothing renders the corpus
as an onboarding narrative.

**Prior art (dispositioned):** recap (FR-700–704) — the pipeline
pattern this FR copies: deterministic collection, bounded judgements,
code-side joins, verbatim status tags, silent-drop lessons; fr_board
(FR-740) — the parse infrastructure and the F7 lesson (no committed
artifact whose only reader is its generator); FR-737 — IDF noun
machinery reusable as a theme-coherence check; diary_index (CAP-110) —
corpus→index precedent. No rejected FR occupies corpus-summary
territory (checked: graveyard hook output + manual noun grep on
"summary", "index", "atlas", "onboarding").

## Proposed Solution

`examples/demos/fr-atlas/` — portable over any repo with
`feature-requests/` (recap's portability contract): input
`--var project_dir=…`, output a dated markdown atlas written to the
target project's `docs/` (on demand, never auto-committed).

1. **Collect (python tool, no LLM):** scan `feature-requests/*.md` →
   per-FR digest: id, **title + first ~10 lines of Problem/Summary**
   (decided: excerpt depth — themes from stated pain, not naming
   fashion), verbatim `**Status:**` header, type, dates. Parse
   failures reported as rows, never dropped.
2. **Module axis (mechanical):** file paths regex-extracted from FR
   bodies; joined against `capabilities/*.yaml` REQ→module mappings
   when the registry exists (yamlgraph), paths-only otherwise
   (ninchat_voice). Convention absence reported as "not detected",
   recap-style.
3. **Map fan-out (judgement #1):** digests chunked ~50/item; each map
   item proposes candidate themes and assigns its FRs, one-line arc
   description each. One abstraction level per prompt.
4. **Merge (judgement #2):** consolidate candidates into **8–15
   themes** (hard cap, readability is the point), each with a short
   arc narrative.
5. **Coverage post-pass (python, the honesty spine):** every FR id
   lands in exactly one theme or explicit `misc`; **count-in ==
   count-out asserted** (recap FR-703/704 silent-join-drop lesson);
   status tags code-joined at HEAD, never model-carried; module lists
   attached per theme by code from step 2.
6. **Story opener (judgement #3, decided):** ONE additional bounded
   judgement writes a 3-paragraph "story of the project" from the
   merged theme taxonomy + counts (input = the taxonomy, never the
   raw corpus — closed inputs).
7. **Render (python):** opener → themes ordered by last-activity date
   (the reader sees what's alive first) → graveyard section (REJECTED
   FRs with their one-line rationale — FR-070 is the exemplar) →
   mechanical counts (status histogram, date span, parse failures).

## Acceptance Criteria

- [x] AC-01 RED: collector + coverage post-pass condemned by fixtures
      (malformed status header, FR dropped by a simulated bad join,
      count-in/count-out mismatch raises).
- [x] AC-02 Raw read BEFORE wiring (FR-745 ordering precedent): run
      the map stage on the real yamlgraph corpus, dump ≥3 chunk
      outputs, read and record surprising details here — the taxonomy
      is not trusted until its raw claims are read.
- [x] AC-03 Full run on yamlgraph corpus: atlas generated; every FR id
      present exactly once (mechanical assert); themes ≤ 15; graveyard
      section non-empty (070 must appear).
- [x] AC-04 Portability run on projects/ninchat_voice (no CAP
      registry): module axis degrades to paths-only, loudly declared.
- [x] AC-05 Theme-coherence spot check: for each theme, the FR-737 IDF
      machinery flags themes whose member titles share no
      rare noun — flagged themes get a human read before the atlas is
      handed to anyone (advisory, not blocking).
- [x] AC-06 Economics recorded (tokens/cost per full run, both
      corpora).
- [x] AC-07 Fragment (feat, FR-748 in title); diary; README with the
      recap-style contract table; demo-output.log per demo-gate.

## Out of scope (purge list)

- Auto-refresh, scheduled runs, committed/standing board (fr-board F7).
- Cross-repo aggregation into one atlas (one project_dir per run).
- Per-FR LLM summarization beyond the chunk digests (the excerpt is
  mechanical).
- Theme taxonomy persistence/stability across runs (each run is a
  fresh read; stability is a future question with its own consumer).
- Any write into `feature-requests/` files.

## Questions for the human (as options, or 'none')

None — the two open decisions (digest depth: title + Problem excerpt;
prose opener: yes, one bounded judgement) were made by the consumer at
planning, 2026-07-18.

## Implementation notes (2026-07-18, enforce)

### AC-02 raw read — recorded BEFORE trusting the taxonomy

Read chunks c1, c8, c15 verbatim from the full-run state dump
(`tmp/fr748-ac02-rawread.txt`; 15 chunks, 119 candidate themes).
Surprising details a generated dump could not produce:

1. **The corpus contains true near-duplicates the model correctly
   fused**: `FR-409-inquisitor-watcher2-reintegration` and
   `FR-411-inquisitor-watcher2-reintegration` — two distinct files,
   near-identical slugs — landed together in a 2-member "Watcher audit
   cadence" theme. The taxonomy discovered a real resurrection pair.
2. **Self-reference**: the run classified its own FR into a 1-member
   theme, "Onboarding corpus map: Turn the FR archive into a
   newcomer-friendly narrative" — FR-748 describing FR-748.
3. **Per-chunk stylistic nonstationarity**: every c8 arc begins
   "These FRs…" while c1/c15 arcs are imperative ("Fix the state…",
   "Close gaps where…") — map slots develop independent house styles
   within one run.
4. **The id-fidelity failures read (strikes below) were slug BLENDS,
   not random noise**: `FR-424-wip-commit-subject-gate` splices tokens
   from both real FR-424 titles — plausible-wrong-answer shaped,
   invisible to any format check, caught only by population
   reconciliation.

### Three live strikes at the id boundary (two_strike_split applied)

Each full-run failure was a distinct token-fidelity class; each got a
RED witness then a mechanical repair in `assemble_candidates` — zero
prompt patches:

1. **Bracket sigils** — model copied ids WITH the `[brackets]` the
   digest block uses as display sigils → strip decoration.
2. **Slug shortening** — `FR-514-dm-v2-delta-close-carry-forward-floor`
   claimed as `FR-514-delta-close-…` → unique numeric-head repair
   against the population.
3. **Slug paraphrase under duplicate heads** — two real FR-424 files
   exist; claim blended their titles → closest head-mate by
   `SequenceMatcher` above a measured floor (true mate 0.59, wrong
   mate 0.308 → floor 0.5), strict-winner only; ties/misses pass
   through untouched and die loudly in `enforce_coverage`.

Repair within the floor, reject below it — the FR-722/727 boundary
pattern, third confirmation.

### AC-03 evidence (yamlgraph corpus, 2026-07-18)

- Atlas: `docs/2026-07-18-fr-atlas.md` (861 lines).
- 729 FRs collected (+2 companions excluded, counted); 729 theme
  members — every FR exactly once (coverage assert held).
- 13 themes (≤ 15). Graveyard non-empty with
  `070-gui-web-playground` present (unprefixed stem survived — F2).
- 23 headerless FRs reported, not dropped (F3). Status histogram
  rendered verbatim buckets incl. `other 130`.

### AC-04 evidence (ninchat_voice, no CAP registry)

- Atlas: `projects/ninchat_voice/docs/2026-07-18-fr-atlas.md`
  (419 lines). 300 FRs — exactly the judgement's F1 pin — with 96
  companion files excluded and counted; 14 themes; 300 members.
- First run silently degraded the module axis (no `capabilities/`
  → paths-only) without saying so — rc=0 is a shape check
  (`gate_checks_shape_not_substance`). Fixed with a loud header
  declaration ("⚠ No `capabilities/` registry … module axis derived
  from git-touched paths only") + two witnesses; rerun carries it.

### AC-05 evidence (IDF coherence advisory)

- All 13 yamlgraph themes pass — every multi-member theme shares ≥1
  rare noun (idf > 2.5) across ≥2 member titles (e.g. Governance:
  gate×14, watcher2×12; Story generation: plot×20, modeller×16).
  Zero flags; no human re-read triggered. Full output:
  `tmp/fr748-ac05-coherence.txt`.
- Honest observation: `misc` holds 226 members (31%) — the coverage
  sweep made the model's unclaimed residue visible instead of forcing
  fake theme membership (F5 upheld).

### AC-06 economics

- yamlgraph: 729 FRs, 17 LLM calls (15 map + merge + story),
  ≈159k input tokens → well under $1/run on the default deployment.
- ninchat_voice: 300 FRs, 8 LLM calls, ≈64k input tokens.
- Wall time: a few minutes per corpus, dominated by the map fan-out.

### AC-07 artifacts

- Fragment: `changelog/unreleased/fr-748-fr-atlas.md` (feat, REQ-YG-566).
- README with contract table + fr_board/recap differentiation:
  `examples/demos/fr-atlas/README.md`.
- `examples/demos/fr-atlas/demo-output.log` (trimmed real ninchat run).
- Diary:
  `docs/diary/diary-2026-07-18-the-floor-you-guess-is-not-the-floor-you-measure.md`.
- Witnesses: 14 in `tests/unit/test_fr748_fr_atlas.py` (REQ-YG-566,
  CAP-208), incl. the three strike repairs and the loud-declaration
  pair.

## Judgement (2026-07-18)

**Verdict: APPROVED — 5 findings from measuring both corpora before
granting authority.** Measured: yamlgraph 729 FRs (706 status headers,
718 Problem/Summary sections = 98.5% excerpt hit rate, 21 rejected);
ninchat_voice **300** FRs (281 headers, 291 sections, 3 rejected).
Chunk arithmetic holds (~175 tokens/digest → ~9k tokens per 50-digest
map call, ~15 calls); cost well inside AC-06 sanity.

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **The FR's ninchat number was wrong** (~400 claimed, 300 actual) and its graveyard is thin (3 rejected vs yamlgraph's 21) | Numbers corrected here; thin graveyard is DECLARED in the ninchat atlas ("3 rejections on record"), never padded. AC-04 unchanged |
| F2 | **The graveyard exemplar would vanish under an `FR-\d+` id regex**: `070-gui-web-playground.md` and its unprefixed elders carry no `FR-` prefix — a naive id parser drops exactly the files AC-03 requires present | Pin: **id = filename stem**, never a prefix regex; the coverage assert counts files, not pattern matches. AC-01 gains a fixture: an unprefixed filename must survive collection |
| F3 | **Status vocabulary is heterogeneous, measured**: 7+ head values (implemented 254, enforced 117, judged 57, approved 56, proposed 42, completed 40, draft 31 on ninchat…) plus parenthesized variants; 23/729 and 19/300 files have no header at all | Display stays VERBATIM (honesty); the histogram and "alive first" ordering use a small normalization table (first word, lowercased) with a visible `other` bucket; headerless files appear in the parse-failure section as designed. Last-activity date comes from ONE `git log --name-only` pass (mechanical, always present), never from header dates |
| F4 | **Companion files would pollute the population**: ninchat carries `*.judgement.md` siblings; both corpora carry TEMPLATE.md | Pin: collector excludes `TEMPLATE.md` and `*.judgement.md` from the FR population, reports their count in the parse notes — excluded, not invisible |
| F5 | Single-theme membership is a deliberate distortion (FR-733 is honestly both "examples" and "measurement discipline") | Accepted for readability and honest counts; themes may name cross-references in arc prose, no mechanism. Recorded so the distortion is a choice, not an oversight |

**Purge additions:** status-vocabulary normalization beyond the
first-word table (a real taxonomy is its own FR with its own consumer),
header-date parsing (git dates only).

**Prior art:** (graveyard-hook hits at judgement, dispositioned)
FR-100 (pipeline ebook) — nearest neighbor: narrative-from-repo-history,
but external-publication consumer and pipeline/docs source, not the FR
corpus; the atlas neither replaces nor feeds it. FR-135
(examples-value-audit) — audits examples' worth, lexical overlap only.
FR-195 (chaplain documentation) — onboarding for the chaplain
machinery, not the project story. FR-439 (terminology tone-down) —
lexical hit on "summary", no territorial overlap. None rejected, none
blocking; no rationale reuse required.
