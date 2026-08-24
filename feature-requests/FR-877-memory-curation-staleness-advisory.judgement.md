# Judgement: FR-877 Memory Curation Staleness Advisory

**Verdict:** APPROVED WITH REVISIONS - the advisory is the right non-scheduled recurrence trigger for FR-875 curation, but authority activates only after the FR pins the post-apply marker semantics, advisory counting scope, hook failure evidence, and fixture-only tests.

**Reviewed against:** `feature-requests/FR-877-memory-curation-staleness-advisory.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-875-memory-corpus-curation-graph.md`; `feature-requests/FR-875-memory-corpus-curation-graph.judgement.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.md`; `feature-requests/FR-874-cross-device-agent-memory-sync.judgement.md`; `feature-requests/FR-743-sessionstart-briefing-hook.md`; `feature-requests/FR-742-undelivered-diary-detection.md`; `docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md`; `.github/hooks/scripts/session-briefing.sh`; `examples/memory-curation/apply.py`; `examples/memory-curation/nodes/collect.py`; `examples/memory-curation/README.md`; `capabilities/CAP-247-memory-corpus-curation.yaml`; `tests/unit/test_memory_curation.py`.

**Prior art:** FR-875/FR-878 (parents), FR-743 (seam), FR-742 (measured
orphaned-reminder evidence), FR-874 (REJECTED — nothing moves
off-machine) dispositioned throughout this judgement; remaining
noun-collision hits carry no territorial overlap.

## What is sound

The problem is real and scoped to a named consumer/event. FR-877 names the SessionStart reader and the drift moment (`feature-requests/FR-877-memory-curation-staleness-advisory.md:8-12`), and FR-742 supplies the measured analogue: Distill-class reminders were orphaned across three dead sessions (`feature-requests/FR-742-undelivered-diary-detection.md:11-17`). The proposal does not schedule destructive work; it only emits a recurrence signal (`feature-requests/FR-877-memory-curation-staleness-advisory.md:20-26`), preserving FR-875's human-signoff boundary for live memory mutation (`feature-requests/FR-875-memory-corpus-curation-graph.md:109-117`).

The architectural fit is narrow and low-risk. The advisory is pure local code, zero LLM calls, zero network (`feature-requests/FR-877-memory-curation-staleness-advisory.md:14-16`, `97-98`), which avoids FR-875's provider-egress hazard for real-corpus judgement (`feature-requests/FR-875-memory-corpus-curation-graph.md:15-26`). It also reuses the FR-743 SessionStart seam and fail-open rule rather than adding cron, a daemon, or automatic curation (`feature-requests/FR-877-memory-curation-staleness-advisory.md:72-75`; `feature-requests/FR-743-sessionstart-briefing-hook.md:55-62`).

Strategic classification: **repo-operations example/tooling**, not a framework primitive. It extends the existing `examples/memory-curation/` local hygiene toolchain (`examples/memory-curation/README.md:1-22`) and the local hook briefing surface (`.github/hooks/scripts/session-briefing.sh:10-14`); it does not need YAMLGraph graph or prompt authoring.

## Required revisions

### R-1: Define `.curation-state.json` as the post-apply live baseline

Revise the marker contract so `notes` represents the live repo-scope corpus after the apply transaction completes, not the pre-apply manifest with redaction overrides. As written, the marker is described as "the frozen manifest's note hashes plus the post-apply hashes of redacted notes" (`feature-requests/FR-877-memory-curation-staleness-advisory.md:58-61`). If `forget` rows remain in that marker with their old manifest hashes, the first advisory after a successful curation will count those intentionally forgotten notes as `deleted` drift (`feature-requests/FR-877-memory-curation-staleness-advisory.md:67-70`), producing an immediate false stale warning.

Fold this by requiring a versioned marker schema such as `{version, applied_at, manifest_sha256, disposition_sha256, notes}` where `notes` contains only live note paths after apply: kept notes with their live sha256, redacted notes with their post-redaction sha256, and no forgotten paths. Write the marker only after all live memory-root mutations and tombstone updates have succeeded.

### R-2: Freeze the advisory comparison domain and system-file treatment

Specify the exact files counted as the live corpus and how system files are treated. FR-877 says the advisory compares live `repo/*.md` hashes (`feature-requests/FR-877-memory-curation-staleness-advisory.md:64-70`), while the existing collector skips dotfiles only (`examples/memory-curation/nodes/collect.py:28-35`) and FR-878-era apply appends the visible system file `repo/_tombstones.md` (`examples/memory-curation/apply.py:24`, `107-149`). Without an explicit rule, `_tombstones.md` can become either noisy drift after restore/apply activity or an untested special case.

Fold this by naming the corpus predicate in the FR and tests: include only regular, non-symlink `.md` files under `<memory-root>/repo/`; exclude `.curation-state.json` by path; and either include `_tombstones.md` in both the marker and comparison or exclude it from both. The choice must be explicit, with a test proving a tombstone-only update does not accidentally trigger the threshold unless that is the intended behavior.

### R-3: Make fail-open observable in the SessionStart integration

Revise the hook integration so a broken advisory cannot be indistinguishable from "no drift." FR-877 correctly requires a bounded log line on advisory failure (`feature-requests/FR-877-memory-curation-staleness-advisory.md:72-75`), but the current briefing script discards stderr and masks all failures around `now.py` (`.github/hooks/scripts/session-briefing.sh:10-14`). A direct `|| true` wrapper around the advisory would repeat that silent-success shape, violating the repo commandment to bear witness of errors (`.github/copilot-instructions.md:217-221`).

