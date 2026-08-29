# Judgement: FR-903 Digest delivery — archive then email, in a declared order

**Prior art:** inherits the disposition in
`FR-903-digest-archive-then-email-ordering.md` — FR-908 is the parent
this FR was split from, FR-907 supplies the transport, FR-819 created the
target repo and its "no email" scope.

## Operator ruling on R-1 (2026-08-29)

R-1's **diagnosis is accepted**: the proposed `--dry-run` does not compose
with FR-907 and would either send anyway (with `SMTP_TO` set) or exit
through a missing-recipient exception.

R-1's **remedy is overruled**. The operator's ruling is that a dry-run
flag is hedging and is retired outright rather than given an explicit
route. `deviant-daily` removed `dry_run`/`force` as paternalistic
ceremony and tests that they stay gone; FR-908 quoted that rule and
carried the flag forward anyway.

Net effect on the frozen scope: **strictly smaller.** The dry-run
argument, the `dry_run` state key, the dry-run edge, and the two tests
R-1 requested are all deleted. The FR gains one negative acceptance
criterion asserting the flag cannot return. R-2, R-3, and R-4 are folded
as written.

**Verdict:** APPROVED WITH REVISIONS — the delivery child is the right scoped slice of FR-908 and its persist-before-publish graph shape is sound, but authority activates only after the dry-run contract is made compatible with FR-907 and the vendored SMTP provenance check is made mechanically possible.

**Reviewed against:** `feature-requests/FR-903-digest-archive-then-email-ordering.md`; `feature-requests/FR-908-daily-digest-slot-bound-refactor.md`; `feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md`; `feature-requests/FR-907-smtp-email-tool.md`; `feature-requests/FR-907-smtp-email-tool.judgement.md`; `feature-requests/FR-906-release-tool-slots-to-pypi.md`; `feature-requests/FR-906-release-tool-slots-to-pypi.judgement.md`; `feature-requests/FR-819-github-native-digest-poc-repo.md`; `feature-requests/TEMPLATE.md`; `pyproject.toml`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; repo doctrine in project instructions.

## What is sound

The FR is a faithful child of the FR-908 split. FR-908 required a Phase 1 delivery child for moving the bulletin write and README-index update into graph tools, routing `format_markdown -> gate -> write_bulletin -> send_email -> END`, preserving no-op behavior, passing SMTP secrets through workflow env, and updating README (`feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md:27-29`). FR-903 does exactly that: it moves the write and README-index update out of `run_digest.py`, appends email after archive, and routes no-new-articles to END (`feature-requests/FR-903-digest-archive-then-email-ordering.md:22-25`, `feature-requests/FR-903-digest-archive-then-email-ordering.md:100-104`, `feature-requests/FR-903-digest-archive-then-email-ordering.md:152-156`).

The user pain and operational event are concrete. FR-903 names the `yamlgraph-daily-digest` scheduled run as the first consumer and the first cron after merge as the event that writes `digests/<date>.md` and then emails it (`feature-requests/FR-903-digest-archive-then-email-ordering.md:8-10`). FR-819 established the existing repo as a GitHub-native publication channel with no email (`feature-requests/FR-819-github-native-digest-poc-repo.md:21-22`), and FR-908 recorded the live evidence of eleven green scheduled runs and committed bulletins (`feature-requests/FR-908-daily-digest-slot-bound-refactor.md:27-50`). Adding email alongside, not instead of, the committed bulletin preserves the FR-819 premise while addressing a real delivery gap.

The architecture alignment is strong. The ordering contract belongs in graph edges, and FR-903 states the desired edge sequence directly (`feature-requests/FR-903-digest-archive-then-email-ordering.md:39-46`, `feature-requests/FR-903-digest-archive-then-email-ordering.md:152-156`). It keeps SMTP transport out of this FR and depends on the already-enforced FR-907 generic email tool (`feature-requests/FR-903-digest-archive-then-email-ordering.md:13-18`, `feature-requests/FR-903-digest-archive-then-email-ordering.md:198-200`; `feature-requests/FR-907-smtp-email-tool.md:5`, `feature-requests/FR-907-smtp-email-tool.md:24-30`). It also correctly records the graph-authoring route because `graph.yaml` is materially changed (`feature-requests/FR-903-digest-archive-then-email-ordering.md:107-110`; `.github/copilot-instructions.md:15`).

