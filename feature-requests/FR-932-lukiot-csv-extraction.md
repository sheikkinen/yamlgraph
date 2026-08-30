# Feature Request: Lukiot specialization list → CSV extraction format

**Priority:** LOW
**Type:** Documentation (document-only — no code, no graph)
**Status:** Done (CSV generated 2026-08-30)
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** the operator, filtering/sorting Finnish
upper-secondary specialization tracks (e.g. "all ratsastuslinja schools",
"all national special tasks") in a spreadsheet at school-selection time.
**Prior art:** none found — no prior FR or script touches `tmp/lukiot.txt`
or Finnish school-list extraction; one-off document-only record.
**Research:** in-body (Alternatives Considered below); document-only FR,
no `scripts/research.sh` run — no framework code is proposed.

## Summary

Define a CSV schema and parsing rules for `tmp/lukiot.txt` — a
semi-structured Finnish-language list of lukio (upper secondary school)
specialization tracks, organized region → city → school, with `*`
marking a valtakunnallinen erityistehtävä (national special education
task). Output: `tmp/lukiot.csv`.

## Value Statement

The operator gets a filterable/sortable dataset instead of 180 lines of
prose with four inconsistent list styles.

## Problem

The source mixes formats: `School: track` lines, bullet sublists,
comma-separated track lists with per-item `*` markers, inline city
mentions, Swedish-language entries, scattered URLs, one duplicate school
(Kiuruveden lukio listed in both Etelä- and Itä-Suomi), and one school
with no track (Helsingin aikuislukio). No mechanical parser handles this
cleanly; it is a one-shot LLM extraction task.

## Ideal Result

A single flat CSV where every specialization track is one row, the `*`
marker is preserved as a boolean at track grain, raw track names are
kept verbatim, and a normalized category column enables thematic
filtering — with source ambiguities recorded in a notes column instead
of silently resolved.

## Proposed Solution

### Schema (one row per school–track pair)

```csv
region,city,school,track,national_special_task,category,notes,url
```

| Column | Type | Rule |
|---|---|---|
| `region` | enum | `Etelä-Suomi`, `Itä-Suomi`, `Länsi-/Keski-Suomi`, `Pohjois-Suomi` — from top-level headings |
| `city` | str | From city section headings; else parsed inline ("Nurmon lukio, Seinäjoki"); else derived from school name (Kotkan lyseo → Kotka) |
| `school` | str | School name, city/date/marketing suffixes stripped to `notes` |
| `track` | str | One track per row, verbatim source wording (minus `*`) |
| `national_special_task` | bool | The `*` marker, bound per-track (Otaniemi: matematiikka-luonnontiede `true`, teatteri- ja medialinja `false`) |
| `category` | enum | Normalized theme, see below |
| `notes` | str | oma haku, toimipiste, start year, language of instruction, source ambiguities |
| `url` | str | School-specific links only; city-level links (tampere.fi) dropped |

### Category enum

`urheilu`, `ratsastus`, `esports`, `musiikki`, `tanssi`, `kuvataide`,
`taide` (mixed-arts lines), `ilmaisu/teatteri`, `media`,
`luonnontiede/LUMA`, `IB`, `englanninkielinen`,
`kielet/kansainvälisyys`, `yrittäjyys/talous`, `muu`.

Raw names are inconsistent (urheilulinja / urheiluvalmennus /
kilpaurheilulinja / idrott); `category` is the join key, `track`
preserves the source.

### Parsing rules (edge cases)

1. **Comma/ja-separated track lists split into rows**; `*` binds to the
   compound it annotates — when `*` follows a list under an explicit
   erityistehtävä heading (Tampere OKM list, Tölö gymnasium,
   Sibelius-lukio "musiikki- ja tanssi\*"), every listed track is `true`.
2. **Kiuruveden lukio duplicate**: appears in both Etelä- and Itä-Suomi
   sections with differing track lists. Deduped to Itä-Suomi (correct
   region), tracks merged, note records the merge.
3. **Helsingin Suomalainen Yhteiskoulu**: source says "kielten
   erityistehtävä" without `*` — marked `true` with a note; sibling
   tracks (kielilinjat, IB-linja) stay `false` per source.
4. **Trackless schools** (Helsingin aikuislukio, Svenska samskolan i
   Tammerfors): one row, empty `track`, explanation in `notes`.
5. **Toimipiste-level tracks** (Tuusulan lukio ×3): one school,
   toimipiste in `notes`.
6. **Inferred school names** ("Hankasalmi: suunnistus" →
   Hankasalmen lukio): inference flagged in `notes`.
7. **Pori appears in two regions** (Porin lukio under Etelä-Suomi,
   BSS/SKiB IB-linja under Länsi-/Keski-Suomi): kept as source states;
   inconsistency noted here, not silently fixed.
