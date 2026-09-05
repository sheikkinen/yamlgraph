# Judgement: FR-1004 Retire the outsider ledger — the posted comment is the record

**Prior art:** dispositioned in the parent FR header ([FR-1004](FR-1004-retire-outsider-ledger.md) — FR-995 R-3/D-7, FR-858, diary 2026-08-23); no REJECTED FR in this territory.

**Route:** `scripts/judge.sh` (Copilot backend, `gpt-5.6-sol`) on lane commit `b3d9fbe1`, 2026-09-05 15:26. Folded verbatim; R-1…R-4 incorporated into the FR (population rule, eleven-field typed marker, graph-route provenance, honest trace claims, revised AC-01…14).

**Verdict:** APPROVED WITH REVISIONS — retiring the contended committed ledger is the minimal cure, but authority activates only after the FR honestly redefines which runs count, preserves the complete observation schema, closes the wrapper-to-graph provenance boundary, and replaces its impossible trace/search assertions.

**Reviewed against:** `feature-requests/FR-1004-retire-outsider-ledger.md`; `feature-requests/FR-995-outsider-reader.md`; `feature-requests/FR-995-outsider-reader.judgement.md`; `feature-requests/FR-858-retire-committed-fr-board.md`; `docs/diary/2026-08-23-the-worktree-is-the-airlock.md`; `docs/census/outsider-ledger.jsonl`; `.github/skills/outsider-view/SKILL.md`; `.github/skills/outsider-view/doctrine.md`; `.github/skills/outsider-view/adapters/graph.yaml`; `.github/skills/outsider-view/adapters/outsider_tools.py`; `scripts/outsider.sh`; `tests/unit/test_fr995_outsider_reader.py`; `tests/unit/test_fr995_outsider_wrapper.py`; `capabilities/CAP-263-outsider-reader.yaml`; `ARCHITECTURE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`.

## What is sound

- **Scope and single responsibility:** the FR addresses one concrete concern: remove a shared derived artifact while retaining the outsider observation on the PR where it occurred. Deleting the ledger, relocating the observation, and replacing its distinct-PR reducer are one coherent retirement, not orthogonal features (`FR-1004:14-18,54-87`). A smaller deletion-only change would discard FR-995's measurement contract.
- **Problem and research substance:** three concurrent branches are recorded as touching the same append-only file (`FR-1004:22-30`), and the in-body alternatives disposition six genuine storage classes (`FR-1004:108-117`). This satisfies the prospective research requirement with more than a shape-only table. The raw-record comparison also identifies specific surprises: a dangling report path and a meaningless temporary source path (`FR-1004:32-50`).
- **Architecture alignment:** the chosen direction follows the cited subtraction precedent. FR-858 retired a committed derived view (`FR-858:12-15,121-144`), and the diary ranks removing the shared artifact above airlocks and conflict choreography (`docs/diary/2026-08-23-the-worktree-is-the-airlock.md:41-56`). The PR comment already exists as the natural observation boundary.
- **Feasibility:** the wrapper already has the PR head, prompt digest, tool SHA, exact input, derived verdict, and counts before posting (`scripts/outsider.sh:67-68,117-140`), while the renderer already emits a machine-identifiable HTML marker (`outsider_tools.py:145-150`). Relocation is technically workable without a new service or dependency.
- **Measurability and testability:** deletion, absence of active ledger writes, exact marker fields, comment-failure behavior, generated architecture, requirement coverage, and TDD history can all be tested directly (`FR-1004:89-106`). Existing focused tests provide the correct seams for renderer, wrapper, comment opt-in, and distinct-count replacement (`test_fr995_outsider_reader.py:181-257`; `test_fr995_outsider_wrapper.py:165-225`).
- **Consistency:** the ideal, solution, and criteria agree that no mode writes under `docs/` and that commenting stays explicit (`FR-1004:54,60-63,92-105`). The remaining contradictions are specific and mechanically repairable in R-1 through R-4.
- **Strategic classification:** **Contrib/example (repo-local process instrument maintenance)**. This serves one repository workflow and reuses an existing PR-comment abstraction; it is not a framework primitive, new example, or general storage facility.

