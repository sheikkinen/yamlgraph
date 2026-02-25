# Chapter 04: Inquisitor — Background Compliance Audit

In the structured world of the YAMLGraph Development Pipeline, consistency and adherence to established principles are paramount. While many checks can be performed upfront, some require a deeper, more reflective analysis. This is where the Inquisitor steps in.

## What is the Inquisitor?

The Inquisitor (`.chaplain/inquisitor.sh`) is an automated background audit process designed to run quietly after every commit. Its primary mission is to assess recent work against the project's foundational Scripture (`CLAUDE.md`), identifying deviations from established doctrine. Unlike tools that prevent commits, the Inquisitor observes, analyzes, and records its findings, classifying them as compliant, drifting, or outright violations. It never intervenes directly to fix issues; its role is purely diagnostic, appending exactly one detailed entry to `docs/diary.md` for team review.

## Why Background Audits?

The YAMLGraph pipeline employs various safeguards, with pre-commit hooks catching immediate syntax errors, formatting inconsistencies, or simple linting violations. These are quick, superficial checks that prevent obvious problems from entering the codebase.

The Inquisitor, however, operates at a different level of scrutiny. It performs a *semantic* audit, delving into the meaning and intent behind changes. This allows it to identify:

*   **Doctrinal Drift:** Subtle deviations from architectural principles or development best practices outlined in `CLAUDE.md`.
*   **Missing Context:** Gaps in documentation, testing, or changelog entries that, while not syntax errors, represent a failure to fully complete a task according to project standards.
*   **Potential Technical Debt:** Areas where shortcuts might have been taken, leading to future maintenance burdens.

By running in the background post-commit, the Inquisitor avoids blocking developer workflow while still providing invaluable feedback on the overall health and compliance of the project's evolution. It ensures that the team isn't just shipping code, but shipping *compliant* code that aligns with the project's long-term vision.

## Audit Flow

The Inquisitor's journey from commit to diary entry is a structured process, ensuring comprehensive analysis without interrupting the immediate development flow.

```mermaid
flowchart LR
  A[Commit] --> B[Post-commit hook]
  B --> C[inquisitor.sh]
  C --> D[Gather context]
  D --> E[Investigate]
  E --> F[Judge findings]
  F --> G[Record to diary]
```

## The Four Audit Steps

The core intelligence of the Inquisitor is delegated to a single `copilot` CLI invocation, which orchestrates four distinct steps: Gather, Investigate, Judge, and Record.

### 1. Gather Evidence

Before any analysis can begin, the Inquisitor collects all necessary context. This step is crucial for providing the `copilot` agent with a comprehensive understanding of the recent changes and the project's current state.

The Inquisitor collects the following intelligence:

*   **Recent Commits:** The last five commit messages (`git log --oneline -5`) are read to understand the immediate history and intent of recent work.
*   **CHANGELOG.md:** The top 30 lines of the `CHANGELOG.md` are reviewed to check for corresponding entries for new features or fixes.
*   **docs/diary.md:** The latest diary entry is consulted, providing context on ongoing tasks and previous observations.
*   **CLAUDE.md (Scripture):** The entire `CLAUDE.md` document, encompassing Commandments, Sermons, and the Rite of Correction, is reread to ensure the `copilot` agent has the freshest understanding of project doctrine.

### 2. Investigate

With the evidence gathered, the `copilot` agent proceeds to scrutinize each recent commit against a set of predefined doctrinal rules. This is where the deeper semantic analysis occurs, asking critical questions about the nature and completeness of the changes.

For each recent commit, the Inquisitor checks six doctrinal rules:

1.  **Conventional Commits:** Does the commit message adhere to the Conventional Commits specification (Commandment 10)?
2.  **CHANGELOG Entry:** Is there a corresponding entry in `CHANGELOG.md` for the changes introduced (Commandment 10)?
3.  **Architecture Requirements:** If a new capability was introduced, was a requirement added to `ARCHITECTURE.md` (ADR-001)?
4.  **Test Tagging:** If new tests were added, do they include `@pytest.mark.req` tags to link them to requirements (ADR-001)?
5.  **Diary Entry:** Was a diary entry written for the task associated with this commit (Sermon: Distill)?
6.  **`# noqa` Suppressions:** Are there any `# noqa` suppressions in the code without corresponding `CONF-XXX` entries, indicating an unconfessed suppression (noqa Confessions)?

### 3. Judge

After investigation, each finding is classified according to its severity and impact on doctrinal compliance. This step provides a clear, actionable assessment of the observed behavior.

Findings are classified into one of three levels:

*   **✓ COMPLIANT:** The work fully adheres to the project's doctrine and best practices. No action is required.
*   **⚠ DRIFT:** A minor deviation or advisory finding. While not a critical violation, it indicates a slight departure from ideal practices or a potential area for future improvement. No immediate harm, but worth noting.
*   **✗ VIOLATION:** A clear breach of established doctrine, commandments, or architectural decisions. These findings often require corrective action during the Plan → Judge phase.

### 4. Record

The final step is to meticulously record the Inquisitor's findings. This ensures that observations are captured, providing a historical log of compliance over time and informing future planning.

All findings are aggregated into a single, comprehensive diary entry that is appended to `docs/diary.md`. This entry includes a summary of the audit, the specific checks performed, and the classification of each finding, along with any relevant notes. Critically, the Inquisitor never *fixes* violations; it only *records* them, empowering the team to address them consciously.

## Findings Classification

The Inquisitor's classifications offer a quick and clear understanding of the audit results:

| Symbol | Classification | Meaning | Example |
| :----- | :------------- | :------ | :------ |
| ✓      | COMPLIANT      | Fully adheres to doctrine. | All new tests tagged with `@pytest.mark.req`. |
| ⚠      | DRIFT          | Minor deviation or advisory. | A `TODO` comment was found without an associated issue ID. |
| ✗      | VIOLATION      | Clear breach of doctrine.  | A `# noqa` suppression was used without a `CONF-XXX` confession. |

## Sample Findings

Here's an example of what a typical Inquisitor report might look like, appended to `docs/diary.md`:

```
### Inquisitor Audit - 2023-10-27T10:30:00Z

**Commit:** `feat: add new data ingestion service (a1b2c3d)`

| Check                      | Result | Notes                                        |
| :------------------------- | :----- | :------------------------------------------- |
| Conventional Commit        | ✓      | Commit message follows 'feat:' convention.   |
| CHANGELOG updated          | ✓      | Entry added for new data ingestion service.  |
| Requirement coverage       | ✓      | All new tests tagged with `@pytest.mark.req`.|
| Architecture.md updated    | ✓      | New ADR-005 for data ingestion service added.|
| Diary entry for task       | ✓      | Task #1234 has a corresponding diary entry.  |
| Hardcoded prompts          | ✓      | No hardcoded LLM prompts found.              |
| Dead code                  | ⚠      | `vulture` flagged `unnecessary_function()` as unused. |
| `# noqa` without confession | ✗      | `src/data/processor.py:45` missing `CONF-XXX`.|
```

## Integration

The Inquisitor is designed to be a seamless, low-overhead component of the development pipeline:

*   **Triggered by `post-commit` hook:** After every successful commit, a `post-commit` Git hook automatically executes `inquisitor.sh`. This ensures consistent and timely audits without requiring manual intervention.
*   **Runs asynchronously:** The audit is typically fast, but it runs in the background, ensuring it doesn't block the developer from immediately starting their next task.
*   **Results appear in next diary entry:** The findings are not immediately displayed in the terminal after the commit. Instead, they are appended to `docs/diary.md`, becoming part of the project's ongoing historical record, available for review when the team consults the diary. This design reinforces the Inquisitor's role as a reflective, rather than immediate, feedback mechanism.
