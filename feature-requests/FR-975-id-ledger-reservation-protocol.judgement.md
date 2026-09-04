# Judgement: FR-975 Isolated Git Remote-Ref Compare-and-Swap for CAP/REQ Reservation

**Prior art:** see FR-975's own Prior Art field (FR-970, FR-180, FR-701, FR-754, FR-823, FR-469) — this judgement reviews and dispositions those same citations; no additional prior art beyond what FR-975 already names.

**Verdict:** APPROVED WITH REVISIONS — the dedicated-ref reservation primitive is the correct narrowly scoped successor, but authority activates only after the FR defines a safe bootstrap/corpus floor, idempotent ledger schema, process-tooling boundary, deterministic recovery contract, and mechanically complete tests, and this draft receives human review.

**Reviewed against:** `feature-requests/FR-975-id-ledger-reservation-protocol.md`; `feature-requests/FR-975.research.md`; `feature-requests/research-briefs/id-ledger-reservation-protocol.md`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.md`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md`; `feature-requests/FR-180-plan-phase-id-reservation.md`; `feature-requests/FR-701-capability-registry-consistency-gate.md`; `feature-requests/FR-754-id-registry-chaplain-path-leak.md`; `feature-requests/FR-823-hosted-declarative-graph-runner.md` lines 1-120; `feature-requests/FR-469-fr-number-allocation-gate.md` lines 1-130; `feature-requests/TEMPLATE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `pyproject.toml` lines 1-180; `.chaplain/id-registry.yaml`; `scripts/id_registry.py`; `scripts/validate_capabilities.py`; `scripts/worktree.sh`; `tests/unit/test_id_registry.py` lines 1-190; committed filename/content inventory matching `capabilities/CAP-*.yaml`.

## What is sound

The problem is real and the proposed serialization boundary is directionally correct. The current helper only increments in-memory counters and appends a local reservation (`scripts/id_registry.py:68-105`), while the committed registry remains at `next_cap: 94` and `next_req: 246` (`.chaplain/id-registry.yaml:11-23`). FR-701 records a concrete concurrent CAP-195/REQ-YG-531 collision and the absence of a preventive boundary (`feature-requests/FR-701-capability-registry-consistency-gate.md:17-31`). A dedicated remote ref with non-force fast-forward pushes gives competing compliant writers one linear winner without adding a server or daemon (`feature-requests/FR-975-id-ledger-reservation-protocol.md:18-25,88-98`).

The FR also obeys the predecessor's most important structural ruling. It isolates the reservation primitive from allocator-adoption enforcement, keeps adapters out of scope, preserves `validate_registry()` as an independent backstop, names `refs/heads/id-ledger`, and requires a real bare-remote contention witness (`feature-requests/FR-975-id-ledger-reservation-protocol.md:18-25,159-167,177-182`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md:28-48,84-94,101-108`). The retry text no longer promises starvation-free completion; it explicitly admits bounded exhaustion (`feature-requests/FR-975-id-ledger-reservation-protocol.md:115-121`).

Against the eight criteria:

