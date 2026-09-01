# Judgement: FR-948 LAN Copilot-CLI delegation channel (supersedes FR-947)

**Verdict:** APPROVED WITH REVISIONS — the WinRM/Copilot direction is a coherent contrib/example, but authority activates only after R-1..R-5 close the typed-contract, timeout, lifecycle, credential, and recursive-delegation gaps and this draft is human-reviewed.

**Prior art:**
- [FR-948-lan-copilot-delegation.md](FR-948-lan-copilot-delegation.md), [FR-948.research.md](FR-948.research.md), [FR-948-spike-evidence.md](FR-948-spike-evidence.md) — the artifacts under judgement; self-references, not distinguished separately.
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) [Proposed] and [FR-945-lan-recon-skill.judgement.md](FR-945-lan-recon-skill.judgement.md) — read-only recon precondition; delegation vs. inspection scope distinguished.
- [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) [Superseded-by FR-948] — SSH design retired via subtractionist path.
- [CAP-30 Copilot Node](../capabilities/CAP-30-copilot-node.yaml) — precedent for local Copilot invocation; explicitly out of scope per C-8 (NOT modified).

**Reviewed against:** `feature-requests/FR-948-lan-copilot-delegation.md`; `feature-requests/FR-948-spike-evidence.md`; `feature-requests/FR-948.research.md`; `feature-requests/research-briefs/copilot-cli-remote-delegation-brief.md`; `feature-requests/FR-947-remote-pytest-delegation.md`; `feature-requests/FR-945-lan-recon-skill.md`; `feature-requests/FR-945.research.md`; `feature-requests/FR-946-huutokauppakone-inference-revival.md`; `feature-requests/FR-766-runpod-provider.md`; `feature-requests/FR-899-org-repo-census-azure.md`; `feature-requests/FR-899-org-repo-census-azure.judgement.md`; `capabilities/CAP-30-copilot-node.yaml`; `capabilities/CAP-249-tool-slot-binding.yaml`; `pyproject.toml`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem and first consumer are concrete: a clean-committed agent workload is moved from the saturated iMac to one already-provisioned LAN host, with a named first event and diagnostic result (`feature-requests/FR-948-lan-copilot-delegation.md:8,26,30-33`). The committed spike is substantive rather than ceremonial: it records the bound-parameter command shape, exit code, elapsed time, reported credits/tokens, and exact returned artifact (`feature-requests/FR-948-spike-evidence.md:19-38,40-77`). It also honestly fences what was not proved, including a representative repository workload and `--add-dir` skill loading (`feature-requests/FR-948-spike-evidence.md:79-99`).

The revised plan is substantially narrower than FR-947. It reuses FR-945's pinned WinRM transport and the existing `pypsrp>=0.9,<1.0` dependency, makes remote tools preconditions rather than installation work, and excludes resume, source transfer, fetch, clone, and runtime bootstrap (`feature-requests/FR-948-lan-copilot-delegation.md:53-55,77-78,82-90`; `pyproject.toml:39-55`). The five-class alternatives table preserves the deterministic-executor, SSH/WSL2, self-hosted-runner, and CI-only disagreements instead of presenting five phrasings of one answer (`feature-requests/FR-948-lan-copilot-delegation.md:41-51`). Retrieved prior art is dispositioned (`feature-requests/FR-948-lan-copilot-delegation.md:10-18`), and the FR reconciles the research artifact's contradictory graph classifications by treating the channel as an external method consumed by graphs (`feature-requests/FR-948.research.md:17-23`; `feature-requests/FR-948-lan-copilot-delegation.md:240`).

The dated safety and spend decisions are explicit rather than silently absorbed by the plan. The operator accepted `--allow-all-tools`, the live-token exposure envelope, lack of formal rotation in v1, post-run-only credit diagnosis, and the absence of a hard credit cap (`feature-requests/FR-948-lan-copilot-delegation.md:222-236`). Those are human product/risk decisions; preserving them as committed constraints is sound.

Strategic classification is **contrib/example**: this is one host and one immediate workload channel, reusing the existing skill convention, Copilot CLI precedent, and FR-945 transport while filling a concrete cross-machine execution gap (`feature-requests/FR-948-lan-copilot-delegation.md:8,17,22`; `capabilities/CAP-30-copilot-node.yaml:1-25`). It is not a framework primitive: three independent use cases are not established. It is more than pattern documentation because the repository lacks the typed WinRM execution, lifecycle, and artifact-return implementation. The retirement bookkeeping is coupled to replacing the same unimplemented channel, so the proposal remains one responsibility and does not require a split.

