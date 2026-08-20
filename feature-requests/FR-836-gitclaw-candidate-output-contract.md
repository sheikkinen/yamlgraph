# Feature Request: FR-836 GitClaw Candidate Output Contract

**Priority:** HIGH
**Type:** Platform / GitClaw runtime contract repair
**Status:** Enforced 2026-08-20 - canonical and consumer rollout published;
20/20 acceptance criteria satisfied; FR-831 Task 6 unblocked
**Effort:** 0.5 day
**Requested:** 2026-08-20
**Parent:** FR-831
**Depends on:** FR-829, FR-830, FR-832, FR-833, FR-834, FR-835
**Blocks:** FR-831 Task 6
**Prior art:** Commit `ff200831962eb34158e77a4c38919776e21800bf`
added a fallback for generated graphs whose output state key differs from their
feature slug, but it recognizes only self-nested dictionary values. FR-832
through FR-834 validly emit one plain string under `state_key: candidate` and
therefore produce a candidate in YAMLGraph state that cron discards. FR-835
preserves this extractor while making the same-run envelope available; it does
not define how cron discovers a graph's final output key.
**First consumer / first event:** The next Oulu consumer cron execution, when
all three source graphs return a non-empty plain `candidate` string and cron
must preserve each as a successful same-run result before a Task 6 composer can
consume it.

## Summary

Repair GitClaw's generated-feature output contract before FR-831 Task 6. Make
`candidate` the explicit final state key for newly generated feature graphs,
align policy and all four pipeline prompts, and teach cron to accept a non-empty
plain or self-nested `candidate` value after preserving the existing
feature-slug extraction path.

Do not scan arbitrary state strings. `date`, `run_instant`,
`source_snapshots`, built-in runtime metadata, errors, and other inputs must
never become output merely because they are the only non-empty string. Empty,
missing, or structurally invalid output remains a recorded feature failure.

This is a shared platform repair, not the Task 6 composer. It changes no Oulu
source graph, adapter, source contract, composition manifest, workflow, secret,
ledger, containment rule, output artifact, or publication behavior.

## Evidence and Root Cause

The consumer's three 2026-08-20 source artifacts all failed with
`no output in state`, while each bounded reason lists `candidate` among the
returned state keys:

- `oulu-harbour-source-snapshot`;
- `oulu-procurement-source-snapshot`; and
- `oulu-municipal-notice-source-snapshot`.

Each graph declares `state_key: candidate`, and its deterministic Python node
returns one Markdown string. Current `extract_output(state, feature)` first
checks `state[feature]`, then restricts fallback candidates to dictionary values
where the outer key is repeated inside the dictionary. A direct regression
probe is therefore:

```python
extract_output({"date": "2026-08-20", "candidate": "ok"}, "feature")
# current result: None
# required result: "ok"
```

The `ff200831` regression test covered
`{"aphorism": {"aphorism": "build less"}}`, not a Python node's plain string.
Existing template features happen to work because `horoscope` and `haiku` use
their feature slug as output key and `aphorism` is self-nested. The latent bug
affects any deterministic Python-node feature whose plain output key differs
from its directory slug, including the planned Task 6 composer.

## Decision

`candidate` becomes the canonical generated-feature output state key:

1. generated graphs MUST write their one final non-empty output to
   `state_key: candidate`;
2. cron preserves existing feature-slug extraction for already committed
   legacy features;
3. if the feature-slug path has no output, cron checks exactly `candidate` and
   accepts a plain non-empty string or the existing self/single-value nested
   shape through `_coerce`;
4. the existing self-nested dictionary fallback remains for committed custom
   LLM keys such as `aphorism`;
5. cron does not infer output from arbitrary plain state values; and
6. zero valid outputs still fails closed with the existing bounded diagnostic.

This explicit key is preferred over parsing `graph.yaml` inside cron. Graph
schema parsing would add a second YAMLGraph configuration reader and couple the
runner to node/edge topology solely to discover one platform output field. It
is also preferred over accepting any lone string, which could publish an input
such as `date` or `source_snapshots` after a failed node.

## Platform Changes

Implement first in canonical `sheikkinen/gitclaw`:

1. add red focused tests proving plain `candidate` output currently fails;
2. update `tools/cron_run.py` so `extract_output` checks exact `candidate`
   after the feature-slug path and before the retained self-nested fallback;
