# Judgement: FR-862 deviant-daily On-Demand Publish (Dispatchable Pipeline)

**Verdict:** APPROVED WITH REVISIONS — the on-demand publish direction is sound, but authority activates only after the FR folds in strict workflow-input normalization, honest dry-run cost semantics, slot-state invariants, graph-authoring governance for the sibling repo, and a human gate for the forced live publish witness.

**Reviewed against:** `feature-requests/FR-862-deviant-daily-on-demand-publish.md`; `feature-requests/FR-826-deviantart-daily-repo.md`; `feature-requests/FR-826-deviantart-daily-repo.judgement.md`; `feature-requests/FR-822-deviantart-publish-spike.md`; `feature-requests/FR-822-deviantart-publish-spike.judgement.md`; `feature-requests/FR-819-github-native-digest-poc-repo.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; cited target repo `sheikkinen/deviant-daily` at commit `568df8b`: `.github/workflows/daily.yml`, `graph.yaml`, `README.md`, `state/published.jsonl`, `tools/ledger.py`, `tools/corpus.py`, `tools/post.py`, `tools/roster.py`, `tools/steps.py`, `tests/test_ledger.py`, `tests/test_roster_corpus_post.py`, `tests/test_steps.py`.

**Prior art:** dispositioned in "What is sound" below — FR-826 (parent: ledger/roster invariants this FR extends), FR-822 (DA API contracts, incl. refresh rotation), FR-819 (Actions-native cron+dispatch and shared-concurrency precedent); FR-781 (vision/describe precedent) and FR-827/FR-828 (gitclaw product line) are noun coincidences with no overlap. No REJECTED prior art occupies this territory. FR-862 is the subject FR.

## What is sound

The first consumer is concrete and time-bound: the operator needs to exercise newly changed roster entries immediately after the 2026-08-23 roster commit, instead of waiting for a 07:00 UTC cron plus random selection (`feature-requests/FR-862-deviant-daily-on-demand-publish.md:8-15`). The target repo evidence supports the problem statement: `daily.yml` currently passes only `--var date="$(date -u +%F)"` to the graph (`sheikkinen/deviant-daily@568df8b:.github/workflows/daily.yml:30-31`), the graph exits at `END` when `drawn.result.done == true` (`sheikkinen/deviant-daily@568df8b:graph.yaml:94-99`), and `draw_step` treats a terminal same-day ledger entry as an idempotent exit (`sheikkinen/deviant-daily@568df8b:tools/steps.py:45-68`). The no-op complaint is therefore real, not invented.

The slot direction preserves the parent FR's core invariant better than overloading `date`. FR-826 requires ledger transitions around external DA side effects and no automatic second same-day deviation (`feature-requests/FR-826-deviantart-daily-repo.md:132-145`), then records AC-16 as a witnessed same-day manual rerun that produced no second DA call (`feature-requests/FR-826-deviantart-daily-repo.md:316-319`). FR-862 correctly keeps default slot 0 as the scheduled path and allocates higher slots only when the operator explicitly forces after a terminal slot (`feature-requests/FR-862-deviant-daily-on-demand-publish.md:72-120`).

The model-targeting and dry-run goals are appropriately scoped to the product repo rather than YAMLGraph core. The active roster already contains `z-image`, `flux-2-flex`, `nano-banana-2`, and `grok` (`sheikkinen/deviant-daily@568df8b:tools/roster.py:22-52`), while `choose_model()` is currently unconditional random selection (`sheikkinen/deviant-daily@568df8b:tools/roster.py:79-82`). Adding an explicit-name path is a small extension at the right boundary.

The workflow factoring proposal follows existing precedent. FR-819 froze the GitHub Actions repo-as-runtime pattern, including shared concurrency and `pull --rebase` before push (`feature-requests/FR-819-github-native-digest-poc-repo.md:102-108`), and FR-826 inherited that pattern for `deviant-daily` (`feature-requests/FR-826-deviantart-daily-repo.md:22-28`, `243-248`). A reusable workflow body plus two callers is a reasonable way to avoid drift, provided the callers retain one shared concurrency group.

Strategic classification: **Contrib/product repo enhancement**. This is not a YAMLGraph framework primitive; it modifies a sibling product repo to expose existing pipeline behavior safely on demand.

## Required revisions

### R-1: Normalize all dispatch inputs at the workflow/graph boundary

Fold a strict input-normalization contract into the FR before enforcement. FR-862 proposes YAMLGraph state fields `model: str`, `dry_run: str`, and `force: str`, then passes them to Python functions with boolean defaults (`feature-requests/FR-862-deviant-daily-on-demand-publish.md:159-167`). That is unsafe because workflow and CLI variables commonly arrive as strings: `"false"` is truthy in Python, and `"random"` is not the same as an omitted model. A stringly boolean bug here can silently turn `force=false` or `dry_run=false` into the opposite behavior.

Fold this mechanically by requiring one boundary helper, used by graph-facing step functions, that maps `""` to the scheduled default, parses booleans from only `true|false` (case-insensitive), rejects any other value, validates `date` as empty or ISO `YYYY-MM-DD`, validates `slot` as a non-negative integer when supplied, and treats `model in {"", "random"}` as random while validating any other model against `ACTIVE_MODELS`. Add tests proving `"false"` is false, `"true"` is true, empty inputs preserve the cron path, `"random"` does not raise, an unknown model raises `RosterError`, and invalid dates/booleans fail before ledger, Replicate, Anthropic, or DeviantArt side effects.

### R-2: Correct the dry-run contract so it is honest about cost and side effects

Revise the FR's "free" claim. It says the pipeline can be started "for free" and calls dry run "free" (`feature-requests/FR-862-deviant-daily-on-demand-publish.md:19-25`, `27-31`), but the proposed dry-run path still runs image generation and description unless the FR adds a separate mock/no-generate mode. The current target pipeline's `generate_step` calls Replicate and `describe_step` calls the vision LLM (`sheikkinen/deviant-daily@568df8b:tools/steps.py:71-78`), so dry-run is no-DA/no-publication, not zero-cost.

Fold this by replacing "free" with the exact guarantee: `dry_run=true` performs no ledger commits, no post commits, no DA OAuth/submit/publish calls, no `gh secret set`, and does not require DA secrets; it may still spend Replicate and LLM provider tokens unless a future separate FR adds a no-generate/mock mode. The acceptance criteria must assert zero `record_transition`, zero `da_api`, and zero secret-persist invocations using injected fail-fast runners/sessions, and must assert that the workflow artifact contains the generated image plus the gate-passing post dict when the gate publishes.

### R-3: Make slot identity complete across helpers, ledger entries, and post paths

Revise the slot design so no date-only lookup remains on the publish path. The current helper stack is date-only: `entry_for_date()` returns the latest row for a date (`sheikkinen/deviant-daily@568df8b:tools/ledger.py:38-41`), `draw_prompt()` resumes by date alone (`sheikkinen/deviant-daily@568df8b:tools/corpus.py:32-46`), and `publish_step()` writes `posts/{date}.md` (`sheikkinen/deviant-daily@568df8b:tools/steps.py:157-170`). FR-862 proposes `(date, slot)` identity, but its acceptance criteria do not require every transition row and every lookup to abandon date-only identity.

Fold this mechanically by requiring `read_ledger()` to normalize old slot-less rows to integer `slot: 0`, reject non-integer or negative `slot` values, and expose slot-aware helpers only on the run-selection path. Every transition row written by `draw_step`, `gate_step`, and `publish_step` must include the selected slot. `draw_prompt()` must either accept the selected `(date, slot)` resume context or stop performing date-only resume decisions itself. Tests must prove terminal slot 0 with `force=true` allocates slot 1, terminal slot 1 with `force=true` allocates slot 2, in-flight latest slot resumes even when `force=true`, slot 0 still writes `posts/<date>.md`, slot N writes `posts/<date>-<N>.md`, and `used_source_ids` remains global across slots so forced extra posts cannot reuse an already published prompt.

### R-4: Apply the graph-authoring route to the sibling repo graph change

Answer the FR's open governance question directly in the FR: yes, this is graph authoring. FR-862 materially modifies `graph.yaml` and possibly workflow-adjacent prompt plumbing in `sheikkinen/deviant-daily` (`feature-requests/FR-862-deviant-daily-on-demand-publish.md:159-167`, `243-248`). Repo doctrine says any new or materially modified `graph.yaml` or `prompts/*.yaml` artifact must use the governed graph-authoring route, and FR-819/FR-826 already applied that rule to sibling public repos (`.github/copilot-instructions.md:15`; `feature-requests/FR-819-github-native-digest-poc-repo.md:131-138`; `feature-requests/FR-826-deviantart-daily-repo.md:82-92`).

Fold this by adding an acceptance criterion requiring graph-authoring evidence for the target repo graph/prompt changes: the authoring brief/report must be preserved in the enforcement record, graph lint must pass, and a smoke run must cover the unchanged scheduled path plus a dry-run dispatch path. This judgement does not authorize manual graph/prompt edits outside that route.

### R-5: Gate the live forced-publish witness with explicit operator approval

Add a human approval condition for AC-11. A `force=true` non-dry run intentionally creates a second public DeviantArt post on a date that already has one (`feature-requests/FR-862-deviant-daily-on-demand-publish.md:193-195`). That is a product/spend/publication decision, not a judgement decision; the judge doctrine requires human decisions to be surfaced rather than absorbed (`.github/skills/judge-fr/doctrine.md:100-101`).

Fold this by requiring an explicit operator approval note, recorded before the live forced publish witness is run. Unit/integration tests may cover forced slot allocation without that approval, but the public second-DA-URL witness must not be attempted until approval is recorded.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-862-deviant-daily-on-demand-publish.md` folding R-1 through R-5 |
| D-2 | Sibling repo `sheikkinen/deviant-daily`: `.github/workflows/_pipeline.yml`, revised `.github/workflows/daily.yml`, new `.github/workflows/publish-now.yml` |
| D-3 | Sibling repo `sheikkinen/deviant-daily`: slot-aware `tools/ledger.py`, `tools/corpus.py`, `tools/steps.py`, `tools/roster.py`, and post-path rendering changes |
| D-4 | Sibling repo `sheikkinen/deviant-daily`: governed `graph.yaml` changes, and prompt changes only if the authoring route/report covers them |
| D-5 | Sibling repo tests for input normalization, dry-run no-DA/no-ledger behavior, explicit model selection, slot identity, workflow concurrency/input shape, and scheduled-path regression |
| D-6 | `README.md` documentation in `sheikkinen/deviant-daily` describing `daily-publish`, `publish-now`, `dry_run`, `model`, `force`, and `date` semantics |
| D-7 | FR implementation-status update with non-secret workflow run IDs, dry-run artifact evidence, optional approved forced-publish witness, and graph-authoring evidence |

Not authorized: YAMLGraph core/runtime changes; judge/review/graph-authoring doctrine changes; modifications to `feature-requests/FR-819*`, `FR-822*`, or `FR-826*`; corpus extraction or sanitization policy changes; prompt/style-contract changes unless required by the graph-authoring route for this FR; new model roster entries beyond the already cited `568df8b` roster; batch/backlog publishing; deleting/unpublishing DeviantArt posts; browser automation; committing generated images, credentials, token values, token-bearing logs, or private transcripts; a reusable DeviantArt publisher library outside the product repo.

## Revised acceptance criteria

- [ ] AC-01: FR-862 is revised to include strict boundary normalization for `dry_run`, `force`, `model`, `date`, and `slot`, honest dry-run cost semantics, slot identity across all ledger transitions, graph-authoring evidence for target graph changes, and the human approval gate for forced live publishing.
- [ ] AC-02: `publish-now.yml` exposes `workflow_dispatch` inputs `dry_run` (boolean, default `true`), `model` (choice: `random` plus the current `ACTIVE_MODELS` names only), `force` (boolean, default `false`), and `date` (string, default `""`).
- [ ] AC-03: `daily.yml` and `publish-now.yml` both call the reusable `_pipeline.yml` body and declare the same `concurrency.group: daily-publish` with `cancel-in-progress: false`; a test parses both workflow files and fails on drift.
- [ ] AC-04: The reusable workflow body preserves the scheduled path: daily cron passes no model, force, dry-run, or date override beyond today's UTC date, and the unforced slot-0 terminal rerun still exits idempotently without DA calls.
- [ ] AC-05: Boundary tests prove empty boolean inputs use scheduled defaults, `"false"` is false, `"true"` is true, invalid boolean strings fail before side effects, empty/`random` model selects randomly, a valid explicit model returns exactly that config, and an unknown explicit model raises `RosterError`.
- [ ] AC-06: `dry_run=true` performs zero `record_transition` calls, zero `da_api` calls, zero `gh secret set` calls, zero git commits, and exits green with all DA secrets absent; fail-fast injected runner/session tests prove this.
- [ ] AC-07: A dry-run dispatch that gate-passes uploads a workflow artifact containing the generated image and the gate-passing post dict, with no credentials or token-bearing data in the artifact.
- [ ] AC-08: `read_ledger()` normalizes every slot-less committed row in `state/published.jsonl` to `slot: 0` at read time and rejects non-integer or negative slot values.
- [ ] AC-09: Every newly written ledger transition (`drawn`, `submitted`, `published`, `skipped`) includes `slot`, and no run-selection helper on the publish path resumes or terminates by date alone.
- [ ] AC-10: Force semantics are mechanically tested: terminal slot 0 plus `force=false` returns `done: true`; terminal slot 0 plus `force=true` allocates slot 1; terminal slot 1 plus `force=true` allocates slot 2; in-flight latest slot plus `force=true` resumes that slot and allocates nothing.
- [ ] AC-11: Post paths are slot-aware: slot 0 writes `posts/<date>.md`, slot N writes `posts/<date>-<N>.md`, and the committed post markdown records the slot.
- [ ] AC-12: Corpus no-repeat remains global across slots: a forced extra post cannot reuse any `source_file` already present in the ledger for any date or slot.
- [ ] AC-13: With `model`, `dry_run`, and `force` unset, `draw_step` and `generate_step` behavior is regression-pinned to the current scheduled path: random model selection, date-derived slot 0, same-day terminal no-op, and `posts/<date>.md`.
- [ ] AC-14: Governed graph-authoring evidence exists for material `graph.yaml` or `prompts/*.yaml` changes in `sheikkinen/deviant-daily`, including graph lint and smoke validation for the scheduled path and dry-run dispatch path.
- [ ] AC-15: `README.md` in `sheikkinen/deviant-daily` documents both workflows and the exact semantics of `dry_run`, `model=random`, explicit model names, `force`, date override, slot numbering, artifacts, and required secrets.
- [ ] AC-16: Tests are added before implementation for the defects above, and the FR records the RED/GREEN evidence or equivalent failing-test witness.
- [ ] AC-17: Witness — a real `publish-now` dispatch with `dry_run=true` and `model=nano-banana-2` completes green; the FR records the run id and artifact contents (PNG plus gate-passing post dict), with no DA secret requirement and no DA publish URL.
- [ ] AC-18: Witness — only after explicit operator approval is recorded, a real `publish-now` dispatch with `force=true` and `dry_run=false` on a date that already has a terminal slot publishes a second DA URL and records `slot: 1` or higher in the ledger and post markdown.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-5 are folded into `feature-requests/FR-862-deviant-daily-on-demand-publish.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | Any material `graph.yaml` or `prompts/*.yaml` change in `sheikkinen/deviant-daily` must use the governed graph-authoring route and retain the authoring report as enforcement evidence. | GATE |
| C-4 | `daily.yml` and `publish-now.yml` must share the same concurrency group before any live dispatch witness is run. | GATE |
| C-5 | Dry-run artifacts, logs, ledger rows, posts, and FR updates must not contain credentials, refresh tokens, access tokens, PATs, cookies, or token-bearing transcripts. | GATE |
| C-6 | A non-dry forced live publish may not be run until explicit operator approval for that second public post is recorded. | GATE |
| C-7 | If enforcement requires YAMLGraph core/runtime changes, a reusable DeviantArt publisher library outside the product repo, or a no-generate/mock dry-run mode to satisfy "free", stop and write a separate FR. | GATE |
| C-8 | The sibling repo boundary remains hard: do not vendor, submodule, archive, or commit `sheikkinen/deviant-daily` into this yamlgraph repository. | GATE |

Authority granted: after the required revisions are folded, enforcement may modify the separate `sheikkinen/deviant-daily` product repo to add the reusable workflow, manual `publish-now` caller, strict input normalization, dry-run/no-DA behavior, explicit model targeting, slot-aware forced publish, tests, docs, and the required non-secret witnesses within the frozen scope above.
