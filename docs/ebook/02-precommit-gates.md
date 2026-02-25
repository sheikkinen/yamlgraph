# Pre-commit Gates: Quality at the Threshold

In the YAMLGraph Development Pipeline, quality is not an afterthought; it's a foundational principle woven into every stage. Nowhere is this more evident than in our implementation of pre-commit gates. These gates are a set of automated checks that run *before* code is even committed to the repository, acting as an essential first line of defense against bugs, inconsistencies, and architectural deviations.

## Why Pre-commit Hooks? Prevention Over Cure

The philosophy behind pre-commit hooks is simple but powerful: **prevention is better than cure.** Catching issues early, ideally before they even enter version control history, dramatically reduces the cost and complexity of remediation. Imagine finding a style violation or a missing test case immediately upon attempting to commit, rather than hours later during a code review or, worse, after deployment. Pre-commit hooks empower developers with instant feedback, fostering a culture of continuous quality and adherence to project standards.

YAMLGraph enforces a rigorous layered quality gate system via its `.pre-commit-config.yaml`. This configuration orchestrates **27 distinct hooks** across three critical Git stages: `pre-commit`, `commit-msg`, and `post-commit`. The pipeline is configured with `fail_fast: true`, meaning the very first hook that fails will immediately abort the entire commit process. This ensures that no code bypasses even the most basic checks. Together, these gates embody the project's "Scripture" — a doctrine that code must pass through the fire of linting, testing, traceability, and entropy measurement before it may merge.

## The YAMLGraph Pre-commit Hook Compendium

Here's a comprehensive overview of the hooks that stand guard over the YAMLGraph codebase:

| Hook ID | Purpose | What It Catches | When It Fires |
|:--------------------------|:-----------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------|
| `ruff` | Linter with autofix | Style violations, import order, unused imports | pre-commit |
| `ruff-format` | Code formatter | Inconsistent formatting | pre-commit |
| `trailing-whitespace` | Whitespace cleanup | Trailing whitespace | pre-commit |
| `end-of-file-fixer` | EOF newline | Missing final newline | pre-commit |
| `check-yaml` | YAML syntax | Invalid YAML files | pre-commit |
| `check-added-large-files` | Binary bloat guard | Accidentally committed large files | pre-commit |
| `check-merge-conflict` | Conflict markers | Unresolved `<<<<<<<` merge markers | pre-commit |
| `check-ast` | Python syntax | Files that don't parse as valid Python | pre-commit |
| `check-toml` | TOML syntax | Invalid pyproject.toml or similar | pre-commit |
| `debug-statements` | Debug cleanup | Leftover `breakpoint()`, `pdb.set_trace()` | pre-commit |
| `detect-private-key` | Secret detection | Private keys accidentally staged | pre-commit |
| `diary-rotate` | Diary rotation on day change | Stale diary — rotates `docs/diary.md` to archive when date changes | pre-commit |
| `req-coverage-strict` | Requirement traceability | Requirements in `ARCHITECTURE.md` without `@pytest.mark.req` test coverage | pre-commit |
| `noqa-confession` | noqa documentation | `# noqa` suppressions not documented in `docs/confessions.md` | pre-commit |
| `inline-llm-check` | Architecture enforcement | Scripts that import LLM execution functions without graph loading (bypassing 3-layer architecture) | pre-commit |
| `radon-complexity` | Cyclomatic complexity gate | Functions with cyclomatic complexity ≥ 21 (grade D or worse) | pre-commit |
| `file-size-gate` | Module size limit | Python files >450 lines (error), >400 lines (warning) | pre-commit |
| `forbid-terms` | Term prohibition | `TODO`, `FIXME`, `backward compatibility` in `yamlgraph/` source | pre-commit |
| `jscpd-dup` | Duplicate detection | Code clones (threshold 10%, min 10 lines / 80 tokens) via jscpd | pre-commit |
| `vulture-dead-code` | Dead code detection | Unreachable/unused code (≥80% confidence) via vulture | pre-commit |
| `hedging-check` | Silent fallback detection | Patterns like `if not X: X = broader_data` or `X = expr or fallback` | pre-commit |
| `pytest` | Unit test suite | Failing unit tests (`tests/unit/` only, ~20s) | pre-commit |
| `conventional-pre-commit` | Conventional Commits | Non-conforming commit messages; allowed types: feat, fix, chore, docs, refactor, test, ci, perf, style, build | commit-msg |
| `feat-requires-fr` | Feature request traceability | `feat:` commits missing `FR-XXX` reference | commit-msg |
| `changelog-required` | Changelog enforcement | `feat:` or `fix:` commits without staged `CHANGELOG.md` changes | commit-msg |
| `absolution` | Final blessing | Nothing — it only runs if ALL other hooks passed. Prints a reminder to Distill. | pre-commit, commit-msg |
| `inquisitor-background` | Async post-commit audit | Fires asynchronously after commit; audits recent work against the Scripture via Copilot CLI | post-commit |

