# Problem brief: precedent evidence reaches the Judge from two disconnected mechanisms

**Prior art:** filename-noun hits share the generic nouns "research" and
"brief" with every file in `feature-requests/research-briefs/` and are
subject-unrelated: `fr-891-web-research-fail-open.md` concerns the
librarian's web-search failure mode, not corpus precedent —
distinguished. `research-route-grounding-echo.md` concerns whether
persona output echoes the brief, adjacent but about echo detection
rather than about what corpus the personas are given — distinguished.
`fr-892-corpus-census-brief.md` and `fr-899-repo-census-brief.md` are
census/inventory subjects over the repo, not evidence delivery to the
Judge — not applicable. FR-737 and FR-738 (the prior-art hook and its
pre-commit gate) and FR-890/FR-896 (the research sole route) are the
direct territory this brief re-enters and are described as current
state below, not as unexamined precedent.

## Problem statement

The Judge withholds authority from a feature request on two independent
evidence grounds. `.github/skills/judge-fr/doctrine.md` requires that
"prior art — including REJECTED FRs — must be dispositioned before
authority is granted, whether or not the prior-art hook fired: a
rejected FR is precedent, and a proposal re-entering its territory must
distinguish itself or die by the same rationale (FR-737)". The same
doctrine, after the FR-890 activation boundary, withholds authority
from any FR whose `**Research:**` field is absent, dangling, or points
at a strawman record.

Those two evidence classes are produced by two mechanisms that do not
meet, at two different times, from two different corpora.

Precedent evidence is produced at FR-file creation time by
`.github/hooks/scripts/checks/prior_art.py`. It extracts nouns from the
new file's *filename only* (FR-737 F4 purged title and body
extraction), ranks candidate files in `feature-requests/` by inverse
corpus frequency, emits at most five, and stays silent unless at least
one noun is rare (frequency ≤ 20 files). Its output is advisory text on
stdout. `.github/hooks/scripts/checks/prior_art_gate.py` then fails a
commit when a newly ADDED `feature-requests/*.md` has hits and the
staged blob lacks a `**Prior art:**` marker. The gate checks that the
marker string is present; it reads nothing about what the line says.
331 of 854 FR files currently carry the marker.

Research evidence is produced earlier, by `scripts/research.sh` and
`examples/demos/research-route/graph.yaml`. Five personas fan out over
a closed problem brief and are grounded by exactly one deterministic
context block, built by `collect_committed_context` in
`examples/demos/research-route/nodes/research_tools.py`: capability
registry one-liners, `ARCHITECTURE.md` headings, and Scripture
trap/cure keys. The feature-request corpus is not in that block. No
node of the research graph reads `feature-requests/`.

The frozen artifact schema nevertheless makes `precedent` a required,
non-empty column for every row
(`scripts/research_preflight.py`, `COLUMNS`). Only librarian rows are
checked further, and only for a URL. Every other persona is required to
produce a precedent citation from a context window that contains no
precedent corpus.

Measured over the twelve committed `feature-requests/*.research.md`
artifacts, 60 rows in total: 33 precedent cells name an `FR-`, `NC-`,
`CAP-` or `REQ-` identifier; 12 carry a URL only (the librarian rows);
15 carry neither — a quarter of all rows satisfy the non-empty shape
check while citing nothing that can be looked up. Twelve cells use a
literal `brief-echo:` prefix, restating the brief back as its own
precedent.

The ordering compounds this. Research runs first, over a brief whose
filename is not yet an FR filename, so the prior-art hook has not fired
and cannot fire. The prior-art hook fires later, when the FR file is
created — after the alternatives have already been generated, ranked
and reduced. The step whose output most depends on knowing what was
already tried, rejected, or shipped is the step run with no access to
that record; the step that retrieves the record runs after the
conclusions are frozen.

The Judge then receives neither mechanism's output as input.
`scripts/judge.sh` passes exactly one variable, `fr_path`, to the judge
graph. The judge prompt tells the agent to read the doctrine and the FR.
Both the prior-art disposition and the research record are reachable
only if the judge navigates markdown references out of the FR body and
reads them itself. Doctrine holds the Judge responsible for the
substance of evidence that arrives, if it arrives, as prose the author
wrote about a retrieval the author performed.

The open question this brief poses: at what point in the research →
plan → judge sequence should the feature-request corpus be retrieved,
and by what mechanism, such that a precedent claim in the record before
the Judge is a retrieval result rather than an author's or a persona's
unverifiable assertion?

## Classification

judgement/analysis/generation

## Constraints

- The research brief is a closed input boundary (FR-890 R-2). Anything
  injected into the research run must be author-independent and
  deterministic, in the manner of the existing committed-context block;
  it must not be a channel through which the author's narrative or a
  preferred conclusion reaches the personas.
- The artifact schema `candidate | persona | class | verdict |
  precedent | is_this_a_graph | effort-risk | rationale` is frozen and
  witnessed by tests in both `scripts/research_preflight.py` and
  `examples/demos/research-route/nodes/research_tools.py`. Column
  changes are not free.
- The `committed_context` block is bounded by `_MAX_CONTEXT_LINES` and
  raises when exceeded. The FR corpus is 854 files; it cannot be
  delivered whole.
- Prior-art retrieval today is filename-noun matching with an inverse
  frequency rank and a rarity floor. FR-737 F4 deliberately removed
  title and body extraction and recorded that escalation beyond
  filenames requires a witnessed miss (`two_strike_split`).
- Judge input closure is FR + cited evidence + repo doctrine only. Any
  evidence must arrive as a committed artifact the FR cites, not as a
  side channel or a chat narrative.
- Local checks are individually skippable by name; `--no-verify` is
  forbidden. Skippability is accepted, not a defect.
- Research runs cost tokens and wall-clock time; the route already
  fans out to five personas with a 600-second graph timeout.

## Witnessed incidents

- 15 of 60 precedent cells across all twelve committed research
  artifacts contain no repo identifier and no URL. Example rows in
  `feature-requests/FR-929.research.md` cite `brief-echo:` followed by
  a restatement of the brief's own text as the precedent for a
  candidate.
- The same FR-929 research run produced precedent strings asserting
  what "FR-192 rejected" from persona memory; the personas had no
  access to `feature-requests/FR-192*` in their context, because
  `collect_committed_context` does not read that directory. The claim
  happened to be checkable, but nothing in the route made it so.
- FR-737 U-1 recorded that the advisory PostToolUse prior-art hook
  dropped its first real payload — the delivery channel failed
  silently, which is why FR-738 added a pre-commit floor. The floor
  checks marker presence, not disposition content, so the failure mode
  it does not cover is a `**Prior art:**` line written to clear the
  gate.
- `scripts/judge.sh` invokes the judge graph with `--var fr_path=…` and
  no other variable. No research path, no prior-art hit list, and no
  corpus handle reaches the judge process.
- The FR-890 activation boundary made a missing or dangling
  `**Research:**` field a no-authority condition, and the doctrine text
  explicitly warns that a table which "merely shape-checks" is
  `gate_checks_shape_not_substance`. The precedent column is currently
  shape-checked for non-emptiness only.
