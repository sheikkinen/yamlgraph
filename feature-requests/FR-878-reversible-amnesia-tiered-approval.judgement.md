# Judgement: FR-878 Reversible Amnesia & Tiered Approval

**Verdict:** APPROVED WITH REVISIONS — replacing irreversible deletion with archive/restore is the right correction to FR-875 C-6, but authority activates only after archive identity, restore conflicts, tier provenance, export-premise detection, and re-derivation scope are made mechanically exact.

**Reviewed against:** `feature-requests/FR-878-reversible-amnesia-tiered-approval.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `ARCHITECTURE.md`; `feature-requests/FR-875-memory-corpus-curation-graph.md`; `feature-requests/FR-875-memory-corpus-curation-graph.judgement.md`; `feature-requests/FR-877-memory-curation-staleness-advisory.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.judgement.md`; `feature-requests/FR-868-scripture-dev-salvage.md`; `feature-requests/FR-868-scripture-dev-salvage.judgement.md`; `docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md`; `docs/diary/diary-2026-07-16-the-human-skims.md`; `capabilities/CAP-247-memory-corpus-curation.yaml`. No author chat narrative was consumed.

**Prior art:** FR-875 (parent, C-6 amended), FR-877, FR-874, FR-868
dispositioned throughout. FR-809 (recon browser sniff) and FR-867
(ramp deviant-daily) — noun collisions on "tiered" only; no territorial
overlap. FR-824 (HVA bulletin) — noun collision on "amnesia"; unrelated.

## What is sound

The problem is real and tightly evidenced. FR-875 currently says live memory deletion/redaction happens only after written, hash-bound human sign-off (`feature-requests/FR-875-memory-corpus-curation-graph.md:28-29`, `109-117`), and its implementation record shows the first real run produced a 57-note disposition that was not signed off, then a second hygiene run was applied under recorded operator delegation (`feature-requests/FR-875-memory-corpus-curation-graph.md:265-292`). FR-878 correctly identifies the defect in approving a long forecast document: the human-skims diary says the human reads FR/judgement corpora by skim, not deep review, and that human-facing load-bearing content should be decision-shaped and tiny (`docs/diary/diary-2026-07-16-the-human-skims.md:5-17`, `23-32`, `50-54`, `75-77`). That matches the repo traps FR-878 cites: shape checks are theatre when they cannot prove substance (`.github/copilot-instructions.md:87-89`), and gates over forecasts should be moved to defect classes where possible (`.github/copilot-instructions.md:95-96`).

The strategic direction is minimal rather than expansive. FR-878 amends the one FR-875 condition whose premise changed, while preserving the inherited hash-binding, live-hash drift refusal, validate-all-then-apply-all, and idempotence mechanics (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:83-93`; `feature-requests/FR-875-memory-corpus-curation-graph.judgement.md:31-36`, `93-105`). It also preserves FR-874's rejected-precedent boundary by staying machine-local and by making export/publication stricter, not looser (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:13-15`, `140-150`; `feature-requests/FR-874-cross-device-agent-memory-sync.md:26-32`). Strategic classification: **contrib/example repo-operations amendment to CAP-247**, not a YAMLGraph framework primitive.

The archive/tombstone idea fits the recall-time evidence. The 2026-08-24 diary states that a note's value is determined at recall time, that forget should require a tombstone, and that negative knowledge is case law (`docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md:118-143`). FR-878 turns that policy into a reversible local mechanism: archive shelf, tombstone index, restore command, and re-derivation advisory (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:53-63`, `70-82`, `94-98`). The broad scope is still one concern: making amnesia safe enough that approval can be proportional to residual irreversibility.

## Required revisions

### R-1: Define archive identity, path preservation, and tombstone schema exactly

Replace the underspecified `<memory_root>/.archive/<YYYY-MM-DD>/repo/<name>` target with a collision-safe, path-preserving archive identity. As written, same-day repeats, nested note paths, and repeated curation of the same filename can collide or erase provenance (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:70-78`). Fold this by defining the exact archive path layout, sanitization rules, duplicate-name behavior, and tombstone row schema. The row must include enough data to verify and restore without guessing: operation id or timestamp, original relative path, verdict, reason, archive path, pre-apply hash, post-apply hash when applicable, manifest hash, disposition hash, and restore status.

### R-2: Make restore conflict-safe and idempotent

Specify restore semantics for both `forget` archives and `redact` original stashes. The FR says `apply.py restore <archive-path>` moves a note back and records a restore line (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:81-82`), but it does not say what happens when the live destination already exists, has changed after curation, or has already been restored. Fold this by requiring restore to validate the tombstone/archive record, refuse overwriting any live file whose hash is not the expected post-apply state or an already-restored match, and report a clear conflict requiring human action. Idempotence must be defined as a second restore attempt succeeding only when the live bytes already equal the archived bytes and the tombstone already records restoration; otherwise it must fail visibly.

