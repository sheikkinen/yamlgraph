<!-- Rendered 2026-09-01 against the channel-B (custom poller) revision of FR-949.
     Historical: the FR was refit to channel C (self-hosted runner) after spike
     evidence; R-1..R-8 dispositioned in the FR's Prior art. New judgement pending. -->

**Prior art:** [FR-949-issue-queue-delegation.md](FR-949-issue-queue-delegation.md) — the governed FR (channel-C refit); this judgement was rendered against its earlier channel-B revision and is retained as the historical record its R-numbers refer to. [FR-948-lan-copilot-delegation.judgement.md](FR-948-lan-copilot-delegation.judgement.md) — sibling channel-A judgement; distinguished: different transport and FR, shared arc only.

# Judgement: FR-949 GitHub-Issues delegation queue

**Verdict:** APPROVED WITH REVISIONS — the one-host GitHub-Issues channel is a coherent contrib/example, but authority activates only after R-1 through R-8 repair the research record, contract the v1 input surface, make claimed-work recovery durable, isolate credentials from delegated agents, and freeze testable artifact, lifecycle, experiment, and deliverable contracts.

**Reviewed against:** `feature-requests/FR-949-issue-queue-delegation.md`; `feature-requests/FR-948.research.md`; `feature-requests/FR-948-lan-copilot-delegation.md`; `feature-requests/FR-948-lan-copilot-delegation.judgement.md`; `feature-requests/FR-243-github-issues-remote-inbox.md`; `feature-requests/FR-251-harden-remote-inbox.md`; `feature-requests/FR-945-lan-recon-skill.md`; `feature-requests/FR-947-remote-pytest-delegation.md`; `feature-requests/FR-946-huutokauppakone-inference-revival.md`; `docs/diary/2026-09-01-incident-fr948-token-in-git-config.md`; `capabilities/CAP-101-a2a-call-node.yaml`; `capabilities/CAP-104-a2a-server-reference-docs.yaml`; `capabilities/CAP-105-a2a-consumer-phase2.yaml`; `.chaplain/lib/watcher/inbox_sync.sh`; `.github/skills/lan-delegate/SKILL.md`; `scripts/judge.sh`; `scripts/research.sh`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

**Scope and single responsibility:** the first consumer and event are concrete, and the proposal owns one operational concern: submit one SHA-pinned judge/research workload to one named host through a durable issue surface (`feature-requests/FR-949-issue-queue-delegation.md:8`, `feature-requests/FR-949-issue-queue-delegation.md:18-24`). The control helper, poller, heartbeat, and issue-result protocol are the two ends and observability of that same channel, not orthogonal features. Fleet scheduling, parallel execution, progress streaming, code-repository writes, and retirement of FR-948 are explicitly excluded (`feature-requests/FR-949-issue-queue-delegation.md:85-91`). A smaller v1 can and should fix the target to `sheikki/yamlgraph`, but the proposal does not require a SPLIT.

**Architecture alignment and feasibility:** GitHub-Issue polling, label lifecycle, author allowlisting, body limits, and retry-by-relabel already have implemented repo precedent (`feature-requests/FR-243-github-issues-remote-inbox.md:33-54`; `feature-requests/FR-251-harden-remote-inbox.md:29-49`; `.chaplain/lib/watcher/inbox_sync.sh:22-47`). FR-948 supplies the detached-worktree, checked process-tree deadline, post-run credit interpretation, recursion, and cleanup precedents (`feature-requests/FR-948-lan-copilot-delegation.md:65-69`, `feature-requests/FR-948-lan-copilot-delegation.md:101-165`; `.github/skills/lan-delegate/SKILL.md:18-43`). Existing launchers accept exactly one committed path and verify fixed draft artifacts at `tmp/draft-judgement.md` and `tmp/draft-alternatives.md`, so the two proposed payloads are workable once the poller adopts those actual contracts (`scripts/judge.sh:10-20`, `scripts/judge.sh:55-62`; `scripts/research.sh:11-21`, `scripts/research.sh:63-84`).

