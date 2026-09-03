# Feature Request: Isolated Git Remote-Ref Compare-and-Swap for CAP/REQ Reservation (Successor A to FR-970)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-09-03
**First consumer / first event:** the next allocator (any of the 3
development devices or chaplain automation) that needs a new `CAP-XXX` or
`REQ-YG-XXX` id after this lands — the first event is that allocation
returning a unique id even when a second allocator races it concurrently
from a stale local clone.
**Research:** [FR-975.research.md](FR-975.research.md) (5 personas: os-infra-primitivist, data-process-planner, yamlgraph-native-planner, subtractionist, librarian)
**Prior art:** [FR-970](FR-970-load-bearing-atomic-id-allocation.md) / [FR-970.judgement](FR-970-load-bearing-atomic-id-allocation.judgement.md) — direct predecessor; SPLIT, this FR is exactly its Successor A (R-1), scoped to the reservation primitive alone, with the corrected incident labels (FR-692/FR-700, not "FR-692/693"), the required `## Ideal Result` section, and the feasibility gaps (named ref, isolated commit construction, real concurrency witness, typed failure table) it found missing. [FR-823](FR-823-hosted-declarative-graph-runner.md) — matched on "ledger"/"reservation" vocabulary only; its prepaid-reservation-ledger concept is a billing primitive for a rejected hosted-runner proposal, unrelated to CAP/REQ id allocation; no disposition needed beyond noting the vocabulary coincidence. [FR-180](FR-180-plan-phase-id-reservation.md) — the direct ancestor; its `scripts/id_registry.py` (confirmed present, functional, pure local read-modify-write with no git operation) is reused as-is for the Pydantic reservation model; this FR adds the git-ledger boundary FR-180 never had. [FR-754](FR-754-id-registry-chaplain-path-leak.md) — flagged that `yamlgraph/utils/id_registry.py` (a *different*, non-existent path) was hardcoded into the shipped package; the actual module lives at `scripts/id_registry.py` and is process tooling, not shipped package code — FR-754's concern does not apply to the module this FR extends.

## Summary

