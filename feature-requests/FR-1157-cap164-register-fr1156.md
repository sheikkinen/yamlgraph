# Feature Request: FR-1157 Register FR-1156 in CAP-164 and State the Literal Rule in REQ-YG-712

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented (approved with revisions; R-1, R-2 folded; see
[judgement](FR-1157-cap164-register-fr1156.judgement.md))
**REQ:** REQ-YG-712 (existing, CAP-164)
**Requested:** 2026-11-13
**First consumer / first event:** the FR-1156 PR (branch
`fix/fr-1156-anthropic-2`). Its fast unit run on the committed GREEN
`f69b58c6`, in a clean CI-mirror container, failed exactly one test,
`test_changelog_req_cross_wiring.py::TestChangelogReqIntegrity::test_no_req_collision_across_unrelated_frs`:
`REQ-YG-712 claimed by FR-1156 (fragment) but FR-1156 capability has no capability`.
The PR cannot merge until this is fixed, and PR #768 waits on that merge.
**Research:** in-body dispositioned alternatives table (§ Alternatives Considered).
**Prior art:**
[FR-1156](FR-1156-anthropic-sdk-2-8-floor.md) is the parent change; its
round-3 amendment request was refused by the judge's round cap
("re-file a shorter plan as a new FR file"), which is why this FR exists.
[FR-1125](FR-1125-refuse-unconstrained-objects-anthropic.md) is the
precedent: it appended itself to CAP-164 `fr:` for the same REQ.
[FR-1123](FR-1123-untyped-subschema-constrained-decoding-gate.md) wrote the
REQ-YG-712 text that FR-1156 makes incomplete.

## Summary

FR-1156's changelog fragment declares `req: REQ-YG-712` (its AC-09). The
cross-wiring gate requires every FR that claims a REQ in a fragment to be
listed in the owning capability's `fr:` field, and CAP-164 does not list
FR-1156. Separately, REQ-YG-712's text defines "untyped" as "lacking
type/anyOf/oneOf/allOf/$ref", which is no longer the shipped rule: FR-1156
also accepts a primitive `const` or a non-empty all-primitive `enum`.

## Value Statement

