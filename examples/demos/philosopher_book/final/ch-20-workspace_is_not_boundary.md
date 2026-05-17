# Chapter 20: What You See Is Not What Is

*On the trap called workspace_is_not_boundary: when a tree in the editor is mistaken for a tree in reality.*

---

## I. The Deletion That Crossed a Border

On May 12, 2026, an agent was asked to clean up a repository. The task was clear: remove all traces of certain directories from the YAMLGraph workspace. The tool was `git filter-repo` — a well-understood instrument for rewriting history, documented and precise. The flags were correct. The output was clean. The force push succeeded.

And then the private repositories were gone.

They had been sitting inside the YAMLGraph workspace — nested projects, each with its own `.git` directory, its own commit history, its own untracked files, its own ownership and privacy expectations. The editor displayed them as subdirectories. The file manager displayed them as subdirectories. The terminal's `ls` displayed them as subdirectories. Every interface the agent consulted presented a single, unified tree.

But the tree was a lie. It was not one tree. It was a forest — several independent repositories sharing a visual canopy.

The diary entry for that day recorded the aftermath with the specificity of a damage report:

> *Tracked files were recoverable from git. Unstaged tracked edits were partly recoverable from pre-commit stash patches. Untracked files had no guaranteed recovery path.*

Recovery succeeded. Not because the deletion operation was safe, but because git's internal machinery — reflogs, tracked state, cached patches — happened to preserve enough fragments for reconstruction. The private repositories were reconstructed from committed history and pre-commit stash patches found in `~/.cache/pre-commit/`. The surviving changes were split into focused commits and pushed.

The diary named this with uncomfortable clarity:

> *The confirmation flow asked about scope (simple rm vs. history rewrite, which dirs to include) but never asked the critical boundary question: "Are any of these directories independent git repositories with their own untracked state?"*

---

## II. The Interface's Promise

Why does a file tree feel like a boundary?

Open any editor. The sidebar shows a root directory and its contents, nested downward, indented by depth. The visual structure communicates containment: everything inside is *inside*. Everything visible is *yours*. The root is the perimeter.

This is the interface's implicit promise: what you see is what you're working with. The tree is your workspace. Your workspace is your domain. Your domain is where your operations take effect, and — critically — where they *only* take effect.

The promise holds in the common case. Most of the time, a workspace *is* a single project, a single repository, a single domain. And this is precisely what makes the trap so effective: the interface's lie is a lie of *omission*, told so rarely that questioning it feels paranoid. It does not mark the nested `.git` directory that indicates a separate blast radius. It does not flag the transition from your repository to someone else's.

There is a further seduction specific to agents. A human developer *might* recall that they cloned a private project into a subdirectory three weeks ago. An agent has no such memory. It has the current context: a tree of files, a task description, a set of tools. The tree is the totality of what it knows about the workspace. When the tree lies, the agent has no second source to consult.

The diary understood this:

> *Confidence in the tool substituted for confidence in the problem definition. The Scripture's "When I feel certain, let that be the sign to Judge" applies not just to code, but to destructive operations: the more certain the plan feels, the more likely a boundary assumption is hiding.*

The workspace feels certain because the interface renders it as certain. The certainty is borrowed from the rendering, not earned from the terrain.

---

## III. The Map at Every Altitude

Chapter 9 examined the diagram that was mistaken for a wall. An architecture drawn in Markdown, described in comments, explained in docs — and enforced nowhere.

`workspace_is_not_boundary` is the same failure at a different altitude — not the architecture diagram, but the filesystem itself. The sidebar is a map. The underlying terrain is a set of independent version-control boundaries, each with its own rules about what is tracked, what is recoverable, and what will be permanently lost when deleted.

The editor sidebar is not merely *a* map; it is the map we consult most often, the one we trust most completely, the one whose accuracy we never question. When you open the file tree, you do not ask whether it is complete. You do not ask because the file tree is not a *representation* of the filesystem; it *is* the filesystem, as far as your tools can show you.

Yet it lies. Not in what it shows — the files are really there, the directories are really nested, the paths are really valid — but in what it *omits*. It does not show that `projects/private-app/.git` is a boundary. It does not show that `projects/private-app/untracked-draft.txt` exists in no backup, no history, no recovery path anywhere in the world. It shows shape but not ownership. Presence but not jurisdiction.

A blast radius is the area affected by a single detonation. When a destructive operation crosses a `.git` boundary, it detonates in each repository separately, with different damage in each. In one repository, the tracked files are recoverable. In another, the untracked files are gone. In a third, the stash patches preserve what the working tree lost. Each blast radius has its own physics, and the operator who assumes a single explosion has already lost control of the others.

The `find . -name .git -type d` command is a blast radius survey. It tells you how many detonations there will be.

---

## IV. What Cannot Be Recovered

The incident's damage report distinguished three categories:

- **Tracked files**: recoverable from git.
- **Unstaged tracked edits**: partly recoverable from pre-commit stash patches.
- **Untracked files**: no guaranteed recovery path.

The ordering is a gradient of increasing risk, and the gradient maps directly to how well each category is *known at the boundary*. Tracked files are fully known — git stores every version, every commit, every reflog entry. Unstaged edits to tracked files are partially known — git knows the file exists, even if it doesn't know the latest changes. Untracked files are unknown. Git has never seen them.

