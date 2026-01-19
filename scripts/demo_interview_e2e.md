# Interview Demo - Human-in-the-Loop Walkthrough

This demo showcases the **interrupt node** feature for human-in-the-loop workflows.

## Files

| File | Purpose |
|------|---------|
| `graphs/interview-demo.yaml` | Graph definition with 2 interrupt nodes |
| `prompts/interview/personalized_greeting.yaml` | Prompt for LLM greeting |
| `scripts/demo_interview_e2e.py` | E2E test script |

## Running the Demo

```bash
# Automated test with verification
python scripts/demo_interview_e2e.py --verify

# Interactive mode (prompts for input)
python scripts/demo_interview_e2e.py --interactive
```

## Graph Structure

```
START → ask_name → ask_topic → generate_response → END
         (interrupt)  (interrupt)     (LLM)
```

## Step-by-Step Flow

### 1. Graph starts, hits first interrupt

```yaml
ask_name:
  type: interrupt
  message: "👋 What is your name?"
  resume_key: user_name
```

- Graph pauses, returns `__interrupt__` with the message
- Caller displays message to user
- Waits for `Command(resume="Alice")`

### 2. Resume → hits second interrupt

```yaml
ask_topic:
  type: interrupt  
  message: "🤔 What topic would you like to learn about?"
  resume_key: user_topic
```

- User's name (`Alice`) stored in `state.user_name`
- Graph pauses again at second interrupt
- Waits for `Command(resume="Python")`

### 3. Resume → LLM generates greeting

```yaml
generate_response:
  type: llm
  prompt: interview/personalized_greeting
  state_key: greeting
```

- `user_topic` (`Python`) stored in state
- LLM receives full state including `{user_name: "Alice", user_topic: "Python"}`
- Generates personalized greeting with learning resources

### 4. Graph completes

Final state contains:
```python
{
    "user_name": "Alice",
    "user_topic": "Python", 
    "greeting": "Hey Alice! So excited you're diving into Python..."
}
```

## Key Concepts

| Concept | How It's Used |
|---------|---------------|
| **Interrupt** | `type: interrupt` pauses for human input |
| **Resume** | `Command(resume=value)` continues execution |
| **Checkpointer** | SQLite stores state between pauses |
| **Thread ID** | Identifies the conversation session |
| **State flow** | Resume values flow to next nodes via state |

## Code Pattern

```python
from langgraph.types import Command

# Initial invoke - hits first interrupt
result = app.invoke({}, config)
question = result["__interrupt__"][0].value  # "👋 What is your name?"

# Resume with user input
result = app.invoke(Command(resume="Alice"), config)
question = result["__interrupt__"][0].value  # "🤔 What topic..."

# Resume again - completes
result = app.invoke(Command(resume="Python"), config)
greeting = result["greeting"]  # Final LLM response
```

## Requirements

- **Checkpointer**: Required for interrupt nodes (stores state between pauses)
- **Thread ID**: Required in config to identify the session
- **State declaration**: Resume keys must be declared in `state:` section

```yaml
checkpointer:
  type: sqlite
  path: ":memory:"

state:
  user_name: str
  user_topic: str
```

## The Magic

The `interrupt()` function from LangGraph:

1. **Pauses** execution at that point
2. **Returns** the payload in `result["__interrupt__"]`
3. On **resume**, returns the `Command(resume=...)` value
4. **Continues** execution from where it paused

This enables true human-in-the-loop workflows where the graph can ask questions and wait for human responses before proceeding.
