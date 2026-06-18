# The Ledger Was a Memory System Wearing a Schema

**Date:** 2026-06-17
**Context:** FR-513 shipped, run 10020-BC reviewed, then research into LLM memory
architectures → the plan-ledger-memory north-star and FR-514–518.
**Incident:** A feature ("relationships persist across chapters") turned out to be a
*category*, not a feature. The thing I had been treating as a typed ledger was an
agent memory store missing four of its six defining operations.

## The Trap: Solving the Instance, Not Seeing the Class

FR-513 fixed *emotional* reset — lovers re-met as strangers. It worked: 10020's
review confirmed Hilde & Gunnar persisted Ch3→Ch4. I could have stopped there with
a clean win.

But the run *also* showed two new defects: a chapter that silently zeroed its
relationships (Ch5), and a bond whose type lagged the prose by four chapters
(enmity until Ch6). My first instinct was to file them as two more local FRs —
"add a floor," "force a type update." Two more patches on the same surface.

The reframe came from asking a different question than "what's broken?" — instead,
"**what kind of thing is this, and how do mature versions of it behave?**" The
ledger threads state across context-window boundaries. That is the definition of
agent memory. So I read what memory systems actually do (Generative Agents, MemGPT,
A-MEM, Zep) instead of designing two more patches from first principles.

## The Insight: One Mismatch Explained Both Defects

Every memory system uses **update-delta** semantics — append, invalidate, evolve,
page. Our close uses **regenerate** — the LLM re-emits the whole ledger every
chapter. That single architectural mismatch *generates* both defects:

- Zero-dropout = regenerate lets a forgetful close emit an empty store. A real
  memory accumulates; it cannot spontaneously empty.
- Type-lag = no invalidation operation, so a stale edge persists until the model
  happens to overwrite it. A real memory reconciles contradictions at the boundary
  where they occur.

Two "separate bugs" were one missing abstraction. The patches I almost wrote would
each have treated a symptom; the delta model dissolves both by construction.

## The Heuristic

When a fix for instance X reveals instances Y and Z of *similar shape*, stop
patching and ask what **class** X belongs to. Find the mature, named version of that
class (here: agent memory) and compare operation-by-operation. The gap between "what
my thing does" and "what the named class does" is usually a single missing
abstraction that explains all the instances at once — cheaper to install once than
to patch N times.

The boundary doctrine held throughout: **the LLM authors meaning, the code authors
persistence.** FR-513 enforced that for *encode* (grounding gate). The memory
reframe just extends the same split to the operations the boundary was missing —
reconcile (code closes contradicted edges), forget (code decays on a schedule),
retrieve (code ranks top-K). Same law, more verbs.

## Seed

The grounding gate checks that a citation is *present*, not that the quoted recap
*supports* the claim — a model could fabricate a plausible `recap_citations` string
and pass. Memory systems trust their own writes because the writer is the same agent
that observed; our writer is an LLM summarizing recaps it could misread. Should the
ledger eventually *verify* citations (the quoted recap actually contains the claimed
event) — i.e., is the next boundary after "grounded" not "delta" but "**audited**"?