## Required revisions

### R-1: Redefine the counted population and prove the transition query

Replace the claim that every FR-995 inclusion rule remains unchanged (`FR-1004:10`) with the new rule the proposal actually implements: **one observation is countable only when a validated real-PR report is successfully posted as a PR comment; non-comment PR runs no longer count**. FR-995 currently records every successfully validated real-PR invocation, including non-comment runs (`FR-995:41,53,68`), and its implementation record explicitly says #591 has a ledger row but no comment (`FR-995:113`). Therefore `pr` mode without `--comment` cannot both leave no record and preserve the old population (`FR-1004:54,87`).

Fold the new population into FR-1004's Prior art, Ideal Result, S-3, S-4, and acceptance criteria; annotate FR-995 Proposed Solution 7, AC-11, and its implementation record, not merely D-7/AC-11 with one sentence. Update `SKILL.md`, `doctrine.md`, REQ-YG-662, and generated `ARCHITECTURE.md` to use the same rule.

Use a transition-safe search marker that matches both existing posted reports (`<!-- outsider reader | source: ... -->`, `outsider_tools.py:150`) and the new marker, for example:

```bash
gh search prs --repo sheikkinen/yamlgraph \
  'in:comments "<!-- outsider reader |"' \
  --limit 1000 --json number
```

Document a separate `--jq 'length'` form for the count. AC-07 must stop predicting `>= 4` or counting #591 (`FR-1004:105`). It must record the actual returned PR numbers and assert that the enforcing PR appears exactly once after its comment is posted. If GitHub search does not return that PR, the ledger replacement has not been demonstrated and enforcement fails. Do not rewrite historical comments merely to make the query pass.

### R-2: Preserve the observation schema honestly

Replace every claim that the marker preserves "every" R-3 field (`FR-1004:10,54,112`) with an explicit field-by-field transition. FR-995 requires timestamp, repo, PR, head SHA, exact-input SHA-256, model, prompt digest, tool SHA, derived verdict, section-3 count, section-4 count, and report path (`FR-995:53`; `outsider_tools.py:188-199`; `ARCHITECTURE.md:3224`). The proposed eight-field `Provenance` model omits verdict, both counts, and report path (`FR-1004:67-73,91`).

Define a typed observation marker containing UTC timestamp, repo, PR, full PR head SHA, full 64-hex input SHA-256, model, prompt digest, tool SHA, derived verdict, section-3 count, and section-4 count. State explicitly that `report_path` is retired rather than preserved because the posted comment is the durable report location; drop `source:` because it exposes only the disposable child path. Non-posted `--input` and `--selftest` reports may use typed `-` placeholders for unavailable repo/PR/head values, but those reports are not countable observations. Tests must assert exact full values, field uniqueness, UTC shape, absence of `source:`, and round-trip parsing of the rendered report.

### R-3: Close the wrapper-to-graph provenance handoff

Specify the actual implementation path for provenance. Today `finalize_report` renders inside the graph (`graph.yaml:22-25,45-48`; `outsider_tools.py:233-260`), but graph state exposes only `input_path`, `report_path`, and `model` as provenance inputs (`graph.yaml:8-13`). "The wrapper passes the values" is therefore incomplete (`FR-1004:73`).

Add `.github/skills/outsider-view/adapters/graph.yaml` to the implementation surface. Extend its typed state and the wrapper's `--var` arguments with the base observation fields; construct the final typed observation inside `finalize_report`, where the validated report supplies verdict and counts. Pass placeholder values for non-PR modes. Update the fake YAMLGraph executable to consume these variables and make the fake `gh pr comment` preserve the actual `--body-file` content for assertion.

