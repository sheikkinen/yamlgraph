# Judgement: FR-1014 Dir-aware authoring guard for `graphs/` (Phase 0 of FR-1010)

**Verdict:** APPROVED WITH REVISIONS — the guard gap is real and the two-predicate hardening is the right-sized remedy, but implementation authority activates only after R-1 through R-4 are folded into the FR and this advisory judgement is human-reviewed.

**DRAFT:** Advisory until human-reviewed.

**Prior art:** see FR-1014's own Prior Art field (FR-767, FR-889, FR-1010) — this judgement reviews and dispositions those same citations; FR-1010/FR-1011 are the governing plan and dependent phase, not precedent.

**Reviewed against:** `feature-requests/FR-1014-dir-aware-authoring-guard.md`; `feature-requests/FR-1010-chaplain-archival-plan.md`; `feature-requests/FR-1010-chaplain-archival-plan.judgement.md`; `feature-requests/FR-1011-relocate-chaplain-live-parts.md`; `feature-requests/FR-767-graph-authoring-sole-route.md`; `feature-requests/FR-889-os-enforced-main-write-lock.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/hooks/scripts/pre-command-guard.sh`; `.github/hooks/tests/test_authoring_guard.py`; `.github/hooks/README.md`; `scripts/check_authoring_proof.py`; `scripts/worktree.sh`; `capabilities/CAP-158-copilot-skill-promotion.yaml`; `capabilities/CAP-192-branch-deny-guidance-manual-worktree-lane.yaml`; `capabilities/CAP-211-sole-route-judge-review.yaml`; `ARCHITECTURE.md`; and the committed `git ls-files` census of `graphs/enforcement/**`, `.chaplain/graphs/**`, `graphs/showcase.yaml`, and `.chaplain/graphs/pipeline.yaml`.

## What is sound

The defect is demonstrated by committed code and real paths. The PreToolUse predicate and commit backstop both accept only flat `graphs/*.yaml` paths (`.github/hooks/scripts/pre-command-guard.sh:164-171`; `scripts/check_authoring_proof.py:8-10,21-26`), while the committed tree contains `graphs/enforcement/changelog-req-check.yaml` and `graphs/enforcement/prompts/cross_check.yaml`. The current Tier-2 witness also names `.chaplain/graphs/pipeline.yaml` and `graphs/showcase.yaml`, neither of which exists, instead of exercising the real directory layout (`.github/hooks/tests/test_authoring_guard.py:23-28,104-114`). Correcting the predicate before FR-1011 relocates graph directories therefore closes a real enforcement gap rather than inventing a new mechanism (`feature-requests/FR-1011-relocate-chaplain-live-parts.md:108-130`).

The phase boundary is disciplined. FR-1010 explicitly split guard hardening from relocation, requires FR-1014 to merge first, and requires human review of the enforcement change (`feature-requests/FR-1010-chaplain-archival-plan.md:210-228,324-388`). FR-1014 preserves the sentinel mechanism, the `.chaplain` arm, the `examples/` arms, and the OS-lock roots, so it remains one concern (`feature-requests/FR-1014-dir-aware-authoring-guard.md:100-123,145-158`).

Against the eight rubric criteria:

