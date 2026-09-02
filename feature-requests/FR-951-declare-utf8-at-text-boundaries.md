# Feature Request: Declare UTF-8 at every first-party text boundary

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-02
**First consumer / first event:** a Windows contributor or user runs `yamlgraph graph lint` or `yamlgraph graph run` on a graph or prompt YAML containing any non-ASCII character — an em dash, a curly quote, `é`, `€`, CJK, emoji — and the file is read as written instead of crashing or silently corrupting.
**Research:** in-body dispositioned alternatives table (FR-889 style, permitted by `TEMPLATE.md`). Prior-art retrieval was performed by direct grep over `feature-requests/*.md` for `encoding=|cp1252|charmap|UnicodeDecodeError|PYTHONUTF8|locale.getpreferredencoding` and for cross-platform/Windows FR titles; the retrieval evidence and its disposition are recorded under Prior Art below. Running `scripts/research.sh` is recommended before judgement and is now possible on this host — FR-950 restored `yamlgraph` import on Windows.
**Prior art:**
- [FR-950-windows-safe-bridge-fork-registration.md](FR-950-windows-safe-bridge-fork-registration.md) — the direct parent. It removed the *import-time* Windows blocker (`os.register_at_fork`) and thereby made the Windows suite runnable and this defect class visible for the first time. Its Implementation Status explicitly excludes the encoding class under judgement condition C-5 and names this follow-up. Same trap (`the_one_law`: a platform default consumed rather than declared), different boundary: FR-950 was an OS *capability* boundary, this is a text *codec* boundary.
- Grep across all `feature-requests/*.md` for encoding vocabulary returned **no governing FR**. The seven hits are incidental: [FR-243](FR-243-chatterbox-txt-file-batch-tts.md), [FR-393](FR-393-prompt-theme-analyzer.md), [FR-403](FR-403-philosopher-turing-test.md), [FR-629](FR-629-data-files-glob-support.md), [FR-643v2](FR-643v2-novel-fandom-world-expansion.md), and [FR-894](FR-894-corpus-map-reduce-github-scope-reconciliation-reference.md) each show a code sample that *already passes* `encoding="utf-8"`. They are evidence that the correct idiom is known and applied ad hoc per FR, never enforced — which is precisely the gap this FR closes. None allocates a requirement for it.
- [FR-948-lan-copilot-delegation.judgement.md](FR-948-lan-copilot-delegation.judgement.md) R-5 concerns cross-platform *result-path* semantics for remote delegation, not text decoding in the product's own load path. No overlap.
- [FR-754-id-registry-chaplain-path-leak.md](FR-754-id-registry-chaplain-path-leak.md) F4 prefers cross-platform assertions over shell `grep` in tests. It is a test-portability note, not an encoding contract.
- Retrieval is filename-noun IDF ranked and finds vocabulary, not problems. The absence of an encoding FR is therefore a floor, not proof; the Judge should treat the FR-950 lineage as the controlling precedent.

## Summary

Declare `encoding="utf-8"` at every first-party text-file boundary and on the
CLI's own output stream, then enforce it with a blocking lint rule so the
class cannot return.

## Value Statement

YAMLGraph reads and writes text identically on every platform, so a graph or
prompt containing a curly quote behaves the same on Windows as on Linux
instead of crashing or silently reaching the LLM as mojibake.

## Problem

Python's `open()` in text mode uses `locale.getpreferredencoding()` when no
`encoding=` is passed. On this Windows host that is **cp1252**; on the Linux
CI runners it is UTF-8. Every first-party read of a UTF-8 file without an
explicit encoding is therefore correct in CI and wrong in production on
Windows.

`ruff check --select PLW1514 --preview` reports **496 sites**:

| Tree | Sites |
|---|---|
| `tests/` | 314 |
| `examples/` | 80 |
| `scripts/` | 47 |
| `yamlgraph/` (product) | 30 |
| `.chaplain/` | 7 |

The 30 product sites include the core load path:
`yamlgraph/compile/graph_loader.py:134`, `yamlgraph/utils/prompts.py:198` and
`:235`, `yamlgraph/schema_loader.py:253`, `yamlgraph/discovery.py:185`.

### Three distinct failure modes, all reproduced on 2026-09-02

**Mode 1 — crash on read.** Bytes undefined in cp1252 (`0x8d`, `0x8f`, `0x90`,
`0x9d`) raise. `0x9d` is the third byte of `U+201D` (a closing curly quote),
so an ordinary typographic quotation mark in a graph description is enough:

```
$ .venv/Scripts/yamlgraph.exe graph lint tmp/enc-repro/graph.yaml
UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 97
```

