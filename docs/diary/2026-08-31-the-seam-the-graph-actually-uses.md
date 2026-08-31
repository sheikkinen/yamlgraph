# 2026-08-31 — The Seam the Graph Actually Uses

FR-932 + FR-933, enforced together because each was hiding the other.

## The shape of the session

FR-933 was REJECTED on first submission for two defects, both mine, both
the same defect: I cited `FR-926-research-route-error-surfacing.md`, a
filename I generated from memory, and I failed to disposition FR-408,
which had already rejected the mechanism I was proposing. The real file is
`FR-926-research-failure-cites-recorded-cause.md`. I hallucinated a
plausible citation *inside the FR about citations generated from memory*.
The judge caught both in one pass by reading the corpus. That is the
comparison FR-932's retrieval has to answer, and it does not yet.

Then enforcement produced two findings neither FR predicted.

## Finding 1 — I measured the wrong code for an hour

The fix was in the worktree. The live run still showed nothing. I added an
unconditional probe log to the changed function — the probe never fired.
That is an impossible result, and an impossible result is a tripwire:
the code being executed is not the code I am reading.

`scripts/research.sh` resolves its executor with `command -v yamlgraph`.
That is a **console script**. Console scripts do not put the working
directory on `sys.path`, so every "live" run of my branch was importing
the framework from the **main checkout**. `PYTHONPATH="$PWD"` and the
retry converged on the first try.

Scripture already has the cure — `artifact_carries_code_identity`, written
for shared-repo measurement runs — but it is phrased as *stamp the
artifact*, which is a post-hoc audit. What I needed was a *pre-hoc*
guarantee: the route should resolve an interpreter, not a console script.
The same class recurred twice more in the same day (`scripts/ramp.sh`,
`.github/hooks/scripts/checks/yaml-checks.sh` — both `exec python3` into
an interpreter without PyYAML, both silently dead). Three instances in one
session is a graduation, not a coincidence.

The trap has a name worth keeping: **an impossible observation is not a
measurement problem, it is a provenance problem.** Before instrumenting
further, prove the code you are reading is the code that ran.

## Finding 2 — green on a seam that does not exist

Once the route succeeded, it produced its first artifact — and the
artifact said `prior_art: none-retrieved`. A direct call to the same
function returned four hits.

The research node called
`collect_committed_context(repo_root=<whole state dict>, brief_path="")`.
A python node is invoked as `func(effective_state)`: **one positional
dict**. `repo_root` survived only because `_state_value` happens to unwrap
a dict. `brief_path` kept its empty default and the prior-art branch
returned nothing.

Every unit witness passed **two positional strings** — a calling
convention the graph never uses. FR-932 shipped a mechanism that was green
on an imaginary seam and dead on the real one. `name_the_seam` says name a
test after the seam it exercises; the deeper form is: *name the seam after
the caller that exists.* A test whose call shape differs from the runtime's
call shape is not testing integration, it is testing a function I invented.

Why was this invisible for a whole FR? Because **no run of this route had
ever succeeded far enough to produce an artifact.** It died at the
validation retry every time. The first green run was the first observation.
A pipeline that has never completed has never been observed, and every
claim about its middle is inference.

## The interlock

FR-933 could not produce its live witness until FR-932's route ran.
FR-932's AC-10 could not be met until FR-933's retry converged. Neither
defect was visible until the other moved. Two FRs mutually blocking is not
a scheduling accident — it is the signature of a pipeline whose failures
are all reported at the same exit code.

## Heuristics

- `impossible_observation_is_provenance`: when a probe that cannot fail
  does not fire, stop investigating behaviour and prove code identity.
  Resolve interpreters, not console scripts, in any script that measures.
- `witness_the_callers_shape`: a unit witness must call the function the
  way its real caller calls it. Enumerate callers before choosing the
  signature you test.
- `first_success_is_first_observation`: a stage that has never completed
  has never been measured. Treat every claim about an unexercised middle
  as a hypothesis.

## Process notes

- The req-collision gate rejected my changelog fragment for claiming
  `REQ-YG-027`, which `FR-315` already claims and which no FR can own
  because `CAP-08` is `fr: legacy`. The gate is correct and the honest
  move was to drop the optional `req:` line, not to weaken the test.
- `git commit --amend` swept six staged files from a *different* FR into
  the commit. Amend takes the index, not the previous commit's file set.
  Caught it in `show --stat`; split with `reset --soft` + `restore
  --staged`. A stray auto-generated `docs/diary/2026-08-31-git-report.md`
  rode in the same way and was removed — it would have satisfied the
  diary-gate without anyone having reflected, which is
  `gate_checks_shape_not_substance` arriving by accident.

**Seed:** The judge found FR-408 by reading the corpus; filename-noun IDF
could not reach it at any floor setting, because the signal was never in
the filename. If an LLM pass over the FR corpus outperforms the lexical
retriever on the only case that mattered — what is the retriever *for*?
Is its job to find precedent, or to be the cheap floor that makes a
model's miss auditable? Those two jobs have different acceptance criteria,
and FR-932 froze the first while delivering the second.
