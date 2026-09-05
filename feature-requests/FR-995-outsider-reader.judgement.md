# Judgement: FR-995 Outsider reader — an adversarial third reader for PR (and FR) descriptions

**Verdict:** APPROVED WITH REVISIONS — the context-free reader is a proven, bounded repo-local process instrument, but authority activates only after the FR repairs its impossible calibration criteria, defines a typed fail-closed report boundary, makes ledger observations attributable, and aligns the promised result with manual-only scope.

**Prior art:** [FR-995-outsider-reader.md](FR-995-outsider-reader.md) — the subject; its own `**Prior art:**` line dispositions judge-fr, review-pr, `scripts/review.sh`, FR-742 and the human-skims diary. [FR-594-l5-prose-regenerability-measurement-graph.md](FR-594-l5-prose-regenerability-measurement-graph.md) — noun collision only: its single "outsider-view" mention names a plot-modeller goals-doc reframing, not a PR reader; no overlap.

**Reviewed against:**

- `feature-requests/FR-995-outsider-reader.md`
- `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/skills/judge-fr/SKILL.md`
- `.github/copilot-instructions.md`, `feature-requests/TEMPLATE.md`
- `.github/skills/graph-authoring/doctrine.md`, `.github/skills/graph-authoring/adapters/README.md`
- `.github/skills/review-pr/doctrine.md`, `.github/skills/review-pr/SKILL.md`, `.github/skills/review-pr/adapters/README.md`, `.github/skills/review-pr/adapters/graph.yaml`, `scripts/review.sh`
- `feature-requests/FR-742-undelivered-diary-detection.md`, `feature-requests/FR-990-cap-journey-census.md`
- `docs/2026-09-05-research-plan-cap-journey-census.md` §§11–12
- `docs/diary/diary-2026-07-16-the-human-skims.md`, `docs/diary/diary-2026-09-05-the-recap-nobody-outside-could-read.md`, `docs/diary/2026-09-05-reflection-fr-990-the-junk-drawer-moved-when-i-reworded-it.md`
- `docs/spikes/outsider-reader-2026-09-05/graph.yaml`, `tools.py`, `outsider.sh`, `EXPECTATIONS.md`, `prompts/outsider.yaml`, `prompts/outsider.v1.yaml`
- `docs/spikes/outsider-reader-2026-09-05/inputs/pr-591.md`, `plain-591.md`, `pr-591-v2.md`, `fr-995.md`
- `docs/spikes/outsider-reader-2026-09-05/out/pr-591-gpt-5.6-sol-20260905T050922Z.md`, `plain-591-gpt-5.6-sol-20260905T051018Z.md`, `pr-591-v2-gpt-5.6-sol-20260905T052431Z.md`, `pr-591-gpt-5.6-sol-20260905T052458Z.md`, `plain-591-gpt-5.6-sol-20260905T052521Z.md`, `fr-995-gpt-5.6-sol-20260905T054043Z.md`

## What is sound

- **The problem and first handoff are evidenced.** The FR names the author and reviewer at a concrete PR-open/review moment (`FR-995:8,20`), and the cited incident shows that author-side plain-language guidance did not catch the author's own private vocabulary (`FR-995:24-26`; `docs/2026-09-05-research-plan-cap-journey-census.md:403-413`).
- **The raw-output requirement is satisfied in substance.** Six committed reports were read, and the FR records specific surprises: v1 count inversion, a false model YES, an actual title/body mismatch, and the unlinked-versus-absent split (`FR-995:28-37`; research plan `:468-519,538-624`). This is analysis rather than an inventory.
- **The architecture starts from working precedent.** The spike proves the model pin, clean working directory, four-section prompt, and artifact-over-exit-code wrapper (`research plan:415-454`; `FR-995:47-52`). The proposed authoring route also conforms to the graph-authoring requirement that copied graphs still pass through a committed brief, lint, smoke, and artifact report (`.github/skills/graph-authoring/doctrine.md:11-17,19-27,69-88,91-107`).
- **The role boundary is appropriately narrow.** The outsider lists comprehension gaps, the reviewer partitions merge needs, and no model output approves, merges, or blocks (`FR-995:16,49,52,85-91`; research plan `:563-576`). The optional comment is delivery, not authority.
- **Prior art and alternatives are dispositioned.** Judge, reviewer, wrapper, successor briefing, vendor summary, cheaper-model, model-verdict, gate, and FR-target alternatives are distinguished (`FR-995:10,83-91`).
- **Single responsibility and strategic classification:** this is one concern—an advisory, context-free reading of PR descriptions. It is a **Contrib/example (repo-local process instrument)**: one target class with a demonstrated gap in the existing context-rich reviewer, implemented using existing YAMLGraph and wrapper abstractions rather than a new framework primitive.

## Required revisions

### R-1: Calibrate the derived verdict against at least one real positive

