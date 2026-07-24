# 2026-07-24 — The venv died mid-commit, and the failures lied about why

**Context:** a routine diary commit failed because `pre-commit` had a
dead shebang: the venv's base interpreter (pyenv 3.12.3) no longer
existed after a system Python cleanup (`rm -rf ~/opt/anaconda3` and
friends). Rebuilt the venv on Python 3.14.6 — the newest inside
`>=3.11,<3.15` — and the first smoke run showed 14 failures + 1 error.

**The trap (a compound one):** the obvious story was "Python 3.14
incompatibility" — new interpreter, red suite, case closed. The actual
story, exposed by reading one traceback instead of theorizing
(`read_raw_output_first`), was `ModuleNotFoundError: No module named
'bs4'`: the old venv had accumulated optional extras (`digest`,
`storyboard`, …) that a bare `.[dev]` reinstall does not restore. All
14 failures were dependency-gap cascades. After `.[digest,storyboard]`:
5203 passed, zero failures. Python 3.14 was never the problem.

**Second trip of the day on the same wire:** the recommit swept two
foreign staged files (`2026-07-23-git-report.md`, `world-digest.md`)
from a parallel session into my commit. The mandatory `git show --stat`
audit caught it; soft-reset, recommit with explicit path, foreign files
left staged for their owner. This is the fourth-plus recorded
`one_session_one_repo` interleave — the ritual (staged-check, explicit
file lists, post-commit audit) is earning its keep, but only the audit
step fired; the pre-commit staged-check was skipped because "I knew"
what was staged. I did not know.

**Heuristic:** a rebuilt environment is a *new boundary*, not a
restored one. The delta between old-venv and fresh-venv is invisible
state (extras, editable installs, console scripts) that manifests as
plausible-but-wrong failure narratives on whatever change you made
next. Cure: after any venv rebuild, diff expectations mechanically —
run the suite before blaming the change, and read the first raw
traceback before naming the cause. Also: earlier this same session,
stale working-tree files (version downgrade, marker deletion) were the
same phenomenon in mirror — environment state pretending to be work.

**Seed:** should the repo pin its dev environment declaratively — a
single `make venv` / `uv sync` target that installs the exact extras
the unit suite imports — so "rebuild the venv" is one command with no
memory required? The extras a test file needs are discoverable from
its imports; a check could assert the dev target covers them.