## Required revisions

### R-1: Complete and reconcile the typed contract

Fold explicit field tables into the FR for `ToolInfo` and `RepoInfo`; replace `FieldError.error_type: Literal[...]` with a closed, named value set; and enumerate the typed pre-launch exception classes. The current FR calls the schemas complete while leaving those types undefined (`feature-requests/FR-948-lan-copilot-delegation.md:94-101,165,243`).

Make source identity one coherent contract. Delete the unused upstream-URL and `.git/HEAD` SHA-256 requirement at line 69. Retain the Git commit identity boundary, add required `remote_sha` to `LanDelegationResult`, obtain it from `git -C <run-worktree> rev-parse HEAD` after worktree creation, and require `remote_sha == local_sha`. This repairs the mismatch between the promised "two SHAs" and the result table's single SHA (`feature-requests/FR-948-lan-copilot-delegation.md:37,68-70,142-163,209`).

Permit `prerequisites=None` only when no wrapper document can be decoded, with `WRAPPER_JSON_MALFORMED` and a typed error required. Otherwise a malformed wrapper cannot produce the validated result that the FR promises because the required prerequisites object exists only inside that document (`feature-requests/FR-948-lan-copilot-delegation.md:142-167,198,251`).

### R-2: Make the wall-clock cap a real process-lifetime boundary

Do not equate a WinRM `operation_timeout` with termination of the remote Copilot process. The spike contains no timeout witness and explicitly limits its proof to a successful invocation (`feature-requests/FR-948-spike-evidence.md:79-99`), while the FR currently claims that operation timeout terminates `copilot.cmd` (`feature-requests/FR-948-lan-copilot-delegation.md:75,233-235`).

Specify a wrapper-owned deadline that starts Copilot as a tracked process, waits for at most `timeout_s`, terminates the full child process tree on expiry, records `TIMEOUT`, and still runs credential clearing, worktree cleanup, and summary emission. Set the outer WSMan operation timeout above that deadline by a documented cleanup margin; it is a transport-failure bound, not the preventive spend cap.

Add a real Huutokauppakone timeout witness, not only the mocked test at line 194. The witness must use a deliberately shorter deadline than the remote operation, then record: non-zero CLI, `timed_out=True`, `TIMEOUT`, no surviving tracked process tree, no remaining run worktree, and no literal token in returned material. The physical process-termination property is the cap on which the dated spend decision depends, so `.github/copilot-instructions.md:81` requires a real witness.

### R-3: Close collision, cleanup, and status totality

Split collision checks by boundary. Before WinRM, refuse an existing local result/log path. During the fixed remote preflight and before worktree creation or Copilot invocation, refuse both an existing run-worktree path and an existing SMB destination directory. Do not enumerate or copy into a pre-existing destination. This makes the isolation claim true; checking only the worktree allows stale SMB files to be attributed to a new run (`feature-requests/FR-948-lan-copilot-delegation.md:73,99-103,121-126,180,200,244,248`).

Extend `DelegationPolicyStatus` and the test matrix to cover at least worktree-add failure, output-directory creation failure, wrapper execution failure before Copilot, and worktree-cleanup failure. Define deterministic precedence when more than one failure occurs, and require every post-WinRM path to return a validated `LanDelegationResult` even when Copilot was never invoked. The present enum omits these wrapper-owned failure phases while claiming launched-run totality (`feature-requests/FR-948-lan-copilot-delegation.md:103-126,140-167,251`).

### R-4: State the actual containment and credential guarantees

Replace "Copilot writes only to `.delegate-out`" with the enforceable statement that only files rooted beneath the newly created `.delegate-out` are eligible for copying and result attribution. `--allow-all-tools` allows child tools to act with all `copilot`-user privileges, which the human decision already acknowledges; omitting `--allow-all-paths` is not a filesystem sandbox (`feature-requests/FR-948-lan-copilot-delegation.md:224-229,247-250`). Keep arbitrary remote mutations outside FR authority, but do not claim the process cannot perform them.

Define token protection mechanically. Before copying, scan every candidate artifact as bytes for the exact `GH_TOKEN` byte sequence; on a match, copy none of that artifact, record a typed `TOKEN_LEAK_DETECTED` error/status, and return non-zero. Redact the exact token from captured stdout/stderr before either stream is persisted. Add success, Copilot-failure, timeout, malformed-summary, and artifact-copy-failure tests. Narrow the absolute claim to literal-token non-persistence; the FR must retain the dated acknowledgement that a tool-enabled model can read the token and that transformed/encoded exfiltration is not prevented (`feature-requests/FR-948-lan-copilot-delegation.md:37,74,193,224-229,250`).

