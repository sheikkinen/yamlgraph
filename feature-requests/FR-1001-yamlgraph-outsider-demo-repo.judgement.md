# Judgement: FR-1001 `yamlgraph-outsider` standalone demo repository

**Verdict:** APPROVED WITH REVISIONS — the standalone outsider is a well-evidenced contrib/demo, but authority activates only after the FR makes the copied skill truthful for the API route, defines deterministic reducer and model-provenance contracts, separates ignored runtime output from committed evidence, and adds the mandatory graph-authoring and cross-repository execution boundaries.

**Prior art:** [FR-1001-yamlgraph-outsider-demo-repo.md](FR-1001-yamlgraph-outsider-demo-repo.md) — the subject; its `**Prior art:**` line dispositions FR-995, FR-865, FR-998 and the node-type census.

**Reviewed against:** `feature-requests/FR-1001-yamlgraph-outsider-demo-repo.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `feature-requests/TEMPLATE.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/outsider-view/SKILL.md`; `.github/skills/outsider-view/doctrine.md`; `.github/skills/outsider-view/adapters/README.md`; `feature-requests/FR-995-outsider-reader.md`; `feature-requests/FR-995-outsider-reader.judgement.md`; `feature-requests/FR-865-ramp-installer.md`; `docs/node-type-census-2026-08.md`; `docs/2026-09-05-research-plan-cap-journey-census.md` §§12–13; `docs/spikes/outsider-llm-2026-09-05/graph.yaml`; `docs/spikes/outsider-llm-2026-09-05/prompts/outsider.yaml`; `docs/spikes/outsider-llm-2026-09-05/tools.py`; `docs/spikes/outsider-llm-2026-09-05/yamlgraph-outsider`; `docs/spikes/outsider-llm-2026-09-05/EXPECTATIONS.md`; and the six committed reports under `docs/spikes/outsider-llm-2026-09-05/out/`: `positive-claude-sonnet-4-5-20260905T080348Z.md`, `positive-claude-sonnet-4-5-20260905T080409Z.md`, `pr-591-claude-sonnet-4-5-20260905T080437Z.md`, `plain-591-claude-sonnet-4-5-20260905T080503Z.md`, `pr-591-v2-claude-sonnet-4-5-20260905T080533Z.md`, and `592-claude-sonnet-4-5-20260905T080708Z.md`. FR-998 was not consumed because FR-1001 supplies neither a repository path nor a commit SHA for that off-branch artifact.

## What is sound

- **The problem, consumer, and value are concrete.** The FR names a maintainer immediately after opening a PR and gives the first command they run (`FR-1001:8`); the standalone spike demonstrates the intended `llm`-node transport with `yamlgraph`, `gh`, and one provider key in about 25 seconds (`research plan:629-649,685-689`; `EXPECTATIONS.md:25`).
- **The raw-output read is substantive.** The evidence preserves disagreement rather than hiding it: the Copilot route flickered from five items to zero while the API route returned seven then six substantially overlapping items, and the API model over-flagged ordinary words, paths, and an inline explanation (`FR-1001:30-35`; `research plan:657-680`; `EXPECTATIONS.md:13-23`). This satisfies the repository's raw-read discipline rather than merely asserting a score.
- **The proposed architecture uses established primitives.** A three-node Python → `llm` → Python graph already ran end to end, structured output removed the markdown-parse failure class, and the node-type census classifies `llm` as an established retained primitive (`research plan:639-655,682-689`; `docs/node-type-census-2026-08.md:143,174,209`).
- **The behavioral change belongs at the reducer boundary.** The prompt has already failed twice to distinguish explanatory identifiers from unexplained jargon, while the source text supplies deterministic path and gloss signals (`research plan:673-680`; `.github/copilot-instructions.md:107,109`). A code cap is therefore smaller and more reliable than another prompt iteration.
- **Scope and single responsibility are basically coherent.** The public repository, its local skill wrapper, fixtures, and one reducer rule all serve one event: obtaining an advisory outsider reading without a Copilot seat. The one-line back-reference is discoverability, not a second feature; ramp inclusion and framework normalization are explicitly deferred (`FR-1001:44-57,73-80`).
- **Strategic classification:** **Contrib/example**. It serves one demonstrated workflow and reuses existing graph, prompt, tool, and skill abstractions with a local calibration gap; it neither establishes a framework primitive nor needs runtime changes. The classification agrees with FR-995's judgement of the underlying reader as a contrib/example process instrument (`FR-995 judgement:28`).
- **Prior art is mostly well dispositioned.** FR-995 owns the reader contract, FR-865 owns generic ramp distribution, FR-998 owns the framework normalization, and the node census confirms no new node primitive is needed (`FR-1001:10`; `FR-865:75-77,189-196`).

## Required revisions

### R-1: Replace byte identity with a truthful standalone doctrine

Delete AC-7's requirement that the demo's `doctrine.md` be byte-identical to this repository's file. The current doctrine states that execution uses the Copilot CLI with pinned `gpt-5.6-sol` and that the reason for an external working directory is to prevent Copilot from loading repository instructions (`.github/skills/outsider-view/doctrine.md:21-23`); FR-1001 instead requires a provider-API `llm` node with no pinned model (`FR-1001:14-16,45-51`). Those contracts cannot both be true.

Create a standalone doctrine derived from the FR-995 doctrine that preserves title-and-body-only input, advisory status, fail-closed output, the three readers, and one run per PR, but accurately names the provider-API route and environment-based model configuration. Keep four top-level report sections as the inherited contract requires (`outsider-view/doctrine.md:7-10`). Render demoted entries as a labelled subsection of section 4, not a fifth top-level section, and state that they are excluded from the derived-verdict count. The copied `SKILL.md` must invoke `./yamlgraph-outsider` and must not retain `scripts/outsider.sh` or Copilot-specific operational claims.

### R-2: Make model selection and provenance internally consistent

Rewrite “the demo makes no model decision.” Setting `ANTHROPIC_MODEL=claude-haiku-4-5` in the distributed `.env.sample` is a demo default, even if it matches a framework default (`FR-1001:16,45-51`). State this honestly as the tested sample configuration, put `PROVIDER=anthropic`, `ANTHROPIC_API_KEY=`, and `ANTHROPIC_MODEL=claude-haiku-4-5` on separate active lines, and put each alternative-provider variable on its own commented line.

Use a model-neutral pre-run report filename such as `out/<label>-<timestamp>.md`. The cited spike can name the report before execution only because the wrapper owns `MODEL`, passes it into graph state, and the finalizer reads that state (`spike yamlgraph-outsider:8,18-20`; `spike tools.py:112,137`). FR-1001 removes that path yet asks the filename and header to contain the model returned by `finalize` (`FR-1001:45,62-63`), which is circular and unsupported by the cited evidence. Define the header and ledger field as the **configured** provider/model loaded from `.env`; tests must prove those exact values reach both the `llm` node's resolution environment and the finalizer. If either variable is omitted, record `framework-default` rather than inventing an effective identifier. Restrict the “only file naming a model” assertion to active configuration: historical evidence and documentation may truthfully name tested models.

### R-3: Specify the reducer as a deterministic typed boundary

Replace the substring sketch with an exact contract over `(source_body, validated_unclear_items)`. For each structured unclear item:

1. preserve the original quote and question;
2. demote a full identifier token matching `CAP-\d+`, `FR-\d+`, or `REQ-[A-Za-z0-9-]+`;
3. demote a path-like quote containing a slash or ending in `.yaml`, `.yml`, `.py`, or `.md`;
4. demote an inline gloss when either the exact quote is followed in the source by ` (`, ` — `, or `: `, or the quote itself contains such a gloss and its pre-gloss prefix occurs at that source boundary;
5. retain all other items in `unclear`, preserving order; append demoted items, with a machine-readable reason, to the labelled section-4 subsection; never discard or duplicate an item.

This second inline-gloss form is necessary because the cited #592 output includes the parenthetical inside the model's quote, so an “exact quote followed by ` (`” check alone cannot match it (`592 report:16`; `FR-1001:53`). Add direct typed-unit tests using the source input plus structured items—not rendered report text alone—for every rule, near misses, case behavior, punctuation, order, counts, and the three named examples. Preserve the existing Pydantic/fail-closed checks from FR-995; malformed structured output must produce no report, comment, or ledger row (`FR-995 judgement:38-48,90`).

Before claiming the live `NO/NO/NO/YES` sequence, record two runs per fixture using the exact sample default and the implemented reducer. Current evidence covers `claude-sonnet-4-5` without the reducer and records `positive` as NO in both runs (`research plan:660-667`; `EXPECTATIONS.md:13-14`); it does not establish the proposed `claude-haiku-4-5` result. Keep deterministic tests over committed structured outputs separate from the credentialed live `--selftest`, whose purpose is to expose provider drift rather than conceal it.

### R-4: Separate ignored runtime output from committed evidence and measurement

Keep `out/` ignored for transient reports and logs, but move committed evidence and the ledger outside it. The current plan simultaneously ignores `out/`, requires a README report committed under `out/`, and writes the ledger to `out/ledger.jsonl` (`FR-1001:44,56,66,68`). Use `docs/evidence/` for the pre-publication README report and `docs/census/outsider-ledger.jsonl` for measurement, matching FR-995's durable ledger precedent (`outsider-view/doctrine.md:49-53`; `FR-995 judgement:44-48,77,96`).

Remove the self-referential requirement that the README embed the count produced by reading itself. Committing that count changes the input that produced it. Instead, make the README link the committed report and state its input SHA-256, item count, configured provider/model, timestamp, and source commit.

Spell out the inherited ledger schema in FR-1001: UTC timestamp, repository, PR number, PR head SHA, exact title-plus-body SHA-256, configured provider/model, graph/prompt digest, demo-repository commit SHA, derived verdict, retained-unclear count, demoted count, needs count, and report path. Append only after successful validation for a real PR; fixture, `--input`, self-test, failed, and comment-failed runs write no row. The five-run ramp threshold means five distinct external PRs, using at most the latest successful row per repository/PR identity.

### R-5: Add the graph-authoring, repository, dependency, and prior-art boundaries

Add and cite `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md`. It must name the external repository as the target, enumerate every graph/prompt/tool/test/document artifact, cite the spike as precedent, and require `scripts/author.sh`, the verified `tmp/draft-authoring-report.md`, `yamlgraph graph lint`, and the narrow credentialed smoke. Copying or adapting a graph is still graph authoring (`graph-authoring/doctrine.md:11-17`), FR-bound briefs must be committed and cited (`:21-29`), and lint plus smoke are mandatory (`:78-89`).

State that `sheikkinen/yamlgraph-outsider` is a separate sibling clone with its own Git root, never a nested repository or untracked directory inside this worktree. Add the external repository's test surface and dependency contract—at minimum `tests/` and a `pyproject.toml` (or an equally explicit existing-environment contract) that makes the reducer tests runnable independently of pipx's isolated application environment. Name the exact test command. Record the tested minimum `yamlgraph` version while leaving end-user installation on the normal package channel.

Replace the unauditable FR-998 branch mention with an exact committed file path and commit SHA, or state only that the demo owns its local normalization and has no dependency on FR-998. No implementation or acceptance criterion may depend on an artifact unavailable from the frozen input set (`FR-1001:10`).

### R-6: Replace proxy checks with end-to-end acceptance checks

Replace AC-1's grep exception and AC-2's “`.env.sample + a key`” prose with exact setup and assertions. Tests must parse the graph, inspect the wrapper's accepted flags, run the typed reducer, validate the whole report, and verify model-configuration propagation; a grep that permits unspecified “state declarations” is not a complete contract (`FR-1001:61-63`). Add negative-path tests for a missing API key, missing `gh`, invalid repository/PR input, failed graph execution, malformed structured output, comment failure, and absent report. The wrapper must trust validated artifact content rather than exit code, as inherited from FR-995 (`outsider-view/doctrine.md:41-47`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Public repository `sheikkinen/yamlgraph-outsider`, MIT licensed, in its own Git root |
| D-2 | External repo: `graph.yaml`, `prompts/outsider.yaml`, `tools.py`, executable `yamlgraph-outsider` |
| D-3 | External repo: `.github/skills/outsider-view/{SKILL.md,doctrine.md}` with the truthful standalone contract |
| D-4 | External repo: four fixtures, pre-written expectations, committed structured-output evidence, and focused reducer/wrapper tests |
| D-5 | External repo: `README.md`, `LICENSE`, `.env.sample`, `.gitignore`, dependency/test manifest, `docs/evidence/`, and `docs/census/outsider-ledger.jsonl` |
| D-6 | This repo: `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md` and verified `tmp/draft-authoring-report.md` |
| D-7 | This repo: one non-Copilot-route link in `.github/skills/outsider-view/adapters/README.md` |
| D-8 | This repo: FR status/implementation record, changelog fragment, and one `docs/diary/` reflection |

Not authorized: changes to YAMLGraph runtime or provider/model defaults; changes to this repository's outsider skill, doctrine, graph, prompt, wrapper, fixtures, ledger, or historical spike; changes to `ramp/manifest.yaml`; automatic invocation, automatic commenting, CI or merge gating; judge/review/graph-authoring doctrine or hook changes; a new node type; packaging the demo itself as a Python distribution; or claiming FR-998 as delivered.

## Revised acceptance criteria

- [ ] AC-01: The revised FR cites `feature-requests/authoring-briefs/fr-1001-yamlgraph-outsider-demo-repo-brief.md`; `scripts/author.sh` produces the declared external graph/prompt/tool artifacts and a valid `tmp/draft-authoring-report.md`; the report records successful `yamlgraph graph lint <external-repo>/graph.yaml` and the narrow smoke, or the exact credential blocker.
- [ ] AC-02: `gh repo view sheikkinen/yamlgraph-outsider --json visibility,licenseInfo` reports public visibility and an MIT license, and the local target is a separate Git root outside the yamlgraph repository.
- [ ] AC-03: Parsed `graph.yaml` contains no configured `provider` or `model` at defaults or node level; the entry script accepts no `--provider` or `--model` flag and contains no hard-coded model identifier.
- [ ] AC-04: `.env.sample` contains one active sample provider, empty key, and explicit sample model on separate lines; README labels that model as the demo's tested sample default and documents one-variable-per-line alternatives.
- [ ] AC-05: With `cp .env.sample .env` and the key value filled in, a fixture run records the configured provider/model in the validated report header and ledger metadata. Changing those `.env` values changes the recorded configured values without editing graph, prompt, tool, or script. Omitted values are recorded as `framework-default`, not as a guessed identifier.
- [ ] AC-06: Reports use a model-neutral pre-run filename. No code needs an LLM result in order to construct the path passed into that same run.
- [ ] AC-07: The standalone doctrine and `SKILL.md` contain no Copilot-CLI or pinned-`gpt-5.6-sol` execution claim; they preserve title-and-body-only model input, advisory status, fail-closed handling, three-reader ownership, four top-level sections, one run per PR, and `./yamlgraph-outsider` invocation.
- [ ] AC-08: Typed unit tests prove every R-3 reducer rule and near miss using paired source bodies and structured unclear items. They prove stable ordering, no loss or duplication, machine-readable demotion reasons, retained-only verdict counts, and the three named cases from FR-1001.
- [ ] AC-09: Missing/invalid structured fields, excessive item counts, malformed unclear items, missing API key, missing `gh`, invalid PR/repository input, graph failure, comment failure, and absent/invalid report all fail non-zero and create no success-shaped report or ledger row.
- [ ] AC-10: Deterministic tests over committed structured outputs derive `NO/NO/NO/YES` after the reducer. A credentialed `./yamlgraph-outsider --selftest` runs every fixture twice with the exact `.env.sample` configuration and requires that sequence on both passes; all eight raw outputs are committed under `docs/evidence/` with expectations written before execution.
- [ ] AC-11: `out/` is ignored and contains only transient runtime reports/logs. The README pre-publication report is committed under `docs/evidence/`, and README links it with input SHA-256, item count, configured provider/model, timestamp, and source commit; README does not claim to contain a count derived from its own final bytes.
- [ ] AC-12: `docs/census/outsider-ledger.jsonl` uses the complete R-4 schema. Tests prove one row per successful real-PR run, no rows for excluded/failed modes, and distinct external-PR counting for the five-run ramp prerequisite.
- [ ] AC-13: At least one validated run against a real PR outside `sheikkinen/yamlgraph` produces a committed evidence report and attributable ledger row without committing credentials or PR-private data.
- [ ] AC-14: The external repository includes the declared test/dependency manifest and exact test command; its focused tests pass in a clean environment using the documented setup, and the README's clone/install/run path succeeds.
- [ ] AC-15: In this repository, the diff is limited to the authoring brief, one adapter-README link, FR/judgement/status record, changelog fragment, and diary entry; the spike tree and ramp manifest are byte-unchanged.
- [ ] AC-16: The FR's prior-art line either cites FR-998 by committed path and SHA or removes it as an evidentiary dependency and states that local normalization is wholly owned by this demo.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 and the revised acceptance criteria into FR-1001 before implementation; the current AC-7, output paths, and model-provenance claims grant no authority. | GATE |
| C-2 | Run all graph/prompt creation or adaptation through the committed FR-1001 authoring brief and `scripts/author.sh`; verify the report artifact, lint, and smoke rather than an exit code. | GATE |
| C-3 | Preserve the outsider boundary: only PR title and body enter the model; no repository files, doctrine, tools, or chat narrative are model inputs. | GATE |
| C-4 | Keep the output manual and advisory. No workflow, hook, automatic comment, blocking status, approval, merge action, or ramp-manifest inclusion is authorized. | GATE |
| C-5 | Keep the external repository outside this worktree with an independent Git root; do not embed or vendor its working tree into yamlgraph. | GATE |
| C-6 | Validate typed output and apply the deterministic reducer before deriving a verdict, writing a report, posting, or appending a ledger row. | GATE |
| C-7 | Do not modify framework normalization for the provider type lie; retain the local boundary normalization until separately judged framework work lands. | GATE |
| C-8 | Complete RED/GREEN tests, public-repository documentation, changelog, FR implementation/status record, and diary reflection within the frozen surfaces. | GATE |

Authority granted: after R-1 through R-6 are folded into FR-1001, implement only the standalone advisory demo repository and the narrow yamlgraph back-reference described by D-1 through D-8.
