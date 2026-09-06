# Authoring brief: FR-1011 relocate the three live graphs out of `.chaplain/graphs/`

**Governing FR:** feature-requests/FR-1011-relocate-chaplain-live-parts.md (judged APPROVED WITH REVISIONS 2026-09-06; scope frozen D-1…D-10; this brief is D-2 and covers D-3 only)
**Prior art:** feature-requests/FR-196-portable-chaplain.md moved `philosopher` INTO `.chaplain/graphs/` and introduced the `parents[2]/lib/diary.py` proxy — this brief reverses that move. `graphs/enforcement/` is the committed precedent for a dir-style process graph under `graphs/` (spec + `prompts/`). The three graphs being moved are their own precedent: the artifacts already exist and are relocated, not authored anew.
**Target directory:** the repository root of the current working tree (relative paths below). Everything moved stays inside this repository.
**Artifacts to author (relocations, `git mv` so history follows):**

| From | To |
|---|---|
| `.chaplain/graphs/fr_triage/` (graph.yaml, prompts/*.yaml, tools.py) | `graphs/fr_triage/` |
| `.chaplain/graphs/world_distill/` (graph.yaml, prompts/*.yaml, tools.py) | `graphs/world_distill/` |
| `.chaplain/graphs/philosopher/` (graph.yaml, prompts/analyze.yaml, challenge.yaml, distill.yaml, reflect.yaml, tools.py, README.md) | `graphs/philosopher/` |
| `.chaplain/lib/diary.py` | `graphs/philosopher/diary.py` |

Do NOT move or edit anything else under `.chaplain/` (watcher graphs, `lib/finalize_lib.sh`, `lib/watcher`, `lib/worktree.py`, scripts, config) — those belong to other deliverables or to Phase 2. Do NOT touch `__pycache__` directories (untracked; delete the moved-from ones if they block the move).

## Task

Relocate the three graph packages with `git mv` (directory moves), then make the **path-only** edits inside the relocated packages listed below. No node, edge, prompt text, schema, provider, model, temperature, or tool-function change of any kind (FR-1011 C-5). If a lint or smoke failure seems to require a semantic change, STOP and record it under "Blocked validation" — do not repair semantics.

### Path-only edits inside the relocated packages (exhaustive)

1. `graphs/philosopher/tools.py`
   - `write_proposals` docstring (old line 261): "Write graduation proposals to `.chaplain/inbox/`." → "Write graduation proposals to the `inbox_dir` state path (the operator's `proposals/` directory)."
   - `write_diary` (old lines 364–371): docstring "Proxy to .chaplain/lib/diary.py:write_diary." → "Proxy to the sibling diary.py:write_diary."; the sentence about "the shared diary library outside this directory is loaded by absolute path" → "the diary library is a sibling file of this module, loaded by path"; and the load line
     `lib_path = Path(__file__).resolve().parents[2] / "lib" / "diary.py"` → `lib_path = Path(__file__).with_name("diary.py")`.
     Keep the module name string `"chaplain_lib_diary"` and everything else in the function unchanged.
2. `graphs/philosopher/graph.yaml` — comments only:
   - line 5 `# FR-196: Relocated from examples/philosopher/ to .chaplain/graphs/philosopher/` → `# FR-196: relocated from examples/philosopher/ to .chaplain/graphs/philosopher/; FR-1011: relocated to graphs/philosopher/`
   - line 12 in `description:` "…from reaching .chaplain/inbox/." → "…from reaching the proposals inbox."
   - line 21 `inbox_dir: str                # Path to .chaplain/inbox/` → `inbox_dir: str                # Path to the proposals inbox (proposals/ on the operator's main checkout)`
   Nothing else in the file changes — not `name`, not `state`, not `tools`, not `nodes`, not `edges`.
3. `graphs/philosopher/README.md` — rewrite truthfully and briefly:
   - Remove the `.chaplain/philosopher.sh` usage block (the wrapper belongs to the dead runtime and is not relocated).
   - "Run directly" command: `yamlgraph graph run graphs/philosopher/graph.yaml --var diary_dir="docs/diary" --var inbox_dir="proposals" …` (keep the other `--var` flags as they are).
   - Phase 5 line: "Write graduation proposals to `inbox_dir` (`proposals/`)".
   - Replace the "Portability" section with two sentences: the graph is self-contained in `graphs/philosopher/` — `tools.py` loads the sibling `diary.py` by path (CAP-75 graph-scope tool loading); it makes no claim about copying `.chaplain/`.
   - Remove the "Related" watcher-plan / watcher-enforce links (they point into the runtime scheduled for removal). Keep the FR list in the first line.
4. `graphs/fr_triage/**` and `graphs/world_distill/**`: no content edits are expected. If any file inside them contains the literal `.chaplain`, report the line under "Artifacts" and change only that path literal; otherwise leave the files byte-identical.

Do NOT edit any file outside `graphs/{fr_triage,world_distill,philosopher}/` — consumers (`triage_gate.py`, `now.py`, skills, CAPs, tests, `.gitignore`, `finalize_merge.sh`) are edited by the requesting session under D-4…D-9, not by this run. Do NOT `git commit`, `git add -A`, or stage anything beyond what `git mv` stages itself.

## Validation the authoring run must perform

All output goes under `tmp/`. Never run fr_triage against a committed FR file; never write to `docs/world-context.md`; never write proposals or diary entries into tracked directories.

```bash
yamlgraph graph lint graphs/fr_triage/graph.yaml
yamlgraph graph lint graphs/world_distill/graph.yaml
yamlgraph graph lint graphs/philosopher/graph.yaml
```

```bash
mkdir -p tmp
cp feature-requests/FR-1011-relocate-chaplain-live-parts.md tmp/fr1011-smoke-fr.md
yamlgraph graph run graphs/fr_triage/graph.yaml --var fr_path=tmp/fr1011-smoke-fr.md --full
yamlgraph graph run graphs/world_distill/graph.yaml --var date=$(date +%F) --var output_path=tmp/fr1011-world-context.md --full
```

The third real smoke (`graphs/philosopher/graph.yaml`, three Copilot nodes) is
budgeted separately: it runs through the sibling validation-only brief
`feature-requests/authoring-briefs/fr-1011-relocate-chaplain-live-parts-smoke-brief.md`
after this run, so this run stays inside the backend's 900 s ceiling
(author_preflight budget finding). Do not run it here.

Record each command verbatim with its outcome. A smoke that fails for a missing credential or an unavailable model is recorded under "Blocked validation" with the exact error — never substituted, never mocked, never retried with a different provider. Then confirm the relocation is a rename in git's eyes:

```bash
git status --short
git diff --cached --name-status -M90% | grep -E '^R'
```

Every moved file must appear as `R` (rename). Report the list under "Artifacts".