1. **Scope:** two mirrored predicate lists, their direct witnesses, traceability, and the documentation that enumerates the predicate are the minimum complete surface. Changes to sentinel lifecycle, author routing, OS-lock roots, or `.chaplain` removal are unnecessary and excluded (`feature-requests/FR-1014-dir-aware-authoring-guard.md:37-43,145-148`).
2. **Consistency:** the objective and phase ordering agree, but the proposed GREEN regex does not match the required `graphs/enforcement/changelog-req-check.yaml` positive, and the no-phantom-fixture criterion conflicts with retaining the nonexistent `graphs/showcase.yaml` fixture (`feature-requests/FR-1014-dir-aware-authoring-guard.md:74-91,100-117,125-133`). R-1 and R-2 resolve both contradictions.
3. **Measurability:** predicate truth tables, unchanged-arm diffs, focused pytest, commit ordering, a hook payload, and human-review evidence are mechanically checkable (`feature-requests/FR-1014-dir-aware-authoring-guard.md:121-143`); the revised criteria below remove the ambiguous claim that a tuple "`GOVERNED` return[s] True."
4. **Feasibility:** both implementations already use Python regular expressions and expose directly testable predicates (`.github/hooks/scripts/pre-command-guard.sh:164-171`; `scripts/check_authoring_proof.py:21-26,39-42`). No dependency or runtime change is required.
5. **Architecture alignment:** extending the existing FR-767 path-based bright line conforms before extending, and leaving `graphs/` outside the broad FR-889 OS lock preserves artifact-specific governance (`.github/hooks/README.md:82-112`; `scripts/worktree.sh:503-537`). The proposed CAP-211 fallback is not aligned: CAP-211 governs judge/review wrappers and REQ-YG-527 governs branch-denial guidance, while CAP-158/REQ-YG-423 owns the executable graph-authoring route (`capabilities/CAP-211-sole-route-judge-review.yaml:1-24`; `capabilities/CAP-192-branch-deny-guidance-manual-worktree-lane.yaml:1-17`; `capabilities/CAP-158-copilot-skill-promotion.yaml:1-46`). R-3 fixes the mapping.
6. **Single responsibility:** this is one enforcement-hardening concern. Documentation and requirement updates describe that same contract; they are not independent features.
7. **Strategic classification:** this is maintenance of an existing repository enforcement primitive, not a new framework primitive, contrib example, or pattern-only proposal. It has multiple immediate consumers but reuses the FR-767 abstraction rather than adding another one (`feature-requests/FR-1014-dir-aware-authoring-guard.md:8-13,37-43`).
8. **Testability:** failing tests follow directly from the positive/negative path table and can fail on the missing regex behavior rather than missing fixtures or imports. The proposed direct import of `scripts.check_authoring_proof.GOVERNED` is workable; R-1 freezes the exact table and R-3 freezes its requirement marker.

## Required revisions

### R-1: Make the GREEN predicate satisfy the stated path contract

Replace the proposed `graphs/([^/]+/)*graph\.ya?ml$` arm with a one-directory graph-specification arm that covers every YAML graph file directly below a named graph directory, including non-`graph.yaml` specifications:

```python
re.search(r"(^|/)graphs/[^/]+/[^/]+\.ya?ml$", p)
re.search(r"(^|/)graphs/[^/]+/prompts/[^/]+\.ya?ml$", p)
re.search(r"(^|/)graphs/[^/]+\.ya?ml$", p)
```

Use the `^`-anchored equivalents in `scripts/check_authoring_proof.py`. Amend Summary, Ideal Result, GREEN, and Acceptance Criteria to say that the governed dir-style contract is `graphs/<name>/*.yaml` plus `graphs/<name>/prompts/*.yaml`, not only `graphs/<name>/graph.yaml`. This is required because the FR's own positive `graphs/enforcement/changelog-req-check.yaml` cannot match the proposed implementation (`feature-requests/FR-1014-dir-aware-authoring-guard.md:61-80,100-114`).

Freeze one shared truth table in both focused test surfaces:

- positive existing paths: `graphs/enforcement/changelog-req-check.yaml`, `graphs/enforcement/prompts/cross_check.yaml`;
- positive FR-1011 paths: `graphs/fr_triage/graph.yaml`, `graphs/fr_triage/prompts/triage_fr.yaml`;
- positive synthetic contract path: `graphs/fr1014-flat.yaml`;
- negative paths: `graphs/README.md`, `graphs/fr_triage/tools.py`, `graphs/fr_triage/nested/graph.yaml`, `graphs/fr_triage/prompts/nested/triage.yaml`.

The RED record must show all three currently missing classes fail: direct child YAML, dir-style `graph.yaml`, and dir-style prompt YAML. The GREEN record must show the hook predicate and `GOVERNED` agree on every row.

### R-2: Replace the impossible fixture rule with explicit provenance

Remove the acceptance criterion claiming that the hook test may contain no path that does not exist or is not about to be created. No committed flat `graphs/*.yaml` file exists, yet retaining the flat arm is an explicit requirement, so a synthetic create-path witness is necessary. Replace `GOVERNED_TOP` with an honestly named `GOVERNED_FLAT_SYNTHETIC`, remove `GOVERNED_CHAPLAIN`, and classify each truth-table fixture as `existing`, `FR-1011`, or `synthetic contract`.

