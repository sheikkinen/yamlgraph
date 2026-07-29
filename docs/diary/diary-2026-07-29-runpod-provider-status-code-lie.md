# Diary 2026-07-29 — FR-766: The Provider's Type Lie Extends to Status Codes

## Context

Enforced FR-766 (runpod provider, ChatOpenAI + base_url, zero new
deps). Unit suite trivial; the whole day's information content came
from the boundary contacts.

## Trap: the OpenAI-compatible surface that isn't

The endpoint advertises OpenAI compatibility and then returns a bare
HTTP 500 (`internal server error`) for `temperature != 1.0` — a
client-side parameter constraint (kimi-k3 is a reasoning model,
o1/o3-class) surfaced as a server fault. The Scripture's
`schema`/`provider` boundary entries speak of type lies in response
*bodies*; this is the same lie one layer down: **the status code
itself is untyped provider output**. A 500 that means "your request
parameter is unsupported" defeats every retry policy built on the
assumption that 5xx = transient. Our `_bounded()` retries dutifully
hammered an endpoint that could never succeed — 9 requests to learn
what one curl with a varied parameter revealed.

Cure applied: the *witness* pins `_TEMP = 1.0` with the curl evidence
in a comment; the factory learned nothing model-specific (purge list
held). The knowledge lives in the test and the FR, where the next
person hits it, not as speculative code.

## Trap: the denied command's phantom side effect

A pre-command-guard denial killed a `printf > tmp/msg.txt && git
commit` chain — the printf never ran, and the RED commit landed with
the *previous* message still in `msg.txt`. A denied command has NO
side effects, including the ones you'd already mentally checked off.
Fixed with `--amend -F` (local-only). Heuristic: after any hook
denial, re-verify every artifact the denied chain was supposed to
produce before reusing it.

## Observation: the file-size gate as scope enforcement

GREEN was blocked at 454/450 lines. The temptation gradient was
instructive: (a) split the module — out of frozen scope; (b) skip the
hook — infrastructure_self_exempt; (c) trim my own docstring — the
only move that respects both the gate and the judgement. The gate
effectively taxed verbosity in exactly the code I had just added.
Boring enforcement = the judgement was good.

## Interleave note

A foreign commit (`07139c5c`, other session) landed on main mid-GREEN
while my 11 files sat staged. Audit (`git show --stat`) showed a
single-file docs commit — no index sweep this time, but the
one_session_one_repo staged-window exposure was real: my staged work
survived by luck of the other session's `git add` discipline, not by
mechanism.

**Seed:** status codes are provider output crossing the same boundary
as response bodies — should the retry policy in `_bounded()`/executor
treat a *deterministically repeating* 5xx (identical error on N
immediate retries) as non-transient and fail fast with the body
surfaced? That would have turned 9 blind requests into 3 and put the
real error in front of the user a minute earlier.
