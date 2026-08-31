# Judgement: FR-942 Instruction Context Diet

**Verdict:** APPROVED WITH REVISIONS — the repository-instruction cleanup is sound, but NO authority exists until R-1 through R-6 are folded into the FR and the enforcement-infrastructure review gate is recorded.

**Reviewed against:** `feature-requests/FR-942-instruction-context-diet.md`; cited/prior-art files `feature-requests/FR-941-home-config-cleanup.md`, `feature-requests/FR-743-sessionstart-briefing-hook.md`, and `feature-requests/FR-918-ci-python-matrix-refresh.md`; repository doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md`, `CLAUDE.md`, and `ARCHITECTURE.md`; implementation precedent `.pre-commit-config.yaml`, `scripts/size_gate.py`, `.github/hooks/tests/test_size_gate.py`, and `capabilities/CAP-255-os-enforced-main-write-lock.yaml`. No uncommitted audit log, session transcript, or author chat narrative was consumed.

## What is sound

- **Scope and single responsibility:** deduplicating, relocating reference material, compressing overgrown doctrine, and preventing the same instruction surface from re-bloating form one repository-governance concern. The byte guard is a standing constraint on the surface being reduced, not an orthogonal feature (FR-942:30-43). No split is required once the completed autocompaction investigation is removed from the implementation deliverables.
- **Problem evidence:** the duplicated `Submitting Proposals` section is present in both instruction files (`CLAUDE.md:37`; `.github/copilot-instructions.md:196`), and the identified reference-heavy sections exist at `CLAUDE.md:60`, `CLAUDE.md:390-438`, and `CLAUDE.md:486-515`. The current files total 56,610 bytes, so there is a concrete baseline rather than a hypothetical optimization.
- **Feasibility and architecture alignment:** the existing gate already centralizes file-size policy (`scripts/size_gate.py:20-23,41-69`) and has direct tests (`.github/hooks/tests/test_size_gate.py`). Extending it is workable, provided the Markdown trigger gap in `.pre-commit-config.yaml:160-165` is closed and requirement traceability is updated. Moving operational reference material out while retaining concise pointers follows the repository's existing quick-reference pattern (`.github/copilot-instructions.md:183-194`).
- **Strategic classification:** this is repository pattern documentation plus a local enforcement guard, not a YAMLGraph framework primitive. It adds no runtime abstraction or graph capability. That classification is consistent with `growth_as_default` and `constraint_over_code` (`.github/copilot-instructions.md:95,163`): subtract prompt mass while preserving the load-bearing constraint.

## Required revisions

### R-1: Supply a substantive committed research record

Replace the `**Research:**` claim at FR-942:9 with a link to a committed `feature-requests/FR-942-instruction-context-diet.research.md`, or expand the in-body record to the same substance. The record must contain 4-6 genuine solution classes, precedent lines, preserved disagreement, and an explicit `is_this_a_graph` answer, as required by `.github/skills/judge-fr/doctrine.md:118-129`. The current alternatives table does not record the graph-fit answer or competing evidence, and “session context analysis 2026-08-31” is not a committed artifact available under input closure.

Record reproducible evidence for both instruction files being injected, the exact byte baseline, and the SessionStart visibility claim. Disposition FR-941 as the disjoint home-side sibling, FR-918 as the stale-reference witness, and FR-743 as conflicting/current precedent: FR-743 still records the visibility verdict as “armed, not yet witnessed” and prescribes first-PreToolUse fallback on a negative result (FR-743:136-145). If no committed witness supports FR-942:35-43, remove the empirical SessionStart verdict and side finding; retain the byte guard only as the standing constraint on committed instruction size.

### R-2: State the ideal result and freeze the document topology

Insert an `## Ideal Result` section immediately before `## Proposed Solution`, as required by `.github/copilot-instructions.md:233`. State the exact post-change role of each injected file and the maximum combined size.

Retain `CLAUDE.md` as the thin development-command, anti-pattern, and pointer surface proposed at FR-942:30. Delete the “Deferred to Judge” alternative at FR-942:60: deletion of a still-recognized platform instruction entry point is not authorized by this FR without a separate, human-evidenced amendment.

Add a source-to-destination table that maps the environment-variable table, branch-protection table, CI-check list, and FR-761 walkthrough to the committed `reference/development-operations.md` destination. `CLAUDE.md` must retain a direct link to each relocated section.

