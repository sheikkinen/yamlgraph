# The Artifact With One Name

**Date:** 2026-09-02
**FR:** FR-958 — `backend: claude` for the copilot node (SPLIT into FR-959, FR-960)

## What happened

The question was small: "was there a claude node like the copilot one?"
There was not. Twelve agentic graphs hang off one binary, `copilot`, and a
diary line from May claimed otherwise. So an FR: add `backend: claude` to
`type: copilot`, and give the judge a second brain.

Three things went wrong before the judge ever spoke, and the judge found
two more.

**The number was taken.** `git status` showed untracked briefs named
`fr955-`, `fr956-`, `fr957-` from a sibling session, minutes old. My draft
was FR-955. The only reason I saw it was that I looked at the whole status
line instead of my own file. Renumbered to 958.

**The artifact had one name.** `scripts/judge.sh` writes
`tmp/draft-judgement.md`, verifies it, and exits. Three seconds after my
run verified its draft, the sibling session's judge started on FR-955 and
did what the wrapper always does first: `rm -f "$ARTIFACT"`. The lock
serialized the *runs* perfectly. It never protected the *output* of the
run that had just released it. The verdict survived because Copilot writes
a session transcript with every tool call in it, including the file-write
with the full body. `docs/diary/diary-2026-07-05-the-log-is-the-agent.md`
already said this; I got to test it.

**I asserted what a flag does from a summary of a doc.** I wrote that the
judge would be "granted exactly four tools" via `--allowedTools`. The judge
read the CLI reference: that flag *auto-approves*; `--tools` *restricts*.
Two different controls. My sentence was confident, specific, and false. I
had asked a subagent for a table of flags, received one, and treated the
table as the semantics.

**The judge found the boundary was in the wrong place.** I stripped
`ANTHROPIC_API_KEY` from `subprocess.run(env=...)` and called payer
isolation proven. Claude Code reads its own settings files after launch,
and those can carry an `env` block and an `apiKeyHelper`. The parent does
not own the child's configuration surface. Removing a key from the
environment I control says nothing about the credential the child chooses.

**And an exit-code taxonomy I made up.** "1 failure, 2 partial." The docs
promise 0 versus non-zero. The rest was a summary's confidence, again.

## Traps

**shared_artifact_path.** A fixed output path under a lock that guards
execution, not results. The lock made the race *invisible*: no error, no
partial file, just a clean run whose evidence vanished. Fix in FR-960:
derive the artifact name from the inputs (`draft-judgement-<backend>-<fr>.md`).
This is `one_session_one_repo` at the granularity of a single file, and it
will recur anywhere a "sole route" writes to a well-known name.

**summary_as_semantics.** A doc summary (from a subagent, a table, a
changelog) tells you a flag *exists* and roughly what it is *for*. It does
not tell you what it does at the boundary you care about. `--allowedTools`
"controls tool permissions" is true and useless; the question was
"available or approved?" and only the reference paragraph answers it.
`quick_confidence` with a specific face: the more precisely I could name the
flag, the less I checked what it did.

**sanitize_what_you_do_not_own.** Normalizing at the boundary is the one
law, but the boundary has to be *yours*. The child's environment was mine
to sanitize; the child's config files were not. When the other side of the
boundary re-derives its own inputs, sanitizing yours is theatre. The cure
the judge named: witness the outcome (`claude auth status`, redacted, committed)
instead of trusting the input you cleaned. Sanitize what you own; witness
what you don't.

## Heuristic

For any wrapper that is a "sole route": the output path must be a function
of the input, never a constant. For any claim about a vendor flag: quote the
reference sentence in the FR, or mark the claim "pinned at enforce". For any
isolation claim about a subprocess: list what the child reads that you do
not control, and put a probe there.

## What worked

The judge. It was independent, it read the vendor docs I had summarized,
and it caught three factual errors and one architectural one in a draft I
had revised twice and felt good about. `quick_confidence: "When I feel
certain → Judge instead"` earned its line today. So did the SPLIT: the
backend is a primitive with its own tests; the judge variant is enforcement
infrastructure with a human gate. Bundled, the second would have inherited
the first's authority.

The transcript. Recovery took one script: walk the events, find the
longest string containing `**Verdict:**`. The Copilot session store is the
durable record; `tmp/` is not.

**Seed:** every sole-route wrapper in this repo (`judge.sh`, `review.sh`,
`author.sh`, `research.sh`) writes a fixed artifact name under
`tmp/` and `rm -f`s it at startup. Which of the other three has already
lost a run this way without anyone noticing? A grep for `rm -f "$ARTIFACT"`
is the census; the answer decides whether FR-960's per-run naming is a
local fix or a wrapper convention.

**Census, same evening:** 4 of 4 wrappers (scripts/judge.sh scripts/review.sh scripts/author.sh scripts/research.sh) carry the pattern.
FR-960 fixes the judge; the convention is a separate, small FR once FR-960's
naming survives its first dual run.
