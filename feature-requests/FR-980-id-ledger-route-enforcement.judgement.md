# Judgement: FR-980 Allocator Inventory and Mandatory Route Enforcement for CAP/REQ Reservation

**Prior art:** see FR-980's own Prior Art field (FR-970, FR-975, FR-180, FR-701, FR-767, FR-466) — this judgement reviews and dispositions those same citations; no additional prior art beyond what FR-980 already names.

**Verdict:** APPROVED WITH REVISIONS — mandatory route enforcement is the correct Successor B, but authority activates only after the inventory names every executable Plan/Enforce/Chaplain/operator surface, the wrapper owns a real child-scoped write envelope, human/editor bypasses are blocked at commit and merge boundaries, legacy allocation fails closed, FR-975 is implemented, and this enforcement-infrastructure draft receives human review.

**Reviewed against:** `feature-requests/FR-980-id-ledger-route-enforcement.md`; `feature-requests/FR-980.research.md`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.md`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md`; `feature-requests/FR-975-id-ledger-reservation-protocol.md`; `feature-requests/FR-975-id-ledger-reservation-protocol.judgement.md`; `feature-requests/FR-180-plan-phase-id-reservation.md`; `feature-requests/FR-701-capability-registry-consistency-gate.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-466-cap-retirement-support.md`; repository filename inventory for `feature-requests/FR-465-*.md`; `feature-requests/TEMPLATE.md`; `.github/skills/feature-request/SKILL.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `scripts/id_registry.py`; `scripts/validate_id_registry.py`; `scripts/validate_capabilities.py`; `.chaplain/id-registry.yaml`; `.pre-commit-config.yaml`; `.github/workflows/workflow.yml`; `.github/hooks/pre-command-guard.json`; `.github/hooks/scripts/pre-command-guard.sh`; `scripts/author.sh`; `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml`; `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml`; `.chaplain/config/watcher-pipeline-v2.yaml`; `.github/skills/judge-fr/adapters/graph.yaml`; `.github/skills/review-pr/adapters/graph.yaml`; `.github/skills/graph-authoring/adapters/graph.yaml`; and repository-wide committed searches for callers of `reserve_ids()`, `save_registry()`, and `load_registry()`.

## What is sound

The problem is real and the predecessor split is being respected. The legacy allocator computes IDs by mutating local counters and an in-memory reservation list (`scripts/id_registry.py:68-105`), while the committed registry remains at `next_cap: 94` and `next_req: 246` (`.chaplain/id-registry.yaml:11-23`). FR-701 records the concrete CAP-195/REQ-YG-531 collision and the missing preventive boundary (`feature-requests/FR-701-capability-registry-consistency-gate.md:17-31`). FR-980 correctly keeps the remote-ref reservation protocol in FR-975, preserves the independent duplicate validator, and confines itself to making adoption load-bearing (`feature-requests/FR-980-id-ledger-route-enforcement.md:18-24,171-172`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md:84-108`).

The proposal also preserves the advisory boundaries that caused FR-970 to be split. The judge, review, and graph-authoring adapters explicitly forbid commit/push or merge side effects (`.github/skills/judge-fr/adapters/graph.yaml:1-5`; `.github/skills/review-pr/adapters/graph.yaml:1-5`; `.github/skills/graph-authoring/adapters/graph.yaml:1-5`), and FR-980 leaves those adapters unchanged (`feature-requests/FR-980-id-ledger-route-enforcement.md:101-107`). Requiring an isolated commit and explicit human review for the new hook is also correct for adversarial enforcement infrastructure (`feature-requests/FR-980-id-ledger-route-enforcement.md:109-115`; `.github/copilot-instructions.md:74`).

The research gate exists, records five personas, preserves dissent, includes precedent, and answers `is_this_a_graph` (`feature-requests/FR-980.research.md:1-20`). Its useful conclusion is that storage and adoption are separate: FR-975 owns remote serialization, while this FR owns route calls and bypass denial. The selected work remains one responsibility. Direct-agent prevention, Chaplain wiring, a commit/merge backstop, and removal of the legacy bypass are layers of the same route-enforcement boundary, not independent product features.

