"""Tests for yamlgraph.utils.template module - Variable extraction and validation."""

import pytest


class TestExtractVariables:
    """Tests for extract_variables function."""

    @pytest.mark.req("REQ-YG-013")
    def test_extract_simple_variables(self):
        """Should extract {var} placeholders."""
        from yamlgraph.utils.template import extract_variables

        template = "Hello {name}, your style is {style}."
        variables = extract_variables(template)
        assert variables == {"name", "style"}

    @pytest.mark.req("REQ-YG-013")
    def test_extract_single_variable(self):
        """Should extract a single variable."""
        from yamlgraph.utils.template import extract_variables

        template = "Welcome {user}!"
        variables = extract_variables(template)
        assert variables == {"user"}

    @pytest.mark.req("REQ-YG-013")
    def test_extract_no_variables(self):
        """Should return empty set when no variables."""
        from yamlgraph.utils.template import extract_variables

        template = "No variables here"
        variables = extract_variables(template)
        assert variables == set()

    @pytest.mark.req("REQ-YG-013")
    def test_extract_duplicate_variables(self):
        """Should deduplicate variables."""
        from yamlgraph.utils.template import extract_variables

        template = "{name} and {name} again"
        variables = extract_variables(template)
        assert variables == {"name"}

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_variable(self):
        """Should extract {{ var }} Jinja2 variables."""
        from yamlgraph.utils.template import extract_variables

        template = "Hello {{ name }}!"
        variables = extract_variables(template)
        assert "name" in variables

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_variable_with_field_access(self):
        """Should extract base variable from {{ var.field }}."""
        from yamlgraph.utils.template import extract_variables

        template = "User: {{ user.name }}"
        variables = extract_variables(template)
        assert "user" in variables

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_loop_variable(self):
        """Should extract iterable from {% for x in items %}."""
        from yamlgraph.utils.template import extract_variables

        template = "{% for item in items %}{{ item.name }}{% endfor %}"
        variables = extract_variables(template)
        assert "items" in variables
        # 'item' is a loop variable, not a required input
        assert "item" not in variables

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_if_variable(self):
        """Should extract variable from {% if condition %}."""
        from yamlgraph.utils.template import extract_variables

        template = "{% if show_details %}Details here{% endif %}"
        variables = extract_variables(template)
        assert "show_details" in variables

    @pytest.mark.req("REQ-YG-013")
    def test_exclude_state_variable(self):
        """State is injected by framework, not a required input."""
        from yamlgraph.utils.template import extract_variables

        template = "{{ state.topic }}"
        variables = extract_variables(template)
        # state is excluded - it's injected by node_factory
        assert "state" not in variables

    @pytest.mark.req("REQ-YG-013")
    def test_exclude_jinja2_builtins(self):
        """Should exclude Jinja2 builtins like loop, range."""
        from yamlgraph.utils.template import extract_variables

        template = "{% for i in range(10) %}{{ loop.index }}{% endfor %}"
        variables = extract_variables(template)
        assert "range" not in variables
        assert "loop" not in variables

    @pytest.mark.req("REQ-YG-013")
    def test_exclude_jinja2_keywords(self):
        """Should exclude Jinja2 keywords: not, and, or, is, in."""
        from yamlgraph.utils.template import extract_variables

        template = "{% if not seeds %}empty{% endif %}{% if x and y %}{% endif %}"
        variables = extract_variables(template)
        assert "not" not in variables
        assert "and" not in variables
        assert "seeds" in variables
        assert "x" in variables

    @pytest.mark.req("REQ-YG-013")
    def test_exclude_jinja2_filters(self):
        """Should exclude Jinja2 filters like |length, |join, |default."""
        from yamlgraph.utils.template import extract_variables

        template = "{% if history and history|length > 0 %}has history{% endif %}"
        variables = extract_variables(template)
        assert "history" in variables
        assert "length" not in variables, "length is a filter, not a variable"

    @pytest.mark.req("REQ-YG-013")
    def test_exclude_field_access_in_condition(self):
        """Should not treat article.content as requiring 'content' variable."""
        from yamlgraph.utils.template import extract_variables

        template = (
            "{% for article in articles %}"
            "{% if article.content %}{{ article.content }}{% endif %}"
            "{% endfor %}"
        )
        variables = extract_variables(template)
        assert "articles" in variables
        assert "content" not in variables

    @pytest.mark.req("REQ-YG-013")
    def test_mixed_simple_and_jinja2(self):
        """Should handle templates mixing {var} and {{ var }}."""
        from yamlgraph.utils.template import extract_variables

        template = "Simple {name} and Jinja2 {{ topic }}"
        variables = extract_variables(template)
        assert "name" in variables
        assert "topic" in variables

    # FR-064: AST-based extraction tests (edge cases regex cannot handle)

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_comment(self):
        """Variables inside Jinja2 comments should be ignored."""
        from yamlgraph.utils.template import extract_variables

        template = "{# {{ foo }} #}{{ bar }}"
        variables = extract_variables(template)
        assert variables == {"bar"}

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_raw_block(self):
        """Variables inside {% raw %} blocks should be ignored."""
        from yamlgraph.utils.template import extract_variables

        template = "{% raw %}{{ not_a_var }}{% endraw %}{{ real }}"
        variables = extract_variables(template)
        assert variables == {"real"}

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_macro(self):
        """Macro parameters should not be extracted; call arguments should."""
        from yamlgraph.utils.template import extract_variables

        template = "{% macro m(a) %}{{ a }}{% endmacro %}{{ m(x) }}"
        variables = extract_variables(template)
        assert variables == {"x"}

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_ternary(self):
        """Ternary expressions should extract all three variables."""
        from yamlgraph.utils.template import extract_variables

        template = "{{ x if cond else y }}"
        variables = extract_variables(template)
        assert variables == {"x", "cond", "y"}

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_dict_literal(self):
        """Dict literal keys should not be extracted; values should."""
        from yamlgraph.utils.template import extract_variables

        template = '{{ {"key": value}.key }}'
        variables = extract_variables(template)
        assert variables == {"value"}

    @pytest.mark.req("REQ-YG-013")
    def test_extract_jinja2_set_stmt(self):
        """{% set %} creates local; the source variable should be extracted."""
        from yamlgraph.utils.template import extract_variables

        template = "{% set local = external %}{{ local }}"
        variables = extract_variables(template)
        assert variables == {"external"}

    @pytest.mark.req("REQ-YG-216")
    def test_extract_variables_set_in_nested_for_if(self):
        """{% set %} inside {% for %}{% if %} must not appear as required."""
        from yamlgraph.utils.template import extract_variables

        template = "{% for i in items %}{% if i %}{% set x = i %}{{ x }}{% endif %}{% endfor %}"
        result = extract_variables(template)
        assert result == {"items"}, f"Expected {{'items'}}, got {result}"

    @pytest.mark.req("REQ-YG-216")
    def test_extract_variables_set_before_use_still_reported(self):
        """A variable genuinely undeclared must still be reported even if a
        {% set %} of the same name exists.  Verifies the subtraction does not
        silently drop real undeclared vars.

        NOTE: Jinja2's find_undeclared_variables already resolves top-level
        {% set x = y %} correctly (y is reported, x is not), so this test
        confirms the combined fix does not regress that behaviour.
        """
        from yamlgraph.utils.template import extract_variables

        # x is assigned via set, but y is never assigned — y must remain in result
        template = "{% set x = y %}{{ x }}"
        result = extract_variables(template)
        assert "y" in result, f"Expected 'y' in result, got {result}"
        assert "x" not in result, f"Expected 'x' not in result, got {result}"