## Standard Hooks: The Foundational Layer

Many of the initial hooks in the pipeline are standard, off-the-shelf tools that provide immediate, high-value quality checks. These hooks are typically sourced from widely adopted repositories like `pre-commit-hooks` and `astral-sh/ruff-pre-commit`.

*   **`ruff` and `ruff-format`**: These hooks leverage the incredibly fast Ruff linter and formatter. `ruff` catches a wide array of style violations, enforces import order, and flags unused imports, while `ruff-format` ensures consistent code formatting across the entire project. Together, they eliminate bikeshedding over style and ensure a clean, readable codebase.
*   **Whitespace and File Structure**: `trailing-whitespace` and `end-of-file-fixer` are small but mighty hooks that ensure basic file hygiene. They prevent annoying diffs caused by invisible characters and ensure that all files end with a newline, a common Unix convention.
*   **Syntax Checks**: `check-yaml`, `check-toml`, and `check-ast` validate the syntax of YAML, TOML, and Python files respectively. These are crucial for catching basic structural errors before they can cause runtime failures.
*   **Security and Cleanup**: `detect-private-key` is a vital security gate, preventing accidental commits of sensitive information. `debug-statements` helps ensure that debugging artifacts like `breakpoint()` calls are not inadvertently shipped to production.
*   **Merge Conflict Markers**: `check-merge-conflict` ensures that no unresolved `<<<<<<<` markers from Git merges are committed, which would otherwise lead to immediate syntax errors or unexpected behavior.
*   **File Bloat**: `check-added-large-files` prevents the accidental addition of massive binary files or other unwanted artifacts that can bloat the repository size and slow down cloning.

These standard hooks form the bedrock of quality, handling common issues efficiently and automatically, allowing developers to focus on more complex, domain-specific challenges.

## Custom Scripts: Enforcing the Scripture

Beyond the standard checks, YAMLGraph employs a suite of custom Python scripts and shell commands, each designed to enforce specific architectural principles, traceability requirements, and quality thresholds unique to the project.

#### `absolution.py`: The Final Blessing

In the YAMLGraph pipeline, "absolution" is the ultimate validation. The `absolution.py` script is configured to run as the very last hook in both the `pre-commit` and `commit-msg` stages, and crucially, it only executes if *every single preceding hook has passed*. Given `fail_fast: true`, reaching the Absolution hook signifies that your commit has successfully navigated the entire gauntlet of quality checks.

Upon success, it prints a specific, verbose message:

```
✓ Absolution granted

**Distill.** After completing a task list, add a metacognitive entry to docs/diary.md.
Name the cognitive trap or insight. Extract a heuristic.
Plant a seed — a forward-looking question to grow new ideas.
If the heuristic proves recurring, graduate it to the Scripture.
```

This message serves not just as a confirmation of code quality, but as a prompt for metacognition and continuous learning, encouraging developers to reflect on their process and contribute to the project's evolving "Scripture" of best practices. The `verbose: true` flag in its configuration ensures this message is always displayed, providing a clear sign-off for a successful commit.

#### `req_coverage.py`: Requirement Traceability

The `req_coverage.py` script is central to YAMLGraph's commitment to robust requirement traceability. It enforces a direct link between requirements defined in `ARCHITECTURE.md` and their corresponding test coverage.

Every test function in `tests/unit/` and `tests/integration/` is expected to carry a `@pytest.mark.req("REQ-YG-XXX")` decorator, explicitly linking it to a specific requirement ID (e.g., `REQ-YG-001`). The script uses Abstract Syntax Tree (AST) parsing to extract these markers from test files and then cross-references them against a master list of all 87 known requirement IDs across 32 capabilities (CAP-01 through CAP-32).

