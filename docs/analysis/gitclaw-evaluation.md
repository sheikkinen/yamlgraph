# GitClaw Evaluation

Repository: https://github.com/sheikkinen/gitclaw

Reviewed: 2026-08-20

## Executive summary

GitClaw is a genuinely interesting prototype with unusually good operational discipline for an autonomous coding-agent repository, but its security boundary is still fundamentally **trusted operator + trusted model/vendor**.

Approximate assessment:

- **8/10** as an experimental architecture
- **6/10** as something I would fork and run unattended
- **3–4/10** as a multi-user/general-purpose agent platform

The concept is clear and coherent: a GitHub issue becomes a small recurring feature through a `plan → judge → enforce → review` pipeline, implemented as a YAMLGraph graph, after which cron executes accepted features daily and commits the outputs.

## What works especially well

The strongest design choice is that GitClaw treats the LLM as an untrusted-ish workflow participant rather than as the state machine itself. Decisions are materialized as artifacts such as `judgement.md` and `review.md`; verdicts are parsed mechanically; illegal state transitions are rejected; and changed paths are independently checked before the final commit.

This is a strong separation between probabilistic reasoning and deterministic control.

### Ledger and state machine

The append-only JSONL ledger provides explicit states and transitions such as:

`seen → planned → judged_approved → enforced → reviewed_approved → pushed → closed`

It also includes recovery/failure states. The transition table is frozen by tests rather than existing only as informal convention.

This provides something particularly valuable in LLM automation: a durable explanation of where execution was when something went wrong.

### Containment

`tools/contain.py` normalizes paths and only permits modifications under the active `features/<feature>/` directory plus the ledger. It explicitly rejects traversal and verifies both sides of renames.

Tests cover modifications to workflows, prompts, tools, package files, README, and similar files as forbidden paths.

This is substantially stronger than depending on a reviewer-agent prompt saying “please don't touch anything else.”

### Intake security

On issue creation, only `OWNER`, `MEMBER`, or `COLLABORATOR` authors can trigger the secret-bearing LLM workflow; `CONTRIBUTOR` is deliberately excluded.

For the label path, the workflow verifies that the sender applying `gitclaw` is the repository owner rather than merely checking whether the label exists.

This avoids several common GitHub Actions privilege-escalation mistakes.

### Defensive details

Feature slugs strip shell-looking characters and have bounded length, with injection-oriented tests.

The cron runner isolates feature failures rather than aborting when the first graph fails. Successful outputs can therefore be committed before the overall workflow surfaces a failure.

These details matter once automation has been running for months rather than minutes.

## Main security limitation

The fundamental weakness is that **containment controls the eventual Git diff, not the agent process**.

Copilot sessions get broad tool access while credentials exist in the runner environment. A sufficiently malicious or prompt-injected agent could therefore potentially do damage before `contain.py` examines the working tree—for example by reading secrets, making external requests, invoking `gh`, or pushing directly.

The containment gate should therefore be understood as a **repository-integrity control, not an execution sandbox**.

A useful concise formulation would be:

> Containment constrains what GitClaw's orchestrated happy path commits; it does not constrain what the Copilot process can execute.

## Reproducibility and supply-chain risk

Both workflows install runtime dependencies without version pins, for example:

```text
npm install -g @github/copilot
pip install yamlgraph
```

This means a GitClaw instance can behave differently tomorrow without any repository commit changing.

For a project whose appeal is auditable-by-construction automation, this is the most obvious mismatch between architecture and implementation.

Highest-priority cleanup:

```text
yamlgraph==<known-good-version>
@github/copilot@<known-good-version>
```

GitHub Actions should ideally also be pinned by full commit SHA rather than mutable major-version tags such as `actions/checkout@v4`.

## Feature graphs as executable artifacts

Once a feature graph passes intake review, cron repeatedly executes it with API credentials available in the workflow environment.

This means the real long-lived executable artifact is:

```text
features/*/graph.yaml
```

not merely the generated textual output.

Any future mechanism that modifies feature graphs should therefore route those modifications through the same security and review process as initial creation.

## Recommended capability model

A strong architectural evolution would be explicit per-feature capabilities, for example:

```yaml
capabilities:
  network:
    - api.openweathermap.org
  filesystem:
    read:
      - features/weather/**
    write:
      - outputs/**
  secrets:
    - WEATHER_API_KEY
```

The runtime would enforce this manifest mechanically.

That changes the security model from:

```text
LLM can do anything → check resulting diff
```

toward:

```text
LLM can only invoke declared capabilities → check resulting diff
```

This would be a substantial security improvement.

## YAMLGraph's role

GitClaw provides a convincing use case for YAMLGraph beyond simply chaining prompts.

