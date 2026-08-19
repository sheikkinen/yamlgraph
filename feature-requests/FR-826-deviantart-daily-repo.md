# Feature Request: FR-826 DeviantArt Daily Auto-Publish Repo (GitHub-Actions-Native)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed (revised 2026-08-19 — pivoted from local publisher
tool to GitHub-Actions-native repo per operator direction)
**Effort:** 2 days
**Requested:** 2026-08-19
**First consumer / first event:** the sheikkinen DeviantArt gallery, on
the first morning a scheduled GitHub Actions run generates an image
from a corpus prompt, writes a mythic post, and publishes it to
DeviantArt with zero human involvement. Second consumer: the
Proclaim narrative — a public repo that autonomously creates and
publishes art daily is the strongest "yamlgraph runs unattended"
artifact after FR-819.

**Prior art:** FR-819 [Completed] is the substrate proof — the
`yamlgraph-daily-digest` repo pattern (repo = runtime + state store +
publication record, cron + commit-back, AC-07 witnessed green
2026-08-19) is inherited wholesale. FR-822 [Completed, Judged] froze
the DA API contracts (PKCE done, refresh rotation, submit/publish,
paragraph rendering, error taxonomy); its spike script stays
quarantined — findings only (R-3/C-5). FR-781 [Enforced] owns the
describe-prompt precedent (`examples/demos/file-hook/prompts/`), reused
as prompt precedent, not moved. FR-769 [Enforced] owns the shared
vision boundary. FR-772 [Enforced] — noun coincidence. The earlier
draft of THIS FR (local CLI publisher, commit df030260) is superseded
by this revision: same number, pivoted architecture, no separate
disposition needed.

## Summary

New public GitHub repo (working name `deviant-daily`) in the FR-819
mold: a daily cron workflow picks a random prompt from a committed
corpus (extracted from `~/Documents/deviant-working/signed.log`),
generates an image on Replicate (model roster: z-image / FLUX / grok),
writes a julkaisuohje-style post (file-hook describe pattern), publishes
it to DeviantArt via the FR-822-proven API flow, and commits the post
record back to itself. All credentials are GitHub repo secrets.

## Value Statement

The operator's entire DeviantArt production line — prompt selection,
generation, description, publication — runs unattended on GitHub
infrastructure; the gallery grows daily without a human writing a word
or clicking a button.

## Problem

Publishing to DeviantArt is manual end-to-end today. All ingredients
are proven separately: image generation (`examples/image_pipeline` +
`../my-replicate-app`, both Replicate), description generation
(FR-781 file-hook, julkaisuohje style), API publishing (FR-822 spike),
and unattended GitHub-Actions operation (FR-819). Nothing composes
them, and the local-machine variants (launchd, file-hook watch dirs)
tie the pipeline to one iMac being awake.

## Ideal Result

Every morning a new deviation appears in the sheikkinen gallery:
generated from a randomly drawn prompt out of the operator's own
13,682-entry prompt history, illustrated by a randomly chosen model
from the roster, described in the frozen mythic voice, flagged
`is_ai_generated=true`/`noai=true`, mature-judged per image — and the
repo's commit log is the complete public provenance record (prompt,
model, post text, deviation URL) of every publication. The operator's
only remaining touchpoints are refilling the corpus and deleting
anything the gallery shouldn't keep.

## Proposed Solution

### Repo scaffold (FR-819 pattern)

`sheikkinen/deviant-daily` — public; `pip install yamlgraph` in the
workflow; committed state; `workflow_dispatch` + daily cron. Contents:

- `prompts/corpus.jsonl` — one-time local extraction from
  `signed.log` (13,682 `==== File:` entries; prompt = free text of the
  `parameters:` field before `Steps:`); dedup'd, one JSON object per
  line `{prompt, source_file}`. Extraction script is a throwaway run
  locally in this workspace; only the corpus lands in the new repo.
- `state/published.jsonl` — committed ledger: date, corpus line drawn,
  model used, deviation URL. Doubles as the no-repeat filter (drawn
  prompts are excluded from future draws) and the dedup guard
  (a date already in the ledger → run exits idempotently, FR-819
  AC-08 pattern).
- `posts/YYYY-MM-DD.md` — the published post text committed back
  (title, paragraphs, quote, tags, DA URL). Images are NOT committed —
  DA hosts them; the repo stays light.

### Secrets (all GitHub repo secrets, no files)

| Secret | Purpose |
|---|---|
| `REPLICATE_API_TOKEN` | image generation |
| `ANTHROPIC_API_KEY` | describe step (vision LLM) |
| `DA_CLIENT_ID` / `DA_CLIENT_SECRET` | DA OAuth client (75301) |
| `DA_REFRESH_TOKEN` | seeded once from the FR-822 grant |
| `GH_PAT` | fine-grained PAT, this repo only, secrets:write |

**Rotation contract (the hard part, FR-822 Q3):** DA rotates the
refresh token on every refresh. The workflow refreshes, then
immediately persists the NEW refresh token back into the repo secret
via `gh secret set DA_REFRESH_TOKEN` using `GH_PAT` (the default
`GITHUB_TOKEN` cannot write secrets). Persist-before-publish ordering:
if secret write fails, the run aborts BEFORE publishing — a published
post with a lost token is worse than a skipped day. Access token lives
1 h — one run fits easily.

### Daily pipeline (one workflow run)

1. **draw** — random corpus line not in the ledger; record the draw.
2. **generate** — Replicate, model drawn at random from a roster
   config: `z-image` (`prunaai/z-image-turbo`, the
   `examples/shared/replicate_tool.py` default), FLUX
   (`black-forest-labs/flux-1.1-pro-ultra`, the my-replicate-app pin),
   grok (xAI image model — exact Replicate slug verified at enforce
   time; roster is config, absent models are dropped with a logged
   notice, never a crash).
