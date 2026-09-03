# Feature Request: Isolated Git Remote-Ref Compare-and-Swap for CAP/REQ Reservation (Successor A to FR-970)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-03). Revisions R-1..R-6 folded below. Authority remains inactive pending human review of the judgement (C-1).
**Effort:** 2 days
**Requested:** 2026-09-03
**First consumer / first event:** the next allocator (any of the 3
development devices or chaplain automation) that calls this protocol
directly for a new `CAP-XXX`/`REQ-YG-XXX` id after this lands — the
guarantee is uniqueness among protocol callers and against IDs already
committed on the canonical remote branch, not yet a repository-wide
guarantee (that activates only after FR-980 is judged and enforced).
**Research:** [FR-975.research.md](FR-975.research.md) (5 personas: os-infra-primitivist, data-process-planner, yamlgraph-native-planner, subtractionist, librarian; addendum below folds R-5's reclassification)
**Prior art:** [FR-970](FR-970-load-bearing-atomic-id-allocation.md) / [FR-970.judgement](FR-970-load-bearing-atomic-id-allocation.judgement.md) — direct predecessor; SPLIT, this FR is exactly its Successor A (R-1), with corrected incident labels (FR-692/FR-700, not "FR-692/693"). [FR-180](FR-180-plan-phase-id-reservation.md) — `scripts/id_registry.py` stays unmodified; this FR defines its own ledger-specific schema rather than reusing FR-180's model unchanged (R-1 correction). [FR-701](FR-701-capability-registry-consistency-gate.md) — `validate_registry()` backstop, unmodified (C-7). [FR-754](FR-754-id-registry-chaplain-path-leak.md) — moved id-allocation tooling to `scripts/`, prohibited a new public `yamlgraph.utils` surface; this FR's implementation path is corrected to `scripts/id_ledger.py` accordingly (R-2). [FR-823](FR-823-hosted-declarative-graph-runner.md) — vocabulary coincidence only ("ledger"/"reservation" describe a billing primitive for a rejected hosted-runner proposal); no further disposition needed. [FR-469](FR-469-fr-number-allocation-gate.md) — separate FR-*number* allocation/gate precedent, out of this FR's CAP/REQ-only scope; added per judgement R-5.

## Summary

Add an isolated, append-only git ref (`refs/heads/id-ledger`) as the
compare-and-swap boundary for CAP/REQ allocation, implemented as
repository process tooling (`scripts/id_ledger.py`, not shipped
`yamlgraph`). An allocator fetches the ledger tip into a disposable
isolated bare repository, constructs a commit appending one idempotent
reservation, and pushes to the ledger ref only — never the allocator's
own branch, worktree, index, or object database. A non-fast-forward push
(another allocator won the race) triggers fetch-and-retry, keyed by a
caller-supplied idempotency key. `validate_registry()` (FR-701) remains
the unmodified commit-boundary backstop.

## Value Statement

Any allocator that calls this protocol directly, on any of the 3
development devices or via chaplain automation, gets a collision-free
CAP/REQ id using only the git remote every allocator already reaches to
file an FR — no new server, no daemon, no requirement that any other
device be online at the same moment. Repository-wide guarantees require
FR-980 (route enforcement) in addition to this primitive.

## Problem

See the committed brief for full incident history:
[research-briefs/id-ledger-reservation-protocol.md](research-briefs/id-ledger-reservation-protocol.md).
In summary: `scripts/id_registry.py` (FR-180) computes reservations
correctly but purely locally — `reserve_ids()`/`save_registry()`
(`scripts/id_registry.py:68-105`) perform no fetch, no remote comparison,
and no push. Two allocators calling it from stale clones collide
identically to the plain file-scan approach it replaced, and the registry
file itself has been stale since 2026-04-19 (`next_cap: 94`, `next_req:
246`, `.chaplain/id-registry.yaml:11-23`) while the live corpus is past
CAP-170/REQ-YG-580, because nothing forces its use. FR-701's
`validate_registry()` gate catches the collision only after both
allocators have already pushed, requiring a manual renumber (FR-692/
FR-700, FR-081).

## Ideal Result

Any allocator that calls this protocol directly, on any device, at any
time it can reach the git remote, receives a reservation with concrete
CAP/REQ ids that are unique among protocol callers and against every id
already committed on the canonical remote branch — with automatic,
idempotent retry if another allocator raced it — and never touches its
own working branch, worktree, index, or object database while doing so.
Collision among protocol callers is impossible in principle (not merely
detected after the fact), because the remote's ordinary non-fast-forward
push rejection is the only enforcement mechanism, requiring no new
infrastructure beyond the git remote already in use. This primitive alone
cannot stop an allocator that bypasses the protocol entirely (e.g. a
direct file edit on a feature branch) — that repository-wide guarantee is
FR-980's scope, gated on this FR's judged contract.

## Proposed Solution

### 1. Dedicated ledger ref, isolated repository tooling

`refs/heads/id-ledger` holds a linear, append-only history. Each commit's
tree contains exactly one file, `id-ledger.yaml`. The implementation lives
at **`scripts/id_ledger.py`** (process tooling, not a shipped `yamlgraph`
module — `scripts/id_registry.py` and `scripts/validate_capabilities.py`
stay exactly where FR-754 placed them; packaging excludes `scripts*`).
`scripts/id_registry.py` is not modified or reused unchanged; this FR
defines its own ledger-specific Pydantic models (R-1, below) because the
ledger needs an idempotency key and parent-commit linkage FR-180's model
never had.

### 2. Ledger-specific schema (R-1)

```python
class LedgerReservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str            # caller-supplied idempotency key
    fr_id: str
    cap: list[int] = Field(default_factory=list)
    req: list[int] = Field(default_factory=list)
    timestamp: datetime         # UTC
    parent_commit: str          # ledger commit this reservation extends

class IdLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = 1
    next_cap: int
    next_req: int
    reserved: list[LedgerReservation] = Field(default_factory=list)
```

Rejected at validation: unknown fields, malformed/negative/non-integer
counts, and a request whose `cap` and `req` counts are both zero
(`LedgerInvalidRequest`). A repeated `request_id` with identical owner and
counts returns the existing reservation without a new commit (idempotent
replay); a repeated `request_id` with different owner/counts raises
`LedgerInvalidRequest`. Abandoned or unused reservations are never reused
or edited — a later additive request for the same FR uses a new
`request_id`.

### 3. Isolated bare-repository git operations (R-2)

Every fetch, object write, temporary ref, tree, and commit happens inside
a newly initialized temporary bare repository with its own `GIT_DIR`.
Reading the caller's configured remote push URL is permitted; reading or
mutating the caller's HEAD, worktree, index, object database, refs, or
branch is not. Fetch and push refspecs are explicit
(`refs/heads/id-ledger:refs/heads/id-ledger`), push is never forced,
`--porcelain` is used wherever machine-readable status exists, every
subprocess has a bounded timeout, and author/committer identity is set
explicitly on `git commit-tree` (never relies on ambient git config).

### 4. Bootstrap and allocation floor (R-3)

On first use (no `refs/heads/id-ledger` on the remote): fetch the
canonical default branch into the isolated bare repository, compute
CAP/REQ maxima from its committed capability corpus, combine those maxima
with the legacy `.chaplain/id-registry.yaml` counters/reservations if
present, construct a versioned root ledger, and attempt ordinary creation
of `refs/heads/id-ledger`. If a concurrent initializer wins, fetch its
ledger and continue through the normal retry path below. Until FR-980
makes every allocator use this primitive, every candidate floor is
computed from both the fetched ledger tip and the current canonical
remote corpus (never from the caller's possibly-stale local checkout) —
a ledger found behind the live corpus advances above the corpus maximum
without editing or reusing prior reservations.

### 5. Allocation, retry, and recovery (R-4)

Sequence per attempt: fetch `refs/heads/id-ledger` -> load and validate
`id-ledger.yaml` at that tip -> apply the requested reservation (schema
above) -> `git hash-object -w` -> `git mktree` (single-file tree) ->
`git commit-tree` (fetched tip as parent, explicit identity) ->
`git push origin <new-commit>:refs/heads/id-ledger` (plain, non-force —
**not** `--force-with-lease`; see the addendum below on why an exact-lease
CAS is valid in principle but the wrong tool here since the candidate
commit already descends from the fetched tip and ancestry must stay
linear, not overwritten).

- **Definite non-fast-forward:** discard the candidate, re-fetch, keep the
  same `request_id`, recompute, retry (bounded, default 5 attempts,
  exponential backoff). `LedgerRetryExhausted` past the bound.
- **Transport failure after push begins (ambiguous outcome):** re-fetch
  and search the ledger by `request_id`. If found, return that exact
  committed reservation (no duplicate commit). If the key exists with
  different inputs, raise `LedgerInvalidRequest`. If genuinely absent,
  retry. If the remote cannot be queried within the bounded recovery
  window, raise `LedgerAmbiguousPush` — never silently return a locally
  computed, unconfirmed id.

Typed, non-silent failures for every path:

```python
class LedgerError(Exception): ...
class LedgerUnreachable(LedgerError): ...       # offline / DNS / connect timeout
class LedgerAuthRejected(LedgerError): ...      # credential/auth failure
class LedgerPolicyRejected(LedgerError): ...    # branch-protection / push rule
class LedgerMalformed(LedgerError): ...         # id-ledger.yaml fails validation
class LedgerInvalidRequest(LedgerError): ...    # schema/idempotency-key conflict
class LedgerRetryExhausted(LedgerError): ...    # N definite non-fast-forward rejections
class LedgerAmbiguousPush(LedgerError): ...     # unqueryable remote after a push attempt
```

Classification never relies solely on locale-dependent stderr substrings;
each typed exception retains the failing command, exit status, and
sanitized stdout/stderr. No ID is ever returned before its reservation
commit is confirmed on the remote ledger ref.

## Alternatives Considered

(from FR-975.research.md, reclassified per judgement R-5 — see the
addendum in the research file for the four-to-six distinct solution
classes and the preserved graph/no-graph disagreement)

- **Dedicated ledger-ref CAS** (adopted) — the four convergent findings
  (os-infra-primitivist, data-process-planner, yamlgraph-native-planner,
  librarian) are packaging variants of this one solution class; this FR
  is the process-tooling variant (R-2), not the graph-pipeline variant.
- **Graph-pipeline variant** (yamlgraph-native-planner, `pursue`,
  explicitly dispositioned, not adopted) — modeling fetch/reserve/push as
  a YAMLGraph pipeline was considered; rejected because the primitive is
  called synchronously from arbitrary tooling contexts (adapters, CLI,
  chaplain) that must not depend on graph compilation to allocate an id,
  and because R-2 requires this to stay outside `yamlgraph/` package
  boundaries entirely.
- **Atomic per-ID refs / multi-ref atomicity for CAP+REQ bundles** — a
  distinct class from single-ledger CAS, not previously disambiguated;
  rejected as unnecessary complexity: a single linear ledger ref already
  gives one canonical ordering for both CAP and REQ counters together,
  and per-ID refs would need a second cross-ref atomicity mechanism to
  bundle a CAP+REQ request, solving a problem the single-ledger design
  doesn't have.
- **Server-side allocation** (e.g. a GitHub Issues-style number-minting
  API) — a distinct class; rejected per this FR's own constraint of no
  new externally-hosted coordination service, and per FR-970's precedent
  that the position is git-native tooling, not a hosted dependency.
- **`git push --force-with-lease`** (librarian, `pursue`, adopted in
  spirit, not literally) — force-with-lease is a valid exact-expected-value
  compare-and-swap in principle, but it is designed to *overwrite* a ref
  at a known prior state (rebase workflows); this ledger's candidate
  commit already descends from the fetched tip via ordinary ancestry, so
  a plain non-force push gives the identical CAS guarantee (reject on
  mismatch) without the overwrite semantics force-with-lease implies —
  the corrected framing per judgement R-5.
- **Delete the requirement, rely solely on `validate_registry()`**
  (subtractionist, `dissent`) — explicitly rejected, consistent with the
  FR-970 judgement's finding that this cost assessment is unsupported by
  the recorded incident count (FR-692/FR-700, FR-693/FR-700, FR-081).
- **Commit-trailer declaration + pre-commit hook** (from FR-970's research,
  not re-selected) — rejected: a trailer lives on the allocator's own
  branch, which R-2's caller-isolation requirement forbids touching.

## Acceptance Criteria

- [ ] AC-01: Strict ledger models reject every invalid schema/request case
      (R-1); round-trip preserves schema version, request key, owner,
      CAP/REQ IDs, UTC timestamp, and parent commit
- [ ] AC-02: A missing-ledger integration test (real local bare remote)
      derives its floor from the remote default branch plus the legacy
      floor, creates exactly one root ledger under two concurrent
      initializers, and allocates no existing CAP/REQ ID
- [ ] AC-03: A real local bare-remote integration test starts 2+ separate
      allocator processes from the same ledger tip and asserts distinct
      IDs, one reservation per request key, one linear commit history,
      no lost reservation
- [ ] AC-04: Repeating an accepted request key with identical inputs
      returns the original reservation without advancing the ref;
      repeating with changed owner/counts raises `LedgerInvalidRequest`
- [ ] AC-05: Fault-injection and real-remote tests cover non-fast-forward
      recovery, retry exhaustion, malformed/missing ledger, counter
      regression, ledger-behind-corpus repair, offline remote, auth
      rejection, policy rejection, timeout, unclassified git failure —
      each raising its specified typed exception, never returning
      uncommitted IDs
- [ ] AC-06: An ambiguous-post-acceptance test suppresses the successful
      push response, then proves re-fetch-by-request-key returns the
      one committed reservation without a duplicate commit; an
      unqueryable remote reaches `LedgerAmbiguousPush`
- [ ] AC-07: Success and every failure path preserve the caller's
      symbolic HEAD, HEAD commit, local refs, index, tracked/untracked
      worktree content, and configured push branch; all temporary
      objects/refs exist only in the disposable bare repository
- [ ] AC-08: Every ledger commit has exactly one tree entry
      (`id-ledger.yaml`), descends from the fetched tip except the root,
      appends exactly one new reservation, and is pushed without any
      force option to exactly `refs/heads/id-ledger`
- [ ] AC-09: `scripts/validate_capabilities.py` and its tests remain
      unchanged and green; reservation success never bypasses or
      suppresses `validate_registry()`
- [ ] AC-10: A targeted test proves every `scripts/worktree.sh` listing,
      GC, and removal path ignores `refs/heads/id-ledger`; no
      `scripts/worktree.sh` edit is made if its existing filters already
      pass
- [ ] AC-11: `reference/id-ledger.md` documents the protocol's
      pre-FR-980 guarantee honestly, including that universal allocator
      adoption is outside this FR's scope
- [ ] AC-12: Tests carry requirement markers; changelog fragment exists;
      diary entry contains a `Seed:`

## Related

- FR-970, FR-970.judgement — predecessor and governing SPLIT verdict this
  FR discharges (R-1 there)
- FR-180 — `scripts/id_registry.py`, unmodified; not reused by this FR's
  ledger schema (corrected per R-1 here)
- FR-701 — `validate_registry()` backstop, unmodified (C-7, C-9)
- FR-754 — process-tooling boundary this FR's implementation path
  corrects to (R-2, C-2)
- FR-469 — separate FR-number allocation/gate precedent, out of scope
- FR-980 (Successor B, to be filed) — allocator inventory + mandatory
  route enforcement, depends on this FR's judged contract
- Scripture: `constraint_over_code`, `one_session_one_repo`,
  `detection_without_enforcement`
