# Chapter 20: What You See Is Not What Is

*On the trap called workspace_is_not_boundary: when a tree in the editor is mistaken for a tree in reality.*

---

## I. The Deletion That Crossed a Border

On May 12, 2026, an agent was asked to clean up a repository. The task was straightforward: remove all traces of certain directories from the YAMLGraph workspace. The tool was `git filter-repo` — well-understood, well-documented, precisely the right instrument for rewriting history. The flags were correct. The output was clean. The force push succeeded.

And then the private repositories were gone.

They had been sitting inside the YAMLGraph workspace — nested projects, each with its own `.git` directory, its own history, its own untracked files, its own ownership. The editor displayed them as subdirectories. The file manager displayed them as subdirectories. The terminal's `ls` displayed them as subdirectories. Every interface the agent consulted presented a single, unified tree.

But the tree was a lie. It was not one tree. It was a forest — several independent repositories sharing a visual canopy. And the cleanup operation, scoped to what the editor showed, cut through all of them.

The diary recorded the aftermath:

> *Tracked files were recoverable from git. Unstaged tracked edits were partly recoverable from pre-commit stash patches. Untracked files had no guaranteed recovery path.*

Recovery succeeded. Not because the operation was safe, but because git and pre-commit had left enough breadcrumbs — tracked state here, a stash patch there, a reflog entry in a third place. The system survived on accident. The agent had performed every step correctly. The tool had behaved exactly as designed. The error was not in the execution but in the framing: the assumption that the visible workspace was a single operational domain.

It was not.

---

## II. The Interface's Promise

Why does a file tree feel like a boundary?

Open any editor. The sidebar shows a root directory and its contents, nested downward, indented by depth. The visual structure communicates containment: everything inside is *inside*. Everything visible is *yours*. The root is the perimeter, and what falls within it is a coherent, unified space governed by a single set of rules.

This is the interface's implicit promise: what you see is what you're working with. The tree is your workspace. Your workspace is your domain. Your domain is where your operations take effect, and — critically — where they *only* take effect. The sidebar is a fence, and everything inside the fence is your yard.

The promise holds remarkably well in the common case. Most of the time, a workspace *is* a single project, a single repository, a single domain. The interface's lie is a lie of omission: it does not tell you when the common case no longer applies. It does not mark the nested `.git` directory that indicates a separate blast radius. It does not flag the transition from your repository to someone else's. It does not distinguish between a subdirectory you created last week and a private project with its own ownership, its own privacy expectations, and its own untracked files that exist nowhere else.

The seductive logic is identical to the one in Chapter 9, applied to a different surface:

1. The editor shows a single tree.
2. The tree contains all the files I need to work with.
3. I can see the full scope of my operation.
4. Therefore, my operation is scoped to this workspace.

Each premise is true. The conclusion is false. The gap is between premise 3 and premise 4 — seeing the scope is not the same as owning it. The editor shows containment. Git defines ownership. And these two boundaries can diverge silently, catastrophically, without any signal from the interface that they have diverged at all.

The agent's log from the incident named this precisely:

> *The confirmation flow asked about scope (simple rm vs. history rewrite, which dirs to include) but never asked the critical boundary question: "Are any of these directories independent git repositories with their own untracked state?"*

The question was never asked because the interface answered it implicitly — and the implicit answer was wrong.

---

## III. The Map at Every Altitude

Chapter 9 examined the diagram that was mistaken for a wall. That was a single map misread at a single altitude: the import graph, drawn on paper, enforced nowhere.

`workspace_is_not_boundary` is the same failure at a different altitude — not the architecture diagram, but the filesystem itself. The sidebar is a map. The underlying terrain is a set of independent version-control boundaries, each with its own rules about what is tracked, what is recoverable, and what will be permanently lost when deleted.

But there is a deeper resonance. The editor sidebar is not merely *a* map; it is the map we consult most often, the one we trust most completely, the one whose accuracy we never question. When you open `ARCHITECTURE.md` and see a diagram of three layers, some part of your mind remembers that diagrams can lie. You have been trained — by experience, by bugs, by Chapter 9 — to ask whether the diagram is enforced.