Fold this by specifying the log path, maximum record size or rotation cap, timeout behavior on Darwin where `timeout` may be absent, and environment overrides for tests. The hook may still exit 0 and print no user-facing advisory on failure, but it must leave one bounded machine-readable failure record.

### R-4: Tighten acceptance criteria around generated files and tests

Add exact test/file expectations before enforcement. The FR names `examples/memory-curation/advisory.py` and `session-briefing.sh` (`feature-requests/FR-877-memory-curation-staleness-advisory.md:64-75`) and says CAP-247 should gain a new REQ (`feature-requests/FR-877-memory-curation-staleness-advisory.md:99-102`), but the acceptance criteria do not yet require marker schema validation, corrupt-marker behavior, threshold edge cases including deletion, or hook log assertions.

Fold this by requiring tests for: successful apply writes the marker; marker contains post-apply hashes and omits forgotten notes; advisory prints nothing below threshold; advisory prints exactly one line at threshold; absent-marker/non-empty corpus prints "never curated"; corrupt/unreadable marker exits nonzero for direct invocation; SessionStart integration exits 0 and logs bounded evidence for advisory failure; and no advisory code imports provider/network packages.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-877-memory-curation-staleness-advisory.md` folding R-1 through R-4 |
| D-2 | `examples/memory-curation/apply.py` marker write after successful apply |
| D-3 | `examples/memory-curation/advisory.py` pure-stdlib drift checker |
| D-4 | `.github/hooks/scripts/session-briefing.sh` advisory invocation with observable fail-open logging |
| D-5 | Unit tests for marker, advisory, hook integration, no-provider-import invariant, and temp-root safety |
| D-6 | `capabilities/CAP-247-memory-corpus-curation.yaml` extended with a new REQ and matching `@pytest.mark.req(...)` coverage |
| D-7 | `examples/memory-curation/README.md` Recurrence section |
| D-8 | FR implementation record and diary reflection |

Not authorized: running or modifying the FR-875 judgement graph; adding graph or prompt YAML; scheduling automatic curation drafts; running LLM calls from SessionStart; network egress; cross-device memory transport; user-scope or session-scope curation; changing judge/review/graph-authoring doctrine; broad hook policy changes outside the one SessionStart advisory call.

## Revised acceptance criteria

- [ ] AC-01: `apply.py` writes a versioned `.curation-state.json` into the memory root only after a successful apply transaction; the marker records `applied_at`, `manifest_sha256`, `disposition_sha256`, and post-apply live repo-note sha256 values; forgotten paths are absent from `notes`.
- [ ] AC-02: The marker is excluded from collection/advisory corpus enumeration; `_tombstones.md` handling is explicit and symmetric between marker and advisory comparison, with a test proving the intended behavior.
- [ ] AC-03: `examples/memory-curation/advisory.py` is pure stdlib, accepts `--memory-root` and `--threshold` (default 5), compares hashes not mtimes, and counts new, edited, and deleted notes against the post-apply marker.
- [ ] AC-04: Advisory direct invocation prints nothing and exits 0 below threshold; prints exactly one stdout line and exits 0 at or above threshold; prints exactly one stdout line and exits 0 when the marker is absent and the repo corpus is non-empty.
- [ ] AC-05: Advisory direct invocation treats malformed/unreadable marker or unreadable corpus paths as real errors: it exits nonzero and emits a bounded stderr diagnostic rather than faking no drift.
- [ ] AC-06: `.github/hooks/scripts/session-briefing.sh` runs the advisory with env-overridable memory root, threshold, timeout, and log path; advisory failure never blocks SessionStart, but appends one bounded log record.
- [ ] AC-07: Tests use fixture/temp memory roots only and never read or write the operator's real memory store.
- [ ] AC-08: Tests assert zero LLM/network/provider imports in the advisory path.
- [ ] AC-09: CAP-247 gains a new REQ for the curation-state/advisory contract; every new or changed test is tagged with that REQ.
- [ ] AC-10: `examples/memory-curation/README.md` gains a Recurrence section documenting the advisory model, threshold semantics, marker location, fail-open behavior, and why scheduling remains deliberately absent.
- [ ] AC-11: The FR records implementation status, decisions/deviations, validation evidence, and a diary reflection.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority does not activate until R-1 through R-4 are folded into `feature-requests/FR-877-memory-curation-staleness-advisory.md`. | GATE |
| C-2 | The marker must describe the post-apply live corpus; enforcement must prove a successful curation with `forget` rows does not immediately create deleted-note drift. | GATE |
| C-3 | The advisory path must remain zero LLM, zero network, pure stdlib. | GATE |
| C-4 | Automated tests must use temp/fixture memory roots only; no test may touch the operator's real memory store. | GATE |
| C-5 | Hook changes are enforcement-infrastructure changes and require human review before being treated as durable policy; the hook must fail open with bounded evidence, not silent success. | GATE |
| C-6 | Do not invoke the judge skill, judge adapter, judge graph, or YAMLGraph while enforcing this judgement. | GATE |

Authority granted: after the required revisions are folded, enforcement may add a local post-apply curation marker, a pure-stdlib drift advisory, and a fail-open SessionStart briefing line for repo-scope memory curation staleness only.