The FR resolves FR-908's empty-bulletin ambiguity. FR-908 required the child to distinguish a legitimate no-new-articles route from malformed ranked output using an explicit predicate rather than empty markdown (`feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md:43-49`, `feature-requests/FR-908-daily-digest-slot-bound-refactor.judgement.md:69-73`). FR-903 introduces `digest_status` with `no_articles` and `ready`, routes only `no_articles` to END, and adds an acceptance test requiring empty markdown with `digest_status == ready` not to become a no-op (`feature-requests/FR-903-digest-archive-then-email-ordering.md:70-82`, `feature-requests/FR-903-digest-archive-then-email-ordering.md:163-168`).

The acceptance criteria are mostly mechanical and testable. They require transition-sequence assertions rather than terminal-state inference, simulated send-failure behavior, no-op behavior, routing by `digest_status`, absence of write/delivery logic from `run_digest.py`, workflow-secret assertions, workflow-shape tests, CI ordering, authoring-report evidence, and one real scheduled archive-and-email proof (`feature-requests/FR-903-digest-archive-then-email-ordering.md:152-180`). This follows the repo's `assert_path_not_destination` cure for pipeline tests (`.github/copilot-instructions.md:112`).

The vendoring decision is honestly framed. FR-907 explicitly says `examples/shared/smtp_email.*` is not shipped in the wheel and standalone repos consume it by vendoring (`feature-requests/FR-907-smtp-email-tool.md:46-50`, `feature-requests/FR-907-smtp-email-tool.md:57-58`). FR-906 records the same `examples*` exclusion and the portability failure caused by absolute `examples` imports (`feature-requests/FR-906-release-tool-slots-to-pypi.md:58-61`, `feature-requests/FR-906-release-tool-slots-to-pypi.md:162-180`; `pyproject.toml:179`). FR-903 therefore does not pretend that the shared SMTP manifest is available to a PyPI consumer.

Strategic classification: **contrib/example integration**. This is not a new framework primitive: the graph, tool-call nodes, FR-768 manifests, and FR-907 SMTP transport already exist. It is also not mere pattern documentation, because the first consumer is a live scheduled digest repo that needs one new integration sequence.

## Required revisions

### R-1: Replace "dry-run by missing recipient" with an explicit, tested no-send route

Revise the `run_digest.py` and `graph.yaml` plan so `--dry-run` cannot depend on omitting the recipient. FR-903 currently says `--dry-run` continues to work "by not binding a recipient" (`feature-requests/FR-903-digest-archive-then-email-ordering.md:102`), but FR-907's email tool uses `SMTP_TO` as the default recipient when `to` is absent (`feature-requests/FR-907-smtp-email-tool.md:147`) and must raise if neither `to` nor `SMTP_TO` yields a recipient (`feature-requests/FR-907-smtp-email-tool.md:218`). That means "not binding a recipient" is not a safe dry-run contract: with `SMTP_TO` in the environment it can still send, and without `SMTP_TO` it fails via a missing-recipient error rather than a deliberate dry-run path.

Fold a concrete rule into FR-903: `run_digest.py --dry-run` sets an explicit graph input/state key such as `dry_run: true`, and the graph routes `dry_run == true` to END after rendering or after archive according to the existing intended dry-run semantics. Add an acceptance test that runs with `SMTP_TO` present and proves `--dry-run` does not call `send_email`, plus a test with `SMTP_TO` absent proving dry-run exits through the deliberate dry-run route rather than through FR-907's missing-recipient exception. The existing no-new-articles `digest_status` route remains separate from dry-run.

### R-2: Make the vendored SMTP provenance check compatible with byte identity

Revise the vendoring acceptance criterion so it is mechanically satisfiable. FR-903 requires the vendored `tools/smtp_email.py` to be "byte-identical to the FR-907 upstream" while also requiring "provenance recorded in a header comment" inside that same file (`feature-requests/FR-903-digest-archive-then-email-ordering.md:170-172`). A header added to the copied file makes the file no longer byte-identical unless the upstream file already contains that exact digest-repo provenance comment. The prose has the same conflict: "verbatim copy" and "header comment" are both demanded for `tools/smtp_email.py` / `.tool.yaml` (`feature-requests/FR-903-digest-archive-then-email-ordering.md:98`).