3. **describe** — vision LLM over the generated image PLUS the
   original prompt text (prompt states intent, image states outcome),
   julkaisuohje voice per the FR-781 prompt precedent. Schema carries
   `{title, paragraphs, quote, tags, confidence, mature, mature_level,
   mature_classification}`.
4. **gate** — `confidence != high` OR mature classification beyond
   what DA permits for API publishing → skip the day: ledger records
   the skip + reason, nothing publishes, run exits green. A skipped
   day is a correct outcome, not a failure.
5. **publish** — FR-822 flow: refresh (+rotate persist, step order
   above) → placebo → `stash/submit` (file, title, comments, `tags[i]`,
   `is_ai_generated=true`, `noai=true`) → `stash/publish` (`is_mature`
   + level/classification from the describe schema). UA header,
   timeouts, 429 backoff, `error_code 9` = idempotent success.
6. **commit** — post MD + ledger entry pushed back (FR-819
   commit-back pattern, `[skip ci]`).

Pipeline implementation reuses `examples/shared/replicate_tool.py`
patterns and the file-hook describe prompt as precedent. If any
`graph.yaml`/`prompts/*.yaml` artifact is authored for the new repo
from this workspace, it goes through the graph-authoring route
(FR-767) — plain-Python steps need no such rite.

### Testing (in the new repo, mirroring FR-819)

- Unit tests, mocked HTTP: DA calls asserted against FR-822's recorded
  response bodies; rotation persist-before-publish ordering; corpus
  draw no-repeat; ledger dedup; MD render; tags validator
  (`[a-z0-9_]+`); mature gate.
- Live path proven by `workflow_dispatch` first (AC-05), cron second
  (AC-06) — the FR-819 two-step.

## Acceptance Criteria

- [ ] AC-01: `prompts/corpus.jsonl` committed to the new repo —
      dedup'd extraction of the signed.log `parameters:` prompts;
      count recorded in the repo README; no other signed.log content
      (no EXIF dumps, no file paths beyond `source_file` names)
- [ ] AC-02: All five secrets configured as repo secrets; no
      credential, token value, or token file appears in any commit,
      log output, or committed artifact
- [ ] AC-03: Refresh rotation round-trip proven: a run refreshes,
      writes the rotated token via `gh secret set`, and the NEXT run
      authenticates successfully with it (two consecutive
      dispatch runs witnessed)
- [ ] AC-04: Rotation ordering witnessed by test: secret-persist
      failure aborts before publish
- [ ] AC-05: `workflow_dispatch` run completes green end-to-end:
      draw → generate → describe → publish; deviation URL in the
      ledger and post MD committed back
- [ ] AC-06: At least one scheduled cron run completes green and
      publishes without human involvement (FR-819 AC-07 pattern)
- [ ] AC-07: Gate path witnessed: a low-confidence or
      DA-impermissible-mature result skips publication, records the
      skip in the ledger, and exits green
- [ ] AC-08: Same-day rerun is idempotent — ledger dedup prevents a
      second publish (dispatch twice on one day to witness)
- [ ] AC-09: Model roster exercised: at least two roster models have
      each produced a published (or gate-skipped) run; absent/renamed
      Replicate models degrade to a logged drop, not a crash
- [ ] AC-10: Post MD on the live deviation page verified once against
      the julkaisuohje contract (paragraphs render, tags attached,
      AI badge shown — FR-822 witness method)

## Constraints

- Inherited from FR-822 judgement: spike code quarantined — findings
  only (C-5); no graph artifacts without the authoring route (C-4);
  no secrets in commits (C-2).
- The julkaisuohje (`DEVIANTART-JULKAISUOHJE.md`) remains the frozen
  style contract for the describe step.
- Mature judgement is per-image from the describe schema, never
  defaulted; content DA forbids outright is gate-skipped, not
  published with flags.
- Corpus prompts are the operator's own generation history — no
  external prompt sources in scope.
- Daily cadence fixed at one publish/day max; no batch/backlog mode
  in this FR.
- The yamlgraph repo gains no core changes; local launchd agents are
  untouched (their retirement is a separate disposition).
- New-repo scaffold work follows FR-819's shape; where this FR and
  FR-819's repo diverge structurally, FR-819 wins unless recorded here.

## Alternatives Considered

- **Local publisher CLI (this FR's first draft):** superseded — ties
  publication to the iMac; the operator redirected to the
  Actions-native shape before judgement.
- **Committed encrypted token file** (age/openssl, passphrase secret)
  instead of `gh secret set` rotation: viable FR-819-style
  commit-state fallback if PAT-based secret writes prove fragile;
  recorded as the designated fallback, not built up front.
- **Committing generated images to the repo:** rejected — ~2 MB/day
  of binary growth; DA is the image host, the repo is the text
  provenance record.
- **Browser automation of DA Studio:** rejected in
  `docs/research-deviantart-api-2026-08-19.md`; API path proven.

## Related

- `feature-requests/FR-819-github-native-digest-poc-repo.md` — repo
  pattern substrate
- `feature-requests/FR-822-deviantart-publish-spike.md` (+ judgement)
  — DA API contracts
- `feature-requests/FR-781-macos-file-hook-example.md` — describe
  precedent
- `docs/research-deviantart-api-2026-08-19.md` — API research
- `.chaplain/inbox/deviantart-auto-publish-pipeline.md` — parent
  proposal (this FR replaces its local two-phase shape)
- `../my-replicate-app` + `examples/image_pipeline` — generation
  precedents

## Judgement (pending)
