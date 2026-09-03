# Judgement: FR-970 Load-Bearing Atomic ID Allocation for CAP/REQ

**Verdict:** SPLIT - the collision problem is real, but the proposal bundles an atomic reservation protocol with mandatory route enforcement, and the proposed judge integration violates the judge adapter's no-auto-commit boundary; each concern must re-enter as a separately researched and judged FR.

**Reviewed against:** `feature-requests/FR-970-load-bearing-atomic-id-allocation.md`; `feature-requests/FR-970.research.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `.github/skills/feature-request/SKILL.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/graph-authoring/SKILL.md`; `.github/skills/graph-authoring/adapters/graph.yaml`; `.github/skills/judge-fr/adapters/graph.yaml`; `feature-requests/FR-180-plan-phase-id-reservation.md`; `feature-requests/FR-701-capability-registry-consistency-gate.md`; `feature-requests/FR-692-world-pressure-agent.md`; `feature-requests/FR-693-event-revision-latent-closure.md`; `feature-requests/FR-731-webllm-browser-prompt-demo-spike.md`; `feature-requests/FR-081-copilot-node.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-767-graph-authoring-sole-route.judgement.md`; `feature-requests/FR-469-fr-number-allocation-gate.md`; `feature-requests/FR-728-session-safe-release-commit-hygiene.md`; `feature-requests/FR-192-draconian-changelog-release-gate.md`; `feature-requests/FR-823-hosted-declarative-graph-runner.judgement.md`; `feature-requests/research-game-engine.md` lines 1-180; `.chaplain/id-registry.yaml`; `scripts/id_registry.py`; `scripts/validate_capabilities.py` lines 130-250; `reference/development-operations.md` lines 150-300; repository inventory of `.github/skills/*/adapters/graph.yaml` and `.github/skills/feature-request/`.

## What is sound

The underlying CAP/REQ collision is real. FR-180 already documented that two branches can reserve the same number from one base and that max-wins counters do not prevent overlap (`feature-requests/FR-180-plan-phase-id-reservation.md:128-130`). FR-701 records the concrete FR-692/FR-700 CAP-195 and REQ-YG-531 collision and the absence of a blocking uniqueness gate at the time (`feature-requests/FR-701-capability-registry-consistency-gate.md:19,27`). FR-081 separately records a REQ allocation collision (`feature-requests/FR-081-copilot-node.md:299`). The old registry is visibly stale at `next_cap: 94` and `next_req: 246` (`.chaplain/id-registry.yaml:11-14`), while its surviving implementation merely increments an in-memory counter and detects duplicate reservations after the fact (`scripts/id_registry.py:96-104,154-188`). Replacing advisory local allocation with a remote compare-and-swap boundary is therefore a legitimate direction.

Retaining duplicate validation as defense in depth is also sound. The current registry validator mechanically rejects duplicate CAP and REQ identifiers (`scripts/validate_capabilities.py:162-210`), and FR-970 correctly does not propose weakening that backstop (`feature-requests/FR-970-load-bearing-atomic-id-allocation.md:95-96,132`).

The strongest case against the current plan is structural, not stylistic:

1. **Scope and single responsibility:** the FR combines a distributed reservation protocol (`id_allocation.py`, ledger schema, fetch/commit/push/retry) with enforcement across every allocation entry point (`feature-requests/FR-970-load-bearing-atomic-id-allocation.md:66-96`). Those concerns have different failure modes, architecture surfaces, and acceptance tests. Judge doctrine says orthogonal bundles get SPLIT (`.github/skills/judge-fr/doctrine.md:49-50,75-77`).
2. **Consistency:** the claimed mandatory FR-authoring graph does not exist. The feature-request skill defines Research, Plan, Judge, and Enforce as workflow prose (`.github/skills/feature-request/SKILL.md:11-19`), while the actual graph-authoring route governs `graph.yaml` and `prompts/*.yaml` artifacts (`.github/skills/graph-authoring/SKILL.md:14-16,39-42`). FR-970 nevertheless claims every FR-authoring route already passes through graph compilation and asks to wire an `FR-authoring` adapter (`feature-requests/FR-970-load-bearing-atomic-id-allocation.md:17-20,73-75,128-129`). The repository contains graph-authoring, judge, and review adapters, but no feature-request adapter graph.
3. **Architecture alignment:** both cited adapters explicitly produce advisory, uncommitted output and must never auto-commit (`.github/skills/graph-authoring/adapters/graph.yaml:1-5`; `.github/skills/judge-fr/adapters/graph.yaml:1-5`). Making the judge append, commit, and push a ledger before rendering an advisory verdict would cross that boundary and introduce repository mutation into independent review. The judge must consume an allocation made during planning or enforcement; it must not allocate by side effect.
4. **Feasibility:** git serializes ref updates, not individual files. "Commits and pushes only that file to origin" does not identify the canonical remote ref, parent-selection protocol, isolated index/tree, push refspec, authentication/branch-protection contract, or recovery after an ambiguous network result (`feature-requests/FR-970-load-bearing-atomic-id-allocation.md:81-93`). On an allocator's current branch, a commit is a complete tree snapshot, not a file-only transaction. Without a dedicated ref and isolated commit construction, the proposal can commit unrelated work or push the wrong branch, directly engaging the shared-index risk in `one_session_one_repo` (`.github/copilot-instructions.md:156`).
5. **Liveness and error semantics:** bounded retry does not imply termination under contention. The statement that retry "terminates because exactly one push can land per parent commit" proves that each round has a winner, not that one particular allocator wins before its retry bound (`feature-requests/FR-970-load-bearing-atomic-id-allocation.md:86-89`). Retry exhaustion, offline operation, authentication failure, remote policy rejection, ambiguous success, and abandoned reservations have no typed outcomes.
6. **Measurability and testability:** a mocked rejection test can prove a branch in Python but cannot prove the physical property this FR exists to provide. The acceptance suite needs a real local bare remote and concurrent allocators starting from the same tip, with assertions over unique IDs, one canonical ledger history, clean caller worktrees/indexes, idempotent recovery, and loud bounded failure. The current fixture criterion also names the wrong pair: FR-701 records FR-692 versus FR-700 (`feature-requests/FR-701-capability-registry-consistency-gate.md:19,52`), while FR-693 says its initial band was renumbered after FR-700 claimed it (`feature-requests/FR-693-event-revision-latent-closure.md:115-117`).
7. **Research and prior art:** the linked research record contains five retrieved hits (`feature-requests/FR-970.research.md:7-12`), but FR-970 dispositions a different list (`feature-requests/FR-970-load-bearing-atomic-id-allocation.md:13`). This violates the template requirement that every retrieved hit be distinguished or dismissed (`feature-requests/TEMPLATE.md:21-25`). The research also labels local `.git/index.lock`, commit trailers, graph compilation, and ordinary append-log merging as atomic/universal without establishing a cross-device remote-ref protocol (`feature-requests/FR-970.research.md:16-20`). FR-469 is directly relevant allocation-gate precedent and is not dispositioned.
8. **Strategic classification:** the reservation protocol is repository process infrastructure, not a YAMLGraph framework primitive. The route-enforcement concern is enforcement/doctrine hardening. The current combined proposal is not eligible for a single framework classification. Each successor has real consumers, but neither may inherit authority from this draft.

The FR also omits the required `## Ideal Result` section: the repository template requires the ideal end state before deriving the proposed solution (`feature-requests/TEMPLATE.md:59-65`), while FR-970 moves directly from root cause to Proposed Solution (`feature-requests/FR-970-load-bearing-atomic-id-allocation.md:54-59`). FR-number incidents such as FR-731 are evidence for the separate FR-number problem, not for the CAP/REQ-only scope frozen here (`feature-requests/FR-731-webllm-browser-prompt-demo-spike.md:8,132`; `feature-requests/FR-469-fr-number-allocation-gate.md:9-15`).

## Required revisions

### R-1: File a reservation-protocol successor

Create a successor FR concerned only with the atomic CAP/REQ reservation primitive. It must define:

- the canonical remote ref as `refs/heads/id-ledger`;
- a versioned, Pydantic-validated ledger entry containing an idempotency key, owner FR, CAP IDs, REQ IDs, timestamp, and parent ledger commit;
- candidate computation from both the live corpus and the canonical ledger;
- isolated commit construction that never reads from or writes to the caller's working tree or index and never pushes the caller's feature branch;
- compare-and-swap semantics against the fetched ledger tip, including the exact fetch and push refspecs;
- idempotent recovery when the push may have succeeded but the client lost the response;
- typed failures for offline, authentication, remote-policy rejection, malformed ledger, non-fast-forward exhaustion, and invalid allocation counts;
- bounded retry with no false termination guarantee; and
- a real bare-remote concurrency witness, not a mocked-remote substitute.

This successor must not modify adapter graphs, skills, hooks, or judge behavior.

### R-2: File a route-enforcement successor

Create a separate successor FR that inventories every actual CAP/REQ allocator and makes the protocol from R-1 load-bearing. The inventory must name each entry event and its current executable surface: feature-request planning, enforcement, chaplain automation, and direct human/operator allocation. It must define one mandatory route or a mechanical denial at every bypassable surface, plus a test proving each listed allocator either returns a committed reservation or fails before writing CAP/REQ identifiers.

The successor must preserve the judge adapter's advisory no-auto-commit boundary. Judgement receives already-reserved identifiers as committed FR input; no judge node may commit or push. If a new feature-request authoring adapter or hook is proposed, that enforcement-infrastructure change requires human review and its own threat/failure analysis.

### R-3: Replace the research record and disposition the actual retrieved prior art

Run a new closed research pass for each successor and promote committed records that distinguish at least:

- dedicated remote-ref compare-and-swap;
- atomic creation of per-ID refs, including multi-ref atomicity for CAP+REQ bundles;
- a dedicated ledger branch using isolated commit construction;
- server-side allocation alternatives;
- validation-only subtraction; and
- route enforcement independent of allocation storage.

The records must correct the false claims that local index locking serializes devices, pre-commit is a push-time allocator, graph compilation is atomic, or ordinary append-log merging prevents collisions. Each successor's `**Prior art:**` field must disposition the exact hits printed by its linked research record, including FR-180, FR-701, FR-469, and any retrieved rejected FR. Add `## Ideal Result` before `## Proposed Solution`.

### R-4: Correct the incident and ownership contract

Restrict CAP/REQ evidence to actual CAP/REQ collisions. Replace the claimed "FR-692/693 double-allocation" fixture with the documented FR-692/FR-700 CAP-195 and REQ-YG-531 incident, and treat FR-693/FR-700 as a separate renumbering witness. Remove FR-731 and the four FR-number collisions from this scope; FR-number allocation remains FR-469 territory.

Define who requests an allocation, how CAP and REQ counts are supplied and validated, whether zero-count requests are legal, how repeated requests for one FR are idempotent or additive, and how unused reservations are represented without reuse.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Successor A: a newly researched FR for the isolated git remote-ref CAP/REQ reservation protocol described by R-1. |
| D-2 | Successor B: a newly researched FR for allocator inventory and mandatory route enforcement described by R-2, depending on Successor A's judged contract. |
| D-3 | Corrected evidence, actual retrieved-prior-art dispositions, and an Ideal Result in each successor per R-3 and R-4. |
| D-4 | FR-970 records this SPLIT disposition and links both successors; no implementation lands under FR-970. |

Not authorized under FR-970: `yamlgraph/utils/id_allocation.py`; `.chaplain/id-ledger.log`; deletion or retirement of `.chaplain/id-registry.yaml`, `scripts/id_registry.py`, or its tests; any commit, push, hook, adapter, graph, prompt, judge, review, chaplain, branch-protection, or remote-ref change; any CAP/REQ allocation; any FR-number allocation work; changelog or diary claims that the mechanism is implemented.

## Revised acceptance criteria

These criteria gate re-entry of the two successor plans; they are not implementation authority under FR-970.

- [ ] AC-01: Successor A contains a complete `refs/heads/id-ledger` compare-and-swap protocol, ledger schema, idempotency contract, isolated commit construction, and typed failure table.
- [ ] AC-02: Successor A proves that allocation does not modify the caller's branch, HEAD, working tree, or index and does not include unrelated files in the ledger commit.
- [ ] AC-03: Successor A specifies a local bare-remote integration test in which at least two allocators start from the same ledger tip and finish with distinct CAP/REQ allocations in one canonical history.
- [ ] AC-04: Successor A specifies recovery tests for non-fast-forward retry, ambiguous push success, malformed ledger, offline/auth rejection, and retry exhaustion.
- [ ] AC-05: Successor A preserves `scripts/validate_capabilities.py::validate_registry()` as an independently tested duplicate backstop.
- [ ] AC-06: Successor B lists every current allocator and maps each to one executable mandatory-allocation or deny-before-write path.
- [ ] AC-07: Successor B keeps judge and review routes advisory and free of commit/push side effects; they consume committed allocation evidence only.
- [ ] AC-08: Successor B defines mechanical bypass tests for planning, enforcement, chaplain, and direct operator surfaces.
- [ ] AC-09: Each successor has a committed substantive research record, dispositions every retrieved prior-art hit, and contains `## Ideal Result` before `## Proposed Solution`.
- [ ] AC-10: Incident fixtures cite FR-692/FR-700 and FR-693/FR-700 accurately; FR-number incidents and FR-469 implementation scope are excluded.
- [ ] AC-11: Allocation request ownership, CAP/REQ counts, repeat requests, zero-count requests, abandoned reservations, and non-reuse are mechanically specified.
- [ ] AC-12: FR-970 contains no implementation checklist presented as authorized after the SPLIT; it links the separately judged successors.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | SPLIT grants no implementation authority. Each successor must independently complete Research, Plan, Judge, and scope freeze before enforcement. | GATE |
| C-2 | The judge and review adapters must remain advisory and must never commit or push allocation state. | GATE |
| C-3 | Automated git mutation must use isolated commit construction and a dedicated ledger ref; it must not touch the caller's branch, worktree, or shared index. | GATE |
| C-4 | No silent fallback to scan-only allocation is permitted on remote, authentication, ledger, or retry failure. Fail before writing CAP/REQ identifiers. | GATE |
| C-5 | Mocked subprocess tests cannot satisfy the concurrency witness; a real local bare remote and concurrent clients are mandatory. | GATE |
| C-6 | Human review is mandatory before merging any hook, adapter, doctrine, branch-policy, or automated commit/push change because it is enforcement infrastructure. | GATE |
| C-7 | `validate_registry()` remains an independent commit-boundary backstop; reservation success must not suppress duplicate validation. | GATE |
| C-8 | Any material `graph.yaml` or `prompts/*.yaml` work in a successor follows the graph-authoring sole route; this judgement authorizes no graph edits. | GATE |

Authority granted: none. FR-970 is split into separately researched and judged reservation-protocol and route-enforcement successors; no code, ledger, graph, adapter, hook, or git-remote mutation may be implemented under this FR.