The pre-commit hook utilizes the `--strict` flag, which means the script will fail (exit with code 1) if any requirement has zero test coverage. This ensures that every declared requirement is adequately tested, preventing "paper requirements" that lack real-world validation. This rigorous enforcement ensures that the project's architecture is fully verifiable through its test suite.

#### `noqa_coverage.py`: The `noqa` Confession Enforcement

While `# noqa` comments are sometimes necessary to suppress linter warnings, they can also hide underlying issues or indicate areas where code quality is being compromised. The `noqa-confession` hook, powered by `noqa_coverage.py`, enforces a strict "confession" process for every `# noqa` suppression in the codebase.

The script scans all Python files for `noqa` comments and demands that each one be documented in `docs/confessions.md` with a structured entry following the `CONF-XXX` pattern. Each confession must include:
*   **CONF-XXX**: A unique identifier (e.g., `CONF-001`).
*   **File**: The path and line number of the suppression as a Markdown link.
*   **Code**: The specific linter error code being suppressed (e.g., `E402`, `F401`, or `ALL` for blanket suppressions).
*   **Sin**: A brief description of what the suppressed code does or why it triggers the linter.
*   **Penance**: A justification for why the suppression is acceptable or necessary in this specific context.

The pre-commit hook runs `noqa_coverage.py` in `--strict` mode, meaning any undocumented `noqa` comment will cause the commit to fail with a clear message: `"FAIL -- undocumented noqa detected"` and `"See docs/confessions.md for how to confess your sins and beg forgiveness."` This ensures that every deviation from linting rules is transparent, intentional, and justified.

#### `diary_rotate.py`: Automated Diary Rotation

The `diary-rotate` hook, powered by `diary_rotate.py`, automates the archival of `docs/diary.md`, which serves as a metacognitive log for developers. This hook has `always_run: true`, meaning it checks on every commit.

Rotation is triggered when the date of the most recent `## YYYY-MM-DD:` header in `docs/diary.md` is *before today's date*. If a new day has dawned since the last diary entry, the script performs the following sequence:
1.  It imports any pending entries or git reports from `~/scheduled-yamlgraphs/outputs/`, ensuring a comprehensive record.
2.  It moves the current `docs/diary.md` to an archive file named `docs/diary-YYYY-MM-DD.md`. If a file with that name already exists (e.g., multiple commits on the same day after a rotation), it appends a numerical suffix (e.g., `diary-YYYY-MM-DD-1.md`).
3.  A fresh `docs/diary.md` is created with a new `## YYYY-MM-DD:` header for the current date, along with a "Previous:" link pointing to the newly archived diary.
4.  Both the archived file and the new `docs/diary.md` are automatically staged with `git add`, ensuring the diary rotation is part of the current commit.

This automated process ensures that the diary remains current, provides a clear historical record, and prevents the main diary file from becoming unwieldy.

#### `changelog-required`: Enforcing Changelog Updates

The `changelog-required` hook is a `commit-msg` stage gate designed to enforce project transparency and maintain an up-to-date `CHANGELOG.md`. This hook specifically targets `feat:` (feature) and `fix:` (bug fix) conventional commits.

If a commit message starts with `feat:` or `fix:`, this hook verifies that changes to `CHANGELOG.md` have been staged as part of the current commit. If no `CHANGELOG.md` modifications are detected, the commit is rejected. This ensures that every significant change that impacts users or functionality is documented in the changelog, facilitating release notes and project communication.

#### `feat-requires-fr`: Feature Request Traceability

Mirroring the requirement traceability for code, the `feat-requires-fr` hook enforces traceability for new features. This `commit-msg` stage hook dictates that any commit message prefixed with `feat:` (indicating a new feature) *must* also include a reference to a `FR-XXX` (Feature Request) identifier.

For example, a valid feature commit message might be `feat: FR-038 add commit enforcement`. If a `feat:` commit is made without an `FR-XXX` reference, the commit is rejected with an error message. This ensures that all new features are tied back to a planned and documented feature request, promoting structured development and preventing ad-hoc feature creep.

#### Other Custom Quality Gates

Beyond these detailed examples, YAMLGraph incorporates several other custom hooks to maintain a high bar for code quality and architectural adherence:

