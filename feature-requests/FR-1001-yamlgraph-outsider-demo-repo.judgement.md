# Judgement: FR-1001 `yamlgraph-outsider` standalone demo repository

**Verdict:** APPROVED WITH REVISIONS — the standalone repository is a sound contrib/example, but authority activates only after the FR makes graph failure necessary to wrapper failure, restores an exact typed report/reducer boundary, closes dangling evidence, states the sample model choice truthfully, and records human approval for paid live runs and the external PR comment.

**Prior art:** [FR-1001-yamlgraph-outsider-demo-repo.md](FR-1001-yamlgraph-outsider-demo-repo.md) — the subject; its `**Prior art:**` line dispositions FR-995, FR-865, FR-998, FR-1004. Second judgement: the first (same file, superseded) covered a plan with a run ledger and a shell-owned `gh` path.

**Reviewed against:** `feature-requests/FR-1001-yamlgraph-outsider-demo-repo.md`; `feature-requests/FR-1001-yamlgraph-outsider-demo-repo.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `feature-requests/TEMPLATE.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/outsider-view/SKILL.md`; `.github/skills/outsider-view/doctrine.md`; `.github/skills/outsider-view/adapters/README.md`; `feature-requests/FR-995-outsider-reader.md`; `feature-requests/FR-995-outsider-reader.judgement.md`; `feature-requests/FR-865-ramp-installer.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.judgement.md`; `docs/2026-09-05-research-plan-cap-journey-census.md` sections 12-13; `docs/spikes/outsider-llm-2026-09-05/{graph.yaml,tools.py,yamlgraph-outsider,EXPECTATIONS.md}`; `docs/spikes/outsider-llm-2026-09-05/prompts/outsider.yaml`; `docs/spikes/outsider-llm-2026-09-05/inputs/{pr-591.md,plain-591.md,pr-591-v2.md,positive.md}`; the six committed reports `docs/spikes/outsider-llm-2026-09-05/out/{positive-claude-sonnet-4-5-20260905T080348Z.md,positive-claude-sonnet-4-5-20260905T080409Z.md,pr-591-claude-sonnet-4-5-20260905T080437Z.md,plain-591-claude-sonnet-4-5-20260905T080503Z.md,pr-591-v2-claude-sonnet-4-5-20260905T080533Z.md,592-claude-sonnet-4-5-20260905T080708Z.md}`; `reference/cli.md`; `reference/graph-yaml.md`; and `reference/development-operations.md`. `FR-1004` was named by FR-1001 but no committed `feature-requests/FR-1004*` artifact exists in the reviewed tree, so it was not consumed. The referenced GitHub PR comments were not consumed because they are not committed artifacts.

## What is sound

| Criterion | Finding |
|---|---|
| Scope | The proposal is bounded to one public demo repository plus one discoverability link in this repository; runtime changes, ramp inclusion, and automatic invocation are excluded (`FR-1001:46-63,87-94`). A smaller plain-Python program would not satisfy the stated YAMLGraph demonstration purpose, while the cited three-node spike already proves the intended shape (`research plan:629-694`). |
| Consistency | The amended plan has removed the run ledger, separated transient `out/` files from committed `docs/evidence/`, and made the graph own GitHub side effects (`FR-1001:46-63`). The remaining contradictions are narrow and mechanically repairable in R-1 through R-4. |
| Measurability | Most criteria name exact commands, files, subprocess argument lists, negative paths, and observable results (`FR-1001:67-82`). The fake-command tests, parsed-graph checks, two-pass live sequence, and clean-environment run are substantially stronger than proxy grep alone. |
| Feasibility | The committed spike ran the same Python -> `llm` -> Python topology end to end, produced six structurally valid reports, and posted one real comment in about 25 seconds (`research plan:639-689`; `EXPECTATIONS.md:9-25`). The proposed graph uses existing `llm` and Python-node primitives rather than adding framework behavior. |
| Architecture alignment | The wrapper is presentation, the graph owns orchestration, and Python tools own GitHub/file side effects (`FR-1001:47-48`), matching the repository's three-layer convention. The committed brief, adapter route, lint, smoke, and separate Git root satisfy graph-authoring and workspace boundaries (`graph-authoring doctrine:9-17,19-29,52-89,93-107`; `FR-1001:46,67-68`). |
| Single responsibility | Repository, script, graph, skill copy, fixtures, evidence, and README all serve one event: a maintainer requesting an advisory outsider reading before review (`FR-1001:8,12-22,46-63`). The adapter link is discovery for that same concern, not an independent feature. |
| Strategic classification | **Contrib/example.** One demonstrated workflow reuses established YAMLGraph abstractions but needs local calibration and packaging. It is not a framework primitive; FR-998 separately owns the repeated provider-boundary defect (`FR-1001:10,90`; `FR-998:8-18`). |
| Testability | Direct tests can be written for the reducer, wrapper argv, subprocess calls, report contract, environment provenance, and all named failures (`FR-1001:74-81`). R-1 and R-2 close the two places where the current text would permit incompatible passing implementations. |

The problem and raw-output read are substantive. The two positive Sonnet reports share six items but disagree by one, the plain-language report over-flags ordinary phrases, and the live #592 report quotes its explanatory parenthetical as unclear (`EXPECTATIONS.md:13-23`; positive reports `:13-21`; `plain-591` report `:13-22`; `592` report `:13-23`). The reducer follows the repository's `two_strike_split` and demote-never-drop rules rather than asking the prompt a third time (`.github/copilot-instructions.md:107-110`).

The proposed rules can also produce the claimed positive on the committed source without weakening the threshold: `yamlgraph` is followed by an em-dash gloss, path-like quotes and `FR-990` demote, while `mercury-2` and (in one run) `authoring-briefs` remain, leaving at most two retained items (`positive.md:5,12,24,49,54`; positive reports `:13-22`). The live two-pass gate remains necessary because the committed reports use Sonnet, not the proposed Haiku sample configuration.

## Required revisions

### R-1: Make graph success necessary and artifact validity independently necessary

Revise Proposed Solution 2-3 and AC-09 through AC-11 so wrapper success requires **both** a zero `yamlgraph graph run` status and a fully validated report. A valid report is necessary but never sufficient. The wrapper must preserve a non-zero graph status even when `finalize` wrote the report before a failed `gh pr comment`.

This is a real composition gap: the plan intentionally writes the report before posting and requires the report to remain after posting fails (`FR-1001:48,76`), while the script description says it confirms only the report's first line before exiting (`FR-1001:47`). The cited spike implements exactly that unsafe ordering: it writes the report, then posts, while its wrapper returns success whenever the report header exists regardless of graph status (`spike tools.py:132-143`; `spike yamlgraph-outsider:19-26`). AC-11 also says comment failure leaves no success-shaped report, contradicting AC-10's requirement that the report remain (`FR-1001:76-77`).

Freeze these semantics:

1. graph status zero plus complete report validation -> wrapper success;
2. graph status non-zero -> wrapper failure, whether or not a report exists;
3. comment failure -> non-zero graph and wrapper status, no claimed/posted comment, valid local report retained for diagnosis;
4. every failure before successful rendering -> no valid report;
5. `comment` crosses the CLI boundary as one canonical `true` or `false` string and is normalized strictly to a boolean; any other value is rejected;
6. `--comment` combined with `--input` is rejected at argument parsing rather than silently ignored.

Add wrapper and tool tests for all six branches. Do not replace artifact validation with exit-code trust; require both independent witnesses.

### R-2: Restore the complete typed report and reducer contract

Replace the phrases “structured output,” “fail-closed validation,” and `validated_unclear_items` with explicit Pydantic boundaries inherited from FR-995:

- `OutsiderReading`: non-empty `restatement`; `opinion: Literal["YES", "NO"]`; non-empty `opinion_reason`; at most eight raw unclear items; at most ten non-empty needs items.
- `UnclearItem`: non-empty `quote` and `question`.
- `DemotionReason`: a closed enum of `identifier`, `path`, and `inline_gloss`.
- `ReducedReading`: retained items plus demoted items carrying exactly one reason.

Freeze the temporary FR-998 normalization rather than inheriting the spike's permissive `str(value)` behavior: accept only `list[str]`, a JSON-encoded `list[str]`, or newline-delimited strings in the two list fields; reject non-list JSON, non-string members, arbitrary scalar/container values, empty malformed lines, and unclear lines that cannot produce both quote and question. Apply the raw item caps before reduction.

Define single-reason precedence as `identifier` -> `path` -> `inline_gloss` when more than one rule matches. State that identifier matching is a full match, suffix matching is case-sensitive or case-insensitive explicitly, and inline-gloss matching succeeds on any exact source occurrence at the frozen boundary. Derive the verdict only from the validated restatement and retained unclear items. Render exactly four top-level sections, with demoted items as a labelled subsection of section 4; never render, comment, or report success from an invalid model.

The current spike accepts arbitrary values by stringifying them and falling through after malformed JSON (`spike tools.py:55-66`), while repo doctrine requires typed boundaries and visible failures (`.github/copilot-instructions.md:181-193`). The FR's reducer rules are otherwise strong, but a machine-readable reason without overlap precedence permits two conforming implementations to disagree (`FR-1001:60,74,77`).

### R-3: Close research and prior-art references

Amend the `Research` field with an explicit answer: `is_this_a_graph: Yes` because the artifact being demonstrated is the already-spiked fetch -> provider `llm` -> deterministic finalize pipeline, and because the graph isolates model inference from side-effect tools. Point from that field to a compact four-to-six-class disposition in the FR or research record covering at least Copilot transport, provider-API graph, plain Python/provider SDK, prompt-only calibration, and deterministic reducer calibration. Preserve the recorded disagreement between the stable/over-flagging Sonnet path and the discriminating/flickering Copilot path (`research plan:629-694`). This satisfies the prospective research gate's substance requirement (`judge doctrine:118-129`) without commissioning new research.

Delete the unsupported statement that “FR-1004 retires” the parent ledger and the dangling Related entry, or replace both with an exact committed FR path. No `feature-requests/FR-1004*` artifact exists in the reviewed tree, so it cannot justify scope under input closure (`FR-1001:10,99`; `judge doctrine:16-24`).

Likewise, either commit and cite exact local copies of the three claimed production reports or label those PR references as non-evidentiary context. The six committed spike reports already satisfy the raw-read requirement; authority must not depend on mutable PR comments unavailable to the judge's committed input set.

### R-4: State the sample model choice truthfully

Replace “Nothing in the repo chooses a model” with: the graph and wrapper contain no provider/model selection; copying `.env.sample` intentionally selects the tested Anthropic/Haiku sample configuration, and users may edit or omit those values (`FR-1001:18,49-58,69-71`). The current absolute claim conflicts with the active `ANTHROPIC_MODEL=claude-haiku-4-5` line and with AC-04's accurate “tested sample default” wording.

Freeze provenance cases independently:

1. configured provider and configured model -> record both literal configured values;
2. configured provider and omitted provider-model variable -> record the provider plus `framework-default`;
3. omitted provider -> record provider as `framework-default` and model as `framework-default`;
4. never infer an effective model name from framework defaults.

Tests must prove the values recorded by `finalize` are the same environment values available to YAMLGraph resolution. This preserves the actual selection priority documented by the graph reference (`reference/graph-yaml.md:91-110`) without claiming that the demo can observe an effective default it did not configure.

### R-5: Record the human decisions for live spend and public posting

Add an implementation gate immediately before AC-12's credentialed runs and AC-14's real comment: record the human-approved provider/model, spending owner, and target public PR. Confirm that the title/body and committed report contain no private material before posting or committing evidence. The first target may be the named `sheikkinen/deviant-daily` event (`FR-1001:8`), but the enforcer must not choose a different third-party PR or incur provider spend by implication.

This does not alter the feature. It surfaces the spend and public-write decisions that judge doctrine reserves for a human (`judge doctrine:100-101`) while leaving deterministic and fake-command tests fully autonomous.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Public MIT repository `sheikkinen/yamlgraph-outsider`, maintained as a sibling clone with its own Git root |
| D-2 | External repo: `graph.yaml`, `prompts/outsider.yaml`, `tools.py`, and executable `yamlgraph-outsider` |
| D-3 | External repo: `.github/skills/outsider-view/{SKILL.md,doctrine.md}` with the truthful provider-API contract |
| D-4 | External repo: four fixtures, pre-written expectations, committed structured-output/live evidence, focused reducer/tool/wrapper tests, and `docs/evidence/` |
| D-5 | External repo: `README.md`, `LICENSE`, `.env.sample`, `.gitignore`, and `pyproject.toml` with the tested minimum YAMLGraph version and test command |
| D-6 | This repo: `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md` and verified `tmp/draft-authoring-report.md` |
| D-7 | This repo: one non-Copilot-route line in `.github/skills/outsider-view/adapters/README.md` |
| D-8 | This repo: revised FR, final human-reviewed judgement, changelog fragment, and one `docs/diary/` reflection |

Not authorized: YAMLGraph runtime, provider factory, provider/model defaults, or framework normalization changes; changes to this repository's existing outsider graph, prompt, wrapper, skill, doctrine, fixtures, or ledger beyond the single adapter-README link; a new demo ledger or census; edits to either historical spike tree; `ramp/manifest.yaml`; GitHub Actions, hooks, automatic invocation, automatic comments, blocking status, approval, merge behavior, or other enforcement; judge/review/graph-authoring doctrine changes; a new node type; or packaging the demo itself as a Python distribution.

## Revised acceptance criteria

- [ ] AC-01: The revised FR cites `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md`; `scripts/author.sh` produces the declared external graph/prompt/tool artifacts and a valid `tmp/draft-authoring-report.md`; the report records successful `yamlgraph graph lint <external-repo>/graph.yaml` and the narrow smoke, or the exact credential blocker.
- [ ] AC-02: `gh repo view sheikkinen/yamlgraph-outsider --json visibility,licenseInfo` reports public visibility and an MIT license; the local target is a separate Git root outside the yamlgraph repository; `git check-ignore` proves `.env` and `out/` are ignored and `.env.sample` is tracked.
- [ ] AC-03: Parsed `graph.yaml` contains no configured `provider` or `model` at defaults or node level; the entry script accepts no `--provider` or `--model` flag and contains no hard-coded model identifier.
- [ ] AC-04: `.env.sample` contains one active sample provider, empty key, and explicit sample model on separate lines. README calls these the tested sample selection—not “no model choice”—and documents alternatives one variable per line.
- [ ] AC-05: Tests cover all four R-4 provenance cases. Changing `.env` changes the recorded configured values without editing graph, prompt, tool, or wrapper; omitted values are recorded only as `framework-default`.
- [ ] AC-06: The wrapper chooses `out/<label>-<timestamp>.md` before invocation and passes it as `report_path`; no LLM result is needed to construct the path.
- [ ] AC-07: The standalone doctrine and `SKILL.md` contain no Copilot-CLI, pinned-`gpt-5.6-sol`, or ledger claim; they preserve title-and-body-only model input, advisory status, fail-closed handling, three-reader ownership, four top-level sections, one run per PR, and `./yamlgraph-outsider` invocation.
- [ ] AC-08: Pydantic tests exercise every R-2 accepted and rejected normalization form, every required field and cap, quote/question parsing, reducer rule and near miss, reason precedence, stable order, no loss or duplication, retained-only counts, and the three named examples.
- [ ] AC-09: The wrapper contains exactly one `yamlgraph graph run`, no `gh`, and one operational `git` call. With controlled executables on `PATH`, each missing prerequisite and missing `.env` has a distinct non-zero result and one-line hint; the `--var` set is exactly `pr,repo,input_path,comment,report_path`; invalid comment values and `--input --comment` fail before graph invocation.
- [ ] AC-10: Wrapper success requires graph status zero **and** complete report validation. Tests prove graph status non-zero is preserved despite a valid report, and graph status zero with an absent/invalid report also fails.
- [ ] AC-11: With a fake `gh`, `fetch_pr` calls `gh pr view <pr> -R <repo> --json title,body` as an argument list and returns exactly `# <title>\n\n<body>`; `--input` never calls `gh`; `finalize` posts only for strict `comment=true` with a PR source. A failed post returns non-zero and leaves the valid local report but no claimed successful comment.
- [ ] AC-12: Malformed structured output, missing API key, missing `gh`, invalid PR/repository, fetch failure, graph failure, absent report, invalid report, and comment failure each follow the distinct R-1/R-2 artifact semantics and never produce wrapper success.
- [ ] AC-13: Deterministic tests over committed structured outputs derive `NO/NO/NO/YES`. After the R-5 human spend decision, `pytest -m live` runs all four fixtures twice on the exact `.env.sample` configuration and requires that sequence on both passes; expectations predate execution and all eight raw outputs are committed under `docs/evidence/`.
- [ ] AC-14: README's pre-publication report is committed under `docs/evidence/` and linked with input SHA-256, item count, configured provider/model, timestamp, and source commit.
- [ ] AC-15: After the R-5 public-write decision, one explicit `--comment` run on the approved public PR outside `sheikkinen/yamlgraph` leaves the comment on that PR; its URL and evidence report are recorded in the FR; no credential or private PR material is committed.
- [ ] AC-16: `pyproject.toml` declares the exact test command and tested minimum `yamlgraph`; focused tests pass in a clean environment; the README's clone/install/configure/run path succeeds.
- [ ] AC-17: The Research and Prior art fields contain the R-3 `is_this_a_graph` answer, substantive solution-class disposition, and only committed evidentiary dependencies; the dangling FR-1004 claim is removed or replaced by an exact committed path.
- [ ] AC-18: This repository's diff is limited to the authoring brief, one adapter-README line, FR plus final judgement/status record, changelog fragment, and diary entry; the spike trees, ramp manifest, existing outsider implementation, and ledger are byte-unchanged.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 and AC-01 through AC-18 into FR-1001 before implementation; this draft grants no authority by itself. | GATE |
| C-2 | Route every external `graph.yaml` or `prompts/*.yaml` creation/adaptation through the committed FR-1001 brief and `scripts/author.sh`; verify the report artifact, lint, and smoke rather than an exit code. | GATE |
| C-3 | Preserve outsider input closure: only exact PR title and body enter the model; repository files, head SHA, doctrine, tools, comments, and chat narrative do not. | GATE |
| C-4 | Keep invocation and commenting manual and advisory. No workflow, hook, automatic comment, blocking status, approval, merge action, or ramp inclusion is authorized. | GATE |
| C-5 | Keep the external repository outside this worktree with an independent Git root; do not embed, vendor, or commit its working tree into yamlgraph. | GATE |
| C-6 | Validate and normalize into the R-2 models, then reduce and derive, before rendering or posting. Unknown shapes fail visibly; no permissive stringification or silent default is authorized. | GATE |
| C-7 | Require both successful graph status and valid artifact content. In particular, a retained local report after comment failure must never become wrapper success. | GATE |
| C-8 | Obtain and record the R-5 human approval before provider-billed live runs or a public write to the selected external PR. | GATE |
| C-9 | Do not modify framework normalization under FR-1001. Any local type-lie normalization remains confined to the demo's typed boundary and tested minimum YAMLGraph contract. | GATE |
| C-10 | Complete RED/GREEN tests, public-repository documentation, changelog, FR implementation/status record, and diary reflection within the frozen surfaces. | GATE |

Authority granted: after R-1 through R-5 are folded into the FR and the draft is human-reviewed, implementation may build only the standalone manual advisory demo, its evidence and tests, and the single yamlgraph adapter-documentation link described in D-1 through D-8.
