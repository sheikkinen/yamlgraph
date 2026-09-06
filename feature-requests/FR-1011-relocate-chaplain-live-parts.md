# Feature Request: Relocate the live parts out of `.chaplain/` (Phase 1 of FR-1010)

**Priority:** MEDIUM
**Type:** Enhancement (refactor — pure relocation, no behaviour change)
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-09-06
**Plan:** [FR-1010-chaplain-archival-plan.md](FR-1010-chaplain-archival-plan.md) — Phase 1 of 3
**First consumer / first event:** the pre-commit `triage-gate` hook, on
the first `feature-requests/*.md` commit after this PR merges — it
imports `fr_triage/tools.py` by filesystem path and is the one consumer
that fails loudly if the relocation is wrong. Second: the operator's next
spark, written to `proposals/`.
**Research:** [FR-1010 § Alternatives Considered](FR-1010-chaplain-archival-plan.md#alternatives-considered)
— the in-body dispositioned table that selected this phase's shape; the
live-parts inventory and inbox pre-check in the same FR are this FR's
evidence record.
**Prior art:**
- [FR-196-portable-chaplain.md](FR-196-portable-chaplain.md) — moved
  philosopher **into** `.chaplain/graphs/` from `examples/philosopher/`
  and introduced the `parents[2]/lib/diary.py` proxy. This FR reverses
  the direction and keeps the stub deletion honest: the stub README says
  "current active chaplain graphs live under `.chaplain/graphs/`" —
  after this FR that sentence is false, so the stub goes.
- [FR-745-fr-triage-graph.md](FR-745-fr-triage-graph.md) — `triage_gate.py`
  loads `.chaplain/graphs/fr_triage/tools.py` by absolute path
  (`checks/triage_gate.py:29`). Path updated here; contract unchanged.
- [FR-744-world-now-distill.md](FR-744-world-now-distill.md) — `now.py:487`
  prints the `world_distill` refresh command. Path updated here.
- [FR-767-graph-authoring-sole-route.md](FR-767-graph-authoring-sole-route.md)
  — the governed-path regex has a `.chaplain/graphs` arm
  (`pre-command-guard.sh:170`, `check_authoring_proof.py:25`). The arm is
  deleted here. See "Guard gap" below: the arm never matched dir-style
  graphs, so nothing is lost by deleting it — and nothing was ever
  protected by it.
- [FR-889-os-enforced-main-write-lock.md](FR-889-os-enforced-main-write-lock.md)
  — `.chaplain/` is not in `FR889_GOVERNED_ROOTS` (`worktree.sh:506`) and
  neither is a top-level `proposals/`; the inbox keeps its current write
  semantics on main.

## Summary

Move the three graphs (`fr_triage`, `world_distill`, `philosopher` with
its `diary.py` dependency) from `.chaplain/graphs/` to `graphs/`, move the
8 live sparks from `.chaplain/inbox/` to `proposals/`, update every
consumer path, and delete the `examples/philosopher/` stub. After this
FR, nothing outside `.chaplain/` refers to anything inside it except the
`chaplain-ops` skill and the retirement-era tests that Phase 2 removes.

## Value Statement

Phase 2 can delete `.chaplain/` without touching a live gate, a live
orientation script, or the operator's inbox.

## Problem

Three live artifacts and one dormant one are physically inside a
directory scheduled for removal (FR-1010 § "What is still live"). The
couplings, by file:line:

| Consumer | Line | Reference |
|---|---|---|
| `.github/hooks/scripts/checks/triage_gate.py` | 29 | `.chaplain/graphs/fr_triage/tools.py` loaded via `spec_from_file_location` |
| `.github/hooks/scripts/checks/fr-checks.sh` | 77 | reminder text: `yamlgraph graph run .chaplain/graphs/fr_triage/graph.yaml` |
| `scripts/vscode/now.py` | 487 | STALE hint: `yamlgraph graph run .chaplain/graphs/world_distill/graph.yaml` |
| `.github/hooks/scripts/pre-command-guard.sh` | 170, 187 | governed-path regex arm `(^|/)\.chaplain/graphs/[^/]+\.ya?ml$` and pre-filter `examples/|graphs/|\.chaplain/` |
| `scripts/check_authoring_proof.py` | 25 | same regex arm |
| `.github/skills/feature-request/SKILL.md` | 88–91, 148 | "Write to `.chaplain/inbox/`" |
| `.github/skills/graph-authoring/doctrine.md` | 44, 116 | precedent-search location; "Submit a Chaplain proposal (`.chaplain/inbox/`)" |
| `.github/skills/session-introspection/SKILL.md` | 40 | world file row names the chaplain runtime |
| `.github/copilot-instructions.md` | 163 | `diary_graduation_pipeline` seed: "auto-proposal to `.chaplain/inbox/`" (path mention only) |
| `.chaplain/graphs/philosopher/tools.py` | 371 | `Path(__file__).resolve().parents[2] / "lib" / "diary.py"` — breaks on any move |
| `tests/unit/test_fr_triage.py` | 27 | `TOOLS = REPO / ".chaplain/graphs/fr_triage/tools.py"` |
| `tests/unit/test_world_distill.py` | 27 | `TOOLS = REPO / ".chaplain/graphs/world_distill/tools.py"` |
| `tests/unit/test_philosopher.py` | 21, 401–1344 | ~30 literal `.chaplain/graphs/philosopher/...` paths |
| `tests/unit/test_chaplain_graph_compile.py` | 22, 55 | globs `.chaplain/graphs/**/*.yaml`; asserts `parents[2]/lib/diary.py` |
| `.gitignore` | 100 | `.chaplain/inbox/` |

Two facts surfaced while tracing that the plan must record:

1. **The inbox is untracked.** `.gitignore:100` ignores it; `git ls-files
   .chaplain/inbox` is empty; the directory does not exist in any
   worktree. Sparks are visible only on the main checkout of one
   machine. This FR preserves that semantics (pure relocation) and files
   the durability/visibility question as a spark of its own
   (`proposals/inbox-is-untracked-and-worktree-invisible.md`).
2. **`philosopher` is dormant, not live.** No consumer outside its own
   tests. Kept and relocated because it is the only implementation of
   the `diary_graduation_pipeline` seed; retiring it is a Phase 2
   decision, recorded in FR-1010.

### Guard gap (verified 2026-09-06, `pre-command-guard.sh:167-171`)

The governed-path predicate is:

```python
re.search(r"(^|/)examples/.+/graph\.ya?ml$", p)
or re.search(r"(^|/)examples/.+/prompts/[^/]+\.ya?ml$", p)
or re.search(r"(^|/)graphs/[^/]+\.ya?ml$", p)
or re.search(r"(^|/)\.chaplain/graphs/[^/]+\.ya?ml$", p)
```

The `graphs/` and `.chaplain/graphs/` arms match only **flat** files one
level down. `.chaplain/graphs/fr_triage/graph.yaml`,
`.chaplain/graphs/*/prompts/*.yaml`, and the existing
`graphs/enforcement/changelog-req-check.yaml` + `graphs/enforcement/prompts/*`
have never been governed. The `.chaplain` arm was vacuous for every graph
that directory actually contains. Relocation to `graphs/<name>/` therefore
changes nothing about their governance — they remain ungoverned unless the
`graphs/` arm becomes dir-aware.

**Decision for the Judge** (options, evidence, default):

| Option | Consequence |
|---|---|
| (a) Make the `graphs/` arm dir-aware in this FR: `graphs/.+/graph\.ya?ml$` and `graphs/.+/prompts/[^/]+\.ya?ml$`, keep the flat arm, delete the `.chaplain` arm; mirror in `check_authoring_proof.py` | Relocated graphs and `graphs/enforcement/` become governed at the moment they enter `graphs/`; this FR already runs through `scripts/author.sh`, so its own writes are sentineled. A witness test asserts the six paths (3 graphs × graph.yaml + one prompt each, plus `graphs/enforcement/`) are governed. |
| (b) Delete the `.chaplain` arm only; file the dir-aware widening as FR-1014 | Pure relocation; the gap stays open for one more PR cycle and `graphs/enforcement/` stays ungoverned meanwhile. |

Recommended default: **(a)**. The change strengthens the guard rather
than loosening it (`guard_widening_when_caught` targets same-session
exclusions added to escape a gate; this is the inverse), it is a
two-line regex change with a witness, and this FR is the event at which
the six paths enter `graphs/`.

## Ideal Result

`ls .chaplain/graphs` shows only `watcher-*`; `ls graphs` shows
`enforcement fr_triage philosopher world_distill`; `ls proposals` shows
nine files (8 carried + 1 new); every consumer above points at the new
path; `pytest tests/unit/test_fr_triage.py tests/unit/test_world_distill.py
tests/unit/test_philosopher.py tests/unit/test_chaplain_graph_compile.py`
is green; `yamlgraph graph lint` and a smoke run pass for each moved
graph from its new location; `git diff --stat` shows renames, not
rewrites, for the graph files.

## Proposed Solution

One PR, two commits (RED, GREEN), routed through `scripts/author.sh`
because `mv` of `graph.yaml`/`prompts/*.yaml` is graph authoring
(`graph-authoring/doctrine.md`; FR-767 sentinel).

### RED

- `tests/unit/test_fr_triage.py:27`, `test_world_distill.py:27`,
  `test_philosopher.py:21` and its literal paths,
  `test_chaplain_graph_compile.py:22,55` → new paths. Collection fails
  until GREEN.
- New `tests/unit/test_fr1011_relocation.py`:
  - `test_no_live_consumer_names_chaplain_graphs`: grep of the consumer
    files in the table above for `.chaplain/graphs` returns nothing
    (excludes `chaplain-ops/`, `.chaplain/**`, and the Phase 2 test set).
  - `test_philosopher_diary_proxy_is_sibling`: `graphs/philosopher/tools.py`
    resolves `diary.py` as `Path(__file__).with_name("diary.py")` and it
    exists.
  - `test_governed_regex_has_no_chaplain_arm`: `pre-command-guard.sh`
    and `check_authoring_proof.py` contain no `\.chaplain` literal.
  - `test_dir_style_graphs_are_governed` (option (a) only): the
    predicate returns True for `graphs/fr_triage/graph.yaml`,
    `graphs/fr_triage/prompts/<first>.yaml`, likewise for
    `world_distill`, `philosopher`, and
    `graphs/enforcement/changelog-req-check.yaml`; False for
    `graphs/README.md`.
  - Tagged `@pytest.mark.req("REQ-YG-563", "REQ-YG-564", "REQ-YG-529")`
    (CAP-206 fr_triage, CAP-205 world_distill, CAP-75 philosopher proxy)
    — existing REQs; no new CAP. The governed-path witness carries the
    FR-767 REQ from `capabilities/CAP-*-graph-authoring-sole-route.yaml`.

### GREEN

```bash
git mv .chaplain/graphs/fr_triage      graphs/fr_triage
git mv .chaplain/graphs/world_distill  graphs/world_distill
git mv .chaplain/graphs/philosopher    graphs/philosopher
git mv .chaplain/lib/diary.py          graphs/philosopher/diary.py
git rm -r examples/philosopher
mkdir proposals && mv .chaplain/inbox/{8 carried}.md proposals/
```

- `graphs/philosopher/tools.py:371` → `Path(__file__).with_name("diary.py")`.
- `graphs/philosopher/graph.yaml:5,12,21` comments: drop the `.chaplain`
  paths.
- `checks/triage_gate.py:29` → `"graphs" / "fr_triage" / "tools.py"`
  (`parents[4]` stays; only the segment list changes).
- `checks/fr-checks.sh:77`, `scripts/vscode/now.py:487` → new paths.
- `pre-command-guard.sh:170` delete the `.chaplain/graphs` alternative;
  `:187` pre-filter → `examples/|graphs/`. `check_authoring_proof.py:25`
  delete the pattern entry. Under option (a), the `graphs/` arm gains
  the two dir-aware alternatives in both files; under (b) no pattern is
  added.
- `capabilities/CAP-205-world-distill.yaml:4,12,25`,
  `CAP-206-fr-triage-graph.yaml:4,14,26`, `CAP-75-portable-chaplain.yaml:8,12,13,29`
  — `source:`/description paths → new locations (`validate_capabilities`
  reads them; text-only, no REQ change).
- Skills: `feature-request/SKILL.md` §"Submitting" rewritten as
  "Write to `proposals/`" (remove the "Remote Submission / `chaplain`
  label" paragraph — the importer is the dead runtime);
  `graph-authoring/doctrine.md:44` → `graphs/`; `:116` → `proposals/`;
  `session-introspection/SKILL.md:40` drop the runtime clause.
- `.github/copilot-instructions.md:163`: `.chaplain/inbox/` → `proposals/`
  in the seed string. Path-only; doctrine text unchanged. (Scripture
  wording changes are Phase 3.)
- `.gitignore:100` → `proposals/`. Same semantics as today.
- New spark `proposals/inbox-is-untracked-and-worktree-invisible.md`
  (fact 1 above, three sentences, no solution).
- Inbox items **not** carried: `deviantart-auto-publish-pipeline.md`,
  `refactor-pre-command-guard-dispatcher.md`,
  `research-prompts-contradict-precedent-validator.md` deleted from disk
  (they are untracked; FR-1010's table is their tombstone);
  `deviant-daily-curated-rerun.md` copied to
  `~/Documents/src/deviant-daily/` by the operator (outside this repo's
  blast radius — this FR only deletes the local copy after the operator
  confirms); `ninchat_voice/` removed.
- Old path behaviour: `.chaplain/inbox/` ceases to exist on main. A
  write there fails with `ENOENT` from the shell — visible, not silent.
  No guard grammar is added (FR-889 C-5: the kernel is the barrier; the
  guard covers only what the kernel cannot).

### Witness

- `yamlgraph graph lint graphs/{fr_triage,world_distill,philosopher}/graph.yaml`
- Smoke: `yamlgraph graph run graphs/fr_triage/graph.yaml --var fr_path=feature-requests/FR-1010-chaplain-archival-plan.md`
  (its real first consumer); `python scripts/vscode/now.py` prints the
  new refresh hint; `pytest tests/unit/test_fr1011_relocation.py -q`.
- `tmp/draft-authoring-report.md` from `scripts/author.sh` committed
  under `docs/spikes/` or cited in the PR body (FR-767 proof).

## Acceptance Criteria

- [ ] `git diff --stat main..HEAD -- graphs/` shows renames (similarity
      ≥ 90%) for every `graph.yaml`, `prompts/*.yaml`, `tools.py`,
      `diary.py` moved.
- [ ] `grep -rn '\.chaplain' .github/hooks/scripts scripts/vscode scripts/check_authoring_proof.py .github/skills/{feature-request,graph-authoring,session-introspection}`
      returns nothing.
- [ ] `pre-command-guard.sh` and `check_authoring_proof.py` contain no
      `.chaplain` literal. Under (a): `test_dir_style_graphs_are_governed`
      green; under (b): FR-1014 filed before this PR merges.
- [ ] `checks/triage_gate.py` imports from `graphs/fr_triage/tools.py`;
      a `feature-requests/*.md` commit in the worktree runs the gate
      without `FileNotFoundError`.
- [ ] `graphs/philosopher/tools.py` resolves `diary.py` as a sibling; the
      `write_diary` proxy test passes from the new path.
- [ ] `examples/philosopher/` does not exist.
- [ ] `proposals/` holds the 8 carried sparks + 1 new; `.chaplain/inbox/`
      does not exist on the main checkout after `git pull`.
- [ ] `.gitignore` ignores `proposals/`, not `.chaplain/inbox/`.
- [ ] Lint + smoke for the three graphs recorded in the authoring
      report; `tests/unit/test_fr1011_relocation.py` green; full unit
      suite green (`pytest tests/unit -q -m "not slow" -n auto`).
- [ ] `req_coverage --strict`, `validate_capabilities --strict` green
      (no CAP change).
- [ ] Changelog fragment `changelog/unreleased/fr-1011-relocate-chaplain-live-parts.md`.
- [ ] FR-1010 live-parts table unchanged (no fourth live artifact
      found) — or amended before merge if one is.

## Purge list (nothing invented)

- No new guard grammar beyond the dir-aware `graphs/` arm (option (a)).
- No symlink from `.chaplain/inbox/` to `proposals/`.
- No `proposals/README.md` — the feature-request skill is the doc.
- No CAP file; existing REQs cover the relocated graphs.

## Alternatives Considered

| Option | Why not |
|---|---|
| `feature-requests/inbox/` for sparks | `.pre-commit-config.yaml:280,286` (`^feature-requests/.*\.md$`) would run `prior-art-gate` and `triage-gate` on sparks that by design have no disposition sections. |
| `examples/` for the three graphs | They are process graphs, not demos; `graphs/enforcement/` is the dir-style precedent for process graphs. |
| Leave the `graphs/` regex flat | Verified gap (§ Guard gap): dir-style graphs under `graphs/` have never been governed. Leaving it means the relocated graphs enter an ungoverned path — option (b) above; defensible only with FR-1014 filed. |
| Retire philosopher now | Phase 2 scope; relocating keeps Phase 1 a pure move. |
| Track `proposals/` in git | Changes spark-filing friction (PR per spark) — a design decision, filed as a spark, not smuggled into a relocation. |

## Related

- FR-1010 (plan), FR-1012 (Phase 2), FR-1013 (Phase 3)

## Judgement (pending)