**Strategic classification:** this is **Contrib/example**, not a framework primitive. It has one host, one control device, and two closely related operational payloads; existing issue, skill, worktree, launcher, and GitHub CLI patterns provide most primitives. It therefore matches the rubric's 1-2-use-case classification rather than the 3+-use-case primitive threshold (`.github/skills/judge-fr/doctrine.md:52-56`). No YAMLGraph graph or prompt change is justified.

**Value and test shape:** the pull-only LAN topology removes FR-948's control-to-worker credential handoff and replaces synchronous waiting with a persistent tracking surface. The proposed offline seams plus real judge and timeout witnesses correctly distinguish deterministic unit coverage from the physical behavior that must be observed on Windows (`feature-requests/FR-949-issue-queue-delegation.md:97-112`). The security direction also preserves the incident's correct lesson that redaction must be structurally attached to the output boundary and credentials must not be embedded into persistent Git configuration (`docs/diary/2026-09-01-incident-fr948-token-in-git-config.md:22-26`, `docs/diary/2026-09-01-incident-fr948-token-in-git-config.md:40-45`, `docs/diary/2026-09-01-incident-fr948-token-in-git-config.md:61-63`).

The strongest case against authority is not that the queue lacks a consumer or feasible components. It is that the current text calls the queue durable across reboots but defines no recovery after `claimed`, gives a delegated agent access to the same ambient account that holds comment/fetch credentials, and makes target repositories configurable while configuring only one canonical clone (`feature-requests/FR-949-issue-queue-delegation.md:20`, `feature-requests/FR-949-issue-queue-delegation.md:29-30`, `feature-requests/FR-949-issue-queue-delegation.md:72-83`). Those are boundary and composition defects; the revisions below contract rather than expand the feature.

## Required revisions

### R-1: Correct the research, prior-art, and classification record

Replace the claim that `FR-948.research.md` researched channel B. That record evaluates WinRM/Copilot variants and contains no GitHub-Issues queue candidate (`feature-requests/FR-948.research.md:17-23`). Retain it only as shared pain/channel-A precedent. Declare the FR's committed five-row alternatives table as the channel-B research record, add a substantive `is_this_a_graph` disposition, and record **Contrib/example** classification. The answer is: this is not a YAMLGraph graph; it is an external operational channel whose payloads invoke existing graph-backed launchers.

Correct A2A prior art from “exists as framework capability” to retired historical precedent. CAP-101, CAP-104, and CAP-105 all say the server/client surfaces were deleted after four months without a consumer (`capabilities/CAP-101-a2a-call-node.yaml:1-6`; `capabilities/CAP-104-a2a-server-reference-docs.yaml:1-6`; `capabilities/CAP-105-a2a-consumer-phase2.yaml:1-6`). Preserve A2A as a historical solution class, disposition the retirement rationale, and do not imply that channel B could reuse a live implementation.

### R-2: Contract v1 to one typed repository and payload boundary

Remove `--repo` from `submit.sh` and remove issue-author control of `repo:` in v1. Configure exactly one target tuple on the worker: `repo = "sheikki/yamlgraph"`, its canonical clone path, and its remote default branch. The current combination of a configurable target repo and a singular canonical clone path is incomplete (`feature-requests/FR-949-issue-queue-delegation.md:20`, `feature-requests/FR-949-issue-queue-delegation.md:51`, `feature-requests/FR-949-issue-queue-delegation.md:62`, `feature-requests/FR-949-issue-queue-delegation.md:72`). Multi-repository mappings require a separate FR after this one-host channel survives.

