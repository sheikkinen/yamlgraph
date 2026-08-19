# Research: DeviantArt API for Automated Publishing (2026-08-19)

Context: chaplain inbox proposal `deviantart-auto-publish-pipeline.md` (Phase 2
publisher). Sources: <https://deviantart.readme.io> (docs updated 2026-05-08,
OpenAPI 1.20240701). This is the analysis, not the inventory — each section
ends in a decision for our pipeline.

## Verdict

Feasible with first-class support. The API natively models every flag the
julkaisuohje requires (`is_ai_generated`, `noai`, mature triage, tags) — no
scraping, no browser automation. Publish is a two-call flow against
`https://www.deviantart.com/api/v1/oauth2`.

## 1. Publish flow (two calls)

### `POST /stash/submit` — multipart upload

Scopes: `basic stash`. Returns `{status, itemid}`.

| Field | Notes |
|---|---|
| `file` | binary multipart |
| `title` | deviation title |
| `artist_comments` | the description body |
| `tags[]` | **letters, numbers, underscore ONLY** |
| `is_ai_generated`, `noai` | booleans, set both `true` per account policy |

### `POST /stash/publish` — form-urlencoded

Scopes: `publish stash`. Returns `{status, url, deviationid}`.

| Field | Notes |
|---|---|
| `itemid` | **required** — from submit |
| `is_mature` | **required** — not optional decoration |
| `mature_level` | `strict\|moderate` — required if `is_mature=true` |
| `mature_classification[]` | `nudity\|sexual\|gore\|language\|ideology` |
| `galleryids[]` | UUIDs (from `/gallery/folders`), optional |
| `is_ai_generated`, `noai` | repeat on publish |
| `feature` | default `true` |

**Decision:** the Phase 1 description schema must be extended — `mature: bool`
alone is insufficient. Schema becomes
`{mature: bool, mature_level: str|None, mature_classification: list[str]}`
with a Pydantic validator enforcing the enums and the
level-required-when-mature rule at the boundary. Tags need a normalizing
validator (`[a-z0-9_]` only) — the style spec's tags already comply, but the
LLM output must be forced to.

## 2. Authentication

- New apps are **OAuth 2.1**: Authorization Code + PKCE (S256) mandatory,
  implicit grant gone, exact redirect-URI match, no query-string tokens.
- Register a **confidential** client (server-side script holds the secret).
- Client Credentials grant only reaches public endpoints — **not** usable for
  stash/publish. A one-time interactive browser authorization (localhost
  redirect) with scopes `basic stash publish` is unavoidable.
- Access token lives **1 hour**; refresh token lives **3 months** and is
  rotated on every refresh.

**Decision:** publisher persists the rotated `refresh_token` after every run
(keychain or chmod-600 local file, never repo). Any publish cadence of
< 3 months keeps the token warm indefinitely; a longer gap costs one manual
re-auth. Call `/api/v1/oauth2/placebo` before upload to validate the token
cheaply (documented purpose: avoid discovering expiry mid-upload).

## 3. Error and rate-limit contract

- **429**: adaptive rate limiting, no fixed quota. Exponential backoff
  (1s → 2s → 4s …). Our proposed 2/day cap is gallery-cadence policy, far
  below anything adaptive limiting would notice.
- **500**: retry up to 3× is expected behavior per docs.
- **403 with HTML body**: client missing `User-Agent` or HTTP compression —
  both must be set.
- Branch on `error` / `error_code`, never parse `error_description`.
- Publish endpoint error codes worth handling: `8` preview image required,
  `9` already published (idempotency signal — safe to mark queue entry done).

## 4. Open spike (pre-Phase-2, one manual publish)

Publish error codes `0`/`1` are "Must accept DA submission policy / terms of
service", but the current OpenAPI schema (`additionalProperties: false`) has
no `agree_submission`/`agree_tos` params that the legacy API had. Likely
account-level acceptance now; verify with a single manual API publish before
granting batch authority. Same spike confirms `artist_comments` formatting
(HTML vs plain text paragraph handling) — the docs don't state it.

## 5. What we do NOT need

- `display_resolution` / `add_watermark` — signing happens locally (sign.sh).
- `groups` / `group_folders`, license options, free download — out of scope
  per julkaisuohje ("älä ota myyntiä … käyttöön ilman erillistä pyyntöä").
- Browser automation of DeviantArt Studio — the API path is complete.
