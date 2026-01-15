"""Tests for showcase.models.state module."""

import ast
from pathlib import Path

from pydantic import BaseModel

from showcase.models import create_initial_state


class TestCreateInitialState:
    """Tests for create_initial_state function."""

    def test_basic_creation(self):
        """Basic state creation with required fields."""
        state = create_initial_state(topic="test topic")
        assert state["topic"] == "test topic"
        assert state["style"] == "informative"
        assert state["word_count"] == 300

    def test_custom_parameters(self):
        """State creation with custom parameters."""
        state = create_initial_state(
            topic="AI",
            style="casual",
            word_count=500,
            thread_id="custom123",
        )
        assert state["topic"] == "AI"
        assert state["style"] == "casual"
        assert state["word_count"] == 500
        assert state["thread_id"] == "custom123"

    def test_auto_generated_thread_id(self):
        """Thread ID should be auto-generated if not provided."""
        state = create_initial_state(topic="test")
        assert state["thread_id"] is not None
        assert len(state["thread_id"]) == 16  # 16 hex chars for better uniqueness

    def test_initial_values_are_none(self):
        """Pipeline outputs should be None initially."""
        state = create_initial_state(topic="test")
        # Framework fields
        assert state["error"] is None
        # Demo-specific fields are not included by default (generic state)

    def test_initial_step_is_init(self):
        """Current step should be 'init' initially."""
        state = create_initial_state(topic="test")
        assert state["current_step"] == "init"


class TestShowcaseStateTypedDict:
    """Tests for ShowcaseState TypedDict."""

    def test_state_is_dict(self):
        """State should be a dict."""
        state = create_initial_state(topic="test")
        assert isinstance(state, dict)

    def test_state_allows_updates(self):
        """State should allow field updates."""
        state = create_initial_state(topic="test")
        state["current_step"] = "generate"
        state["error"] = "Test error"
        assert state["current_step"] == "generate"
        assert state["error"] == "Test error"


class TestStateModuleDecoupling:
    """Tests to ensure state module is decoupled from demo-specific models."""

    def test_state_module_has_no_demo_imports(self):
        """State module should not import demo-specific models."""
        source = Path("showcase/models/state.py").read_text()
        tree = ast.parse(source)

        demo_models = {
            "Analysis",
            "GeneratedContent",
            "ToneClassification",
            "DraftContent",
            "Critique",
            "GitReport",
            "Greeting",
            "PipelineResult",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    assert (
                        alias.name not in demo_models
                    ), f"Found demo import: {alias.name}"

    def test_content_state_accepts_any_pydantic_model(self):
        """State should work with any Pydantic model, not just specific ones."""
        from showcase.models.state import ContentState

        class CustomOutput(BaseModel):
            custom_field: str

        state: ContentState = {
            "topic": "test",
            "generated": CustomOutput(custom_field="works"),
        }
        assert state["generated"].custom_field == "works"

    def test_router_state_accepts_any_classification(self):
        """RouterState should work with any classification model."""
        from showcase.models.state import RouterState

        class CustomClassification(BaseModel):
            category: str
            score: float

        state: RouterState = {
            "message": "test",
            "classification": CustomClassification(category="positive", score=0.9),
        }
        assert state["classification"].category == "positive"

    def test_reflexion_state_accepts_any_draft_critique(self):
        """ReflexionState should work with any draft/critique models."""
        from showcase.models.state import ReflexionState

        class CustomDraft(BaseModel):
            text: str

        class CustomCritique(BaseModel):
            rating: int

        state: ReflexionState = {
            "topic": "test",
            "current_draft": CustomDraft(text="draft"),
            "critique": CustomCritique(rating=5),
        }
        assert state["current_draft"].text == "draft"
        assert state["critique"].rating == 5
