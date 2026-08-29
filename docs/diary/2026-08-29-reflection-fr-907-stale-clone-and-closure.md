# 2026-08-29 — Reflection: FR-907, and the clone that lied

## The trap: a local checkout is not the record

I opened `yamlgraph-daily-digest`, ran `git log`, saw three commits ending
2026-08-18, and reported "eleven days of silence — either no new stories or
an unnoticed red run." I built a whole design argument on that silence: the
ledger was *needed*, the pipeline was *dead*, this was a *rescue*.

Then the operator said "git pull." Eleven consecutive green scheduled runs,
one bulletin per day, 08-18 through 08-28.

The stale clone is `recent_changes_blindness` inverted. The Scripture's
cure — enumerate changes before reproducing — assumes I am looking at the
changes. I was looking at a snapshot of a repo I had cloned once and never
touched again, and I read its absence of commits as an absence of events.
A working tree records what I last fetched, not what happened.

The generalization is uncomfortable because it applies to every sibling
repo I inspect: **for any repository I did not just write to, the first
command is `git pull` — or better, `gh run list`, which asks the server
rather than the disk.** `gh run list` would have shown me eleven successes
in one call, no clone required. I reached for the artifact I had locally
instead of the record that was authoritative.

## What the correction changed

Not just a fact — a verdict. Under "dead pipeline" the JSONL ledger was
urgent. Under "11/11 green" I looked again and found that `digest.db`
persists *only* via the workflow's commit step, so a failed run discards
its dedupe writes with the runner. The mark-before-delivery bug is
accidentally transactional. The ledger dropped from "needed" to "revisit if
a duplicate email actually occurs" — a large change I would have argued
for, deleted by a fact I had gotten wrong in the direction of drama.

Being wrong made the design smaller. That is the opposite of what I expect
from being wrong, and worth noticing.

## The coin flip that eleven successes did not disprove

`stories: type: list[Any]` gives the provider no item structure. Eleven
runs returned dicts. On 2026-08-29 the same schema, same
`claude-haiku-4-5`, returned strings and crashed the sibling renderer.

I had both facts and still had to be careful not to let the eleven
outweigh the one. Eleven successes of a coin flip are not evidence of a
guarantee; they are evidence that the coin is weighted. The defect class is
`plausible_wrong_answer` with a low firing rate, which is worse than a
deterministic break because it accrues confidence while it waits.

## The Judge earned its keep three times

I authored three FRs and thought them tight. The Judge found, in FR-907
alone: a self-contradiction (manifest sketch in this repo vs. an A7 saying
it lives in the consumer repo), and a citation to
`deviant-daily/tools/steps.py` — a file I had genuinely read in this
session but which is outside the repo's input closure, so neither the Judge
nor any future enforcer could verify it. My session context had leaked into
an artifact that must stand alone.

On FR-908 it found the contradiction I am most annoyed to have missed: I
authorized a gate routing an empty bulletin to END *and* a rule that no
path emits an empty bulletin as success. Those collide. A malformed ranker
response would have laundered into a green no-op — precisely the failure
mode the FR existed to prevent, reintroduced by the FR's own routing.

The lesson is not "the Judge is useful." It is that the two defects were
*structural*, visible only by reading the document as a whole against
itself, and I cannot do that to my own text in the same pass that produces
it.

## Costume check

`raise ... from None` in the SMTP tool looks like sloppy exception
handling. It is the opposite: `SMTPAuthenticationError` carries the
server's response string, which can echo the credential back, so chaining
it would defeat the non-disclosure contract three lines above. The test
asserts `__cause__ is None`. Without that test, the next reader "fixes" it
to `from exc` and silently reopens the leak — a correct line that reads as
a mistake needs a witness, not a comment.

**Seed:** The stale clone and the out-of-closure citation are the same
defect wearing different clothes — I trusted my session's private context
(a fetched tree, a file I had read) as though it were shared, verifiable
record. What other private context am I currently treating as public
ground truth, and what would a mechanical check for "cited artifact is
reachable from the repo under judgement" have caught before the Judge
did?

## Addendum — the 37th collision

The PR merged clean, and then main showed `FR-901-smtp-email-tool.md`
sitting next to `FR-901-skills-layer-in-process-overview.md`. Two
sessions, same repo, same allocation method: `ls feature-requests | tail`,
increment. Deterministic collision. FR-900 and FR-902 too.

Writing the guard was the interesting part. I expected to find my three
and freeze nothing. I found **36 duplicated numbers going back to
FR-082** — including FR-896 and FR-898 from other sessions this same
week. Mine was the 37th instance of a defect that has been present for
the entire life of the repository and was never once noticed, because
no artifact ever compared two filenames.

That reframes it. `one_session_one_repo` names the shared index and the
working tree as collision surfaces and prescribes rituals for both. The
ID namespace is a third surface, and it had no ritual and no guard — so
it degraded silently while the guarded surfaces got louder. **The
unguarded surface is not the one that fails loudly; it is the one that
never fails at all, until you write the check.**

The CAP-251 collision two hours earlier was the same defect with a
different outcome: the registry *had* a uniqueness test, so it failed at
rebase and I fixed it in five minutes. Same hazard, same day, same
session — one caught mechanically, one caught by a human reading a
directory listing after the merge. The delta between those two outcomes
is one test file.

**Seed:** What else in this repo has no comparison test — not "is it
valid?" but "is it the same as its neighbour?" Capability IDs and REQ IDs
have one; FR numbers now do. Diary filenames, changelog fragment names,
CAP names, prompt names, and graph `name:` fields do not. Which of those
would show 36 silent duplicates the first time anyone looked?

## Addendum 2 — the guard measured the wrong thing

The guard merged green and was red on `main` within minutes: FR-899,
`disable-implicit-context-attachment` vs `org-repo-census-azure`.

My first diagnosis was wrong, and I nearly committed it. I assumed a
stale baseline — that I had frozen the grandfathered list from a tree one
merge behind `main` — and started adding "899" to the list. Then a fresh
worktree at the same SHA showed only *one* FR-899 file.

`FR-899-disable-implicit-context-attachment.md` is **untracked**. It is
another live session's work in progress, sitting in the shared checkout,
never committed. There is no collision in the repository at all.

The defect is in the guard: it globbed the filesystem. A test that
asserts a property of *the repository* must ask git what the repository
contains, not ask the directory what happens to be lying in it. Fixed to
`git ls-files`, plus a test that plants an untracked probe and asserts it
is invisible.

Two things worth keeping. First, this is `workspace_is_not_boundary`
wearing a new costume — the Scripture entry warns about nested repos
before destructive operations, and I had filed it under "deletion
safety", so it did not fire when I wrote a *read*. Editor visibility is
not repository membership, in either direction.

Second, and worse: my instinct was to widen the exception list. Adding
"899" would have passed CI, looked reasonable in review, and permanently
encoded a phantom collision — a fix that makes the symptom go away by
teaching the guard to expect the bug. The tell was that I could not
explain *why* FR-899 collided; I only knew *that* the assertion fired. An
exception you cannot justify individually is a confession that you have
not found the cause yet.

**Seed:** How many of this repo's checks read the filesystem where they
mean to read the repository? The gates that inspect `docs/diary/`,
`changelog/unreleased/`, and `capabilities/` all glob. In a workspace
that always holds several sessions' uncommitted work, every one of them
can fail — or pass — for files that are not in the commit under test.