1. **Scope:** the reservation protocol is one concern and is smaller than FR-970's combined protocol-plus-enforcement plan. Documentation and tests are direct witnesses, not orthogonal features. Adapter, hook, and route adoption remain outside this FR (`feature-requests/FR-975-id-ledger-reservation-protocol.md:177-182`).
2. **Consistency:** the core fetch/construct/push/retry sequence is coherent, but "reuse unchanged" conflicts with the predecessor's required versioned, idempotent entry and typed invalid-request outcome (`feature-requests/FR-975-id-ledger-reservation-protocol.md:65-69,79-113`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md:32-40`). The package location and global-uniqueness claims also require correction under R-2 and R-5.
3. **Measurability:** the real bare-remote race, linear-history, no-lost-reservation, and untouched-validator checks are strong starting witnesses (`feature-requests/FR-975-id-ledger-reservation-protocol.md:159-167`). AC-02 and AC-06 are not yet sufficient because `git status` does not by itself prove ref/HEAD/index identity and a `refs/heads/*` ref necessarily appears in ordinary Git branch listings (`feature-requests/FR-975-id-ledger-reservation-protocol.md:155-171`).
4. **Feasibility:** Git plumbing and Pydantic are already available, and ordinary non-force push is sufficient for the compliant-writer race. Feasibility is not complete until the FR defines first-ref creation, a floor above the live remote corpus, commit identity, remote selection, command timeouts, and ambiguous-success recovery. The legacy model's constants and counters are far below the current corpus (`scripts/id_registry.py:19-40`; `.chaplain/id-registry.yaml:11-23`).
5. **Architecture alignment:** this is repository process tooling, not a shipped YAMLGraph utility. FR-754 deliberately moved the registry helper to `scripts/` and prohibited a new public `yamlgraph.utils` surface (`feature-requests/FR-754-id-registry-chaplain-path-leak.md:25-45,58-73`); packaging excludes `scripts*` but includes `yamlgraph` (`pyproject.toml:170-172`). The proposed `yamlgraph/utils/id_ledger.py` would reverse that boundary while depending on a script-only model (`feature-requests/FR-975-id-ledger-reservation-protocol.md:14,68-76`).
6. **Single responsibility:** the FR now contains only the primitive. Live-route adoption correctly remains FR-980, and no further split is required (`feature-requests/FR-975-id-ledger-reservation-protocol.md:181-182`).
7. **Strategic classification:** this is repository process infrastructure with named consumers on three development devices plus chaplain automation, not a YAMLGraph framework primitive or an example (`feature-requests/FR-975-id-ledger-reservation-protocol.md:8-12,27-32`). It has sufficient recurring use to justify code rather than pattern documentation, but its eventual load-bearing adoption belongs to FR-980.
8. **Testability:** direct failing tests can be derived for contention, bootstrap, idempotency, isolation, malformed state, bounded retries, and ambiguous push recovery. They cannot be complete from the current criteria because the request key, initial ledger state, remote/default-branch contract, and exact recovery state machine are absent.

The research gate is present and committed, preserves dissent, and answers `is_this_a_graph` (`feature-requests/FR-975.research.md:1-20`). Its substance is not yet enough for authority: three entries are packaging variants of the same dedicated-ref solution, the predecessor-required per-ID-ref and server-side classes are absent, and the FR's alternatives omit the research record's graph proposal while adding alternatives not produced by that record (`feature-requests/FR-975.research.md:16-20`; `feature-requests/FR-975-id-ledger-reservation-protocol.md:123-148`; `feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md:50-61`).

## Required revisions

### R-1: Define a ledger-specific, idempotent schema and request contract

Replace the claim that FR-180's models are reused unchanged. Keep `scripts/id_registry.py` unchanged and define strict ledger-specific Pydantic models with:

- a ledger schema version;
- monotonically increasing `next_cap` and `next_req`;
- an ordered reservation list whose entries contain `request_id`, owner `fr_id`, CAP IDs, REQ IDs, UTC timestamp, and parent ledger commit;
- rejection of unknown fields, malformed IDs, booleans/non-integer counts, negative counts, and requests whose CAP and REQ counts are both zero;
- a typed `LedgerInvalidRequest` outcome for every invalid request; and
- append-only, non-reuse semantics for abandoned or unused reservations.

Make `request_id` a required caller-supplied idempotency key. A repeated key with the same owner and counts returns the existing reservation without creating a commit; reuse with different inputs raises `LedgerInvalidRequest`. State explicitly that a later additive reservation for the same FR uses a new request key.

### R-2: Keep the primitive in process tooling and isolate the complete Git environment

Change the implementation surface from `yamlgraph/utils/id_ledger.py` to `scripts/id_ledger.py`; do not add a package re-export or make shipped `yamlgraph` import `scripts`. Define the callable's repository/remote input explicitly, including how the push URL and canonical default branch are resolved.

Perform every fetch, object write, temporary ref update, tree creation, and commit in a newly initialized temporary bare repository with its own `GIT_DIR`. Reading the caller repository's configured remote URL is permitted; reading or mutating its HEAD, worktree, index, object database, refs, or branch is not. Specify exact fetch and push refspecs, non-force push, `--porcelain` output where machine-readable status exists, per-command timeouts, and explicit author/committer identity so `git commit-tree` does not depend on ambient user configuration.

### R-3: Define bootstrap and the live-corpus allocation floor

Specify the missing-ref state machine. On first use, fetch the canonical remote default branch into the isolated bare repository, compute CAP/REQ maxima from its committed capability corpus, combine those maxima with any imported legacy registry counters/reservations, create a versioned root ledger, and attempt ordinary creation of `refs/heads/id-ledger`. If another initializer wins, fetch its ledger and continue through the normal retry path.