Because this materially modifies `graph.yaml`, add the graph artifact to an FR-1004 authoring brief and route that change through `scripts/author.sh`; retain the resulting `tmp/draft-authoring-report.md`, lint, and smoke record. The repository requires that route for every material `graph.yaml` change regardless of task framing (`.github/copilot-instructions.md:13`). Revise `is_this_a_graph: No` to distinguish "no new LLM decision" from "an existing graph artifact is materially modified" (`FR-1004:9`).

### R-4: Replace impossible trace claims and close the artifact surface

Rewrite "nothing in the repository changes" and "leave no trace anywhere" (`FR-1004:54`). The existing contract intentionally preserves validated reports under repo `tmp/` (`FR-995:48,61`; `scripts/outsider.sh:71-75,113-126`), and S-2 still requires markers on `--input`/`--selftest` reports (`FR-1004:73,91`). The accurate promise is: **outsider execution changes no tracked repository state and creates no durable measurement record unless a validated report is successfully posted; local reports/logs under git-ignored `tmp/` remain diagnostic artifacts**.

Make AC-03 assert no write under `docs/` and no tracked-file mutation, not absence of all artifacts. Add the graph/authoring files, FR-995 active-contract amendments, exact comment-body fake, and query witness to the frozen surface. Remove or correct the dangling `FR-998-anthropic-constrained-structured-output.md` citation (`FR-1004:122`), which is not present at the cited path.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Delete `docs/census/outsider-ledger.jsonl`; remove active ledger configuration, append, reducer, and output paths |
| D-2 | `.github/skills/outsider-view/adapters/outsider_tools.py`: typed observation marker, rendering/parsing, and deletion of ledger helpers |
| D-3 | `scripts/outsider.sh`: pass observation values, post the validated enriched body, remove `OUTSIDER_LEDGER`, and never write under `docs/` |
| D-4 | `.github/skills/outsider-view/adapters/graph.yaml`, FR-1004 authoring brief, and authoring report/lint/smoke evidence |
| D-5 | `.github/skills/outsider-view/{SKILL.md,doctrine.md}` documenting comment-only counting and the transition-safe `gh search` |
| D-6 | Focused renderer and wrapper tests in the two existing FR-995 test modules |
| D-7 | `capabilities/CAP-263-outsider-reader.yaml`, generated `ARCHITECTURE.md`, and REQ-YG-662 traceability |
| D-8 | FR-995 active-contract annotations and FR-1004 implementation/status record, including the credentialed comment/search witness |
| D-9 | FR-1004 removal changelog fragment and one metacognitive diary entry |

Not authorized: automatic invocation or comments; CI, hook, pre-commit, merge-gate, or workflow changes; a blocking outsider verdict; model, prompt, parsing-rule, or derived-verdict changes; edits to historical spike outputs or historical PR comments; deletion of other census artifacts; a new query service or subcommand; judge/review doctrine changes.

## Revised acceptance criteria