Define Pydantic `DelegationIssueRequest`, `PollerConfig`, `RunRecord`, and `DelegationResult` models at the issue/config/process boundaries. Freeze the issue schema to `schema_version`, `task`, `sha`, `payload`, `timeout_s`, and `max_reported_credits`; reject unknown or duplicate keys and multiple/missing fenced YAML blocks. Freeze task-specific payload rules: `judge` accepts only a normalized repo-relative `feature-requests/FR-*.md` path other than `*.judgement.md`; `research` accepts only the committed brief path shape required by `scripts/research.sh`; absolute paths, `..`, separators other than `/`, control characters, leading `-`, symlinks escaping the worktree, missing files, and wrong file types fail before launch. Define concrete timeout bounds and require the issue value to be no greater than the worker-configured hard maximum. Define `max_reported_credits` as post-run diagnostics, bounded by the worker-configured maximum; it is not a preventive spend claim, matching FR-948 (`feature-requests/FR-948-lan-copilot-delegation.md:68-69`, `feature-requests/FR-948-lan-copilot-delegation.md:315-317`).

### R-3: Make the issue lifecycle recoverable and idempotent

Replace the informal label swap with a closed state machine and one-shot recovery contract:

`delegate -> claimed -> done|failed`; only `failed -> delegate` by an allowlisted operator starts a new numbered attempt. Each claim comment and atomic local run record must include issue number, attempt, host, poller code SHA, target SHA, claim UTC, and a unique run ID. Before claiming new work, a cycle must reconcile every open `claimed` issue owned by this one-host poller. An interrupted attempt is never silently rerun: terminate any still-matching recorded process tree, remove its worktree, post typed `INTERRUPTED` diagnostics, and transition it to `failed`. Scheduled Task registration must enforce one running poller instance.

Define behavior for failure between every GitHub mutation: repeated cycles must detect already-posted run/part identifiers, must not execute a completed attempt twice, and must retry only missing comments or terminal label/close operations. API unavailability leaves the issue in its last truthful state and the local atomic run record intact for reconciliation. This repairs the contradiction between “durable across partitions, reboots” and a flow that currently stops after `claimed` if the poller dies (`feature-requests/FR-949-issue-queue-delegation.md:30`, `feature-requests/FR-949-issue-queue-delegation.md:75-83`). Resolve open question 2 as proposed: v1 is one-shot; operator relabeling creates a new attempt.

### R-4: Isolate poller credentials from delegated agents

Replace “no token in transit” with the narrower truthful claim: no credential is handed from the control device to the worker or across the LAN; the worker still authenticates to GitHub over HTTPS. Define two least-privilege worker credentials: comms-repo Issues read/write and target-repo Contents read. They must be supplied to individual `gh`/`git fetch` subprocesses through scoped environment/askpass bindings, never embedded in a URL, clone origin, TOML file, command line, diagnostic, or persistent `gh` configuration.

The judge/research child environment must remove `GH_TOKEN`, `GITHUB_TOKEN`, askpass variables, and credential/config paths. The execution account must have no ambient `gh` or Git credential that works without those per-call bindings; document and live-verify that precondition. Thus an agent cannot invoke `gh` directly and bypass the poller's redaction/posting boundary. Every captured diagnostic is bounded and redacted before persistence or API submission. If a final artifact contains a literal configured token or credential-pattern match, fail typed `TOKEN_LEAK_DETECTED` and do not post a silently modified judgement/research artifact. Record transformed/encoded exfiltration as residual risk rather than claiming impossibility. These requirements apply the cited incident's credential-helper and print-boundary lessons (`docs/diary/2026-09-01-incident-fr948-token-in-git-config.md:40-45`, `docs/diary/2026-09-01-incident-fr948-token-in-git-config.md:61-63`).

### R-5: Freeze launcher, artifact, comment, and result contracts

Replace “all agent output” with the actual v1 contract: on success, post a typed run summary and the verified final artifact only; on failure, post the typed summary plus a bounded, redacted stdout/stderr tail. For `judge`, require non-empty `tmp/draft-judgement.md` containing a verdict line; for `research`, require the verified `tmp/draft-alternatives.md`. These are the launchers' committed output contracts (`scripts/judge.sh:10`, `scripts/judge.sh:59-62`; `scripts/research.sh:11`, `scripts/research.sh:67-84`). Missing, stale, malformed, or task-mismatched artifacts fail even when the child exits zero.

