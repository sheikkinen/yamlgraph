# Feature Request: Allocator Inventory and Mandatory Route Enforcement for CAP/REQ Reservation (Successor B to FR-970)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-03). Revisions R-1..R-7 folded below. Authority remains inactive pending FR-975's own revisions being folded, human-approved, implemented, tested, and its canonical ledger bootstrapped (C-1), plus human review of this judgement (C-2).
**Effort:** 3 days
**Requested:** 2026-09-03
**First consumer / first event:** the next CAP/REQ allocation attempt
through a compliant route (direct FR authoring, Chaplain Plan/Enforce) on
any of the 3 development devices — the guarantee is that a compliant route
either returns a committed FR-975 reservation before writing a concrete
id, or aborts; bypassing the route entirely (e.g. hand-typing an id in an
editor outside any governed tool call) cannot be prevented at the point of
typing, only rejected before commit/merge (see Ideal Result).
**Research:** [FR-980.research.md](FR-980.research.md) (5 personas: os-infra-primitivist, data-process-planner, yamlgraph-native-planner, subtractionist, librarian; addendum below folds R-7's boundary corrections)
**Prior art:** [FR-970](FR-970-load-bearing-atomic-id-allocation.md) / [FR-970.judgement](FR-970-load-bearing-atomic-id-allocation.judgement.md) — direct predecessor; SPLIT, this FR is exactly its Successor B (R-2), depending on Successor A's judged contract (D-2). [FR-975](FR-975-id-ledger-reservation-protocol.md) / [FR-975.judgement](FR-975-id-ledger-reservation-protocol.judgement.md) — Successor A; judged APPROVED WITH REVISIONS, authority not yet activated. This FR's dependency on FR-975 is corrected (R-7) to require FR-975's revisions folded, judgement human-approved, implementation complete with green real-remote tests, and its canonical ledger bootstrapped — not merely "authority activated" as originally stated. [FR-180](FR-180-plan-phase-id-reservation.md) — `scripts/id_registry.py`/`.chaplain/id-registry.yaml`, the advisory-mechanism precedent this FR retires (R-6). [FR-701](FR-701-capability-registry-consistency-gate.md) — `validate_registry()` backstop, unmodified (C-8). [FR-767](FR-767-graph-authoring-sole-route.md) — the PreToolUse guard pattern this FR extends, corrected (R-3) to be honest about its actual boundary (Copilot tool calls only, not arbitrary editors). [FR-466](FR-466-cap-retirement-support.md) — defines `status: retired` for capability YAML specifically; corrected citation (R-6) — this FR's legacy purge is executable removal, not a `status:` field on Python modules. Filename-noun matches from the research gate (FR-902, FR-596, FR-823, FR-824, FR-862) remain coincidental vocabulary overlaps in unrelated domains — no further disposition needed.

## Summary

Make FR-975's reservation protocol mandatory at every point CAP/REQ ids
are actually allocated (direct FR authoring, Chaplain Plan, Chaplain
Enforce), using a child-scoped grant (not a global sentinel) for the
agent-tool surface, plus a deterministic commit-and-merge validator as the
honest backstop for the surface no in-process guard can reach: an
operator typing directly into an editor outside any governed tool call.
Legacy local allocation (`scripts/id_registry.py`) is removed, not merely
labeled retired. Judge, review, and graph-authoring adapters remain
byte-for-byte unchanged and allocate nothing.

## Value Statement

The collision class witnessed four times (FR-692/FR-700, FR-693/FR-700,
FR-081, FR-180's own registry decaying unused) becomes structurally
unavailable for every compliant route, and every bypass is rejected before
it can be committed or merged — a guarantee this FR states honestly
(compliant-route prevention + bypass rejection at commit/merge), not the
impossible claim that any tool can intercept an arbitrary keystroke in an
external editor.

## Problem

**The corrected inventory** (R-1 — allocator class, entry event,
executable path, where counts become known, `request_id` source, mandatory
call, denial boundary):

| Allocator class | Entry event | Executable path | Count source | Request-id source | Denial boundary |
|---|---|---|---|---|---|
| Direct FR authoring (human/agent) | New FR filed or an existing FR amended to add a capability/requirement | `.github/skills/feature-request/SKILL.md` workflow; no code today, a text edit | Author infers from FR scope at Plan time | FR id + amendment ordinal | PreToolUse grant (R-2/R-3) for the write; commit/merge validator (R-4) as backstop |
| Chaplain Plan | Autonomous plan generation for an inbox topic | `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml`, reached from `.chaplain/config/watcher-pipeline-v2.yaml` | Plan prompt infers from the drafted FR | Topic/run id + `plan` phase | Two-stage caller wiring (R-5); commit/merge validator (R-4) |
| Chaplain Enforce | Autonomous implementation, including capability YAML creation, requirement declaration, test marking, FR update | `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml` | Enforce prompt infers from the frozen FR scope | Topic/run id + `enforce` phase + additive ordinal | Two-stage caller wiring (R-5); commit/merge validator (R-4) |
| Direct human/operator editor or shell write (any of 3 devices) | An operator hand-types a concrete id outside any governed tool call | No code path — cannot be intercepted at the point of typing | N/A | N/A | **Not preventable in-process; rejected only at commit/merge (R-4).** Stated honestly, not claimed as prevented. |
| Legacy `scripts/id_registry.py` API | N/A — no current caller | `reserve_ids()`/`save_registry()` (`scripts/id_registry.py:68-105`) | N/A | N/A | Removed, not migrated (R-6): repository-wide search confirms zero current callers |

`scripts/validate_id_registry.py` is explicitly **not** an allocator — it
validates `.chaplain/id-registry.yaml`'s internal consistency and writes
no identifiers. It is legacy validation evidence, retired alongside the
registry it validates (R-6), distinct from FR-701's
`scripts/validate_capabilities.py::validate_registry()`, which stays.

An "allocation declaration" in this FR means a newly minted concrete id
placed into an owning FR or capability record — distinct from a test,
adapter, changelog, or document merely *referring to* an id already
committed on the canonical branch. No mechanism in this FR blocks the
latter.

## Ideal Result

Every compliant route (direct FR authoring, Chaplain Plan, Chaplain
Enforce) either returns a FR-975-committed reservation before writing a
concrete CAP/REQ id, or aborts loudly with no scan/local fallback. No
tool-call surface can introduce a concrete, uncommitted allocation without
matching an active, child-scoped, exact path/id grant. Separately, and
honestly stated as a distinct guarantee: repository tooling cannot prevent
arbitrary text from entering an external editor buffer outside any
governed tool call — but no such bypass can be committed or merged,
because a deterministic, no-LLM validator rejects any staged or PR diff
that introduces a concrete CAP/REQ id not present in a matching, confirmed
canonical-ledger reservation. Judge, review, and graph-authoring adapters
remain unchanged, consuming only ids already committed by the time they
run. Legacy local allocation no longer exists as callable code.

## Proposed Solution

### 1. Corrected inventory (R-1)

See the Problem table above — the committed artifact this FR's tests are
written against.

### 2. Wrapper-owned child execution, not arm-and-exit (R-2)

```text
scripts/allocate_ids.sh \
  --request-id <stable-key> \
  --fr-id FR-NNN \
  --cap-count N \
  --req-count M \
  --manifest <path-to-write-manifest> \
  -- <writer-command>
```

The manifest maps each target repository-relative path to the exact
concrete CAP/REQ ids it may introduce. The wrapper: calls FR-975's
(by-then-implemented) protocol; confirms the remote reservation commit;
creates a fresh, unpredictable token and a sentinel containing the token,
request key, reservation commit, allowed path/id mapping, creation time,
expiry, and remaining allowed writes; exports the token and sentinel path
**only to the child writer it launches** (mirroring `scripts/author.sh`'s
proven token-scoping shape — `scripts/author.sh:61-89`); and removes the
sentinel on every exit, signal, or unconsumed-manifest condition. Rejected
at the wrapper boundary: absolute/out-of-repository targets, duplicate
paths, ids not present in the confirmed reservation, empty requests,
malformed manifests, an already-running conflicting grant, and a child
that exits without consuming the declared grant. No design leaves a
globally usable sentinel for a later, unrelated session.

### 3. Honest PreToolUse boundary (R-3)

The guard governs Copilot `PreToolUse` tool calls only — `create_file`,
`replace_string_in_file`, `multi_replace_string_in_file`, `apply_patch`,
`run_in_terminal`, `send_to_terminal` (including redirection, heredoc,
`tee`, `cp`, `mv`, `rsync`, `install`, in-place editing, generated-script
shapes) — targeting `capabilities/CAP-*.yaml` (new or existing) and
`feature-requests/FR-*.md` (new or existing). It explicitly does **not**
and cannot intercept an operator's direct edit in an external editor
outside a Copilot tool call — that surface's only enforcement is R-4.
A write introducing a concrete, uncommitted allocation must match the
active token, reservation commit, target path, and exact allowed id set;
wrong ids, wrong paths, expired grants, token mismatch, cross-session use,
replay beyond the manifest, malformed hook input, or an unparseable write
shape touching an allocation-bearing path deny and audit — fail closed,
never fail open. Ordinary references to already-committed ids, or edits
introducing no concrete allocation, are not blocked; if the PreToolUse
payload cannot prove that distinction, the ambiguous write is denied and
routed through the wrapper.

### 4. Deterministic commit/merge backstop (R-4)

A no-LLM validator compares concrete CAP/REQ allocations newly introduced
by a staged diff (pre-commit) or PR diff (CI) against the canonical
remote ledger: it requires the ledger reservation to contain the exact
id, owner FR, and request key; rejects missing, mismatched, duplicated,
malformed, unreachable, or ambiguous ledger state; and never creates or
mutates a reservation itself. Wired into local pre-commit **and** a
required CI path that also runs for markdown-only FR diffs (today's CI
treats all-markdown changes as docs-only and skips registry checks —
that filter is widened for this validator specifically, not removed
generally). This is the honest enforcement point for the direct-editor
surface R-3 cannot reach.

### 5. Two-stage callers for Plan/Enforce/Chaplain (R-5)

Each R-1 compliant route: draft with placeholder ids (`CAP-TBD`/
`REQ-YG-TBD`) -> count and target-manifest derivation -> FR-975
reservation via the wrapper -> concrete-id write under the child-scoped
grant. The caller-supplied `request_id` is persisted *before* the remote
call so retries reuse it — for Chaplain, derived deterministically from
topic/run identity + phase (`plan`/`enforce`) + additive-allocation
ordinal, so a retry of one logical request never mints a second key, and
a later additive allocation for the same FR uses the next ordinal and a
new key. Any FR-975 typed failure (offline, auth, malformed ledger,
policy, timeout, ambiguous push, retry exhaustion) aborts the route before
any concrete id is substituted — no scan-only or placeholder-to-guessed-
number fallback. Any material change this wiring requires in
`.chaplain/graphs/**/graph.yaml` or `prompts/*.yaml` follows the
graph-authoring sole route.

### 6. Legacy retirement by removal (R-6)

After FR-975's ledger bootstrap has imported the legacy floor: land the
route migration first, then in a **separate purge commit** remove
`scripts/id_registry.py`, `scripts/validate_id_registry.py`,
`tests/unit/test_id_registry.py`, and the corresponding pre-commit entry.
`.chaplain/id-registry.yaml` is removed unless FR-975's own documentation
requires preserving it as clearly marked immutable historical/bootstrap
evidence. A repository-wide search proves no import, command, hook,
prompt, or documentation instruction can still invoke the local allocator.
`status: retired` (FR-466) applies only to capability YAML, not to Python
modules or the legacy registry file — those are deleted, not labeled.

### 7. Enforcement-infrastructure review discipline

Hook, CI, prompt/graph, and legacy-purge changes land in separate,
reviewable commits; every enforcement-infrastructure commit is explicitly
flagged for human review before merge (FR-970 C-6/C-8, Scripture
`instruction_boundary_uncrossed`).

## Alternatives Considered

(from FR-980.research.md, corrected per judgement R-7 — see the addendum
for the honest boundary comparison)

- **Pre-commit hook alone intercepting capability-file/ARCHITECTURE.md
  writes** (os-infra-primitivist, `pursue`) — not sufficient alone: a
  pre-commit hook fires only at commit time and cannot prevent an agent
  tool call from writing an unreserved id in the first place; adopted
  instead as one half of a combined design (PreToolUse for the tool-call
  surface, R-4's commit/merge validator for everything else), corrected
  from the original framing that treated it as a full solution.
- **Corpus-census discover-extract-map-reduce pattern with FR-892 tool
  slots** (yamlgraph-native-planner, `pursue`) — the corrected R-1
  inventory is exactly this census's output, done directly; a full census
  graph remains unnecessary machinery for a five-row, manually-verifiable,
  now file-and-line-cited table.
- **LedgerDB-style git-native optimistic-concurrency document store**
  (librarian, `pursue`) — FR-975 already is this pattern for this
  repository's specific need; adopting a third-party library would
  reintroduce an external dependency FR-970's position rejects.
- **Delete the judge/review advisory-only constraint** (subtractionist,
  `dissent`) — explicitly rejected: contradicts FR-970's binding
  judgement (R-2/C-2) and would reintroduce allocation-by-side-effect.
  Correctly answered instead by two-stage callers (R-5): reservations
  happen during Plan/Enforce; judge/review only ever read.

## Acceptance Criteria

- [ ] AC-01: The FR inventory (table above) names every entry event,
      executable path, count source, stable request key, mandatory
      route/denial boundary, and direct test; `validate_id_registry.py`
      is not represented as an allocator
- [ ] AC-02: `scripts/allocate_ids.sh` validates a typed exact path/id
      manifest, obtains and confirms an FR-975 reservation, exports a
      fresh token only to its child writer, and removes the grant on
      success, failure, signal, expiry, or unconsumed-manifest exit
- [ ] AC-03: Hook tests cover every R-3 tool/terminal shape and prove
      denial for no grant, wrong id, wrong path, existing-FR allocation,
      expired grant, token mismatch, cross-session use, replay, malformed
      input, and ambiguous writes; an exact confirmed path/id grant
      succeeds
- [ ] AC-04: Tests distinguish a newly minted allocation from a reference
      to an already-committed id, allowing the latter without treating
      adapters, tests, changelogs, or documentation as allocators
- [ ] AC-05: A deterministic local pre-commit witness rejects unreserved
      FR/capability allocations and accepts an exact owner/request/id
      ledger match; unreachable or malformed ledger state fails closed
- [ ] AC-06: A required CI witness runs for markdown-only and
      capability/code diffs and rejects the same unreserved fixtures
      before merge; the validator performs no remote mutation
- [ ] AC-07: Plan/Enforce tests prove a placeholder draft is counted,
      reserved, and substituted only after remote confirmation; every
      FR-975 typed failure leaves governed files without newly minted ids
- [ ] AC-08: A real disposable bare-remote integration test runs 2+
      route callers from different inventory classes against one ledger
      tip and asserts distinct committed ids, exact manifest writes, one
      reservation per stable request key, no local-registry fallback
- [ ] AC-09: Chaplain retry tests prove one logical Plan/Enforce request
      reuses its persisted idempotency key; a later additive allocation
      uses the next ordinal and a new key
- [ ] AC-10: Static/import boundary tests prove judge, review, and
      graph-authoring adapters make no allocation import/call and remain
      byte-for-byte unchanged
- [ ] AC-11: After a canonical ledger bootstrap witness, the legacy
      allocator/validator and pre-commit entry are purged in a separate
      commit; repository-wide search finds no remaining invocation path
- [ ] AC-12: `scripts/validate_capabilities.py::validate_registry()` and
      its tests remain unchanged and green; no bypass of duplicate
      validation
- [ ] AC-13: Hook, CI, prompt/graph, and legacy-purge changes are
      separated into reviewable commits, each explicitly flagged for
      human review
- [ ] AC-14: New capabilities/requirements this FR itself adds are
      allocated through the completed FR-975 protocol; all new tests
      carry those exact requirement markers
- [ ] Changelog fragment in `changelog/unreleased/`
- [ ] Diary entry containing a `Seed:` in `docs/diary/`

## Related

- FR-970, FR-970.judgement — predecessor and governing SPLIT verdict this
  FR discharges (R-2 there)
- FR-975, FR-975.judgement — Successor A; this FR's authority is gated on
  FR-975's revisions, human approval, implementation, and ledger bootstrap
  (corrected dependency, R-7)
- FR-180 — the advisory-registry failure mode this FR closes by removal
- FR-701 — `validate_registry()` backstop, unmodified
- FR-767 — the PreToolUse pattern this FR extends, boundary corrected
- FR-466 — `status: retired` scope (capability YAML only; corrected
  citation, this FR's Python/registry purge is deletion, not labeling)
- Scripture: `detection_without_enforcement`, `instruction_boundary_uncrossed`,
  `constraint_over_code`, `gate_checks_shape_not_substance`
