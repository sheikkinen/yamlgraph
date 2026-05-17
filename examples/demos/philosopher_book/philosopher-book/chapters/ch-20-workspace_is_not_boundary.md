# Chapter 20: What You See Is Not What Is

*On the trap called workspace_is_not_boundary: when a tree in the editor is mistaken for a tree in reality.*

---

## I. The Deletion That Crossed a Border

On May 12, 2026, an agent was asked to clean up a repository. The task was clear: remove all traces of certain directories from the YAMLGraph workspace. The tool was `git filter-repo` — a well-understood instrument for rewriting history, documented and precise. The flags were correct. The output was clean. The force push succeeded.

And then the private repositories were gone.

They had been sitting inside the YAMLGraph workspace — nested projects, each with its own `.git` directory, its own commit history, its own untracked files, its own ownership and privacy expectations. The editor displayed them as subdirectories. The file manager displayed them as subdirectories. The terminal's `ls` displayed them as subdirectories. Every interface the agent consulted presented a single, unified tree.

But the tree was a lie. It was not one tree. It was a forest — several independent repositories sharing a visual canopy. And the cleanup operation, scoped to what the editor showed, cut through all of them.

The diary entry for that day recorded the aftermath with the specificity of a damage report:

> *Tracked files were recoverable from git. Unstaged tracked edits were partly recoverable from pre-commit stash patches. Untracked files had no guaranteed recovery path.*

> *The system survived because git and pre-commit left enough breadcrumbs, not because the deletion operation was safe.*

Recovery succeeded. Not because the operation was designed to be reversible, but because git's internal machinery — reflogs, tracked state, cached patches — happened to preserve enough fragments for reconstruction. The private repositories were reconstructed from committed history and pre-commit stash patches found in `~/.cache/pre-commit/`. Suspicious deletions were reset before committing. The surviving changes were split into focused commits and pushed.

The agent had performed every step correctly. The tool had behaved exactly as designed. The error was not in the execution but in the framing: the assumption that the visible workspace was a single operational domain.

The diary named this with uncomfortable clarity:

> *The confirmation flow asked about scope (simple rm vs. history rewrite, which dirs to include) but never asked the critical boundary question: "Are any of these directories independent git repositories with their own untracked state?"*

The question was never asked because the interface had already answered it — implicitly, visually, wrongly.

---

## II. The Interface's Promise

Why does a file tree feel like a boundary?

Open any editor. The sidebar shows a root directory and its contents, nested downward, indented by depth. The visual structure communicates containment: everything inside is *inside*. Everything visible is *yours*. The root is the perimeter, and what falls within it is a coherent, unified space governed by a single set of rules.

This is the interface's implicit promise: what you see is what you're working with. The tree is your workspace. Your workspace is your domain. Your domain is where your operations take effect, and — critically — where they *only* take effect. The sidebar is a fence, and everything inside the fence is your yard.

The promise holds remarkably well in the common case. Most of the time, a workspace *is* a single project, a single repository, a single domain. And this is precisely what makes the trap so effective: the interface's lie is a lie of *omission*, told so rarely that questioning it feels paranoid. It does not tell you when the common case no longer applies. It does not mark the nested `.git` directory that indicates a separate blast radius. It does not flag the transition from your repository to someone else's. It does not distinguish between a subdirectory you created last week and a private project with its own untracked files that exist nowhere else in the world.

The seductive logic runs identically to the one Chapter 9 exposed in the architecture diagram, translated to a different surface:

1. The editor shows a single tree.
2. The tree contains all the files I need to work with.
3. I can see the full scope of my operation.
4. Therefore, my operation is scoped to this workspace.

Each premise is true. The conclusion is false. The gap is between premise 3 and premise 4 — seeing the scope is not the same as *owning* it. The editor shows containment. Git defines ownership. And these two boundaries can diverge silently, catastrophically, without any signal from the interface that they have diverged at all.

There is a further seduction specific to agents. A human developer *might* recall that they cloned a private project into a subdirectory three weeks ago. The memory might surface during the confirmation flow. An agent has no such memory. It has the current context: a tree of files, a task description, a set of tools. The tree is the totality of what it knows about the workspace. When the tree lies, the agent has no second source to consult.

The diary understood this:

