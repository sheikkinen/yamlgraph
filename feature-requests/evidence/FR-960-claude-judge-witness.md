# FR-960 Evidence — Claude judge variant witness (authoring proof, live runs, dual-run inventory)

**FR:** [FR-960](../FR-960-claude-judge-variant.md) · **Judgement:** [FR-960 judgement](../FR-960-claude-judge-variant.judgement.md) (R-6 protocol)
**Branch:** `feat/fr-960-claude-judge-variant` · **Host:** Windows 11, Git Bash inside the Claude desktop app's process tree; `copilot` 1.0.82 on PATH; Claude Code 2.1.255 at the MSIX LocalCache path (see FR-959 evidence)

## 1. Authoring proof (judgement C-3, AC-03)

| Field | Value |
|---|---|
| Command | `scripts/author.sh --no-preflight feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md` with `PATH=/c/src/yamlgraph/.venv/Scripts:$PATH`, `YAMLGRAPH_BIN=…/.venv/Scripts/yamlgraph.exe`. The pre-flight was run first, separately, with the venv interpreter (`python scripts/author_preflight.py <brief> --workdir .`): premise `.github/skills/judge-fr/adapters/graph.yaml` exists; commands `yamlgraph`, `yamlgraph`, `python`, `python` resolve; rc 0. `--no-preflight` only skipped the wrapper's second, identical run of that check (its `python3` lookup hits the Windows Store stub on this host). |
| Brief | `feature-requests/authoring-briefs/fr-960-claude-judge-variant-brief.md`, committed in `9a4ecd76` before the run |
| Run | 2026-09-03 03:38:58Z start; yamlgraph 0.5.23 run id `01a06559-2c61-75a1-9f2b-cea95070459e`; Copilot CLI session `2190105c-3750-456f-9206-c867d1fbd1d6`, model `gpt-5.5`; wrapper verified the report (`author rc=0`) |
| Local report | `tmp/draft-authoring-report.md` — **not committed** (`.github/skills/graph-authoring/SKILL.md:35`); sha256 `ed42ab0f96797f205f9212eec4cdfa0a4937ef2c6fa38ed9afefe2f33d0feee0` |
| Report — Artifacts (quoted) | `.github/skills/judge-fr/adapters/graph.yaml`; `.github/skills/judge-fr/adapters/prompts/judge.yaml` |
| Report — Validation (quoted) | "`yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml` -> passed, 0 issues." · "`yamlgraph graph validate …` -> passed, graph valid with 3 nodes and 5 edges." · "`python -m pytest tests/unit/test_fr960_claude_judge_variant.py -k TestGraphRouting …` -> passed, 4 passed and 8 deselected." · "`python -m pytest tests/unit/test_fr931_sole_route_model_pin.py …` -> passed, 3 passed." |
| Report — Repairs (quoted) | "Initial lint reported `E601` for `select` because passthrough nodes require an explicit `output` mapping. Repaired by adding `output: {}` to the selector node, matching existing committed passthrough precedent." |
| Report — Blocked validation (quoted) | "None." |
| Re-verified by the requesting session | lint 0 issues; validate ok; routing + pin tests 7 passed; `git diff` of the two files matches the brief's target byte-for-byte except the `output: {}` repair and the two header-comment edits the brief allowed |
| Graph commit | `235e2cab` (`feat(judge): FR-960 Claude judge variant …`) |
| Limitations | The authoring agent ran under Copilot on this host; it did not execute any judge. The wrapper's own bash tests could not run from pytest here (FR-953 class) and were exercised by hand — see FR-960 Implementation Status. |

## 2. Live runs

### 2.1 Run A — default backend (`copilot`), target FR-961

| Field | Value |
|---|---|
| Target | `feature-requests/FR-961-claude-code-hooks-registration.md` (Status Proposed, unjudged before this run) at commit `235e2cab` |
| Command | `YAMLGRAPH_BIN=…/.venv/Scripts/yamlgraph.exe bash scripts/judge.sh feature-requests/FR-961-claude-code-hooks-registration.md` (no `JUDGE_BACKEND` set → `copilot`) |
| Backend / model | `copilot` · Copilot CLI 1.0.82 · `gpt-5.6-sol` (graph pin) |
| Auth mode | GitHub Copilot seat (unchanged route; FR-959 preflight not involved) |
| Start / end | 2026-09-03T03:43:22Z / 2026-09-03T03:47:42Z |
| Run id / session | yamlgraph run `01a0655d-3bc3-7ade-a34d-bf1e22c8e34a`; Copilot session `cc5b174b-3ba7-496f-80b4-91f80375c474` |
| Artifact | `tmp/draft-judgement-copilot-FR-961-claude-code-hooks-registration.md` — 19,670 bytes, 122 lines, sha256 `4d1ce473f6f69b5d177558c364bb97332e3f225b2a6108ec7de74d81b6e1ef70` (local; kept as `tmp/draft-judgement-copilot-FR-961-…` for the inventory) |
| Verdict line | `**Verdict:** APPROVED WITH REVISIONS - the shared-script, thin-registration direction is sound and cohesive, but authority activates only after runtime provenance, interpreter failure semantics, transcript selection, evidence closure, and the two human decisions are made mechanically unambiguous.` |
| Wrapper output | `judge.sh: draft written: …/tmp/draft-judgement-copilot-FR-961-claude-code-hooks-registration.md (backend=copilot; advisory until human-reviewed)`, rc 0 |
| Coexistence | the pre-FR-960 fixed-name file `tmp/draft-judgement.md` (from the 2026-09-02 FR-960 judgement) was **not** touched by this run — the first live proof that the new naming stops the clobber |

### 2.2 Run B — `JUDGE_BACKEND=claude`, target FR-961

_Waits for the C-8 spend decision (§4, signature 2). Not started._

### 2.3 Run B' — Run B with `ANTHROPIC_API_KEY=sk-invalid-on-purpose` exported (AC-13)

_Not started._

## 3. Dual-run inventory (judgement R-6, AC-15)

_Filled after runs A and B. Items are `CP-n` (Copilot draft) and `CL-n` (Claude draft); each carries `matched <id>`, `contradicted <id>`, or `backend-only`, with the source section and the file:line evidence each relies on. If no item is `contradicted` or `backend-only`, this section ends with the literal sentinel `no backend-only or contradicted items`._

## 4. Signatures (judgement AC-16; a human other than the enforcer)

1. Enforcement-infrastructure diff and route invariants accepted by: `<name>, <date>` — **UNSIGNED**
2. Residual Claude subscription payer boundary (FR-959 §5) accepted for judge execution by: `<name>, <date>` — **UNSIGNED**

## 5. Limitations

_Filled at the end._