### R-3: Separate forgotten-note re-derivation from redaction backups

Narrow re-derivation detection to the forecast it is supposed to validate: "`forget` means this note should not recur." FR-878 archives both forgotten notes and redacted originals (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:70-72`), then says collect warns on same filename or identical hash against the archive (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:94-98`). That would cause every redacted note to resemble its archived original by filename on every future collection, making the advisory noisy immediately after a successful redaction. Fold this by having collect/advisory compare live notes only against tombstones whose verdict class is `forget`, or by otherwise marking backup-only redaction archives as excluded from re-derivation checks. Tests must prove a redacted note backup does not emit a false re-derivation warning.

### R-4: Pin tier computation and sign-off provenance to machine-checkable records

Make the tier table enforceable without trusting prose. FR-878 says tier detection is content-based, tier 1 is agent-signable under standing delegation, tier 2 names a human, and tier 3 is non-delegable (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:83-93`, `102-114`), but it does not freeze the exact disposition fields, precedence rules, accepted sign-off line formats, standing-delegation source, or audit-log path. Fold this by defining: tier precedence (`export/publication` > any `forget` > `redact`/`compress` only > keep-only); the disposition metadata used to compute it; the exact signed-review fields required for each tier; the committed or FR-recorded standing-delegation text that authorizes tier 1; and the audit line path/content for delegated tier 1 applies. Tier 2 and tier 3 must require a recorded human response artifact, not merely an agent-written human name.

### R-5: Represent publication/export premise as explicit metadata, not fuzzy text

Add an exact premise field that makes tier 3 mechanically detectable. The FR says export-premise dispositions are always tier 3 and that the premise is recorded by reconcile (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:88-89`, `112-114`), while FR-875's current artifact contract records manifest/disposition hashes and audience premise prose, not an exact premise class (`feature-requests/FR-875-memory-corpus-curation-graph.md:102-117`, `131-138`, `265-280`). Fold this by adding a validated field such as `premise_kind: hygiene | export_publication` to the disposition JSON/markdown and requiring apply to compute tier 3 from that exact value. Do not implement substring matching over freeform premise text.

### R-6: Resolve the FR-877 dependency before extending its advisory seam

