# 2026-08-23 — FR-860: The Audit That Audited Its Own Corpus First

## What happened

FR-860's runner worked on the first honest attempt. Getting to an
honest attempt took six runs. The failures, in order: two terminals
without the venv (exit 127), one nonexistent pytest-cov flag frozen
into the judgement itself, one mass-error wall that killed 80% of the
suite, and one live-LLM assertion demanding exact case. Only then: 414
REQs audited, zero rejected batches.

## The trap: the instrument was the victim of its own subjects

The mass-error wall was the interesting one. Solid `E` lines from ~20%
onward, log truncated by terminal death, no traceback. The reflex was
to suspect the new instrument (ctrace? context recording? Python
3.14?). The `-x` probe said otherwise: `sqlite3.OperationalError: no
such table: context` — the outer run's coverage DB was a 0-byte file.
Nine slow-marked tests spawn nested `python -m pytest` at repo root;
addopts hands them `--cov`; the nested pytest-cov session
combine-deletes every `.coverage.*` in the root, eating the outer
run's live data file. Coverage reopens it lazily (`con=None` in the
traceback was the tell), finds no schema, and every subsequent test
errors.

Three Scripture entries fired in one defect:

- **`composition_bug`** — every component correct in isolation
  (pytest-cov's combine-delete is by design; addopts are by design;
  nested spawns are legitimate tests). The defect is the policy
  connecting them: nothing said "a nested pytest must not inherit the
  outer session's coverage config."
- **The fast suite as a blind instrument** — the culprits are all
  `slow`-marked, so `-m "not slow"` had never executed them under
  coverage. FR-860 exists precisely to run what the fast suite skips;
  its first full run detonated every landmine the fast suite had been
  stepping around. The audit audited the corpus before it audited the
  requirements.
- **`tolerant_matching`** — the last blocker was
  `assert "World" in greeting` against a live model that said "the
  world". A 6322-pass run killed at 99% by case sensitivity, in a
  test whose own comment claimed to be about compatibility.

## The result nobody wanted but everyone needed

AC-09's honest outcome: `no-link-unrecorded` fell 1,279 → 1,262. The
FR-850 hypothesis — record the full suite and the unlinked class
collapses — is refuted. Those tests execute no `yamlgraph/` source at
all; they witness bash, workflow YAML, markdown doctrine, and
`examples/` code via subprocess. No amount of recording links them,
because the instrument (`--cov=yamlgraph`) cannot see their subjects.
The judgement's C-4 (aggregate distribution is evidence, not a gate)
is what allowed this refutation to be recorded instead of laundered:
a threshold gate on the fall would have forced either scope creep or
a dishonest number. `threshold_encodes_forecast`, witnessed again.

## Heuristic

**A full-suite instrument's first run is a corpus audit, not a
measurement.** Budget for it: the first honest run of any
whole-corpus tool will fail on corpus defects invisible to the
partial-corpus workflow, and those failures are the tool's first
deliverable. (Second witness: FR-850's first recording attempt died
on the sysmon core; this run died on nested-spawn clobbering and
exact-case LLM asserts. Same shape — the instrument's maiden voyage
maps the reefs.)

Also mechanical, now enforced: `test_nested_pytest_cov_guard.py`
AST-scans the corpus so a tenth nested spawn without `--no-cov`
cannot land.

**Seed:** the 1,262 permanently-unlinkable tests witness subjects the
coverage instrument cannot see (bash, YAML, markdown, subprocess'd
examples). Is `no-link-unrecorded` the wrong name — should the
construct stage classify *subject kind* (python-in-package vs
out-of-instrument) at the boundary, so the audit stops re-flagging
the same structural fact as 242 partial verdicts every run?