Add an isolated, append-only git ref (`refs/heads/id-ledger`) as the
compare-and-swap boundary for CAP/REQ allocation: an allocator fetches the
ledger tip, constructs a commit incrementing `next_cap`/`next_req` and
appending a `Reservation` (reusing FR-180's existing Pydantic model),
and pushes to the ledger ref only — never the allocator's own branch,
worktree, or index. A non-fast-forward push (another allocator won the
race) triggers fetch-and-retry. `validate_registry()` (FR-701) remains
the unmodified commit-boundary backstop.

## Value Statement

Any allocator on any of the 3 development devices, or chaplain automation,
gets a collision-free CAP/REQ id using only the git remote every allocator
already reaches to file an FR — no new server, no daemon, no requirement
that any other device be online at the same moment.

## Problem

See the committed brief for full incident history:
[research-briefs/id-ledger-reservation-protocol.md](research-briefs/id-ledger-reservation-protocol.md).
In summary: `scripts/id_registry.py` (FR-180) computes reservations
correctly but purely locally — `reserve_ids()`/`save_registry()` perform no
fetch, no remote comparison, and no push. Two allocators calling it from
stale clones collide identically to the plain file-scan approach it
replaced, and the registry file itself has been stale since 2026-04-19
because nothing forces its use. FR-701's `validate_registry()` gate
catches the collision only after both allocators have already pushed,
requiring a manual renumber (FR-692/FR-700, FR-081).

## Ideal Result

Any allocator, on any device, at any time it can reach the git remote,
receives a `Reservation` with concrete, globally unique `CAP-XXX`/
`REQ-YG-XXX` ids after a single function call — with automatic retry if
another allocator raced it — and never touches its own working branch,
worktree, or index while doing so. No collision is possible in principle
(not merely detected after the fact), because the remote's ordinary
non-fast-forward push rejection is the only enforcement mechanism, and it
requires no new infrastructure beyond the git remote already in use. The
minimal path to this: extend FR-180's existing, already-correct Pydantic
model with a git-ledger-ref boundary around its two mutating calls,
nothing else.

## Proposed Solution

### 1. Dedicated ledger ref, not a working branch

`refs/heads/id-ledger` holds a linear, append-only history. Each commit's
tree contains exactly one file, `id-ledger.yaml`, structurally identical to
FR-180's existing `IdRegistry` model (`next_cap`, `next_req`, `reserved:
list[Reservation]`) — the Pydantic model in `scripts/id_registry.py` is
reused unchanged.

### 2. Isolated commit construction (no working-tree/index contact)

`yamlgraph/utils/id_ledger.py` (new module; distinct from the nonexistent
path FR-754 flagged) implements allocation using git plumbing
(`git hash-object`, `git mktree`, `git commit-tree`, `git push`) against a
bare or side clone of the ledger ref only:

```python
def allocate(fr_id: str, cap_count: int = 0, req_count: int = 0) -> Reservation:
    """Fetch refs/heads/id-ledger, reserve ids, push, retry on rejection.

    Never reads or writes the caller's HEAD, working tree, or index.
    Raises a typed LedgerError subclass on any non-retryable failure;
    never falls back to unprotected local allocation.
    """
```

Sequence per attempt: `git fetch origin refs/heads/id-ledger` into a
detached, path-scoped temp ref -> load `id-ledger.yaml` at that tip ->
`reserve_ids()` (FR-180's existing function, unchanged) -> serialize with
`save_registry()` (unchanged) -> `git hash-object -w` the new
`id-ledger.yaml` -> `git mktree` a single-file tree -> `git commit-tree`
with the fetched tip as parent -> `git push origin <new-commit>:refs/heads/id-ledger`
(plain fast-forward push — **not** `--force-with-lease`, which is a
rebase-overwrite primitive and would risk clobbering a legitimately
concurrent reservation rather than being rejected by it; ordinary
non-force push is the correct compare-and-swap here, since it fails
closed on non-fast-forward exactly when a race occurred).

### 3. Typed failure outcomes (no silent fallback)

```python
class LedgerError(Exception): ...
class LedgerUnreachable(LedgerError): ...      # offline / DNS / connect timeout
class LedgerAuthRejected(LedgerError): ...      # credential/auth failure
class LedgerPolicyRejected(LedgerError): ...    # branch-protection / push rule
class LedgerMalformed(LedgerError): ...         # id-ledger.yaml fails Pydantic validation
class LedgerRetryExhausted(LedgerError): ...    # N non-fast-forward rejections
class LedgerAmbiguousPush(LedgerError): ...     # network dropped after push; re-fetch to check before retrying
```

Every path raises one of these or returns a `Reservation`; none silently
returns unprotected local ids.

### 4. Retry bound

Bounded exponential backoff, default 5 attempts. Termination is honest:
each round has exactly one winner (git's ref update is atomic), so the
*count* of concurrent allocators bounds the number of rounds any one
allocator needs, not a blanket guarantee of success — `LedgerRetryExhausted`
is raised and surfaced loudly past the bound, never swallowed.

## Alternatives Considered

(from FR-975.research.md; all five personas' verdicts preserved)

- **`.git/index.lock`-style local file-creation atomicity**
  (carried over from FR-970's research, re-surfaced by os-infra-primitivist
  here as the ledger-ref variant, `pursue`) — superseded: local index
  locking cannot serialize across 3 independent devices; the dedicated
  remote ref does the same job at the correct scope.
- **Commit-trailer declaration + pre-commit hook** (from FR-970's research,
  not re-selected here) — rejected again: a trailer is per-commit metadata
  on the allocator's own branch, which the FR-970 judgement's C-3 forbids
  touching; the trailer approach cannot avoid touching the caller's branch
  the way an isolated ledger-ref commit can.
- **`git push --force-with-lease`** (librarian, `pursue`, but with a flaw
  this FR does not adopt as proposed) — force-with-lease is a
  rebase/overwrite primitive: it succeeds by replacing what it expected to
  find, which is the wrong semantics for an append-only ledger where a
  concurrent legitimate reservation must be preserved, not overwritten.
  Ordinary non-force, fast-forward-only push is adopted instead; it fails
  closed exactly when force-with-lease would otherwise risk clobbering a
  valid concurrent commit.
- **Delete the requirement, rely solely on `validate_registry()`**
  (subtractionist, `dissent`) — explicitly rejected, consistent with the
  FR-970 judgement's own finding that this cost assessment is unsupported
  by the recorded incident count (FR-692/FR-700, FR-693/FR-700, FR-081).

## Acceptance Criteria

- [ ] AC-01: `yamlgraph/utils/id_ledger.py::allocate()` implements the
      isolated fetch/reserve/push/retry sequence above; unit tests cover
      each `LedgerError` subclass via fault injection
- [ ] AC-02: A test proves `allocate()` never modifies the caller's
      current branch, HEAD, working tree, or index (git status diff
      before/after is empty on all paths except the temp/detached refs
      used internally)
- [ ] AC-03: An integration test starts a real local bare git remote,
      runs 2+ concurrent `allocate()` calls from the same ledger tip in
      separate processes, and asserts distinct CAP/REQ ids and one linear
      ledger history with no lost reservation
- [ ] AC-04: Fault-injection tests cover non-fast-forward retry-and-recover,
      retry exhaustion, malformed ledger, and simulated offline/auth
      rejection, each raising its typed `LedgerError`
- [ ] AC-05: `scripts/validate_capabilities.py::validate_registry()` is
      untouched and its existing tests remain green
- [ ] AC-06: `refs/heads/id-ledger` is documented (this FR + a short
      `reference/` note) as append-only infrastructure, excluded from
      normal branch listing/cleanup tooling (`scripts/worktree.sh` must
      not treat it as a feature branch)
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary entry in `docs/diary/`

## Related

- FR-970, FR-970.judgement — predecessor and governing SPLIT verdict this
  FR discharges (R-1, C-1 through C-8 as applicable to the primitive alone)
- FR-180 — `scripts/id_registry.py`'s Pydantic model, reused unchanged
- FR-701 — `validate_registry()` backstop, unmodified
- FR-980 (Successor B, to be filed) — allocator inventory + mandatory
  route enforcement, depends on this FR's judged contract per FR-970's D-2
- Scripture: `constraint_over_code`, `one_session_one_repo`,
  `detection_without_enforcement`