Make FR-878 independent of FR-877 or explicitly gated on FR-877 landing first. FR-878 says it extends the FR-877 advisory (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:67-68`, `94-98`), but FR-877 is still Proposed and its briefing/advisory surfaces are not established authority (`feature-requests/FR-877-memory-curation-staleness-advisory.md:3-7`, `137-140`). Fold this by either moving the minimal archive-comparison advisory into FR-878's authorized surfaces with tests, or declaring a hard dependency that FR-877 must be judged/enforced before FR-878's advisory portion may be implemented. Archive/restore/tiered apply may remain independent.

### R-7: Protect the tombstone index from erasing its own case law

Specify how `_tombstones.md` participates in future curation. FR-878 calls the tombstone file a normal note and "curated by the same graph" (`feature-requests/FR-878-reversible-amnesia-tiered-approval.md:73-78`), but the diary justifies tombstones as negative knowledge and case law (`docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md:133-143`). If the same graph can later redact or forget the tombstone index, restore discoverability and forecast history become self-erasing. Fold this by defining a protected policy for tombstones: either exclude `_tombstones.md` from `forget`/`redact` while still allowing it to be collected as context, or require any tombstone mutation to keep all archive path/hash/restore records intact and test that the restore index cannot be destroyed by ordinary curation.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-878-reversible-amnesia-tiered-approval.md` folding R-1 through R-7 |
| D-2 | `examples/memory-curation/apply.py` archive, tombstone, restore, tier-computation, sign-off, and conflict behavior |
| D-3 | Memory-curation collect/advisory code that excludes `.archive/`, reads tombstones, and emits forgotten-note re-derivation advisories |
| D-4 | `examples/memory-curation/README.md` documentation for archive/restore, tombstones, tier table, standing-delegation provenance, and export non-delegability |
| D-5 | `feature-requests/FR-875-memory-corpus-curation-graph.md` implementation note/pointer recording that FR-878 amends C-6 |
| D-6 | `capabilities/CAP-247-memory-corpus-curation.yaml` requirement text amended or extended for archive/restore/tiered approval |
| D-7 | Pytest coverage using temp memory roots only, with `@pytest.mark.req("REQ-YG-XXX")` tags for the new/extended requirement |
| D-8 | FR implementation record and diary reflection |

Not authorized: committing live memory note bodies, redacted drafts, archive contents, customer facts, hostnames, credentials, or raw memory-corpus content; moving anything out of the machine-local memory root; rebuilding FR-874 transport or cross-device sync; user/session-scope curation; retention-window purge or hard deletion of the archive; LLM/network calls in apply, restore, tier computation, or re-derivation advisory; fuzzy premise detection; changes to CI, hooks, judge/review doctrine, graph-authoring doctrine, or YAMLGraph framework primitives; graph/prompt YAML changes unless a revised FR explicitly invokes the governed graph-authoring route.

## Revised acceptance criteria

- [ ] AC-01: FR-878 is revised to define archive path identity, tombstone schema, restore conflict rules, re-derivation scope, tier computation, sign-off provenance, export-premise metadata, and FR-877 dependency handling from R-1 through R-7.
- [ ] AC-02: `forget` archives rather than unlinks; `redact` stashes the original before replacement; archived files preserve original relative path identity without collisions; `.archive/` is invisible to memory recall and excluded from collect manifests (tests, temp roots only).
- [ ] AC-03: `_tombstones.md` is appended for every archive and restore event with operation id, original path, verdict, one-line reason, archive path, pre/post hashes as applicable, manifest hash, disposition hash, and restore status; tests validate schema/rendering.
- [ ] AC-04: Restore validates a tombstone/archive record, restores only to the recorded live path, refuses unsafe overwrite or live-hash drift, appends a restore line, and is idempotent only for an already-restored matching live file (tests).
- [ ] AC-05: Apply computes approval tier from disposition content with exact precedence: export/publication premise = tier 3; otherwise any `forget` = tier 2; otherwise any `redact`/`compress` = tier 1; otherwise keep-only = tier 0.
- [ ] AC-06: Tier 1 accepts only a machine-checked standing-delegation provenance line and appends the configured audit line; tier 2 refuses without a recorded human response artifact for the forget rows; tier 3 refuses without a non-delegable recorded human response artifact for the export/publication premise (tests).
- [ ] AC-07: Disposition JSON/markdown records an exact validated premise kind, including `export_publication`; apply derives tier 3 from that field and never from substring matching freeform text.
- [ ] AC-08: Hash-binding, disposition-hash binding, validate-all-then-apply-all behavior, live-hash drift refusal, and existing FR-875 idempotence behavior remain enforced at every tier (existing and new tests).
- [ ] AC-09: Re-derivation advisory emits on same filename or identical content hash only for live notes matching archived `forget` tombstones; redaction backup archives do not trigger the advisory; advisory is pure stdlib with zero LLM/network (tests).
- [ ] AC-10: If FR-877 is not enforced first, FR-878 implements and tests its own minimal archive-comparison advisory seam; if FR-877 is enforced first, FR-878 integrates through that documented seam without changing FR-877's drift marker semantics.
- [ ] AC-11: FR-875 records the C-6 amendment pointer to FR-878, and `examples/memory-curation/README.md` documents archive/restore, tombstones, tier table, standing-delegation provenance, and export non-delegability.
- [ ] AC-12: Tests are req-tagged through CAP-247 or a successor requirement; a diary reflection records the approval-theatre trap and the archive/restore correction.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-7 are folded into `feature-requests/FR-878-reversible-amnesia-tiered-approval.md`. | GATE |
| C-2 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-3 | Tests and smoke checks must use temporary memory roots only; no automated validation may read, archive, restore, or mutate the operator's real memory store. | GATE |
| C-4 | No implementation path may hard-delete archived note content; archive purge, retention windows, or irreversible deletion are separate human-authorized work. | GATE |
| C-5 | Tier 3 export/publication approvals are non-delegable; tier 1 delegation is valid only if the standing-delegation provenance source is recorded and machine-checked. | GATE |
| C-6 | Apply, restore, tier computation, and re-derivation advisory must be deterministic local code with zero LLM or network calls. | GATE |
| C-7 | No committed artifact may contain copied memory note bodies, redacted originals, archive payloads, customer facts, hostnames, credentials, or raw memory-corpus content. | GATE |
| C-8 | If implementation materially modifies `graph.yaml` or any `prompts/*.yaml`, enforcement must stop and revise the FR to use the governed graph-authoring route; this judgement authorizes code/docs/tests only. | GATE |

Authority granted: after the required revisions are folded, enforcement may amend the memory-curation example to archive and restore local amnesia, compute approval tiers from signed dispositions, warn when forgotten notes are re-derived, update FR-875/CAP-247/README documentation, and validate the behavior with temp-root tests only.
