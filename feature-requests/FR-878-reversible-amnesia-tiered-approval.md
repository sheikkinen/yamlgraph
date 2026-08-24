# Feature Request: Reversible Amnesia & Tiered Approval (amends FR-875 C-6)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-24); R-1…R-7 folded below
**Effort:** 1 day
**Requested:** 2026-08-24
**First consumer / first event:** the operator and agent at the next
curation apply — specifically the first disposition containing a `forget`
verdict, which under the current contract would demand a 57-row document
review the operator has (correctly) challenged as superficial.

**Blast radius:** machine-local. The archive shelf lives inside the memory
root, invisible to recall and excluded from collection; nothing new leaves
the machine. The export premise remains fully human-gated and out of scope.

## Summary

The operator challenged FR-875's per-run human sign-off (C-6) as
compliance theatre, and the record supports the challenge: the human
skims long agent documents (operator-preferences doctrine), neither real
catch in the FR-874/875 arc came from document review (one came from a
reframing question, one from the agent reading rows), and the
disposition's rationale column is itself a forecast — a skim on top of a
prediction validates nothing (`threshold_encodes_forecast`). This FR
replaces approval-of-irreversibility with three honest mechanisms:
**remove the irreversibility** (soft-delete archive + restore), **catch
forecast errors mechanically** (re-derivation detection), and **spend
human attention only on the residue** (tiered approval; export stays
always-human).

## Value Statement

Curation stops needing a ritual nobody performs honestly: wrong forgets
become restores instead of re-paid incidents, forecast errors surface
mechanically, and the human decides policies and exceptions instead of
skimming corpora.

## Problem

1. **The gate guards the wrong thing.** C-6 exists because apply deletes;
   deletion is the only irreversible step in the pipeline. Approving
   through irreversibility is strictly worse than removing it.
2. **Human review of a 57-row table is shape, not substance** —
   `gate_checks_shape_not_substance` with a human as the shape. The
   sign-off line cannot distinguish a read from a skim, and (per the
   deployment-gates lesson) cannot distinguish operator keystrokes from
   agent keystrokes; only provenance text does.
3. **A wrong forget is currently undetectable.** The failure mode of
   forgetting is not remembering what was forgotten; there is no error
   signal. The forecast "this will never fire again" is never validated.

## Ideal Result

Apply is transactional *and reversible*: forgotten notes move to an
archive shelf inside the memory root (invisible to recall, listed in a
tombstone index), redacted originals are stashed beside them, and one
command restores any of it. Collection warns when a new note resembles an
archived one — the mechanical "the forecast was wrong" signal, with a
restore path. Approval is tiered by residual risk: no-ops need nothing,
compress-only runs proceed under standing delegation with an audit line,
the first forget of a run asks the human one structured question, and
export-premise dispositions are always and non-delegably human.

## Proposed Solution

Amends `examples/memory-curation/apply.py` and collect; adds a restore
mode; extends the FR-877 advisory.