3. update `policy/generated-features.md` to require exactly one non-empty final
   output under `state_key: candidate` for newly generated graphs;
4. update plan, judge, enforce, and review prompts to plan, require, implement,
   and verify the exact key;
5. add no graph parser, dependency, command option, workflow, migration, or
   fallback over arbitrary state strings; and
6. roll out only the exact human-reviewed canonical files to
   `sheikkinen/gitclaw-oulu-civic-intelligence` after canonical validation.

The three source features remain immutable. Their existing `candidate` keys
already satisfy the repaired contract.

## Exact Change Surface

Canonical implementation and consumer rollout are restricted to these exact
repository-relative paths:

| Purpose | Canonical and consumer path |
|---|---|
| Runtime extraction | `tools/cron_run.py` |
| Runtime focused tests | `tests/test_intake_tools.py` |
| Composition regression | `tests/test_cron_run.py` |
| Policy/prompt consistency tests | `tests/test_generated_feature_policy.py` |
| Binding generated-feature policy | `policy/generated-features.md` |
| Planning contract | `prompts/plan.yaml` |
| Judgement contract | `prompts/judge.yaml` |
| Enforcement contract | `prompts/enforce.yaml` |
| Review contract | `prompts/review.yaml` |

The consumer receives byte-identical copies of only these reviewed canonical
files. `README.md`, source features, workflows, dependencies, ledger/state,
containment, outputs, and every other path remain unchanged.

## Validation

Focused tests must prove:

- plain `{"candidate": "text"}` succeeds unchanged when the feature slug is
  different;
- a supported nested `candidate` shape remains accepted;
- whitespace-only, missing, list, numeric, or multi-field invalid candidates
  do not become output;
- `date`, `run_instant`, `source_snapshots`, error text, and built-in metadata
  are never selected as output;
- feature-slug plain/nested extraction remains unchanged;
- the committed self-nested custom-key fallback remains unchanged;
- a failed node with no valid output still records the existing bounded
  failure;
- a successful plain source candidate enters an FR-835 envelope byte-for-byte
  and permits its dependent composer to execute in a synthetic composition
  test;
- policy and all four prompts name `state_key: candidate` and prohibit
  arbitrary-state inference; and
- the complete canonical and consumer suites pass.

After exact consumer parity, run a bounded no-LLM witness through the consumer
cron runner using synthetic YAMLGraph JSON states for the three existing source
slugs. Each state must contain real runtime metadata plus one distinct plain
`candidate` string. Prove all three results are successful, candidate bytes are
unchanged in the ordered composition envelope, and `source_snapshots` is not
selected as output.

Then run each committed Oulu source graph through the consumer's actual
`run_feature` path with its normal bounded public read and no LLM node. Record
only success/failure, candidate byte count, and declared source health; retain
no live candidate text or raw response. All three must be recognized as output
before FR-831 Task 6 is filed. Live source unavailability may be retried once
only to distinguish transport availability, but an extractor failure or graph
contract failure blocks Task 6.

Run these exact validation commands from the applicable repository root.
Artifacts under `tmp/` are local evidence and are not committed:

```bash
# Canonical focused red/green and full suite
/Users/sami.j.p.heikkinen/src/yamlgraph/.venv/bin/pytest -q \
      tests/test_intake_tools.py tests/test_cron_run.py \
      tests/test_generated_feature_policy.py \
      2>&1 | tee tmp/fr836-canonical-focused.log
/Users/sami.j.p.heikkinen/src/yamlgraph/.venv/bin/pytest -q \
      2>&1 | tee tmp/fr836-canonical-full.log

# Consumer synthetic witness and full suite
/Users/sami.j.p.heikkinen/src/yamlgraph/.venv/bin/pytest -q \
      tests/test_cron_run.py -k three_plain_source_states \
      2>&1 | tee tmp/fr836-consumer-synthetic.log
/Users/sami.j.p.heikkinen/src/yamlgraph/.venv/bin/pytest -q \
      2>&1 | tee tmp/fr836-consumer-full.log

# Consumer parity hashes, in the Exact Change Surface table order
platform_files=(
      tools/cron_run.py tests/test_intake_tools.py tests/test_cron_run.py
      tests/test_generated_feature_policy.py policy/generated-features.md
      prompts/plan.yaml prompts/judge.yaml prompts/enforce.yaml prompts/review.yaml
)
for file in "${platform_files[@]}"; do shasum -a 256 "$file"; done \
      | tee tmp/fr836-consumer-parity.sha256
```

