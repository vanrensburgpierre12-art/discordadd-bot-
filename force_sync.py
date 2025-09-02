#!/usr/bin/env python3
"""
Force sync Discord slash commands without restarting the bot
This can be run while the bot is running to sync commands
"""

import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import logging
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ForceSyncBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Force sync all commands globally
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Successfully synced {len(synced)} commands globally!")
            for command in synced:
                logger.info(f"   - /{command.name}: {command.description}")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands globally: {e}")
        
        # Also try guild-specific sync if we have a guild ID
        if Config.DISCORD_GUILD_ID:
            try:
                guild = discord.Object(id=int(Config.DISCORD_GUILD_ID))
                synced = await self.tree.sync(guild=guild)
                logger.info(f"✅ Successfully synced {len(synced)} commands to guild {Config.DISCORD_GUILD_ID}!")
            except Exception as e:
                logger.error(f"❌ Failed to sync commands to guild: {e}")

    async def on_ready(self):
        logger.info(f"🤖 {self.user} is ready and commands are synced!")
        logger.info("🔄 You can now see all commands in Discord!")
        await self.close()

async def main():
    if not Config.DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in environment variables!")
        logger.error("Please make sure your bot token is set in the environment.")
        return

    logger.info("🔄 Starting command sync...")
    bot = ForceSyncBot()
    
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())