1. **Archive shelf (soft delete):**
   - `forget` → move note to
     `<memory_root>/.archive/<op_id>/<original-relative-path>` where
     `op_id = <UTC timestamp YYYYMMDDTHHMMSSZ>-<manifest_sha256[:8]>`
     (R-1: collision-safe across same-day repeats and repeated filenames;
     original relative path preserved under the op directory). `redact`
     → stash the original at the same layout with the op record marked
     `backup` (R-3: backups are NOT re-derivation candidates).
   - Append one row per archive/restore event to
     `<memory_root>/repo/_tombstones.md` — schema (R-1): `op_id |
     original path | verdict (forget|redact-backup) | one-line reason |
     archive path | pre-apply sha256 | post-apply sha256 (redact only) |
     manifest sha256 | disposition sha256 | restore status`.
   - **Tombstone protection (R-7):** `_tombstones.md` is collected as
     context but is never a `forget`/`redact` target — apply refuses any
     disposition row addressing it; the restore index cannot be destroyed
     by ordinary curation (test).
   - Dot-directory is invisible to the memory tool's listing and excluded
     from `collect.py` by construction (repo/*.md glob).
   - No retention purge in v1 — archive deletion is a future human act,
     not a mechanism (judgement C-4).
2. **Restore (R-2, conflict-safe):** `apply.py restore <op_id>/<path>`
   validates the tombstone/archive record, restores only to the recorded
   live path, and refuses when the live destination exists with bytes
   that are neither the expected post-apply state nor already the
   archived bytes (conflict → clear report, human action). Idempotent
   only when live bytes already equal archived bytes AND the tombstone
   records restoration; any other repeat fails visibly. Every restore
   appends its tombstone row.
3. **Tiered approval (replaces the uniform C-6 sign-off; R-4/R-5 exact):**
   | Tier | Trigger (content-computed, precedence top-down) | Requirement |
   |---|---|---|
   | 3 | `premise_kind: export_publication` in the disposition | non-delegable recorded human response artifact |
   | 2 | any `forget` verdict | recorded human response artifact naming the human, covering the forget rows |
   | 1 | any `redact`, zero forgets | sign-off line with machine-checked standing-delegation provenance: `DELEGATION: <source-ref>` where source-ref cites this FR's recorded delegation section; audit line appended to `.github/hooks/logs/memory-curation-audit.jsonl` |
   | 0 | keep-only | none (no-op) |
   - **Premise metadata (R-5):** reconcile records a validated
     `premise_kind: hygiene | export_publication` field in
     disposition.json/md, set from an explicit graph variable — never
     substring-matched from freeform premise text. Missing/unknown
     premise_kind → apply fails closed to tier 3.
   - **Standing delegation source (R-4):** the operator's recorded
     delegation for tier-1 applies is this FR's approval plus the run-2
     precedent recorded in FR-875 ("proceed — I feel this is your call",
     2026-08-24); the sign-off line must cite it as
     `DELEGATION: FR-878 tier-1 standing (operator 2026-08-24)`.
   - Hash-binding mechanics (manifest + disposition sha256, live-hash
     drift refusal, validate-all-then-apply-all, idempotence) unchanged
     at every tier — the amendment relocates *who approves*, not *what
     is verified*.
4. **Re-derivation detection (forecast validation; R-3 scoped):**
   `collect.py` compares live note filenames and content hashes against
   tombstone rows whose verdict class is `forget` ONLY — redaction
   backups never trigger it (test proves a redacted note emits no
   warning). On match it emits one advisory line — "note X resembles
   archived Y (forgotten <date>) — consider restore". Pure stdlib, zero
   LLM/network. **FR-877 dependency (R-6):** FR-878 implements this as
   collect output (its own authorized surface) with tests; if/when
   FR-877 lands, the briefing seam consumes the same line without
   changing FR-877's drift-marker semantics.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: FR revised with archive identity, tombstone schema, restore
      conflict rules, re-derivation scope, tier computation, sign-off
      provenance, export-premise metadata, FR-877 handling (R-1…R-7) —
      this document.
- [ ] AC-02: `forget` archives rather than unlinks; `redact` stashes the
      original; archive paths are op-id collision-safe and preserve
      original relative paths; `.archive/` invisible to recall and
      collect (tests, temp roots only).
- [ ] AC-03: `_tombstones.md` gains one schema-valid row per
      archive/restore event (op id, path, verdict, reason, archive path,
      pre/post hashes, manifest hash, disposition hash, restore status);
      tests validate schema.
- [ ] AC-04: restore validates the record, restores only to the recorded
      path, refuses unsafe overwrite/drift with a clear conflict report,
      idempotent only for already-restored matching bytes (tests).
- [ ] AC-05: tier computed content-based with exact precedence
      export_publication > any forget > any redact > keep-only (tests).
- [ ] AC-06: tier 1 accepts only the machine-checked `DELEGATION:` line
      and appends the audit record; tier 2 refuses without a recorded
      human response artifact; tier 3 refuses without a non-delegable
      one (tests).
- [ ] AC-07: `premise_kind` is a validated enum recorded by reconcile
      from an explicit variable; apply derives tier 3 from it only;
      missing/unknown fails closed to tier 3 (tests).
- [ ] AC-08: hash-binding, drift refusal, validate-all-then-apply-all,
      and idempotence unchanged at every tier (existing tests green).
- [ ] AC-09: re-derivation advisory fires only against `forget`
      tombstones; redaction backups never trigger it; pure stdlib
      (tests).
- [ ] AC-10: the advisory is implemented as collect output with tests
      (FR-877-independent); tombstone file is never a forget/redact
      target (test).
- [ ] AC-11: FR-875 C-6 pointer recorded; README documents
      archive/restore, tombstones, tier table, delegation provenance,
      export non-delegability.
- [ ] AC-12: tests req-tagged via CAP-247 extension; diary reflection
      records the approval-theatre trap and the correction.

## Alternatives Considered

- **Keep the uniform per-run human sign-off:** measured as theatre — the
  skim is not a review; rejected by the operator's direct challenge.
- **Fully automate apply (drop the gate):** wrong at tier 2/3 — forgets
  carry forecast risk until re-derivation detection has field history,
  and export is genuinely irreversible.
- **LLM double-judge instead of tiers:** a second model vote launders
  ambiguity into confidence (FR-726 lesson); disagreement-diff is
  useful evidence but not an approval substitute — kept as a named
  follow-up, not scope.
- **Retention-window auto-purge of the archive:** reintroduces the
  irreversibility this FR removes, to save kilobytes; rejected for v1.

## Prior art

**Prior art:** FR-875 (parent — this amends its C-6 per-run sign-off;
all other gates and mechanics inherited unchanged). FR-877 (sibling —
same briefing seam, drift advisory; this adds the re-derivation
advisory beside it). FR-874 (REJECTED — untouched: nothing here moves
data off-machine, and the export premise gains a *stricter* gate).
FR-868 (written-approval precedent — its hard gate survives at tier 3
where irreversibility survives). Scripture: `threshold_encodes_forecast`
(gate on defect class, not forecast — tiers gate on verdict class),
`gate_checks_shape_not_substance` (the challenged sign-off), the
deployment-gates ambient-credential lesson (provenance lines, and why
tier 2 names a human).

## Related

- `docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md`
  (addendum 3: recall-time value law; tombstone policy this FR implements)
- Named follow-up (not scope): premise-pair disagreement-diff; fire-count
  instrumentation (diary seed 3)

## Judgement (2026-08-24)

**Verdict: APPROVED WITH REVISIONS** — rendered via the sole judge route
(gpt-5.5); full artifact:
`feature-requests/FR-878-reversible-amnesia-tiered-approval.judgement.md`.
R-1 archive identity/tombstone schema; R-2 conflict-safe restore; R-3
re-derivation scoped to forget-tombstones only; R-4 machine-checkable
tier provenance; R-5 exact `premise_kind` enum, fail-closed to tier 3;
R-6 FR-877 decoupled (advisory is collect output); R-7 tombstone index
protected from self-erasure. All folded above. Authority active.

**Not authorized:** hard-deleting archive content; retention purges;
moving anything off-machine; FR-874 transport; user/session scope; LLM or
network calls in apply/restore/tier/advisory paths; fuzzy premise
detection; graph/prompt YAML changes (C-8: code/docs/tests only);
CI/hook/doctrine changes.