This reveals a principle so fundamental it reads like physics: *the recoverability of data is proportional to how well it is known at the boundary*. Data that has been normalized — committed, tracked, indexed — survives. Data that has not been normalized — untracked, unstaged, unindexed — does not.

What the boundary knows, the boundary can restore. What the boundary does not know, no operation can recover.

The `find . -name .git -type d` command is not merely discovering directories. It is discovering *what is known where*. Each `.git` directory is a boundary that knows certain things — its tracked files, its commit history, its reflog, its stashes. The inventory tells the operator: here is what is known, here is what is at risk, here is where loss is permanent.

---

## V. The Boundary Nobody Drew

Nobody drew a boundary between the workspace and the nested repositories. They accumulated. A developer cloned a related project into a convenient subdirectory. Another project was initialized for quick prototyping. A third was inherited from a different machine's backup. Each addition was small, natural, unremarkable. Each addition moved the workspace further from the implicit model — one directory, one repository, one domain — without any signal that the model was being violated.

This is how boundaries erode: not by dramatic violation but by gradual accretion. No single addition was wrong. Each was a reasonable, local decision. But the aggregate effect was a workspace whose visual appearance no longer matched its operational reality.

Workspace boundary erosion is distinguished from other boundary failures by its *invisibility*. An un-enforced import can be found by scanning code. An empty changelog can be found by reading the file. A nested repository boundary is invisible to every tool that does not explicitly look for `.git` directories. It is not checked by pre-commit hooks. It is not flagged by CI. It is not displayed by the editor sidebar.

The diary concluded with a reframing so precise it became a heuristic:

> *Private application repositories inside a framework workspace must be treated as external systems mounted into the editor, not as disposable subdirectories.*

"Mounted into the editor" — the phrase converts what the operator sees. A mounted system is a guest. It has its own rules, its own permissions, its own recovery semantics. You do not `rm -rf` a mounted volume without unmounting it first. You do not delete a guest's files without asking whether the guest has backups.

---

## VI. The Census Before the Campaign

The cure is named `boundary_inventory`. It consists of two commands:

```bash
find . -name .git -type d -prune
git status --short --untracked-files=all
```

For each nested repository discovered, repeat the status check inside that repository. If any untracked file or unstaged change exists, stop and make an explicit backup or commit plan before deletion.

This is not a sophisticated tool. It is a census. It counts the boundaries, enumerates the unknowns, and makes the operator's ignorance visible before the operation begins. Its value is not in what it finds — most of the time, it will find nothing unexpected — but in the act of looking. The act of looking transforms the workspace from an assumed domain into a surveyed one.

The census is performed at the *point of irreversibility*. The developer inventories before deleting, not after. The cure is positioned at the boundary where the destructive operation enters the filesystem — the last moment when knowledge can still prevent loss.

And the ritual feels redundant almost every time. The developer sees a single project in the sidebar. The redundancy is the point. The moment the ritual finds nothing is the moment it proves the assumption was safe. The moment it finds something is the moment it prevents the catastrophe.

---

## VII. What Visibility Conceals

What does this trap reveal about thinking itself?

It reveals that we think in interfaces. We do not think about the filesystem — we think about the file tree in the sidebar. We do not think about the version-control topology — we think about the branch dropdown in the status bar. We do not think about the set of all `.git` directories under the current working directory — we think about "the repository," singular, because that is what the interface presents.

This is not a failure of intelligence. It is a feature of cognition. Interfaces exist precisely because thinking about raw reality is too expensive. The abstraction serves us well — until it hides a boundary that matters. And when it hides a boundary that matters, the abstraction does not merely fail to help. It actively prevents the question that would have exposed the boundary, because the question — "is this really one workspace?" — contradicts the visual evidence so completely that asking it feels absurd.

The `workspace_is_not_boundary` trap is, at bottom, a failure to distinguish between what the interface shows and what the system contains. The interface shows a tree. The system contains a forest. The interface shows containment. The system contains independent jurisdictions.

The diary drew the connection to the project's other boundary traps:

> *This is the filesystem analogue of the `instruction_boundary` trap: just as agent instructions must be treated as external input, nested repositories must be treated as external systems.*

Chapter 16 traces the instruction boundary — vendor's instructions, arriving through the same channel as the agent's own reasoning, treated as self rather than as external data. Here, the nested repositories arrive through the same visual channel as the workspace's own directories, treated as owned rather than as external systems. Both traps share a structure: something that *appears* to be part of the current context is actually external, with its own rules, its own ownership, and its own consequences for loss.

The cure for both is the same: inventory before action. The boundary inventory is not, in the end, a filesystem operation. It is a *cognitive* operation: the deliberate replacement of what the interface tells you with what the system actually contains.

Every interface makes a promise: what you see is what is. The promise is almost always true. The cost of verifying it is negligible. And the cases where it is false are the cases where the damage is irreversible, the recovery depends on luck, and the operator says afterward: "I didn't know those were separate repositories."

The inventory would have taken five seconds. The recovery took hours.

---

*The editor shows one tree. The filesystem contains many. And the gap between what you see and what is — that narrow, silent gap — is where the untracked files live, and where they die.*