The mechanical rule is: no synthetic path may be cited as evidence of current repository shape, and every path described as existing must be checked with `git ls-files --error-unmatch <path>`. This preserves the substance-over-presence lesson without making flat-arm testing impossible.

### R-3: Bind the witnesses to the graph-authoring requirement

Delete the "`grep -l FR-767` / if none / CAP-211" decision branch from the RED plan. Tag both the Tier-2 hook witness and the new Tier-1 proof witness with `REQ-YG-423`, the existing requirement that owns the executable graph-authoring route. Extend `capabilities/CAP-158-copilot-skill-promotion.yaml`'s REQ-YG-423 description and module list to include `.github/hooks/scripts/pre-command-guard.sh`, `scripts/check_authoring_proof.py`, `.github/hooks/tests/test_authoring_guard.py`, and `tests/unit/test_fr1014_authoring_proof_dir_graphs.py`; regenerate the corresponding `ARCHITECTURE.md` entry.

Do not use CAP-211/REQ-YG-642, REQ-YG-569, or REQ-YG-632: those govern judge/review execution. Do not use REQ-YG-527: it governs branch-create denial guidance, not graph authoring (`ARCHITECTURE.md:2473-2478`; `capabilities/CAP-211-sole-route-judge-review.yaml:1-24`).

### R-4: Complete the research and documentation records

Make the FR's own Alternatives Considered section the substantive research record. Render five solution classes with precedent and disposition: the selected root-scoped direct-YAML-plus-prompts predicate; folding the change into FR-1011; adding `graphs/` to the FR-889 OS lock; a repository-global `graph.yaml` predicate; and flattening graph layouts. Preserve the real disagreement between the selected artifact-specific guard and the broader OS lock, then state:

> `is_this_a_graph`: no — this is a deterministic predicate, test, and documentation correction with no LLM stage or corpus fan-out.

The inherited FR-1010 answer concerns the archival program and its Phase 2 census, not this enforcement FR (`feature-requests/FR-1010-chaplain-archival-plan.md:17-23,420-438`). The local statement is required by the prospective research gate (`.github/skills/judge-fr/doctrine.md:116-128`).