Fold one exact scheme into the FR. Either: (a) keep `tools/smtp_email.py` and `tools/smtp_email.tool.yaml` byte-identical and record upstream path, upstream commit SHA, and FR-907 provenance in a separate committed sidecar such as `tools/smtp_email.VENDORED.md`; or (b) allow a bounded provenance header and define the identity check as "byte-identical after stripping the declared provenance header block." The acceptance test must implement the chosen rule and compare against a pinned upstream fixture or recorded upstream digest, not a live network fetch.

### R-3: State the target repository boundary for all file paths and evidence artifacts

Add one sentence before the `### Files` table stating that all unqualified paths in the table are paths in the external `yamlgraph-daily-digest` repository, not in this YAMLGraph repository. FR-819's repo-boundary rule says the PoC repo is a separate GitHub repository and must never be committed into yamlgraph as a nested repo, submodule, vendored directory, or generated artifact (`feature-requests/FR-819-github-native-digest-poc-repo.md:131-136`). FR-903's file table uses root paths such as `graph.yaml`, `run_digest.py`, `.github/workflows/digest.yml`, and `tools/smtp_email.py` without restating that boundary (`feature-requests/FR-903-digest-archive-then-email-ordering.md:96-105`). The child FR should make the target surface explicit so enforcement does not accidentally apply these paths in the wrong checkout.

### R-4: Tighten the scheduled-run evidence so "email delivered" is observable without exposing secrets