### R-5: Prevent delegated Copilot from delegating again and prove skill loading

The run worktree contains the new `lan-delegate` skill and `--add-dir <run-worktree>` makes repository skills visible to the remote Copilot (`feature-requests/FR-948-lan-copilot-delegation.md:57-62,105-118`). A heavy-work prompt can therefore satisfy the same skill trigger that launched the current run. Add a hard re-entry guard: the wrapper sets a fixed `YAMLGRAPH_LAN_DELEGATED=1` marker in the Copilot child environment; `delegate.py` refuses with a typed exception when that marker is present; and `SKILL.md` states that an already-delegated process executes locally and never invokes LAN delegation. Test both the code refusal and marker propagation.

Strengthen the success witness so it proves the unverified differentiator identified by the spike. The real run must invoke the repository's named `run-code-analysis` skill through `--add-dir <run-worktree>`, execute a bounded representative static-analysis workload, and return an artifact whose command/result shape is specific to that skill. Record observable Copilot output naming the selected skill, as well as both matched SHAs and the existing result fields. A generic pytest prompt would prove remote shell execution again, not skill loading (`feature-requests/FR-948-spike-evidence.md:90-99`; `feature-requests/FR-948-lan-copilot-delegation.md:205,207-209,256`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/lan-delegate/SKILL.md`, `delegate.py`, `models.py`, and `wrapper.ps1` |
| D-2 | `tests/unit/test_lan_delegate.py` and sanitized fixtures used only by that module |
| D-3 | `capabilities/CAP-257-lan-copilot-delegation.yaml`, `REQ-YG-636`, and regenerated `ARCHITECTURE.md` registry content |
| D-4 | `reference/development-operations.md` LAN-delegation subsection and commented `.env.sample` `GH_TOKEN` placeholder |
| D-5 | `changelog/unreleased/fr-948-lan-copilot-delegation.md` and `changelog/unreleased/fr-948-retire-fr947.md` |
| D-6 | `feature-requests/FR-948-lan-copilot-delegation.md` revisions, implementation status, and sanitized live-witness records |
| D-7 | FR-947 supersession bookkeeping only; preserve `feature-requests/FR-947-remote-pytest-delegation.md:3-9` |
| D-8 | One FR-948 diary entry carrying the required metacognitive reflection and `Seed:` |

Not authorized: changes to FR-945 or its recon schema/implementation; CAP-30 or the YAMLGraph Copilot node; graph-level invocation, graph-level credit budgeting, or any graph artifact; judge/review doctrine, hooks, CI, or Chaplain; remote software installation, cloning, fetching, source upload, users/groups, firewall, services, shares, SSH, or WSL; `--resume`; fleet scheduling; fallback to local execution; a preventive credit claim stronger than the witnessed process deadline; or remote mutation outside the disposable worktree/process and designated artifact directory.

## Revised acceptance criteria

