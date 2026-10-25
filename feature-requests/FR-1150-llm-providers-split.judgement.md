# Judgement: FR-1150 Split llm_providers.py under the size gate

**Prior art:** [FR-1150-llm-providers-split.md](FR-1150-llm-providers-split.md) — the FR this judgement rules on, not precedent; dismissed. [FR-1063-map-compiler-package-split.md](FR-1063-map-compiler-package-split.md) — REJECTED move-only split; distinguished in R-1 and in the FR's Prior art. [FR-1057-prompt-template-dialect-split.md](FR-1057-prompt-template-dialect-split.md) — splits a prompt dialect, not a provider module; dismissed, as FR-1063's judgement did. (Added by the FR author at promotion to satisfy the FR-738 gate; not judge output. Backend: `JUDGE_BACKEND=claude scripts/judge.sh`, 2026-10-25, round 1.)

**Verdict:** APPROVED WITH REVISIONS — the problem is real and mechanically verified (473 > 450) and the chosen first module is already judged-owed by FR-1148 R-6/AC-08, but the FR claims "No rejected FR covers this territory" while FR-1063 (a move-only module split) was REJECTED for exactly the research defect this FR repeats, and its second move passes FR-998's locality test by re-export alone — the same shape-not-substance pass it sets out to repair; no authority now, authority activates when R-1..R-9 are folded into the FR.

**Reviewed against:** `feature-requests/FR-1150-llm-providers-split.md`; `feature-requests/FR-1148-anthropic-thinking-off.md`; `feature-requests/FR-1149-size-gate-windows-paths.md`; `feature-requests/FR-1063-map-compiler-package-split.judgement.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.md` (cited lines only); `yamlgraph/utils/llm_providers.py`; `yamlgraph/utils/structured_output.py` (import site); `scripts/size_gate.py`; `.github/hooks/tests/test_size_gate.py`; `tests/unit/test_fr998_structured_output.py`; `tests/unit/test_thinking_budget.py` (imports); `.importlinter`; `.github/workflows/commitlint.yml`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

Round 1 for this FR file — no `FR-1150-llm-providers-split.judgement.md` exists; the FR-1022 round sentinel is not armed.

## What is sound

