# Feature Request: Chaplain Documentation

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
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

- [ ] `.chaplain/README.md` created with comprehensive documentation
- [ ] Watcher2 pipeline architecture clearly explained
- [ ] All shell tools in `.chaplain/lib/watcher/*.sh` documented
- [ ] Usage examples for both pipeline and individual tools
- [ ] Environment variables and configuration documented
- [ ] Troubleshooting section included
- [ ] Documentation follows project markdown style
- [ ] Cross-references to related files (FR-273, etc.)

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