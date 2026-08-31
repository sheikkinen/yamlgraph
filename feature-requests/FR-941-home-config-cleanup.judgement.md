# Judgement: FR-941 Home Config Cleanup — Dead Agents and Global CLAUDE.md

**Verdict:** APPROVED WITH REVISIONS — the source-boundary cleanup is coherent and minimal, but authority activates only after committed evidence, exact human-approved dispositions, and mechanically checkable desired-state witnesses are folded into the FR.

**Reviewed against:** `feature-requests/FR-941-home-config-cleanup.md`; cited sibling `feature-requests/FR-942-instruction-context-diet.md`; cited repo doctrine `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `feature-requests/TEMPLATE.md`; prior doctrine authority record `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; and `feature-requests/FR-890-research-sole-route-closed-input-alternatives.judgement.md`. No `$HOME` file, chat transcript, or uncommitted session-analysis record was consumed.

## What is sound

The problem is aimed at the correct boundary. The FR identifies user-home definitions and instructions as the sources injected across workspaces, rejects a repo-side loader filter, and confines enforcement to `~/.claude/` rather than framework code (`feature-requests/FR-941-home-config-cleanup.md:23-32`, `feature-requests/FR-941-home-config-cleanup.md:47-48`). That follows the Scripture's rule to normalize where external data enters and to treat instruction-boundary drift as a defect (`.github/copilot-instructions.md:52`, `.github/copilot-instructions.md:84-85`).

Scope and single responsibility are sound in principle. The seven agent definitions and the global instruction file are two inputs to the same user-home prompt-assembly boundary and share the same first consumer/event (`feature-requests/FR-941-home-config-cleanup.md:8`, `feature-requests/FR-941-home-config-cleanup.md:23-30`). The sibling FR confirms that repo instruction files are a deliberately separate surface with no shared enforcement target (`feature-requests/FR-942-instruction-context-diet.md:10`, `feature-requests/FR-942-instruction-context-diet.md:67`), so FR-941 does not need a split.

The implementation class is feasible and appropriately subtractive: exact filesystem moves or deletions need no new framework primitive, provider, graph, loader filter, or dependency (`feature-requests/FR-941-home-config-cleanup.md:28-32`). Strategically, this is **pattern documentation / operator-configuration cleanup**: existing filesystem operations suffice, and there is no framework use case to generalize.

The intended result is testable after revision. Exact path manifests, content hashes, byte counts, file-existence assertions, and a captured post-restart roster can directly prove the desired state. The current criteria do not yet supply those exact assertions: dispositions remain choices, the surviving `CLAUDE.md` content remains a candidate, and the final roster criterion is only an operator spot-check (`feature-requests/FR-941-home-config-cleanup.md:28-30`, `feature-requests/FR-941-home-config-cleanup.md:36-39`).

## Required revisions

### R-1: Replace session narrative with substantive committed evidence

Expand the in-body research record or link a committed `feature-requests/FR-941.research.md`. Record the exact pre-state inventory for the seven named agent files and `~/.claude/CLAUDE.md`, including path, byte count, line count, and SHA-256; quote the specific conflicting instruction lines. Replace the untraceable “session context analysis” reference and the unsupported `~2k tokens/turn` claim with a named measurement method and result; if only file bytes are measured, state bytes rather than tokens.

The alternatives record must contain 4–6 genuine solution classes, a precedent line for each, preserved disagreement, and an explicit `is_this_a_graph` answer. The present four-row table has dispositions but no precedent column, disagreement record, or graph answer (`feature-requests/FR-941-home-config-cleanup.md:9`, `feature-requests/FR-941-home-config-cleanup.md:41-48`), so it does not satisfy the research-substance contract (`.github/skills/judge-fr/doctrine.md:118-130`).

### R-2: Record prior art and the ideal result

Add the template's `**Prior art:**` field and disposition FR-942 explicitly as a disjoint repo-side sibling; disposition every additional retrieved hit, including rejected precedents. Add an `## Ideal Result` section that states the exact globally valid end state before describing filesystem operations. These are required plan surfaces in the current template (`feature-requests/TEMPLATE.md:21-29`, `feature-requests/TEMPLATE.md:59-63`).

### R-3: Obtain and freeze the human disposition decisions

Before enforcement, add a seven-row table with one final action per named agent file: `keep-global`, `move`, or `delete`; one-line rationale; and, for every move, an exact destination path. Add a separate final decision for `~/.claude/CLAUDE.md`: either delete it or retain exact approved content identified by hash. Remove “default expectation,” “likely delete,” “candidate,” and “evaluate” language after those decisions are recorded (`feature-requests/FR-941-home-config-cleanup.md:28-29`).

**Human decision required:** Which final action is approved for each of the seven agent files, and is `~/.claude/CLAUDE.md` deleted or retained with exact content? Options are the actions already enumerated by the FR. Evidence currently supports removal from global injection but does not identify six owning workspace destinations or grant authority to destroy their only copies. Recommended default: move a file only to a named owning workspace; otherwise require explicit delete approval, and delete the global instruction file unless exact universally valid content is named.

### R-4: Freeze an allowlisted, recoverable operation plan