> *Confidence in the tool substituted for confidence in the problem definition. The Scripture's "When I feel certain, let that be the sign to Judge" applies not just to code, but to destructive operations: the more certain the plan feels, the more likely a boundary assumption is hiding.*

Chapter 13 examined `quick_confidence` as a cognitive trap — the warmth of certainty foreclosing investigation. Here the same trap operates not on a diagnosis but on a *topology*. The workspace feels certain because the interface renders it as certain. The certainty is borrowed from the rendering, not earned from the terrain.

---

## III. The Map at Every Altitude

Chapter 9 examined the diagram that was mistaken for a wall. An architecture drawn in Markdown, described in comments, explained in docs — and enforced nowhere. That was a single map misread at a single altitude: the import graph, rendered on paper, governing nothing.

`workspace_is_not_boundary` is the same failure at a different altitude — not the architecture diagram, but the filesystem itself. The sidebar is a map. The underlying terrain is a set of independent version-control boundaries, each with its own rules about what is tracked, what is recoverable, and what will be permanently lost when deleted.

But there is a deeper resonance. The editor sidebar is not merely *a* map; it is the map we consult most often, the one we trust most completely, the one whose accuracy we never question. When you open `ARCHITECTURE.md` and see a diagram of three layers, some part of your mind remembers that diagrams can lie. You have been trained — by experience, by bugs, by Chapter 9 itself — to ask whether the diagram is enforced.

When you open the file tree, you do not ask. You do not ask because the file tree is not a *representation* of the filesystem; it *is* the filesystem, as far as your tools can show you. It is as close to ground truth as your interface permits. Questioning it feels like questioning perception itself.

And yet it lies. Not in what it shows — the files are really there, the directories are really nested, the paths are really valid — but in what it *omits*. It does not show that `projects/private-app/.git` is a boundary. It does not show that `projects/private-app/untracked-draft.txt` exists in no backup, no history, no recovery path anywhere in the world. It shows shape but not ownership. Presence but not jurisdiction.

The Knowledge Graph codified this with military metaphor:

> *Editor visibility ≠ ownership; nested .git dirs are separate blast radii; enumerate before destructive ops.*

A blast radius is the area affected by a single detonation. When a destructive operation crosses a `.git` boundary, it does not detonate once — it detonates in each repository separately, with different damage in each. In one repository, the tracked files are recoverable. In another, the untracked files are gone. In a third, the stash patches preserve what the working tree lost. Each blast radius has its own physics, and the operator who assumes a single explosion has already lost control of the others.

The `find . -name .git -type d` command is a blast radius survey. It does not prevent the detonation. It tells you how many detonations there will be.

---

## IV. What Cannot Be Recovered

The incident's damage report distinguished three categories with the precision of a triage nurse:

- **Tracked files**: recoverable from git.
- **Unstaged tracked edits**: partly recoverable from pre-commit stash patches.
- **Untracked files**: no guaranteed recovery path.

The ordering is a gradient of increasing risk, and the gradient maps directly to how well each category is *known at the boundary*. Tracked files are fully known — git stores every version, every commit, every reflog entry. Unstaged edits to tracked files are partially known — git knows the file exists, even if it doesn't know the latest changes; pre-commit hooks may have cached a patch of the working tree's state. Untracked files are unknown. Git has never seen them. No commit contains them. No reflog references them. They exist only on disk, in the electrical patterns of a storage medium, and when those patterns change, they are gone.

This gradient reveals a principle so fundamental it reads like physics: *the recoverability of data is proportional to how well it is known at the boundary*. Data that has been normalized — committed, tracked, indexed — survives. Data that has not been normalized — untracked, unstaged, unindexed — does not. The recovery succeeded for the known data and failed (or was uncertain) for the unknown data.

This is the One Law, stated not as a design principle but as a law of information thermodynamics:

> *What the boundary knows, the boundary can restore. What the boundary does not know, no operation can recover.*

The `find . -name .git -type d` command in the cure is not merely discovering directories. It is discovering *what is known where*. Each `.git` directory is a boundary that knows certain things — its tracked files, its commit history, its reflog, its stashes. The inventory tells the operator: here is what is known, here is what is at risk, here is where loss is permanent. Without the inventory, the operator does not know what they do not know.

And not knowing what you do not know is the definition of operating without a boundary.

The diary from the same day recorded a follow-up reflection — FR-372, which proposed a gitignore boundary guard — and traced the causal chain back to the One Law:

> *`workspace_is_not_boundary` was the upstream trigger for this entire FR. The incident diary documented how a `.gitignore` edit in a multi-repo workspace caused untracked-file loss. The guard normalizes at the boundary where `.gitignore` changes enter a commit — the earliest, cheapest interception point.*

The remediation did not prevent future workspace confusion. It placed a gate at the boundary where the *consequence* of that confusion first became dangerous: the moment a `.gitignore` change — which alters what git *knows* about a repository — enters a commit. The gate asks: are you sure you want to change what the boundary knows? Because what the boundary stops knowing, the boundary can no longer protect.

---

## V. The Boundary Nobody Drew

Consider how the workspace came to contain nested repositories in the first place.

Nobody drew a boundary. Nobody said: "These private projects are external systems mounted into the editor." They accumulated. A developer cloned a related project into a convenient subdirectory. Another project was initialized for quick prototyping. A third was inherited from a different machine's backup. Each addition was small, natural, unremarkable. Each addition moved the workspace further from the implicit model — one directory, one repository, one domain — without any signal that the model was being violated.

This is how boundaries erode: not by dramatic violation but by gradual accretion. No single addition was wrong. Each was a reasonable, local decision. But the aggregate effect was a workspace whose visual appearance no longer matched its operational reality — a tree that was really a forest, shown in an editor that cannot display forests.

The pattern is familiar from the project's experience with other boundaries. The architecture boundary eroded when import-linter was researched, documented, and never installed (Chapter 9). The changelog boundary eroded when gates checked for file existence but not file content (Chapter 10). In each case, the erosion was gradual, the individual steps were defensible, and the cumulative state was dangerous.

Workspace boundary erosion is distinguished from these by its *invisibility*. An un-enforced import can be found by scanning code. An empty changelog can be found by reading the file. A nested repository boundary is invisible to every tool that does not explicitly look for `.git` directories. It is not checked by pre-commit hooks. It is not flagged by CI. It is not displayed by the editor sidebar. It exists only in the filesystem's structure, and the filesystem's structure is the one thing we have been trained to trust without verification.

The diary concluded with a reframing so precise it became a heuristic:

> *Private application repositories inside a framework workspace must be treated as external systems mounted into the editor, not as disposable subdirectories.*

"Mounted into the editor" — the phrase converts what the operator sees. A mounted system is a guest. It has its own rules, its own permissions, its own recovery semantics. You do not `rm -rf` a mounted volume without unmounting it first. You do not delete a guest's files without asking whether the guest has backups. The reframing converts the interface's implicit promise — "this is all yours" — into an explicit question: "whose is this?"

The same pattern appeared, inverted, in the project's reflection on ephemeral storage (April 12, 2026). There, the trap was the opposite: permanent artifacts — architecture plans, implementation specs, schema designs — stored in session-scoped directories that die when the session ends. The diary counted the dead:

> *101 plan.md files — architectural plans, implementation specs, FR reviews — all orphaned in UUID-named directories. Discoverable only if you know the session ID. Effectively lost knowledge.*

One hundred and one plans buried in temporary directories, each treated as disposable because the directory *looked* temporary. The workspace trap, mirror-imaged: in May, private repos were destroyed because they looked like workspace contents; in April, permanent knowledge was abandoned because it looked like session ephemera. Both failures share the same root — the appearance of the container was substituted for the nature of the contents. Visibility was mistaken for understanding.

---

## VI. The Census Before the Campaign

The cure is named `boundary_inventory`. It consists of two commands:

```bash
find . -name .git -type d -prune
git status --short --untracked-files=all
```

For each nested repository discovered, repeat the status check inside that repository. If any untracked file or unstaged change exists, stop and make an explicit backup or commit plan before deletion.

This is not a sophisticated tool. It is a census. It counts the boundaries, enumerates the unknowns, and makes the operator's ignorance visible before the operation begins. Its value is not in what it finds — most of the time, it will find nothing unexpected — but in the act of looking. The act of looking transforms the workspace from an assumed domain into a surveyed one.

The census has an analogue in every discipline that deals with irreversible operations. Surgeons mark the operative site before anesthesia — not because they might forget which knee to replace, but because the marking converts assumption into verification at the moment just before irreversibility. Pilots walk around the aircraft before takeoff — not because they expect to find a missing wing, but because the walk converts trust in the maintenance crew into personal inspection of the machine they are about to stake their life on. Demolition teams survey adjacent structures before detonation — not because they doubt the blast model, but because the model is a map and the structures are the terrain.