- **The problem is verified, not asserted.** `yamlgraph/utils/llm_providers.py` ends at line 473; `scripts/size_gate.py:25` sets `LIMIT = 450`; `scripts/size_gate.py:46-48` holds the file with the temporary FR-1149 entry. Every number in the Problem section checks out against the tree.
- **The tautology is real and correctly diagnosed.** `.github/hooks/tests/test_size_gate.py:122` asserts `actual <= allowed`; line 123's `allowed >= actual` is therefore already proven, so the clause can only be satisfied — the FR's reading (FR-1150:48-52) is exact, and the proposed `assert actual > size_gate.LIMIT` is the right repair at the right place.
- **The repair is safe against today's tree.** I checked every `BASELINE` entry's actual length: 807, 675, 549, 615, 592, 589, 510, 501 — all above `LIMIT`, so the repaired assert goes green once the temporary entry is gone, and goes red for nothing the FR does not own. (Note the FR cites the *allowed* numbers, not the actual ones; see R-4.)
- **The first module is not an invention.** `yamlgraph/utils/anthropic_thinking.py` is FR-1148's judged deliverable (FR-1148:155, AC-08, R-6), owed since 2026-10-25 and named in FR-1148's Follow-up-owed paragraph (FR-1148:344-351). FR-1150 is the FR that pays it.
- **The cross-FR ledger is honest.** The FR names what it does *not* do (FR-1148's owed tests, docs, CAP-28, the rename) instead of quietly absorbing it, and it names FR-1149's temporary entry as the thing it must remove — the entry whose only expiry FR-1149's judge flagged as missing.
- **The move is genuinely behaviour-free.** Both blocks are self-contained: neither uses `logger`, `os`, `_bounded` nor any other module-level import of `llm_providers`, and both of their provider imports are already lazy and local (`llm_providers.py:431`, `:462`). No new top-level dependency is created by the split.

## Required revisions

### R-1: Disposition FR-1063 and make the research substantive

FR-1150:26 states "No rejected FR covers this territory." That is wrong. `FR-1063-map-compiler-package-split` is a REJECTED move-only module split, and its judgement (FR-1063 judgement:15-17) rejected it for precisely the shape of research FR-1150 offers: "FR-1063:91-98 rejects four variants of the same refactor without precedent or the graph-fit answer." FR-1150's Alternatives table (FR-1150:116-122) is five variants of the same refactor, with no precedent line, no preserved disagreement, and no `is_this_a_graph` answer (both FR-1148:228 and FR-1149:131 carry one; this FR dropped it). Under the FR-890 clause of judge doctrine and the FR-737 precedent rule, that combination is a no-authority defect.

Fold, in the Prior art paragraph and the Alternatives section:

1. Replace the "No rejected FR covers this territory" sentence with a named disposition of `FR-1063-map-compiler-package-split`: same class (move-only split for size pressure), distinguished by — (a) the target module was already specified and judged under FR-1148 R-6/AC-08, so the chosen solution class is not this FR's invention; (b) 84 moved lines with no typed-return, no `CompiledMap`-equivalent, no consumer-signature change, against FR-1063's five modules plus shared normalisation; (c) the enumerate-importers-first duty of FR-1063 judgement R-2 is discharged here by R-4 below.
2. Add the `**is_this_a_graph:**` line (answer: no — a mechanical code move with no per-item model judgement).
3. Replace the variant table with 4–6 genuine solution classes, each with a precedent line and its disposition, keeping the current variant rows as sub-rows of the chosen class. The classes to disposition, at minimum: (A) extract the two Anthropic blocks into sibling `utils` modules (chosen; precedent FR-263, which extracted `llm_providers.py` from `llm_factory.py` for this same gate); (B) keep one file and widen the gate — a permanent BASELINE entry or a raised `LIMIT` (precedent: FR-889 introduced the ratchet; anti-precedent: `infrastructure_self_exempt`); (C) move the FR-998 block into `yamlgraph/utils/structured_output.py`, its only production consumer (`structured_output.py:29-31`); (D) split `llm_providers.py` by provider, one module per `_create_*_llm` (anti-precedent: FR-1063's rejection of the five-module split); (E) make `yamlgraph/utils/providers/` a package whose `__init__` re-exports (same anti-precedent, plus a wider import surface).
4. Preserve the disagreement rather than flattening it: record the re-export dispute of R-2/R-3 below (façade vs. retargeting the import sites) as the live dissent, with the reason the chosen side won.

### R-2: The FR-998 locality test passes by re-export only — repair it in this FR

`tests/unit/test_fr998_structured_output.py:186-197` (`TestProviderBoundary::test_predicates_live_in_llm_providers`, `REQ-YG-664`) asserts, per its own docstring, "Review #599 P2 / AC-04: provider identity and unsupported-feature classification **live in** the frozen provider boundary module", and checks it with `getattr(providers, ...)`. After the move, the predicates no longer live there; a `from ... import x as x` line satisfies the `getattr` and the test keeps passing while its stated claim has become false. That is `gate_checks_shape_not_substance` — the identical defect class this FR exists to repair one file away, and the FR must not create it while fixing it.

Fold:

1. Amend that test in this FR: keep the two `getattr` clauses (the façade is the contract for callers) and add a definition-site assertion, `assert providers.is_anthropic_chat_model.__module__ == "yamlgraph.utils.anthropic_capability"` and the same for `is_anthropic_unsupported_structured_output`; update the test's docstring to state the split contract — defined in `anthropic_capability`, exposed by `llm_providers`.
2. Correct AC-04: `test_fr998_structured_output.py` does **not** pass unchanged; exactly this one test changes, and the FR must say so.
3. Record in Prior art that FR-998 AC-04's "live in `llm_providers`" wording now reads "exposed by `llm_providers`", so the next reader of FR-998 is not misled.

### R-3: Drop the `_ANTHROPIC_THINKING_ALWAYS_ON` re-export, and drop the alias clause

Two defects in Proposed Solution item 1 (FR-1150:88-96):

1. `_ANTHROPIC_THINKING_ALWAYS_ON` has no importer anywhere in the tree: its only reads are its definition (`llm_providers.py:29`) and its use inside `_anthropic_thinking_off` (`llm_providers.py:40`), both of which move together. `llm_providers.py` imports `_anthropic_thinking_off` because `_create_anthropic_llm` calls it (`llm_providers.py:68`) — a real use. Importing the constant back is an unused import: ruff `F401` fails it, and AC-06 forbids the `noqa` that would silence it. Remove the constant from the re-export and from AC-02; state in the FR that no module imports it from `llm_providers` (the grep is the evidence).
2. Delete "which may add it as an alias" (FR-1150:96). Commandment 8 forbids shims and compat aliases; when FR-1148's owed work takes the `_THINKING_OFF_UNSUPPORTED` name it performs a rename, not an addition. The FR may say the rename is owed; it may not pre-authorise an alias.

### R-4: Pin the move mechanically — line ranges, base SHA, arithmetic

AC-04 ("`git diff` of the moved bodies shows only the move") is not mechanically checkable as written: a partial-file extraction produces no rename detection, so there is nothing for `git diff` to assert against. Fold:

1. Name the exact source ranges and the commit they are taken from: the thinking block is `yamlgraph/utils/llm_providers.py:28-47` (20 lines) and the FR-998 block is `:410-473` (64 lines), at the commit recorded in the FR (`431c0ef8` at the time of judgement).
2. Restate AC-04 as a byte-identity check the enforcer can run and paste: the moved regions of the new modules are byte-identical to those ranges, modulo nothing — no reflow, no docstring rewording, no message change.
3. Correct the arithmetic in FR-1150:110. Removing `:28-47` plus one blank leaves 452, and the import line brings it back to ~453 — not "about 456". The conclusion (the second move is required) is unchanged; the number must be right because it is the FR's whole justification for the second move.
4. Discharge FR-1063 judgement R-2's enumerate-importers duty explicitly: list the import sites of every moved name — `yamlgraph/utils/structured_output.py:29-31` and `tests/unit/test_fr998_structured_output.py:36-38` for the two predicates; none for `_structured_error_message`, the three term tuples, or `_ANTHROPIC_THINKING_ALWAYS_ON`; `llm_providers.py:68` for `_anthropic_thinking_off`.

### R-5: Name the tests that carry AC-02 and AC-03, with their REQ markers

AC-02 and AC-03 state assertions but no file, so no test can be derived without a guess, and ADR-001 requires every test function to carry `@pytest.mark.req`. Fold: AC-02's identity assertions for `is_anthropic_chat_model` / `is_anthropic_unsupported_structured_output` go in `tests/unit/test_fr998_structured_output.py` under the existing `REQ-YG-664` class marker (alongside R-2's amendment); AC-02's `_anthropic_thinking_off` import-identity and AC-03's `ValueError` message assertion go in `tests/unit/test_thinking_budget.py` with `@pytest.mark.req("REQ-YG-083")`; the honesty repair stays in `.github/hooks/tests/test_size_gate.py` under the module-level `pytestmark = pytest.mark.req("REQ-YG-631")` (infrastructure scope, FR-436).

### R-6: Fix the commit order and paste the RED witness verbatim

AC-05 describes a RED witness but not when it exists, and the witness is only constructible in one order. Fold the order into the FR as three commits, one concern each:

1. `refactor`: both module moves and the `llm_providers.py` docstring. The size gate passes at this commit — the file is ~390 lines against the entry's `allowed = 473` — and the old tautological test still passes.
2. RED: the repaired assert alone, with the 473 entry still present. The test fails naming `llm_providers.py`; the failure output is pasted **verbatim** into the FR's Implementation status (FR-1149 R-2 precedent); committed with `SKIP=pytest` and its reason recorded in the PR body.
3. GREEN: remove the `"yamlgraph/utils/llm_providers.py": 473` entry and its two comment lines (`scripts/size_gate.py:46-48`). The suite goes green.

### R-7: State the PR title and the changelog consequence

The FR never names its PR title, and the changelog gate is title-keyed: `.github/workflows/commitlint.yml:165-188` requires a fragment only when the PR title starts with `feat` or `fix`. Fold: name the title — `refactor(utils): FR-1150 split llm_providers.py under the size gate` (`refactor` is an accepted commitlint type, `.github/workflows/commitlint.yml:36-44`) — and state explicitly that no `changelog/unreleased/` fragment is required because the change is behaviour-free and the title is `refactor`. If the enforcer instead titles the PR `fix`, a fragment is required and must be added as an AC; the FR must not leave this unstated.

### R-8: Docstrings and the lazy-import discipline in the new modules

1. `llm_providers.py`'s module docstring (`:1-9`) currently tells the reader that capability classification "live[s] at the bottom of this module". Make its update an AC, not prose: the docstring names `anthropic_thinking.py` and `anthropic_capability.py` as the new homes and keeps the FR-263 extraction sentence.
2. Each new module carries a docstring naming its owning FR (`anthropic_thinking.py` → FR-1148, moved by FR-1150; `anthropic_capability.py` → FR-998, moved by FR-1150).
3. Make the lazy-import rule an AC: neither new module gains a module-level `langchain_anthropic` or `anthropic` import — both provider imports stay inside their functions, as they are today at `llm_providers.py:431` and `:462`. This is the one place a "tidying" move would silently break the discipline the docstring promises.

### R-9: Verification commands, and the FR-1148 hand-off

1. The FR's command list omits three checks that this change can break: `lint-imports` (two new modules; FR-1148 AC-08 required it), `python scripts/req_coverage.py --strict` (new test functions), and the fast unit suite `pytest tests/unit/ -q --no-cov -m "not slow" -n auto`. Add all three to Planned Operations and to the acceptance criteria.
2. Traceability, mirroring FR-1149 AC-09: add a sentence to FR-1148's Follow-up-owed paragraph (FR-1148:344-351) naming FR-1150 as the FR that performs the module move and removes FR-1149's temporary entry, and state in FR-1150 which clauses of FR-1148 AC-08 close here (module exists and holds the rule; `llm_providers.py` ≤ 450; `lint-imports`; `pre-commit`) and which stay owed (the `_THINKING_OFF_UNSUPPORTED` rename and every test/doc clause of AC-01..AC-07, AC-10, AC-11).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/anthropic_thinking.py` — new; `llm_providers.py:28-47` moved byte-identically |
| D-2 | `yamlgraph/utils/anthropic_capability.py` — new; `llm_providers.py:410-473` moved byte-identically |
| D-3 | `yamlgraph/utils/llm_providers.py` — the two blocks removed, `_anthropic_thinking_off` imported for use, the two FR-998 predicates re-exported (`import x as x`), module docstring updated |
| D-4 | `scripts/size_gate.py` — the `"yamlgraph/utils/llm_providers.py": 473` entry and its comment removed (`:46-48`) |
| D-5 | `.github/hooks/tests/test_size_gate.py` — line 123's tautology replaced by `assert actual > size_gate.LIMIT, …` |
| D-6 | `tests/unit/test_fr998_structured_output.py` — `test_predicates_live_in_llm_providers` amended per R-2; identity assertions per R-5 |
| D-7 | `tests/unit/test_thinking_budget.py` — import-identity and message assertions per R-5 |
| D-8 | `feature-requests/FR-1150-llm-providers-split.md` — R-1..R-9 folded, judgement fold table, Implementation status with the verbatim RED witness |
| D-9 | `feature-requests/FR-1148-anthropic-thinking-off.md` — one hand-off sentence (R-9.2) |
| D-10 | `docs/diary/` — one reflection with a **Seed:** |

**Not authorized:** renaming `_ANTHROPIC_THINKING_ALWAYS_ON` to `_THINKING_OFF_UNSUPPORTED`, or adding an alias for it; any edit to the message text, prefix tuples, term tuples, or any function body being moved; any edit to `_create_*_llm` bodies, `dispatch_provider`, `_PROVIDER_FACTORIES`, `_THINKING_PROVIDERS`, `llm_bounds.py`, `llm_factory.py`, or `structured_output.py` logic; retargeting `structured_output.py`'s import to the new module; FR-1148's owed payload-level tests, 14-id table test, CAP-28/`ARCHITECTURE.md` regeneration, `reference/graph-yaml.md` sites, and the `effort` setting; any change to `LIMIT`, `WARN`, `BYTE_CEILING`, `SCAN_DIRS`, or any other `BASELINE` entry; splitting `llm_providers.py` by provider or into a package; any `# noqa`; any new `changelog/unreleased/` fragment unless R-7's `fix` branch is taken.

## Revised acceptance criteria

- [ ] AC-01: `wc -l yamlgraph/utils/llm_providers.py` ≤ 450 and `scripts/size_gate.py` `BASELINE` contains no `yamlgraph/utils/llm_providers.py` key; `PYTHONUTF8=1 python scripts/size_gate.py` exits 0 with no `✗` line (output pasted into the FR).
- [ ] AC-02: `yamlgraph/utils/anthropic_thinking.py` and `yamlgraph/utils/anthropic_capability.py` exist; the regions moved into them are byte-identical to `llm_providers.py:28-47` and `:410-473` at the recorded base SHA; neither module has a module-level `langchain_anthropic` or `anthropic` import (R-4, R-8).
- [ ] AC-03: `_anthropic_thinking_off`, `is_anthropic_chat_model` and `is_anthropic_unsupported_structured_output` import from `yamlgraph.utils.llm_providers` and are the same objects as in their defining modules (`is` identity). `_ANTHROPIC_THINKING_ALWAYS_ON` is **not** re-exported, and no production or test module imports it from `llm_providers` (R-3).
- [ ] AC-04: `_anthropic_thinking_off("claude-opus-5-5")` raises `ValueError` whose message is exactly `thinking_budget=0: thinking cannot be turned off on claude-opus-5-5; omit thinking_budget for this model`; `_anthropic_thinking_off("claude-sonnet-5-5") == {"type": "between_tools"}` and `_anthropic_thinking_off("claude-haiku-5-5") == {"type": "disabled"}`.
- [ ] AC-05: `tests/unit/test_fr998_structured_output.py::TestProviderBoundary::test_predicates_live_in_llm_providers` asserts both the `llm_providers` exposure and `__module__ == "yamlgraph.utils.anthropic_capability"` for both predicates, with its docstring updated to the split contract (R-2).
- [ ] AC-06: every new test function carries `@pytest.mark.req` (`REQ-YG-664` / `REQ-YG-083` / module-level `REQ-YG-631`); `python scripts/req_coverage.py --strict` exits 0.
- [ ] AC-07: `.github/hooks/tests/test_size_gate.py` line 123 reads `assert actual > size_gate.LIMIT, f"stale baseline entry: {rel} is {actual} lines, not over LIMIT"`, and `LIMIT`, `WARN`, `BYTE_CEILING` and every other `BASELINE` entry are unchanged.
- [ ] AC-08: RED witness — at the second commit (repaired assert, 473 entry still present) `pytest .github/hooks/tests/test_size_gate.py -q --no-cov` fails naming `llm_providers.py`; the failure output is pasted verbatim into the FR's Implementation status, and the three-commit order of R-6 is visible in `git log`.
- [ ] AC-09: `pytest -q --no-cov tests/unit/test_thinking_budget.py tests/unit/test_fr998_structured_output.py .github/hooks/tests/test_size_gate.py` passes at the final commit; `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` passes or every failure is shown to be untouched by this change against a baseline run of the same command on `main`.
- [ ] AC-10: `lint-imports` exits 0; `PYTHONUTF8=1 pre-commit run --files <changed files>` passes.
- [ ] AC-11: `llm_providers.py`'s module docstring names both new modules and no longer says the FR-998 block is at the bottom of the file; each new module's docstring names its owning FR and FR-1150 (R-8).
- [ ] AC-12: the FR records the R-1 fold — FR-1063 dispositioned by name, the `is_this_a_graph` line, 4–6 solution classes with precedent lines, and the preserved re-export dissent.
- [ ] AC-13: the FR names its PR title and states the changelog consequence; if the title starts with `fix`, `changelog/unreleased/fr-1150-llm-providers-split.md` exists and validates (R-7).
- [ ] AC-14: FR-1148's Follow-up-owed paragraph names FR-1150, and FR-1150 states which FR-1148 AC-08 clauses close here and which stay owed (R-9.2).
- [ ] AC-15: no new `# noqa`; no `--no-verify`; no `Co-authored-by` trailer; every `SKIP=` is recorded with its commit and reason in the PR body.
- [ ] AC-16: a `docs/diary/` reflection with a **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is void until R-1..R-9 are folded into the FR with a judgement-fold table; R-1 is the FR-890/FR-737 gate and is not discretionary. | GATE |
| C-2 | Behaviour-free: no edit to any moved body, message, tuple, or to `_create_*_llm`, `dispatch_provider`, `_PROVIDER_FACTORIES`, `_THINKING_PROVIDERS`, `llm_bounds.py`, `llm_factory.py`, `structured_output.py`. A diff that changes a character inside a moved region fails the AC. | GATE |
| C-3 | `scripts/size_gate.py` and `.github/hooks/tests/test_size_gate.py` are enforcement infrastructure and are adversarial input: the human reviewer must confirm the entry removal and the repaired assert before merge. The enforcer may not weaken `LIMIT`, `WARN`, `BYTE_CEILING`, add any `BASELINE` entry, or exempt any path. | GATE |
| C-4 | No rename and no alias of `_ANTHROPIC_THINKING_ALWAYS_ON` under this FR; it stays FR-1148's owed rename. | GATE |
| C-5 | If a moved name turns out to be imported from `llm_providers` by a site not enumerated under R-4, keep it importable there and record the site in the FR — never drop an import path silently. | GATE |
| C-6 | The RED commit precedes the GREEN commit in `git log`, one concern per commit; no `--no-verify`, no `Co-authored-by` trailer; each `SKIP=` named with its reason in the PR body. | GATE |
| C-7 | Supervision is separate from execution: the enforcer stops at "ready for review" and does not self-certify AC-08's RED witness or merge. | GATE |

## Questions for the human (not absorbed)

1. **The façade, decided provisionally against the letter of Commandment 8.** This judgement keeps `llm_providers` as the import path for the two FR-998 predicates (a `from … import x as x` re-export), because FR-998 review #599 P2 froze that module as *the* provider boundary and the alternative touches the hot path `structured_output.py:29-31`. The cost is two import paths to one object — the "no shims, no adapters" tension. R-2 removes the dishonest half (the test's claim) but not the façade. If the operator prefers no façade, the fold is small and mechanical: retarget `structured_output.py:29-31` and `tests/unit/test_fr998_structured_output.py:36-38` at `anthropic_capability`, drop the re-export, and drop AC-03's exposure clause.
2. **FR-1149's parked question returns, sharpened.** The temporary `473` entry's only expiry is this PR. Until R-6's third commit lands, the entry outlives its reason with nothing mechanical to notice — and R-1's fold delays that landing. If the operator wants the expiry guaranteed independently of this FR's research fold, say so and the entry removal can be split into its own one-line PR ahead of the moves.

Authority granted: none at this round. On the fold of R-1..R-9 into `feature-requests/FR-1150-llm-providers-split.md`, the enforcer may move `llm_providers.py:28-47` into `yamlgraph/utils/anthropic_thinking.py` and `:410-473` into `yamlgraph/utils/anthropic_capability.py` byte-identically, re-export the two FR-998 predicates, update the three docstrings, repair `test_size_gate.py`'s tautological assert, remove the temporary `BASELINE` entry, amend the two named test files, and write the FR, FR-1148 hand-off sentence and diary entry — and nothing else.
