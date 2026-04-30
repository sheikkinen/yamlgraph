# State Machine

**Description:**

**Generated from:** `watcher-pipeline.yaml`
**Machine Name:** `watcher-pipeline`
**Version:** `0.2.0`
**Job Type:** `unknown`

---

## Main State Machine Flow

```mermaid
stateDiagram-v2
    [*] --> preflight

    %% PLANNING PHASE
    state PLANNINGPHASE {
        preflight --> worktree_setup : preflight_done
        worktree_setup --> planning : worktree_ready
        planning --> committing_plan : plan_done
        committing_plan --> researching : plan_committed
        researching --> committing_research : research_done
        committing_research --> writing_tests : research_committed
        writing_tests --> verifying_red : tests_written
        verifying_red --> judging : red_verified
        judging --> [*] : approve
        judging --> [*] : reject
        judging --> [*] : amend
        judging --> [*] : split
        planning --> [*] : timeout(600)
        researching --> [*] : timeout(600)
        writing_tests --> [*] : timeout(600)
        judging --> [*] : timeout(600)
    }

    %% ENFORCEMENT PHASE
    state ENFORCEMENTPHASE {
        [*] --> implementing
        implementing --> committing_implementation : implement_done
        committing_implementation --> testing_demo : implementation_committed
        testing_demo --> critiquing : test_demo_done
        critiquing --> changelog_gen : critique_done
        changelog_gen --> finalizing : changelog_done
        finalizing --> finalizing : precommit_retry
        finalizing --> pushing : finalize_done
        pushing --> creating_pr : pushed
        creating_pr --> waiting_ci : pr_created
        waiting_ci --> merging : ci_passed
        waiting_ci --> remediating_ci : ci_failed
        remediating_ci --> waiting_ci : remediated
        merging --> cleaning_up : merged
        cleaning_up --> [*] : cleaned_up
        implementing --> [*] : timeout(600)
        testing_demo --> [*] : timeout(600)
        critiquing --> [*] : timeout(600)
        remediating_ci --> [*] : timeout(600)
    }

    %% TERMINAL
    state TERMINAL {
        [*] --> completed
        [*] --> failed
        [*] --> stopped
        failed --> forensics : analyze
        forensics --> completed : forensics_done
        forensics --> failed : timeout(600)
    }

    %% Transitions
    PLANNINGPHASE --> ENFORCEMENTPHASE : approve
    PLANNINGPHASE --> TERMINAL : reject
    PLANNINGPHASE --> TERMINAL : amend
    PLANNINGPHASE --> TERMINAL : split
    ENFORCEMENTPHASE --> TERMINAL : cleaned_up
    PLANNINGPHASE --> TERMINAL : timeout(600)
    PLANNINGPHASE --> TERMINAL : timeout(600)
    PLANNINGPHASE --> TERMINAL : timeout(600)
    PLANNINGPHASE --> TERMINAL : timeout(600)
    ENFORCEMENTPHASE --> TERMINAL : timeout(600)
    ENFORCEMENTPHASE --> TERMINAL : timeout(600)
    ENFORCEMENTPHASE --> TERMINAL : timeout(600)
    ENFORCEMENTPHASE --> TERMINAL : timeout(600)

    stopped --> [*]
```

---

## Stop/Shutdown Flow

```mermaid
stateDiagram-v2
    %% Stop/Shutdown Flow
    stopped : ⏹️ stopped
    stopped --> [*]
    preflight --> stopped : stop
    worktree_setup --> stopped : stop
    planning --> stopped : stop
```

---

## States Overview

| State | Description | Key Actions |
|-------|-------------|-------------|
| `preflight` | Preflight | bash_context |
| `worktree_setup` | Worktree Setup | bash_context |
| `planning` | Planning | yamlgraph_async |
| `committing_plan` | Committing Plan | git_commit |
| `researching` | Researching | yamlgraph_async |
| `committing_research` | Committing Research | git_commit |
| `writing_tests` | Writing Tests | yamlgraph_async |
| `verifying_red` | Verifying Red | bash |
| `judging` | Judging | yamlgraph_async |
| `implementing` | Implementing | yamlgraph_async |
| `committing_implementation` | Committing Implementation | git_commit |
| `testing_demo` | Testing Demo | yamlgraph_async |
| `critiquing` | Critiquing | yamlgraph_async |
| `changelog_gen` | Changelog Gen | bash |
| `finalizing` | Finalizing | precommit |
| `pushing` | Pushing | bash |
| `creating_pr` | Creating Pr | bash_context |
| `waiting_ci` | Waiting Ci | bash_context |
| `remediating_ci` | Remediating Ci | yamlgraph_async |
| `merging` | Merging | bash |
| `cleaning_up` | Cleaning Up | bash |
| `completed` | Completed | bash |
| `failed` | Failed | bash |
| `forensics` | Forensics | yamlgraph_async |
| `stopped` | Stopped | N/A |

---

## Events Overview

| Event | Type | Description |
|-------|------|-------------|
| `preflight_done` | Success | Preflight Done |
| `worktree_ready` | Internal | Worktree Ready |
| `plan_done` | Success | Plan Done |
| `plan_committed` | Internal | Plan Committed |
| `research_done` | Success | Research Done |
| `research_committed` | Internal | Research Committed |
| `tests_written` | Internal | Tests Written |
| `red_verified` | Internal | Red Verified |
| `approve` | Internal | Approve |
| `reject` | Internal | Reject |
| `amend` | Internal | Amend |
| `split` | Internal | Split |
| `implement_done` | Success | Implement Done |
| `implementation_committed` | Internal | Implementation Committed |
| `test_demo_done` | Success | Test Demo Done |
| `critique_done` | Success | Critique Done |
| `changelog_done` | Success | Changelog Done |
| `finalize_done` | Success | Finalize Done |
| `precommit_retry` | Internal | Precommit Retry |
| `pushed` | Internal | Pushed |
| `pr_created` | Internal | Pr Created |
| `ci_passed` | Internal | Ci Passed |
| `ci_failed` | Error | Ci Failed |
| `remediated` | Internal | Remediated |
| `merged` | Internal | Merged |
| `cleaned_up` | Internal | Cleaned Up |
| `analyze` | Internal | Analyze |
| `forensics_done` | Success | Forensics Done |
| `stop` | Control | Stop |
| `timeout(600)` | Internal | Timeout(600) |

---

## Configuration Summary

- **States:** 25
- **Events:** 30
- **Transitions:** 38
- **Initial State:** `preflight`

---

*Generated by yaml_to_fsm.py*