Keep the proposed rule—YES only when section 3 has at most two items and section 1 contains no configured hedge marker—but make every claim and fixture agree with it. The committed rewritten report has five section-3 items and the hedge “the text does not say,” so it is NO under that rule (`out/pr-591-v2-…md:5,13-19`), despite Proposed Solution 5 and AC-3 calling it YES (`FR-995:51,59`). The dogfood report has eight items, so correct its recorded verdict from YES to NO (`FR-995:68-75`; `out/fr-995-…md:13-22`).

Add a committed final-glossed input and an actual `gpt-5.6-sol` output that satisfies the unchanged rule; write its expectation before running it. The self-test set must then classify original body NO, plain account NO, pre-gloss rewritten body NO, and final-glossed body YES. Do not loosen the threshold merely to fit the observed 8/6/5 sequence: the evidence itself says count alone is weak (`EXPECTATIONS.md:30-34`; research plan `:609-616`).

### R-2: Define a typed, fail-closed report and derivation boundary

Replace “small python tool node” with an explicit contract. Normalize the model text into a Pydantic model containing: non-empty section-1 restatement; model opinion `YES | NO` plus reason; zero-to-eight section-3 items with quote and question; and zero-to-ten section-4 items. Require all four numbered headings exactly once and in order; define `nothing` as an empty list; reject missing, duplicate, reordered, over-cap, or malformed sections.

Compute the derived verdict only from that validated model, with case-insensitive hedge matching. Emit a front-loaded `**Derived verdict:** YES|NO` and label section 2 as the model's non-authoritative opinion. A parse/shape failure must produce a non-zero wrapper result and must not comment or append a ledger row. Add direct tests for every failure class. This repairs the spike's untyped `dict[str, Any]` boundary (`docs/spikes/outsider-reader-2026-09-05/graph.yaml:12-17`; `tools.py:10-25`) and satisfies the repository's Pydantic boundary law (`.github/copilot-instructions.md:16,47,192`).

### R-3: Make each ledger observation attributable and non-gameable

Define “per run” as one successfully parsed, artifact-validated invocation against a real GitHub PR. Each JSONL row must contain UTC timestamp, repository and PR number, PR head SHA, SHA-256 of the exact title-plus-body input, pinned model, prompt/adapter version or digest, local tool git SHA, derived verdict, section-3 count, section-4 count, and report path. Append while the wrapper lock is held and only after report validation.

Self-tests, dry runs, parse failures, graph failures, and comment failures must not create measurement rows. “Twenty rows before a gate” means twenty distinct PRs, using at most the latest successful observation per PR—not twenty reruns of one PR. Tests must prove those inclusion, exclusion, and duplicate semantics. The current five-field row (`FR-995:53,63`) identifies neither the exact PR text nor a distinct observation.

### R-4: Align the ideal result and first event with manual-only scope

Rewrite the Ideal Result and Summary so this FR promises a manually invoked advisory report after a PR is opened, not that every `feat`/`fix` PR automatically receives a comment within one minute (`FR-995:16,39-41`). State automatic invocation as a separate future FR, independently of the blocking-gate decision; Alternative 6 currently defers only blocking (`FR-995:90`) and cannot carry automation by implication.

Keep `--comment` explicit and off by default. No workflow, hook, scheduled service, automatic PR-open invocation, or mandatory review step is authorized here.

### R-5: Close the artifact and test surface

Enumerate the complete implementation boundary in the FR:

- `.github/skills/outsider-view/SKILL.md` with discovery frontmatter and the manual invocation;
- `doctrine.md`, `adapters/README.md`, `adapters/graph.yaml`, `adapters/prompts/outsider.yaml`, and the exact Python tool module used for parsing, derivation, report writing, and ledger append;
- committed `feature-requests/authoring-briefs/fr-995-outsider-reader-brief.md`, cited by the FR, naming every graph artifact;
- `scripts/outsider.sh`, fixtures, focused unit tests, capability/REQ registration, changelog fragment, FR implementation record, and diary entry.