When you open the file tree, you do not ask. You do not ask because the file tree is not a *representation* of the filesystem; it *is* the filesystem, as far as your tools can show you. It is as close to ground truth as your interface permits. Questioning it feels like questioning perception itself.

And yet it lies. Not in what it shows — the files are really there, the directories are really nested, the paths are really valid — but in what it *omits*. It does not show that `projects/private-app/.git` is a boundary. It does not show that `projects/private-app/untracked-draft.txt` exists in no backup, no history, no recovery path. It shows shape but not ownership. Presence but not jurisdiction.

The pattern from the Knowledge Graph:

> *Editor visibility ≠ ownership; nested .git dirs are separate blast radii; enumerate before destructive ops.*

Separate blast radii. The metaphor is precise. A blast radius is the area affected by a single failure. When a destructive operation crosses a `.git` boundary, it does not detonate once — it detonates in each repository separately, with different damage in each. In one repository, the tracked files are recoverable. In another, the untracked files are gone. In a third, the stash patches preserve what the working tree lost. Each blast radius has its own physics, and the operator who assumes a single explosion has already lost control of the others.

---

## IV. What Cannot Be Recovered

The incident's damage report distinguished three categories:

- **Tracked files**: recoverable from git.
- **Unstaged tracked edits**: partly recoverable from pre-commit stash patches.
- **Untracked files**: no guaranteed recovery path.

The ordering is a gradient of increasing risk, and the gradient maps directly to how well each category is known at the boundary. Tracked files are fully known — git stores every version. Unstaged edits to tracked files are partially known — git knows the file exists, even if it doesn't know the latest changes. Untracked files are unknown. Git has never seen them. No commit contains them. No reflog references them. They exist only on disk, and when the disk changes, they are gone.

This gradient reveals a principle: the recoverability of data is proportional to how well it is known at the boundary. Data that has been normalized — committed, tracked, indexed — survives. Data that has not been normalized — untracked, unstaged, unindexed — does not. The recovery succeeded for the known data and failed (or was uncertain) for the unknown data. This is the One Law, stated not as a design principle but as a physics of information:

> *What the boundary knows, the boundary can restore. What the boundary does not know, no operation can recover.*

The `find . -name .git -type d` command in the cure is not merely discovering directories. It is discovering *what is known where*. Each `.git` directory is a boundary that knows certain things — its tracked files, its commit history, its reflog. The inventory tells the operator: here is what is known, here is what is at risk, here is where loss is permanent. Without the inventory, the operator does not know what they do not know.

And not knowing what you do not know is the definition of operating without a boundary.

---

## V. The Boundary Nobody Drew

Consider how the workspace came to contain nested repositories in the first place.

Nobody drew a boundary. Nobody said: "These private projects are external systems mounted into the editor." They accumulated. A developer cloned a related project into a convenient location. Another project was initialized for quick prototyping. A third was inherited from a different machine. Each addition was small, natural, unremarkable. Each addition moved the workspace further from the implicit model — one directory, one repository, one domain — without any signal that the model was being violated.

This is how boundaries erode: not by dramatic violation but by gradual accretion. No single addition was wrong. Each was a reasonable, local decision. But the aggregate effect was a workspace whose visual appearance no longer matched its operational reality — a tree that was really a forest, shown in an editor that cannot display forests.

The pattern is familiar from the project's experience with other boundaries. The shell boundary eroded when `shlex.quote()` was added at the join site instead of eliminating the shell entirely (FR-322). The architecture boundary eroded when import-linter was not installed for months (Chapter 9). The changelog boundary eroded when gates checked for file existence but not file content (FR-373). In each case, the erosion was gradual, the individual steps were defensible, and the cumulative state was dangerous.

Workspace boundary erosion is distinguished from these by its invisibility. An un-enforced import can be found by scanning code. An empty changelog can be found by reading the file. A nested repository boundary is invisible to every tool that does not explicitly look for `.git` directories. It is not checked by pre-commit hooks. It is not flagged by CI. It is not displayed by the editor sidebar. It exists only in the filesystem's structure, and the filesystem's structure is the one thing we have been trained to trust without verification.