Run the actual-source witness from the consumer repository with YAMLGraph on
`PATH`. It calls only the three committed deterministic source graphs and emits
no candidate text or raw response:

```bash
PATH="/Users/sami.j.p.heikkinen/src/yamlgraph/.venv/bin:$PATH" \
/Users/sami.j.p.heikkinen/src/yamlgraph/.venv/bin/python - <<'PY' \
      | tee tmp/fr836-consumer-live.json
import json
from pathlib import Path
from tools import cron_run

rows = []
for slug in (
            "oulu-harbour-source-snapshot",
            "oulu-procurement-source-snapshot",
            "oulu-municipal-notice-source-snapshot",
):
            ok, text = cron_run.run_feature(
                        Path("features") / slug / "graph.yaml", "2026-08-20"
            )
            health = None
            if ok:
                        health = next(
                                    (
                                                line.split(":", 1)[1].strip()
                                                for line in text.splitlines()
                                                if line.lower().startswith("source health:")
                                    ),
                                    "not-declared",
                        )
            rows.append(
                        {
                                    "feature": slug,
                                    "recognized": ok,
                                    "candidate_bytes": len(text.encode("utf-8")) if ok else 0,
                                    "source_health": health,
                        }
            )
assert all(row["recognized"] for row in rows), rows
print(json.dumps(rows, separators=(",", ":")))
PY
```

The implementation status must record these five log/hash paths, exact test
counts, both commit SHAs, both human approvals, and every failed/red attempt.
None of the artifacts may contain candidate text, raw responses, secrets, or
environment values.

## Human Gates

A human must review the exact canonical runtime, policy, prompt, and test diff
plus red/green evidence before canonical commit or push. After canonical
publication, a human must separately review the exact consumer parity diff and
hash report before consumer commit or push. Direct push capability does not
waive either gate.

## Acceptance Criteria

- [x] AC-01: Direct red test reproduces plain `candidate` rejection against the
      canonical baseline
- [x] AC-02: FR records `candidate` as the exact generated-feature output key
      while preserving legacy feature-slug and self-nested extraction
- [x] AC-03: Canonical `extract_output` accepts non-empty plain `candidate`
      output unchanged after the feature-slug path
- [x] AC-04: Supported nested `candidate` output remains accepted through the
      existing coercion rules
- [x] AC-05: Empty, missing, whitespace-only, list, numeric, multi-field
      invalid, or otherwise invalid candidate output fails closed
- [x] AC-06: `date`, `run_instant`, `source_snapshots`, errors, and built-in
      runtime state cannot be selected as output
- [x] AC-07: Existing feature-slug plain/nested extraction remains unchanged
- [x] AC-08: The committed self-nested custom-key fallback remains unchanged
- [x] AC-09: A failed node with no valid output retains the existing bounded
      failure recording
- [x] AC-10: Exact policy and plan/judge/enforce/review prompt files require
      `state_key: candidate` and prohibit arbitrary-state inference
- [x] AC-11: Synthetic composition test proves a plain source candidate becomes
      an unchanged successful envelope entry and its composer executes
- [x] AC-12: Recorded canonical focused and full-suite commands pass
- [x] AC-13: Human approves the exact canonical diff before canonical
      commit/push
- [x] AC-14: Exact reviewed canonical files reach the Oulu consumer with
      matching recorded hashes
- [x] AC-15: Recorded full consumer-suite command passes
- [x] AC-16: Human approves the exact consumer parity diff before consumer
      commit/push
- [x] AC-17: Synthetic consumer witness proves all three plain source states,
      metadata exclusion, exact bytes, and ordered composition
- [x] AC-18: Bounded actual `run_feature` witnesses recognize all three
      committed Oulu source outputs without retaining live candidate text
- [x] AC-19: No source graph/adapter, composition feature, workflow, dependency,
      ledger/state, containment, secret, issue #1, output, notification, or
      publication change
- [x] AC-20: FR records canonical/consumer commits, commands, logs, hashes,
      both human reviews, witnesses, deviations, and failed attempts before
      Task 6 filing