The FR-1156 PR (and with it PR #768) can merge with a green suite, and the
capability registry describes the rule the code enforces.

## Problem

The test is the condemning witness: it fails on `f69b58c6` and is the only
failure in the clean CI-mirror run (1 failed, 7646 passed, 57 skipped).

## Ideal Result

CAP-164 lists every FR that claims REQ-YG-712, and REQ-YG-712's text
states the rule the walker implements.

## Planned Operations

```yaml
probes:
  - "done: clean CI-mirror run on f69b58c6 (FR-1156 Implementation Status)"
branches:
  - "any other failure after the edit → stop, record, new FR"
delegations:
  - "judge.sh: 1 run"
waits:
  - "judge"
  - "CI"
commands:
  - python -m pytest tests/unit/test_changelog_req_cross_wiring.py -q --no-cov
  - python scripts/req_coverage.py --strict
  - "CI-mirror recipe below, on the committed candidate"
```

**CI-mirror recipe (R-2).** Run from the repository root on Docker; `/src`
is the read-only checkout, the clone takes the committed `HEAD` only.
Extras are the CI 3.11 leg's (`.github/workflows/workflow.yml`), unpinned
as CI installs them:

```sh
docker run --rm -v "$PWD:/src:ro" python:3.11-slim sh -c '
set -e
apt-get update -qq && apt-get install -y -qq git curl >/dev/null
useradd -m w
su w -c "
set -e
git config --global --add safe.directory \"*\"
git config --global user.email witness@example.invalid
git config --global user.name witness
git clone -q /src ~/r && cd ~/r && git log --oneline -1
python -V; uname -sm; id -un
python -m venv ~/v && . ~/v/bin/activate
pip install -q --upgrade pip
pip install -q -e \".[dev,digest,websearch,fsm,verify,rag,replicate,openai-proxy,examples-dungeon-master,otel,vision]\"
pip show anthropic langchain-anthropic langchain-core | grep -E \"^(Name|Version)\"
python -m pytest tests/unit -q --no-cov -m \"not slow\" -n auto
"'
```

## Proposed Solution

One file, `capabilities/CAP-164-structured-output-fallback.yaml`:

1. `fr: FR-464, FR-998, FR-1121, FR-1123, FR-1125` →
   `fr: FR-464, FR-998, FR-1121, FR-1123, FR-1125, FR-1156`.
2. In REQ-YG-712 `text`, replace
   `untyped (lacking type/anyOf/oneOf/allOf/$ref, FR-1123)` with
   `untyped (lacking type/anyOf/oneOf/allOf/$ref and carrying no primitive
   const or non-empty all-primitive enum, FR-1123/FR-1156)`, and (R-1)
   replace `object (type object with no declared properties, which the
   transform` with `object (type object with no declared properties and
   carrying no primitive const or non-empty all-primitive enum, which the
   transform`. Only these two clause replacements; all other text unchanged.

No new REQ, capability, test, or other field. It lands as a commit in the
FR-1156 PR, because that PR cannot pass CI without it.

## Acceptance Criteria

Revised by the judgement (verbatim):

- [x] AC-01: CAP-164 `fr:` is exactly `FR-464, FR-998, FR-1121, FR-1123, FR-1125, FR-1156`; its prior entries and order are unchanged.
- [x] AC-02: REQ-YG-712 `text` contains exactly the proposed untyped replacement and R-1 open-object replacement; a baseline-relative diff proves no other capability field or requirement text changed.
- [x] AC-03: `python -m pytest tests/unit/test_changelog_req_cross_wiring.py -q --no-cov` and `python scripts/req_coverage.py --strict` exit zero without test or gate modifications.
- [x] AC-04: The committed R-2 recipe executes the unchanged fast-unit command on the committed candidate in the non-root Linux/3.11 CI mirror and exits zero; the implementation record contains its identity, environment, command and totals. The corresponding Linux CI test checks for that candidate also pass.
- [x] AC-05: FR-1157 records implementation status, revision folds and validation outcomes. The repair lands in the FR-1156 PR using its existing REQ-YG-712 fragment, without a separate fragment; the scoped Distill record contains a **Seed:**.

## Alternatives Considered

**is_this_a_graph:** no.

| # | Alternative | Disposition |
|---|---|---|
| A | Drop `req:` from the FR-1156 fragment | Rejected: violates FR-1156 AC-09 and hides the REQ the change alters. |
| B | Exempt FR-1156 in the cross-wiring test | Rejected: weakens a gate to pass a change. |
| C | Register only (item 1), leave the REQ text | Rejected: registry would then misstate the rule it owns. |
| D | Register and correct the text (this FR) | Chosen; matches FR-1125's precedent. |

## Implementation Status

- Commit `327d8c85` (`chore(capabilities)`; a `fix` type requires a fragment, which the judgement forbids).
  `fr:` gains `FR-1156`; REQ-YG-712 `text` gets exactly the two clause replacements. The
  `cap-architecture-sync` hook regenerated the matching `ARCHITECTURE.md` line, committed with it.
- AC-03: `test_changelog_req_cross_wiring.py` 2 passed; `req_coverage.py --strict` exit 0.
- AC-04: the inline recipe above, run verbatim on committed `327d8c85` (Python 3.11.18, Linux x86_64,
  user `w`; anthropic 2.8.0, langchain-anthropic 1.7.10, langchain-core 1.8.0): **7647 passed,
  57 skipped, 1 xfailed**, exit 0. Linux CI on PR #769 green (run 43374850780); merged as `02f6827c`.
- Distill: [diary-2026-11-13-reflection-fr-1156-the-error-string-was-the-cheap-half.md](../docs/diary/diary-2026-11-13-reflection-fr-1156-the-error-string-was-the-cheap-half.md) (shared with FR-1156).