Against the eight criteria:

1. **Scope:** route adoption is the minimal missing successor and does not need another split. The current four-row inventory is not yet an allocator inventory, however: it includes a validator that writes no identifiers and a helper with no committed callers, while failing to name the separate Plan and Enforce execution paths required by the predecessor (`feature-requests/FR-980-id-ledger-route-enforcement.md:36-44`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md:89-94`).
2. **Consistency:** the Summary promises denial before every new identifier write, but the proposed guard covers agent PreToolUse only, limits FR governance to new-file creation, and nevertheless claims to cover human editing and every CAP/REQ string (`feature-requests/FR-980-id-ledger-route-enforcement.md:8-12,18-24,41,71-79`). Existing FR edits can introduce allocations, and `scripts/validate_id_registry.py` cannot satisfy the Ideal Result because it allocates nothing (`feature-requests/FR-980-id-ledger-route-enforcement.md:44,53-65`). The Prior Art field also says “see Constraints,” but the FR has no Constraints section (`feature-requests/FR-980-id-ledger-route-enforcement.md:14`).
3. **Measurability:** exact-ID allow/deny tests are sound (`feature-requests/FR-980-id-ledger-route-enforcement.md:154-161`). AC-02 does not define how an exited shell wrapper can authorize a later tool call; AC-04 says only “simulates” concurrency; AC-05 would require executing LLM-backed adapters without defining a deterministic seam; and AC-06 permits an unspecified “file-level equivalent” (`feature-requests/FR-980-id-ledger-route-enforcement.md:156-170`). Those are not complete mechanical witnesses.
4. **Feasibility:** a shell process cannot export a token into its parent or a later independent Copilot tool call. The cited FR-767 mechanism works because `scripts/author.sh` creates the token file, exports the matching token only to the child authoring execution, and removes both on wrapper exit (`scripts/author.sh:61-69,84-89`). FR-980 instead says `allocate_ids.sh` exits after arming a sentinel and a “subsequent write” succeeds, without defining a child writer, session binding, expiry, cleanup, target manifest, or how `--cap N --req M` determines “specific paths” (`feature-requests/FR-980-id-ledger-route-enforcement.md:71-79,156-158`).
5. **Architecture alignment:** reusing the FR-767 guard shape is appropriate, but its actual boundary is Copilot `PreToolUse`, configured as a command hook (`.github/hooks/pre-command-guard.json:1-8`) and limited to enumerated agent tools (`.github/hooks/scripts/pre-command-guard.sh:142-182,240-271`). It cannot intercept an ordinary editor or shell outside Copilot. The current CI also treats all-markdown changes as docs-only and runs no registry gate on that path (`.github/workflows/workflow.yml:17-31,65-116`), so an FR-only unreserved allocation has no merge-boundary witness. Repository doctrine requires a CI block rather than an advisory lint claim (`.github/copilot-instructions.md:151-152`).
6. **Single responsibility:** the valid scope is one concern: make FR-975 mandatory at every allocation boundary. Legacy retirement is a directly coupled purge because leaving a working local allocator preserves a bypass. The validator-name cleanup noted by the FR is correctly out of scope (`feature-requests/FR-980-id-ledger-route-enforcement.md:44`).
7. **Strategic classification:** this is repository process/enforcement infrastructure with recurring Plan, Enforce, Chaplain, and direct-operator consumers. It is not a YAMLGraph framework primitive, contrib example, or documentation-only pattern. The incident evidence and dead optional helper justify code, but not a new service or dependency (`feature-requests/FR-980-id-ledger-route-enforcement.md:26-32,137-142`).
8. **Testability:** failing tests can be written for exact reservation/path grants, wrong IDs, stale or cross-session sentinels, legacy denial, route callers, and merge-boundary rejection. The present criteria cannot prove the human/operator surface, existing-FR edits, shell write shapes, wrapper lifecycle, or real route-to-ledger composition; the predecessor explicitly requires mechanical bypass tests for planning, enforcement, Chaplain, and direct operators (`feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md:89-94`).

The strongest case against the selected mechanism is therefore not that route enforcement is unnecessary, but that a PreToolUse sentinel alone cannot deliver the proposal's own universal claim. The repair is to retain PreToolUse as the early agent boundary, add a deterministic commit-and-merge proof for editor/operator bypasses, and narrow the promise honestly: compliant routes reserve before writing; bypassed local text may exist, but no unreserved allocation may be committed or merged.

## Required revisions

### R-1: Replace the four-row inventory with executable allocation events

Rewrite the Problem inventory so each row names: allocator class, entry event, current executable path, where CAP/REQ counts become known, stable `request_id` source, mandatory FR-975 call, denial boundary, and test.

At minimum, distinguish:

- direct feature-request planning under `.github/skills/feature-request/SKILL.md`, including new FR creation and amendment of an existing FR;
- Chaplain Plan at `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml:20-35`, reached from `.chaplain/config/watcher-pipeline-v2.yaml:225-240`;
- direct and Chaplain Enforce, including capability YAML creation, requirement declaration, test marking, and FR update; the current Chaplain prompt can introduce `REQ-YG-XXX` while implementing and updating the FR (`.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml:34-56`);
- direct human/operator editor or shell writes on each development device; and
- the importable legacy `scripts/id_registry.py` API as a bypass to remove, not as a live caller to migrate.

Move `scripts/validate_id_registry.py` out of the allocator table and describe it only as legacy validation evidence. Record the committed search result that no current code calls `reserve_ids()`/`save_registry()`; do not claim a caller migration when there is no caller. Define “allocation declaration” as a newly minted concrete ID placed in an owning FR or capability record, distinct from an adapter, test, changelog, or document merely referring to an already committed ID. Replace the impossible “before any CAP/REQ string is written” claim with the exact allocation-declaration guarantee.

### R-2: Make the allocation wrapper own the complete write execution

Replace the arm-and-exit contract with a wrapper-owned child execution. Define an interface equivalent to:

```text
scripts/allocate_ids.sh \
  --request-id <stable-key> \
  --fr-id FR-NNN \
  --cap-count N \
  --req-count M \
  --manifest <path-to-write-manifest> \
  -- <writer-command>
```

The manifest must map each target repository-relative path to the exact concrete CAP/REQ IDs it may introduce. The wrapper calls the implemented FR-975 protocol, confirms the remote reservation commit, creates a fresh unpredictable token and sentinel containing the token, request key, reservation commit, allowed path/ID mapping, creation time, expiry, and remaining allowed writes, exports the token and sentinel path only to the child writer, and removes the sentinel on every exit/signal. The wrapper must reject absolute/out-of-repository targets, duplicate paths, IDs not present in the confirmed reservation, empty requests, malformed manifests, an already-running conflicting grant, and a child that exits without consuming the declared grant.

No design in which `allocate_ids.sh` exits and leaves a globally usable sentinel for a later unrelated session is authorized. Plan and Enforce may first produce a non-governed temporary draft containing `CAP-TBD`/`REQ-YG-TBD`, derive counts and targets, reserve, and then launch the concrete-ID writer inside this envelope.

### R-3: Specify identifier-aware PreToolUse enforcement completely

Extend the FR-767 guard without weakening it. Govern both new and existing `capabilities/CAP-*.yaml` and `feature-requests/FR-*.md` writes. Define the concrete ID grammar, placeholder treatment, ownership check, and the difference between introducing a reserved allocation and referring to an ID already committed on the canonical branch.

Enumerate `create_file`, `replace_string_in_file`, `multi_replace_string_in_file`, `apply_patch`, `run_in_terminal`, and `send_to_terminal`, plus terminal redirection, heredoc, `tee`, `cp`, `mv`, `rsync`, `install`, in-place editing, and generated-script shapes. A proposed write that introduces a concrete uncommitted allocation must match the active token, reservation commit, target path, and exact allowed ID set. Wrong IDs, wrong paths, expired grants, token mismatch, cross-session use, replay beyond the manifest, malformed hook input, and an unparseable write shape touching an allocation-bearing path must deny and audit rather than fail open.

Do not block ordinary references to already committed IDs or edits that introduce no concrete allocation. If the PreToolUse payload cannot prove that fact, deny the ambiguous agent write and route it through the wrapper.

### R-4: Add a human/operator commit-and-merge backstop

Add a deterministic reservation validator, with no LLM calls, that compares concrete CAP/REQ allocations newly introduced by a staged diff or PR diff against the canonical remote ledger. It must require the ledger reservation to contain the exact ID, owner FR, and request key; reject missing, mismatched, duplicated, malformed, unreachable, or ambiguous ledger state; and never create or mutate a reservation.

Wire the validator into local pre-commit and a required CI path that runs for markdown-only FR changes as well as capability/code changes. The current CI's `!**/*.md` filter means adding only a unit test is insufficient (`.github/workflows/workflow.yml:17-31`). Tests must prove that a human-created unreserved FR allocation and an unreserved capability allocation both fail before commit/merge, while a confirmed matching reservation passes. State honestly that repository tooling cannot prevent arbitrary text from entering an editor buffer; the enforceable guarantee is reservation before compliant writes plus rejection of every bypass before commit and merge.

### R-5: Wire Plan, Enforce, and Chaplain as two-stage callers

For each R-1 route, define a two-stage flow: draft/count/manifest without concrete IDs, then FR-975 reservation, then concrete write under R-2's child-scoped grant. Persist the caller-supplied `request_id` before the remote call so retries reuse it. For Chaplain, derive the key deterministically from a stable topic/run identity, phase (`plan` or `enforce`), and additive-allocation ordinal; a retry of one logical request must not mint a new key.

Additive Enforce allocations must use a new ordinal and request key while retaining the same owner FR. Remote, authentication, malformed-ledger, policy, timeout, ambiguous-push, and retry-exhaustion outcomes from FR-975 must abort the route before concrete identifiers are substituted. No scan-only, local-registry, placeholder-to-guessed-number, or “continue and validate later” fallback is permitted.

Any material modification to `.chaplain/graphs/**/graph.yaml` or `prompts/*.yaml` required by this wiring must follow the graph-authoring sole route (`.github/copilot-instructions.md:13`). Judge, review, and graph-authoring adapters remain consumers of committed input and receive no allocation call.

### R-6: Retire the legacy allocator by removal or hard failure, not metadata

Replace “`status: retired` (or file-level equivalent)” with one exact executable outcome. FR-466 defines `status: retired` for capability YAML, not arbitrary Python modules or the legacy registry (`feature-requests/FR-466-cap-retirement-support.md:9-15,27-40`). The `FR-465/466` citation is also ambiguous because this repository contains two different `FR-465-*` files; cite FR-466 precisely.

After FR-975 has imported the legacy floor and a canonical ledger exists, first land the route migration, then in a separate purge commit remove `scripts/id_registry.py`, `scripts/validate_id_registry.py`, `tests/unit/test_id_registry.py`, and the `validate-id-registry` pre-commit entry. Preserve `.chaplain/id-registry.yaml` only as clearly marked immutable historical/bootstrap evidence if FR-975 documentation requires it; otherwise remove it too. A repository-wide test/search must prove no import, command, hook, prompt, or documentation instruction can still invoke the local allocator. Leaving callable `reserve_ids()`/`save_registry()` behavior behind while calling it “retired” is not authorized because it preserves the silent bypass this FR exists to close.

### R-7: Repair the research and dependency gates

Amend `FR-980.research.md` to state the actual boundary of each solution class. In particular, correct the claim that local pre-commit alone covers CI or human writes, state that PreToolUse governs Copilot tools rather than arbitrary editors, and compare at least: route-specific protocol calls, child-scoped PreToolUse grants, local pre-commit plus required CI validation, OS/file-permission denial, and validation-only subtraction. Preserve the graph/no-graph answer and dissent. Disposition the selected combined design rather than presenting the PreToolUse guard as if it alone covered the human surface.

Change the dependency from FR-975 “authority activation” to FR-975 revisions folded, judgement human-approved, implementation complete, tests green, and canonical ledger bootstrap available. FR-975's own judgement grants no implementation authority before its revisions and human approval (`feature-requests/FR-975-id-ledger-reservation-protocol.judgement.md:103-114`); FR-980 cannot call a merely authorized but nonexistent protocol.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-980-id-ledger-route-enforcement.md` and `feature-requests/FR-980.research.md`: fold R-1 through R-7, correct the inventory/claims/prior art, and record implementation decisions. |
| D-2 | `scripts/allocate_ids.sh` plus a typed manifest model under `scripts/`: FR-975 invocation and child-scoped exact path/ID grant; no allocation algorithm duplication. |
| D-3 | `.github/hooks/scripts/pre-command-guard.sh`, `.github/hooks/README.md`, and focused hook tests: identifier-aware, fail-closed PreToolUse enforcement without weakening FR-767. |
| D-4 | A deterministic reservation-proof validator under `scripts/`, its unit/integration tests, `.pre-commit-config.yaml`, and the minimal required `.github/workflows/workflow.yml` job/step that also runs for markdown-only allocation diffs. |
| D-5 | Direct Plan/Enforce workflow documentation and the exact Chaplain Plan/Enforce pipeline surfaces identified by R-1, with stable request-key persistence and route tests. |
| D-6 | Legacy allocator purge: `scripts/id_registry.py`, `scripts/validate_id_registry.py`, `tests/unit/test_id_registry.py`, the old pre-commit entry, and `.chaplain/id-registry.yaml` only as specified by R-6. |
| D-7 | Deterministic boundary tests proving `.github/skills/judge-fr/adapters/`, `.github/skills/review-pr/adapters/`, and `.github/skills/graph-authoring/adapters/` contain no allocation dependency and remain unchanged. |
| D-8 | One FR-975-reserved capability/requirement record for mandatory ID-route enforcement, with every new test carrying the assigned requirement marker. |
| D-9 | One FR-980 changelog fragment under `changelog/unreleased/` and one FR-980 metacognitive entry under `docs/diary/` containing a `Seed:`. |

Not authorized: changes to `scripts/id_ledger.py` or FR-975's reservation semantics; any allocation, commit, or push by judge/review/graph-authoring adapters; any modification under `.github/skills/judge-fr/adapters/`, `.github/skills/review-pr/adapters/`, or `.github/skills/graph-authoring/adapters/`; weakening or conditional execution of `scripts/validate_capabilities.py::validate_registry()`; FR-number allocation; renaming the two validators as adjacent cleanup; a new service, daemon, hosted allocator, or dependency; force push; caller-feature-branch mutation by allocation tooling; a global sentinel; a hook bypass; graph/prompt changes beyond the named Chaplain route wiring; or production ledger mutation by tests.

## Revised acceptance criteria

- [ ] AC-01: The FR inventory names every R-1 entry event, executable path, count source, stable request key, mandatory route or denial boundary, and direct test; `scripts/validate_id_registry.py` is not represented as an allocator.
- [ ] AC-02: `scripts/allocate_ids.sh` validates a typed exact path/ID manifest, obtains and confirms an FR-975 reservation, exports a fresh token only to its child writer, and removes the grant on success, failure, signal, expiry, or unconsumed-manifest exit.
- [ ] AC-03: Hook tests cover all R-3 file and terminal tool shapes and prove denial for no grant, wrong ID, wrong path, existing-FR allocation, expired grant, token mismatch, cross-session use, replay, malformed input, and ambiguous writes; an exact confirmed path/ID grant succeeds.
- [ ] AC-04: Tests distinguish a newly minted allocation from a reference to an ID already committed on the canonical branch, allowing the latter without treating adapters, tests, changelogs, or documentation as allocators.
- [ ] AC-05: A deterministic local pre-commit witness rejects unreserved FR and capability allocations and accepts an exact owner/request/ID ledger match; unreachable or malformed ledger state fails closed.
- [ ] AC-06: A required CI witness runs for markdown-only and capability/code diffs and rejects the same unreserved fixtures before merge; the validator performs no remote mutation.
- [ ] AC-07: Plan and Enforce tests prove a temporary placeholder draft is counted, reserved, and substituted only after remote confirmation; every FR-975 typed failure leaves governed files without newly minted concrete IDs.
- [ ] AC-08: A real disposable bare-remote integration test runs at least two separate route callers from different R-1 classes against one ledger tip and asserts distinct committed IDs, exact manifest writes, one reservation per stable request key, and no local-registry fallback.
- [ ] AC-09: Chaplain retry tests prove one logical Plan or Enforce request reuses its persisted idempotency key, while a later additive allocation for the same FR uses the next stable ordinal and a new key.
- [ ] AC-10: Static/import boundary tests prove judge, review, and graph-authoring adapters make no allocation import or call and remain byte-for-byte unchanged; no LLM-backed adapter execution is required for this assertion.
- [ ] AC-11: After a canonical ledger bootstrap witness, the legacy allocator/validator and pre-commit entry are purged in a separate commit; repository-wide search finds no remaining invocation path, and any preserved legacy YAML is immutable evidence rather than executable state.
- [ ] AC-12: `scripts/validate_capabilities.py::validate_registry()` and its tests remain unchanged and green; reservation or route success never bypasses duplicate validation.
- [ ] AC-13: Hook, CI, prompt/graph, and legacy-purge changes are separated into reviewable commits, and every enforcement-infrastructure commit is explicitly flagged for human review.
- [ ] AC-14: The implementation's new capability and requirements are allocated through the completed FR-975 protocol; all new tests carry those exact requirement markers.
- [ ] AC-15: The FR-980 changelog fragment exists, and the FR-980 diary entry records the boundary mismatch and contains a `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-975 R-1 through R-6 must be folded, its judgement human-approved, its implementation and real-remote tests complete, and the canonical ledger bootstrap available before FR-980 route enforcement begins. | GATE |
| C-2 | This draft grants no authority until R-1 through R-7 are folded into the committed FR/research record and a human approves this judgement. | GATE |
| C-3 | No route may return or write a newly minted concrete ID before the exact request-key reservation is confirmed on the canonical remote ledger; every failure is loud and has no scan/local fallback. | GATE |
| C-4 | PreToolUse grants are unpredictable, child-scoped, path-and-ID exact, expiring, replay-bounded, and cleaned on every exit; no global or arm-and-exit sentinel is permitted. | GATE |
| C-5 | Direct editor/operator bypasses are blocked by deterministic local commit and required merge-boundary validation, including markdown-only FR diffs; advisory-only validation does not satisfy this condition. | GATE |
| C-6 | Judge, review, and graph-authoring adapters remain advisory and byte-for-byte unchanged; they consume committed IDs and never allocate, commit, or push. | GATE |
| C-7 | Real disposable bare remotes and separate processes are mandatory for route-to-ledger contention and bootstrap witnesses; mocked subprocesses alone cannot satisfy AC-08. | GATE |
| C-8 | `scripts/validate_capabilities.py::validate_registry()` remains an independent, unconditional commit-boundary backstop and is not weakened or modified. | GATE |
| C-9 | Every hook, CI, prompt/graph, or other instruction-boundary change is isolated for explicit human review; material graph/prompt edits use the graph-authoring sole route. | GATE |
| C-10 | Legacy local allocation is removed only after successful ledger bootstrap and route migration, but no callable retired allocator may remain afterward. | GATE |
| C-11 | Tests use disposable remotes and must never create, update, or delete the production `refs/heads/id-ledger`. | GATE |
| C-12 | The authorized guarantee is exact: compliant routes reserve before writing, and bypasses cannot commit or merge unreserved allocations; the FR must not claim repository tooling can prevent arbitrary text from entering an external editor buffer. | GATE |

Authority granted: after R-1 through R-7 are folded, C-1 and C-2 are satisfied, and the advisory draft is human-approved, implementation may proceed only for D-1 through D-9 under C-1 through C-12.
