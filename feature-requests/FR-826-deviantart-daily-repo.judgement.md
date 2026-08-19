# Judgement: FR-826 DeviantArt Daily Auto-Publish Repo (GitHub-Actions-Native) (DRAFT)

**Verdict:** APPROVED WITH REVISIONS — the Actions-native DeviantArt repo is a sound contrib/product artifact, but authority activates only after the FR freezes the YAMLGraph execution surface, public-corpus approval, external-publish idempotency, model roster, DA gate schema, and committed style contract.

**Reviewed against:** `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-819-github-native-digest-poc-repo.md`; `feature-requests/FR-822-deviantart-publish-spike.md`; `feature-requests/FR-822-deviantart-publish-spike.judgement.md`; `feature-requests/FR-781-macos-file-hook-example.md`; `feature-requests/FR-781-macos-file-hook-example.judgement.md`; `feature-requests/FR-769-shared-vision-tool.md`; `feature-requests/FR-769-shared-vision-tool.judgement.md`; `feature-requests/FR-772-tool-call-inline-dict-args.md`; `feature-requests/FR-772-tool-call-inline-dict-args.judgement.md`; `docs/research-deviantart-api-2026-08-19.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`.


**Prior art:** dispositioned in "What is sound" below — FR-819 (substrate pattern), FR-822 (API contracts, spike quarantined), FR-781/FR-769 (describe/vision precedent), FR-772 (noun coincidence); FR-826 is the subject FR.

## What is sound

The first consumer and first event are concrete: the sheikkinen DeviantArt gallery gets a daily generated image and post without human intervention, and the public repo becomes a visible "yamlgraph runs unattended" Proclaim artifact (`feature-requests/FR-826-deviantart-daily-repo.md:9-15`, `43-46`). That is a real use case, not growth by default.

The prior-art chain is directionally correct. FR-819 proves the Actions-native pattern where the repo is runtime, state store, and publication channel (`feature-requests/FR-819-github-native-digest-poc-repo.md:17-22`) and already froze concurrency/no-op behavior for cron plus dispatch runs (`feature-requests/FR-819-github-native-digest-poc-repo.md:102-108`). FR-822 records live DeviantArt API evidence for PKCE, refresh rotation, submit, publish, paragraph rendering, tags, and AI badge (`feature-requests/FR-822-deviantart-publish-spike.md:153-183`), while the research doc establishes the required DA fields, tag constraints, OAuth rotation, and error taxonomy (`docs/research-deviantart-api-2026-08-19.md:15-49`, `51-79`).

The architecture target is aligned if kept as a separate public repo. FR-826 explicitly bars yamlgraph core changes and local launchd retirement (`feature-requests/FR-826-deviantart-daily-repo.md:198-201`), and the graph-authoring boundary is already acknowledged for any `graph.yaml` or `prompts/*.yaml` artifacts (`feature-requests/FR-826-deviantart-daily-repo.md:137-141`; `.github/copilot-instructions.md:15`). Strategic classification: **Contrib/example / product repo**, not a framework primitive; it should demonstrate existing YAMLGraph patterns plus side-effect tools, not add YAMLGraph runtime semantics.

The split from the earlier local publisher is justified. The FR rejects the iMac-bound local CLI path and chooses the FR-819 Actions-native shape (`feature-requests/FR-826-deviantart-daily-repo.md:203-211`), which is the smaller path back from the ideal unattended daily publication.

## Required revisions

### R-1: Freeze the YAMLGraph execution surface

Revise the FR so the new repo's execution shape matches its own Proclaim claim. The FR says the artifact proves "yamlgraph runs unattended" (`feature-requests/FR-826-deviantart-daily-repo.md:13-15`) and inherits the FR-819 repo pattern, whose scaffold includes `graph.yaml`, `prompts/`, nodes, and a runner (`feature-requests/FR-819-github-native-digest-poc-repo.md:53-64`). But FR-826's scaffold lists only `prompts/corpus.jsonl`, `state/published.jsonl`, and `posts/YYYY-MM-DD.md` (`feature-requests/FR-826-deviantart-daily-repo.md:77-89`), and then makes graph/prompt authoring conditional (`feature-requests/FR-826-deviantart-daily-repo.md:137-141`).

