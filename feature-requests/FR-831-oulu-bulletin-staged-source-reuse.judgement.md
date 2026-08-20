# Judgement: FR-831 Oulu Bulletin Staged Source Reuse

**Verdict:** APPROVED WITH REVISIONS — the decomposition is sound, but authority activates only after R-1 through R-3 are folded into the FR so the private issue is self-contained and the interrupted FR-828 witness remains traceable.

**Prior art:** FR-831 is the judged proposal; FR-828 is its failed monolithic
predecessor; FR-824 is the bounded bulletin precedent. Their reusable and
distinguished surfaces are dispositioned in FR-831's Prior Art Disposition
table; this judgement adds no competing implementation.

**Reviewed against:** `feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-828-gitclaw-oulu-civic-intelligence-cookbook.md`; `feature-requests/FR-829-gitclaw-read-only-public-tool-policy.md`; `feature-requests/FR-830-gitclaw-repository-scoped-ledger.md`; `../gitclaw/policy/generated-features.md`; `../gitclaw/tools/contain.py`; `../gitclaw/tools/cron_run.py`; `../control-plane/probes/digitraffic-marine-probe.sh`; `../control-plane/probes/hilma-probe.sh`; `../control-plane/probes/municipality-kit.sh`; `../control-plane/probes/config/municipalities.csv`; `../control-plane/docs/municipality-probe-kit.md`; `../control-plane/docs/use-cases.md`.

## What is sound

FR-831 correctly identifies FR-828's second failure as an abstraction-span failure rather than a timeout-tuning problem: the proposal says the failed issue mixed source discovery, private prior-art recall, transport implementation, normalization, failure policy, and bulletin authoring, and rejects rewording or timeout increases as preserving that overload. That aligns with repository doctrine to split bloated work and preserve operational truth rather than hiding failures.

The first deliverable is deliberately small: exactly one private control-plane issue, no public cookbook repository touch, and no GitClaw trigger. The scope fence then explicitly excludes code implementation, public issue intake, secrets, workflow changes, retries, timeout changes, and publication. This satisfies the rubric's single-responsibility and minimality tests.

The cited source assets are real and relevant. Digitraffic Marine documents a public no-auth Port Call API, Oulu LOCODE `FIOUL`, gzip-compressed responses, earliest ETA sorting, a bounded `--top`, and a cargo-inference caveat. Hilma documents the public eForms search URL, bounded `$top`, publication ordering, notice ID deduplication, stable SPA detail URL construction, and SPA detail limitation. Oulu municipality facts are present in config and research: code `564`, platform `triplan`, and `https://asiakirjat.ouka.fi/ktwebscr`.

The architecture classification is **Pattern documentation / process decomposition**, not a framework primitive. FR-831 creates an operator research record and transfer packet; it does not add reusable YAMLGraph or GitClaw runtime behavior. That is the right classification because current GitClaw policy allows bounded public reads inside one generated feature directory but does not automatically create a shared library across separately generated features.

## Required revisions

### R-1: Add an explicit Ideal Result section before the task design

Insert a short `## Ideal Result` section before `## Task 1: Private Provenance Reconstruction Issue`. It must state the desired end state in reader/event terms: the private control-plane issue contains a reviewed source-asset inventory and a redacted public transfer packet; a later public GitClaw issue can quote one packet section without private repository access, memory of prior runs, or source rediscovery.

### R-2: Make the private issue body self-contained

Revise the required private issue body so it does not rely on the phrase "assets named by FR-831" as an external pointer. The body must include either the complete required asset list or a checklist with every repository-relative path from the asset table, including `probes/digitraffic-marine-probe.sh`, `probes/hilma-probe.sh`, `probes/config/municipalities.csv`, `probes/municipality-kit.sh`, `docs/municipality-probe-kit.md`, and `docs/use-cases.md`. This is foldable without changing scope: the acceptance criteria already require the issue to cite every required source asset by repository-relative path. The revision only moves the requirement into the artifact the operator will actually execute.

### R-3: Record the FR-828 second-attempt stop in FR-828 before any downstream issue

