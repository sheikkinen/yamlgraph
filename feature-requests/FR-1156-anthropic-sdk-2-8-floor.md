# Feature Request: FR-1156 Raise the Anthropic SDK Floor to 2.8.0 and Re-Align the Untyped-Schema Walker

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**REQ:** REQ-YG-712 (existing, CAP-164)
**Requested:** 2026-11-13
**First consumer / first event:** PR #768 (FR-1155). CI `test (3.11)` and
`test (3.14)` failed on 2026-11-12 (run 43308399918). The FR-1155 diff does
not touch any of the 13 failing tests; all are in
`tests/unit/test_fr1123_sdk_parity.py`. Every open PR and the next push to
`main` hit the same red, because CI installs `pip install -e ".[dev]"`
unpinned and resolves `anthropic` 2.8.0 and `langchain-anthropic` 1.7.10.
**Research:** in-body probes (2026-11-13, local `anthropic` 2.8.0 /
`langchain-anthropic` 1.7.10, Python 3.13).
**Prior art:**
[FR-1123](FR-1123-untyped-subschema-constrained-decoding-gate.md) built the
untyped-subschema walker. It also added the parity test, which compares the
walker with the SDK's private `transform_schema` by exact error string. This FR
restores that parity under 2.8.0.
[FR-1125](FR-1125-refuse-unconstrained-objects-anthropic.md) added the
open-object rule and the content-parity half of the same test module.
2.8.0 does not change open-object hollowing: every content-parity case that
does not involve an untyped subschema still passes.
[FR-1154](FR-1154-anthropic-api-version-sampling-removed.md) made
`create_llm` correct under either SDK major. Its constraint 5 says "No pin is
added to `pyproject.toml`", meaning no cap that would block SDK 2. This FR
adds a floor, not a cap, so it does not contradict FR-1154. One consequence
follows: with `anthropic>=2.8.0`, the SDK header is always `2026-10-21`.
FR-1154's `elif` to the FR-1146 guard then becomes unreachable in a conforming
install. That branch is left in place here (see Out of Scope).
[FR-761](FR-761-reproducible-dependency-governance.md) owns `constraints/dev-py312.txt`.

## Summary

`anthropic` 2.8.0 changed `transform_schema` in two ways:

1. The untyped-subschema `ValueError` text grew a suffix. It is now
   `Schema must have a 'type', 'anyOf', 'oneOf', or 'allOf' field, or a 'const' or non-empty 'enum' of strings, numbers, booleans, or null.`
   The FR-1123 parity oracle matches the old text exactly. It therefore
   re-raises every rejection it should count. That accounts for 13 CI
   failures.
2. The SDK now accepts a subschema that has no `type` or composition keyword
   but does have a primitive `const` or a non-empty all-primitive `enum`.
   The yamlgraph walker still flags these as `untyped`. Pydantic emits this
   shape for a mixed-type `Literal` (`Literal["a", 1]` →
   `{"enum": ["a", 1]}`), so a valid prompt schema is falsely refused at lint
   and at compile time.

yamlgraph's `pyproject.toml` floors are `anthropic>=0.96.0` and
`langchain-anthropic>=1.5.1`. The committed constraints artifact pins
`anthropic==0.120.0`. CI therefore tests an SDK nobody pinned, and the walker
follows the 1.x rule while the SDK being tested follows the 2.8 rule.

## Value Statement

CI goes green again for every open PR, and `main` stops failing. The
compile/lint refusal again matches what the installed SDK actually does.
A graph author whose schema has a mixed-type `Literal` is no longer told the
field "has no type" when the provider would accept it.

## Problem

### Probe 1: CI failure reproduces locally