*   **`radon-complexity`**: Fails commits if any function has a cyclomatic complexity of 21 or higher (Radon's 'D' grade or worse), promoting modularity and testability.
*   **`file-size-gate`**: Warns for Python files over 400 lines and fails for files over 450 lines, encouraging smaller, more focused modules.
*   **`forbid-terms`**: Prevents the use of certain prohibited terms (e.g., `TODO`, `FIXME`, `backward compatibility`) in core source code, encouraging immediate action or proper documentation.
*   **`jscpd-dup`**: Leverages `jscpd` to detect code clones, failing if duplication exceeds a 10% threshold or if blocks of 10+ lines/80+ tokens are duplicated.
*   **`vulture-dead-code`**: Identifies and flags unreachable or unused code segments with high confidence (≥80%), promoting a lean codebase.
*   **`hedging-check`**: Detects "silent fallback" patterns in code (e.g., `if not X: X = broader_data`), which can obscure logic and make debugging harder.
*   **`inline-llm-check`**: A crucial architectural enforcement hook that prevents scripts from directly importing LLM execution functions without first loading a graph, ensuring adherence to YAMLGraph's 3-layer architecture.
*   **`pytest`**: Runs a focused suite of unit tests (`tests/unit/`) as a pre-commit check, providing immediate feedback on core functionality.

## Annotated Configuration Examples

Understanding the configuration of these hooks provides insight into their behavior. Here are a few examples from `.pre-commit-config.yaml` with inline explanations:

### Absolution Hook: The Final Gate

```yaml
  - repo: local # This hook is defined locally within the project.
    hooks:
      - id: absolution # Unique identifier for the hook.
        name: "Absolution" # Human-readable name for pre-commit output.
        entry: .venv/bin/python scripts/absolution.py # The command to execute.
        language: system # Indicates the script is run directly using system Python.
        pass_filenames: false # The script doesn't need specific filenames as arguments.
        always_run: true # Ensures this hook runs every time, regardless of staged files.
        verbose: true # Displays the script's output (the "Absolution granted" message).
        stages: [pre-commit, commit-msg] # Runs at both pre-commit and commit-msg stages.
```

### Feature Request Traceability Hook

```yaml
  - repo: local
    hooks:
      - id: feat-requires-fr
        name: feat commits require FR-XXX # Descriptive name.
        entry: "bash -c 'msg=$(cat \"$1\"); if echo \"$msg\" | grep -qE \"^feat(\\\\(.*\\\\))?:\" && ! echo \"$msg\" | grep -qE \"FR-[0-9]+\"; then echo \"ERROR: feat: commits require FR-XXX reference\"; echo \"Example: feat: FR-038 add commit enforcement\"; exit 1; fi' _"
        # The 'entry' defines an inline bash script.
        # It reads the commit message ($1), checks if it starts with 'feat:'
        # AND if it *does not* contain 'FR-XXX'. If both true, it prints an error and exits 1.
        language: system # Indicates a system command (bash in this case).
        stages: [commit-msg] # This hook specifically runs on the commit message stage.
        always_run: true # Always runs when a commit message is being processed.
```

### Radon Complexity Gate

```yaml
  - repo: local
    hooks:
      - id: radon-complexity
        name: radon CC gate (block grade D) # Name indicating its purpose and threshold.
        entry: bash -c 'output=$(.venv/bin/python -m radon cc yamlgraph/ -n D -s 2>&1); if [ -n "$output" ]; then echo "$output"; echo ""; echo "FAIL -- functions with cyclomatic complexity >= 21 (grade D) detected"; exit 1; fi'
        # Inline bash script:
        # 1. Runs 'radon cc' on the 'yamlgraph/' directory.
        # 2. '-n D' means it reports functions with grade D complexity or worse (CC >= 21).
        # 3. '-s' shows the score.
        # 4. Redirects stderr to stdout and captures all output into 'output' variable.
        # 5. If 'output' is not empty (meaning radon found issues), it prints the output,
        #    a custom error message, and exits with 1 to fail the commit.
        language: system # System command.
        pass_filenames: false # Radon checks the entire directory, not specific files.
        always_run: true # Always runs.
        stages: [pre-commit] # Runs at the pre-commit stage.
```

## The Absolution Pattern: You May Commit

When you finally see "✓ Absolution granted" printed in your terminal, it's more than just a confirmation; it's a testament to the robustness of the YAMLGraph development pipeline and your adherence to its quality standards. It means your changes have passed through a comprehensive gauntlet of automated checks—from basic syntax and style to complex architectural rules, requirement traceability, and code health metrics. Only then is your code deemed worthy to become part of the project's history. This pattern ensures that every commit is a high-quality contribution, fostering a reliable and maintainable codebase.
