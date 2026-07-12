"""FR-715 witnesses: PromptRequest — one object through the front door.

AC-01 (Judgement F3): the public `execute_prompt` signature and the
`PromptRequest` dataclass fields must be the same set, derived from one
source — fails while PromptRequest does not exist, and keeps failing if
a parameter is ever added to one side only (the drift this FR kills:
max_tokens and thinking_budget were each added in three places).
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest


def _request_field_names() -> set[str]:
    from yamlgraph.executor_base import PromptRequest

    return {f.name for f in dataclasses.fields(PromptRequest)}


class TestSignatureParity:
    @pytest.mark.req("REQ-YG-543")
    def test_execute_prompt_params_equal_request_fields(self):
        from yamlgraph.executor import execute_prompt

        params = set(inspect.signature(execute_prompt).parameters)
        assert params == _request_field_names(), (
            "execute_prompt signature and PromptRequest fields drifted — "
            "every parameter must exist in both (single source of truth)"
        )

    @pytest.mark.req("REQ-YG-543")
    def test_executor_execute_takes_request(self):
        """The method half of the old clone accepts the object, not a
        second hand-maintained copy of the signature."""
        from yamlgraph.executor import PromptExecutor

        params = list(inspect.signature(PromptExecutor.execute).parameters)
        assert params == [
            "self",
            "request",
        ], f"PromptExecutor.execute must take PromptRequest only, got {params}"

    @pytest.mark.req("REQ-YG-543")
    def test_async_front_door_is_subset(self):
        """execute_prompt_async params must be a subset of PromptRequest
        fields — a param added to the async door but not the dataclass is
        the three-places drift reborn. (Known gap, recorded in the FR:
        async lacks max_tokens/thinking_budget — subset, not equality.)"""
        from yamlgraph.executor_async import execute_prompt_async

        params = set(inspect.signature(execute_prompt_async).parameters)
        assert params <= _request_field_names(), (
            f"async front door drifted beyond PromptRequest: "
            f"{params - _request_field_names()}"
        )


class TestRequestDefaults:
    @pytest.mark.req("REQ-YG-543")
    def test_defaults_live_once(self):
        """Defaults are defined on the dataclass, and execute_prompt's
        signature defaults match them — one source."""
        from yamlgraph.executor import execute_prompt
        from yamlgraph.executor_base import PromptRequest

        sig = inspect.signature(execute_prompt)
        for f in dataclasses.fields(PromptRequest):
            if f.default is dataclasses.MISSING:
                continue
            assert sig.parameters[f.name].default == f.default, (
                f"default for {f.name!r} drifted between execute_prompt "
                f"and PromptRequest"
            )