- [ ] AC-01: `docs/census/outsider-ledger.jsonl` is deleted, and `git grep -n ledger -- scripts/outsider.sh .github/skills/outsider-view` returns no active ledger implementation or instruction.
- [ ] AC-02: A typed marker on every rendered report contains exactly one UTC timestamp, repo, PR, full head SHA, full input SHA-256, model, prompt digest, tool SHA, derived verdict, section-3 count, and section-4 count; it contains no `source:` or local temp path. Non-PR reports use the specified placeholders and are not countable.
- [ ] AC-03: `report_path` is explicitly recorded as retired/superseded by the posted comment location in FR-1004 and FR-995; no claim says all old fields or inclusion rules are unchanged.
- [ ] AC-04: No mode of `scripts/outsider.sh` creates or modifies a path under `docs/` or any tracked file. Validated local reports/logs may remain under git-ignored `tmp/`; `OUTSIDER_LEDGER` has no effect and is absent from active code.
- [ ] AC-05: `pr --comment` posts exactly the enriched validated report; a fake captures `--body-file` and proves its full head/input values match the fake `gh pr view` result. Comment failure exits non-zero and creates no durable measurement record.
- [ ] AC-06: A non-comment PR run still writes its validated local report under `tmp/` but is excluded from the count. `--input`, `--selftest`, graph failures, parse failures, and comment failures are also excluded.
- [ ] AC-07: `SKILL.md` and doctrine document the transition-safe search and comment-only population. A credentialed enforcing-PR run records the returned PR-number set, proves the enforcing PR appears exactly once, and quotes the actual distinct count without a speculative minimum.
- [ ] AC-08: The graph's typed state carries the base observation fields into `finalize_report`; the graph change has a committed authoring brief and valid authoring report, lint, and smoke evidence.
- [ ] AC-09: Direct tests cover marker field completeness/uniqueness, full digest lengths, UTC timestamp, placeholders, report round-trip, posted-body identity, no `docs/` writes, ignored `OUTSIDER_LEDGER`, non-comment exclusion, and comment-failure exclusion.
- [ ] AC-10: REQ-YG-662 and CAP-263 describe the new marker schema and comment-only inclusion rule with `fr: FR-995, FR-1004`; `ARCHITECTURE.md` is regenerated; every changed test has a REQ marker; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: FR-995 Proposed Solution 7, AC-11, and implementation record are annotated with the superseding storage/inclusion contract; its historical judgement and spike artifacts remain unchanged.
- [ ] AC-12: A RED commit precedes GREEN; `changelog/unreleased/fr-1004-retire-outsider-ledger.md` records a removal for REQ-YG-662; the FR implementation record cites both commits and the credentialed witness.
- [ ] AC-13: The dangling FR-998 citation is corrected or removed, and the diff contains none of the explicitly unauthorized surfaces.
- [ ] AC-14: One `docs/diary/2026-09-05-reflection-fr-1004-*.md` entry records the cognitive process and contains `**Seed:**`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into FR-1004 before implementation begins; the current claim that inclusion rules are unchanged grants no authority. | GATE |
| C-2 | Preserve manual, advisory operation and explicit `--comment`; automation and any blocking gate remain separate judged work. | GATE |
| C-3 | Parse and validate before constructing/posting the observation; a graph, parse, or comment failure must not become countable. | GATE |
| C-4 | Do not treat local `tmp/` reports as durable measurements; only successfully posted validated comments enter the distinct-PR population. | GATE |
| C-5 | Do not declare the replacement complete unless the credentialed GitHub search returns the enforcing PR exactly once. | GATE |
| C-6 | Modify `graph.yaml` only through the repository's graph-authoring route and retain its required report, lint, and smoke evidence. | GATE |
| C-7 | Preserve the existing outsider model, prompt, typed report parser, derived-verdict rule, external child cwd, recursion guard, and comment opt-in behavior. | GATE |
| C-8 | Complete RED/GREEN history, requirement traceability, changelog, FR records, and diary within D-1 through D-9. | GATE |

Authority granted: after R-1 through R-4 are folded into the FR, implement only D-1 through D-9 to replace the committed outsider ledger with a typed, searchable, successfully posted PR-comment observation.

---

## Second judgement (2026-09-05, S-8 scope amendment — `adapters/README.md`)

**Route:** `scripts/judge.sh feature-requests/FR-1004-retire-outsider-ledger.md` (Copilot backend, `gpt-5.6-sol`) on lane commit `9d7cfd6d`, 2026-09-05 15:49Z, requested by review #602 round 3 P3 after the README direct-invocation recipe was found broken by D-4. Folded verbatim below; R-1 and R-2 incorporated into the FR (status chronology, AC-15, README contract witness). The original judgement above is unchanged (C-8 of this judgement).

**Verdict:** APPROVED WITH REVISIONS — the `adapters/README.md` repair is the smallest coherent completion of the already-authorized graph-state change, but authority to retain that hunk activates only after the FR records that review requested rather than granted the amendment and adds a mechanical acceptance witness for the repaired recipe.