Until FR-980 makes all allocators use this primitive, compute every candidate floor from both the fetched canonical ledger and the current canonical remote corpus, as required by the predecessor (`feature-requests/FR-970-load-bearing-atomic-id-allocation.judgement.md:32-40`). Never seed from the caller's stale checkout. Define malformed, missing-file, counter-regression, duplicate-request, non-prefix reservation history, and ledger-behind-corpus outcomes. A ledger behind the corpus advances above the corpus maximum without reusing or editing prior reservations.

### R-4: Complete the push-result and failure state machine

For a definite non-fast-forward result, discard the candidate, fetch the new tip, preserve the same request key, recompute, and retry. For a transport failure after push begins, re-fetch and search by `request_id`: return the exact committed reservation if present; raise `LedgerInvalidRequest` if the key exists with different inputs; retry only when absence is proven; raise `LedgerAmbiguousPush` when the remote cannot be queried before the bounded recovery limit.

Add a deterministic command/status-to-exception table for unreachable remote, authentication rejection, remote policy rejection, malformed ledger, invalid request, non-fast-forward exhaustion, timeout, and otherwise unclassified Git failure. Do not classify failures solely by locale-dependent stderr substrings, and retain command, exit status, and sanitized stdout/stderr on the typed exception. No path may return locally computed IDs before their reservation commit is confirmed on the remote ref.

### R-5: Narrow the guarantee and repair the research/prior-art disposition

Change the first-consumer, Value Statement, and Ideal Result to claim uniqueness among protocol callers and against IDs committed on the canonical remote branch. State that repository-wide mandatory use and the stronger "every allocator" guarantee activate only after FR-980 is judged and enforced; this primitive alone cannot prevent an unmodified allocator on another feature branch from bypassing the ledger.

Revise `FR-975.research.md` into four to six genuinely distinct solution classes, including dedicated ledger-ref CAS, atomic per-ID refs and CAP+REQ multi-ref atomicity, server-side allocation, validation-only subtraction, and route enforcement independent of storage. Preserve the graph/no-graph disagreement and disposition the graph proposal explicitly. Add FR-469 to prior art as the separate FR-number allocation/gate precedent. Correct the force-with-lease discussion: an exact expected-value lease is a valid CAS, but ordinary non-force push is selected because the candidate commit already descends from the fetched tip and ancestry must remain linear; do not claim that an exact lease can overwrite a ref changed by a concurrent writer.

### R-6: Replace partial criteria with end-to-end mechanical witnesses

