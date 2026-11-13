# Feature Request: FR-1160 Remove the FR-1159 Map Memo Contrib and Its Demo

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved with revisions R-1..R-4 folded; see
[judgement](FR-1160-remove-map-memo-contrib.judgement.md)
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
`git show 1c8b0b85~1:<path>`. `is_this_a_graph`: No -- deterministic
reversal, registry reconciliation and absence witnesses; no model stage or
new graph/prompt artifact is required.
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
test. Its judgement was SPLIT; the retirement was implemented under the
recorded operator override. This FR reuses the implementation shape, not
that verdict's authority.
[FR-1155](FR-1155-prompt-cache-tokens-in-token-usage.md) § "Follow-up:
warm-first map dispatch" is the original use case. It is not implemented
here; it needs its own FR.

## Summary

Undo PR #771's code, example, test and registry changes. Every touched
non-FR file with no change after `1c8b0b85` returns to its content at
`1c8b0b85~1`; a file changed since keeps the later hunks and loses only
the FR-1159 ones (R-2); `ARCHITECTURE.md` is regenerated, never restored. FR documents, the
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
  - "git log --oneline 1c8b0b85..HEAD -- <each restored path> — record the implementation base SHA; any later commit on a restored path means hand-reversal of the FR-1159 hunks only (R-2)"
  - "git grep -n -F -e contrib.map_memo -e contrib/map_memo -e demos/map_memo -e CAP-302 -e REQ-YG-726 — after GREEN, hits only in feature-requests/, docs/diary/, tests/unit/test_fr1160_retirements.py; inspect any other hit, never delete history to pass"
  - "ls capabilities/CAP-303* and git grep -F REQ-YG-727 — both empty at implementation time, else take the next free ids"
  - "changelog/unreleased: does any released version contain fr-1159-map-memo-contrib.md — no means delete the fragment"
branches:
  - "a restored path changed after 1c8b0b85 → reverse only the FR-1159 hunks, keep the later ones, record path, commits and retained differences in the reconciliation table; a semantic conflict stops the FR for revised authority"
  - "a guard denies deleting the demo artifacts → stop and report the denial; do not retry through a different tool; any routing or guard correction needs separate authority"
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
  - python -m pytest tests/unit/test_fr1160_retirements.py tests/unit/test_fr1116_map_memo.py tests/unit/test_fr1120_map_memo_versions.py tests/unit/test_fr1113_meta_map.py tests/unit/test_fr1120_census_memo_graph.py tests/unit/test_fr335_module_map_compression.py -q --no-cov -p no:cacheprovider
  - docker run --rm -v "C:\src\yamlgraph:/src:ro" python:3.11-slim sh /src/scripts/ci_mirror_fr1160.sh  # recipe below, § Validation recipe
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
REQ-YG-727, module: the test file) and regenerate `ARCHITECTURE.md` in the
same commit, so strict requirement coverage holds at RED (FR-1134 AC-01
lesson). Every test fails on its actual parent by assertion, not by
collection or import error; the RED parent SHA and failure output are
recorded in this FR.

**2. GREEN commit** (`revert(contrib): FR-1160 remove the FR-1159 map memo contrib and demo`):

- Restore to `1c8b0b85~1` content (R-2: only paths with no later commit;
  otherwise reverse just the FR-1159 hunks):
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
- Run `python scripts/aggregate_capabilities.py` over the current registry:
  CAP-302 leaves `ARCHITECTURE.md`; unrelated generated content is kept.
- Add `changelog/unreleased/fr-1160-remove-map-memo-contrib.md`
  (`type: removal`, `scope: contrib`, `req: REQ-YG-727`).

**3. FR status.** The FR-1158 and FR-1159 **Status** lines were set to
Rejected with the operator's reason in this FR's planning commit, so the
judge reads them. The closing `docs(fr)` commit adds FR-1160's
implementation status and the completion reconciliation table.

### Validation recipe (R-4)

Tracked as `scripts/ci_mirror_fr1160.sh`, added in the RED commit. It runs
on the committed candidate (a clone of `/src` HEAD) as a non-root user in
`python:3.11-slim`, with the CI 3.11 leg's extras:

```sh
#!/bin/sh
set -e
apt-get update -qq >/dev/null && apt-get install -y -qq git curl >/dev/null
useradd -m w
su w -c '
set -e
git config --global --add safe.directory "*"
git clone -q /src ~/r && cd ~/r
git log --oneline -1
python -m venv ~/v && . ~/v/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev,digest,websearch,fsm,verify,rag,replicate,openai-proxy,examples-dungeon-master,otel,vision]"
python -m pytest tests/unit -q --no-cov -m "not slow" -n auto -p no:cacheprovider
python scripts/req_coverage.py --strict
ruff check yamlgraph/
ruff check --select PLW1514 --preview .
lint-imports
'
```

`-m "not slow"` keeps `process`-marked tests, so the retirement witness
runs. The candidate SHA (`git log --oneline -1`) and outcome are recorded
in the implementation status.

Kept unchanged as history: both FR documents and judgements,
`feature-requests/authoring-briefs/fr-1159-map-memo-demo-brief.md`, and
`docs/diary/diary-2026-11-13-reflection-fr-1159-the-node-the-evidence-did-not-earn.md`.

## Acceptance Criteria

Revised by the [judgement](FR-1160-remove-map-memo-contrib.judgement.md):

- [ ] AC-01: R-1 through R-4 are folded into the committed FR before
  implementation; the research record answers `is_this_a_graph`; the
  operations contain no denial-evasion branch.
- [ ] AC-02: A separate RED commit adds the process-marked REQ-YG-727
  witnesses, registers the retirement capability and regenerates
  architecture. Recorded execution on its actual parent fails by the
  intended assertions; GREEN makes the same witnesses pass.
- [ ] AC-03: Every listed deletion is absent, `examples/shared/map_memo.py`
  exists, both shared manifests declare `runtime.path: map_memo.py` without
  `runtime.module`, and the contrib initializer, vulture whitelist and
  examples index contain no `map_memo` token.
- [ ] AC-04: A per-path intervening-change check is recorded. Unchanged
  restoration paths, including the restored memo, equal `1c8b0b85~1`
  byte-for-byte; any changed path keeps unrelated hunks and has an explicit
  baseline/base/candidate reconciliation.
- [ ] AC-05: CAP-302 / REQ-YG-726 are removed from the active registry and
  replaced by CAP-303 / REQ-YG-727. Generated architecture reflects the
  current registry without losing unrelated entries; strict requirement
  coverage passes; no test references REQ-YG-726.
- [ ] AC-06: `git grep -n -F` for `contrib.map_memo`, `contrib/map_memo`,
  `demos/map_memo`, `CAP-302` and `REQ-YG-726` hits only `feature-requests/`,
  `docs/diary/` and `tests/unit/test_fr1160_retirements.py`.
- [ ] AC-07: The targeted selection (retirement witness, both memo suites,
  both consumer suites, module-map compression at budget 300) passes. No
  behavioural assertion is weakened.
- [ ] AC-08: The committed validation recipe and the lint/format/import
  checks pass on the recorded candidate; no result depends on an
  uncommitted helper or an unexplained deselection.
- [ ] AC-09: FR-1158 and FR-1159 keep their committed Rejected statuses,
  operator reason and FR-1160 links; their judgements, the authoring brief
  and the FR-1159 diary are unchanged. FR-1160 records status, decisions,
  commands, results and any restoration exceptions.
- [ ] AC-10: The FR-1159 unreleased fragment is deleted, an FR-1160
  removal fragment is added, and the completion diary has a metacognitive
  insight and **Seed:**.

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