## Enforcement Record

Enforced and independently audited on 2026-08-20.

- Canonical GitClaw commit:
  `2a0a3c4fbb53d81884ca162dcf3c714b96a99e9b`.
- Oulu consumer parity commit:
  `33ec4467f7ed06d3b156695af7959b2e9fa35c77`.
- A human approved the exact nine-file canonical commit/push after reviewing
  red/green evidence and an audit with no blocker or high finding.
- A human separately approved the exact nine-file consumer commit/push after
  SHA-256 parity and an independent audit with no finding.
- Canonical focused suite: 60 passed in
  `tmp/fr836-canonical-focused.log`; canonical full suite: 101 passed in
  `tmp/fr836-canonical-full.log`.
- Consumer synthetic witness: 1 passed and 29 deselected in
  `tmp/fr836-consumer-synthetic.log`; consumer full suite: 101 passed in
  `tmp/fr836-consumer-full.log`.
- Exact consumer file hashes are retained in
  `tmp/fr836-consumer-parity.sha256`; the independent audit confirmed every
  reviewed consumer blob matches canonical commit `2a0a3c4` byte-for-byte.
- Actual `run_feature` evidence is retained as metadata only in
  `tmp/fr836-actual-source-witness.json` and
  `tmp/fr836-actual-source-retry.json`. All three committed source slugs were
  recognized with declared source health `ok`: harbour 336 bytes,
  procurement 2613 bytes, and municipal notices 2548 bytes. No candidate text
  or raw response was retained. The one contract-permitted retry resolved
  transient unavailable health from harbour and procurement.
- Ruff check/format, Radon grade-D scan, editor diagnostics, and
  `git diff --check` passed. Runtime and composition test files remain below
  the 450-line hard limit.
- Initial red evidence was three failures; adversarial review then exposed two
  fail-closed gaps for malformed candidate dictionaries and reserved nested
  metadata. Both were repaired before publication. A final low audit request
  for explicit precedence, arbitrary-string, and underscore-metadata tests was
  also folded before either commit.
- No source graph/adapter, composer, issue, workflow, dependency, ledger/state,
  containment, secret, output, notification, publication, or cadence surface
  changed. FR-831 Task 6 was not filed during this enforcement.

## Prior Art Disposition

| Prior art | Disposition |
|---|---|
| FR-831 | Direct parent; repair the discovered Task 6 prerequisite, then resume the staged queue |
| FR-829 | Preserve bounded public-read and same-directory policy; only `policy/generated-features.md` may change to name the output key, with no retrieval or origin change |
| FR-830 | Preserve repository-scoped append-only ledger identity; no ledger, state, or repository-identity file may change |
| FR-832 / FR-833 / FR-834 | Preserve generated source code and contracts; their existing exact `candidate` keys are the acceptance witnesses |
| FR-835 | Preserve strict composition manifests, opaque same-run envelopes, resource bounds, and two human rollout gates |
| `ff200831` | Preserve feature-slug and self-nested fallback behavior; close its missing plain custom-key case |
| `tools/cron_run.py` | Repair output identification only; do not alter scheduling, process containment, result recording, or bounds |

## Alternatives Rejected

- **File Task 6 now:** its deterministic Python node would use the same plain
  candidate shape and be recorded as failed even when it produced output.
- **Edit the three source graphs to use their directory slugs:** duplicates a
  platform convention across generated code, invalidates reviewed artifacts,
  and leaves future Python-node features exposed.
- **Accept any lone plain state string:** can publish `date`,
  `source_snapshots`, or another input after node failure.
- **Parse every graph in cron to infer terminal state keys:** creates a second
  graph-schema reader and unnecessary topology coupling for one explicit
  output field.
- **Read candidate text from prior output files:** violates FR-835 same-run
  composition and can silently substitute stale state.
- **Treat all-source failure as sufficient Task 6 evidence:** FR-835 proves
  structural failure transport, but Task 6 also requires real successful
  source reuse.

## Scope Fence

FR-836 authorizes one tests-first canonical GitClaw output-contract repair and
one exact consumer rollout. It authorizes no Task 6 issue, source edit, adapter
copy, source rediscovery, LLM synthesis, bulletin output, cron cadence change,
workflow or dependency change, issue #1 action, or publication. Any broader
runtime need stops for a separately judged FR.
