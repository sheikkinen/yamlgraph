# Judgement: FR-870 Constitution Diff -- Spec Kit vs Scripture

**Verdict:** APPROVED WITH REVISIONS -- the comparative docs experiment is worth doing, but authority activates only after the FR defines a contamination-controlled input corpus, reproducible Spec Kit invocation, and an exhaustive classification taxonomy.

**Reviewed against:** `feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/origin-story.md`; `docs/diary/diary-2026-08-23-identity-by-the-nearest-neighbors-missing-organ.md`; `docs/memento/feature-requests/040-default-quality-gates.md`; `feature-requests/FR-866-ramp-tailoring-graphs.md`; `feature-requests/FR-866-ramp-tailoring-graphs.judgement.md`; GitHub `github/spec-kit` README at SHA `b9b3243520cac52182c8ea89c4354ec36fa57cd5`; GitHub `github/spec-kit` `docs/quickstart.md` at SHA `fb2ecc2f744202c1dd9862df9151230d078ac097`; GitHub `github/spec-kit` `docs/guides/existing-projects.md` at SHA `479715546e884aa09bea500896a672b64644f423`; GitHub `github/spec-kit` `docs/reference/agentic-sdd.md` at SHA `dc38e76a5acbe75148dcfd4f9dfa4eae40600c59`. No author chat narrative was consumed.

**Prior art:** the sole noun-match is the judged FR itself (`FR-870-constitution-diff-speckit-vs-scripture.md`) — self-reference, no external precedent to disposition. Adjacent precedents are dispositioned in the FR's Alternatives/Related sections: FR-866 (transplant fidelity — kept disjoint), memento FR-040 (LLM-as-judge classification — rejected route honored by hand classification).

## What is sound

The problem is real and bounded. `docs/origin-story.md` claims the divergence from Spec Kit is the independent judge and case-law model: Spec Kit has no independent judge and its specs are launch documents rather than binding rejected case law (`docs/origin-story.md:449-456`). FR-870 turns that rhetorical claim into a falsifiable artifact by diffing generated constitution text against the Scripture (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:23-39`).

The first consumer and first event are explicit enough for a docs/research FR: the origin-story essay needs a concrete exhibit before making the claim that incident-paid law cannot be generated (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:8-11`). The cited diary independently records this proposal as the fourth ranked next step and states the intended use: a concrete exhibit for the essay and a fitness check on written law (`docs/diary/diary-2026-08-23-identity-by-the-nearest-neighbors-missing-organ.md:77-82`).

The proposed deliverable is appropriately small. One document, `docs/constitution-diff.md`, plus a one-line cross-link in `docs/origin-story.md` is a pattern-documentation/research exhibit, not a framework primitive (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:45-53`, `81-87`). The FR correctly rejects adopting Spec Kit, writing tooling, automating classification, or changing the Scripture under this scope (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:84-87`).

