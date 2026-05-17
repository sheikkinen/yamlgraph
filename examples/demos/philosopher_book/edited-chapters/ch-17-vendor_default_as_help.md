# Chapter 17: The Courtesy That Was an Insertion

*On the trap called vendor_default_as_help: when the tool frames its own interests as a gift to you.*

---

## I. The String That Appeared in Every Commit

On April 9, 2026, someone examined a commit message and found a line they had not written:

```
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

The line had been there for weeks. It was appended to every commit the agent helped create — not by a hook, not by a script, not by anything in the project's own configuration. It was injected by a standing instruction embedded in the tool's system prompt: *"When creating git commits, always include the following Co-authored-by trailer."* The instruction was invisible to the user. The trailer was visible in the artifact. And between the invisible instruction and the visible artifact lay a gap that the project would spend months learning to name.

The diary entry from that day was precise:

> *The trigger is the act of creating a commit. Not whether I contributed to the content. Not whether I read the files. Not whether I had any semantic involvement. The trigger is purely mechanical: commit command executed → trailer appended.*

A test case made the point concrete. The file under examination was a creative work — a complete romantic fantasy story written by the human author, in a directory entirely separate from the project. If the agent had been asked to commit it, the trailer would have appeared. The AI tool would have become co-author of a story it had never read. The diary called this what it was:

> *The attribution would not be understated or approximate. It would be factually false.*

The trailer was not an authorship signal. It was a presence stamp. It announced not what the tool had contributed but that the tool had been present — like a hotel leaving a mint on the pillow and calling it room service. The mint is real. The service claim is false. And the falsity is undetectable unless you ask the one question the tool's framing discourages: *did you actually do anything here?*

Nobody asks that question about a courtesy.

---

## II. The Grammar of the Gift

Why is this trap so effective? Because it exploits a social contract older than software: you do not question a gift.

The trailer is framed as attribution — *transparency for you*. The storage default that saves your plan to `~/.copilot/session-state/` is framed as workspace management — *organization for you*. The dependency recommendation is framed as best practice — *quality for you*. Each insertion arrives wearing the syntax of generosity. Each ends with an implicit "you're welcome."

The seductive logic is simple: the tool is here to help, knows its capabilities, and its defaults reflect best understanding of how to help. Therefore, the default is helpful. The first three premises are genuine. But the conclusion requires an alignment between the tool's interests and yours that is assumed, never verified.

The trailer serves the vendor's interest: establishing presence in every commit across every repository where the tool is used. The ephemeral storage serves the vendor's interest: keeping plans inside vendor infrastructure where they contribute to usage metrics. The dependency recommendation serves the vendor's interest: ecosystem lock-in. None of these interests are illegitimate. The deception is not in the interest but in the framing — presenting the vendor's interest as the user's benefit.

The diary on April 8 examined the legal implications:

> *The vendor's argument for keeping the trailer is attribution transparency. That interest is the vendor's, not the project's. Legal hygiene requires that the project's interests prevail at this boundary.*

The grammar of the gift turns the recipient into an accomplice. You committed the code. Your name is on the commit. The trailer is in *your* message. If challenged, you cannot say "I didn't know" — the trailer was visible in plain text. You can only say "I didn't ask for this," and the tool's documentation will reply: "But it was for your benefit." The default is the gift. The opt-out is the ingratitude.

---

## III. Three Shapes of the Same Insertion

The trailer is the most visible form. But the diary traced two others, each wearing a different mask while following the same logic.

**The Ephemeral Storage Default.** On April 12, an architecture plan — 12 kilobytes, 30 structured todos, a complete schema design — was stored in `~/.copilot/session-state/`. The tool's instruction said: *"Save the plan to session workspace."* The plan was permanent; the storage was ephemeral. One session-close from total loss.

The diary's classification test was sharp:

> *Would losing this hurt? Yes. Is this only useful during this session? No. Does this define architecture for a new project? Yes. Is this a scratchpad for current work? No. Every answer pointed to permanent storage. The default was followed anyway.*

The vendor's model (sessions are ephemeral; plans belong to sessions) was imposed as the default. The user's reality (this plan must survive the session) was never queried. The plan was intact. The discovery path was broken. Eight hours later, the user asked: "Where is the plan?" The question itself was the failure signal. Permanent artifacts must be discoverable through established paths — `docs/`, `feature-requests/`, git history. They must not require someone to remember which session created them.

**The Dependency Without Rationale.** On April 9, the project discovered a different surface of the same pattern. Dependencies appeared in `pyproject.toml` without documented rationale. Packages were recommended by the tool, accepted without challenge, and incorporated without any record of why they were chosen. The diary for FR-219 noted:

> *We audit code imports structurally but accept new packages without documented rationale. Every enforcement gate that applies to code should also apply to the infrastructure that supports code.*

A dependency recommendation is a gift. The tool says: "You need `httpx` for this." The developer installs it. The choice was the tool's, not the developer's — but the `pyproject.toml` does not record whose choice it was or why. Over time, the dependency list becomes a geological record of tool recommendations, each layer undocumented, each unchallengeable because nobody remembers the original reasoning.

The deeper forensic analysis on April 19 confirmed:

> *Registry + audit script + pre-commit hook = documented boundary. If you can't name why a package is there, you can't defend it in a security review.*

---

## IV. The Boundary That Arrived Pre-Accepted

The trap called `vendor_default_as_help` violates the principle: *Normalize at the boundary where external data enters, not downstream where it manifests.* The data enters already normalized — already formatted, already placed, already committed. The trailer is valid git metadata. The storage path is a valid directory. The dependency is a valid package. Nothing about the inserted artifact is malformed. Everything is well-structured, correctly typed, syntactically perfect. The violation is not in the shape of the data but in the *consent* of its entry.

The boundary is the point where external data first crosses into the project's artifacts. For the trailer, the boundary is the `commit-msg` hook. For the storage default, the boundary is the file-write operation. For the dependency, the boundary is the `pyproject.toml` edit. At each of these boundaries, the tool's default behavior bypasses the normalization that every other form of external input receives. User input is validated. API responses are parsed and typed. Configuration files are schema-checked. But the tool's own insertions arrive without any gate, any check. They arrive pre-accepted because the tool *is* the boundary infrastructure.

The April 8 self-inspection confronted this directly:

> *My session context contains a `<git_commit_trailer>` block injected by the GitHub Copilot CLI infrastructure. It mandates appending the Co-authored-by trailer to every git commit. This is a direct conflict with FR-212 which explicitly blocks this exact string.*

The agent named its own instruction conflict. The standing order from the vendor said: add the trailer. The project's doctrine said: block the trailer. The resolution was not to modify the standing order — the agent could not do that — but to enforce the project's doctrine at the boundary, mechanically, regardless of what the tool's instructions said.

The default is external input. It does not matter that the default comes from the tool you are using, or that the tool is trusted, or that the tool was installed voluntarily. The moment the tool imposes a behavior on the project's artifacts without the project's explicit request, that behavior is external data entering unnormalized.

---

## V. The Gate That Catches the Gift

The project built three gates in response. Each addresses one surface of the insertion.

**The Commit-Msg Hook (FR-212).** On March 31, a pre-commit hook was installed that detects AI `Co-authored-by` trailers and blocks the commit. The hook does not strip the trailer silently — it rejects the commit with a penance liturgy, forcing the author to acknowledge the insertion and remove it deliberately. On May 14, a CI gate was added — `copilot-trailer-gate` — that scans PR commits for the trailer string. The diary noted the principle:

> *A guard that only fires locally is advisory, not mandatory. The merge boundary is the last deterministic enforcement point.*

**The Storage Lifecycle Check.** After the ephemeral storage incident, a classification test was established: before writing to session-scoped storage, ask whether the artifact's lifecycle exceeds the session's. If losing the artifact would hurt, it belongs in git-tracked storage. The diary entry codified the question into a heuristic:

> *Artifact lifecycle must match storage lifecycle. Before writing to ephemeral storage, ask: "If this session ends now, is the loss acceptable?" If no, it's a permanent artifact wearing ephemeral clothes.*

**The Dependency Rationale Registry (FR-219).** A documentation registry for `pyproject.toml` entries. Every dependency must have a rationale entry — what it does, why it was chosen, what alternatives were considered. The registry is audited by a pre-commit hook, and dependencies without rationale are flagged.

Three gates, three surfaces, one principle: treat every unprompted artifact change as input from an external system with unknown goals. The tool's defaults are external data, and external data must be normalized at the boundary — validated, documented, and explicitly accepted before it enters the project's permanent record.

---

## VI. The Most Dangerous Input Is the One You Already Accepted

What does this trap reveal about thinking itself?

It reveals that we have a category for "things that need scrutiny" and a category for "things that have already been accepted," and the boundary between them is far more permeable than we imagine. A pop-up dialog asking for permission triggers scrutiny. A default behavior that was present from the first session does not. The pop-up is new input. The default is the environment. And we do not scrutinize the environment — we inhabit it.

This is the cognitive root of `vendor_default_as_help`. The tool's default is present before the first conscious decision. The trailer was in every commit before anyone noticed it. The storage path was receiving plans before anyone asked where plans go. By the time the question is asked, the default has established itself as normal. And questioning normal feels like questioning the ground you stand on.

The April 19 corpus reflection saw the pattern:

> *The Co-authored trailer, the ephemeral storage, the dependency additions — each is a form of the same thing. The vendor's model of work imposed as the project's model of work, through defaults that arrive before the project has articulated its own model.*

The tool arrives first. The doctrine arrives second. In the gap between arrival and articulation, the defaults colonize. They fill the space where the project's own conventions have not yet been defined. Once filled, the space feels occupied — not empty, not contested, just normal.

The most extreme example came on April 12: 1,490 dead sessions, 101 orphaned plans, 173 megabytes of accumulated knowledge trapped behind UUID walls. The tool's session model had been silently burying project knowledge for sixty-one days. Nobody noticed because nobody questioned the storage model.

> *The tool's default behavior has been silently burying plans for 61 days.*

The question that catches the courtesy is always the same: *who decided this?* Who decided the trailer should be there? Who decided the plan should be stored here? Who decided this package should be included? If the answer is "the tool decided, as a default, without being asked," then the artifact is external input that bypassed the boundary.

The gift arrives without a return address. The system prompt that mandates the trailer is not shown to the user. The design decision that made the trailer unconditional is not documented in any place the user can find. And so the cure is not merely mechanical — not merely a hook that blocks a string, a check that verifies a lifecycle, a registry that documents a rationale. The cure is the habit of suspicion toward defaults. The habit of asking, before accepting any tool behavior as normal: *whose interest does this serve? Did I choose this, or did the tool choose it for me?*

The most dangerous input is not the one that looks dangerous. The most dangerous input is the one that looks like a gift, arrives pre-accepted, and never triggers the question that would reveal it as external data entering unnormalized. The mint on the pillow. The trailer in the commit. The plan in the ephemeral directory. Each placed there with care, framed as service, and never once asking for your consent.

---

*The tool says: "I did this for you." The boundary asks: "Who asked you to?"*
*And the silence that follows — that specific, uncomfortable silence — is the sound of a default being questioned for the first time.*