List every source and destination path before execution. Prohibit wildcards, recursive deletion, rewrites of moved agent definitions, and changes outside those paths. For any delete decision, record explicit human approval and preserve the pre-state content in a recoverable operator-approved location before deletion. For any workspace destination, apply the Scripture's repository-boundary inventory before writing there (`.github/copilot-instructions.md:65`, `.github/copilot-instructions.md:88`, `.github/copilot-instructions.md:110`).

### R-5: Replace semantic and manual criteria with exact assertions

Define the expected final `~/.claude/agents/` manifest and exact shell assertions for every keep, move, and delete disposition. For `~/.claude/CLAUDE.md`, assert either nonexistence or equality to the approved SHA-256; do not rely on the semantic phrases “planning-process doctrine,” “leftovers,” or “effort-estimation directive” (`feature-requests/FR-941-home-config-cleanup.md:38`).

Capture a fresh-session post-state roster in a committed evidence block with exact start/end markers, then define a command that extracts only that block and fails if any of the six creative-agent names occurs. The present “operator spot-check” is not mechanically checkable (`feature-requests/FR-941-home-config-cleanup.md:39`; `.github/skills/judge-fr/doctrine.md:43-44`, `.github/skills/judge-fr/doctrine.md:58-61`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised `feature-requests/FR-941-home-config-cleanup.md` with committed evidence, substantive research, prior-art disposition, ideal result, final disposition matrix, implementation status, and before/after witness |
| D-2 | The seven named source files under `~/.claude/agents/`: `forge-image-generator`, `image-art-analyzer`, `image-prompt-architect`, `kalevala-songwriter`, `long-video-generator`, `topical-image-downloader`, and `project-planner`, using their exact existing filenames |
| D-3 | Only the exact owning-workspace destination paths approved and recorded under R-3, with file content preserved byte-for-byte on moves |
| D-4 | `~/.claude/CLAUDE.md`, either deleted or reduced to the exact human-approved content recorded under R-3 |
| D-5 | A committed after-state witness containing commands, exit statuses, manifests, hashes, byte counts, and the delimited fresh-session roster |

Not authorized: changes to `.github/copilot-instructions.md`, repo-root `CLAUDE.md`, hooks, CI, skills, agent loaders, VS Code user prompts, framework code, dependencies, or any `$HOME` path not individually allowlisted in the revised FR; implementation of FR-942; semantic rewrites of agent definitions while relocating them; creation of a global replacement doctrine; wildcard or recursive deletion.

## Revised acceptance criteria

- [ ] AC-01: The committed research evidence inventories all seven exact agent-definition paths and `~/.claude/CLAUDE.md` with path, line count, byte count, SHA-256, and the quoted conflicting global-instruction lines.
- [ ] AC-02: The research record contains 4–6 genuine solution classes with disposition, precedent, preserved disagreement, and an explicit `is_this_a_graph` answer; the FR's `**Research:**` field points to that committed record.
- [ ] AC-03: The FR contains an `## Ideal Result` and a `**Prior art:**` field that dispositions FR-942 and every retrieved prior-art hit.
- [ ] AC-04: A human-approved matrix records exactly one final disposition and rationale for each of the seven agent files, an exact destination for every move, and one final delete-or-exact-content decision for `~/.claude/CLAUDE.md`.
- [ ] AC-05: The operation allowlist contains every approved source and destination and no wildcard; every delete has explicit human approval plus a recoverable pre-state copy, and every move preserves the recorded source SHA-256.
- [ ] AC-06: Post-state assertions prove each of the seven dispositions: kept files remain at the recorded source hash, moved files are absent from the source and present at the destination hash, and deleted files are absent.
- [ ] AC-07: A manifest command proves that `~/.claude/agents/` contains exactly the expected global files after enforcement.
- [ ] AC-08: `~/.claude/CLAUDE.md` is absent, or its post-state SHA-256 equals the exact approved hash; the recorded assertion exits zero.
- [ ] AC-09: The FR records the before/after commands, outputs, exit statuses, manifests, hashes, and byte-count delta in a committed witness.
- [ ] AC-10: A fresh agent session's roster is recorded between unique post-state markers, and the FR's extraction/assertion command exits zero only when none of the six named creative agents appears within that roster block.
- [ ] AC-11: The committed repo diff is limited to FR-941's plan/status/witness and its judgement artifact; no repo code, doctrine, hook, CI, skill, dependency, or FR-942 implementation file changes.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Do not mutate `$HOME` until R-1 through R-5 are folded into FR-941 and the final dispositions are explicitly human-approved. | GATE |
| C-2 | Execute only exact allowlisted paths; no wildcard, recursive deletion, or unrelated `$HOME` cleanup is permitted. | GATE |
| C-3 | Do not delete the only recoverable copy of any agent definition or instruction file. | GATE |
| C-4 | A move into another workspace requires that workspace's boundary inventory and must preserve the source content byte-for-byte. | GATE |
| C-5 | Do not change repo instruction surfaces or implement any part of FR-942 under this authority. | GATE |
| C-6 | Enforcement must leave a committed, mechanically checkable after-state witness; shell success without the witness is not completion. | GATE |

Authority granted: after all required revisions and human disposition decisions are folded into FR-941, perform only the exact allowlisted user-home cleanup and record its mechanically checkable witness within the frozen scope above.
