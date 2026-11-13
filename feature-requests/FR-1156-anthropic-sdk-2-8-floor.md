# Feature Request: FR-1156 Raise the Anthropic SDK Floor to 2.8.0 and Re-Align the Untyped-Schema Walker

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed (round 2: round 1 REJECTED, R-1..R-4 folded; see
[judgement](FR-1156-anthropic-sdk-2-8-floor.judgement.md))
**REQ:** REQ-YG-712 (existing, CAP-164)
**Requested:** 2026-11-13
**First consumer / first event:** PR #768 (FR-1155). CI `test (3.11)` and
`test (3.14)` failed on 2026-11-12 (run 43308399918). The FR-1155 diff does
not touch any of the 13 failing tests; all are in
`tests/unit/test_fr1123_sdk_parity.py`. Every open PR and the next push to
`main` hit the same red, because CI installs `pip install -e ".[dev]"`
unpinned and resolves `anthropic` 2.8.0 and `langchain-anthropic` 1.7.10.
**Research:** in-body Probes 1–7 (2026-11-13) and the committed in-body
dispositioned alternatives table (§ Alternatives Considered, six solution
classes).
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
`create_llm` correct under either SDK major. Its judgement explicitly
excluded dependency upgrades from its authority (Not authorized; C-6), so
that judgement does not permit this change; this FR is the separately judged
authority for the upgrade. One consequence follows: with `anthropic>=2.8.0`, the SDK header is always `2026-10-21`.
FR-1154's `elif` to the FR-1146 guard then becomes unreachable in a conforming
install. That branch is left in place here (see Out of Scope).
[FR-761](FR-761-reproducible-dependency-governance.md) owns `constraints/dev-py312.txt`
and its obligation: the artifact reproduces the CI-tested surface on
Python 3.12 via its documented install command. An amendment must therefore
be witnessed by a clean Python 3.12 install, not only by a resolver run on
another interpreter (Probe 6).

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
   `{"enum": ["a", 1]}`), so a Python output model that the provider would
   accept is falsely refused at bind (`bind_structured_output`, reached by
   `execute_prompt(..., output_model=...)` and `tools/agent.py`).
   YAML prompt schemas cannot produce this shape: `resolve_type` accepts
   only basic types, `list[T]` and `dict[K, V]`
   (`yamlgraph/schema_loader.py` `resolve_type`), and `output_schema` maps
   `enum` to `str` (`build_pydantic_model_from_json_schema`). Lint (E016/W028)
   and compile therefore never see a literal-only subschema; their behaviour
   is unchanged and the drift is reachable only at the bind boundary.

yamlgraph's `pyproject.toml` floors are `anthropic>=0.96.0` and
`langchain-anthropic>=1.5.1`. The committed constraints artifact pins
`anthropic==0.120.0`. CI therefore tests an SDK nobody pinned, and the walker
follows the 1.x rule while the SDK being tested follows the 2.8 rule.

## Value Statement

CI goes green again for every open PR, and `main` stops failing. The shared
walker again matches what the installed SDK actually does. A Python caller
whose output model has a mixed-type `Literal` is no longer told the field
"has no type" when the provider would accept it.

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

### Probe 3: dependency floors

`langchain-anthropic` declares `anthropic<2.0.0` up to 1.7.6 and drops the cap
from 1.7.7 onward (wheel `Requires-Dist`, 1.7.1–1.7.10 read locally). The
lowest version that can coexist with `anthropic` 2.8.0 is therefore
`langchain-anthropic` 1.7.7. 1.7.10 requires `langchain-core>=1.7.5`.
`anthropic` 2.8.0 adds `httpx2` and `opentelemetry-api` as new runtime
dependencies.

### Probe 4: constraints closure (dry run, supplementary)

```
python -m pip install --dry-run --ignore-installed --report tmp/fr1156-report.json \
  -c <edited constraints> -e ".[dev,digest,websearch,fsm,verify]"
```

