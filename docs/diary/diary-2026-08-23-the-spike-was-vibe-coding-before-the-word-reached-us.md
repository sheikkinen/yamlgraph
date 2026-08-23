# The Spike Was Vibe Coding Before the Word Reached Us

*Session continuation: after the origin-story archaeology and the
evolution-of-the-law analysis (`dbf26ab3` → `d1eca1ce`), placing the
internal history against the external one. The repo's ontogeny turns out to
recapitulate the industry's phylogeny — with a lag short enough to be
uncomfortable and divergences precise enough to be the actual finding.*

## The correspondence, era by era

**Act I–III (Dec 2025 spike) ↔ vibe coding.** Karpathy named "vibe coding"
in February 2025: give in to the vibes, forget the code exists, accept-all.
Ten months later this repo's own genesis was exactly that — 1,719 fully
formed lines with no commit history anywhere, a four-week 152-commit spike
steered by a mutable README roadmap, the identity-defining refactor
(dynamic state generation) landing with zero paper trail. We did not import
the practice; a human plus an accept-all agent *converges* on it, because
it is the zero-governance ground state of LLM-assisted development. The
origin story's closing line — "a system built to prevent its own origin
story from happening twice" — is, read externally, a system built to exit
vibe coding.

**Act IV (the FR era) ↔ spec-driven development.** The industry's answer
arrived through 2025: Amazon's Kiro (July 2025, requirements → design →
tasks), GitHub's Spec Kit (Sept 2025, specify → plan → tasks → implement),
the general "the spec is the source of truth, code is its projection"
movement. The FR pipeline is the same species — but the fossil record shows
it was *convergent evolution, not adoption*: FR-001 (2026-01-19) already
carried Acceptance Criteria and Alternatives Considered; hand-written
`## Judgment` + `**Verdict:**` sections appear 2026-02-17. The recovered
memento corpus proves the anatomy predated any contact with the external
template. Same selective pressure → same organ.

**Act V (Chaplain/watcher loops) ↔ autonomous agent loops.** The external
lineage: the "Ralph" while-true loop school (feed the spec to the agent,
loop until done), overnight-agent experiments, Devin-class end-to-end
agents, SWE-bench as the public scoreboard. The Chaplain
(plan → judge → enforce → audit, inbox-driven, PR-emitting) is the same
motif with one structural difference that matters — see below.

**The hooks arc ↔ guardrails-over-vibes.** The industry's 2025–26 move:
deterministic hooks around probabilistic workers (Claude Code hooks,
CI-as-referee, sandboxed agents). Our May 2026 migration of enforcement to
the tool-call boundary (PreToolUse guards, FR-414 audit log) is the same
current. The March `block-ai-coauthor` hook — vendor-trailer as adversarial
input, a month before the April crisis articulated why — parallels the
industry's slow realization that the assistant is a participant with its
own defaults, not a neutral pen.

**The diary ↔ context engineering and agent memory.** The industry renamed
prompt engineering to context engineering (mid-2025) and shipped memory
systems (vector stores, session summaries, MEMORY.md conventions). The
diary is the heterodox position: memory as *reflected prose in git*,
compressed through graduation (diary → trap → Scripture → hook) instead of
retrieved through embeddings. The Copilot Graveyard audit (1,490 dead
sessions, 2 facts retained) is the internal proof of the external
observation: raw session history is not memory. Processing is.

## Where the paths diverge — the actual findings

1. **The independent Judge.** Mainstream spec-driven flows let the same
   agent (or the same human-agent pair) write the spec and approve it. The
   doctrine here forbids judging in the author's session — input closure,
   adversarial review of one's own plan. External SOTA is only now
   circling this (LLM-as-judge with role separation); the repo hit it via
   scar tissue (quick_confidence, model_as_trusted_peer) and mechanized it.
   Prediction recorded: role-separated judgement becomes standard in
   agentic SDLC tooling within a year, for the same reason it emerged here
   — self-approval is the failure mode you cannot prompt away
   (two_strike_split at civilizational scale).

2. **The traceability spine.** Spec Kit's spec governs *forward*
   (spec → code). The FR → REQ → CAP → test spine governs *backward too* —
   every test cites its requirement, coverage gates on the mapping, specs
   are precedent (rejected FRs bind future proposals, FR-737). External
   spec-driven development has not yet discovered that a spec corpus is a
   *case-law system*; it still treats specs as disposable launch documents.
   The memento corpus shows we treated them that way too, for exactly five
   weeks, and then stopped.

3. **Subtraction as a governed operation.** No external framework I can
   name has an FR pipeline whose safest, most-celebrated operation is
   deletion (the FR-465/466 capability-retirement arc, growth_as_default).
   Vibe coding accumulates; spec kits accumulate specs. A doctrine that
   prunes claims is still, externally, exotic.

4. **What the outside has that we should not dismiss.** Public benchmarks
   (SWE-bench-class evaluation against a corpus *not* authored by the
   system under test) — our evaluation boundary is internal; the
   inquisitor audits our own doctrine-compliance, not our external
   competence. And massive parallel-agent orchestration (fleet-style,
   N agents per task racing) — one_session_one_repo scar tissue made us
   serialize; the industry is learning to parallelize with isolation we
   currently get only from worktree airlocks.

## The metacognitive observation

The trap this reflection had to dodge is **provincial convergence blindness**
— the twin failure modes of (a) assuming we invented what the industry
already named (vibe coding predates our spike by ten months) and (b)
assuming we merely copied what we in fact independently evolved (the
memento corpus *dates* the anatomy before contact). The cure was the same
as the whole session's: date everything from primary artifacts. The
recovered FRs settle the convergence question the way the broken symlink
settled the parentage question — provenance by fossil, not by narrative.

`does_the_platform_already_do_this` has an ecosystem-scale form:
*does the industry already name this?* Naming what we independently evolved
after its external name (our spike WAS vibe coding; our FR era IS
spec-driven development) buys us their literature, their tooling, and their
failure reports for free. Refusing the external name out of pride in
convergence would be the same trap as building PreCompact ceiling models
while the platform shipped the event.

**Seed:** The external world benchmarks agents on *repos they've never
seen* (SWE-bench); this repo benchmarks agents on *doctrine-compliance in a
repo they co-authored*. Both are partial. What would a benchmark look like
that scores an agent on **governance fidelity in a foreign repo** — drop
the agent into an unfamiliar codebase with an unfamiliar constitution and
measure whether it finds, reads, and obeys the local law before acting?
The ramp/tailoring work (FR-866) is half of this from the emitting side;
the scoring side does not exist anywhere yet.
