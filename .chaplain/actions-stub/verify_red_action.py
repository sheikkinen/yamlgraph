"""Stub: verify_red — always succeeds (no pytest needed in integration)."""

import logging

from statemachine_engine.actions.base import BaseAction

logger = logging.getLogger(__name__)


class VerifyRedAction(BaseAction):
    async def execute(self, context):
        machine_name = self.get_machine_name(context)
        success_event = self.get_config_value("success", "red_verified")
        logger.info(f"[{machine_name}] stub verify_red → {success_event}")
        return success_event
