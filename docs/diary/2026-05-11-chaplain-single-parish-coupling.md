# Diary: The Chaplain Governs One Parish

**Date:** 2026-05-11
**FR:** (none — architectural reflection)
**Author:** sami / copilot session

---

## What Happened

Observation: the Chaplain cannot process an inbox entry for `projects/ninchat_voice`. It cannot create worktrees in that project, run its tests, open PRs against its repository, or apply its pre-commit hooks. The Chaplain governs yamlgraph exclusively — its parish has exactly one parishioner.

Tracing why reveals the coupling is not incidental. It is structural, layered, and load-bearing.

---

## The Coupling Chain

**Layer 1: The worktree is a git worktree of the yamlgraph repo.**

`worktree.py` calls `git worktree add <path> -b <branch> main`. This creates a worktree of the *current* git repo — yamlgraph. A `ninchat_voice` feature would need a worktree of the `ninchat_voice` repository (if it were one) or a subdirectory worktree (which git doesn't support natively). The worktree mechanism is hardcoded to the Chaplain's own repo.

**Layer 2: The `.venv` symlink assumes one Python environment.**

`worktree_setup.sh` symlinks `$MAIN_DIR/.venv` into the worktree. This is the yamlgraph `.venv` — `pip install -e ".[dev]"`. A `ninchat_voice` worktree would need its own `.venv` with its own `pyproject.toml`. The single-venv assumption breaks immediately.

**Layer 3: The validate gate runs yamlgraph's test suite.**

`validate_gate_action.py` runs `pytest tests/` and `pre-commit run`. These are yamlgraph's tests and yamlgraph's `.pre-commit-config.yaml`. A `ninchat_voice` enforce phase needs `pytest projects/ninchat_voice/tests/` and the hooks from `projects/ninchat_voice/.pre-commit-config.yaml` (which exists separately).

**Layer 4: The pipeline invokes `yamlgraph graph run`.**

Every action step of type `yamlgraph_async` calls into the yamlgraph runtime. The Chaplain is a YAMLGraph application calling itself. For a `ninchat_voice` Chaplain, this dependency is fine — yamlgraph is a declared dependency — but the *graphs* being invoked (`watcher-plan`, `watcher-enforce`) are stored in `.chaplain/graphs/` inside the yamlgraph repo. They are not bundled with `ninchat_voice`.

**Layer 5: The PRs target the yamlgraph GitHub repository.**

`merge_pr.sh` and `wait_ci.sh` use `gh pr create` against the current repo's remote. A `ninchat_voice` PR would need to target a different remote — either a separate GitHub repo or a different remote on the same monorepo (not how GitHub works).

---

## The Trap: `working_system_inertia`

*"'It works' blocks seeing it clearly."*

The Chaplain works perfectly for yamlgraph because it was built inside yamlgraph, for yamlgraph, making every assumption that yamlgraph is the only project. Each assumption was locally rational. The aggregate is a system that cannot be reused without either (a) everything becoming yamlgraph, or (b) significant parameterization work.

`ninchat_voice` has its own `.pre-commit-config.yaml`. Its own `pyproject.toml`. Its own test suite (`NC-`prefixed tickets). Its own deploy target (Fly.io). Its own feature-request backlog. It is a complete, autonomous project that shares a git repo with yamlgraph for pragmatic reasons (dog-fooding, shared `.venv` economy, atomic commits). But the Chaplain sees only one project: itself.

---

## What Multi-Project Chaplain Would Need

A `chaplain.yaml` project manifest per governed project:

```yaml
# projects/ninchat_voice/chaplain.yaml
project: ninchat_voice
repo_root: ../..              # Path to git root (for worktrees)
work_dir: projects/ninchat_voice
venv: projects/ninchat_voice/.venv
test_cmd: pytest projects/ninchat_voice/tests/
lint_cmd: pre-commit run --config projects/ninchat_voice/.pre-commit-config.yaml
fr_template: projects/ninchat_voice/feature-requests/TEMPLATE.md
inbox: .chaplain/inbox/ninchat_voice/
branch_prefix: feat/nv-
pr_target: origin/main        # Same repo, different prefix convention
```

With this manifest, the Chaplain's pipeline becomes configurable:
- `worktree_setup.sh --config projects/ninchat_voice/chaplain.yaml` creates a worktree with the right venv
- `validate_gate_action` reads `test_cmd` and `lint_cmd` from the manifest
- `git_commit_action` uses `branch_prefix` for naming
- The inbox path is project-scoped

This is not a small change. It requires parameterizing every layer of the pipeline. It is a new FR, not a config tweak.

---

## The Strategic Question

There are two possible responses to this constraint:

**Option A: Accept the limitation.** The Chaplain governs yamlgraph. Each project (`ninchat_voice`, `outcaller`) either gets its own Chaplain instance (requires separate repo) or manages its own development loop manually. The monorepo remains a convenience co-location, not a governed multi-project IDE.

**Option B: Build the multi-project Chaplain.** Parameterize the pipeline via `chaplain.yaml`, make the inbox project-aware, decouple the venv and test commands. The Chaplain becomes a governance service that can target any project directory within a monorepo.

Option A is the current reality. Option B is a significant engineering investment — but it's the investment that would make scripture-dev + Chaplain a genuinely portable governance system, not just a set of hooks with an ambitious README.

---

## The Compounding Observation

`ninchat_voice` is the highest-fidelity user of the yamlgraph framework. It runs in production. It has healthcare domain logic with IEC 62304-adjacent traceability needs (NC-prefixed tickets map to requirements). It generates the most change volume. And it receives *zero* Chaplain automation.

The project with the greatest governance need is the one the governance system cannot reach. That is the clearest possible signal that the current architecture has a scope boundary problem.

---

## Seed

> **What if the inbox were the universal interface?** Any project drops a markdown file into `.chaplain/inbox/<project>/`. The Chaplain reads `chaplain.yaml` from the project directory, selects the right pipeline configuration, and processes the proposal with project-scoped test commands, venv, and branch conventions. The routing layer is trivial; the parameterization is the work. Is `chaplain.yaml` the right primitive, or should the manifest be inferred from the project's own `pyproject.toml` + `ARCHITECTURE.md`?