Chunk UTF-8 on byte boundaries, not character counts. Set a maximum body size that includes the `run <id> artifact sha256 <hash> part i/N` header, never splits a code point, and is below the configured GitHub comment-body ceiling. Hash the safe original artifact before chunking; byte-for-byte ordered reassembly must equal that hash. On retry, discover parts by run ID, artifact hash, and part number so already-posted parts are not duplicated. Keep stdout/stderr capture bounded and define the exact last-100-lines behavior for unterminated lines and invalid UTF-8.

### R-6: Make process termination, cleanup, and outcomes total

Use a directly owned process handle/PID and checked full-tree termination. `TIMEOUT` is valid only after `taskkill /PID <pid> /T /F` succeeds and a follow-up proves the tracked process tree absent; otherwise `PROCESS_TREE_KILL_FAIL` outranks timeout. Put process termination, worktree removal, scoped credential/askpass cleanup, and local run-record finalization in unconditional cleanup, retaining every cleanup error. Cleanup failure must not be overwritten by a prior successful payload result.

Add a closed `DelegationStatus` with deterministic precedence and a witness for every member: at minimum `OK`, `INVALID_REQUEST`, `UNTRUSTED_AUTHOR`, `FETCH_FAIL`, `SHA_UNREACHABLE`, `WORKTREE_ADD_FAIL`, `LAUNCH_FAIL`, `PAYLOAD_NONZERO`, `TIMEOUT`, `PROCESS_TREE_KILL_FAIL`, `ARTIFACT_MISSING`, `ARTIFACT_INVALID`, `TOKEN_LEAK_DETECTED`, `CREDIT_FAIL_HIGH`, `CREDIT_FAIL_UNPARSEABLE`, `COMMENT_POST_FAIL`, `WORKTREE_CLEANUP_FAIL`, and `INTERRUPTED`. Define for each status whether the payload ran, which result fields may be absent, which label/close state is required, and whether operator relabeling may retry it. Unit evidence that merely asserts the kill function was called is insufficient for the no-orphan claim; retain the real descendant-process timeout witness (`feature-requests/FR-949-issue-queue-delegation.md:103`, `feature-requests/FR-949-issue-queue-delegation.md:110`).

### R-7: Make heartbeat and coexistence measurements mechanical

Resolve open question 1 as proposed: `delegation_poller.py --once` is the only execution primitive; the Scheduled Task supplies the two-minute cadence and single-instance policy. Freeze heartbeat schema/version, UTC format, poller code SHA, host, cycle result, and interval. `submit.sh --check-poller` must fail non-zero and actionable for missing issue, malformed/stale heartbeat, wrong host/version, GitHub failure, or age greater than three configured intervals; it must not submit work in check mode.

Define the experiment window as closing when both channels have 10 eligible real runs or 30 UTC days have elapsed from the first eligible channel-B run, whichever happens first. Exclude deliberate timeout witnesses from success-rate comparison but retain them as incidents/tests. Replace the undefined “overhead vs. local run” metric with comparable per-task-class queue delay, execution duration, and end-to-end duration for channels A and B; define success denominator, babysitting intervention, and incident. Channel-B terminal comments must carry those machine-readable fields. FR-949 may collect evidence but may not declare a winner or retire either channel; that decision requires a separate disposition/subtraction FR.

### R-8: Fold an exact deliverable table, traceability ID, and revised criteria into the FR