Fold the revised acceptance criteria below into the FR. Replace the impossible promise that `refs/heads/id-ledger` is excluded from ordinary Git branch listing with the precise claim that repository-specific worktree creation and cleanup never select it. Do not modify `scripts/worktree.sh` if its existing ref filters already satisfy that test.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/id_ledger.py`: ledger-specific Pydantic models, isolated bare-repository Git operations, bootstrap, allocation, retry, recovery, and typed failures. |
| D-2 | `tests/unit/test_id_ledger.py`: request/schema, failure mapping, idempotency, bootstrap, caller-isolation, and real local bare-remote contention witnesses. |
| D-3 | `reference/id-ledger.md`: canonical ref, schema, initialization, append-only/non-reuse rule, recovery behavior, guarantees, and operational inspection. |
| D-4 | `feature-requests/FR-975-id-ledger-reservation-protocol.md` and `feature-requests/FR-975.research.md`: fold R-1 through R-6 and record implementation status after enforcement. |
| D-5 | One FR-975 changelog fragment under `changelog/unreleased/`. |
| D-6 | One FR-975 metacognitive entry under `docs/diary/`. |

Not authorized: any file under `yamlgraph/`; changes to `scripts/id_registry.py`, `.chaplain/id-registry.yaml`, `scripts/validate_capabilities.py`, `scripts/worktree.sh` unless a revised criterion proves its existing filters insufficient, `.github/skills/`, `.github/hooks/`, `.github/workflows/`, graph or prompt artifacts, judge/review behavior, branch-protection configuration, FR-number allocation, allocator-route adoption, or FR-980 implementation. Tests must not create or mutate `origin`'s production `refs/heads/id-ledger`.

## Revised acceptance criteria

- [ ] AC-01: Strict ledger models reject every invalid schema/request case in R-1 and preserve a round-trip containing schema version, request key, owner, CAP/REQ IDs, UTC timestamp, and parent commit.
- [ ] AC-02: A missing-ledger integration test uses a real local bare remote, derives its floor from the remote default branch plus the legacy floor, creates exactly one root ledger under two concurrent initializers, and allocates no existing CAP/REQ ID.
- [ ] AC-03: A real local bare-remote integration test starts at least two separate allocator processes from the same ledger tip and asserts distinct IDs, one reservation per request key, one linear commit history, and no lost reservation.
- [ ] AC-04: Repeating an accepted request key with identical inputs returns the original reservation without advancing the ref; repeating it with changed owner or counts raises `LedgerInvalidRequest`.
- [ ] AC-05: Fault-injection and real-remote tests cover definite non-fast-forward recovery, exhaustion, malformed/missing ledger content, counter regression, ledger-behind-corpus repair, offline remote, authentication rejection, policy rejection, timeout, and unclassified Git failure, each producing its specified typed exception and never returning uncommitted IDs.
- [ ] AC-06: An ambiguous-post-acceptance test suppresses the successful push response, then proves re-fetch-by-request-key returns the one committed reservation without a duplicate commit; an unqueryable remote reaches `LedgerAmbiguousPush`.
- [ ] AC-07: Success and every failure path preserve the caller's symbolic HEAD, HEAD commit, local refs, index bytes/state, tracked and untracked worktree content, and configured push branch; all temporary objects and refs exist only in the disposable bare repository.
- [ ] AC-08: Every ledger commit has exactly one tree entry named `id-ledger.yaml`, descends from the fetched ledger tip except the root, appends exactly one new reservation on allocation, and is pushed without any force option to exactly `refs/heads/id-ledger`.
- [ ] AC-09: `scripts/validate_capabilities.py` and its tests remain unchanged and green; reservation success does not bypass or suppress `validate_registry()`.
- [ ] AC-10: A targeted test proves every `scripts/worktree.sh` listing, GC, and removal path ignores `refs/heads/id-ledger`; no `scripts/worktree.sh` edit is made when the current implementation already passes.
- [ ] AC-11: `reference/id-ledger.md` documents the protocol's pre-FR-980 guarantee honestly, including that universal allocator adoption is outside FR-975.
- [ ] AC-12: Targeted tests pass with requirement markers, the FR-975 changelog fragment exists, and the FR-975 diary entry contains a `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | This draft grants no authority until R-1 through R-6 are folded into the committed FR and research record and a human approves the judgement. | GATE |
| C-2 | The implementation remains repository process tooling under `scripts/`; no shipped `yamlgraph` module may depend on repository allocation infrastructure. | GATE |
| C-3 | All Git mutation occurs in a disposable isolated bare repository and targets only `refs/heads/id-ledger`; the caller's branch, worktree, index, refs, and object database are read-only. | GATE |
| C-4 | No force push, force-with-lease push, caller-feature-branch push, local-only allocation, or silent fallback is permitted. | GATE |
| C-5 | No ID is returned until the exact request-key reservation is confirmed on the remote ledger; ambiguous outcomes reconcile before retry or fail loudly. | GATE |
| C-6 | Real local bare remotes and concurrent processes are mandatory witnesses; mocked subprocesses alone cannot satisfy bootstrap, contention, or ambiguous-success criteria. | GATE |
| C-7 | `validate_registry()` remains an independent commit-boundary backstop and is not weakened, skipped, or made conditional on ledger success. | GATE |
| C-8 | Judge, review, graph-authoring, hooks, CI, branch policy, and allocator adoption remain untouched; any such enforcement-infrastructure change requires a separate judged scope and human review. | GATE |
| C-9 | Repository-wide collision-prevention claims are forbidden until FR-980 makes every inventoried allocator use the protocol or fail before writing identifiers. | GATE |
| C-10 | Production remote-ref creation or mutation is not a test side effect; enforcement tests use disposable local remotes, and the first live operation requires explicit human review because it creates automated commit/push infrastructure. | GATE |

Authority granted: after R-1 through R-6 are folded and this advisory draft is human-approved, implementation may proceed only for D-1 through D-6 under C-1 through C-10.