Windows / Python 3.13 (supplementary only, not the artifact's target):
exit 0, no conflicts; every resolved package pinned and equal to its pin
except `yamlgraph` (editable), `pip`, and `sspilib` (a Windows-only marker
dependency outside the Linux artifact). An unpinned-core dry run backtracked
for >20 minutes and was abandoned.

### Probe 5: literal traversal (real `anthropic` 2.8.0 `transform_schema`)

| schema | SDK 2.8.0 | rule |
|---|---|---|
| `{"const": "x", "enum": ["a","b"]}` | accepts, keeps both | const and enum eligible independently |
| `{"const": "x", "enum": [{"a":1}]}` | accepts (enum folded into description) | one eligible literal suffices |
| `{"const": {"a":1}, "enum": ["a"]}` | accepts (const folded) | same |
| `{"type": "object", "enum": ["a"]}` | accepts → `{"enum": ["a"]}` | literal drops `type`: no open-object hollowing |
| `{"type": "object", "enum": ["a"], "properties": {"u": {}}}` | accepts; `properties` folded into description | no descent below a literal |
| `{"type": "array", "const": "x", "items": {}}` | accepts; `items` folded | same |
| `{"anyOf": [{}], "enum": ["a"]}` (also `oneOf`+const, `allOf`+const) | rejects (child `{}`) | compositions still walked |
| `{"enum": ["a"], "$defs": {"D": {"type":"object","properties":{"v":{}}}}}` | rejects | `$defs` still walked |
| `{"enum": ["a"], "$ref": "#/$defs/X"}` | accepts | `$ref` still stops |
| `{"enum": [null,"s",1,2.5,true]}`, `{"const": null}`, `{"const": false}` | accepts | every primitive category |
| `{"enum": []}`, `{"enum": ["a", ["b"]]}` | rejects | empty / non-primitive member |

**Traversal contract (frozen):** at each node, `$defs` is walked first;
`$ref` stops; a node is *literal* when its `enum` is a non-empty list of
primitives or it has a `const` that is primitive (each tested
independently). The first present composition is walked whether or not the
node is literal. A literal node with no composition is never `untyped`.
A literal node is never descended by `type` (`properties`/`items`) and is
never an `open_object`.

### Probe 6: clean Linux / Python 3.12 install of the amended artifact

`docker run --rm -v <repo>:/src:ro python:3.12-slim sh /src/w312.sh` (Appendix)
(Docker 29.9.3; Python 3.12.16, Linux x86_64): copies `pyproject.toml`,
`README.md`, `LICENSE`, `yamlgraph/`, `constraints/` into a clean
container, runs the artifact's own documented command
`pip install -c constraints/dev-py312.txt -e ".[dev,digest,websearch,fsm,verify]"`
(exit 0), then diffs `pip freeze --exclude-editable` against the pin lines:
**IDENTICAL** (no unpinned package, no pin missing). `anthropic` 2.8.0,
`langchain-core` 1.8.0 import.

### Probe 7: declared minimum pair

`docker run --rm python:3.12-slim` with
`pip install anthropic==2.8.0 langchain-anthropic==1.7.7` (resolves
`langchain-core` 1.8.0): imports; `transform_schema` on a model with
`f: Literal["a", 1]` returns `{"enum": ["a", 1], ...}`; `{}` is rejected
with the 2.8.0 text; `ChatAnthropic(...).with_structured_output(M,
method="json_schema")` binds (`RunnableSequence`, no request sent).
The floor `langchain-anthropic>=1.7.7` is therefore exercised, not inferred.

## Ideal Result

There is one Anthropic SDK rule, the installed 2.8+ one, and three places
agree with it: `pyproject.toml` floors, the constraints artifact, and the
walker. The parity test proves the agreement against the real transform.
CI on an unpinned install is green.

## Planned Operations

```yaml
probes:
  - "probes 1-7 above (done, recorded)"
branches:
  - "any changed or new pin beyond the ten in Proposed Solution 2 → stop, amend the FR, re-judge; never regenerate the whole artifact"
  - "Probe 6 re-run not IDENTICAL → stop, amend"
delegations:
  - "judge.sh: 1 run per round"
  - "review.sh: 1 run after PR (operator session)"
waits:
  - "judge"
  - "CI"
commands:
  - bash scripts/judge.sh feature-requests/FR-1156-anthropic-sdk-2-8-floor.md
  - python -m pytest tests/unit/test_fr1156_literal_subschema.py tests/unit/test_fr1123_sdk_parity.py tests/unit/test_fr1123_untyped_subschema.py tests/unit/test_fr1125_open_objects.py -q --no-cov -p no:randomly
  - python -m pytest tests/unit -q --no-cov -m "not slow" -n auto
  - python scripts/req_coverage.py --strict
  - ruff check yamlgraph/ tests/ && ruff format --check yamlgraph/ tests/ && lint-imports
  - docker run --rm -v <repo>:/src:ro python:3.12-slim sh /src/w312.sh  # Appendix script
```

## Proposed Solution

1. **`pyproject.toml`**: set `anthropic>=2.8.0` and `langchain-anthropic>=1.7.7`
   (Probe 7 exercises exactly this minimum pair).
2. **`constraints/dev-py312.txt`**: exactly these ten lines change, plus an
   FR-1156 amendment comment under `# Generated:`; nothing else:

   | pin | before | after |
   |---|---|---|
   | anthropic | 0.120.0 | 2.8.0 |
   | langchain-anthropic | 1.5.2 | 1.7.10 |
   | langchain-core | 1.5.1 | 1.8.0 |
   | langsmith | 0.10.10 | 0.14.17 |
   | langchain-protocol | 0.0.18 | 0.0.21 |
   | certifi | 2026.7.22 | 2026.10.23 (`langchain-core` 1.8.0 requires ≥2026.10.19) |
   | httpx2 | — | 2.12.0 (new, `anthropic` 2.x) |
   | httpcore2 | — | 2.12.0 (new, `httpx2`) |
   | truststore | — | 0.10.4 (new, `httpx2`) |
   | opentelemetry-api | — | 1.45.2 (new, `anthropic` 2.x) |

   Probe 6 is the reproducibility witness; Probe 4 is supplementary.
3. **`yamlgraph/utils/schema_walk.py`**: implement the Probe 5 traversal
   contract. `_is_primitive` mirrors the SDK predicate; `_has_literals`
   tests `enum` and `const` independently. The module docstring and the
   `find_untyped_subschemas` docstring state the literal rule.
4. **`tests/unit/test_fr1123_sdk_parity.py`**: `MISSING_KEYWORD` becomes the
   2.8.0 text. `_NESTED` gains every Probe 2/5 row, at the root and nested
   under a property, plus a literal-masked object, so rejection and content
   parity run against the real transform. The content oracle's
   `_concrete_objects` restates the SDK's literal stop locally (it must not
   call the walker it checks). Unrelated SDK exceptions still propagate.