Here YAMLGraph acts as an **auditable execution contract between probabilistic agents and deterministic GitHub automation**.

The layering is approximately:

```text
GitHub
  issue / schedule
        │
        ▼
GitHub Actions             ← privilege + trigger boundary
        │
        ▼
gitclaw.yaml               ← orchestration / agent workflow
        │
   ┌────┴────┐
   ▼         ▼
Copilot    deterministic tools
agents     ledger / contain / slug
   │
   ▼
feature graph              ← generated executable contract
   │
   ▼
YAMLGraph runtime
   │
   ▼
daily output
```

This separation is one of GitClaw's strongest architectural characteristics.

The project therefore supports a broader YAMLGraph thesis: **graphs as auditable contracts** is considerably more compelling than graphs merely as prettier prompt chains.

## Judge/reviewer independence

GitClaw has two separate semantic decision stages, but if both stages use the same provider/model family they are not independent failure domains.

A stronger configuration could allow provider diversity:

```text
Copilot author
      ↓
Claude/GPT reviewer
      ↓
deterministic policy checks
```

or:

```text
author → semantic reviewer → security reviewer → mechanical gate
```

The current policy of allowing only one remediation lap is good. Unlimited self-correction loops make cost and behavior increasingly difficult to bound.

## Testing

Testing is good for the project's size but primarily concentrated around deterministic safety infrastructure: containment, ledger behavior, and intake helpers.

The next useful layer would be adversarial workflow-level fixtures covering cases such as:

- prompt-injected issue text
- malicious feature names
- graph attempting out-of-scope writes
- malformed verdicts
- interrupted runs between ledger transitions
- poisoned graph output
- network exfiltration attempts
- concurrent cron/intake pushes

These tests would probe the actual trust model rather than merely increasing line coverage.

## Concurrency and consistency

The intake workflow serializes intake runs through one concurrency group, which makes sense because the ledger is shared state.

Cron has its own single concurrency group. Intake and cron can therefore still interact through Git pushes, making `pull --rebase` part of the consistency model.

This is reasonable for a small template repository. At larger scale, ledger/output writes would benefit from explicit cross-workflow serialization or separation through branches/artifacts.

## Scorecard

| Area | Score | Comment |
|---|---:|---|
| Concept | **9/10** | Extremely clear small-system idea |
| Architecture | **8.5/10** | Strong deterministic/LLM separation |
| Auditability | **9/10** | Ledger + artifacts + graph representation |
| Code complexity | **8/10** | Refreshingly small |
| Tests | **7/10** | Good safety-unit tests; needs adversarial integration tests |
| Reproducibility | **5/10** | Unpinned runtime is the glaring issue |
| Single-user security | **7/10** | Reasonable given stated assumptions |
| Adversarial security | **3/10** | Full-shell agent + secrets remains decisive |
| README honesty | **9.5/10** | Risks are unusually explicitly documented |
| Project maturity | **6/10** | Early-stage repository without release maturity |

## Recommended priorities

1. **Pin the entire runtime and supply chain.**
2. **Introduce a feature capability manifest and runtime sandbox/enforcement.**
3. **Add adversarial end-to-end tests.**
4. **Optionally separate author and reviewer providers/models.**
5. **Expose graph/runtime provenance in every committed output.**
6. **Consider stronger cross-workflow consistency if usage grows.**

## Overall assessment

GitClaw can be characterized as **an agentic GitHub bot designed by someone who has already been burned by agentic GitHub bots**.

The interesting innovation is not that an LLM can generate software from an issue. That capability is increasingly commonplace. The interesting part is the attempt to make autonomous generation **bounded, stateful, replay-understandable, and mechanically inspectable**.

More fundamentally, GitClaw is not really just an “AI coding agent.” It is a **small governance system around one**.

That is the more interesting direction.

## References

- GitClaw repository: https://github.com/sheikkinen/gitclaw
- Orchestrator: https://github.com/sheikkinen/gitclaw/blob/main/gitclaw.yaml
- Ledger: https://github.com/sheikkinen/gitclaw/blob/main/tools/ledger.py
- Containment: https://github.com/sheikkinen/gitclaw/blob/main/tools/contain.py
- Containment tests: https://github.com/sheikkinen/gitclaw/blob/main/tests/test_contain.py
- Intake workflow: https://github.com/sheikkinen/gitclaw/blob/main/.github/workflows/intake.yml
- Cron workflow: https://github.com/sheikkinen/gitclaw/blob/main/.github/workflows/cron.yml
- Cron runner: https://github.com/sheikkinen/gitclaw/blob/main/tools/cron_run.py
- Tests: https://github.com/sheikkinen/gitclaw/tree/main/tests
