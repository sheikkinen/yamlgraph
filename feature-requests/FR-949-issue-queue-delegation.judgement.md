<!-- Third-round judgement, rendered 2026-09-01. Judgement of record. R-1/R-2/R-4 folded
     into FR rev 4. R-3 (numeric output trim bounds) and the one-repo v1 narrowing are
     OVERRIDDEN by operator directives O-1/O-2 recorded in the FR (§ Operator Overrides);
     the judge's dissent below is preserved verbatim. Operator directive O-3: no further
     rejudge rounds — this document plus the overrides is the final planning input.
     Round-2 judgement in git history at ea35a983; round-1 (channel B) at 410db0b1. -->

**Prior art:** [FR-949-issue-queue-delegation.md](FR-949-issue-queue-delegation.md) — the governed FR (rev 4 folds R-1/R-2/R-4 and records overrides O-1..O-3). [FR-948-lan-copilot-delegation.judgement.md](FR-948-lan-copilot-delegation.judgement.md) — sibling channel-A judgement; distinguished: different transport and FR, shared arc only.

# Judgement: FR-949 GitHub-Issues delegation via self-hosted runner

**Verdict:** APPROVED WITH REVISIONS — channel C is a coherent contrib/example, but authority activates only after R-1 through R-4 separate the payload deadline from platform cancellation, split execution truth from publication outcome, freeze total output bounds, and replace the unattainable global-redaction claim with a mechanically enforceable credential boundary.