5. **`tests/unit/test_fr1156_literal_subschema.py`** (new): SDK-independent
   walker witnesses for every Probe 5 row (exact paths), the literal
   open-object rule, the pydantic mixed-literal model, and the bind boundary:
   `bind_structured_output` binds the mixed-literal model and still refuses
   a neighbouring `Any` field by name.
6. `test_ac07_private_sdk_import_lives_in_one_test_module` compares
   `as_posix()` paths (Probe 1, 14th failure).

Lint (E016/W028) and compile are unchanged and get no new witness: no YAML
prompt schema can express a literal-only subschema (Summary item 2), so a
lint/compile fixture for it cannot be authored. Their existing FR-1123
witnesses stay green.

No production code imports the SDK's private module. The
`test_ac07_private_sdk_import_lives_in_one_test_module` invariant holds.

## Acceptance Criteria

- [ ] AC-01: `pyproject.toml` declares `anthropic>=2.8.0` and `langchain-anthropic>=1.7.7`; Probe 7 records the minimum-pair install/import/transform/bind witness.
- [ ] AC-02: `constraints/dev-py312.txt` differs from `origin/main` by exactly the ten pins in Proposed Solution 2 plus the FR-1156 amendment comment; Probe 6 (clean Linux/Python 3.12 install via the artifact's documented command, freeze IDENTICAL to pins) passes on the committed artifact.
- [ ] AC-03: `find_untyped_subschemas` returns `[]` for `{"enum": ["a","b"]}`, `{"const": "x"}` and `{"enum": [None, 1]}`, and `['(root)']` for `{"enum": []}`, `{"enum": [{"a": 1}]}` and `{"const": {"a": 1}}`; every primitive category and non-primitive case has its own row.
- [ ] AC-04: Every Probe 5 row has an exact-path walker witness: literal stops type descent and open-object findings; compositions and `$defs` under a literal report their child paths; `$ref` stops; const/enum eligibility is independent.
- [ ] AC-05: A pydantic model with `f: Literal["a", 1]` yields no untyped finding; `bind_structured_output` (Anthropic, `json_schema`) binds it, and refuses the same model with a neighbouring `g: Any`, naming `g` and not `f`.
- [ ] AC-06: `tests/unit/test_fr1123_sdk_parity.py` executes (no skip, no deselect) and passes on `anthropic` 2.8.0 across the committed census, existing open-object fixtures, and every Probe 2/5 row at root and nested, for both rejection and content parity; the only private-SDK import remains in that module and its path assertion is platform-neutral.
- [ ] AC-07: Every new or changed test carries `@pytest.mark.req("REQ-YG-712")`. The behavioural witnesses are committed failing (RED, `SKIP=pytest`) before the walker change (GREEN).
- [ ] AC-08: The targeted command in Planned Operations passes with no failure; `req_coverage.py --strict`, ruff check/format and `lint-imports` pass; Linux CI is green. Any failure in the fast unit suite caused by this host is recorded with its cause and shown identical on `origin/main` in a temporary worktree; Linux CI is the binding gate.
- [ ] AC-09: `changelog/unreleased/fr-1156-anthropic-sdk-2-8-floor.md` has `type: fix`, `scope: deps`, `req: REQ-YG-712`; the FR records each judgement fold, implementation status, the exact dependency diff, the validation environments, and deviations; a `docs/diary/` entry with a **Seed:** is added.

## Out of Scope

- **Retiring FR-1154's SDK-1 branch.** The FR-1146 `elif` in `create_llm` is
  unreachable under `anthropic>=2.8.0`. Deleting it, and its `2023-06-01`
  tests, is a purge with its own blast radius (FR-1146/FR-071 tests), so it
  is a follow-up FR.
- **Full regeneration of `constraints/dev-py312.txt`**: the standing FR-761
  follow-up; this FR amends ten pins only.

## Alternatives Considered

**is_this_a_graph:** no. This is a dependency floor plus a deterministic
schema predicate.

Six solution classes. The oracle-text repairs (prefix match, accept both
messages) are not classes of their own: they fix the 13 red tests but not
the semantic drift, and appear only as parts of classes 2 and 3.

| # | Class | Evidence | Strongest case for it | Disposition |
|---|---|---|---|---|
| 1 | **Cap** `anthropic<2` (and `langchain-anthropic<1.7.7`) | Probe 3: 1.7.7+ resolve SDK 2 for every downstream install | Zero code change; old rule stays true | Rejected. Downstream installs already get SDK 2 via `langchain-anthropic`; a cap forces them onto 1.7.6 and freezes them out of FR-1154's work. It hides the drift rather than closing it. |
| 2 | **Dual-major support**: version-dependent predicate in the walker (`anthropic.__version__` ≥ 2.8 → literal rule) and a version-aware oracle (expected text per major) | Probes 1, 2, 5 (the rules differ only by the literal clause) | Keeps `anthropic>=0.96` users working; no floor | Rejected on cost, not impossibility: two maintained branches in a pure module that the linter imports, an SDK import into `schema_walk.py` (now import-free), and a parity matrix CI can only exercise for one major at a time (unpinned CI resolves 2.8). The untested branch would decay. |
| 3 | **Oracle repair only** (prefix match) + no walker change | Probe 1 | Smallest diff; CI green | Rejected: leaves Probe 2's false refusal at bind; the parity rows for accepted literals would fail, so it can only pass by not testing them. |
| 4 | **Normalize mixed literals at the boundary** (rewrite `{"enum": ["a", 1]}` to `anyOf` of typed `const`s before binding) | Probe 5 (SDK accepts both forms) | Walker rule unchanged; works under either major | Rejected: changes the schema sent to the provider (FR-1125's content-parity premise is that we send what the model declares), adds a rewrite step at a boundary FR-1123 deliberately kept read-only, and still needs the oracle text fix. |
| 5 | **Pin exact versions in `pyproject.toml`** (`anthropic==2.8.0`) | FR-761 owns pins in the constraints artifact, not the package metadata | Fully deterministic CI | Rejected: a library pinning exact versions breaks every consumer resolving alongside other langchain packages; reproducibility belongs in the constraints artifact (FR-761). |
| 6 | **Floor + walker realignment + bounded constraints amendment** (this FR) | Probes 1–7 | One rule, three places agree, parity proven on the real transform, artifact reproduces on 3.12 | Chosen. Cost: drops SDK-1 users (they must upgrade to 2.8+); leaves FR-1154's SDK-1 branch unreachable (Out of Scope). |

## Appendix: witness scripts

Probe 6 (`docker run --rm -v <repo>:/src:ro python:3.12-slim sh /src/w312.sh`):

```sh
#!/bin/sh
# FR-1156 witness: clean Linux / Python 3.12 install from the amended constraints.
set -e
mkdir -p /w && cd /w
cp -r /src/pyproject.toml /src/README.md /src/LICENSE /src/yamlgraph /src/constraints .
python -V
uname -sm
pip install --quiet --upgrade pip
pip install --quiet -c constraints/dev-py312.txt -e ".[dev,digest,websearch,fsm,verify]"
echo "install exit=$?"
pip freeze --exclude-editable | sed 's/\r$//' | sort -f > /tmp/freeze.txt
grep -E '^[A-Za-z0-9]' constraints/dev-py312.txt | sed 's/\r$//' | sort -f > /tmp/pins.txt
echo "--- freeze vs pins (< freeze only, > pins only) ---"
diff /tmp/freeze.txt /tmp/pins.txt && echo "IDENTICAL"
python -c "import anthropic, langchain_anthropic, langchain_core; print('anthropic', anthropic.__version__, 'langchain-core', langchain_core.__version__)"
```

Probe 7 (`docker run --rm -v <repo>:/src:ro python:3.12-slim sh /src/wmin.sh`):

```sh
#!/bin/sh
# FR-1156 witness: declared minimum pair anthropic 2.8.0 + langchain-anthropic 1.7.7.
set -e
python -V
pip install --quiet "anthropic==2.8.0" "langchain-anthropic==1.7.7"
pip show anthropic langchain-anthropic langchain-core | grep -E '^(Name|Version)'
python - <<'EOF'
from typing import Literal

from anthropic.lib._parse._transform import transform_schema
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel


class M(BaseModel):
    f: Literal["a", 1]


print("transform:", transform_schema(M.model_json_schema()))
try:
    transform_schema({"type": "object", "properties": {"g": {}}})
except ValueError as err:
    print("rejects untyped:", err)
llm = ChatAnthropic(model="claude-sonnet-4-5", api_key="sk-witness-no-call")
bound = llm.with_structured_output(M, method="json_schema")
print("bind ok:", type(bound).__name__)
EOF
```