`python -m pytest tests/unit/test_fr1123_sdk_parity.py -q --no-cov -p no:randomly`
on `anthropic` 2.8.0 gives `14 failed, 20 passed`. 13 of the failures are the
CI set; each one raises `ValueError` from `anthropic/lib/_parse/_transform.py:167`
with the new text. The 14th, `test_ac07_private_sdk_import_lives_in_one_test_module`,
fails only on Windows because it compares `\` paths with `/` paths. CI on Linux
passes it; this FR fixes it with `.as_posix()` (a one-token change in a file
already being edited).

### Probe 2: 2.8.0 transform vs walker, literal-only subschemas

| schema | SDK 2.8.0 | walker (`find_untyped_subschemas`) |
|---|---|---|
| `{"enum": ["a", "b"]}` | accepts | `['(root)']` (refuses) |
| `{"const": "x"}` | accepts | `['(root)']` (refuses) |
| `{"enum": [None, 1]}` | accepts | `['(root)']` (refuses) |
| `{"enum": []}` | rejects | `['(root)']` |
| `{"enum": [{"a": 1}]}` | rejects | `['(root)']` |
| `{"const": {"a": 1}}` | rejects | `['(root)']` |
| model with `f: Literal["a", 1]` → `{"enum": ["a", 1]}` | accepts | `['f']` (refuses) |
| model with `f: Literal["a"]` → `{"const": "a", "type": "string"}` | accepts | `[]` |

The SDK's primitive predicate is
`value is None or isinstance(value, (str, int, float, bool))`
(`anthropic/lib/_parse/_transform.py`, `is_primitive`). When a literal is
present the transform sets `type_ = None`: compositions are still
transformed, but `properties`/`items` below a literal are never visited.

### Probe 4: constraints closure (dry run)

```
python -m pip install --dry-run --ignore-installed --report tmp/fr1156-report.json \
  -c <edited constraints> -e ".[dev,digest,websearch,fsm,verify]"
```

exit 0, no conflicts, every resolved package pinned and equal to its pin
except `yamlgraph` (editable), `pip`, and `sspilib` (Windows-only marker
dependency, absent from the Linux-generated artifact). Changed pins:
`anthropic` 0.120.0→2.8.0, `langchain-anthropic` 1.5.2→1.7.10,
`langchain-core` 1.5.1→1.8.0, `langsmith` 0.10.10→0.14.17,
`langchain-protocol` 0.0.18→0.0.21, `certifi` 2026.7.22→2026.10.23
(`langchain-core` 1.8.0 requires ≥2026.10.19). New pins: `httpx2` 2.12.0,
`httpcore2` 2.12.0, `truststore` 0.10.4, `opentelemetry-api` 1.45.2. An
unpinned-core dry run backtracked for >20 minutes and was abandoned; pinning
the cascade to the locally-installed working set resolved in seconds.

### Probe 3: dependency floors

`langchain-anthropic` declares `anthropic<2.0.0` up to 1.7.6 and drops the cap
from 1.7.7 onward (wheel `Requires-Dist`, 1.7.1–1.7.10 read locally). The
lowest version that can coexist with `anthropic` 2.8.0 is therefore
`langchain-anthropic` 1.7.7. 1.7.10 requires `langchain-core>=1.7.5`.
`anthropic` 2.8.0 adds `httpx2` and `opentelemetry-api` as new runtime
dependencies.

## Ideal Result

There is one Anthropic SDK rule, the installed 2.8+ one, and three places
agree with it: `pyproject.toml` floors, the constraints artifact, and the
walker. The parity test proves the agreement against the real transform.
CI on an unpinned install is green.

## Planned Operations

```yaml
probes:
  - "probe 1/2/3 above (done, recorded)"
  - "pip dry-run of the edited constraints set resolves (record command + result)"
branches:
  - "constraints cascade larger than the langchain-core family → stop, record, ask operator before regenerating the whole artifact"
delegations:
  - "judge.sh: 1 run"
  - "review.sh: 1 run after PR (operator session)"
waits:
  - "judge"
  - "CI"
commands:
  - bash scripts/judge.sh feature-requests/FR-1156-anthropic-sdk-2-8-floor.md
  - python -m pytest tests/unit/test_fr1123_sdk_parity.py tests/unit/test_fr1123_untyped_subschema.py tests/unit/test_fr1125_open_objects.py -q --no-cov
  - python -m pytest tests/unit -q --no-cov -m "not slow" -n auto
  - python scripts/req_coverage.py --strict
```

## Proposed Solution

1. **`pyproject.toml`**: set `anthropic>=2.8.0` and `langchain-anthropic>=1.7.7`.
2. **`constraints/dev-py312.txt`**: pin `anthropic==2.8.0` and
   `langchain-anthropic==1.7.10`, plus whatever minimal cascade the pip
   dry-run requires (`langchain-core`, `langsmith`, `langchain-protocol`,
   `httpx2`, `httpcore2`, `truststore`, `opentelemetry-api`). Add an amendment
   line under `# Generated:` naming FR-1156. The full regeneration on
   Python 3.12 stays the FR-761 follow-up.
