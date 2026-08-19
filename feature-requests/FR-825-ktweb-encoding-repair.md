# Feature Request: KTweb Encoding Detection and Event-Safe State Repair

**Priority:** HIGH
**Type:** Bug fix
**Status:** Proposed
**Effort:** 0.5–1 day
**Requested:** 2026-08-19
**Consumer repository:** `https://github.com/sheikkinen/hva-weekly-bulletin`
**Depends on:** FR-824
**Prior art:** FR-824 established the KTweb consumer, typed compact-state and
deterministic-delta contracts, but did not specify response charset handling or
an event-safe repair for already corrupted state. FR-825 reuses those contracts
and addresses only that evidenced gap.

## Summary

Decode KTweb meeting pages using their declared or validated character encoding
instead of unconditionally decoding as UTF-8 with replacement. Repair the 293
already committed KTweb records containing Unicode replacement characters
without turning encoding-only corrections into substantive weekly events.

## Evidence

The first FR-824 baseline committed 1,437 normalized source items. A post-run
quality audit found 293 records containing U+FFFD (`�`), all from KTweb:

| Organization | Affected records |
|---|---:|
| Lappi | 70 |
| Varsinais-Suomi | 51 |
| Etelä-Pohjanmaa | 41 |
| Kanta-Häme | 37 |
| HUS-yhtymä | 36 |
| Kymenlaakso | 34 |
| Päijät-Häme | 24 |

The controlling code path is `src/hva_bulletin/sources.py::collect_ktweb`:

```python
html = request(meeting_url).decode("utf-8", errors="replace")
```

A live Etelä-Pohjanmaa meeting response on 2026-08-19 declared only
`Content-Type: text/html`. Its bytes failed strict UTF-8 at byte 55 and decoded
without replacement as both ISO-8859-1 and Windows-1252. The defect is therefore
local transport decoding, not upstream replacement text.

The latest substantive Hilma event (`EF-55147`) is unaffected. Repository object
integrity, commit provenance, secret scanning, and tracked-path inspection found
no other anomalous artifact.

## Problem

Replacement decoding destroys source text before normalization and hashing.
Consequences include:

1. unreadable Finnish titles in committed state and future bulletins;
2. corrupted strings becoming part of stable substantive hashes;
3. a naive parser fix making every repaired title appear to be a substantive
   update, flooding the weekly event ledger with migration noise;
4. silent recurrence because current tests cover source shape but not legacy
   KTweb encodings or U+FFFD rejection.

## Proposed Solution

### 1. Lossless response decoding

Add one bounded HTML decoding helper used by KTweb meeting pages:

1. honor a valid HTTP `Content-Type` charset when available;
2. otherwise honor an HTML `<meta charset>` or equivalent content-type meta;
3. otherwise accept strict UTF-8 when it succeeds;
4. otherwise fall back to Windows-1252 for the observed KTweb legacy pages;
5. fail the endpoint health observation if decoding still produces U+FFFD or
   cannot be completed losslessly.

Do not use `errors="replace"` for persisted source text. Do not add a general
encoding-detection dependency or probabilistic detector for this bounded source
family unless fixtures prove the deterministic chain insufficient.

The transport may return response headers alongside bytes or parse charset
metadata from the body. Keep curl argument-safe and retain the existing timeout,
user agent, and fail-closed source-family behavior.

### 2. Event-safe repair

Repair current KTweb compact state from freshly decoded source records, but do
not emit `updated` events solely because U+FFFD was replaced by the correct
source characters.

Implement this as an explicit, bounded migration rather than weakening normal
delta semantics:

- identify only existing KTweb state records containing U+FFFD;
- match each repair by the existing stable `(source, source_id)` key;
- require the incoming record to be lossless and retain the same source URL;
- update compact state and substantive hash basis;
- suppress only the encoding-repair event for those identified records;
- preserve normal events for any simultaneous non-title substantive change;
- record migration completion in state metadata so it is idempotent;
- remove the migration path after the repaired state is committed and verified,
  or make it inert after its completion marker.

Do not rewrite historical event ledgers. The current ledger contains no corrupt
KTweb event, so historical provenance requires no mutation.

### 3. Publication guard

Before YAMLGraph synthesis, reject narrative candidates containing U+FFFD. The
guard is deterministic and must report source plus stable ID. It prevents a
future transport regression from publishing corrupted text even if collection
health handling is accidentally weakened.

## Acceptance Criteria

- **AC-01:** A legacy-encoded KTweb fixture containing Finnish characters such
  as `Pöytäkirjan tarkastaminen` decodes exactly, with no U+FFFD.
- **AC-02:** A UTF-8 KTweb fixture continues to decode exactly.
- **AC-03:** Declared HTTP or HTML charset takes precedence over fallback, and
  an unsupported or lossy result becomes explicit endpoint health failure.
- **AC-04:** Persisted `SourceItem.title`, organization, and excerpt fields from
  KTweb contain no U+FFFD after successful collection.
- **AC-05:** The repair updates all currently reachable corrupt KTweb records in
  compact state without creating encoding-only `updated` or `transition` events.
- **AC-06:** A repaired record with another substantive field change still emits
  the correct normal event and exact `changed_fields`.
- **AC-07:** Re-running the migration and collection is a deterministic no-op.
- **AC-08:** Migration completion is recorded in bounded state metadata and does
  not alter historical event ledgers.
- **AC-09:** Weekly-window construction or publication rejects any candidate
  containing U+FFFD before the LLM call.
- **AC-10:** Unit tests cover UTF-8, Windows-1252/ISO-8859-1-compatible Finnish
  bytes, malformed bytes, event suppression, simultaneous substantive change,
  and retry behavior without live network access.
- **AC-11:** A live six-family smoke reports zero U+FFFD records among newly
  collected KTweb items and preserves explicit per-endpoint health.
- **AC-12:** Post-repair census reports zero U+FFFD records in
  `state/source-items.jsonl`, or lists unreachable stale records explicitly with
  source ID, URL, and reason rather than silently claiming completion.
- **AC-13:** Ruff, focused tests, full tests, Radon grade-D scan, and file-size
  gates pass before commit; no source or test file exceeds 450 lines.
- **AC-14:** One dispatched collector run commits the bounded repair, and a
  second dispatched run proves no encoding-only replay event or state churn.

## Non-Goals

- Changing Dynasty, CaseM, Hilma, TED, or MAO normalization without evidence of
  the same defect.
- Treating title spelling or punctuation changes as generally non-substantive.
- Rewriting git history or historical baseline commits.
- Using an LLM to repair, transliterate, infer, or validate source text.
- Expanding the source inventory or bulletin schema.

## Verification Evidence

Implementation notes must record:

1. fixture encodings and exact decoded assertions;
2. pre/post U+FFFD census by source and organization;
3. migration state/event counts and completion marker;
4. focused and full test results;
5. live collection health census;
6. collector workflow run URLs and resulting commit SHAs;
7. confirmation that the next bulletin input contains no U+FFFD candidates.

## Implementation Boundary

All consumer code, tests, state repair, and workflow evidence belong in
`hva-weekly-bulletin`. YAMLGraph changes are limited to this FR's status,
judgement, and implementation evidence. No YAMLGraph package or capability
change is required.
