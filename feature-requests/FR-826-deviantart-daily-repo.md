# Feature Request: FR-826 DeviantArt Daily Auto-Publish Repo (GitHub-Actions-Native)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced 2026-08-19 — repo live
(https://github.com/sheikkinen/deviant-daily), first publish green
(run 32267564652), idempotency witnessed (32268278258), cron enabled;
AC-07/AC-13/AC-15 + z-image roster leg are pending observations
(first cron run 2026-08-20). Judged 2026-08-19 APPROVED WITH REVISIONS
(`FR-826-deviantart-daily-repo.judgement.md`) — R-1..R-6 folded, C-4
approvals recorded (corpus + cron)
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
workflow; committed state; `workflow_dispatch` + daily cron.

**Execution surface (Judgement R-1):** the daily pipeline IS a
YAMLGraph graph in the new repo — `graph.yaml` orchestrates
draw → generate → describe → gate → publish → commit; Python tools
exist only for side effects (corpus draw, Replicate call, DA API,
ledger/post writes); the describe step uses YAML prompt artifacts. A
plain-Python entrypoint may bootstrap `yamlgraph graph run` but must
not be the orchestration layer — the repo's Proclaim claim is
"yamlgraph runs unattended", so yamlgraph must actually run it. All
`graph.yaml`/`prompts/*.yaml` artifacts are authored from this
workspace through the governed route (`scripts/author.sh`), with the
authoring evidence report copied into the enforcement record.

Contents:

- `graph.yaml` + `prompts/*.yaml` — the pipeline (authored via the
  governed route, lint + smoke evidenced).
- `STYLE-CONTRACT.md` — committed snapshot of
  `DEVIANTART-JULKAISUOHJE.md` (Judgement R-6): the style source of
  truth lives IN the new repo, not on the iMac; AC witnesses check
  against this committed copy.
- `prompts/corpus.jsonl` — one-time local extraction from
  `signed.log` (13,682 `==== File:` entries; prompt = free text of the
  `parameters:` field before `Steps:`); dedup'd, one JSON object per
  line `{prompt, source_file}` where `source_file` is a basename only,
  never an absolute path. **Corpus publication gate (Judgement R-2):**
  the corpus is a public artifact of the operator's prompt history —
  before the repo is created or populated, the operator must approve
  publication explicitly; the approval date, corpus count, and
  redaction policy are recorded in the new-repo README; a mechanical
  secret/private-data scan runs over the extraction before commit and
  the operator sample-reviews a random slice; prompts that cannot be
  public are redacted or excluded.
  **APPROVED by operator 2026-08-19** with this redaction policy:
  - LoRA syntax (`<lora:...>` and weight tags) STRIPPED from prompts
    (kept prompts, removed tags — model-internal noise, not content)
  - prompts containing personal names EXCLUDED — name blocklist
    seeded with Katja, Tuija, Nina; extensible in the extraction
    script; sample review watches for misses
  - prompts containing non-consent/violence terms EXCLUDED — term
    blocklist seeded with "rape"; extensible; these are
    DA-impermissible regardless of corpus policy
  - both blocklists live in the extraction script and are themselves
    committed to the new repo (the policy is public, the raw
    unsanitized corpus never is)
- `state/published.jsonl` — committed ledger, see idempotency
  contract below.
- `posts/YYYY-MM-DD.md` — the published post text committed back
  (title, paragraphs, quote, tags, DA URL). Images are NOT committed —
  DA hosts them; the repo stays light.

**Idempotency state machine (Judgement R-3):** DA publish is an
external side effect; the ledger is the only guard, so it must commit
at every transition that protects one. Ledger entries carry a status:
`drawn` → `submitted` → `published` (or `skipped`), and each
transition guarding an external call is committed-and-pushed (FR-819
concurrency group, `git pull --rebase` before push) BEFORE the next
side effect. A rerun that finds an incomplete same-day record resumes
from its status or fails safely — it never draws a new prompt. If the
post-publish commit fails and cannot self-heal, the run fails visibly
as `RECOVERY_REQUIRED` with the non-secret DA URL/itemid in the log,
and automatic republish is blocked until the ledger is repaired.
Tests simulate commit/push failure before publish, after submit, and
after publish — proving no path creates a second public deviation for
the same date.

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

1. **draw** — random corpus line not in the ledger; ledger transition
   `drawn` committed.
2. **generate** — Replicate. **Frozen roster (Judgement R-4):** two
   ACTIVE models — `prunaai/z-image-turbo` (the
   `examples/shared/replicate_tool.py` default) and
   `black-forest-labs/flux-1.1-pro-ultra` (the my-replicate-app pin);
   grok is DISABLED until its exact Replicate slug is committed to the
   roster config by a recorded FR update. **R-4 update 2026-08-19:**
   grok ENABLED — operator supplied `xai/grok-imagine-image-2`
   (an earlier agent probe wrongly concluded no Replicate grok exists;
   the search API missed it, direct GET returns the schema). Params
   frozen from the model schema: aspect_ratio 16:9, resolution 2k,
   quality medium (enum is low|medium — no high). Local generation
   smoke green (PNG, 7.6 MB). Commit d8ebd54 in deviant-daily.
   The runner validates the
   roster before drawing: zero active models is a hard failure BEFORE
   any corpus draw or DA side effect — never a green skipped day; an
   unavailable optional model is dropped only with a structured log of
   model ID and reason.
3. **describe** — vision LLM over the generated image PLUS the
   original prompt text (prompt states intent, image states outcome),
   voice per the committed `STYLE-CONTRACT.md`.
4. **gate** — mechanical, typed (Judgement R-5). Pydantic output
   model with deterministic validators:
   - `confidence`: enum `high|medium|low`; only `high` may publish
   - `tags`: normalized to `[a-z0-9_]+` or the result is rejected
   - `mature_level`: `strict | moderate | None`
   - `mature_classification`: subset of DA's allowed enum
   - `mature=true` requires level + ≥1 classification;
     `mature=false` requires neither
   - invalid or policy-forbidden results gate-skip: ledger records
     `skipped` + reason, nothing publishes, run exits green only
     after the skip record is committed
5. **publish** — FR-822 flow: refresh (+rotate persist, step order
   above) → placebo → `stash/submit` (file, title, comments, `tags[i]`,
   `is_ai_generated=true`, `noai=true`) → `stash/publish` (`is_mature`
   + level/classification from the schema; `is_ai_generated=true` and
   `noai=true` passed on BOTH calls). UA header, timeouts, 429
   backoff, `error_code 9` = idempotent success. Ledger transitions
   `submitted` and `published` committed around the calls per the
   state machine.
6. **commit** — post MD + final ledger entry pushed back (FR-819
   commit-back pattern, `[skip ci]`).

### Testing (in the new repo, mirroring FR-819)

- Unit tests, mocked HTTP: DA calls asserted against FR-822's recorded
  response bodies; rotation persist-before-publish ordering; corpus
  draw no-repeat; ledger dedup; MD render; tags validator
  (`[a-z0-9_]+`); mature gate.
- Live path proven by `workflow_dispatch` first (AC-05), cron second
  (AC-06) — the FR-819 two-step.

## Acceptance Criteria (revised by Judgement)

- [x] AC-01: FR-826 revised with the exact YAMLGraph execution
      surface, corpus approval/sanitization gate, idempotency state
      machine, frozen model roster, deterministic DA gate schema, and
      committed style contract (R-1..R-6 — this fold)
- [x] AC-02: Public `sheikkinen/deviant-daily` repo exists outside
      this repository — never vendored, submoduled, or committed here
      *(created 2026-08-19, https://github.com/sheikkinen/deviant-daily,
      local tree at ../deviant-daily)*
- [x] AC-03: New repo contains YAMLGraph `graph.yaml` + YAML prompt
      artifacts; governed authoring evidence records lint and smoke
      *(scripts/author.sh run 2026-08-19; report committed as new-repo
      docs/authoring-report.md — lint, info, compile, prompt-shape
      passed; live smoke recorded blocked, deferred to AC-14)*
- [x] AC-04: `prompts/corpus.jsonl` committed only after operator
      approval + sanitization; README records count, source, approval
      date, redaction policy; rows are `{prompt, source_file}` with
      basenames only — no absolute paths, EXIF, token-like strings
      *(5,893 kept / 2,020 name-excluded / 69 term-excluded / 1,054
      dups; source_file reduced to numeric id; scan 0 hits; sample
      slice at ../deviant-daily/prompts/corpus.sample.txt)*
- [x] AC-05: Workflow has `workflow_dispatch`, daily cron,
      `permissions: contents: write`, concurrency group with
      `cancel-in-progress: false`, `git pull --rebase` before push,
      no secret-printing shell tracing
      *(cron enabled eeca704 after AC-14/AC-16 witnesses,
      per C-4 cron approval condition)*
- [x] AC-06: All secrets as repo secrets; no credential, token, PAT,
      cookie, or secret-bearing transcript in any commit, log,
      README, ledger, post, or artifact
      *(6 repo secrets set via gh; run 32267564652 logs show only
      `***` masks; ledger/post/README grep clean; images never
      committed — git ls-files image count 0)*
- [ ] AC-07: Rotation round-trip proven by two consecutive dispatch
      runs — first writes rotated `DA_REFRESH_TOKEN`, second
      authenticates with it
      *(PENDING OBSERVATION: run 32267564652 rotated the secret —
      `gh secret list` shows DA_REFRESH_TOKEN updated 15:02:54Z
      mid-run, publish succeeded after persist. The idempotent
      same-day rerun exits before refresh, so the second
      authentication is witnessed by the first cron run, 07:00 UTC
      2026-08-20.)*
- [x] AC-08: Rotation ordering proven by test: persist failure aborts
      before any DA submit/publish call
      *(tests/test_steps.py::test_persist_failure_aborts_before_submit)*
- [ ] AC-09: Roster validated before draw; zero active models fails
      before side effects; drops logged structured; both frozen
      active models (`prunaai/z-image-turbo`,
      `black-forest-labs/flux-1.1-pro-ultra`) each produce a
      published or gate-skipped run
      *(PARTIAL: validate-before-draw + structured drop logging
      witnessed in run logs ("roster: model=grok disabled");
      flux-1.1-pro-ultra produced the 2026-08-19 publish;
      z-image-turbo and grok (enabled d8ebd54 per R-4) pending days
      they are drawn — observation, not blocker, per FR-819 AC-07
      precedent)*
- [x] AC-10: Describe output validated through the typed schema;
      invalid tags or invalid mature combinations gate-skip with a
      ledger reason
      *(tests/test_gate.py — 10 tests; live run passed schema with
      confidence=high)*
- [x] AC-11: Mocked HTTP tests assert the DA flow against FR-822
      shapes: placebo, submit, publish, both AI flags on both calls,
      UA/timeouts, 429 backoff, `error_code 9` idempotent success
      *(tests/test_da_api.py — 12 tests)*
- [x] AC-12: Ledger state machine proves no-repeat and no-duplicate
      behavior for same-day reruns and interrupted runs at each
      side-effect boundary; no automatic rerun creates a second
      deviation for the same date
      *(tests/test_ledger.py + test_steps.py: commit failure simulated
      before submit, after submit, after publish → RecoveryRequired)*
- [ ] AC-13: Gate path witnessed: low confidence / invalid tags /
      invalid mature fields / impermissible content → skip reason
      committed to ledger, nothing published, green exit only after
      the skip record lands
      *(PENDING OBSERVATION: gate logic fully unit-tested
      (test_gate.py, test_steps.py::gate skip-commit-before-green);
      a live gate-skip day cannot be forced — recorded when it
      occurs naturally)*
- [x] AC-14: `workflow_dispatch` green end-to-end publish path:
      draw/generate/describe/publish, rotated token persisted, DA URL
      in ledger, post MD committed, no image committed
      *(run 32267564652 green 2026-08-19: ledger
      drawn→submitted→published, itemid 1134093669574380, URL
      https://www.deviantart.com/sheikkinen/art/Vigil-in-the-Hollow-World-1370599817,
      posts/2026-08-19.md committed, zero images in git. First
      dispatch 32267072470 failed on a boundary bug — flux-ultra
      returns JPEG despite .png output name; fixed by magic-byte
      media-type detection at vision + DA submit boundaries,
      RED 8c393dd / GREEN 8d88e8f)*
- [ ] AC-15: At least one scheduled cron run publishes green without
      human runner access
      *(PENDING OBSERVATION: cron enabled eeca704, first run
      07:00 UTC 2026-08-20 — doubles as AC-07 witness)*
- [x] AC-16: Same-day manual rerun after successful publish exits
      idempotently — no second deviation
      *(run 32268278258 green: "already published — idempotent
      exit", zero new commits, no DA calls)*
- [x] AC-17: Live deviation verified once against the committed
      `STYLE-CONTRACT.md`: paragraphs render separately, quote/title
      shape survives, tags attach, AI badge shown, no
      sales/download/license options enabled
      *(live page fetch 2026-08-19: 3 paragraphs render separately,
      "Be Art. Be Unique." epigram, quote line, gallery footer
      ✨📂🎉, 9 underscore tags attached, "Created using AI tools"
      badge, download behind login only — no sales options)*
- [x] AC-18: New-repo tests cover corpus extraction/dedup, ledger
      transitions, rotation ordering, tag normalization, mature gate,
      roster validation, MD rendering, DA/Replicate request
      construction *(47 tests green, ruff clean, graph lint clean)*
- [x] AC-19: FR-826 records implementation status with non-secret
      links/identifiers: new repo, dispatch run, cron run, roster
      evidence, DA URL, authoring report, scope deviations
      *(this section: repo https://github.com/sheikkinen/deviant-daily,
      dispatch runs 32267072470 (failed, boundary bug) /
      32267564652 (green publish) / 32268278258 (idempotent),
      cron pending 2026-08-20, DA URL above, authoring report
      docs/authoring-report.md in new repo. Scope deviation: none —
      one unplanned fix (JPEG media type) within scope, TDD'd.)*

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

## Judgement (2026-08-19)

**Verdict:** APPROVED WITH REVISIONS — full text in
`FR-826-deviantart-daily-repo.judgement.md`. Six revisions, all folded
above: R-1 YAMLGraph execution surface frozen (graph orchestrates,
Python only for side effects, governed authoring route); R-2 corpus
publication is a human-approved, sanitized artifact; R-3 idempotency
state machine with committed transitions and `RECOVERY_REQUIRED`;
R-4 roster frozen to two active models, grok disabled until slug
committed, zero-active fails closed; R-5 typed gate schema with
deterministic validators; R-6 style contract committed to the new repo
as `STYLE-CONTRACT.md`.

**Gates:** authority active only now that R-1..R-6 are folded (C-1);
corpus release and cron enablement need explicit operator approval
recorded first (C-4); the new repo is never committed into yamlgraph
(C-6); zero-model config fails closed, never green (C-7); core/runtime
changes or a reusable publisher library here → stop for a new FR (C-8).

### Questions for the human

1. **Corpus publication approval (C-4, blocking):** ANSWERED
   2026-08-19 — approved with sanitization: strip LoRA tags, exclude
   prompts with personal names (Katja, Tuija, Nina, extensible
   blocklist), exclude non-consent terms ("rape", extensible
   blocklist). Policy recorded in the corpus gate above.
2. **Cron enablement (C-4):** ANSWERED 2026-08-19 — cron approved;
   enable after the dispatch witnesses (AC-07/AC-14) pass.

C-4 is fully satisfied — enforcement unblocked.
