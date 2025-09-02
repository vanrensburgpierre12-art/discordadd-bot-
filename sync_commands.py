#!/usr/bin/env python3
"""
Force sync Discord slash commands
This script will force Discord to register all slash commands
"""

import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Force sync all commands
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} commands to Discord!")
            for command in synced:
                logger.info(f"   - {command.name}")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")
        
        # Also try guild-specific sync if we have a guild ID
        if Config.DISCORD_GUILD_ID:
            try:
                guild = discord.Object(id=int(Config.DISCORD_GUILD_ID))
                synced = await self.tree.sync(guild=guild)
                logger.info(f"✅ Synced {len(synced)} commands to guild {Config.DISCORD_GUILD_ID}!")
            except Exception as e:
                logger.error(f"❌ Failed to sync commands to guild: {e}")

    async def on_ready(self):
        logger.info(f"🤖 {self.user} is ready!")
        logger.info("🔄 Commands have been synced!")
        await self.close()

async def main():
    if not Config.DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in environment variables!")
        return

    bot = SyncBot()
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())