### R-3: Define semantic preservation before compressing Scripture

Resolve the scope contradiction between the named target `one_session_one_repo` (FR-942:26), which is under `process`, and the proposed `trap/cure/question` scope (FR-942:32,49): include `process` in the governed collections. Freeze the governed set as `traps`, `cures`, `questions`, and `process`; boundaries, generative methods, seeds, the Ten Commandments, and the Sermon are not authorized for compression.

Replace “~40 words” with an exact maximum of 40 whitespace-delimited words per governed scalar and define the counting command/test. Preserve the exact collection/key set. For each changed key, `docs/scripture-provenance.md` must contain the removed incident narrative and every removed citation verbatim, keyed as `<collection>.<key>`; checking only `FR-XXX` tokens is insufficient because the current entries also carry NC identifiers, dates, cross-project witnesses, commands, and named incidents (`.github/copilot-instructions.md:116-118,164`).

The mechanical tests must enforce word limits, key-set equality, provenance-key coverage, and citation preservation. Semantic preservation remains a human gate: the reviewer must confirm side-by-side that every compressed trap/cure/process entry retains its trigger and prescribed response, and every question retains its `MOMENT:` firing condition. The FR cannot assign this verification to “the Judge” after scope is frozen (FR-942:32).

### R-4: Replace approximate and proxy criteria with exact assertions

Freeze the measured baseline at 56,610 bytes and the 40% reduction ceiling at 33,966 combined bytes for `.github/copilot-instructions.md` plus `CLAUDE.md`. Use raw byte counts, not rounded “57.5 KB” or token estimates (FR-942:8,50).

Replace the “no shared heading with >2 identical consecutive sentences” proxy at FR-942:47 with assertions that:

1. `Submitting Proposals` exists only in `.github/copilot-instructions.md`;
2. no normalized three-sentence run is identical across the two files;
3. the four relocated blocks are absent from `CLAUDE.md`;
4. every relocation pointer resolves to a committed file; and
5. both instruction files remain non-empty and their combined size is at most 33,966 bytes.

State the normalization and sentence-boundary algorithm in the test so a change cannot pass by renaming a heading or adjusting whitespace.

### R-5: Specify and test the byte-budget enforcement path

Extend `scripts/size_gate.py` with an explicit combined instruction-byte budget of 33,966 bytes while preserving its existing line-count behavior. Update `.pre-commit-config.yaml:160-165` so the hook runs when either instruction Markdown file changes; the current `files: \.(py|sh)$` selector does not run for the governed files.

Write RED-first tests in `.github/hooks/tests/test_size_gate.py` for: exactly-at-budget pass, over-budget failure naming both files and the measured total, either required instruction file missing/empty, and preservation of the existing Python/shell line gate. Update `capabilities/CAP-255-os-enforced-main-write-lock.yaml` and the REQ-YG-631 entry in `ARCHITECTURE.md:3128` so the requirement and test marker describe both the line ratchet and instruction-byte ceiling.

### R-6: Add the adversarial human-review and completion gates

Add an acceptance criterion and implementation-status checkbox requiring explicit human review of the `.github/copilot-instructions.md`, `scripts/size_gate.py`, `.pre-commit-config.yaml`, capability/requirement, and test diffs before landing. Scripture and pre-commit are enforcement infrastructure and must be treated as adversarial input (`.github/skills/judge-fr/doctrine.md:98-99`; `.github/copilot-instructions.md:84`).

Add the required changelog fragment, FR implementation-status update, and diary reflection with a `Seed:`. Record the exact validation commands and their outputs in the FR; “existing hooks/gates still pass” at FR-942:53 is not a mechanically complete criterion.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Amended `feature-requests/FR-942-instruction-context-diet.md` and committed `feature-requests/FR-942-instruction-context-diet.research.md` |
| D-2 | Deduplicated and compressed `.github/copilot-instructions.md` |
| D-3 | Retained, thin `CLAUDE.md` containing development commands, anti-patterns, and pointers |
| D-4 | Consolidated operational reference `reference/development-operations.md` |
| D-5 | `docs/scripture-provenance.md` |
| D-6 | `scripts/size_gate.py`, `.pre-commit-config.yaml`, and `.github/hooks/tests/test_size_gate.py` |
| D-7 | `capabilities/CAP-255-os-enforced-main-write-lock.yaml` and the REQ-YG-631 text in `ARCHITECTURE.md` |
| D-8 | One changelog fragment, one `docs/diary/` reflection, and FR implementation-status evidence |

