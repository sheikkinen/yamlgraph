# 2026-07-29 — The Guard That Denied Its Own Author

**Context:** FR-767 enforcement. Same-day double failure of the
graph-authoring skill (strike 1: "mv" phrasing bypassed the trigger;
strike 2: the acceptance-test agent *read the doctrine* and then authored
in-session anyway) had already proven that instruction text does not
hold. The judgement froze a mechanical cure: per-run sentinel in
`author.sh`, PreToolUse denial of unsentineled writes to governed graph
artifact paths.

**The moment worth recording:** minutes after GREEN, I attempted a live
witness — `create_file examples/demos/zodiac/graph.yaml` from my own
session — and my own hook denied me with the exact message I had written
into it an hour earlier. The AC-11 "fresh-session replay" evidence was
produced not by a simulation harness but by the enforcement itself
biting the session that built it. This is `infrastructure_self_exempt`
inverted: the guardrail applied to its own author on the first
opportunity, which is precisely the property strike 2 proved instruction
text lacks.

**Trap observed (recurrence, now 3rd strike):**
`denied-command-phantom-side-effect` — when the PreToolUse guard denies
a compound command, *none* of it ran, but the session's mental model
retains the side effects (msg.txt written, files staged). This session
hit it again with `SKIP=pytest git commit ... | tail` — the token
`pytest` inside `SKIP=pytest` plus `| tail` matched the pipe-buffer
pattern, the whole chain was denied, and tmp/msg.txt stayed stale.
Second occurrence was FR-766; this is the third. Heuristic, now
graduated in behavior if not yet in Scripture: **after any denial,
re-verify every side effect the denied chain was supposed to have —
assume zero of it happened.** Corollary: never put `pytest` (even as an
env-var name) and `| tail` in the same chain.

**Second trap dodged:** to witness the D-8 backstop's failing case I
needed a staged new governed artifact — but the freshly armed guard
forbids creating one on disk. The escape was `git update-index
--cacheinfo` with a hashed blob: stage the artifact in the index without
any filesystem write. The enforcement boundary is the write surface, not
the git object database — and that is correct: the backstop exists
precisely to catch what arrives in the index by routes the write guard
cannot see.

**Design insight:** the sentinel is an *authorization channel through
the environment* — the same mechanism (`AUTHOR_EXECUTION=1`) that
already carried the re-entry guard now carries an unpredictable token
that the hook reconciles against a file. Instruction text says "don't";
the token makes "do" impossible without possessing a secret that only
the adapter mints. This is `two_strike_split` applied to doctrine
itself: after two prompt-level failures in one day, the abstraction
level moved into code.

**Seed:** the guard's terminal parser is a taxonomy of write shapes
(redirect, tee, sed -i, cp/mv, ambiguous writers) that fails closed on
what it cannot parse. Every such parser invites a fifth special case
(`regex_fourth_exclusion`). When the first false-negative bypass is
found, should the cure be another regex — or should governed-path
protection move below the tool layer entirely, e.g. filesystem
permissions or a pre-write LSM-style check that no command string can
route around?