8. **Swedish-language schools**: `ruotsinkielinen` in `notes`, track
   names verbatim in Swedish, normalized via `category`.
9. Fields containing commas are double-quoted per RFC 4180.

### Generation method

One-shot LLM extraction (this session), per doctrine "YAMLGraph and LLM
should be used instead of complex regex logic" — but no graph artifact
is warranted for a single static source file; a graph would be
`growth_as_default`. Output committed as `tmp/lukiot.csv`.

### Cross-check plan (CSV vs. source)

LLM extraction is a claim; the cross-check reconciles it against the
source at the boundary. Four mechanical checks, run as a throwaway
script (`tmp/crosscheck_lukiot.py`, not committed):

- **A — School coverage (source → CSV):** extract school names from the
  source via pattern heuristics (`lukio|gymnasium|lyseo|yhteiskoulu|
  samskolan` colon-lines, Tampere dash-list) plus an alias table for
  the inferred/normalized names (rule 6 above, plus typo fixes like
  "Lappeenrannan Lyseon luki"). Every extracted school must match ≥1
  CSV row. Failure = dropped school.
- **B — Star reconciliation:** `*` count in source content (excluding
  the legend line) must equal `national_special_task=true` rows minus
  the documented expansions: Sibelius 1 star → 2 rows, Tölö 1 star →
  3 rows, SYK unmarked erityistehtävä → 1 row (rule 3), Tammerkoski
  design under the OKM list → 1 row (rule 1). Expected: stars + 5 =
  true rows. Failure = a `*` invented or dropped.
- **C — URL coverage:** every `http(s)://` or `www.` URL in the source
  must appear in the CSV `url` column, except the documented city-level
  `tampere.fi` drop. Failure = lost link.
- **D — Reverse membership (CSV → source):** the distinguishing token
  of every CSV school name must occur in the source text (alias table
  applied). Failure = hallucinated row.

Track-level wording is NOT mechanically checkable (the whole reason
this is an LLM extraction); rows carry source wording verbatim so
spot-checks are a grep away.

### Cross-check results (2026-08-30)

Run: `python3 tmp/crosscheck_lukiot.py` — all four checks PASS.

| Check | Result | Detail |
|---|---|---|
| A — school coverage | PASS | 109 source school mentions, 0 missing from CSV (1 initial flag was a heuristic artifact: the Kiviruukki line has no colon separator; resolved via alias, school was present) |
| B — star reconciliation | PASS | 33 source `*` (excl. legend) + 5 documented expansions = 38 = CSV `true` rows exactly |
| C — URL coverage | PASS | 11 source URLs, 0 lost; city-level tampere.fi drop as documented |
| D — reverse membership | PASS | 102 distinct CSV schools, all traceable to source text — no hallucinated rows |

Residual (accepted): track-level wording and category assignments are
not mechanically verified — by design; `track` carries source wording
verbatim so any row is one grep from its source line.

### Excel export (2026-08-30)

Human skim surface: `tmp/lukiot.xlsx`, generated from the CSV by the
throwaway script `tmp/lukiot_to_xlsx.py` (openpyxl, not committed).
Styling contract:

- **Autofilter on all 8 headings** (`A1:H187`) + frozen header row —
  filter dropdowns are the primary consumption mode (e.g. filter
  `category = ratsastus` or `national_special_task = true`).
- **Alternating fill per region block** (light blue / light orange,
  switching at each of the 4 region boundaries), header row dark blue
  with white bold text, columns auto-sized (capped at 60 chars).
- Data is byte-identical to the CSV — the xlsx is a rendering, the CSV
  remains the canonical artifact; regenerate with
  `python3 tmp/lukiot_to_xlsx.py` after any CSV edit.

## Acceptance Criteria

- [x] Every school line in `tmp/lukiot.txt` yields ≥1 CSV row
- [x] `*` markers preserved at track grain as `national_special_task`
- [x] Kiuruvesi duplicate merged with note
- [x] All ambiguities recorded in `notes`, none silently resolved
- [x] No code or graph artifacts added (document-only)
- [x] Cross-check A–D pass (or every failure dispositioned in results)

## Alternatives Considered

- **Regex/Python parser**: rejected — four list styles plus prose
  qualifiers is past the `regex_fourth_exclusion` threshold, and the
  source is a one-off static file.
- **YAMLGraph extraction graph**: rejected — no recurring consumer; a
  graph for a single run fails the first-consumer test.
- **Wide format (one row per school, track columns)**: rejected —
  per-track `*` markers and 1–6 tracks per school make track-grain rows
  the only lossless grain.

## Related

- Source: `tmp/lukiot.txt`
- Output: `tmp/lukiot.csv` (canonical), `tmp/lukiot.xlsx` (styled view)
- Tooling (throwaway, uncommitted): `tmp/crosscheck_lukiot.py`,
  `tmp/lukiot_to_xlsx.py`
