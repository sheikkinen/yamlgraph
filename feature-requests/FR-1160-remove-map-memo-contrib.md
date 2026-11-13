# Feature Request: FR-1160 Remove the FR-1159 Map Memo Contrib and Its Demo

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Requested:** 2026-11-13
**First consumer / first event:** the operator, on 2026-11-13, reading the
merged FR-1159 against the request it answered. The request was a
standalone "cached map" node for the FR-1155 follow-up use case (warm-first
dispatch so a map fan-out pays one Anthropic prompt-cache write instead of
one per concurrent branch). FR-1158 and FR-1159 instead built a cross-run
per-item result memo. The operator's verdict: both the use case and the
requested solution were lost, FR-1158 and FR-1159 are rejected, and their
code and examples are removed. The first event after this FR merges: the
next `yamlgraph` wheel no longer contains `yamlgraph/contrib/map_memo.py`,
and `examples/demos/map_memo` no longer exists.
**Research:** in-body dispositioned alternatives table (§ Alternatives
Considered). This is a removal of an unreleased change; the only research
question is what "before FR-1159" means per file, answered by
`git show 1c8b0b85~1:<path>`.
**Prior art:**
[FR-1159](FR-1159-map-memo-contrib.md) is the change removed here
(PR #771, squash `1c8b0b85`); this FR rejects it after merge.
[FR-1158](FR-1158-cached-map-node.md) was REJECTED at judgement and added no
code; this FR records the operator's reason on it as well.
[FR-1116](FR-1116-map-memo-file-corpus.md) and
[FR-1120](FR-1120-census-map-memo.md) are the memo's original home and
contract in `examples/shared`; this FR restores them byte-for-byte and does
not touch their behaviour.
[FR-1134](FR-1134-retire-fr-knowledge-graph-and-fr275-meta-tests.md) is the retirement
precedent: deleted capability, new retirement capability, absence witness
test. This FR follows it.
[FR-1155](FR-1155-prompt-cache-tokens-in-token-usage.md) § "Follow-up:
warm-first map dispatch" is the original use case. It is not implemented
here; it needs its own FR.

## Summary

Undo PR #771's code, example, test and registry changes, restoring every
touched non-FR file to its content at `1c8b0b85~1`. FR documents, the
FR-1159 judgement, the FR-1159 authoring brief and the FR-1159 diary entry
stay as history. FR-1158 and FR-1159 are marked Rejected with the
operator's reason. CAP-302 / REQ-YG-726 are retired and replaced by a
retirement capability whose test witnesses the absence.

## Value Statement

The repository stops shipping a contrib module and demo that no one asked
for, so the real cached-map work (FR-1155 follow-up) starts from a tree
that does not suggest the problem is already solved.

## Problem

PR #771 added `yamlgraph/contrib/map_memo.py` to the wheel, a demo
`examples/demos/map_memo`, CAP-302 / REQ-YG-726, a vulture whitelist entry,
a module-map budget bump (300 → 302) and an unreleased changelog fragment
that announces the contrib module. None of it serves the requested use
case. Left in place it:

- ships a public-looking `yamlgraph.contrib` API that the next release
  would have to keep or deprecate;
- names a demo `map_memo` next to the coming warm-first cached map, so two
  different meanings of "cached map" would sit side by side;
- leaves the unreleased changelog claiming a feature the operator rejected.

The change is unreleased (last release v0.6.6, before #771), so removal
costs no installed user anything.

## Ideal Result

The tree is as if PR #771 had merged only its FR documents and diary entry:
`examples/shared/map_memo.py` is the memo's only home and is loaded by
`path:` as under FR-1116/FR-1120; `yamlgraph/contrib` is as before; no
`map_memo` demo exists; the registry carries a retirement record instead of
CAP-302; FR-1158 and FR-1159 read Rejected with the reason.

## Planned Operations

```yaml
probes:
  - "git diff --name-status 1c8b0b85~1 1c8b0b85 — the closed list of files to restore or delete"
  - "git log 1c8b0b85..origin/main -- <each restored path> — any later commit on a restored path means merge by hand, not checkout"
  - "grep -r 'contrib.map_memo\\|contrib/map_memo\\|demos/map_memo\\|CAP-302\\|REQ-YG-726' outside feature-requests/ and docs/diary/ — must be empty after GREEN"
  - "changelog/unreleased: does any released version contain fr-1159-map-memo-contrib.md — no means delete the fragment"
branches:
  - "a restored path changed after 1c8b0b85 → hand-merge only the FR-1159 hunk, record it in the FR"
  - "the PreToolUse guard denies deleting examples/demos/map_memo/*.yaml → deletion is by git rm in a terminal, which the guard does not govern; if it does, stop and report rather than bypass"
  - "commit-msg gate demands a changelog fragment for the GREEN commit → add a type: removal fragment naming FR-1160"
  - "module-map test fails at 300 after restore → the generator still sees a contrib entry; find it, do not raise the budget"
delegations:
  - "judge.sh: 1 run, 2 if revisions are disputed"
  - "outsider.sh: 1 run on the PR"
  - "review.sh: 1 run from another session"
waits:
  - "judge"
  - "CI on the PR"
  - "operator merge decision"
commands:
  - scripts/judge.sh feature-requests/FR-1160-remove-map-memo-contrib.md
  - git checkout 1c8b0b85~1 -- <restored paths>
  - git rm -r examples/demos/map_memo yamlgraph/contrib/map_memo.py tests/unit/test_fr1159_map_memo_contrib.py capabilities/CAP-302-map-memo-contrib.yaml changelog/unreleased/fr-1159-map-memo-contrib.md
  - python scripts/aggregate_capabilities.py
  - python scripts/req_coverage.py --strict
  - docker run --rm -v "C:\src\yamlgraph:/src:ro" python:3.11-slim sh /src/tmp/fr1156_w_ci.sh
  - scripts/outsider.sh <pr> --comment
```

## Proposed Solution

**1. RED commit** (`test(contrib): FR-1160 RED map memo contrib retired`,
`SKIP=pytest`). Add `tests/unit/test_fr1160_retirements.py`, modelled on
`test_fr1134_retirements.py`, all `@pytest.mark.req("REQ-YG-727")`,
`pytestmark = pytest.mark.process`:

- these paths are absent: `yamlgraph/contrib/map_memo.py`,
  `examples/demos/map_memo`, `tests/unit/test_fr1159_map_memo_contrib.py`,
  `capabilities/CAP-302-map-memo-contrib.yaml`,
  `changelog/unreleased/fr-1159-map-memo-contrib.md`;
- `examples/shared/map_memo.py` exists;
- both `examples/shared/map_memo_*.tool.yaml` manifests declare
  `path: map_memo.py` and no `module:`;
- the token `map_memo` occurs in none of `yamlgraph/contrib/__init__.py`,
  `vulture_whitelist.py`, `examples/README.md`.

Add `capabilities/CAP-303-map-memo-contrib-retired.yaml` (fr: FR-1160,
REQ-YG-727, module: the test file) in the same commit so the requirement
exists when the test references it.

**2. GREEN commit** (`revert(contrib): FR-1160 remove the FR-1159 map memo contrib and demo`):

- Restore to `1c8b0b85~1` content: `ARCHITECTURE.md` (then regenerate),
  `capabilities/CAP-289-map-memo-file-corpus.yaml`,
  `capabilities/CAP-292-census-map-memo.yaml`, `examples/README.md`,
  `examples/shared/README.md`, `examples/shared/map_memo_merge.tool.yaml`,
  `examples/shared/map_memo_split.tool.yaml`,
  `tests/unit/test_fr1116_map_memo.py`,
  `tests/unit/test_fr1120_map_memo_versions.py`,
  `tests/unit/test_fr335_module_map_compression.py` (budget back to 300),
  `vulture_whitelist.py`, `yamlgraph/contrib/__init__.py`.
- Move `yamlgraph/contrib/map_memo.py` back to `examples/shared/map_memo.py`
  with `git mv`, restoring its pre-FR-1159 docstring (the only diff in the
  rename).
- Delete: `examples/demos/map_memo/` (all files),
  `tests/unit/test_fr1159_map_memo_contrib.py`,
  `capabilities/CAP-302-map-memo-contrib.yaml`,
  `changelog/unreleased/fr-1159-map-memo-contrib.md`.
- Run `python scripts/aggregate_capabilities.py`: CAP-302 leaves
  `ARCHITECTURE.md`, CAP-303 enters.

**3. FR status.** The FR-1158 and FR-1159 **Status** lines were set to
Rejected with the operator's reason in this FR's planning commit, so the
judge reads them. The closing `docs(fr)` commit adds FR-1160's
implementation status and the completion reconciliation table.

Kept unchanged as history: both FR documents and judgements,
`feature-requests/authoring-briefs/fr-1159-map-memo-demo-brief.md`, and
`docs/diary/diary-2026-11-13-reflection-fr-1159-the-node-the-evidence-did-not-earn.md`.

## Acceptance Criteria

- [ ] AC-01: `tests/unit/test_fr1160_retirements.py` is committed RED
  (fails on `1c8b0b85`) before the GREEN commit, and passes after it.
- [ ] AC-02: For every path in the restore list, `git diff 1c8b0b85~1 HEAD
  -- <path>` is empty, except `ARCHITECTURE.md`, whose only diff against
  `1c8b0b85~1` is the generated CAP-303 / REQ-YG-727 row and section (plus
  any generated rows from FRs merged after `1c8b0b85~1`).
- [ ] AC-03: `git diff 1c8b0b85~1 HEAD -- examples/shared/map_memo.py` is
  empty.
- [ ] AC-04: `git grep -n -e "contrib.map_memo" -e "contrib/map_memo" -e
  "demos/map_memo" -e "CAP-302" -e "REQ-YG-726"` returns hits only under
  `feature-requests/`, `docs/diary/` and `tests/unit/test_fr1160_retirements.py`.
- [ ] AC-05: `python scripts/req_coverage.py --strict` passes; REQ-YG-727
  is covered and REQ-YG-726 is not referenced by any test.
- [ ] AC-06: The Docker CI-mirror run passes, including
  `test_fr1116_map_memo.py`, `test_fr1120_map_memo_versions.py` and
  `test_fr335_module_map_compression.py` at budget 300.
- [ ] AC-07: FR-1158 and FR-1159 **Status** lines read Rejected with the
  operator's reason and a link to this FR.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| `git revert 1c8b0b85` wholesale | Rejected: it also deletes the FR-1158/FR-1159 documents, judgements and diary entry, which are the record of the deviation. |
| Keep the contrib module, delete only the demo | Rejected: the operator ruled both code and examples out; the contrib API is the larger long-term cost. |
| Delete CAP-302 and REQ-YG-726 with no replacement | Rejected: the absence would have no witness; FR-1134 is the precedent for a retirement capability. |
| Rewrite CAP-302 in place as the retirement record | Rejected: CAP-302's id and REQ-YG-726 would change meaning; ids are stable identifiers. |
| Also delete the FR-1116 memo in `examples/shared` | Out of scope: FR-1116/FR-1120 were requested, judged and have two consumers; the operator rejected FR-1158/FR-1159 only. |
| Implement the warm-first cached map in this FR | Out of scope: a removal and a feature in one FR mixes concerns; the warm-first map needs its own FR from the FR-1155 follow-up. |

## Related

- PR #771 (`1c8b0b85`), the change removed.
- [FR-1155 § Follow-up: warm-first map dispatch](FR-1155-prompt-cache-tokens-in-token-usage.md)
  and [FR-1155.research.md § Map fan-out spike](FR-1155.research.md): the
  original use case.
- `docs/diary/diary-2026-11-13-reflection-fr-1160-the-name-matched-the-wrong-precedent.md`.