Fold this mechanically by stating that the daily pipeline is a YAMLGraph graph in the new repo, with Python tools only for side effects (corpus draw, Replicate call, DA API, ledger/post writes). A plain Python entrypoint may bootstrap `yamlgraph graph run`, but it must not be the real orchestration layer. The new repo must include `graph.yaml` and any YAML prompt artifacts needed for the describe/post step, authored through `scripts/author.sh` from this workspace with `tmp/draft-authoring-report.md` or a copied enforcement evidence report recording lint and smoke results. If the FR deliberately chooses a plain-Python pipeline instead, remove the "yamlgraph runs unattended" claim and re-enter judgement because the strategic classification changes.

### R-2: Make public corpus publication a human-approved, sanitized artifact

Revise the corpus contract so the judge and enforcer do not silently absorb a product/privacy decision. The FR commits a public `prompts/corpus.jsonl` extracted from `~/Documents/deviant-working/signed.log` (`feature-requests/FR-826-deviantart-daily-repo.md:33-39`, `77-81`) and makes the prompt history part of the public provenance record (`feature-requests/FR-826-deviantart-daily-repo.md:60-68`). The existing AC only excludes EXIF dumps and file paths beyond source names (`feature-requests/FR-826-deviantart-daily-repo.md:154-157`), but it does not record explicit human approval to publish the corpus or a redaction/sanitization method. Human product/safety decisions must be surfaced rather than absorbed by the judge (`.github/skills/judge-fr/doctrine.md:100-101`).

Fold this by adding an explicit corpus-publication gate: before the public repo is created or populated, the operator must approve publishing the prompt corpus, the FR or new-repo README must record the approval date, the corpus count, and the redaction policy, and the extraction output must prove it contains only `{prompt, source_file}` where `source_file` is a basename or stable non-reversible identifier, never an absolute local path. Add a mechanical secret/private-data scan over the corpus before commit, plus a human sample-review witness for a random slice of the extracted prompts. If any prompt cannot safely be public, it must be redacted or excluded before the corpus lands.

### R-3: Define the external-publish idempotency boundary

Revise the ledger and commit-back design for the fact that DeviantArt publish is an external side effect but the repo ledger is the dedup guard. FR-826 currently says drawn prompts are excluded from future draws and "a date already in the ledger" makes reruns idempotent (`feature-requests/FR-826-deviantart-daily-repo.md:82-86`), but the workflow publishes first and commits the post/ledger afterward (`feature-requests/FR-826-deviantart-daily-repo.md:129-135`). That leaves an unhandled failure window: if DA publish succeeds and the commit/push fails, the repo has no ledger URL and a same-day rerun can publish a second deviation. FR-819's committed-state pattern was sufficient for a repo-only publication, but this FR adds a second system of record (`feature-requests/FR-819-github-native-digest-poc-repo.md:102-108`).

Fold one exact state machine into the FR. Minimum acceptable contract: `state/published.jsonl` records statuses such as `drawn`, `submitted`, `published`, and `skipped`; every transition that protects an external side effect is committed with FR-819-style concurrency, no-op handling, and `git pull --rebase` before push; a rerun seeing an incomplete same-day record resumes or fails safely instead of drawing a new prompt; and tests simulate commit/push failure before publish, after stash submit, and after publish to prove no automatic second public deviation is created. If the implementation cannot make post-publish commit failure self-healing, the FR must require a visible `RECOVERY_REQUIRED` failure that includes the non-secret DA URL/item identifier and blocks automatic republish until the ledger is repaired.

### R-4: Freeze the Replicate model roster and zero-active behavior

Revise the generation roster from "verified at enforce time" into a judged, testable contract. The FR names `z-image`, FLUX, and grok, but leaves the grok Replicate slug unresolved and says absent models are "dropped with a logged notice, never a crash" (`feature-requests/FR-826-deviantart-daily-repo.md:112-119`). That is not measurable and can turn a configuration error into a green skipped system, contradicting repo doctrine that filters must not silently substitute success-shaped behavior (`.github/copilot-instructions.md:218`).

Fold this by listing the exact initial model IDs that are authorized, or by marking unresolved candidates disabled until their slug is committed. The runner must validate the roster before drawing: zero active models is a hard failure before any corpus draw or DA side effect; one active model is allowed only if the FR revises the "at least two roster models" acceptance criterion; an unavailable optional model may be dropped only after logging the model ID and reason. AC-09 must be rewritten so it cannot be satisfied by silent drops: either two named active models are exercised, or the FR narrows the roster and records why.

### R-5: Make the DA publish schema, tag normalization, and mature gate mechanical