Also make the currently conditional documentation update mandatory. Update `scripts/check_authoring_proof.py:8-10` and `.github/hooks/README.md:82-86` to enumerate `graphs/<name>/*.yaml` and `graphs/<name>/prompts/*.yaml` alongside flat `graphs/*.yaml`; both currently publish the old flat-only contract.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1014-dir-aware-authoring-guard.md`: fold R-1 through R-4, the revised criteria, implementation record, RED/GREEN SHAs, and human-review record. |
| D-2 | `.github/hooks/scripts/pre-command-guard.sh`: change only the `graphs/` alternatives in `governed_path()`. |
| D-3 | `scripts/check_authoring_proof.py`: mirror the exact root-anchored `graphs/` alternatives and update its governed-path docstring. |
| D-4 | `.github/hooks/tests/test_authoring_guard.py` and `tests/unit/test_fr1014_authoring_proof_dir_graphs.py`: shared positive/negative contract, provenance labels, denial-message witness, and REQ-YG-423 tags. |
| D-5 | `capabilities/CAP-158-copilot-skill-promotion.yaml` and generated `ARCHITECTURE.md`: extend REQ-YG-423 traceability to the guard and proof surfaces. |
| D-6 | `.github/hooks/README.md`: document flat and dir-style `graphs/` coverage. |
| D-7 | `changelog/unreleased/fr-1014-dir-aware-authoring-guard.md`: one fix/enforcement-hardening fragment linked to FR-1014 and REQ-YG-423. |

Not authorized under FR-1014: changing the `examples/` or `.chaplain/graphs` predicates; deleting the `.chaplain` arm or changing the terminal pre-filter; changing sentinel creation, validation, cleanup, or denial wording except as required by the existing assertion; modifying `scripts/author.sh`; adding `graphs/` to `FR889_GOVERNED_ROOTS`; changing graph layouts or graph contents; relocating Chaplain files; introducing a shared regex module or new runtime abstraction; changing judge/review routes; or modifying unrelated hook behavior.

## Revised acceptance criteria

- [ ] AC-01: FR-1014 contains five dispositioned solution classes with precedent, preserved guard-versus-OS-lock disagreement, and the explicit local `is_this_a_graph: no` answer.
- [ ] AC-02: For every frozen truth-table row, `governed_path(path)` equals `any(pattern.match(path) for pattern in GOVERNED)` and equals the expected result.
- [ ] AC-03: Existing positives pass `git ls-files --error-unmatch`; FR-1011 positives are named by that judged phase FR; synthetic fixtures are explicitly named synthetic and are not cited as existing-tree evidence.
- [ ] AC-04: RED tests fail for direct child YAML, dir-style `graph.yaml`, and dir-style prompt YAML while all frozen negatives remain allowed; the RED commit carries `SKIP=pytest`.
- [ ] AC-05: GREEN uses only the three authorized `graphs/` arms in each predicate: `graphs/[^/]+/[^/]+\.ya?ml`, `graphs/[^/]+/prompts/[^/]+\.ya?ml`, and the retained flat `graphs/[^/]+\.ya?ml`.
- [ ] AC-06: `.github/hooks/tests/test_authoring_guard.py` denies every positive without a sentinel, allows every negative, and confirms the denial names `scripts/author.sh`; `tests/unit/test_fr1014_authoring_proof_dir_graphs.py` checks the same table against `GOVERNED`.
- [ ] AC-07: Both focused test files carry `pytest.mark.req("REQ-YG-423")`; CAP-158 and generated `ARCHITECTURE.md` describe and list all four guard/proof implementation and witness modules; no FR-1014 witness is assigned to CAP-211 or REQ-YG-527.
- [ ] AC-08: `git diff` shows the `examples/` arms and `.chaplain/graphs` arm byte-identical, the terminal pre-filter unchanged, and no sentinel or `author.sh` change.
- [ ] AC-09: `scripts/check_authoring_proof.py`'s docstring and `.github/hooks/README.md` enumerate flat, direct-child, and prompt-subdirectory `graphs/` coverage.
- [ ] AC-10: `pytest .github/hooks/tests/test_authoring_guard.py tests/unit/test_fr1014_authoring_proof_dir_graphs.py -q` passes, and `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: A direct hook payload attempting unsentineled creation of `graphs/enforcement/prompts/x.yaml` returns `deny` and names `scripts/author.sh`.
- [ ] AC-12: The RED commit precedes the GREEN commit in `git log`; both SHAs and commands are recorded in FR-1014.
- [ ] AC-13: The FR-1014 changelog fragment exists and validates under the repository's existing changelog checks.
- [ ] AC-14: A human reviews the final enforcement diff and records the reviewed PR or commit in FR-1014 before merge.
- [ ] AC-15: FR-1014 merges before any FR-1011 relocation commit is enforced.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 and the revised acceptance criteria are folded into FR-1014 before implementation begins. | GATE |
| C-2 | Human review of this advisory judgement and of the final hook diff is recorded before merge; enforcement infrastructure is adversarial input. | GATE |
| C-3 | Only the two mirrored `graphs/` predicate lists, their direct tests, their traceability, and their enumerating documentation may change. | GATE |
| C-4 | The `examples/` and `.chaplain/graphs` arms, terminal pre-filter, sentinel lifecycle, `scripts/author.sh`, and FR-889 root list remain unchanged. | GATE |
| C-5 | The RED commit with `SKIP=pytest` precedes the GREEN implementation commit and demonstrates the missing behavior rather than a fixture/import failure. | GATE |
| C-6 | Hook and proof predicates agree on the complete frozen table; a one-sided fix is not mergeable. | GATE |
| C-7 | FR-1014 is merged and verified before FR-1011 begins relocation enforcement. | GATE |

Authority granted: after R-1 through R-4 are folded and this judgement is human-reviewed, implement the frozen dir-aware `graphs/` predicate hardening, witnesses, traceability, documentation, and changelog only.