**Mode 2 — silent corruption (the dangerous one).** Most UTF-8 sequences
*are* decodable as cp1252, just wrongly. No exception is raised; the mojibake
flows into prompts, LLM calls, and outputs:

```
locale.getpreferredencoding(): cp1252
loaded (no encoding=) -> 'cost â‚¬5 â€” cafÃ©'
correct (utf-8)       -> 'cost €5 — café'
SILENTLY CORRUPTED: True
```

This is `plausible_wrong_answer`: the value passes every type and shape check
and is semantically wrong. Mode 2 has no crash to alert anyone, so its
prevalence is unknown and unbounded.

**Mode 3 — the diagnostic destroys itself.** When Mode 1 fires, the CLI's
error handler prints `❌` (`U+274C`) to a stdout that is also cp1252 when
piped, so the handler raises while reporting:

```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 97
During handling of the above exception, another exception occurred:
UnicodeEncodeError: 'charmap' codec can't encode character '\u274c' in position 0
```

The user loses the actionable message and receives a confusing chained
traceback about an emoji. The output boundary is unnormalized too.

### Why this was invisible

Every GitHub Actions job in `.github/workflows/` is `runs-on: ubuntu-latest`;
there is no Windows job anywhere. The suite could not run on Windows at all
until FR-950, so a 496-site defect class accumulated behind a green CI that
only ever measured the platform where the bug does not exist.

## Ideal Result

Text crosses YAMLGraph's boundaries in a declared encoding, never an inherited
one. Every first-party read and write of a text file states UTF-8 explicitly,
the CLI's own streams state UTF-8 explicitly, and a lint rule running on the
existing Linux CI makes an unencoded boundary a build failure — so the class
is closed by construction rather than by vigilance, and a Windows user's
curly quote is simply a curly quote.

## Proposed Solution

Normalize at the boundary; enforce statically.

**1. Declare the encoding at every first-party text boundary.** Ruff offers a
mechanical fix for all 496 sites (`--unsafe-fixes`; "unsafe" only because
declaring an encoding *changes behavior* — which is the intent):

```python
with open(path) as f:                      # inherits cp1252 on Windows
with open(path, encoding="utf-8") as f:    # declared
```

The fix set must be reviewed rather than trusted: any site that genuinely
reads non-UTF-8 or binary content is a real finding and gets an explicit
encoding plus a one-line comment, not a blind rewrite.

**2. Normalize the CLI's own output stream once, at the entry point**, so
diagnostics survive being piped:

```python
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
```

One callsite in the CLI entry module. Not a per-`print` fix, and not
`PYTHONUTF8` guidance in a README — an environment variable the user must
remember is not a boundary.

**3. Make it enforceable.** Add `PLW1514` to `[tool.ruff.lint] select` in
`pyproject.toml` so the existing Linux CI blocks any new unencoded boundary.
This is the load-bearing deliverable: it converts a platform bug that only
manifests on an unmeasured OS into a static check on the OS already in CI.
Per `detection_without_enforcement`, the rule ships selected and blocking, not
advisory.

**4. Prove it on the real platform.** Add one Windows CI job running a smoke
set only — `import yamlgraph`, `graph lint` on a fixture containing `U+201D`
and `U+20AC`, and the new witnesses. Deliberately *not* the full unit suite:
that remains red for unrelated reasons (below), and gating on it would repeat
FR-950's AC-07 mistake.

New capability `CAP-259` with `REQ-YG-638`, since no existing requirement owns
cross-platform text encoding.

## Acceptance Criteria

