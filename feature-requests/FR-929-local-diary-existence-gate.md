# Feature Request: FR-929 Local pre-push diary existence gate — close the last CI-only gate

**Priority:** MEDIUM
**Type:** Enhancement (process enforcement, `.pre-commit-config.yaml` + `scripts/`)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-08-30
**First consumer / first event:** the next agent session that finishes a
`feat: FR-NNN` branch and runs `git push` in its worktree — the gate
fires at that push, before the PR exists, instead of two minutes later
in `diary-gate`. Concretely: the FR-929 branch itself is the first
witness (AC-05).
**Research:** [FR-929.research.md](FR-929.research.md)
(brief: [research-briefs/fr-929-local-diary-existence-brief.md](research-briefs/fr-929-local-diary-existence-brief.md),
run 2026-08-30, 5 personas, provenance in `research-runs.jsonl`)

**Prior art:** FR-158 (created the CI `diary-gate` — this FR does not
touch it); FR-373 (hardened remote substance validation, explicitly left
local hooks out of scope); FR-380 (closed the `Seed:` **content** parity
gap local↔CI, explicitly left broader parity out of scope — this FR
closes the remaining **existence** gap, the complement, not a repeat);
FR-144 (local reflection content enforcement); FR-742 (diary debt for
sessions that die before any commit — a briefing signal, disjoint path:
that FR handles work with no PR, this one handles work with a PR);
FR-192 (**rejected** a `pre-push` hook for *release-tag validation*,
rationale: "not installed by default, easily bypassed, the project does
not currently use them"). Disposition of the rejection: §Alternatives A1
distinguishes on all three grounds — the tag case was subsumed by
`release.sh`, this case has no subsuming script; "not used anywhere" was
circular and is dissolved by installing it; "easily bypassed" is the
accepted property of *every* local hook here (`SKIP=<id>`) and is why
the CI gate stays the merge boundary. No other rejected FR occupies this
territory.

## Summary

Add a `pre-push`-stage pre-commit hook that answers the one question no
local check currently asks — *does this branch contain a diary
reflection for the FR it claims to implement?* — and make it, plus the
existing local diary hooks, consume the same shared semantic contract
CI uses instead of a third inline re-implementation.

## Value Statement

The author learns a reflection is missing at `git push`, while the work
is still in working memory, instead of after a push → PR → CI round trip
that the repository's own history records failing at least five times
(FR-188, FR-191, FR-228, FR-761, and the FR-380 parity incident).

## Problem

Diary enforcement is split, and the split is asymmetric in *kind*, not
just in strictness:

| Question | Local | CI |
|---|---|---|
| Is a staged diary file well formed? (stubs, `Seed:`, filename) | ✅ `diary-reflection-check`, `diary-filename-check` | ✅ `diary-gate` |
| **Does a diary file exist at all for this FR?** | ❌ **nothing** | ✅ `diary-gate` |

Both local hooks are scoped `files: ^docs/diary/`. When no diary file is
staged, **neither hook runs at all** — absence is structurally
invisible to them. So a whole `feat: FR-NNN` branch can pass every local
hook on every commit and still fail at the PR.

The comparable artifact is gated locally: `changelog-required`
(`commit-msg` stage) blocks any `feat`/`fix` commit whose staged files
contain no `changelog/unreleased/*.md`. The diary has no equivalent —
and, importantly, **must not have the same one**. Doctrine puts the
reflection *last* (`.github/copilot-instructions.md:33`), so a
per-commit existence check would fail the first `feat` commit of every
arc for the absence of an artifact doctrine says comes later. Both
`process-boundary` research personas independently dissented on exactly
that shape (FR-929.research.md rows 1–2).

That is the real answer to "why only in CI": **a per-commit hook cannot
see a branch, and until now the PR was the only place in the workflow
with branch-range visibility.** It is not a deliberate policy — it is
the shape of the only boundary that was available.
Secondary defect found while researching: `scripts/gate_artifact_semantics.sh`
declares itself the "shared semantic contract for CI artifact
validation" but has **no local consumer** — its only importers are
`.github/workflows/commitlint.yml` and unit tests. The two local diary
hooks re-implement a subset as inline bash inside the YAML. That is the
mechanism by which FR-380's parity gap arose in the first place, and it
will produce the next one.

## Ideal Result

`git push` is the moment of truth. A branch that claims `FR-NNN` in a
`feat`/`fix` commit and carries no valid reflection for it never reaches
the remote; the author sees the same message, from the same contract
file, that CI would have shown — only sooner and for free. Nothing about
the doctrine ordering changes: the reflection is still written last, it
is simply *checked* at the first instant "last" has passed. The CI gate
is untouched and remains the merge boundary; the local gate is a
strictly cheaper copy of it, not a second opinion.

## Proposed Solution

### In scope

1. **`scripts/check_diary_existence.sh`** — a shell script, stdlib git
   only, that takes a commit range and:
   - collects commit subjects in the range; extracts `FR-NNN` from any
     subject matching `^(feat|fix)(\(.*\))?:` — mirroring the CI job's
     trigger semantics (which reads the PR title; the PR title is the
     squash subject, so the sets agree);
   - for each such `FR-NNN`, requires a path in the range's diff
     matching `docs/diary/.*reflection.*fr-NNN([^0-9]|$)`
     (case-insensitive, per FR-188 fix 3);
   - `source`s `scripts/gate_artifact_semantics.sh` and calls
     `validate_diary_reflection_file` on each match — **no new
     validation logic**;
   - exits 0 with no FR refs found (docs/chore/refactor branches pass
     silently, identical to CI's skip).

2. **Pre-commit hook `diary-existence-gate`**, `stages: [pre-push]`,
   `pass_filenames: false`, invoking the script with
   `${PRE_COMMIT_FROM_REF}..${PRE_COMMIT_TO_REF}` (pre-commit exports
   these for the pre-push stage); falls back to
   `origin/main..HEAD` when the refs are absent.

3. **Installation**: add `pre-commit install --hook-type pre-push` to
   `CLAUDE.md` and `reference/onepager-development-process.md` next to
   the two existing install lines. Git worktrees share
   `$GIT_COMMON_DIR/hooks`, so a single install covers every
   `scripts/worktree.sh new` lane — which is what dissolves FR-192's
   "not installed by default" objection under the FR-889 flow.

4. **De-duplication**: rewrite the two existing inline diary hooks
   (`diary-reflection-check`, `diary-filename-check`) to call a small
   script that sources the same contract, so all three local diary
   checks and CI share one definition of "valid reflection". This is in
   scope because item 1 would otherwise be the *third* copy — the
   brief's own constraint.

### Out of scope (purge list)

- Any change to `.github/workflows/commitlint.yml` or the `diary-gate`
  job. CI remains the merge boundary; this FR is a strictly-local
  early-warning copy of it.
- Extending the same pre-push treatment to `changelog-gate`,
  `demo-gate`, or `commitlint` parity. One artifact, one gate.
- Auto-generating the reflection, by LLM or template. The gate reports
  absence; the author writes.
- Any new bypass channel. `SKIP=diary-existence-gate` is inherited from
  the pre-commit framework and is sufficient; `--no-verify` remains
  forbidden by the pre-command guard.
- A `pre-push` hook for anything other than this check.

## Acceptance Criteria

- [ ] **AC-01 (RED first):** `scripts/check_diary_existence.sh` fails on
      a fixture range whose commits carry `feat: FR-999` and no
      `docs/diary/*reflection*fr-999*` path, with the CI-identical error
      text and exit 1.
- [ ] **AC-02:** the same script passes when the range contains a valid
      reflection for every referenced FR, and passes (exit 0) when the
      range contains no `feat`/`fix` + `FR-NNN` commit at all.
- [ ] **AC-03:** the script rejects a present-but-invalid reflection
      (empty, ≤100 bytes, no `##` header, no `Seed:`) — proving the
      shared contract is actually being sourced, not re-implemented.
      Test asserts the script `source`s `scripts/gate_artifact_semantics.sh`.
- [ ] **AC-04:** `.pre-commit-config.yaml` declares
      `diary-existence-gate` with `stages: [pre-push]`; the two existing
      diary hooks no longer contain inline validation bash. Asserted in
      `tests/unit/test_precommit_hooks.py`.
- [ ] **AC-05 (the witness):** the FR-929 branch itself is pushed with
      the hook installed, and the push is blocked before its own
      reflection is written. Evidence pasted into this FR's
      Implementation section — an unfaked RED at the real boundary.
- [ ] **AC-06:** `CLAUDE.md` and `reference/onepager-development-process.md`
      carry the `--hook-type pre-push` install line; capability registry
      updated (extend `CAP-45`/`CAP-54` or add a REQ under the existing
      diary CAP — no new CAP for a parity fix).
- [ ] **AC-07:** changelog fragment + diary reflection for FR-929
      (`diary-gate`, and now `diary-existence-gate`, both apply to this
      very PR).

## Failing Acceptance Tests (RED plan)

RED artifact: `tests/unit/test_fr929_diary_existence_gate_red.py`

1. `test_ac01_missing_reflection_for_feat_fr_fails`
2. `test_ac02_valid_reflection_passes_and_no_fr_ref_skips`
3. `test_ac03_invalid_reflection_content_fails_via_shared_contract`
4. `test_ac04_precommit_declares_pre_push_stage_and_no_inline_bash`

```bash
pytest tests/unit/test_fr929_diary_existence_gate_red.py -q --no-cov
```

Regression: `pytest tests/unit/test_precommit_hooks.py tests/unit/test_ci_diary_gate.py -q --no-cov`

## Alternatives Considered

Dispositioned from `FR-929.research.md` (5 personas) plus the FR-192
precedent.

**Recorded honestly: no persona in the committed run proposed the
accepted candidate.** Four of five converged on `prepare-commit-msg` /
`commit-msg` variants and three of those dissented against their own
candidate; the fifth proposed deletion. The librarian's dissent states
the decisive fact without naming its consequence — branch completion
"cannot [be distinguished] without upstream visibility that only CI
possesses **after push**". A1 is the author's synthesis of that
sentence: push is the first local moment with upstream visibility. The
research's value here was elimination, not proposal.

| # | Candidate | Source | Disposition |
|---|---|---|---|
| A1 | `pre-push`-stage hook with branch-range visibility | **author, from the librarian row's own rationale** | **Accepted** — the only mechanism whose lifecycle matches a last-written artifact, and the one the librarian's dissent implies without stating. Overrides FR-192's rejection on all three of its grounds (see Prior art). Uses the pre-commit framework's native `pre-push` stage — no new dependency. |
| A2 | `commit-msg`-stage existence check, mirroring `changelog-required` | data-process-planner (*dissent*) | **Rejected** — commit-msg runs once per commit, not once per branch; it would fail the first `feat` commit for an artifact doctrine schedules last. Inverting doctrine to fit the hook is the tail wagging the dog. The persona dissented against its own candidate. |
| A3 | `prepare-commit-msg` hook detecting "final commit" via reflog | os-infra-primitivist (*dissent*) | **Rejected** — "branch is finished" is undecidable from the reflog; false positives on every ordinary commit, and it still lacks push visibility. Persona dissented against its own candidate. |
| A4 | `prepare-commit-msg` hook invoking a `graph-tool-demo`-style subgraph | yamlgraph-native-planner (*pursue*) | **Rejected** — inherits A3's undecidable trigger, and the question ("does path X exist in range Y?") is deterministic `git diff --name-only`. `is_this_a_graph`: no. An LLM graph here is `framework_costume`. |
| A5 | Delete the local diary hooks; rely solely on CI | subtractionist (*pursue*) | **Rejected** — subtraction is normally the right default here, but this one *loses* FR-380's committed content parity and buys nothing: the round-trip cost stays, and the honest-enforcement argument it rests on ("a last-written artifact cannot be gated locally") is exactly what A1 falsifies. Recorded because it is the strongest case against this FR. |
| A6 | `prepare-commit-msg` reading branch state via `git rev-parse` / `git diff` | librarian (*dissent*) | **Rejected by its own author** — and its rationale is A1's evidence: only post-push has the needed visibility. |
| A7 | Do nothing; document the latency | — | **Rejected** — five recorded incidents, all discovered remotely. `detection_without_enforcement`: advisory documentation is what we already have. |

## Related

- [.pre-commit-config.yaml](../.pre-commit-config.yaml) — `diary-reflection-check`, `diary-filename-check`, `changelog-required`
- [.github/workflows/commitlint.yml](../.github/workflows/commitlint.yml#L292) — `diary-gate`
- [scripts/gate_artifact_semantics.sh](../scripts/gate_artifact_semantics.sh) — `validate_diary_reflection_file`, the contract to be shared
- [feature-requests/FR-380-precommit-diary-seed-marker-parity.md](FR-380-precommit-diary-seed-marker-parity.md)
- [feature-requests/FR-373-substance-validation-diary-changelog-gates.md](FR-373-substance-validation-diary-changelog-gates.md)
- [feature-requests/FR-192-draconian-changelog-release-gate.md](FR-192-draconian-changelog-release-gate.md) — the `pre-push` rejection being overturned in scope
- [feature-requests/FR-742-undelivered-diary-detection.md](FR-742-undelivered-diary-detection.md)

## Questions for the human (as options, or 'none')

1. **Scope of item 4 (de-duplication).** Options: (a) rewrite both
   existing inline diary hooks to source the shared contract — *default,
   recommended*, since item 1 otherwise creates a third copy and the
   brief forbids it; (b) new hook only, leave the inline bash, accept a
   third definition. Evidence for (a): FR-380 exists solely because two
   definitions drifted.
2. **Overturning FR-192.** Options: (a) treat FR-192's `pre-push`
   rejection as scoped to release-tag validation and install the hook
   type — *default, recommended*, per the three-ground distinction
   above; (b) honour the rejection repo-wide and close this FR in favour
   of A5/A7. Evidence for (a): FR-192's own rationale was that
   `release.sh` subsumed the check; no script subsumes this one.