**Reviewed against:** `feature-requests/FR-1004-retire-outsider-ledger.md`; `feature-requests/FR-1004-retire-outsider-ledger.judgement.md`; `feature-requests/FR-995-outsider-reader.md`; `feature-requests/FR-995-outsider-reader.judgement.md`; `feature-requests/FR-858-retire-committed-fr-board.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.md`; `feature-requests/authoring-briefs/fr-1004-outsider-observation-brief.md`; `feature-requests/TEMPLATE.md`; `docs/diary/2026-08-23-the-worktree-is-the-airlock.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/outsider-view/SKILL.md`; `.github/skills/outsider-view/doctrine.md`; `.github/skills/outsider-view/adapters/README.md`; `.github/skills/outsider-view/adapters/graph.yaml`; `.github/skills/outsider-view/adapters/outsider_tools.py`; `scripts/outsider.sh`; `tests/unit/test_fr995_outsider_reader.py`; `tests/unit/test_fr995_outsider_wrapper.py`; `capabilities/CAP-263-outsider-reader.yaml`; `ARCHITECTURE.md`.

## What is sound

- **Scope:** the amendment is narrow and necessary. The original frozen D-5 names only `SKILL.md` and `doctrine.md` (`FR-1004-retire-outsider-ledger.judgement.md:61-71`), while the graph now requires five additional state inputs (`graph.yaml:8-17`) and the adapter README is the documented direct invocation. A smaller change cannot leave that command usable: omitting any of those inputs reaches `finalize_report`, which indexes them directly (`outsider_tools.py:312-345`).
- **Consistency of the technical contract:** S-8 precisely limits the repair to the five variables, input-closure explanation, and tracked-state wording, while preserving the model, prompt, parser, and verdict rule (`FR-1004:117-119`). The current README implements those exact three changes (`adapters/README.md:19-25,27-45`) and does not broaden behavior.
- **Measurability:** the proposed content is statically checkable: the direct command can be inspected for `repo`, `pr`, `head_sha`, `prompt_digest`, and `tool_sha`; the placeholder rule and model-input boundary are literal prose; and the tracked-state promise has an exact required phrase (`adapters/README.md:19-45`).
- **Feasibility:** the wrapper already supplies the five values (`scripts/outsider.sh:86-97`), the graph declares them (`graph.yaml:8-17`), and finalization consumes them (`outsider_tools.py:312-345`). Repairing the documentation requires no runtime, dependency, prompt, or graph change.
- **Architecture alignment:** FR-995 originally made `adapters/README.md` part of the outsider bundle (`FR-995-outsider-reader.judgement.md`, D-2), and the repository keeps operational invocation guidance beside each adapter. Updating that document when the graph input contract changes conforms to the existing bundle rather than creating a new surface.
- **Single responsibility:** this is one documentation-contract repair caused directly by D-4. It does not bundle the review's marker-attribution fixes, reducer fixes, or any new outsider behavior (`FR-1004:193-197`).
- **Strategic classification:** **Contrib/example (repo-local process instrument maintenance)**. The amendment maintains one existing adapter's operational documentation; it is not a framework primitive, new graph capability, or general documentation abstraction.
- **Testability:** a focused static test can fail solely when the README recipe or its three required explanations drift. Existing tests cover graph state and tracked-state wording in the script/tool module (`test_fr995_outsider_wrapper.py:190-215`) but do not cover the README, so one explicit witness is still required.
- **Research and precedent:** the parent FR contains a substantive seven-alternative disposition and answers `is_this_a_graph` honestly (`FR-1004:9,204-214`). The amendment itself is a defect discovered by review, not a new solution class requiring fresh external research.

## Required revisions

### R-1: Record amendment authority and chronology honestly

