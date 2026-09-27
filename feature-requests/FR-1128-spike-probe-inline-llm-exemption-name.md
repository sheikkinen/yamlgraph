# Feature Request: The #729 spike probe breaks every commit's inline-LLM check

**Priority:** HIGH
**Type:** Bug
**Status:** Approved with revisions ([judgement](FR-1128-spike-probe-inline-llm-exemption-name.judgement.md), 2026-09-27); R-1..R-3 folded 2026-09-27
**Effort:** 0.5 day
**Requested:** 2026-09-27
**First consumer / first event:** any branch based on current `main` that
stages a `.py` file. The first recorded case is FR-1124 on 2026-09-27: two
commits were refused by `inline-llm-check` because of a file that is not in
their diff.
**Research:** in-body dispositioned alternatives table (see
[Alternatives Considered](#alternatives-considered)); this is a one-file
naming defect with no design space worth a research run.
**Prior art:**
- [047-lint-inline-llm.md](047-lint-inline-llm.md) wrote the rule this FR
  enforces. This FR does not change the rule.
- [FR-599](FR-599-l7-affect-recall-miss-decomposition-probe.md) added the
  `probe_` exemption for read-only diagnostic probes. This FR uses that
  exemption and does not widen it.
- [FR-1125](FR-1125-refuse-unconstrained-objects-anthropic.md) consumes the
  spike's findings. It does not touch the probe's file name.
- [FR-1110](FR-1110-unit-test-runtime-sandbox.md) and
  [FR-916](FR-916-ban-dry-run-phrase.md) share only the retrieval nouns
  `llm` and `exemption`. They concern the unit-test sandbox and a banned
  phrase, not the inline-LLM lint. Dismissed.

## Summary

#729 committed `docs/spikes/constrained-object-2026-09-27/probe.py`. The
file has a `def main()` and imports `create_llm` and `langchain_anthropic`
without a graph loader, so `scripts/lint_inline_llm.py` flags it. The hook
runs with `pass_filenames: false` and scans the whole tree, so every commit
that stages any `.py` file now fails. Nothing at the merge boundary runs the
lint against the repository, which is how the file reached `main`.

## Value Statement

Contributors on any branch can commit Python again without a bypass, and
the next file that breaks the rule fails CI on its own PR.

## Problem

- `python scripts/lint_inline_llm.py` returns 1 on `origin/main` `d7539f93`,
  and `probe.py` is the only violation.
- The file is a throwaway research probe. FR-599 already exempts files
  whose names contain `probe_`. This one is named `probe.py`, so the
  exemption misses it.
- `tests/unit/test_lint_inline_llm.py` only scans temporary directories,
  and no workflow runs the lint. The rule is enforced only by a local hook,
  and #729 got past it.

## Ideal Result

`main` has zero inline-LLM violations, and a unit test in CI proves it on
every PR. A violation then fails the PR that introduces it, not the next
unrelated commit.

## Proposed Solution

1. RED (R-1): add `test_repository_has_no_inline_llm_violations` to
   `tests/unit/test_lint_inline_llm.py`. It resolves
   `repo_root = Path(__file__).resolve().parents[2]`, calls
   `scan_directory(repo_root)` and asserts the result equals `[]`. The RED
   commit comes before the rename, and its failure output names
   `docs/spikes/constrained-object-2026-09-27/probe.py`.
2. GREEN: `git mv` the probe to
   `docs/spikes/constrained-object-2026-09-27/probe_constrained_object.py`,
   and update its three references: the probe's own `Run:` docstring line
   and two lines in the spike `README.md`. The probe's code, the output
   files and `scripts/lint_inline_llm.py` stay unchanged.

## Acceptance Criteria

The judgement's revised list is binding.

- [ ] AC-01: a RED commit on `d7539f93`, made before the rename, adds
  `test_repository_has_no_inline_llm_violations`.
  - The test resolves `Path(__file__).resolve().parents[2]`, calls
    `scan_directory(repo_root)`, asserts the result equals `[]` and carries
    `@pytest.mark.req("REQ-YG-073")`.
  - It fails with output naming
    `docs/spikes/constrained-object-2026-09-27/probe.py`, and the failure is
    not an import, collection or fixture error.
- [ ] AC-02: a separate, later GREEN commit renames the tracked file to
  `docs/spikes/constrained-object-2026-09-27/probe_constrained_object.py`.
  After it, the repository test passes, `scan_directory(repo_root) == []`,
  and `python scripts/lint_inline_llm.py` exits 0.
- [ ] AC-03 (R-2): `git diff --exit-code d7539f93 -- scripts/lint_inline_llm.py
  .pre-commit-config.yaml` exits 0.
- [ ] AC-04: the old name is gone and the new name is in place.
  - `git grep -n "probe\.py" -- docs/spikes/constrained-object-2026-09-27/`
    returns no matches.
  - The `Run:` line and both README references name
    `probe_constrained_object.py`.
  - The new path is tracked and the old path is not.
- [ ] AC-05: the focused inline-LLM test module, the non-slow unit suite
  and `python scripts/req_coverage.py --strict` all exit 0.
- [ ] AC-06 (R-3): a `changelog/unreleased/*.md` fragment has `type: fix`,
  names FR-1128 and REQ-YG-073, describes the restored repository-wide
  invariant, and passes the changelog checks.
- [ ] AC-07 (R-3): FR-1128 records its Implemented status, the RED and
  GREEN SHAs, the validation commands and results, the decisions and any
  deviations. A Distill entry in `docs/diary/` contains `Seed:`.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Add `docs/spikes/` to `EXCLUDE_PATHS` | Rejected. It widens a guard to admit a file that the existing exemption already covers under the right name (`guard_widening_when_caught`). |
| Rewrite the probe as a graph | Rejected. The probe measures what the library does to a wire schema below the graph layer, and a graph would hide exactly that. |
| Delete the probe | Rejected. The spike's claims would lose their reproduction record. |
| Run `lint_inline_llm.py` as a new CI workflow step | Rejected in favour of a unit test. The unit suite already runs in CI, so it needs no new workflow surface. |
| SKIP=inline-llm-check on downstream commits | Rejected by the operator on 2026-09-27. |

## Related

- `scripts/lint_inline_llm.py` (`EXCLUDE_PATHS`), `.pre-commit-config.yaml`
  (`inline-llm-check`).
- PR #729, FR-1124 (blocked branch).
