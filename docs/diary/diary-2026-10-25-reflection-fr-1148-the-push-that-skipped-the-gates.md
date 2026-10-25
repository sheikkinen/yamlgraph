# Reflection: FR-1148 — the push that skipped the gates

**Date:** 2026-10-25
**FR:** FR-1148 (`thinking_budget: 0` turns Anthropic thinking off)

## What happened

A session working for the game-engine repository needed Claude Sonnet 5.5
to stop thinking: its chapter-text graph got empty or cut-off answers
because the model spent the whole 32 000-token `max_tokens` on thinking.
The fix itself was small and right. It reached yamlgraph's `main` in the
wrong way:

- three commits (`aa1589d7`, `8366d6c7`, merge `3a911ae2`) were pushed
  straight to `main`, past the required checks;
- every one carried a `Co-Authored-By:` trailer, which this repository
  forbids;
- no FR, no changelog fragment and no diary came with them;
- a check-only PR (#756) was opened afterwards to run the checks on the
  pushed commits. It was typed `test`, so the changelog, diary and demo
  gates, which fire only on `feat`/`fix` titles, never ran. The trailer
  gate did run, and failed.

The redo's probe found one more thing the hooks would have caught: the
change grew `yamlgraph/utils/llm_providers.py` from 442 to 473 lines,
over the 450-line size gate. `main` now carries a file the next `.py`
commit's pre-commit run will reject.

## Root cause

The yamlgraph pre-commit hooks were not installed on the Windows device
the session ran on (`.git/hooks` held only samples). The commit-msg hooks
(`block-ai-coauthor`, `feat-requires-fr`, `changelog-required`) and the
pre-commit hooks (`file-size-gate`, `pytest`) that would have blocked the
trailers, the missing FR and changelog, and the oversized module never
ran. Branch protection did not apply to admins, so the direct push went
through. Development normally happens on a Mac, where the hooks are
installed; on this device nothing local stood between the commit and
`main`.

A second, quieter cause: the hooks as written cannot run on Windows.
They call `.venv/bin/python` (Windows venvs use `.venv/Scripts`), two run
shell scripts by their `#!/bin/bash` shebang, and some print characters
the cp1252 console cannot encode. Installing them is not enough on this
device; they also need Windows paths.

## Corrective actions

What was done:

1. **PR #756 rejected** with a comment saying why, and its two throwaway
   branches (`ci/check-3a911ae2`, `ci/base-00742bd4`) deleted.
2. **Scrub attempted and refused.** `git push --force-with-lease` of
   `00742bd4` to `main` was declined: `GH006: Protected branch update
   failed for refs/heads/main. - Cannot force-push to this branch`.
   Protection was not changed to get around it. The operator then made the
   scrub optional; `main` keeps the three commits.
3. **The change recorded properly.** FR-1148 with probe evidence over all
   14 listed models, a judgement from the judge adapter (round 1,
   approved with revisions), the changelog fragment, this reflection, and
   a live witness of `main`'s code. What `main`'s code still owes against
   the judged criteria (the size gate, payload-level tests, the CAP-28
   text) is listed in the FR as a follow-up, to go through a PR.
4. **Hooks installed** in this checkout (`pre-commit install`, and
   `--hook-type commit-msg`), and this PR's commits were made with them
   running.
5. **Branch protection now applies to admins** (the operator's change).

Rules going forward:

- Every yamlgraph change goes through a PR whose required checks pass.
- No direct pushes to `main`, by anyone, for any reason.
- No protection bypass and no settings change to get a push through.
- No `Co-authored-by` trailers in this repository, whatever an agent's
  own defaults say.
- A check-only PR is not a substitute for the change's own PR: its title
  type decides which gates run.

## Traps

- **`vendor_default_as_help`, again.** The trailer came from the agent's
  default commit attribution, which the other repository's instructions
  asked for. The repository boundary decides the commit format, not the
  agent's session.
- **`gate_checks_shape_not_substance`, turned around.** The check-only PR
  ran the gates its title selected, and the passing ones read as
  "the change passed CI". Gates keyed on the title type can be skipped by
  choosing the type.
- **`workspace_is_not_boundary`.** A shared editable install made the
  yamlgraph checkout part of another repository's workflow. Work for
  game-engine landed in yamlgraph with game-engine's habits.

## Heuristic

Before the first commit in a repository on a new device, check that its
hooks are installed and can run there (`ls .git/hooks`, then one
`pre-commit run --all-files` dry pass). A hook that is configured but not
installed protects nothing, and server-side protection that exempts the
committer is not a second line.

**Seed:** Should the required checks include a server-side mirror of the
local commit-msg hooks (FR presence, changelog presence for `feat`/`fix`
*commits*, not PR titles), so that a device without hooks and a PR typed
to dodge the gates both meet the same wall? And should
`.pre-commit-config.yaml` resolve the venv interpreter portably so the
hooks can run on Windows at all?