Replace the claim that a reviewer instruction amended the governed surface (`FR-1004:187-190`) with: the reviewer identified the broken direct-invocation contract and requested a second judgement; review did not grant scope authority. Keep the round-3 statement that P3 was routed to the judge (`FR-1004:193-197`).

Amend the status and implementation record (`FR-1004:5,140`) to distinguish the already-enforced ledger retirement from this pending scope amendment. Record that the README hunk was implemented before revised authority and is now submitted for retention review; this judgement does not retroactively authorize that sequence. Until this draft is human-reviewed and R-1/R-2 are folded, do not describe D-5 as amended or AC-13 as satisfied by the README hunk.

### R-2: Add a mechanical acceptance witness for the README repair

Add an unchecked acceptance criterion and one focused `REQ-YG-662` static test in `tests/unit/test_fr995_outsider_wrapper.py` that reads `.github/skills/outsider-view/adapters/README.md` and proves all of the following:

1. The direct-invocation command includes `--var` entries for `repo`, `pr`, `head_sha`, `prompt_digest`, and `tool_sha`.
2. The document states that non-PR runs use `-` for `repo`, `pr`, and `head_sha`.
3. The document states that only title/body reach the model and the five observation fields are consumed by Python finalization rather than the prompt.
4. The document uses the no-tracked-repository-state promise and does not claim that execution writes nothing under the repository.

Record this as the witness for the amended D-5 surface. Do not change runtime code to satisfy the documentation test.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Delete `docs/census/outsider-ledger.jsonl`; remove active ledger configuration, append, reducer, and output paths |
| D-2 | `.github/skills/outsider-view/adapters/outsider_tools.py`: typed observation marker, rendering/parsing, and deletion of ledger helpers |
| D-3 | `scripts/outsider.sh`: pass observation values, post the validated enriched body, remove `OUTSIDER_LEDGER`, and never write under `docs/` or mutate tracked state |
| D-4 | `.github/skills/outsider-view/adapters/graph.yaml`, FR-1004 authoring brief, and authoring report/lint/smoke evidence |
| D-5 | `.github/skills/outsider-view/{SKILL.md,doctrine.md}` plus `.github/skills/outsider-view/adapters/README.md`; README changes are limited to the five required observation variables, non-PR placeholders, title/body-only model boundary, Python-finalization handoff, and accurate tracked-state wording |
| D-6 | Focused renderer and wrapper tests in `tests/unit/test_fr995_outsider_reader.py` and `tests/unit/test_fr995_outsider_wrapper.py`, including the README contract witness required by R-2 |
| D-7 | `capabilities/CAP-263-outsider-reader.yaml`, generated `ARCHITECTURE.md`, and REQ-YG-662 traceability |
| D-8 | FR-995 active-contract annotations and FR-1004 implementation/status record, including the credentialed comment/search witness and honest amendment chronology |
| D-9 | FR-1004 removal changelog fragment and one metacognitive diary entry |

Not authorized: any README rewrite beyond the five-variable recipe and the two directly coupled explanations; runtime behavior changes; automatic invocation or comments; CI, hook, pre-commit, merge-gate, or workflow changes; a blocking outsider verdict; model, prompt, report parser, marker parser, reducer, or derived-verdict changes; edits to historical spike outputs or historical PR comments; deletion of other census artifacts; a new query service or subcommand; judge/review doctrine changes.

## Revised acceptance criteria