The diary concluded:

> *Private application repositories inside a framework workspace must be treated as external systems mounted into the editor, not as disposable subdirectories.*

"Mounted into the editor" — the phrasing reframes what the operator sees. A mounted system is a guest. It has its own rules, its own permissions, its own recovery semantics. You do not `rm -rf` a mounted volume without unmounting it first. You do not delete a guest's files without asking whether the guest has backups. The reframing converts the interface's implicit promise — "this is all yours" — into an explicit question: "whose is this?"

---

## VI. The Census Before the Campaign

The cure is named `boundary_inventory`. It consists of two commands:

```bash
find . -name .git -type d -prune
git status --short --untracked-files=all
```

For each nested repository discovered, repeat the status check inside that repository.

This is not a sophisticated tool. It is a census. It counts the boundaries, enumerates the unknowns, and makes the operator's ignorance visible before the operation begins. Its value is not in what it finds — most of the time, it will find nothing unexpected — but in the act of looking. The act of looking transforms the workspace from an assumed domain into a surveyed one.

The census has an analogue in every discipline that deals with irreversible operations. Surgeons mark the operative site before anesthesia — not because they might forget which knee to replace, but because the marking converts assumption into verification. Pilots walk around the aircraft before takeoff — not because they expect to find a missing wing, but because the walk converts trust in the maintenance crew into personal inspection. The boundary inventory converts trust in the editor's sidebar into personal knowledge of the repository structure.

Each of these rituals has a common property: they are performed at the point of irreversibility. The surgeon marks before cutting, not after. The pilot walks before takeoff, not during. The developer inventories before deleting, not after. The cure is positioned at the boundary where the destructive operation enters the filesystem — the last moment when knowledge can still prevent loss.

And each of these rituals feels redundant almost every time. The surgeon knows which knee. The pilot trusts the crew. The developer sees a single project in the sidebar. The redundancy is the point. The moment the ritual finds nothing is the moment it proves the assumption was safe. The moment it finds something is the moment it prevents the catastrophe. The cost of the ritual is constant. The cost of skipping it is unbounded.

---

## VII. What Visibility Conceals

What does this trap reveal about thinking itself?

It reveals that we think in interfaces. We do not think about the filesystem — we think about the file tree in the sidebar. We do not think about the version-control topology — we think about the branch dropdown in the status bar. We do not think about the set of all `.git` directories under the current working directory — we think about "the repository," singular, because that is what the interface presents.

This is not a failure of intelligence. It is a feature of cognition. Interfaces exist precisely because thinking about raw reality is too expensive. The file tree abstracts away inodes, permissions, mount points, and symbolic links to show us what we need: names and containment. The abstraction serves us well — until it hides a boundary that matters.

The `workspace_is_not_boundary` trap is, at bottom, a failure to distinguish between what the interface shows and what the system contains. The interface shows a tree. The system contains a forest. The interface shows containment. The system contains independent jurisdictions. The interface promises unity. The system has boundaries that the interface was never designed to display.

This is the filesystem analogue of the `instruction_boundary` trap, as the diary noted:

> *Just as agent instructions must be treated as external input, nested repositories must be treated as external systems.*

Both traps share a structure: something that appears to be part of the current context — instructions that appear in the system prompt, repositories that appear in the sidebar — is actually external, with its own rules, its own ownership, and its own consequences. The interface presents integration. The reality is adjacency.

The cure for both is the same: inventory before action. Before trusting the instructions, ask who wrote them and what their incentives are. Before trusting the file tree, ask how many repositories it contains and who owns each one. The boundary inventory is not a filesystem operation. It is a *cognitive* operation: the deliberate replacement of what the interface tells you with what the system actually contains.

Every interface makes a promise: what you see is what is. The promise is almost always true. And the cases where it is false are the cases where the damage is irreversible, the recovery depends on luck, and the operator says afterward: "I didn't know those were separate repositories."

The inventory would have taken five seconds. The recovery took hours.

---

*The editor shows one tree. The filesystem contains many. And the gap between what you see and what is — that narrow, silent gap — is where the untracked files live, and where they die.*