Revise the final acceptance criterion to name the evidence that proves the email step executed, not only that the run and commit exist. FR-903 asks for "one real scheduled run archives and emails a bulletin, evidenced here by run ID and commit SHA" (`feature-requests/FR-903-digest-archive-then-email-ordering.md:179-180`). A run ID and commit SHA prove archive/commit, but they do not by themselves prove the SMTP node sent. Add a non-secret evidence requirement such as the workflow log line from FR-907's successful send shape, a redacted SMTP result record, or an FR implementation note naming the sent subject and recipient domain without credentials. The evidence must not expose `SMTP_PASSWORD`, consistent with FR-907's secret-non-disclosure contract (`feature-requests/FR-907-smtp-email-tool.md:221-225`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | External `yamlgraph-daily-digest/graph.yaml`: `format_markdown -> gate -> write_bulletin -> send_email -> END`, with separate routes for `digest_status == no_articles` and `dry_run == true` |
| D-2 | External `yamlgraph-daily-digest/nodes/formatting.py`: emit `digest_status` with exactly `no_articles` and `ready` in this FR's scope |
| D-3 | External `yamlgraph-daily-digest/tools/write_bulletin.py` and `tools/write_bulletin.tool.yaml`: write `digests/<date>.md`, update the README index, and return the written path |
| D-4 | External `yamlgraph-daily-digest/tools/smtp_email.py` and `tools/smtp_email.tool.yaml`: vendored FR-907 SMTP tool copy with R-2 provenance/identity scheme |
| D-5 | External `yamlgraph-daily-digest/run_digest.py`: argument parsing, graph invocation, summary output, and explicit dry-run state/input only; no file-writing or delivery logic |
| D-6 | External `yamlgraph-daily-digest/.github/workflows/digest.yml`: pytest-before-digest execution, required SMTP secret env bindings, and existing cron/concurrency/content-write shape preserved |
| D-7 | External `yamlgraph-daily-digest/tests/test_workflow.py` and delivery-order/no-op/dry-run tests |
| D-8 | External `yamlgraph-daily-digest/README.md`: SMTP environment contract and behavior note |
| D-9 | FR-903 implementation notes: authoring report path, scheduled run ID, commit SHA, and non-secret SMTP-send evidence |

Not authorized: implementing or redesigning SMTP transport beyond vendoring the FR-907 artifact; changing FR-907 in this repository; slot-bound collection or `--tool` source switching (FR-904); rank-to-format validation or `digest_status == invalid` (FR-905); committed-SQLite/JSONL ledger changes; Markdown-to-HTML rendering; packaging `examples/shared/` into the yamlgraph wheel; changing YAMLGraph core, FR-768, or FR-892 semantics; committing the external digest repo into this repository; editing CI, hooks, judge/review doctrine, or other enforcement infrastructure.

## Revised acceptance criteria

- [ ] AC-01: FR-903 is revised to fold R-1 through R-4 before enforcement starts.
- [ ] AC-02: All unqualified implementation paths in the FR are explicitly scoped to the external `yamlgraph-daily-digest` repository, and no nested repo, submodule, vendored digest checkout, or generated digest artifact is committed into this YAMLGraph repository.
- [ ] AC-03: `graph.yaml` declares the transition sequence `format_markdown -> gate -> write_bulletin -> send_email -> END`, with the gate routing `digest_status == no_articles` to END before any write or send.
- [ ] AC-04: A test asserts the transition sequence and proves `write_bulletin` is visited before `send_email`, not merely that the graph reaches END.
- [ ] AC-05: A simulated send failure leaves `digests/<date>.md` written on the runner filesystem and makes `run_digest.py` exit non-zero before the workflow commit/push step.
- [ ] AC-06: `digest_status == no_articles` produces no write, no send, and no commit.
- [ ] AC-07: Routing is driven by `digest_status`, never by empty markdown; a test renders an empty bulletin with `digest_status == ready` and proves it is not treated as a no-op.
- [ ] AC-08: `run_digest.py --dry-run` uses an explicit dry-run graph input/state route, not missing-recipient behavior; with `SMTP_TO` present it does not call `send_email`, and with `SMTP_TO` absent it does not fail through FR-907's missing-recipient exception.
- [ ] AC-09: `run_digest.py` contains no file-writing and no delivery logic after the graph owns both side effects.
- [ ] AC-10: The vendored SMTP files follow the R-2 provenance/identity scheme, recording the upstream path, FR-907 provenance, upstream commit SHA, and either exact byte identity or exact identity after stripping the declared provenance block.
- [ ] AC-11: The workflow passes `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_TO` into the digest run step; README documents those variables and the optional `SMTP_FROM` behavior inherited from FR-907.
- [ ] AC-12: `tests/test_workflow.py` asserts the cron value, digest concurrency group with `cancel-in-progress: false`, `contents: write`, pytest-before-digest ordering, and every required SMTP secret binding.
- [ ] AC-13: An authoring report exists for the `graph.yaml` change and records graph lint/smoke validation as an artifact, not merely an exit code.
- [ ] AC-14: One real scheduled run archives and emails a bulletin, evidenced in FR-903 by run ID, commit SHA, and non-secret proof that the SMTP send node executed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-4 are folded into `feature-requests/FR-903-digest-archive-then-email-ordering.md`. | GATE |
| C-2 | Implement only in the external `yamlgraph-daily-digest` repository surfaces named above; do not commit that repository or its generated artifacts into this YAMLGraph repository. | GATE |
| C-3 | Use the governed graph-authoring route for the `graph.yaml` edit and retain the authoring report with lint/smoke evidence. | GATE |
| C-4 | The delivery graph may consume only the independently enforced FR-907 SMTP tool copy; it must not redesign SMTP transport or weaken FR-907's raise-on-failure, header-injection, or secret-non-disclosure guarantees. | GATE |
| C-5 | Dry-run, no-new-articles, send failure, and successful send must be four distinct tested paths; none may be implemented as a success-shaped failure or by relying on missing SMTP config. | GATE |
| C-6 | The no-new-articles route is limited to `digest_status == no_articles`; malformed ranked output and `digest_status == invalid` remain FR-905 scope and must not be laundered into a green no-op here. | GATE |
| C-7 | Do not expand into FR-904 slot-bound collection, FR-905 boundary validation, committed-state redesign, HTML email rendering, `examples/shared` packaging, or YAMLGraph framework changes. | GATE |
| C-8 | Human review is required before merge because the change sends real email from a scheduled workflow using repository secrets. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, the enforcer may implement only the external digest-repo archive-before-email graph ordering, explicit no-op and dry-run routing, vendored FR-907 SMTP copy, workflow env/test assertions, README updates, and recorded scheduled-run evidence described above.
