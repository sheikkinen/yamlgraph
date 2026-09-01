# Judgement: FR-948 LAN Copilot-CLI delegation channel

**Verdict:** APPROVED WITH REVISIONS — the one-host contrib/example is justified and empirically grounded, but authority activates only after R-1 through R-6 make process launch, timeout cleanup, secret handling, failure typing, result paths, and the D-1..D-8 scope internally complete.

**Prior art:**
- [FR-948-lan-copilot-delegation.md](FR-948-lan-copilot-delegation.md), [FR-948.research.md](FR-948.research.md), [spike-evidence-fr948-copilot-remote.md](spike-evidence-fr948-copilot-remote.md) — the artifacts under judgement; self-references.
- [FR-945-lan-recon-skill.md](FR-945-lan-recon-skill.md) [Proposed] and [FR-945-lan-recon-skill.judgement.md](FR-945-lan-recon-skill.judgement.md) — read-only recon precondition.
- [FR-947-remote-pytest-delegation.md](FR-947-remote-pytest-delegation.md) [Superseded-by FR-948] — SSH design retired.
- [CAP-30 Copilot Node](../capabilities/CAP-30-copilot-node.yaml) — precedent; explicitly out of scope per C-7 (NOT modified).

**Reviewed against:** `feature-requests/FR-948-lan-copilot-delegation.md`; `feature-requests/spike-evidence-fr948-copilot-remote.md`; `feature-requests/FR-948.research.md`; `feature-requests/research-briefs/copilot-cli-remote-delegation-brief.md`; `feature-requests/FR-945-lan-recon-skill.md`; `feature-requests/FR-945.research.md`; `feature-requests/FR-946-huutokauppakone-inference-revival.md`; `feature-requests/FR-947-remote-pytest-delegation.md`; `feature-requests/FR-766-runpod-provider.md`; `feature-requests/FR-899-org-repo-census-azure.md`; `feature-requests/FR-899-org-repo-census-azure.judgement.md`; `capabilities/CAP-30-copilot-node.yaml`; `capabilities/CAP-249-tool-slot-binding.yaml`; `pyproject.toml`; `.github/skills/lan-recon/recon.py`; `.github/skills/run-code-analysis/SKILL.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

**Scope and single responsibility:** the first consumer and event are concrete, and the proposal owns one coherent boundary: submit one clean commit to one already-qualified LAN host, run one stateless Copilot workload, and return isolated diagnostics/artifacts (`feature-requests/FR-948-lan-copilot-delegation.md:8`, `feature-requests/FR-948-lan-copilot-delegation.md:20-36`). Retiring the unimplemented FR-947 is lifecycle bookkeeping coupled to choosing this replacement, not an orthogonal implementation concern (`feature-requests/FR-947-remote-pytest-delegation.md:1-12`). Fleet management, installation, source transfer, resume, local fallback, and graph-level budgeting are explicitly excluded (`feature-requests/FR-948-lan-copilot-delegation.md:277-283`).

**Research and strategic classification:** the committed research record preserves disagreement about whether this is a graph and exposes cost/session-state risks (`feature-requests/FR-948.research.md:12-18`). More importantly, the FR body reconciles that disagreement, dispositions five genuine solution classes, and explains why the channel is not itself a graph (`feature-requests/FR-948-lan-copilot-delegation.md:40-50`). The classification **Contrib/example** is correct: there is one host and one immediate consumer, while existing skill, WinRM, and Copilot-node precedents provide the primitives (`feature-requests/FR-948-lan-copilot-delegation.md:20-22`; `capabilities/CAP-30-copilot-node.yaml:1-19`). It is not a framework primitive because the required 3+ use cases are absent under the judge rubric (`.github/skills/judge-fr/doctrine.md:38-44`).

**Feasibility and architecture alignment:** the spike proves the narrow transport/model/tool/file-return chain and honestly lists what it did not prove (`feature-requests/spike-evidence-fr948-copilot-remote.md:79-99`). FR-945 already establishes the pinned-address Negotiate/encryption transport and typed recon receipt (`feature-requests/FR-945-lan-recon-skill.md:64-85`, `feature-requests/FR-945-lan-recon-skill.md:87-118`); the repository has the required `pypsrp>=0.9,<1.0` dependency and a working client-construction precedent (`pyproject.toml:44-57`; `.github/skills/lan-recon/recon.py:74-101`). The proposal reuses those boundaries rather than inventing a second transport.

**Measurability and testability:** the FR distinguishes offline seam tests from two real physical witnesses, which follows the doctrine that tests prove constraints while demos prove abstraction worth (`feature-requests/FR-948-lan-copilot-delegation.md:219-243`; `.github/copilot-instructions.md:145`). The SHA equality, collision, recursion, literal-token, timeout, and named-skill witnesses are substantially more diagnostic than terminal-success checks (`feature-requests/FR-948-lan-copilot-delegation.md:221-243`, `feature-requests/FR-948-lan-copilot-delegation.md:265-286`). After the revisions below, failing tests can be written directly from the criteria.

The strongest case against authority is not that remote Copilot delegation is unreal; the spike defeats that claim. It is that the current pseudo-wrapper can mis-tokenize an arbitrary prompt, persist an unredacted token before redaction, leave descendants alive, and then lack a total result status for those failures. Those are boundary-contract defects and must be corrected before implementation.

## Required revisions

### R-1: Freeze a PowerShell 5.1-safe argv contract

Replace the `Start-Process ... -ArgumentList @('-p', $Prompt, ...)` snippet with an explicit PowerShell 5.1-compatible launch contract that preserves `$Prompt` as exactly one child argument and retains a process handle/PID for the deadline. `Start-Process` joins `ArgumentList` elements into a command line, while the committed spike used PowerShell's call operator after an earlier argument-shape failure (`feature-requests/FR-948-lan-copilot-delegation.md:107-114`; `feature-requests/spike-evidence-fr948-copilot-remote.md:30-39`; `feature-requests/research-briefs/copilot-cli-remote-delegation-brief.md:68-74`).

Fold into the FR the exact encoder/launcher contract. The child argv must be exactly `["-p", <prompt-as-one-value>, "--allow-all-tools", "--add-dir", <worktree>]`; prompt text must never become flags or shell syntax. Add offline witnesses for whitespace, double and single quotes, backticks, CR/LF, trailing backslashes, non-ASCII text, and a prompt beginning with `--allow-all-paths`. Assert the reconstructed child argv byte-for-byte and assert that no extra flag appears. Extend the AC-19 live prompt with spaces and punctuation so the real host witnesses the same seam.

### R-2: Make the deadline terminate the full tree and make cleanup unconditional

Replace the one-level `ParentProcessId` enumeration and silent `catch {}` blocks (`feature-requests/FR-948-lan-copilot-delegation.md:115-124`) with a frozen full-tree termination primitive: on timeout invoke Windows `taskkill /PID <tracked-pid> /T /F`, check its exit status, and emit a typed `PROCESS_TREE_KILL_FAIL` if termination cannot be proved. Put process termination, worktree removal, and `GH_TOKEN` clearing in an outer `finally` whose failures are retained in `errors`; no cleanup exception may be swallowed. `TIMEOUT` is valid only when full-tree termination succeeds; kill failure outranks `TIMEOUT`.

Revise AC-10 and AC-18 so the workload creates a named long-lived descendant, the wrapper records the tracked root and observed descendant PIDs without credentials, and the follow-up WinRM query proves all recorded PIDs are absent. The witness must also prove the run worktree and token environment are absent. Checking only for a surviving `copilot.exe` is insufficient because the stated contract covers every child tool (`feature-requests/FR-948-lan-copilot-delegation.md:241`).

### R-3: Prevent raw token bytes from reaching persistent stdout/stderr files

The wrapper currently redirects child output straight to `$stdout`/`$stderr` and only later says those files are redacted (`feature-requests/FR-948-lan-copilot-delegation.md:110-113`, `feature-requests/FR-948-lan-copilot-delegation.md:126-129`). That contradicts “redacted BEFORE persistence” and the ideal that literal token bytes appear nowhere (`feature-requests/FR-948-lan-copilot-delegation.md:34-36`, `feature-requests/FR-948-lan-copilot-delegation.md:279`).

Fold a no-raw-spool contract into the FR: capture stdout and stderr through byte streams into bounded volatile memory, replace every literal token-byte occurrence there, and only then write the local diagnostic logs. Do not use `-RedirectStandardOutput` or `-RedirectStandardError` with a filesystem path. Add explicit size bounds and typed `OUTPUT_CAPTURE_FAIL` behavior; output exceeding the bound must fail closed, terminate the process tree, and run cleanup. Tests must instrument every filesystem write on success, non-zero, timeout, and malformed-output paths and prove no written byte sequence contains the token; a committed-source assertion must reject raw-file redirection in `wrapper.ps1`. Keep the dated acknowledgement that transformed/encoded exfiltration is outside v1 (`feature-requests/FR-948-lan-copilot-delegation.md:255-263`).

### R-4: Make the result schema total over every attempted-WinRM failure

The FR says a `LanDelegationResult` exists whenever WinRM was attempted and that `prerequisites=None` is allowed only for malformed wrapper JSON (`feature-requests/FR-948-lan-copilot-delegation.md:171-184`). Yet the enum and precedence omit connect, authentication, transport-timeout, output-capture, and process-tree-kill failures; `PREFLIGHT_FAIL` exists in the enum but is absent from the precedence list (`feature-requests/FR-948-lan-copilot-delegation.md:160-166`). AC-13 therefore cannot be implemented for all post-attempt paths (`feature-requests/FR-948-lan-copilot-delegation.md:278`).

Add `WINRM_CONNECT_FAIL`, `WINRM_AUTH_FAIL`, `WINRM_TRANSPORT_TIMEOUT`, `OUTPUT_CAPTURE_FAIL`, and `PROCESS_TREE_KILL_FAIL` to `DelegationPolicyStatus`, its deterministic precedence, and mocked witnesses. List every enum member exactly once in the precedence table. Define `prerequisites=None` for failures before a valid preflight document exists, not only malformed JSON. Define `PREFLIGHT_FAIL` as ordinary prerequisite refusal; reserve `SMB_DEST_EXISTS` for the post-preflight race where the destination becomes occupied. Extend the typed error vocabulary so auth, transport, capture, and termination failures do not collapse to `unknown`. State for each phase whether Copilot ran, whether cleanup was attempted, which result fields may be `None`, and which CLI exit is required.

### R-5: Complete host validation and cross-platform result-path semantics

AC-05 promises invalid-host refusal, but the input contract defines neither host grammar nor an exception for it (`feature-requests/FR-948-lan-copilot-delegation.md:56-70`, `feature-requests/FR-948-lan-copilot-delegation.md:270`). Add `UnsafeHostError`; reuse FR-945's DNS/IP and canonical-safe-slug rules; derive the receipt path only after validation; and require the requested host to match the receipt's `requested_target` before using its pinned address. The refusal must occur before receipt access, DNS, WinRM, or file creation.

The first-consumer and ideal contracts promise an artifact root, but `LanDelegationResult` has no `artifact_root`, and `Path` does not define whether artifact entries are mac-local paths or Windows UNC paths (`feature-requests/FR-948-lan-copilot-delegation.md:8`, `feature-requests/FR-948-lan-copilot-delegation.md:34-36`, `feature-requests/FR-948-lan-copilot-delegation.md:171-194`). Add `artifact_root: str | None` with UNC semantics, make `artifacts` root-relative POSIX-style strings or explicitly typed UNC strings, and keep `stdout_path`/`stderr_path` as local `Path` values beneath `tmp/lan/delegate/<host-slug>/`. Define when those three fields exist on every status, including transport failure and token-leak refusal. Add schema invariants and round-trip tests for macOS parsing of Windows paths.

### R-6: Put the referenced D-1..D-8 boundary into the FR and align the criteria

The governance text and AC-20 prohibit changes outside D-1..D-8, but the FR contains no D-1..D-8 table (`feature-requests/FR-948-lan-copilot-delegation.md:245-253`, `feature-requests/FR-948-lan-copilot-delegation.md:286`). Fold the exact table from “Scope is frozen” below into the FR. Update the schema, test list, AC-04/05/10/12/13/17/18/19/20, and implementation estimate to include R-1 through R-5. Remove stale wording that calls the current 20 criteria the judge's revised list unless the folded list exactly matches this judgement (`feature-requests/FR-948-lan-copilot-delegation.md:265`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/lan-delegate/SKILL.md`, `delegate.py`, `models.py`, and `wrapper.ps1` implementing the folded boundary |
| D-2 | `tests/unit/test_lan_delegate.py` and narrowly scoped sanitized fixtures for argv, result schemas, output capture, lifecycle, and status precedence |
| D-3 | `capabilities/CAP-257-lan-copilot-delegation.yaml`, `REQ-YG-636` markers, and generated `ARCHITECTURE.md` traceability |
| D-4 | `reference/development-operations.md` LAN-delegation subsection and commented `.env.sample` placeholder |
| D-5 | `changelog/unreleased/fr-948-lan-copilot-delegation.md` and `changelog/unreleased/fr-948-retire-fr947.md` |
| D-6 | `feature-requests/FR-948-lan-copilot-delegation.md`, including folded revisions, implementation status, and sanitized AC-18/AC-19 command/result evidence |
| D-7 | `feature-requests/FR-947-remote-pytest-delegation.md` supersession bookkeeping only |
| D-8 | `docs/diary/2026-09-XX-fr948-copilot-delegation.md` reflection with a `Seed:` |