Revise the describe/publish gate so tests can be derived directly from it. The research doc says tags are restricted to letters, numbers, and underscore and that mature publishing requires `is_mature`, `mature_level`, and `mature_classification[]` with enum values (`docs/research-deviantart-api-2026-08-19.md:21-49`). FR-826's schema names the right fields (`feature-requests/FR-826-deviantart-daily-repo.md:120-124`), but the gate says "mature classification beyond what DA permits for API publishing" without enumerating the allowed and forbidden cases (`feature-requests/FR-826-deviantart-daily-repo.md:125-128`).

Fold this by specifying a Pydantic output model and deterministic validators: `confidence` is an enum where only `high` may publish; `tags` are normalized to `[a-z0-9_]+` or rejected; `mature_level` is `strict | moderate | None`; `mature_classification` is a subset of DA's allowed enum; `mature=true` requires level and at least one classification; `mature=false` requires no mature level/classification; invalid or policy-forbidden results gate-skip with a ledger reason. The publish step must pass `is_ai_generated=true` and `noai=true` on both submit and publish, and tests must assert the exact form fields against FR-822's recorded response shapes.

### R-6: Commit or snapshot the julkaisuohje style contract

Revise the FR so the describe/post style contract is inside input closure for enforcement and review. FR-826 says `DEVIANTART-JULKAISUOHJE.md` remains the frozen style contract (`feature-requests/FR-826-deviantart-daily-repo.md:189-190`) and AC-10 requires live verification against the julkaisuohje contract (`feature-requests/FR-826-deviantart-daily-repo.md:180-182`), but that file was not present in the committed repo path available to this judgement. FR-781 proves a file-hook prompt can be a julkaisuohje-derived artifact (`feature-requests/FR-781-macos-file-hook-example.md:83-86`), but FR-826 must not depend on an uncited local file as the source of truth.