Add a condition to FR-831 and its acceptance criteria that the FR-828 implementation/status record is updated with the fresh replacement repository, initial SHA `b7e0bcf`, run `32332927531`, `judged_approved -> enforce timeout`, and the FR-831 stop decision before any Task 2-7 issue is opened. FR-831 itself records those facts, but the cited governing cookbook FR still shows the earlier copied-ledger block as its visible status and first enforcement witness. Leaving the second failure only in FR-831 creates a provenance fork.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | One private GitHub issue in `sheikkinen/control-plane` titled `Oulu bulletin source assets: provenance and public transfer packet` |
| D-2 | A source-asset inventory inside that issue, frozen to control-plane commit `6cadb00cc77d6f110a5342b2cbd9dff830a4ac6d` |
| D-3 | A bounded `Public transfer packet` inside that issue with separate Harbour, Procurement, and Municipal decisions sections |
| D-4 | Human redaction/completeness review record for the transfer packet |
| D-5 | FR implementation-status notes recording the private issue URL, review URL, and FR-828 second-attempt stop provenance |

Not authorized: GitClaw or YAMLGraph code changes; probe, graph, prompt, workflow, runtime, policy, containment, cron, ledger, secret, or dependency changes; public cookbook repository edits; public issue creation; FR-828 retry or relabel; timeout changes; synthetic ledger repair; manual generated-feature implementation edits; downstream Tasks 2-7; publication or scheduled bulletin work.

## Revised acceptance criteria

- [ ] AC-01: FR-831 contains an explicit Ideal Result section before Task 1, stating the reviewed private inventory and public-safe transfer packet as the end state.
- [ ] AC-02: One private `sheikkinen/control-plane` issue exists with the exact Task 1 title and no `gitclaw` label.
- [ ] AC-03: The issue body freezes repository commit `6cadb00cc77d6f110a5342b2cbd9dff830a4ac6d` and includes a self-contained checklist naming every required source asset by repository-relative path.
- [ ] AC-04: Every cited asset records public origin, request/auth contract, bounds, parser/encoding assumptions, normalized identity and fields, failure modes, caveats, evidence, and one of `reuse`, `adapt`, `reference-only`, or `reject`.
- [ ] AC-05: The issue contains one `Public transfer packet` with separate Harbour, Procurement, and Municipal decisions sections.
- [ ] AC-06: Each transfer-packet source section visibly distinguishes facts established by existing assets, live-reverification needs, condemned behavior, and deferred decisions reserved for source-specific implementation FRs.
- [ ] AC-07: Human review confirms the packet contains no credential, environment value, private output, personal/local-device data, unrelated probe inventory, or unbounded raw response body.
- [ ] AC-08: No probe, graph, workflow, runtime, policy, prompt, secret, public cookbook repository, public issue, or generated feature is created or modified under Task 1.
- [ ] AC-09: FR-828 issue #1 and run `32332927531` remain preserved as failed, interrupted evidence without rerun, timeout increase, ledger repair, or manual implementation edit.
- [ ] AC-10: FR-828's implementation/status record is updated with the second-attempt repository, commit/run IDs, timeout outcome, and FR-831 stop decision before any downstream issue is opened.
- [ ] AC-11: The downstream queue records Tasks 2-7 as separate judgements, one active at a time, with source reuse and composition stop gates.
- [ ] AC-12: No downstream task is filed until the Task 1 issue URL, human redaction review URL, and FR-828 status-update reference are recorded in FR-831's implementation status.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 into FR-831 before creating the private issue. | GATE |
| C-2 | The control-plane issue must be private, unlabelled for GitClaw intake, and must not trigger automation. | GATE |
| C-3 | The transfer packet must be redacted by human review before any text is copied to a public repository or public issue. | GATE |
| C-4 | The enforcer must not modify GitClaw/YAMLGraph runtime, policy, prompts, workflows, probes, generated features, public repositories, secrets, or ledger state. | GATE |
| C-5 | Tasks 2-7 require separately judged FRs; no source implementation, shared-library decision, composition, synthesis, cron, or publication work is authorized here. | GATE |
| C-6 | Private control-plane source contents may be summarized into public contracts only after path-cited provenance and redaction review; raw private outputs and unrelated/private-data probes must not be transferred. | GATE |

Authority granted: after R-1 through R-3 are folded into FR-831, enforcement may create exactly one private provenance issue and record its reviewed public transfer packet; no implementation or public GitClaw work is authorized.
