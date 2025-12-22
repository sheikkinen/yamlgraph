"""YAML Prompt Executor - Unified interface for LLM calls.

This module provides a simple, reusable executor for YAML-defined prompts
with support for structured outputs via Pydantic models.
"""

from typing import Type, TypeVar

import yaml
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from showcase.config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    PROMPTS_DIR,
)

T = TypeVar("T", bound=BaseModel)


def load_prompt(prompt_name: str) -> dict:
    """Load a YAML prompt template.
    
    Args:
        prompt_name: Name of the prompt file (without .yaml extension)
        
    Returns:
        Dictionary with 'system' and 'user' keys
    """
    prompt_path = PROMPTS_DIR / f"{prompt_name}.yaml"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    
    with open(prompt_path) as f:
        return yaml.safe_load(f)


def format_prompt(template: str, variables: dict) -> str:
    """Format a prompt template with variables.
    
    Args:
        template: Template string with {variable} placeholders
        variables: Dictionary of variable values
        
    Returns:
        Formatted string
    """
    return template.format(**variables)


def create_llm(temperature: float = DEFAULT_TEMPERATURE) -> ChatAnthropic:
    """Create a configured LLM instance.
    
    Args:
        temperature: Sampling temperature (0.0 to 1.0)
        
    Returns:
        Configured ChatAnthropic instance
    """
    return ChatAnthropic(
        model=DEFAULT_MODEL,
        temperature=temperature,
        max_tokens=DEFAULT_MAX_TOKENS,
    )


def execute_prompt(
    prompt_name: str,
    variables: dict | None = None,
    output_model: Type[T] | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
) -> T | str:
    """Execute a YAML prompt with optional structured output.
    
    Args:
        prompt_name: Name of the prompt file (without .yaml)
        variables: Variables to substitute in the template
        output_model: Optional Pydantic model for structured output
        temperature: LLM temperature setting
        
    Returns:
        Parsed Pydantic model if output_model provided, else raw string
        
    Example:
        >>> result = execute_prompt(
        ...     "greet",
        ...     variables={"name": "World", "style": "formal"},
        ...     output_model=Greeting,
        ... )
        >>> print(result.message)
    """
    variables = variables or {}
    
    # Load and format prompt
    prompt_config = load_prompt(prompt_name)
    system_text = format_prompt(prompt_config.get("system", ""), variables)
    user_text = format_prompt(prompt_config["user"], variables)
    
    # Create messages
    messages = []
    if system_text:
        messages.append(SystemMessage(content=system_text))
    messages.append(HumanMessage(content=user_text))
    
    # Create LLM
    llm = create_llm(temperature=temperature)
    
    # Execute with or without structured output
    if output_model:
        structured_llm = llm.with_structured_output(output_model)
        return structured_llm.invoke(messages)
    else:
        response = llm.invoke(messages)
        return response.content


# Convenience function for the main executor pattern
def get_executor():
    """Get a reusable executor instance.
    
    Returns:
        PromptExecutor instance
    """
    return PromptExecutor()


class PromptExecutor:
    """Reusable executor with LLM caching."""
    
    def __init__(self):
        self._llm_cache: dict[str, ChatAnthropic] = {}
    
    def _get_llm(self, temperature: float = DEFAULT_TEMPERATURE) -> ChatAnthropic:
        """Get or create cached LLM instance."""
        cache_key = f"temp_{temperature}"
        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = create_llm(temperature=temperature)
        return self._llm_cache[cache_key]
    
    def execute(
        self,
        prompt_name: str,
        variables: dict | None = None,
        output_model: Type[T] | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> T | str:
        """Execute a prompt using cached LLM.
        
        Same interface as execute_prompt() but with LLM caching.
        """
        variables = variables or {}
        
        prompt_config = load_prompt(prompt_name)
        system_text = format_prompt(prompt_config.get("system", ""), variables)
        user_text = format_prompt(prompt_config["user"], variables)
        
        messages = []
        if system_text:
            messages.append(SystemMessage(content=system_text))
        messages.append(HumanMessage(content=user_text))
        
        llm = self._get_llm(temperature=temperature)
        
        if output_model:
            structured_llm = llm.with_structured_output(output_model)
            return structured_llm.invoke(messages)
        else:
            response = llm.invoke(messages)
            return response.content