Replace “README follows the judge/review shape” with assertions: it documents the sole manual command, input closure, artifact path, derived-versus-model verdict distinction, advisory status, and forbidden actions. Add wrapper tests proving that absolute repo paths resolve while the child process cwd is an external directory with no `.github/`, temporary input is removed on success and failure, the report survives under repo `tmp/`, the lock/sentinel serialize runs, and `--comment` is the only path that calls `gh pr comment`. Existing skill precedent includes a `SKILL.md` discovery wrapper (`.github/skills/review-pr/SKILL.md:1-12,23-40`), while the current proposed skill list omits it (`FR-995:47`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/skills/outsider-view/SKILL.md` and `doctrine.md` |
| D-2 | `.github/skills/outsider-view/adapters/{README.md,graph.yaml,prompts/outsider.yaml,<typed-tool-module>}` |
| D-3 | `feature-requests/authoring-briefs/fr-995-outsider-reader-brief.md` and `tmp/draft-authoring-report.md` as authoring-route evidence |
| D-4 | `scripts/outsider.sh` manual wrapper with lock, lineage sentinel, clean external cwd, cleanup, artifact validation, and opt-in comment |
| D-5 | `.github/skills/outsider-view/fixtures/` containing the historical canaries plus one evidenced final-glossed positive |
| D-6 | Focused unit/wrapper tests under `tests/` |
| D-7 | `docs/census/outsider-ledger.jsonl` with the R-3 schema and semantics |
| D-8 | One new `capabilities/CAP-*.yaml` record, its `ARCHITECTURE.md` REQ, and tagged tests |
| D-9 | Changelog fragment, FR implementation/status update, and one `docs/diary/` reflection |
| D-10 | Existing committed spike directory retained as reference evidence; FR dogfood report/comment citation corrected |

Not authorized: GitHub Actions or other automatic PR-open invocation; CI, pre-commit, or hook changes; a blocking gate; automatic comments; FR-body input; changes to judge/review doctrine or execution; graph-authoring guard changes; model comparison or model selection logic; rewriting PR descriptions; merge/approval actions; edits that rewrite the historical spike outputs.

## Revised acceptance criteria

- [ ] AC-01: The FR cites `feature-requests/authoring-briefs/fr-995-outsider-reader-brief.md`; `scripts/author.sh` produces the named graph/prompt/tool artifacts and a valid `tmp/draft-authoring-report.md`; the authored graph passes `yamlgraph graph lint` and a recorded smoke attempt.
- [ ] AC-02: The skill bundle contains `SKILL.md`, doctrine of at most 60 lines, adapter README, graph, prompt, and typed tool module. The docs state the manual command, title-plus-body-only input closure, three-reader division, derived/model verdict distinction, advisory boundary, artifact path, and forbidden actions.
- [ ] AC-03: The adapter pins `gpt-5.6-sol` literally and contains neither `allow_all_paths` nor `allow_all_tools`. A wrapper test proves the child cwd is outside the repository and contains no `.github/`, while absolute graph/tool/report paths still resolve.
- [ ] AC-04: The wrapper fetches title, body, and PR head SHA; holds one repo-scoped directory lock; rejects recursive execution; removes temporary input on success, graph failure, and parse failure; preserves the validated report under repo `tmp/`; and validates the complete report contract rather than only the section-1 heading.
- [ ] AC-05: Model text is normalized into the R-2 Pydantic model. Missing, duplicate, reordered, malformed, and over-cap sections fail closed; no failed run comments or writes a ledger row.
- [ ] AC-06: The derived verdict is case-insensitively computed as section-3 count `<= 2` and absence of all four hedge markers. The report front-loads that verdict and clearly labels the model's section-2 answer as opinion.
- [ ] AC-07: Tests classify all six historical reports as NO under the derived rule and one newly committed final-glossed model report as YES. The FR dogfood record says the eight-item pre-fix report derived NO and links the actual PR comment plus each item's disposition.
- [ ] AC-08: `scripts/outsider.sh --selftest` runs original, plain-account, pre-gloss rewritten, and final-glossed fixtures and requires derived `NO/NO/NO/YES`; expectations for the new positive are committed before its output.
- [ ] AC-09: A credentialed `scripts/outsider.sh 591` smoke writes a structurally valid report from the current GitHub title/body. Its observed counts and verdict are recorded without changing the fixed unit expectations if the model drifts.
- [ ] AC-10: `--comment` is off by default. Mocked wrapper tests prove only explicit `--comment` posts exactly the validated report to the requested PR and that no self-test, dry run, or failed run posts.
- [ ] AC-11: Each successful real-PR run appends exactly one locked JSONL row with every R-3 field. Tests prove excluded modes/failures write none and repeated PR runs cannot satisfy the twenty-distinct-PR prerequisite.
- [ ] AC-12: A new capability record and `ARCHITECTURE.md` requirement cover the feature; every test has the matching `@pytest.mark.req`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-13: The spike directory remains unchanged as historical evidence and is cited from the skill README; a changelog fragment, FR implementation/status record, and metacognitive diary entry are added.
- [ ] AC-14: The diff contains none of the explicitly unauthorized surfaces.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into `feature-requests/FR-995-outsider-reader.md` before production implementation begins; the contradictory current AC-3 grants no authority. | GATE |
| C-2 | Author graph and prompt artifacts only through the committed brief and `scripts/author.sh`; verify the authoring report, lint, and smoke artifacts rather than an exit code. | GATE |
| C-3 | Preserve inverted input closure: the model receives only the fetched PR title and body, runs from the tested external cwd, and has no path/tool grants. | GATE |
| C-4 | Parse and validate before deriving, commenting, or recording; malformed or absent output must fail closed. | GATE |
| C-5 | Keep invocation and commenting manual and advisory; automation and blocking require separate judged authority after twenty distinct attributable PR observations. | GATE |
| C-6 | Do not count fixtures, reruns of one PR, or failed runs toward the twenty-PR evidence threshold. | GATE |
| C-7 | Do not edit judge/review doctrine, CI, hooks, graph-authoring guards, or the historical spike outputs under this FR. | GATE |
| C-8 | Complete TDD, requirement traceability, changelog, FR status, and diary obligations within the frozen surfaces. | GATE |

Authority granted: after R-1 through R-5 are folded into the FR, implement the manual, advisory PR-description outsider reader and only the deliverables D-1 through D-10 above.