3. **`yamlgraph/utils/schema_walk.py`**: in `_walk`'s untyped branch, a
   subschema with no `type`/composition/`$ref` is **not** untyped when it
   carries a primitive `const`, or a non-empty `enum` whose members are all
   primitive. As in the SDK, a literal also stops descent into
   `properties`/`items` (compositions are still walked). The module
   docstring states the rule. `_is_primitive` mirrors the SDK predicate.
4. **`tests/unit/test_fr1123_sdk_parity.py`**: `MISSING_KEYWORD` becomes the
   2.8.0 text. `_NESTED` gains the literal rows from Probe 2, so parity is
   proven on the newly accepted and still-rejected literal shapes.
5. **`tests/unit/test_fr1156_literal_subschema.py`** (new): direct walker
   witnesses for the literal rule, independent of the SDK.
6. `test_ac07_private_sdk_import_lives_in_one_test_module` compares
   `as_posix()` paths (Probe 1, 14th failure).

No production code imports the SDK's private module. The
`test_ac07_private_sdk_import_lives_in_one_test_module` invariant holds.

## Acceptance Criteria

- [ ] AC-01: `pyproject.toml` declares `anthropic>=2.8.0` and `langchain-anthropic>=1.7.7`.
- [ ] AC-02: `constraints/dev-py312.txt` pins `anthropic==2.8.0` and `langchain-anthropic==1.7.10`, and the FR records a pip dry-run showing that the edited set resolves for `.[dev,digest,websearch,fsm,verify]`.
- [ ] AC-03: `find_untyped_subschemas` returns `[]` for `{"enum": ["a","b"]}`, `{"const": "x"}` and `{"enum": [None, 1]}`, and `['(root)']` for `{"enum": []}`, `{"enum": [{"a": 1}]}` and `{"const": {"a": 1}}`.
- [ ] AC-04: A model with field `f: Literal["a", 1]` produces no untyped finding, so neither lint E016/W028 nor the compile refusal fires on it.
- [ ] AC-05: `tests/unit/test_fr1123_sdk_parity.py` passes on `anthropic` 2.8.0, including new parity rows for every Probe 2 schema.
- [ ] AC-06: Every new or changed test carries `@pytest.mark.req("REQ-YG-712")`. The walker witnesses are committed failing (RED, `SKIP=pytest`) before the walker change (GREEN).
- [ ] AC-07: `python -m pytest tests/unit -q --no-cov -m "not slow" -n auto` adds no failure relative to `origin/main` on the same host, and Linux CI is green.
- [ ] AC-08: `changelog/unreleased/fr-1156-anthropic-sdk-2-8-floor.md` has `type: fix`, `scope: deps`, `req: REQ-YG-712`.
- [ ] AC-09: The FR records the judgement fold, implementation status and any deviations.

## Out of Scope

- **Retiring FR-1154's SDK-1 branch.** The FR-1146 `elif` in `create_llm` is
  unreachable under `anthropic>=2.8.0`. Deleting it, and its `2023-06-01`
  tests, is a purge with its own blast radius (FR-1146/FR-071 tests), so it
  is a follow-up FR.
- **Full regeneration of `constraints/dev-py312.txt` on Python 3.12**: the
  standing FR-761 follow-up. No 3.12 interpreter exists on the authoring host.

## Alternatives Considered

**is_this_a_graph:** no. This is a dependency floor plus a deterministic
schema predicate.

| # | Alternative | Disposition |
|---|---|---|
| A | Cap `anthropic<2` | Rejected. It reverses FR-1154's intent, and `langchain-anthropic` ≥1.7.7 already resolves SDK 2 for every downstream install. |
| B | Match the oracle by prefix (`startswith("Schema must have a 'type'")`) and keep the floor | Rejected. It hides the semantic drift (Probe 2): the walker would keep refusing schemas the SDK accepts. The user asked for the bump. |
| C | Accept either message text (support both SDK majors) | Rejected. The two majors have different rules, so the walker cannot be correct for both. The floor picks one rule. |
| D | Floor plus walker realignment (this FR) | Chosen. |