- [ ] AC-01: The FR retains five genuine solution classes, dispositions for every retrieved prior-art hit, the reconciled "not a graph; consumed by graphs" answer, and the **contrib/example** strategic classification.
- [ ] AC-02: Every claim attributed to the spike is bounded by `FR-948-spike-evidence.md:79-99`; the FR does not attribute repository workload, timeout termination, Python provisioning, or `--add-dir` skill loading to that spike.
- [ ] AC-03: FR-945 is a precondition only; FR-948 consumes its committed receipt fields, reuses `pypsrp>=0.9,<1.0`, and does not modify FR-945.
- [ ] AC-04: `LanDelegationRequest`, `ToolInfo`, `RepoInfo`, `RemoteCopilotPrerequisites`, `LanDelegationResult`, `FieldError`, all closed status/error enums, and every pre-launch exception are completely specified and implemented without an untyped boundary.
- [ ] AC-05: Local validation refuses missing/stale/disqualifying inventory, missing credentials, dirty Git state, invalid host/run ID, unsafe or colliding local paths, and missing/non-UTF-8/oversized prompt before DNS, WinRM, or file write.
- [ ] AC-06: Remote preflight verifies git, node major at least 22, Copilot CLI/version, canonical-clone containment of `local_sha`, free worktree path, and absent SMB destination before worktree creation or Copilot invocation.
- [ ] AC-07: A successful run records `local_sha` and independently reads `remote_sha` from the detached run worktree; model validation and tests require exact equality.
- [ ] AC-08: Client construction uses the FR-945 pinned address with exact `auth="negotiate"`, `encryption="always"`, `ssl=False`, port 5985, and finite connection/operation timeouts; Basic, CredSSP, and downstream DNS re-resolution are absent.
- [ ] AC-09: Prompt and token cross WinRM only through bound parameters and are absent from script literals; Copilot uses `--allow-all-tools --add-dir <run-worktree>` without `--allow-all-paths`.
- [ ] AC-10: The wrapper owns a process deadline shorter than the outer WSMan timeout, kills the tracked process tree on expiry, executes cleanup, and returns a validated `TIMEOUT` result.
- [ ] AC-11: Only files rooted beneath the new run's `.delegate-out` are eligible for SMB copy; the SMB destination must be absent before launch; two concurrent runs and a stale-destination case prove exact attribution.
- [ ] AC-12: Exact token bytes are redacted before stdout/stderr persistence and block any matching artifact from being copied; `TOKEN_LEAK_DETECTED` is typed and non-zero. The FR claims no protection against transformed token exfiltration and retains the dated human risk acceptance.
- [ ] AC-13: Every post-WinRM failure phase has a typed status, deterministic precedence, non-zero CLI result, and validated `LanDelegationResult`; malformed wrapper output alone permits `prerequisites=None`.
- [ ] AC-14: Reported credits remain post-run diagnostics only. Missing, malformed, or over-threshold reports fail policy while preserving non-secret artifacts; no hard credit or bounded-cost claim is made.
- [ ] AC-15: v1 has no `--resume`, source transfer, fetch, clone, installation, service/policy/firewall/group mutation, fleet abstraction, local fallback, or graph-level budget implementation; committed-source scans enforce the forbidden wrapper operations.
- [ ] AC-16: The wrapper propagates `YAMLGRAPH_LAN_DELEGATED=1`; both `delegate.py` and `SKILL.md` refuse recursive LAN delegation; offline tests prove refusal occurs before receipt loading or WinRM.
- [ ] AC-17: Offline tests cover all specified input, transport, preflight, lifecycle, status-precedence, redaction, timeout, collision, concurrency, cleanup, and recursion seams without real DNS, socket, WinRM, SMB, or Copilot.
- [ ] AC-18: A real short-timeout Huutokauppakone run proves process-tree termination, no remaining run worktree, validated `TIMEOUT`, non-zero CLI, and literal-token non-persistence.
- [ ] AC-19: A separate real Huutokauppakone success run loads the named `run-code-analysis` skill through the run root, executes a bounded representative static-analysis workload, returns the skill-specific artifact, and records observable skill selection, matched local/remote SHAs, run/worktree IDs, exit/policy/credit states, elapsed time, and exact artifact list.
- [ ] AC-20: CAP-257/REQ-YG-636, strict requirement coverage, generated architecture content, skill frontmatter, operational docs, environment sample, two changelog fragments, FR-947 supersession, implementation status, and diary entry are committed; no file outside D-1..D-8 changes.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | A human reviews this advisory draft and R-1..R-5 plus AC-01..AC-20 are folded into the committed FR before implementation authority activates. | GATE |
| C-2 | FR-945 remains a read-only dependency; FR-948 must not change its schema, skill, tests, capability, or host configuration. | GATE |
| C-3 | No remote bootstrap, installation, cloning, fetching, source upload, account/group, policy, firewall, service, share, SSH, or WSL mutation may be added. | GATE |
| C-4 | The human safety/spend decisions remain explicit; implementation must not relabel post-run credit diagnosis as a preventive cap or `--allow-all-tools` as a filesystem sandbox. | GATE |
| C-5 | The real timeout witness in AC-18 must pass before the channel is marked implemented because timeout is the sole preventive spend boundary. | GATE |
| C-6 | The recursive-delegation guard is mandatory before any live success witness uses `--add-dir <run-worktree>`. | GATE |
| C-7 | Graph integration, graph-level budgets, resume, fleet scheduling, and local fallback require separate FRs. | GATE |
| C-8 | Changes are restricted to D-1..D-8; hooks, CI, judge/review doctrine, Chaplain, CAP-30, and the YAMLGraph Copilot node are excluded. | GATE |

Authority granted: after C-1 is satisfied, implement only the stateless single-host LAN Copilot delegation contrib/example and lifecycle surfaces frozen in D-1..D-8.