class TestValidateVariables:
    """Tests for validate_variables function."""

    @pytest.mark.req("REQ-YG-013")
    def test_validate_all_provided(self):
        """Should not raise when all variables provided."""
        from yamlgraph.utils.template import validate_variables

        template = "Hello {name}, style: {style}"
        # Should not raise
        validate_variables(template, {"name": "World", "style": "formal"}, "greet")

    @pytest.mark.req("REQ-YG-013")
    def test_validate_missing_single_variable(self):
        """Should raise ValueError for single missing variable."""
        from yamlgraph.utils.template import validate_variables

        template = "Hello {name}, style: {style}"
        with pytest.raises(ValueError, match="Missing required variable.*name"):
            validate_variables(template, {"style": "formal"}, "greet")

    @pytest.mark.req("REQ-YG-013")
    def test_validate_missing_multiple_variables(self):
        """Should list ALL missing variables in error."""
        from yamlgraph.utils.template import validate_variables

        template = "Hello {name}, style: {style}"
        with pytest.raises(ValueError) as exc_info:
            validate_variables(template, {}, "greet")
        error_msg = str(exc_info.value)
        assert "name" in error_msg
        assert "style" in error_msg

    @pytest.mark.req("REQ-YG-013")
    def test_validate_extra_variables_ok(self):
        """Should not raise when extra variables provided."""
        from yamlgraph.utils.template import validate_variables

        template = "Hello {name}"
        # Should not raise - extra vars are fine
        validate_variables(template, {"name": "World", "extra": "ignored"}, "greet")

    @pytest.mark.req("REQ-YG-013")
    def test_validate_prompt_name_in_error(self):
        """Error message should include prompt name."""
        from yamlgraph.utils.template import validate_variables

        template = "Hello {name}"
        with pytest.raises(ValueError, match="greet"):
            validate_variables(template, {}, "greet")

    @pytest.mark.req("REQ-YG-013")
    def test_validate_empty_template(self):
        """Should not raise for template without variables."""
        from yamlgraph.utils.template import validate_variables

        template = "No variables here"
        # Should not raise
        validate_variables(template, {}, "static")

    @pytest.mark.req("REQ-YG-013")
    def test_validate_jinja2_template(self):
        """Should validate Jinja2 templates correctly."""
        from yamlgraph.utils.template import validate_variables

        template = "{% for item in items %}{{ item }}{% endfor %}"
        with pytest.raises(ValueError, match="items"):
            validate_variables(template, {}, "list_template")


class TestExecutePromptValidation:
    """Integration tests for validation in execute_prompt."""

    @pytest.mark.req("REQ-YG-013")
    def test_execute_prompt_raises_on_missing_variable(self):
        """Should raise clear error when required variable is missing."""
        from yamlgraph.executor import execute_prompt

        with pytest.raises(ValueError, match="Missing required variable.*name"):
            execute_prompt(
                prompt_name="greet",
                variables={"style": "formal"},  # Missing 'name'
            )

    @pytest.mark.req("REQ-YG-013")
    def test_execute_prompt_lists_all_missing_variables(self):
        """Error should list ALL missing variables, not just first."""
        from yamlgraph.executor import execute_prompt

        with pytest.raises(ValueError) as exc_info:
            execute_prompt(
                prompt_name="greet",
                variables={},  # Missing both 'name' and 'style'
            )
        error_msg = str(exc_info.value)
        assert "name" in error_msg
        assert "style" in error_msg
