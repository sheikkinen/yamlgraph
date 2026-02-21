# Verified Search POC

**Pattern:** Evaluation-first agent design via prompt engineering, not graph config.

## The Concept

Agents often take actions without clear intent. This makes evaluation hard:
- What was the agent *trying* to do?
- Did it succeed by its own criteria?
- Why did it make those tool calls?

**Solution:** Force the agent to state a verification question *before* acting. Capture this as structured output for post-hoc analysis.

## Key Design Decision

The verification logic lives in **prompts**, not **graph config**:

```yaml
# ❌ WRONG - leaking prompt concern into orchestration
nodes:
  search:
    type: agent
    verification_question: "What specific fact am I verifying?"  # No!
```

```yaml
# ✅ CORRECT - graph stays clean, prompt defines reasoning pattern
nodes:
  search:
    type: agent
    prompt: verified_analyst  # Prompt teaches the reasoning pattern
```

## What This Enables

1. **LangSmith trace labeling** — The `verification_question` field becomes a span label
2. **Automated evaluation** — Compare stated question vs tools called vs result
3. **Drift detection** — Alert when agents claim one intent but demonstrate another
4. **Human review** — Auditors see stated intent, not just raw actions

## Run It

```bash
yamlgraph graph run examples/demos/verified-search/graph.yaml \
  --var query="How many node types does YAMLGraph support?" \
  --full
```

## Expected Output

```json
{
  "verification_question": "How many distinct node types exist in YAMLGraph?",
  "success_criteria": "A count and list of node types from the source code",
  "criteria_met": true,
  "confidence": 0.9,
  "findings": "YAMLGraph supports 10 node types: llm, router, agent, tool...",
  "reasoning_trace": "Searched constants.py for NodeType enum..."
}
```

## Layer Separation

| Layer | Responsibility |
|-------|---------------|
| **Graph YAML** | Structure: nodes, edges, state_key |
| **Prompt YAML** | Reasoning: how to think, what to output |
| **Schema fields** | Data shape: `verification_question`, `criteria_met` |

The graph doesn't know about verification questions. The prompt teaches the agent to ask them. The schema captures them. Clean separation.
