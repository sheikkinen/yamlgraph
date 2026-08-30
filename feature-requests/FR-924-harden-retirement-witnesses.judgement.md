# Judgement: FR-924 Harden retirement witnesses — assert tracked absence, not filesystem absence

**Prior art:** the top gate hit is this judgement's own subject FR (`FR-924-harden-retirement-witnesses.md`), not independent precedent. The three retirement FRs it hits — FR-909, FR-910, FR-915 — are the witnesses being hardened, dispositioned throughout this judgement (notably R-2, which preserves FR-910 AC-01's filesystem contract); FR-858 supplies the `git ls-files` witness form and the CONF-432/433/434 confession precedent. None is a competing proposal: this FR fixes their tests without reopening any retirement.

**Verdict:** APPROVED WITH REVISIONS — the witness-hardening direction is sound, but authority activates only after the FR resolves its stale-directory/importability contradiction and preserves FR-910's original filesystem-absence contract instead of silently weakening it.

**Reviewed against:** `feature-requests/FR-924-harden-retirement-witnesses.md`; `tests/unit/test_fr909_a2a_retirement.py`; `tests/unit/test_fr910_mcp_retirement.py`; `tests/unit/test_fr915_mastra_demo_retirement.py`; `feature-requests/FR-858-retire-committed-fr-board.md`; `feature-requests/FR-909-retire-a2a-surface.md`; `feature-requests/FR-910-retire-mcp-surface.md`; `feature-requests/FR-915-retire-mastra-integration-demo.md`; `docs/confessions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`.

## What is sound

