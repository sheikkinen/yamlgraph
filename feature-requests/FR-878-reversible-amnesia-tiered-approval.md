# Feature Request: Reversible Amnesia & Tiered Approval (amends FR-875 C-6)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
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
   - `forget` → move note to `<memory_root>/.archive/<YYYY-MM-DD>/repo/<name>`
     (never unlink); `redact` → stash the original there before replacing.
   - Append one line per archived note to `<memory_root>/repo/_tombstones.md`:
     date, name, verdict, one-line reason, archive path, manifest hash.
     The tombstone file is a normal note (curated by the same graph;
     self-referential by design — the graveyard is case law).
   - Dot-directory is invisible to the memory tool's listing and excluded
     from `collect.py` by construction (repo/*.md glob).
   - No retention purge in v1 — the corpus is kilobytes; deletion of the
     archive is a future human act, not a mechanism.
2. **Restore:** `apply.py restore <archive-path>` — moves a note back
   into the live scope and appends a restore line to the tombstone index.
3. **Tiered approval (replaces the uniform C-6 sign-off):**
   | Tier | Disposition contents | Requirement |
   |---|---|---|
   | 0 | keep-only | none (no-op) |
   | 1 | compress/redact only, zero forgets | agent-signable under recorded standing delegation; sign-off line carries provenance; audit line appended to hook log |
   | 2 | any `forget` | human answer to a structured question (evidence: the forget rows + tombstone preview + recommended default); sign-off names the human |
   | 3 | export/publication premise | always human, non-delegable — publication is the one act soft-delete cannot undo |
   The hash-binding mechanics (manifest + disposition sha256, live-hash
   drift refusal, validate-all-then-apply-all, idempotence) are unchanged
   at every tier — the amendment relocates *who approves*, not *what is
   verified*.
4. **Re-derivation detection (forecast validation):** `collect.py`
   compares each live note name and content hash against the archive;
   on similarity (same filename, or identical hash) it emits an advisory
   line — "note X resembles archived Y (forgotten <date>) — consider
   restore". Rides the FR-877 briefing seam; zero LLM.

## Acceptance Criteria

- [ ] AC-01: `forget` archives + tombstones instead of unlinking; `redact`
      stashes the original; archive is invisible to memory recall and to
      collect manifests (tests, temp roots only).
- [ ] AC-02: restore moves an archived note back and records the restore
      in the tombstone index; idempotent (test).
- [ ] AC-03: apply computes the tier from the disposition contents and
      enforces the matching sign-off requirement: tier 1 accepts
      delegation-provenance lines; tier 2 refuses unless the sign-off
      names a human approver; tier detection is content-based, not
      flag-based (tests).
- [ ] AC-04: export-premise dispositions (premise recorded in the
      disposition by reconcile) are always tier 3 regardless of verdicts
      (test).
- [ ] AC-05: hash-binding, drift refusal, and idempotence behavior are
      unchanged at all tiers (existing tests stay green).
- [ ] AC-06: re-derivation advisory fires on filename or content-hash
      match against the archive; zero LLM/network (test).
- [ ] AC-07: FR-875's C-6 amendment is recorded in FR-875 (pointer to
      this FR) and `examples/memory-curation/README.md` documents the
      tier table.
- [ ] AC-08: tests req-tagged (extend CAP-247); diary reflection.

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

## Judgement (pending)

Not judged in the author's session; route:
`.github/skills/judge-fr/adapters/README.md`.
