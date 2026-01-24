# Multi-Step Form

> Multi-step form with human review using interrupt pattern.

## Usage

```bash
yamlgraph graph run graph.yaml --var topic="Product feedback survey"
```

This is an interactive pipeline - it will pause for human input.

## Pipeline Flow

1. **generate_questions** - Generate survey questions
2. **review_questions** (interrupt) - Pause for human review
3. **finalize_form** - Create final form with approved questions

## Patterns Used

- Interrupt (human-in-the-loop)
- Linear (generate → review → finalize)
