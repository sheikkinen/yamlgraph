# Feature Request: First-Class Template Bootstrap (`yamlgraph project init`)

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 5 days
**Requested:** 2026-02-17

## Summary

Promote the lesson generator's `render_templates.py` → project directory pattern into a first-class YAMLGraph CLI feature: `yamlgraph project init --template=<name> --var key=value`. Graphs, prompts, and nodes are templated with Jinja2 and instantiated into a ready-to-run project.

## Problem

Only 1 of 10 YAMLGraph pipelines has a bootstrap phase: the lesson generator uses `bootstrap.yaml` + `render_templates.py` + Jinja2 templates to instantiate subject-specific prompts from generic templates. Every other pipeline hardcodes its prompts. The innovators toolkit uses 15 fixed prompts. The novel generator uses 7. None can be trivially re-aimed at a new domain without editing YAML files.

The lesson generator's bootstrap pattern is the most powerful thing in the ecosystem — it enables one-command instantiation of a new subject (`psykologia`, `biologia`, etc.) from shared templates. But it's hand-coded and not extractable. A new user wanting a similar pipeline would have to reverse-engineer the pattern from scratch.

## Proposed Solution

### CLI Interface

```bash
# List available templates
yamlgraph project list

# Initialize a new project from a template
yamlgraph project init lesson-generator \
  --var subject=biologia \
  --var language=fi \
  --output ./biologia-project

# Run the initialized project
yamlgraph project run ./biologia-project
```

### Template Structure

Templates live in a `templates/` directory (local or registry):

```
templates/
  lesson-generator/
    template.yaml          # Template metadata + required variables
    graphs/
      prepare.yaml.j2      # Jinja2-templated graph
      generate.yaml.j2
    prompts/
      generate_lesson.yaml.j2
      review_lesson.yaml.j2
    nodes/
      load_data.py.j2
      save_lessons.py.j2
```

### Template Metadata

```yaml
# templates/lesson-generator/template.yaml
name: lesson-generator
description: "Generate structured lesson plans for any subject"
version: "1.0"
variables:
  subject:
    type: str
    required: true
    description: "Subject name (e.g. psykologia, biologia)"
  language:
    type: str
    default: "fi"
    description: "Output language code"
  lessons_per_module:
    type: int
    default: 15
    description: "Target lessons per module"
```

### Rendering Pipeline

1. `yamlgraph project init` loads `template.yaml`, validates required variables
2. All `.j2` files are rendered with Jinja2 using provided variables
3. Rendered files are written to the output directory (without `.j2` extension)
4. Non-template files (data, configs) are copied as-is
5. A `project.yaml` manifest is written with the template name, variables, and timestamp

## Acceptance Criteria

- [ ] `yamlgraph project init` CLI command creates a project from a template
- [ ] `yamlgraph project list` lists available templates with descriptions and required vars
- [ ] Template variables are validated against `template.yaml` metadata
- [ ] Missing required variables produce clear error messages
- [ ] `.j2` files are rendered with Jinja2 and written without the `.j2` extension
- [ ] Non-template files are copied verbatim
- [ ] Generated project is immediately runnable with `yamlgraph graph run`
- [ ] At least one built-in template (lesson-generator) ships with YAMLGraph
- [ ] Tests added with `@pytest.mark.req` tags
- [ ] Documentation added to `reference/` with template authoring guide

## Alternatives Considered

- **Cookiecutter integration:** Use cookiecutter for project scaffolding. Adds external dependency and doesn't integrate with YAMLGraph's existing Jinja2 engine.
- **CLI wizard/questionnaire:** Interactive prompting for template variables. Could be layered on later but the `--var` flag approach is more scriptable and CI-friendly.
- **Git-based templates:** Templates as separate git repos. More flexible distribution but higher setup friction for users.

## Related

- Lesson generator bootstrap: `projects/opinto-ohjaus/bootstrap.yaml` + `render_templates.py`
- Existing Jinja2 support in prompts: `reference/prompt-yaml.md`
- Diary entry: "The Constraint Shift" — Observation 2