- [ ] AC-01 A witness asserts that reading a UTF-8 fixture containing `U+201D` and `U+20AC` through `yamlgraph`'s graph, prompt, and schema loaders returns the exact source characters, and it fails before the fix when run under a forced cp1252 locale.
- [ ] AC-02 A witness asserts that the Mode 2 corruption is absent: the loaded string is byte-identical to the value read with an explicit `encoding="utf-8"`, not merely non-raising.
- [ ] AC-03 `yamlgraph graph lint` on a fixture containing `U+201D` exits zero on Windows with its output piped, and no `UnicodeDecodeError` or `UnicodeEncodeError` appears.
- [ ] AC-04 A witness asserts the CLI emits its non-ASCII status glyphs to a piped stream without raising, exercising the Mode 3 path.
- [ ] AC-05 `ruff check --select PLW1514 .` reports zero findings across `yamlgraph/`, `scripts/`, `tests/`, `examples/`, and `.chaplain/`.
- [ ] AC-06 `PLW1514` is listed in `[tool.ruff.lint] select` in `pyproject.toml` and blocks CI; any per-file-ignore is individually justified in the FR.
- [ ] AC-07 Every site whose fix is not a bare `encoding="utf-8"` addition is enumerated in this FR with its reason.
- [ ] AC-08 `.venv/Scripts/python.exe -m pytest tests/unit/ -q --no-cov -m "not slow" -n auto` on Windows reports zero `UnicodeDecodeError` and zero `UnicodeEncodeError`. Aggregate pass/fail is recorded as context, not gated (see Out of Scope).
- [ ] AC-09 `python scripts/req_coverage.py --strict` exits zero on Windows without `PYTHONUTF8=1`.
- [ ] AC-10 A Windows CI job runs import, the AC-03 lint smoke, and the AC-01/AC-02/AC-04 witnesses, and blocks merge.
- [ ] AC-11 `capabilities/CAP-259-*.yaml` and `ARCHITECTURE.md` allocate `REQ-YG-638`; every new test carries `@pytest.mark.req("REQ-YG-638")`.
- [ ] AC-12 The witnesses are committed RED before the fixes and GREEN afterward, in separate commits.
- [ ] AC-13 A `type: fix` changelog fragment names FR-951 and REQ-YG-638; an `Implementation Status` section records dated commands and results; one `docs/diary/` entry records a trap or insight, a heuristic, and a `Seed:`.

## Out of Scope

Explicitly excluded, to avoid FR-950's AC-07 error of gating on an aggregate
that spans several defect classes:

- **Optional-dependency failures.** 19 `ModuleNotFoundError` (`fastapi`, `litellm`, `bs4`, `feedparser`, `statemachine_engine`) reflect an incomplete local venv, not a code defect.
- **POSIX path and shell assumptions** in test fixtures.
- **Full Windows unit-suite green.** A separate FR once the two classes above are dispositioned.
- **Retrofitting `encoding=` to third-party code.** PyYAML raised in the FR-950 traces, but it was reading a stream *we* opened; the fix is ours.

## Alternatives Considered

| # | Alternative | Benefit | Failure mode | Disposition |
|---|---|---|---|---|
| A1 | Declare `encoding="utf-8"` at each boundary + `PLW1514` gate | Fixes cause where data enters; statically enforced on existing Linux CI; no runtime cost | 496-site diff needs review | **Chosen.** The only option that closes Mode 2 and cannot regress. |
| A2 | Set `PYTHONUTF8=1` in CI and document it for users | One-line change | Fixes only machines that set it; the shipped library still corrupts data for every user who does not. Moves the boundary into the user's environment, where we cannot enforce it | Rejected |
| A3 | Add `# -*- coding: utf-8 -*-` headers | Familiar idiom | Governs *source* decoding, not `open()` of data files. Solves nothing here | Rejected |
| A4 | Wrap reads in a first-party `read_text_utf8()` helper | Single chokepoint; future policy changes land once | Adds an abstraction over a stdlib call whose only defect is a missing argument; the lint rule cannot see through it, so the gate weakens. Violates `constraint_over_code` | Rejected |
| A5 | Catch `UnicodeDecodeError` and retry as UTF-8 | No call-site churn | `downstream_fix` at the symptom. Mode 2 raises nothing, so the fallback never fires on the dangerous path — the plausible-wrong-answer class survives untouched | Rejected |
| A6 | Add `PLW1514` as advisory only, fix opportunistically | Small diff now | `detection_without_enforcement`: lint without a gate is a claim. 496 sites will not shrink voluntarily | Rejected |
| A7 | Do nothing; declare Linux/macOS-only support | Zero effort | `pyproject.toml` declares no platform restriction, the repo ships Windows-specific tests, and FR-950 was just enforced to support Windows. Leaves a silent data-corruption defect for anyone who installs it | Rejected |

**`is_this_a_graph`?** No. There is no per-item model call, multi-stage LLM
pipeline, or fan-out. This is a mechanical source transformation plus a lint
rule; `yamlgraph graph list` offers nothing applicable.

## Related

- `yamlgraph/compile/graph_loader.py:134`, `yamlgraph/utils/prompts.py:198`, `yamlgraph/utils/prompts.py:235`, `yamlgraph/schema_loader.py:253`, `yamlgraph/discovery.py:185`
- `yamlgraph/cli/graph_validate.py:193` — the Mode 3 self-destroying error handler
- `pyproject.toml` — `[tool.ruff.lint] select`
- `.github/workflows/workflow.yml` — currently `ubuntu-latest` only
- Reproductions: `tmp/enc-repro/graph.yaml` (Modes 1 and 3), `tmp/enc_mojibake_probe.py` (Mode 2)
- FR-950 verification log: `tmp/fr950-ac07.log`
