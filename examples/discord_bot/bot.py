"""Discord `/hello` gateway bot executing the hello demo graph (FR-812).

Presentation layer only: compiles the graph once at startup, defers each
interaction (3s ack deadline), runs the graph via run_graph_async, replies
with an embed rendered by the pure adapter.

Requires: pip install "discord.py==2.7.1" and env DISCORD_BOT_TOKEN,
DISCORD_GUILD_ID (see README.md).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path

try:
    import discord
    from discord import app_commands
except ImportError:  # pragma: no cover - guarded for environments without the pin
    sys.exit('discord.py not installed: pip install "discord.py==2.7.1"')

REPO_ROOT = Path(__file__).resolve().parents[2]
# Script-path execution (`python examples/discord_bot/bot.py`) puts only the
# script dir on sys.path; the `examples` package needs the repo root.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HELLO_GRAPH = str(REPO_ROOT / "examples" / "demos" / "hello" / "graph.yaml")
GRAPH_TIMEOUT_S = 120.0


class HelloBot(discord.Client):
    def __init__(self, guild_id: int) -> None:
        super().__init__(intents=discord.Intents.default())
        self.guild = discord.Object(id=guild_id)
        self.tree = app_commands.CommandTree(self)
        self.app_graph = None

    async def setup_hook(self) -> None:
        from yamlgraph.executor_async import load_and_compile_async

        self.app_graph = await load_and_compile_async(HELLO_GRAPH)
        self.tree.copy_global_to(guild=self.guild)
        synced = await self.tree.sync(guild=self.guild)
        logger.info("Synced %d guild command(s)", len(synced))


def main() -> None:
    from examples.discord_bot.adapter import (
        STYLE_CHOICES,
        error_message,
        greeting_to_embed,
        options_to_state,
    )
    from yamlgraph.executor_async import run_graph_async

    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    guild_id = os.environ.get("DISCORD_GUILD_ID", "")
    if not token or not guild_id.isdigit():
        sys.exit("Set DISCORD_BOT_TOKEN and numeric DISCORD_GUILD_ID (see README.md)")

    bot = HelloBot(int(guild_id))

    @bot.tree.command(name="hello", description="Greet someone via the hello graph")
    @app_commands.describe(name="Who to greet (1-80 chars)", style="Greeting tone")
    @app_commands.choices(
        style=[app_commands.Choice(name=s, value=s) for s in STYLE_CHOICES]
    )
    async def hello(
        interaction: discord.Interaction, name: str, style: app_commands.Choice[str]
    ) -> None:
        correlation_id = uuid.uuid4().hex[:12]
        # Defer immediately: graph latency exceeds Discord's 3s ack deadline.
        await interaction.response.defer()
        try:
            state = options_to_state(name, style.value)
            async with asyncio.timeout(GRAPH_TIMEOUT_S):
                result = await run_graph_async(bot.app_graph, state)
            rendered = greeting_to_embed(result["greeting"])
            embed = discord.Embed(title=rendered["title"])
            embed.set_footer(text=rendered["footer"])
            await interaction.followup.send(embed=embed)
        except Exception:
            logger.exception("/hello failed (correlation_id=%s)", correlation_id)
            await interaction.followup.send(
                error_message(correlation_id), ephemeral=True
            )

    bot.run(token)


if __name__ == "__main__":
    main()