**Reviewed against:** `feature-requests/FR-949-issue-queue-delegation.md`; `feature-requests/spike-evidence-fr949-gha-runner.md`; `feature-requests/FR-949-issue-queue-delegation.judgement.md`; git object `410db0b1:feature-requests/FR-949-issue-queue-delegation.judgement.md`; `feature-requests/FR-948-lan-copilot-delegation.md`; `feature-requests/FR-948.research.md`; `feature-requests/FR-243-github-issues-remote-inbox.md`; `feature-requests/FR-251-harden-remote-inbox.md`; `feature-requests/FR-945-lan-recon-skill.md`; `feature-requests/FR-946-huutokauppakone-inference-revival.md`; `feature-requests/FR-947-remote-pytest-delegation.md`; `docs/diary/2026-09-01-incident-fr948-token-in-git-config.md`; `capabilities/CAP-101-a2a-call-node.yaml`; `capabilities/CAP-104-a2a-server-reference-docs.yaml`; `capabilities/CAP-105-a2a-consumer-phase2.yaml`; `capabilities/CAP-257-lan-copilot-delegation.yaml`; `scripts/judge.sh`; `scripts/research.sh`; `scripts/research_preflight.py`; `.github/workflows/workflow.yml`; `.github/workflows/weekly-recap.yml`; `.github/workflows/commitlint.yml`; `.github/workflows/security.yml`; `.github/copilot-instructions.md`; `ARCHITECTURE.md`; `docs/development-process.md`; `feature-requests/TEMPLATE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

**Scope and single responsibility:** the FR fixes one target repository, one named Windows service runner, serial execution, and a two-value payload enum; it explicitly excludes fleet management, concurrency, per-issue timeout, automatic recovery, code-repository writes, graph changes, and retirement of either channel (`feature-requests/FR-949-issue-queue-delegation.md:23`, `feature-requests/FR-949-issue-queue-delegation.md:68`, `feature-requests/FR-949-issue-queue-delegation.md:98-100`). The coexistence record measures the same operational decision but leaves channel retirement to a separate FR, so no orthogonal concern requires SPLIT (`feature-requests/FR-949-issue-queue-delegation.md:102-107`).

**Research and strategic classification:** the spike is substantive: it records a 26-second success, an exact three-minute platform timeout, an empty timeout capture, and a surviving grandchild that falsified the assumption that runner cancellation owns the process tree (`feature-requests/spike-evidence-fr949-gha-runner.md:14-30`). The FR preserves six genuine solution classes and dissent, dispositions its retrieved prior art, verifies that CAP-101/104/105 are retired, and explains why the transport is not a graph (`feature-requests/FR-949-issue-queue-delegation.md:131-143`; `capabilities/CAP-101-a2a-call-node.yaml:1-7`; `capabilities/CAP-104-a2a-server-reference-docs.yaml:1-7`; `capabilities/CAP-105-a2a-consumer-phase2.yaml:1-7`). **Contrib/example** is the correct classification: two concrete workloads reuse existing GitHub Issues, Actions, skill, and launcher abstractions; this is not a framework primitive with three independent use cases (`.github/skills/judge-fr/doctrine.md:51-57`).

**Architecture and boundary alignment:** the canonical-bundle/deployed-mirror rule removes the earlier two-source defect, request parsing is assigned to Pydantic entrypoints shared by workflow and unit tests, authorization precedes mutation, target checkout is SHA-pinned, and a Windows Job Object owns the payload tree (`feature-requests/FR-949-issue-queue-delegation.md:43-57`, `feature-requests/FR-949-issue-queue-delegation.md:60-84`). GitHub-Issue lifecycle and author allowlisting have implemented precedent (`feature-requests/FR-243-github-issues-remote-inbox.md:33-54`; `feature-requests/FR-251-harden-remote-inbox.md:29-49`). The existing launchers expose real artifact contracts rather than exit-code-only success: judge requires a non-empty verdict artifact and research requires a schema-verified alternatives artifact (`scripts/judge.sh:55-60`; `scripts/research.sh:66-84`).

**Measurability and testability:** most criteria name direct offline assertions and two real Windows witnesses. Identity fields, exact submit argv/body, closed request/status models, process absence, artifact hash reassembly, issue state, requirement markers, and diff scope can all be tested mechanically (`feature-requests/FR-949-issue-queue-delegation.md:110-129`). The strongest case against authority is narrower than the architecture: the same static Actions timeout is currently asked both to cancel the job and to leave that cancelled job alive long enough to prove tree absence and publish `TIMEOUT`; `COMMENT_POST_FAIL` is currently resolved before the publication attempt that creates it; and “bounded” output has per-comment but no total numeric bound (`feature-requests/FR-949-issue-queue-delegation.md:23`, `feature-requests/FR-949-issue-queue-delegation.md:68`, `feature-requests/FR-949-issue-queue-delegation.md:74`, `feature-requests/FR-949-issue-queue-delegation.md:90-96`, `feature-requests/FR-949-issue-queue-delegation.md:120-126`). These are consistency and feasibility defects, not reasons to reject the channel.

## Required revisions

### R-1: Separate the payload deadline from the platform kill switch

Freeze a two-tier timeout. `windows_job.ps1` must enforce a fixed 25-minute payload deadline; the workflow retains `timeout-minutes: 30` only as the outer platform kill switch, reserving five minutes for Job Object termination, process-absence proof, checkout/credential cleanup, artifact verification, and publication. `TIMEOUT` is emitted only when the inner deadline fires and all post-payload invariants complete. A 30-minute Actions cancellation is `PLATFORM_CANCELLED`: it may strand the issue at `claimed`, has no typed terminal issue result, and is recovered only by the documented operator relabel path already specified at `feature-requests/FR-949-issue-queue-delegation.md:76`.

Make AC-17 exercise the 25-minute boundary through a test-only launcher deadline override that is unavailable in issue input and production configuration. Prove both clocks in offline workflow/launcher tests and prove that the live timeout witness completes before the outer Actions deadline. Job Object termination truth must include zero active processes reported by the Job Object plus absence of the recorded root and descendant PIDs; recorded-PID absence alone does not prove the whole job is empty.

### R-2: Separate execution status from publication outcome

Remove `COMMENT_POST_FAIL` from `DelegationStatus` and its precedence chain. Add a closed `PublicationStatus` with `NOT_ATTEMPTED`, `OK`, `COMMENT_POST_FAIL`, and `TERMINAL_MUTATION_FAIL`. Resolve and persist the execution/cleanup `DelegationResult` before publication; publication then produces a separate Actions step-summary record because its outcome cannot be included truthfully in a comment whose attempted write determines that outcome.

Publish all result/artifact comments first. Only after every comment succeeds may one terminal GitHub API mutation atomically replace `claimed` with `done` and close an `OK` issue, or replace `claimed` with `failed` while leaving a non-OK issue open. A comment failure skips the terminal mutation. A terminal-mutation failure leaves the actual issue state observable and records `TERMINAL_MUTATION_FAIL` in Actions; no success-shaped fallback is allowed.

Add `CREDENTIAL_ISOLATION_FAIL` and `ARTIFACT_TOO_LARGE` to `DelegationStatus`, place each exactly once in the documented precedence, and map the corresponding AC-08 and R-3 refusals to them. Document authored worker/API phase failures exhaustively. An unexpected worker crash is not relabeled as a domain status: Actions remains the durable failure record and the issue remains recoverably `claimed`.

### R-3: Freeze numeric total-output and decoding bounds

Replace the placeholders “defined byte limit” and “bounded” with these v1 constants: `MAX_CAPTURE_BYTES = 4_000_000`, `MAX_FAILURE_TAIL_BYTES = 32_000`, `MAX_COMMENT_BYTES = 60_000`, `MAX_ARTIFACT_BYTES = 500_000`, and `MAX_ARTIFACT_PARTS = 10`. The incremental capture must be a bounded ring/tail implementation rather than an unbounded file followed by truncation. A larger verified artifact yields `ARTIFACT_TOO_LARGE` and is not published.

Artifacts must be valid UTF-8 Markdown or fail `ARTIFACT_INVALID`. Failure streams replace invalid byte sequences with U+FFFD, retain a final unterminated line, and apply the byte bound after UTF-8 encoding without splitting a code point. Comment headers count against `MAX_COMMENT_BYTES`; chunking must satisfy both the total-byte and part-count limits before the first comment is posted. Tests must cover every exact boundary, one-byte overflow, multibyte code points at each cut, invalid UTF-8, an unterminated final line, and byte-identical artifact reassembly.

### R-4: Make credential isolation and redaction claims attainable

Replace “one redaction function covers workflow logs” with two explicit boundaries. For worker-controlled payload data, one `worker.py` redactor must mediate captured stdout/stderr, failure tails, artifact bodies, issue comments, and generated step-summary content before those bytes reach a publication API or runner stdout. Workflow steps outside that mediator must never interpolate or echo issue bodies, payload output, artifacts, or secrets; GitHub configured-secret masking is the platform control for runner/action diagnostic logs and must not be represented as the Python redactor.

Keep the PAT solely as the checkout action input with `persist-credentials: false`; do not pass it or a token-derived value to the payload or post-checkout worker. The post-checkout credential-isolation step must instead prove the attainable structural invariants: no GitHub credential environment variable or askpass binding, no `http.*.extraheader`, no credential helper, sanitized `git config --show-origin`, and failing `gh auth status`. Any invariant failure yields `CREDENTIAL_ISOLATION_FAIL` before payload launch. Scan worker-controlled outputs for configured GitHub token prefixes and other frozen credential patterns; a match yields `TOKEN_LEAK_DETECTED`. Preserve transformed/encoded exfiltration as residual risk.

The comms workflow must declare explicit minimum permissions (`contents: read`, `issues: write`, all others absent) and constrain the job to the frozen Windows runner labels. The exact deployed workflow, permissions, action references, secret wiring, and bundle hash remain subject to the separate human review gate because they are external execution infrastructure (`.github/skills/judge-fr/doctrine.md:97-100`; `feature-requests/FR-949-issue-queue-delegation.md:53-56`, `feature-requests/FR-949-issue-queue-delegation.md:129`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/issue-delegate/SKILL.md` and `submit.sh` |
| D-2 | `.github/skills/issue-delegate/delegate.yml`, `models.py`, `worker.py`, `windows_job.ps1`, and `sync-worker.sh` |
| D-3 | `tests/unit/test_issue_delegate.py` and sanitized fixtures |
| D-4 | `capabilities/CAP-258-issue-delegation-runner.yaml`, `REQ-YG-637` markers, strict coverage, and generated `ARCHITECTURE.md` traceability |
| D-5 | `reference/development-operations.md` issue-delegation subsection |
| D-6 | `changelog/unreleased/fr-949-issue-delegation-runner.md` |
| D-7 | `feature-requests/FR-949-issue-queue-delegation.md`, including folded revisions, implementation status, deployment identity, and sanitized live witnesses |
| D-8 | `docs/diary/2026-09-XX-fr949-runner-delegation.md` with a `Seed:` |