Fold this by committing the style contract or a derived prompt snapshot to the new repo, or by adding the exact style instructions to FR-826 before enforcement. The acceptance criteria must require a render witness that checks paragraph separation, quote/title shape, tag attachment, AI badge, and the absence of forbidden sales/download/license options named by the research doc (`docs/research-deviantart-api-2026-08-19.md:89-94`). Do not let "julkaisuohje-style" remain an untestable prose label.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-826-deviantart-daily-repo.md` folding R-1 through R-6 |
| D-2 | New separate public repository `sheikkinen/deviant-daily` with workflow, YAMLGraph graph, YAML prompts, Python side-effect tools, tests, README, corpus, ledger, and post artifacts |
| D-3 | Governed graph-authoring evidence for any `graph.yaml` or `prompts/*.yaml` artifacts created or adapted from this workspace |
| D-4 | Corpus extraction/redaction evidence and human approval record, with only the sanitized corpus committed to the new repo |
| D-5 | DA/Replicate mocked unit tests plus live dispatch/cron witnesses in the new repo |
| D-6 | FR implementation-status update in this repo and a diary reflection if enforcement modifies this repo |

Not authorized: yamlgraph core changes; local launchd/file-hook retirement; browser automation of DeviantArt Studio; batch/backlog publishing; committing generated images; external prompt sources; unreviewed public release of the full local `signed.log`; storing credentials, token JSON, cookies, or token-bearing transcripts in any commit/log/artifact; reusable DeviantArt publisher code inside this repo; Marketplace/GitHub App packaging; modifying FR-819/FR-822 artifacts; manual edits to governed graph or prompt artifacts outside the graph-authoring route.

## Revised acceptance criteria

- [ ] AC-01: FR-826 is revised to include the exact YAMLGraph execution surface, public-corpus approval/sanitization gate, external-publish idempotency state machine, frozen model roster, deterministic DA gate schema, and committed/snapshotted style contract from R-1 through R-6.
- [ ] AC-02: The public `sheikkinen/deviant-daily` repo exists outside this repository and is not committed here as a nested repo, submodule, vendored directory, generated artifact, or archive.
- [ ] AC-03: The new repo contains a YAMLGraph `graph.yaml` and required YAML prompt artifacts for orchestration/description; governed authoring evidence records lint and smoke validation for those artifacts.
- [ ] AC-04: `prompts/corpus.jsonl` is committed only after operator approval and sanitization; the README records corpus count, extraction source, approval date, and redaction policy; each row contains only `{prompt, source_file}` with no absolute paths, EXIF dumps, token-like strings, or non-prompt `signed.log` content.
- [ ] AC-05: The workflow has `workflow_dispatch`, a daily cron, `permissions: contents: write`, a repo-specific concurrency group with `cancel-in-progress: false`, safe `git pull --rebase` before push, and no shell tracing that can print secrets.
- [ ] AC-06: All required secrets are configured as repo secrets; no credential, access token, refresh token, PAT, token file, cookie, or secret-bearing transcript appears in any commit, workflow log, README, ledger, post, or artifact.
- [ ] AC-07: Refresh rotation round-trip is proven by two consecutive dispatch runs: the first refresh writes the rotated `DA_REFRESH_TOKEN` using the scoped secret-writing credential, and the second authenticates with the rotated token.
- [ ] AC-08: Rotation ordering is proven by test: failure to persist the new refresh token aborts before any DA submit or publish call.
- [ ] AC-09: The model roster is validated before draw/generate; zero active models fails before side effects; unavailable optional models log a structured drop; at least two frozen active model IDs each produce a published or gate-skipped run unless the revised FR explicitly narrows the roster.
- [ ] AC-10: The describe output is validated through a typed schema covering title, paragraphs, quote, normalized tags, confidence, mature flag, mature level, and mature classifications; invalid tags or invalid mature combinations gate-skip with a ledger reason.
- [ ] AC-11: Mocked HTTP tests assert the DA flow against FR-822 shapes: `placebo`, `stash/submit`, `stash/publish`, `is_ai_generated=true`, `noai=true`, user-agent/timeouts, 429 backoff, and `error_code 9` as idempotent success for an already-published stash item.
- [ ] AC-12: The ledger state machine proves no-repeat and no-duplicate behavior for successful same-day reruns and for interrupted runs at each external side-effect boundary; no automatic rerun can create a second public deviation for the same date.
- [ ] AC-13: Gate path is witnessed: low confidence, invalid tags, invalid mature fields, or DA-impermissible content records a skip reason in the ledger, publishes nothing, and exits green only after the skip record is committed.
- [ ] AC-14: `workflow_dispatch` completes green end-to-end for a publish path: draw/generate/describe/publish, rotated-token persistence, DA URL in the ledger, post markdown committed, README/index updated if present, and no generated image committed.
- [ ] AC-15: At least one scheduled cron run completes green and publishes without human runner access.
- [ ] AC-16: Same-day manual rerun after a successful publication exits idempotently and does not create a second deviation.
- [ ] AC-17: Post markdown on the live deviation page is verified once against the committed style contract: paragraphs render separately, quote/title shape survives, tags attach, AI badge is shown, and out-of-scope sales/download/license options are not enabled.
- [ ] AC-18: New-repo tests cover corpus extraction/dedup, ledger state transitions, token rotation ordering, tag normalization, mature gate, model-roster validation, Markdown rendering, and DA/Replicate HTTP request construction.
- [ ] AC-19: FR-826 records implementation status with links or non-secret identifiers for the new repo, dispatch run, cron run, model-roster evidence, DA deviation URL, graph-authoring report, and any deviations from frozen scope.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-826-deviantart-daily-repo.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | Any `graph.yaml` or `prompts/*.yaml` artifact created or materially adapted from this workspace must use the governed graph-authoring route; manual graph/prompt authoring is not authorized. | GATE |
| C-4 | Public corpus release and autonomous daily publishing require explicit operator approval recorded in the FR or new repo before cron is enabled. | GATE |
| C-5 | No secret-bearing value may be printed, committed, uploaded as an artifact, or preserved in transcript form; use stdin/file-safe secret update mechanisms and keep workflow shell tracing disabled. | GATE |
| C-6 | The new repo boundary is hard: do not vendor, submodule, archive, or commit the new repo into yamlgraph. | GATE |
| C-7 | If the model roster cannot be validated to at least one active model before side effects, the run must fail closed; do not convert a zero-model configuration into a green skipped day. | GATE |
| C-8 | If enforcement requires yamlgraph core/runtime changes, DeviantArt browser automation, or a reusable publisher library in this repo, stop for a new FR. | GATE |
| C-9 | Any GitHub permission broader than the listed repo-scoped secret-writing credential requires explicit human review before use in the public repo. | GATE |

Authority granted: after the required revisions are folded, enforcement may build the separate Actions-native DeviantArt daily publishing repo and the directly necessary graph, prompts, side-effect tools, tests, corpus, workflow, and documentation within the frozen scope above.