Fold D-1 through D-8 below into FR-949, allocate and record the exact CAP/REQ identifiers before enforcement, replace the current criteria with the revised list below, and update the effort estimate after R-1 through R-7. Tests must carry the allocated requirement marker. The current `@pytest.mark.req` promise has no named requirement and the FR has no capability, changelog, implementation-status, or diary deliverable (`feature-requests/FR-949-issue-queue-delegation.md:111-112`; `.github/copilot-instructions.md:13-16`, `.github/copilot-instructions.md:210-212`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/issue-delegate/SKILL.md` and `submit.sh` implementing submit, recursion refusal, and heartbeat-check modes |
| D-2 | `scripts/delegation_poller.py` plus narrowly factored typed support modules under `scripts/` only if needed to keep modules within repo size limits |
| D-3 | `tests/unit/test_issue_delegate.py`, `tests/unit/test_delegation_poller.py`, and sanitized fixtures for issue, process, artifact, credential, lifecycle, and retry seams |
| D-4 | One newly allocated `capabilities/CAP-*-issue-queue-delegation.yaml`, its named `REQ-YG-*` markers, and generated `ARCHITECTURE.md` traceability |
| D-5 | `reference/development-operations.md` delegation-queue subsection and a credential-free poller TOML example |
| D-6 | One FR-949 changelog fragment under `changelog/unreleased/` |
| D-7 | `feature-requests/FR-949-issue-queue-delegation.md`, including folded revisions, implementation status, and sanitized live-witness/experiment evidence |
| D-8 | `docs/diary/2026-09-XX-fr949-issue-queue-delegation.md` reflection with a `Seed:` |

Not authorized: changes to graphs or prompts; changes to `scripts/judge.sh`, `scripts/research.sh`, FR-948, FR-945, Chaplain, A2A, Copilot-node behavior, CI, hooks, judge/review doctrine, or unrelated dependencies; more than one worker, target repository, or concurrent payload; auto-retry, resume, progress streaming, inbound listeners, SMB/WinRM transport, code-repository writes from the worker, automatic comms-repo/Scheduled-Task/account creation, or retirement of either coexistence channel. No file outside D-1 through D-8 may change under FR-949 authority.

## Revised acceptance criteria

- [ ] **AC-01** The FR records five genuine solution classes, preserved dissent, all cited prior-art dispositions, the corrected retired status of CAP-101/104/105, the substantive “not a graph” answer, and **Contrib/example** classification.
- [ ] **AC-02** V1 fixes the worker to `sheikki/yamlgraph` and one configured canonical clone/default branch; issue bodies and `submit.sh` cannot select another repository.
- [ ] **AC-03** Pydantic models validate the closed issue, config, atomic run-record, and result schemas; unknown/duplicate keys and malformed/multiple YAML blocks fail before fetch or launch.
- [ ] **AC-04** Task-specific payload validation rejects absolute/traversing/option-like/control-character/wrong-directory/wrong-type/missing/escaping-symlink paths before child launch.
- [ ] **AC-05** `submit.sh` refuses dirty tree, HEAD not reachable from the configured remote default branch, missing/invalid payload, recursive delegation, malformed options, and stale/missing poller in check mode with actionable stderr and non-zero status.
- [ ] **AC-06** A mocked submit test asserts exact `gh` argv/body/label, schema version, task, normalized payload, full HEAD SHA, bounded timeout, and bounded post-run credit threshold.
- [ ] **AC-07** The poller considers allowlisted authors only, orders eligible `delegate` issues oldest first, claims at most one, and leaves untrusted issues unmodified.
- [ ] **AC-08** Label transitions obey `delegate -> claimed -> done|failed`; operator relabeling creates a new numbered attempt, and no automatic payload retry exists.
- [ ] **AC-09** Atomic run records and reconciliation make every crash/API-failure seam idempotent: no completed attempt executes twice, posted parts are not duplicated, and interrupted claimed work becomes typed `INTERRUPTED` before new work is claimed.
- [ ] **AC-10** SHA reachability is verified against the fetched configured default branch; the detached worktree HEAD must equal the issue SHA before payload launch.
- [ ] **AC-11** The judge/research child receives `YAMLGRAPH_DELEGATED=1` but no GitHub token, askpass binding, or usable ambient `gh`/Git credential; a live precondition probe confirms child-side `gh auth status` fails without scoped injection.
- [ ] **AC-12** Scoped GitHub credentials never appear in URL/origin, TOML, argv, logs, run records, artifacts, comments, or child environment; literal leak detection fails closed without posting a modified verdict/research artifact.
- [ ] **AC-13** `judge` success requires the launcher's verified `tmp/draft-judgement.md`; `research` success requires verified `tmp/draft-alternatives.md`; stale, absent, empty, malformed, or mismatched artifacts fail typed even on exit zero.
- [ ] **AC-14** Artifact comments use UTF-8 byte-safe chunks with run ID, artifact SHA-256, and `part i/N`; retry is idempotent and ordered reassembly is byte-identical to the safe original artifact.
- [ ] **AC-15** Success posts only a typed run summary plus final artifact; failure posts a typed summary plus a bounded redacted tail whose invalid-UTF-8 and line-boundary behavior is tested.
- [ ] **AC-16** Every `DelegationStatus` has a direct mocked witness, appears exactly once in deterministic precedence, and enforces its documented payload/result/label/close invariants.
- [ ] **AC-17** Timeout uses the directly owned PID and checked full-tree kill; `TIMEOUT` requires absence proof, kill failure is `PROCESS_TREE_KILL_FAIL`, and cleanup errors remain visible.
- [ ] **AC-18** Worktree, process, askpass/environment, and run-record cleanup execute on success, payload failure, timeout, artifact failure, comment failure, interruption, and poller exception.
- [ ] **AC-19** `delegation_poller.py --once` updates a versioned heartbeat every cycle; `submit.sh --check-poller` detects every missing, malformed, wrong-host/version, GitHub-error, and older-than-three-interval state.
- [ ] **AC-20** Offline tests perform no network, real `gh`, git remote, agent, or Windows mutation and carry the allocated `@pytest.mark.req("REQ-YG-*")` marker.
- [ ] **AC-21** Live judge witness: one committed Proposed FR at the pinned SHA produces a verified complete judgement on the issue, typed timings/credits, `done`, close, no duplicate parts, clean worktree, and control-side promotion to committed `.judgement.md`.
- [ ] **AC-22** Live timeout witness creates a named descendant, records root/descendant identities, proves all absent after the checked kill, produces `failed` + `TIMEOUT` + bounded tail, leaves no worktree/credential bytes, and does not count as an experiment success run.
- [ ] **AC-23** Experiment records define eligible runs, success denominator, interventions, incidents, queue/execution/end-to-end timings, close threshold, and task class; FR-949 neither selects nor retires a channel.
- [ ] **AC-24** Exact CAP/REQ IDs, strict requirement coverage, generated architecture, skill docs, operations docs/config example, changelog fragment, implementation status, sanitized witnesses, and diary reflection are committed with no change outside D-1 through D-8.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-8 are folded into FR-949 and this advisory draft is human-reviewed before implementation begins. | GATE |
| C-2 | Worker target remains one host, one repository, one payload at a time, and the closed `judge|research` enum; expansion re-enters Plan. | GATE |
| C-3 | No delegated child may inherit or discover a usable GitHub credential; credential isolation precedes live agent execution. | GATE |
| C-4 | Offline RED witnesses for validation, lifecycle reconciliation, credential isolation, artifact integrity, status precedence, timeout, and cleanup precede production branches. | GATE |
| C-5 | `TIMEOUT`, `done`, and `failed` are truth claims: each requires its folded process, artifact, comment, cleanup, and issue-state invariants rather than exit code alone. | GATE |
| C-6 | Manual creation of the private comms repo, fine-grained credentials, execution-account state, labels, heartbeat issue, and single-instance Scheduled Task requires operator review and is not automated under this FR. | GATE |
| C-7 | Live AC-21/AC-22 runs occur only after offline gates pass; committed evidence and issue comments contain no credential or private token-derived value. | GATE |
| C-8 | Coexistence evidence cannot retire FR-948 or FR-949 under this authority; a human-reviewed disposition/subtraction FR owns that decision. | GATE |
| C-9 | No file or behavior outside D-1 through D-8 changes under FR-949 authority. | GATE |

Authority granted: after R-1 through R-8 are folded, exact CAP/REQ IDs replace the placeholders, and a human accepts this advisory judgement, the enforcer may implement only D-1 through D-8 and satisfy AC-01 through AC-24 under C-1 through C-9.