- [ ] AC-01: `docs/census/outsider-ledger.jsonl` is deleted, and `git grep -n ledger -- scripts/outsider.sh .github/skills/outsider-view` returns no active ledger implementation or instruction.
- [ ] AC-02: Every rendered report carries one typed marker with exactly one UTC timestamp, repo, PR, full head SHA, full input SHA-256, model, prompt digest, tool SHA, derived verdict, s3, and s4; it contains no `source:` or local temp path. Non-PR reports use the specified placeholders and are not countable.
- [ ] AC-03: `report_path` is explicitly recorded as retired in FR-1004 and FR-995; no active text claims that all old fields or inclusion rules are unchanged.
- [ ] AC-04: No mode of `scripts/outsider.sh` creates or modifies a path under `docs/` or any tracked file. Validated local reports/logs may remain under git-ignored `tmp/`; `OUTSIDER_LEDGER` has no effect and is absent from active code.
- [ ] AC-05: `pr --comment` posts exactly the enriched validated report; a fake captures `--body-file` and proves its full head/input values match the fake `gh pr view` result and fetched text. Comment failure exits non-zero and creates no durable measurement record.
- [ ] AC-06: A non-comment PR run writes its validated local report under `tmp/` but is excluded from the count. `--input`, `--selftest`, graph failures, parse failures, and comment failures are also excluded.
- [ ] AC-07: `SKILL.md` and doctrine document the complete-marker reducer and comment-only population. A credentialed enforcing-PR run records the returned PR-number set, proves the enforcing PR appears exactly once, and quotes the actual distinct count without a speculative minimum.
- [ ] AC-08: The graph's typed state carries the base observation fields into `finalize_report`; the graph change has a committed authoring brief and valid authoring report, lint, and smoke evidence.
- [ ] AC-09: Direct tests cover marker completeness/uniqueness, digest lengths, UTC shape, placeholders, round-trip, marker attribution, posted-body identity, no `docs/` writes, no tracked-file mutation, ignored `OUTSIDER_LEDGER`, non-comment exclusion, comment-failure exclusion, and CRLF marker handling.
- [ ] AC-10: REQ-YG-662 and CAP-263 describe the marker schema and comment-only inclusion rule with `fr: FR-995, FR-1004`; `ARCHITECTURE.md` is regenerated; every changed test has a REQ marker; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: FR-995 Proposed Solution 7, AC-11, and implementation record carry the superseding storage/inclusion contract; its historical judgement and spike artifacts remain unchanged.
- [ ] AC-12: RED precedes GREEN for behavioral implementation; `changelog/unreleased/fr-1004-retire-outsider-ledger.md` records a removal for REQ-YG-662; the FR implementation record cites the commits and credentialed witness.
- [ ] AC-13: The final diff touches only D-1 through D-9 as amended here. The FR records that the README hunk preceded revised authority and does not represent reviewer instruction as judge approval.
- [ ] AC-14: One `docs/diary/2026-09-05-reflection-fr-1004-*.md` entry records the cognitive process and contains `**Seed:**`.
- [ ] AC-15: `adapters/README.md` documents all five required observation variables, the three non-PR placeholders, title/body-only model input, Python-finalization consumption, and the accurate no-tracked-state promise; a focused `REQ-YG-662` test checks those statements and forbids the false no-write claim.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 and R-2 into FR-1004 before treating the README hunk as within frozen scope; reviewer findings do not amend judge authority. | GATE |
| C-2 | Human review of this draft is required before authority activates; until then the output is advisory. | GATE |
| C-3 | Limit the README repair to the direct graph-input contract and its two coupled explanations; make no runtime, prompt, parser, reducer, or verdict change. | GATE |
| C-4 | Preserve manual, advisory operation and explicit `--comment`; automation and any blocking gate remain separate judged work. | GATE |
| C-5 | Preserve title/body-only model input: observation metadata may enter graph state and Python finalization but must not enter the outsider prompt. | GATE |
| C-6 | Keep the original C-3 through C-8 enforcement conditions in force for the ledger retirement; this amendment relaxes only the D-5 file boundary. | GATE |
| C-7 | Add the R-2 regression witness under existing REQ-YG-662 traceability and do not alter production code merely to satisfy a documentation assertion. | GATE |
| C-8 | Record the amendment chronology without rewriting the historical original judgement or review findings. | GATE |

Authority granted: after human review and after R-1 and R-2 are folded into the FR, retain only the narrowly described `adapters/README.md` repair, its focused regression witness, and the corresponding FR status/history update; all other original scope boundaries remain frozen.