Not authorized: deleting `CLAUDE.md`; deleting or semantically weakening any Scripture heuristic; changing Knowledge Graph collections outside `traps`, `cures`, `questions`, and `process`; modifying SessionStart/PreToolUse hooks or FR-743 implementation; implementing runtime autocompaction; changing user-home files governed by FR-941; changing judge/review doctrine; or modifying YAMLGraph runtime code, graphs, prompts, examples, or unrelated reference documentation.

## Revised acceptance criteria

- [ ] AC-01: The `**Research:**` field links to a committed substantive record satisfying R-1, including reproducible instruction-injection and byte-count evidence, 4-6 solution classes, precedent dispositions, disagreement, and an explicit `is_this_a_graph` answer.
- [ ] AC-02: An `## Ideal Result` precedes `## Proposed Solution`; the FR freezes `CLAUDE.md` as retained/thin and contains the exact R-2 source-to-destination mapping.
- [ ] AC-03: `Submitting Proposals` exists only in `.github/copilot-instructions.md`, and the committed normalization test finds no identical normalized three-sentence run across the two instruction files.
- [ ] AC-04: The environment-variable table, branch-protection table, CI-check list, and FR-761 walkthrough are absent from `CLAUDE.md`; every replacement pointer resolves to the exact committed destination named in the FR.
- [ ] AC-05: The `traps`, `cures`, `questions`, and `process` collection/key sets are unchanged; no other Knowledge Graph collection or Scripture section is compressed.
- [ ] AC-06: Every governed scalar contains at most 40 whitespace-delimited words; every question retains `MOMENT:`; the human review record confirms every changed trap/cure/process entry retains its trigger and prescribed response.
- [ ] AC-07: `docs/scripture-provenance.md` has exactly one keyed record for every changed governed entry and preserves every removed incident narrative and citation verbatim; the preservation test passes.
- [ ] AC-08: `wc -c .github/copilot-instructions.md CLAUDE.md` reports a combined total no greater than 33,966 bytes, against the frozen 56,610-byte baseline.
- [ ] AC-09: `scripts/size_gate.py` rejects a combined instruction size above 33,966 bytes and missing/empty governed files while preserving the existing line gate; `.pre-commit-config.yaml` triggers it for either instruction Markdown path.
- [ ] AC-10: RED and GREEN commits are recorded for the byte-budget tests; `.github/hooks/tests/test_size_gate.py` covers the exact boundary, overage diagnostic, missing/empty files, and existing line behavior.
- [ ] AC-11: `capabilities/CAP-255-os-enforced-main-write-lock.yaml` and `ARCHITECTURE.md` describe the instruction-byte ceiling under REQ-YG-631, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-12: `pytest .github/hooks/tests/test_size_gate.py -q --no-cov`, `python scripts/size_gate.py`, and `pre-commit run file-size-gate --files CLAUDE.md .github/copilot-instructions.md scripts/size_gate.py .github/hooks/tests/test_size_gate.py` pass with outputs recorded in the FR.
- [ ] AC-13: A human explicitly reviews and approves the Scripture, pre-commit, size-gate, capability/requirement, and test diffs before landing.
- [ ] AC-14: The FR implementation status records decisions and deviations; one changelog fragment and one diary reflection with `Seed:` are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not begin enforcement until R-1 through R-6 are folded into the committed FR; the current draft grants no authority. | GATE |
| C-2 | Preserve every governed key and heuristic meaning; compression that loses a trigger, prescribed response, firing moment, or provenance record must be reverted. | GATE |
| C-3 | Do not delete `CLAUDE.md`, touch runtime hook delivery, or cross any surface listed as not authorized. | GATE |
| C-4 | Human review of all Scripture and enforcement-infrastructure changes is required before landing; automated green checks cannot satisfy this condition. | GATE |
| C-5 | The byte guard must trigger on changes to either governed Markdown file and must retain all existing line-size behavior and tests. | GATE |

Authority granted: after the committed FR satisfies C-1 and a human records the C-4 approval, enforcement may perform only D-2 through D-8 within the frozen boundaries above.