The problem is real. The current FR-909 witness asserts filesystem absence for every retired A2A path at `tests/unit/test_fr909_a2a_retirement.py:48-50`, while FR-909's governing AC-01 specified a tracked-file question via `git ls-files 'yamlgraph/a2a/*' ...` at `feature-requests/FR-909-retire-a2a-surface.md:86-90`. FR-915 has the same mismatch: its witness asserts `(EXAMPLES / "demos" / "mastra-integration").exists()` at `tests/unit/test_fr915_mastra_demo_retirement.py:19-20`, while FR-915 AC-02 specified `git ls-files 'examples/demos/mastra-integration/*'` at `feature-requests/FR-915-retire-mastra-integration-demo.md:104-110`.

The import guard is a necessary hardening, not decoration. FR-924 identifies that a stale `yamlgraph/a2a/` directory can make `import yamlgraph.a2a` succeed as a namespace package at `feature-requests/FR-924-harden-retirement-witnesses.md:48-56`, and the Proposed Solution names concrete retired import surfaces at `feature-requests/FR-924-harden-retirement-witnesses.md:72-84`. That aligns with the repo doctrine to normalize at the boundary rather than patching downstream symptoms (`.github/copilot-instructions.md:51-71`).

The chosen mechanism has precedent. FR-858 is cited as the `git ls-files` witness precedent in FR-924 at `feature-requests/FR-924-harden-retirement-witnesses.md:16-18` and `feature-requests/FR-924-harden-retirement-witnesses.md:114-117`; its confession states that the test must ask git the tracking question because no library answer exists at `docs/confessions.md:1851-1855`.

The strategic classification is **test/process witness hardening**, not a framework primitive. The FR touches three existing retirement witnesses, confessions, changelog, and the FR record; it does not authorize new production behavior, new graph artifacts, or new user-facing APIs. Its single concern is the boundary question a retirement witness asks.

## Required revisions

### R-1: Resolve the stale-directory versus importability contradiction

Fold this into the FR before enforcement: AC-02 and AC-03 must not both claim that `tests/unit/test_fr909_a2a_retirement.py` passes with a stale `yamlgraph/a2a/__pycache__/` directory and that an import guard for `yamlgraph.a2a` fails while that namespace package exists. The current AC-02 says the FR-909 test module passes with stale untracked residue at `feature-requests/FR-924-harden-retirement-witnesses.md:95-97`, while AC-03 requires the import guard to fail in exactly that state at `feature-requests/FR-924-harden-retirement-witnesses.md:97`.

Use this resolution: the tracked-absence assertion must pass with stale untracked residue, but the full FR-909 witness module must fail while `import yamlgraph.a2a` succeeds; with the stale directory removed, the full module must pass. This preserves FR-924's own claim that E-4 is "the part that matters" at `feature-requests/FR-924-harden-retirement-witnesses.md:51-56`.

### R-2: Preserve FR-910's filesystem-absence contract

Fold this into the Summary, Proposed Solution, and AC-01: do not claim that all three governing retirement FRs specified tracked absence. FR-910 AC-01 explicitly required `test ! -e yamlgraph/export/mcp.py && test ! -e .vscode/mcp.json && test ! -e reference/mcp-server.md` at `feature-requests/FR-910-retire-mcp-surface.md:89-95`, and its current witness enforces filesystem absence at `tests/unit/test_fr910_mcp_retirement.py:48-50`.

The FR-910 witness may add `git ls-files` checks and must add the `yamlgraph.export.mcp` import guard, but it must not silently replace FR-910 AC-01's filesystem-absence checks for `yamlgraph/export/mcp.py`, `.vscode/mcp.json`, or `reference/mcp-server.md`. If any of those checks move from `Path.exists()` to a helper, the helper must still answer the same filesystem-absence question for those three paths.

### R-3: Tighten the authorized diff surface

Replace AC-07's broad "contains only `tests/`, `docs/confessions.md`, `feature-requests/`, and `changelog/`" wording at `feature-requests/FR-924-harden-retirement-witnesses.md:101` with an exact file allowlist: the three named witness modules, `docs/confessions.md`, `feature-requests/FR-924-harden-retirement-witnesses.md`, the final judgement artifact, and one FR-924 changelog fragment. Broad directory allowances would permit unrelated feature-request or test edits under the same umbrella.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tests/unit/test_fr909_a2a_retirement.py`: replace the tracked-deletion witness with a `git ls-files` assertion and add import guards for `yamlgraph.a2a`, `yamlgraph.a2a.server`, `yamlgraph.a2a.message`, `yamlgraph.contrib.a2a_client`, and `yamlgraph.cli.a2a_commands`. |
| D-2 | `tests/unit/test_fr910_mcp_retirement.py`: add tracked-file checks where they do not weaken FR-910, preserve filesystem-absence checks required by FR-910 AC-01, and add an import guard for `yamlgraph.export.mcp`. |
| D-3 | `tests/unit/test_fr915_mastra_demo_retirement.py`: replace the demo-directory deletion witness with a `git ls-files 'examples/demos/mastra-integration/*'` assertion. |
| D-4 | `docs/confessions.md`: add only the new `S603` confessions required by the local `subprocess.run(["git", "ls-files", ...])` witnesses. |
| D-5 | `feature-requests/FR-924-harden-retirement-witnesses.md`: fold R-1 through R-3 and later record implementation status/decisions. |
| D-6 | `feature-requests/FR-924-harden-retirement-witnesses.judgement.md`: final human-reviewed judgement artifact produced from this draft if accepted. |
| D-7 | `changelog/unreleased/<fr-924-...>.md`: one fix fragment naming FR-924. |

Not authorized: production code under `yamlgraph/`; graph or prompt artifacts; cleanup hooks; CI changes; `.gitignore` changes; deletion of stale local build residue as the implementation; reopening FR-909, FR-910, or FR-915 retirement scope; moving helpers into shared `conftest.py`; broad refactors of retirement witnesses beyond the three named modules.

## Revised acceptance criteria

- [ ] AC-01: FR-924 is revised to state the three witness questions separately: git tracked absence, Python import absence, and retained FR-910 filesystem absence.
- [ ] AC-02: `tests/unit/test_fr909_a2a_retirement.py` uses `git ls-files` to assert no tracked files for every path in its A2A `DELETED_PATHS`, and no `Path.exists()` assertion remains in that tracked-deletion test.
- [ ] AC-03: The FR-909 tracked-absence assertion passes with stale untracked `yamlgraph/a2a/__pycache__/` residue, but the FR-909 import guard fails while `import yamlgraph.a2a` succeeds; after the stale directory is removed, `pytest tests/unit/test_fr909_a2a_retirement.py -q --no-cov` passes.
- [ ] AC-04: The FR-909 import guard asserts `ModuleNotFoundError` for `yamlgraph.a2a`, `yamlgraph.a2a.server`, `yamlgraph.a2a.message`, `yamlgraph.contrib.a2a_client`, and `yamlgraph.cli.a2a_commands`.
- [ ] AC-05: `tests/unit/test_fr910_mcp_retirement.py` preserves filesystem-absence checks for `yamlgraph/export/mcp.py`, `.vscode/mcp.json`, and `reference/mcp-server.md`, adds any non-weakening tracked-file checks needed for the remaining retired paths, and asserts `ModuleNotFoundError` for `yamlgraph.export.mcp`.
- [ ] AC-06: `tests/unit/test_fr915_mastra_demo_retirement.py` uses `git ls-files 'examples/demos/mastra-integration/*'` to assert no tracked retired demo files, and no `Path.exists()` assertion remains in that demo-directory deletion witness.
- [ ] AC-07: Any new `subprocess` `S603` suppressions are documented in `docs/confessions.md`, and `python scripts/noqa_coverage.py --strict` passes.
- [ ] AC-08: `pytest tests/unit/test_fr909_a2a_retirement.py tests/unit/test_fr910_mcp_retirement.py tests/unit/test_fr915_mastra_demo_retirement.py -q --no-cov` passes on a tree with no importable stale retired package directories.
- [ ] AC-09: Full unit suite passes; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-10: `git diff --name-only` contains only the exact surfaces listed in D-1 through D-7.
- [ ] AC-11: A changelog fragment exists under `changelog/unreleased/` with `type: fix` and text naming FR-924.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority exists until R-1 through R-3 are folded into `feature-requests/FR-924-harden-retirement-witnesses.md`. | GATE |
| C-2 | The enforcer must not weaken FR-910 AC-01's filesystem-absence checks while hardening tracked-file and import witnesses. | GATE |
| C-3 | Import guards must exercise the real import system; no monkeypatching `sys.path`, deleting local residue during the test, or mutating `sys.modules` to manufacture success. | GATE |
| C-4 | No production code, graph, prompt, CI, hook, or `.gitignore` change is authorized by this FR. | GATE |
| C-5 | A failing import guard caused by stale `yamlgraph/a2a/` residue is not a false failure; it is the namespace-package hazard FR-924 elected to witness. | GATE |

Authority granted: after the required revisions are folded, implement only the three named retirement-witness hardenings, their necessary `S603` confessions, the FR status update, the final judgement artifact, and the FR-924 changelog fragment.
