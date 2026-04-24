# Feature Request: Chaplain Documentation

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-24

## Summary

Document the watcher2 pipeline orchestrator and its shell library in `.chaplain/README.md` to provide a comprehensive guide for the automated pipeline system and its reusable shell tools.

## Value Statement

Developers and maintainers get clear documentation of the watcher2 architecture and shell primitives, reducing onboarding time and enabling independent use of pipeline components.

## Problem

The `.chaplain/` directory contains a sophisticated automation pipeline (watcher2) and shell library that handles:
- Automated feature request processing
- Worktree lifecycle management
- PR creation, CI waiting, and merge automation
- Complex shell operations for git branch management

However, this system lacks documentation, making it difficult to:
1. Understand the overall watcher2 workflow
2. Use individual shell tools independently
3. Debug pipeline failures
4. Extend or modify the system
5. Onboard new contributors to the automation infrastructure

The shell library in `.chaplain/lib/watcher/*.sh` contains reusable primitives (worktree creation, branch management, PR operations) that could be invoked independently but lack usage documentation.

## Proposed Solution

Create `.chaplain/README.md` with comprehensive documentation covering:

### 1. Watcher2 Pipeline Overview
- Architecture: 4-phase pipeline (Plan → Research → Acceptance → Judge → Enforce)
- Flow diagram of the complete cycle
- State management and session chaining
- Error handling and forensic preservation

### 2. Shell Library Reference
Document each tool in `.chaplain/lib/watcher/*.sh`:

#### Core Worktree Operations
- `worktree_setup.sh` - Create isolated worktrees with branch management
- `worktree_teardown.sh` - Clean removal with corruption guards
- `preflight.sh` - Pre-flight validation and cleanup

#### Git/GitHub Integration
- `create_pr.sh` - PR creation with reuse logic
- `merge_pr.sh` - Squash merge with state verification
- `wait_ci.sh` - CI status polling
- `post_merge.sh` - Post-merge cleanup

#### Pipeline Support
- `inbox_sync.sh` - Remote issue synchronization
- `metrics.sh` - Performance tracking
- Environment variables and configuration

### 3. Usage Examples
- Running watcher2 daemon
- Invoking individual shell tools standalone
- Environment setup and dependencies
- Troubleshooting common issues

### 4. Architecture Details
- Directory structure and purposes
- State files and logging
- Integration with YAMLGraph execution
- Pre-commit hook cascade handling

## Acceptance Criteria

- [x] `.chaplain/README.md` created with comprehensive documentation
- [x] Watcher2 pipeline architecture clearly explained
- [x] All shell tools in `.chaplain/lib/watcher/*.sh` documented
- [x] Usage examples for both pipeline and individual tools
- [x] Environment variables and configuration documented
- [x] Troubleshooting section included
- [x] Documentation follows project markdown style
- [x] Cross-references to related files (FR-273, etc.)

## Alternatives Considered

1. **Inline code comments only** - Rejected because shell scripts are hard to navigate and comments don't provide high-level architecture view
2. **Separate docs/ file** - Rejected because documentation should be co-located with the code it documents
3. **Wiki or external docs** - Rejected because documentation should be version-controlled with the code

## Related

- FR-273: Watcher2 pipeline implementation
- `.chaplain/watcher2.sh` - Main orchestrator script
- `.chaplain/lib/watcher/*.sh` - Shell tool library
- GitHub Issues with `chaplain` label - Remote submission mechanism
- FR-139: Worktree corruption fixes
- FR-174: Python path cleanup
- FR-241: Editable install validation

## Implementation Notes

The documentation should capture the current state of the watcher2 system as implemented in FR-273, including:
- The 8-step enforcement pipeline
- Shell steps between YAMLGraph executions
- State file management and session chaining
- Error handling patterns and failure preservation
- Integration with GitHub CLI and git worktrees

This documentation will serve as both user guide and maintenance reference for the automation infrastructure.

## Research Brief

### Competitive Landscape

Most CI/CD and automation frameworks provide comprehensive documentation for their architecture and primitives:

- **GitHub Actions** features detailed documentation covering workflow syntax, runner configuration, and marketplace actions with clear usage examples
- **Tekton** provides structured docs for pipelines, tasks, and CLI components with conceptual overviews and installation guides
- **LangGraph** offers well-organized documentation covering core benefits, execution patterns, and ecosystem integration
- **CrewAI** maintains clear documentation for agents, flows, and enterprise features with quickstart guides and examples

However, these frameworks differ from YAMLGraph's chaplain system in that they are primarily end-user tools, while the chaplain is internal automation infrastructure. The competitive analysis reveals that **documenting internal automation tools follows the same patterns as documenting public APIs** - architecture overviews, component references, usage examples, and troubleshooting guides are universal best practices.

### Existing Abstractions

The YAMLGraph codebase shows strong patterns around documentation:

- **README-driven development**: Every example and demo includes comprehensive README.md files (80+ found)
- **Reference documentation**: `reference/` directory contains structured guides for core concepts
- **Inline documentation**: Shell scripts contain header comments explaining purpose and environment variables
- **Architecture documentation**: `ARCHITECTURE.md` provides high-level design philosophy and patterns
- **Process documentation**: `CLAUDE.md` contains development workflows and commands

The chaplain system follows these established patterns but lacks the central README that ties everything together.

### Diary Precedents

Key diary insights relevant to this proposal:

- **Documentation drift trap** (2026-03-08): Asymmetric coverage across instruction files led to silent capability discovery failures - documentation should be co-located and comprehensive
- **Infrastructure self-exempt trap** (2026-04-09): Meta-tooling often lacks the same documentation rigor applied to user-facing features
- **README as minimum viable documentation** (2026-04-19): The reference documentation, not just example READMEs, establishes the baseline for pattern understanding
- **Audit as ritual trap** (2026-03-09): Multiple audits without fixes indicates process failure - documentation prevents this by making systems inspectable

The pattern: **undocumented infrastructure becomes unmaintainable infrastructure**.

### Usage Evidence

- Existing graphs using related abstractions: 17 (automation/watcher/chaplain references across examples and ebook pipeline)
- Shell script references in examples: 7 files
- README.md files in project: 80+ (indicating established documentation patterns)
- Real-world use cases beyond the proposal: The watcher2 system is actively used for automated feature request processing, with the chaplain daemon running continuously

### Classification Signal

- **Abstraction level**: pattern (infrastructure documentation)
- **Recommended approach**: document
- **Key risk**: Without documentation, the sophisticated watcher2 system remains a "black box" limiting contributor onboarding and debugging capability