Not authorized: changes to FR-948, CAP-257, `lan-delegate`, `lan-recon`, existing judge/research launchers, graphs, prompts, hooks, judge/review doctrine, Chaplain, unrelated workflows, or dependencies; production use of the macOS spike runner; another host or target repository; concurrency above one; caller-selected/per-issue timeout; progress streaming; automatic retry or recovery; fleet management; code-repository write access; graph-level budget enforcement; or retirement of either channel. Runner registration, service-account authentication, PAT creation/rotation, comms-repo secret configuration, and invocation of the reviewed deployment remain human-operated preconditions.

## Revised acceptance criteria

- [ ] AC-01: The FR retains the substantive spike, six genuine solution classes with dissent, every cited prior-art disposition, retired CAP-101/104/105 status, the “channel is not a graph” answer, and Contrib/example classification.
- [ ] AC-02: V1 fixes `sheikkinen/yamlgraph`, Huutokauppakone's labeled Windows service runner, one payload at a time, `judge|research`, a fixed 25-minute inner payload deadline, and a static 30-minute outer workflow timeout; neither value is issue-controlled.
- [ ] AC-03: The canonical D-2 bundle and deployed comms mirror are byte-identical; every submission refuses offline runner or drift before issue creation; identity records carry target SHA, workflow SHA, bundle hash, run ID, runner, and UTC.
- [ ] AC-04: Pydantic models validate the closed request, execution-result, delegation-status, and publication-status boundaries; exactly one YAML block and all malformed/unknown/duplicate/schema/task/SHA/credit cases fail before checkout or launch.
- [ ] AC-05: Task normalization rejects every path class frozen in the FR; judge accepts only a committed eligible FR path, and research accepts only a committed regular brief passing `scripts/research_preflight.py`.
- [ ] AC-06: `submit.sh` rejects dirty/unpushed trees, invalid payload/options, recursion, unavailable runner, and bundle drift with typed non-zero diagnostics; a mock asserts exact `gh issue create` argv, body, label, and SHA.
- [ ] AC-07: Authorization is read-only before claim; the workflow declares only `contents: read` and `issues: write`, runs only on the frozen Windows labels, and excluded authors cause no issue mutation, payload, or delegation status.
- [ ] AC-08: Checkout proves SHA ancestry and exact HEAD, uses the Contents-read PAT only as checkout input with `persist-credentials: false`, and maps any failed post-checkout structural credential invariant to `CREDENTIAL_ISOLATION_FAIL` before payload launch.
- [ ] AC-09: All worker-controlled payload bytes cross one redactor before runner stdout, step summary, comment, tail, or artifact publication; frozen token-pattern fixtures leak zero bytes; a detected literal pattern yields `TOKEN_LEAK_DETECTED`; platform log masking and transformed-exfiltration residual risk are documented honestly.
- [ ] AC-10: The Windows service-account preflight proves runner restart survival, both Git Bash launchers, Copilot authentication, Python/project dependencies, both timeout values, workflow permissions, and runner labels before live delegation.
- [ ] AC-11: `windows_job.ps1` assigns the suspended payload to a kill-on-close Job Object before resume; inner timeout success requires zero active Job Object processes plus absence of every recorded PID; otherwise `PROCESS_TREE_KILL_FAIL` outranks `TIMEOUT`.
- [ ] AC-12: Capture, tail, comment, artifact, and part limits equal R-3 exactly; decoding/truncation rules and all boundary cases pass; success publishes only a typed result plus verified fresh artifact, while failure publishes only a typed result plus bounded redacted tail.
- [ ] AC-13: `DelegationStatus` and `PublicationStatus` are separate and total; comments precede one terminal issue mutation; every status/outcome has direct offline witnesses and documented payload, field, observability, issue-state, and relabel invariants.
- [ ] AC-14: Runner loss and outer platform cancellation are witnessed as Actions-owned failures that may strand `claimed`; neither may emit `TIMEOUT`; operator relabel creates a distinct run ID without custom recovery machinery.
- [ ] AC-15: Offline tests use no network, real `gh`, runner, secret, or host mutation; invoke the same typed entrypoints as the workflow; cover every R-1 through R-4 seam; and carry `@pytest.mark.req("REQ-YG-637")`.
- [ ] AC-16: A real Windows judge witness under the service account produces a verified judgement with complete identity/timing/credit fields, `DelegationStatus.OK`, `PublicationStatus.OK`, atomic `done`+closed state, and no checkout/credential residue.
- [ ] AC-17: A real Windows inner-timeout witness completes before 30 minutes, records a named descendant, proves the Job Object empty and every PID absent, publishes bounded non-empty tail with `TIMEOUT`, reaches atomic `failed`+open state, and leaves no residue.
- [ ] AC-18: The coexistence record uses the frozen eligibility rule and records task class, queue/execution/end-to-end duration, credits, execution status, publication outcome, and babysitting interventions for 10 eligible runs or 30 UTC days without selecting a winner.
- [ ] AC-19: CAP-258/REQ-YG-637, strict coverage, generated architecture, operations/skill docs, changelog, implementation status, sanitized cross-repo/live evidence, and diary reflection are committed.
- [ ] AC-20: The current-repository diff changes only D-1 through D-8; the exact deployed comms-repository diff receives separate human review before live use.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 are folded into FR-949 and this advisory draft is human-reviewed before implementation authority activates. | GATE |
| C-2 | The canonical and deployed bundles are byte-identical; drift blocks submission; a human explicitly reviews the external workflow diff, permissions, action references, labels, secret wiring, and bundle identity. | GATE |
| C-3 | Offline RED witnesses for every revised AC-02 through AC-15 seam precede production branches, following the repository's TDD commit order. | GATE |
| C-4 | `TIMEOUT` is exclusively the inner Job Object deadline result; the 30-minute Actions timeout is an outer platform failure and can never be published as typed timeout success. | GATE |
| C-5 | No live payload runs until the checkout credential-isolation and Windows service-account preflights pass without credential material entering worker-controlled output. | GATE |
| C-6 | `OK`, `TIMEOUT`, `done`, `failed`, and publication success are independent truth claims requiring their complete process, artifact, cleanup, publication, and issue-state witnesses. | GATE |
| C-7 | Live AC-16 and AC-17 run only on Huutokauppakone's Windows service runner after C-2 through C-5 pass; committed evidence contains no secret, token-derived value, or private issue body. | GATE |
| C-8 | Runner registration, PAT scope/rotation, service-account authentication, comms secrets, and deployment invocation remain human-operated; enforcement may verify but not silently create or broaden them. | GATE |
| C-9 | Coexistence evidence cannot retire FR-948 or FR-949; a separate human-reviewed disposition FR owns that decision. | GATE |
| C-10 | No file or behavior outside D-1 through D-8 changes under FR-949 authority. | GATE |

Authority granted: after R-1 through R-4 are folded into FR-949 and a human accepts this advisory judgement, the enforcer may implement only D-1 through D-8 and satisfy AC-01 through AC-20 under C-1 through C-10.