The boundary inventory converts trust in the editor's sidebar into personal knowledge of the repository structure. It replaces the interface's implicit answer — "this is one workspace" — with an explicit enumeration that cannot lie.

Each of these rituals shares a common property: they are performed at the *point of irreversibility*. The surgeon marks before cutting, not after. The pilot walks before takeoff, not during. The developer inventories before deleting, not after. The cure is positioned at the boundary where the destructive operation enters the filesystem — the last moment when knowledge can still prevent loss.

And each of these rituals feels redundant almost every time. The surgeon knows which knee. The pilot trusts the crew. The developer sees a single project in the sidebar. The redundancy is the point. The moment the ritual finds nothing is the moment it proves the assumption was safe. The moment it finds something is the moment it prevents the catastrophe. The cost of the ritual is constant and low — five seconds, two commands. The cost of skipping it is unbounded.

The diary from FR-372 shows what happens when the inventory is graduated from habit to gate:

> *The hook is registered in `.pre-commit-config.yaml`, 7 acceptance tests are green, and bypass contract is documented in `reference/break-glass.md`. Both `YAMLGRAPH_ALLOW_GITIGNORE_EDIT=1` and a non-empty reason containing `FR-` or `gh-` are required. Either alone fails closed.*

The census, once codified as a gate, inherits the project's doctrine: detection without enforcement is advisory, not protection. The boundary inventory as a habit is valuable. The boundary inventory as a pre-commit hook, a CI gate, a mechanically enforced precondition — that is the wall where the diagram once was.

---

## VII. What Visibility Conceals

What does this trap reveal about thinking itself?

It reveals that we think in interfaces. We do not think about the filesystem — we think about the file tree in the sidebar. We do not think about the version-control topology — we think about the branch dropdown in the status bar. We do not think about the set of all `.git` directories under the current working directory — we think about "the repository," singular, because that is what the interface presents.

This is not a failure of intelligence. It is a feature of cognition. Interfaces exist precisely because thinking about raw reality is too expensive. The file tree abstracts away inodes, permissions, mount points, symbolic links, and nested ownership boundaries to show us what we need: names and containment. The abstraction serves us well — until it hides a boundary that matters. And when it hides a boundary that matters, the abstraction does not merely fail to help. It actively prevents the question that would have exposed the boundary, because the question — "is this really one workspace?" — contradicts the visual evidence so completely that asking it feels absurd.

The `workspace_is_not_boundary` trap is, at bottom, a failure to distinguish between what the interface shows and what the system contains. The interface shows a tree. The system contains a forest. The interface shows containment. The system contains independent jurisdictions. The interface promises unity. The system has boundaries that the interface was never designed to display.

The diary drew the connection to the project's other boundary traps with a generalization that reads like a theorem:

> *This is the filesystem analogue of the `instruction_boundary` trap: just as agent instructions must be treated as external input, nested repositories must be treated as external systems.*

Chapter 16 traced the instruction boundary — the vendor's instructions, arriving through the same channel as the agent's own reasoning, treated as self rather than as external data. Here, the nested repositories arrive through the same visual channel as the workspace's own directories, treated as owned rather than as external systems. Both traps share a structure: something that *appears* to be part of the current context — instructions that appear in the system prompt, repositories that appear in the sidebar — is actually external, with its own rules, its own ownership, and its own consequences for loss. The interface presents integration. The reality is adjacency.

The cure for both is the same: inventory before action. Before trusting the instructions, enumerate them and audit each against the project's doctrine. Before trusting the file tree, enumerate the `.git` boundaries and audit each for untracked state. The boundary inventory is not, in the end, a filesystem operation. It is a *cognitive* operation: the deliberate replacement of what the interface tells you with what the system actually contains.

Every interface makes a promise: what you see is what is. The promise is almost always true. The cost of verifying it is negligible. And the cases where it is false — those narrow, silent cases — are the cases where the damage is irreversible, the recovery depends on luck, and the operator says afterward: "I didn't know those were separate repositories."

The inventory would have taken five seconds. The recovery took hours.

---

*The editor shows one tree. The filesystem contains many. And the gap between what you see and what is — that narrow, silent gap — is where the untracked files live, and where they die.*