Not authorized: changes to FR-945's schema or implementation; changes to CAP-30 or YAMLGraph's Copilot node; graphs or prompts; source transfer, clone, fetch, installation, service/policy/firewall/group mutation, resume, fleet scheduling, local fallback, or graph-level budget enforcement; CI, hooks, judge/review doctrine, Chaplain, unrelated dependencies, or any file outside D-1..D-8. Remote prerequisites remain inspected preconditions, never repaired by this feature.

## Revised acceptance criteria

- [ ] **AC-01** The FR retains five genuine solution classes, preserved disagreement, every prior-art disposition, the reconciled “not a graph; consumed by graphs” answer, and **Contrib/example** classification.
- [ ] **AC-02** Every spike-attributed claim stays within `spike-evidence-fr948-copilot-remote.md:79-99`; repository workload, deadline termination, Python provisioning, and skill loading are attributed only to later witnesses.
- [ ] **AC-03** FR-945 remains a read-only precondition: FR-948 consumes its committed receipt and existing `pypsrp>=0.9,<1.0` transport without modifying FR-945.
- [ ] **AC-04** All request, prerequisite, result, error, status, and pre-launch-exception models named in the folded schema are Pydantic-implemented with invariants; no untyped boundary crosses from receipt/wrapper JSON into control flow.
- [ ] **AC-05** Local validation rejects unsafe host, host/receipt mismatch, missing/stale/disqualifying receipt, missing token, dirty tree, unsafe run ID, path collision, and missing/non-UTF-8/oversized prompt before DNS, WinRM, or file write.
- [ ] **AC-06** Remote preflight verifies git, Node major >=22, Copilot path/version, canonical clone SHA availability, free run worktree, and free SMB destination before worktree creation or Copilot invocation.
- [ ] **AC-07** A successful run records independently obtained local and remote SHAs; `OK` requires exact equality.
- [ ] **AC-08** The client uses the receipt's pinned address, Negotiate, mandatory encryption, HTTP 5985, finite connect timeout, and outer operation timeout equal to wrapper timeout plus cleanup margin; Basic, CredSSP, and downstream DNS are absent.
- [ ] **AC-09** Prompt and token cross WinRM only as bound parameters; the PowerShell 5.1 launcher preserves the prompt as one child argv value for every R-1 edge-case fixture; only the frozen Copilot flags appear.
- [ ] **AC-10** The wrapper-owned deadline is shorter than WSMan's outer timeout; timeout uses checked `taskkill /T /F`; `TIMEOUT` requires proven full-tree termination; kill failure is typed and outranks timeout.
- [ ] **AC-11** Process-tree termination, worktree removal, and token clearing execute in an outer `finally`; every cleanup failure is typed and retained, never silently caught.
- [ ] **AC-12** Child stdout/stderr are captured as bounded volatile bytes, token-redacted before any persistence, and written only to the local diagnostic paths; raw filesystem redirection is absent.
- [ ] **AC-13** Only byte-scanned files rooted under the run's `.delegate-out` are eligible for the new SMB destination; token matches are skipped and fail typed; concurrent-run and destination-race tests prove exact attribution.
- [ ] **AC-14** Every attempted-WinRM failure has a validated result, non-zero CLI status, typed error, and one closed-enum policy status; all statuses occur exactly once in precedence; nullable fields obey phase invariants.
- [ ] **AC-15** Credit parsing remains post-run diagnostics only; missing, malformed, or excessive reports fail policy while preserving clean artifacts; no preventive credit/budget claim is made.
- [ ] **AC-16** v1 contains no resume, transfer, fetch, clone, installation, host mutation, fleet abstraction, local fallback, graph, or graph-level budget; committed-source tests enforce forbidden wrapper operations.
- [ ] **AC-17** `YAMLGRAPH_LAN_DELEGATED=1` reaches the child; both code and skill refuse recursion before receipt loading or WinRM.
- [ ] **AC-18** Offline tests cover every input, argv, transport, preflight, schema invariant, status, precedence, capture/redaction, deadline, process-tree, collision, concurrency, cleanup, and recursion seam without real DNS, sockets, WinRM, SMB, or Copilot.
- [ ] **AC-19** A real short-timeout run creates a named long-lived descendant and proves non-zero CLI, validated timeout/kill status, matching SHA, absence of every recorded process PID, absence of worktree, token clearing, and zero literal-token bytes in all persisted outputs.
- [ ] **AC-20** A real success run uses a punctuation-bearing prompt to select `run-code-analysis` through `--add-dir`, produces the named skill-specific artifact, and records observable selection, matching SHAs, run/worktree IDs, exit/policy/credit states, elapsed time, artifact root, and exact artifact list.
- [ ] **AC-21** CAP-257/REQ-YG-636, strict requirement coverage, generated architecture, skill frontmatter, operations docs, `.env.sample`, two changelog fragments, FR-947 supersession, implementation status, and diary reflection are committed.
- [ ] **AC-22** The diff changes no file outside D-1..D-8.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-6 are folded into FR-948 and this advisory draft is human-reviewed before implementation begins. | GATE |
| C-2 | The dated human safety/spend decisions remain the only authority for `--allow-all-tools`, the live token, transformed-exfiltration residual risk, and timeout-as-cap; the enforcer may not broaden them. | GATE |
| C-3 | Remote mutation and prerequisite installation are forbidden; a failed preflight must return diagnostics, not repair the host. | GATE |
| C-4 | Offline RED witnesses for the folded seams precede production implementation; every test carries `@pytest.mark.req("REQ-YG-636")`. | GATE |
| C-5 | `wrapper.ps1` remains ASCII and Windows PowerShell 5.1-compatible; no silent catch, raw secret spool, or unchecked process termination is permitted. | GATE |
| C-6 | Live AC-19/AC-20 runs occur only after offline gates pass; committed evidence is sanitized and contains no credential, raw prompt secret, or private token-derived value. | GATE |
| C-7 | No file or behavior outside D-1..D-8 is changed under FR-948 authority. | GATE |

Authority granted: after R-1 through R-6 are folded and human review accepts this advisory judgement, the enforcer may implement only D-1..D-8 and satisfy AC-01 through AC-22 under C-1 through C-7.