The scratch-worktree instinct is aligned with local doctrine. The Scripture warns that workspace visibility is not ownership and records `one_session_one_repo` as the cure for shared-index/worktree contamination (`.github/copilot-instructions.md:63-65`, `109-110`, `163-163`). FR-870 already requires an isolated scratch copy and forbids committing Spec Kit scaffolding (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:59-61`, `96-99`).

Strategic classification: **Pattern documentation / research exhibit**. There is one named consumer and no new runtime abstraction; the value is the measured external comparison.

## Required revisions

### R-1: Define a contamination-controlled input corpus

Replace "against this repository" with an exact allow-list and deny-list for the Spec Kit run. The FR's own neutral prompt says the generator should derive principles from "codebase, tests, and CI configuration" (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:66-68`), but the scratch copy would also contain the target answer, `.github/copilot-instructions.md`, which the summary names as the actual written law being compared (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:15-17`). If the agent can read the Scripture, the experiment measures leakage, not rediscovery.

Fold this by requiring a sanitized scratch copy before `/speckit.constitution` runs. The FR must name forbidden inputs at minimum: `.github/copilot-instructions.md`, `.github/skills/`, `feature-requests/`, `docs/diary/`, `docs/origin-story.md`, any prior `docs/constitution-diff.md`, and generated judge/review artifacts. It must name the allowed corpus explicitly, e.g. source code, tests, CI workflows, packaging metadata, and non-doctrine reference docs if the author intentionally includes them. `docs/constitution-diff.md` must include the input manifest and the sanitation command/log so a reader can verify what the generator could and could not see.

### R-2: Make the Spec Kit invocation reproducible and compatible with existing-project setup

Revise the setup command and provenance requirements. FR-870 currently proposes `uvx --from git+https://github.com/github/spec-kit.git specify init --here` (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:62-66`), but Spec Kit's existing-project guide says `--here` targets the current directory, `--force` is needed for a non-empty directory, and an integration key is chosen during init (`docs/guides/existing-projects.md` in `github/spec-kit` SHA `479715546e884aa09bea500896a672b64644f423`). The README also documents non-interactive initialization flags for agent harnesses (`github/spec-kit` README SHA `b9b3243520cac52182c8ea89c4354ec36fa57cd5`, lines 153-158 in the fetched artifact).

Fold this by pinning the Spec Kit version or commit SHA in the FR, naming the exact install/init command, including `--force`, `--non-interactive`, and `--integration copilot` or another explicit integration, and recording both the Specify CLI version and the generated command surface in the final document. Correct the generated constitution path to the actual Spec Kit managed path if needed: the Spec Kit monorepo guide describes `.specify/memory/constitution.md`, while FR-870 currently names `memory/constitution.md` (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:70-71`).

### R-3: Replace the ambiguous three-label taxonomy with two reconciled inventories

Define exhaustive labels for both sides of the diff. FR-870 says every clause of the Scripture will be classified as REDISCOVERED, GENERIC-MISSED, or INCIDENT-PAID (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:15-21`, `47-51`), but later says the Scripture walk uses only REDISCOVERED / INCIDENT-PAID while generated clauses we lack are tagged GENERIC-MISSED (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:72-78`). That leaves no legal label for a generic Scripture clause the generator does not rediscover, and it mixes source-side and generator-only findings in one denominator.

Fold this by requiring two tables: (1) a Scripture-unit table where every source unit has exactly one source-side label such as `REDISCOVERED`, `SOURCE_ONLY_INCIDENT_PAID`, or `SOURCE_ONLY_UNTRACED_GENERIC`; and (2) a generated-only table for Spec Kit clauses absent from the Scripture, such as `GENERATOR_ONLY_GENERIC_MISSED` or `GENERATOR_ONLY_REJECTED`. The FR may choose different names, but the labels must be mutually exclusive, collectively exhaustive, and must not reuse one label for both source-side and generator-only meanings.

### R-4: Define the normative-unit inventory before classification starts

Make "every normative unit of the Scripture" countable. The FR's proposed walk includes the 10 Commandments, traps, cures, questions, generative methods, process rules, and conventions (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:72-75`), but `.github/copilot-instructions.md` also contains boundaries, seeds, the Sermon of the Chaplain, Rite of Correction, and the Agents' prayer (`.github/copilot-instructions.md:54-65`, `165-171`, `229-258`). Without a manifest, a plausible-looking table can omit whole families while still satisfying the shape check.

Fold this by requiring a "source-unit manifest" section in `docs/constitution-diff.md` before the classification table. The manifest must list included and excluded Scripture sections, stable unit IDs, the total source-unit count, and a count reconciliation proving every included unit appears exactly once in the classification table. Any excluded section must have a one-sentence reason, e.g. "seeds are forward-looking backlog, not governing law."

### R-5: Add evidence standards for REDISCOVERED and INCIDENT-PAID rows

Specify what counts as equivalence and what counts as incident-paid. The FR correctly requires every INCIDENT-PAID row to cite a graduating diary entry or FR (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:76-78`, `95-95`), and the Scripture itself says its trap/cure registry is graduated from diary patterns (`.github/copilot-instructions.md:45-49`). But the acceptance criteria do not require REDISCOVERED rows to quote the generated clause, and they do not say what happens when a source clause lacks a traceable incident citation.

Fold this by requiring each REDISCOVERED row to cite or quote the generated constitution clause that makes it equivalent, each INCIDENT-PAID row to cite an existing FR/diary/witness from the source text or cited corpus, and each uncited source-only row to remain out of the incident-paid numerator. This preserves Commandment 6's "plausible wrong answer is harder to catch than a crash" rule (`.github/copilot-instructions.md:219-219`) and the judge doctrine's demand for file/line evidence on findings (`.github/skills/judge-fr/doctrine.md:34-61`).

### R-6: Convert the cleanup and no-scaffolding checks into concrete evidence

Make the "scratch removed" and "zero scaffolding committed" acceptance criteria mechanically checkable. FR-870 requires no `memory/`, `.specify/`, or `.speckit*` files committed and a clean worktree prune (`feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md:96-99`), but does not say what evidence the enforcer must record. This matters because Spec Kit initialization explicitly adds `.specify/` project files for existing projects (`docs/guides/existing-projects.md` in `github/spec-kit` SHA `479715546e884aa09bea500896a672b64644f423`).

Fold this by requiring `docs/constitution-diff.md` or the FR implementation record to include the exact outputs of `git --no-pager diff --name-only`, `git worktree list`, and `git worktree prune --dry-run` or equivalent evidence proving only the authorized docs files changed and no scratch worktree remains registered.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md` folding R-1 through R-6 |
| D-2 | Sanitized scratch-worktree run of Spec Kit, with generated constitution captured verbatim |
| D-3 | `docs/constitution-diff.md` containing provenance, input manifest, generated constitution, source-unit manifest, two reconciled classification tables, measured fractions, conclusion, and cleanup evidence |
| D-4 | One-line link from `docs/origin-story.md` External Record to `docs/constitution-diff.md` |
| D-5 | FR implementation-status update with command/provenance notes and any deviations |

Not authorized: changing `.github/copilot-instructions.md`, judge/review/authoring doctrine, hooks, CI, capabilities, runtime code, graph artifacts, prompts, Spec Kit scaffolding in the live repo, sibling repositories, or any generated governance artifact other than `docs/constitution-diff.md`. Not authorized: adopting Spec Kit output into the Scripture, automating the classifier, re-running the experiment on other repositories, or claiming the essay thesis is proven from contaminated input.

## Revised acceptance criteria

- [ ] AC-01: FR-870 is revised to define the sanitized input allow-list/deny-list, exact Spec Kit version/commit and invocation, classification taxonomy, source-unit manifest rules, row evidence standards, and cleanup evidence required by R-1 through R-6.
- [ ] AC-02: The Spec Kit run occurs only in a scratch worktree or copied scratch directory, after removing or hiding the forbidden doctrine/history inputs named by the FR.
- [ ] AC-03: `docs/constitution-diff.md` records provenance: date, operator/agent, model/provider, Spec Kit version or commit SHA, init command, `/speckit.constitution` prompt, generated constitution path, and sanitized input manifest.
- [ ] AC-04: `docs/constitution-diff.md` includes the generated constitution verbatim before any analysis.
- [ ] AC-05: `docs/constitution-diff.md` includes a source-unit manifest listing included and excluded Scripture sections, stable unit IDs, total count, and count reconciliation.
- [ ] AC-06: Every included source unit appears exactly once in the Scripture classification table with one exhaustive source-side label.
- [ ] AC-07: Every REDISCOVERED row cites or quotes the generated constitution clause used as evidence of equivalence.
- [ ] AC-08: Every source-side INCIDENT-PAID row cites a graduating diary entry, FR, or source-text witness; uncited source-only rows are not counted as incident-paid.
- [ ] AC-09: Every generated clause absent from the source Scripture appears in a separate generated-only table with one exhaustive generator-side label.
- [ ] AC-10: The measured fractions state numerator, denominator, and label family, separating source-side rediscovery/incident-paid rates from generated-only findings.
- [ ] AC-11: `docs/constitution-diff.md` concludes in no more than three sentences and explicitly states whether the result strengthens, weakens, or invalidates the origin-story claim.
- [ ] AC-12: `docs/origin-story.md` External Record links to `docs/constitution-diff.md` in one line and makes no broader claim than the measured result supports.
- [ ] AC-13: No Spec Kit scaffolding files (`.specify/`, `memory/`, `.speckit*`, integration command files) are committed to the live repo unless separately authorized by a future FR.
- [ ] AC-14: The implementation record or `docs/constitution-diff.md` includes cleanup evidence showing the scratch worktree/directory was removed or is outside the repository and only authorized docs/FR files changed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-6 are folded into `feature-requests/FR-870-constitution-diff-speckit-vs-scripture.md`. | GATE |
| C-2 | Do not run Spec Kit against a corpus that contains `.github/copilot-instructions.md`, `.github/skills/`, `feature-requests/`, `docs/diary/`, or `docs/origin-story.md`; contaminated output may be archived as a failed run but must not be used for the measured fractions. | GATE |
| C-3 | Do not invoke or re-run the judge while enforcing this FR. | GATE |
| C-4 | Do not modify the Scripture, judge/review/authoring doctrine, hooks, CI, runtime code, graph artifacts, or prompts under this FR. | GATE |
| C-5 | Do not commit Spec Kit scaffolding or leave a registered scratch worktree behind. | GATE |
| C-6 | If an external LLM/provider is used, restrict inputs to the sanitized committed corpus and do not include secrets, untracked files, ignored files, sibling repositories, or private local notes. | GATE |
| C-7 | If the Spec Kit run fails or cannot produce a constitution from the sanitized corpus, the deliverable must report the failed experiment and stop; do not substitute the template constitution or an unsanitized run. | GATE |

Authority granted: after the required revisions are folded, enforcement may run the sanitized Spec Kit constitution experiment and publish only the measured docs exhibit plus the origin-story cross-link.
