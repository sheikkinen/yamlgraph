# Judgement: FR-825 KTweb Encoding Detection and Event-Safe State Repair

**Verdict:** APPROVED — the FR isolates a real KTweb transport-decoding defect, preserves FR-824's deterministic delta contract, and gives mechanically testable repair and publication gates.

**Reviewed against:** `feature-requests/FR-825-ktweb-encoding-repair.md`; `feature-requests/FR-824-hva-weekly-bulletin-new-repo.md`; `feature-requests/FR-824-hva-weekly-bulletin-new-repo.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

**Prior art:** FR-824 is reused for the consumer, typed-state, and deterministic-delta contracts; FR-795 concerns an unrelated endpoint-probe schema-dialect repair and does not overlap this transport-decoding migration. FR-825 is the judged target, not precedent.

## What is sound

The problem is evidenced and local. FR-825 identifies 293 affected records, all KTweb, and names the precise destructive decode call `decode("utf-8", errors="replace")` (`feature-requests/FR-825-ktweb-encoding-repair.md:22-46`). That matches doctrine's boundary rule: normalize external data at entry, not downstream (`.github/copilot-instructions.md:49-52`, `.github/copilot-instructions.md:246-249`).

Scope is clear and minimal. The FR limits implementation to the consumer repository and states that YAMLGraph changes are limited to FR status, judgement, and implementation evidence (`feature-requests/FR-825-ktweb-encoding-repair.md:166-171`). It also excludes unrelated source families and schema expansion (`feature-requests/FR-825-ktweb-encoding-repair.md:145-152`). Strategic classification: **Contrib/example consumer repair**, not a YAMLGraph framework primitive, because it repairs one downstream deployment source family while preserving the framework boundary established by FR-824 (`feature-requests/FR-824-hva-weekly-bulletin-new-repo.md:116-117`, `feature-requests/FR-824-hva-weekly-bulletin-new-repo.judgement.md:20-20`).

The design preserves the governing FR-824 contracts instead of weakening them. FR-824 requires Pydantic-normalized source items before persistence, substantive hashes, deterministic event IDs, exact `changed_fields`, and no event for observation noise (`feature-requests/FR-824-hva-weekly-bulletin-new-repo.md:133-173`, `feature-requests/FR-824-hva-weekly-bulletin-new-repo.md:179-200`). FR-825's migration is explicitly bounded to existing KTweb records with U+FFFD, stable `(source, source_id)` matches, retained URLs, idempotent metadata, and suppression only of encoding-repair noise (`feature-requests/FR-825-ktweb-encoding-repair.md:85-105`).

The acceptance criteria are mostly mechanical and testable. They require fixture assertions for legacy and UTF-8 decoding, precedence/failure behavior, exact event suppression versus simultaneous substantive changes, no-op reruns, publication rejection before LLM synthesis, no-live-network unit coverage, live smoke evidence, a post-repair census, and two dispatched collector runs (`feature-requests/FR-825-ktweb-encoding-repair.md:114-143`). That satisfies the judge rubric for measurability and testability (`.github/skills/judge-fr/doctrine.md:43-45`, `.github/skills/judge-fr/doctrine.md:58-61`).

The FR is feasible with existing repository patterns. FR-824 already defines `state/source-items.jsonl`, weekly events, `source_health`, typed source models, collection workflows, and scoped staging (`feature-requests/FR-824-hva-weekly-bulletin-new-repo.md:82-108`, `feature-requests/FR-824-hva-weekly-bulletin-new-repo.md:267-332`). FR-825 asks for deterministic decoding, state migration, and a pre-synthesis U+FFFD guard; it does not require probabilistic charset detection, new dependencies, graph authoring, or historical ledger rewriting (`feature-requests/FR-825-ktweb-encoding-repair.md:66-83`, `feature-requests/FR-825-ktweb-encoding-repair.md:104-112`).

## Required revisions

None.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `hva-weekly-bulletin` KTweb response decoding helper and `collect_ktweb` integration |
| D-2 | Consumer-repo fixtures for UTF-8, declared charset, HTML meta charset, Windows-1252/ISO-8859-1-compatible Finnish bytes, malformed bytes, and U+FFFD rejection |
| D-3 | Bounded KTweb compact-state repair keyed by `(source, source_id)` with retained source URL checks, completion metadata, and idempotent no-op behavior |
| D-4 | Delta/event tests proving encoding-only repair suppression, simultaneous substantive-change event emission, exact `changed_fields`, retry/no-op behavior, and unchanged historical event ledgers |
| D-5 | Publication/window guard rejecting U+FFFD candidates before YAMLGraph synthesis with source and stable ID in the error |
| D-6 | Implementation evidence in the FR: fixture encodings, pre/post census, migration counts/marker, focused/full test results, live KTweb health census, workflow run URLs, commit SHAs, and next-bulletin U+FFFD check |
| D-7 | YAMLGraph repository status/judgement/implementation-note evidence only |

Not authorized: changes to Dynasty, CaseM, Hilma, TED, MAO, YAMLGraph package code, YAMLGraph capabilities/requirements, graph or prompt artifacts, bulletin schema expansion, LLM-based text repair, historical event-ledger rewriting, branch protection, credentials, workflow permission expansion beyond FR-824's direct-commit model, or any source inventory expansion.

## Revised acceptance criteria

- [ ] AC-01: A legacy-encoded KTweb fixture containing Finnish text such as `Pöytäkirjan tarkastaminen` decodes exactly with no U+FFFD.
- [ ] AC-02: A UTF-8 KTweb fixture decodes exactly with no behavior change.
- [ ] AC-03: Declared HTTP charset and HTML meta charset are honored before fallback; unsupported, contradictory, undecodable, or U+FFFD-producing results become explicit endpoint health failures.
- [ ] AC-04: KTweb persisted `SourceItem.title`, `organization`, and `body_excerpt`/excerpt fields contain no U+FFFD after successful collection.
- [ ] AC-05: The repair updates all reachable corrupt KTweb records in `state/source-items.jsonl` without creating encoding-only `updated` or `transition` events.
- [ ] AC-06: A repaired record with another substantive field change emits the normal event with exact `changed_fields`; only the encoding-repair portion is suppressed.
- [ ] AC-07: Re-running migration and collection after the completion marker produces no state churn, event replay, or encoding-only commit.
- [ ] AC-08: Migration completion is recorded in bounded state metadata and historical event ledgers are not rewritten.
- [ ] AC-09: Weekly-window construction or publication rejects any candidate containing U+FFFD before the LLM/YAMLGraph synthesis step and reports source plus stable ID.
- [ ] AC-10: Unit tests cover UTF-8, declared charset, HTML meta charset, Windows-1252/ISO-8859-1-compatible Finnish bytes, malformed bytes, event suppression, simultaneous substantive change, and retry behavior without live network access.
- [ ] AC-11: A live six-family smoke reports zero U+FFFD records among newly collected KTweb items and preserves explicit per-endpoint health.
- [ ] AC-12: Post-repair census reports zero U+FFFD records in `state/source-items.jsonl`, or lists unreachable stale records explicitly with source ID, URL, and reason.
- [ ] AC-13: Ruff, focused tests, full tests, Radon grade-D scan, and file-size gates pass; no source or test file exceeds 450 lines.
- [ ] AC-14: One dispatched collector run commits the bounded repair, and a second dispatched run proves no encoding-only replay event or state churn.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-824's repository, public-data, direct-commit, scoped-staging, graph-authoring, dispatch/cron evidence, and human-review gates remain binding; FR-825 may not weaken or bypass them. | GATE |
| C-2 | The enforcer must implement decoding at the KTweb transport boundary and must not use `errors="replace"` for persisted source text. | GATE |
| C-3 | The migration must be bounded to existing KTweb records containing U+FFFD and matched by `(source, source_id)` with the same source URL; unmatched records must be reported, not silently skipped as success. | GATE |
| C-4 | Event suppression is allowed only for encoding-repair noise on identified corrupt KTweb records; any simultaneous non-encoding substantive change must emit the normal event and exact `changed_fields`. | GATE |
| C-5 | Historical event ledgers must not be rewritten. | GATE |
| C-6 | Any new dependency, probabilistic charset detector, branch-protection/credential change, source-family expansion, graph/prompt edit, or YAMLGraph package/CAP/REQ change is separate scope. | GATE |
| C-7 | The publication guard must fail closed before LLM/YAMLGraph synthesis if U+FFFD remains in a candidate. | GATE |
| C-8 | The FR is not complete until the pre/post U+FFFD census, migration marker/counts, live health smoke, two dispatch run URLs, resulting commit SHAs, and next-bulletin candidate check are recorded in implementation notes. | GATE |

Authority granted: the enforcer may implement the bounded KTweb decoding fix, event-safe state repair, and U+FFFD publication guard in `hva-weekly-bulletin`, with YAMLGraph limited to FR/judgement/evidence updates.
