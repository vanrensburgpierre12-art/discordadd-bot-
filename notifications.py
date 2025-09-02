import logging
from datetime import datetime
import discord
from config import Config

logger = logging.getLogger(__name__)

async def send_points_notification(user_id: str, points_earned: int, new_balance: int):
    """Send a DM notification when user earns points"""
    try:
        # Import bot from discord_bot module
        from discord_bot import bot
        user = bot.get_user(int(user_id))
        if user:
            embed = discord.Embed(
                title="✅ Points Earned!",
                description=f"You just earned **{points_earned:,}** points by completing an offer!",
                color=0x00ff00
            )
            embed.add_field(name="Points Earned", value=f"**+{points_earned:,}**", inline=True)
            embed.add_field(name="New Balance", value=f"**{new_balance:,}**", inline=True)
            embed.add_field(name="Next Goal", value=f"**{Config.REDEMPTION_THRESHOLD:,}** points", inline=True)

            if new_balance >= Config.REDEMPTION_THRESHOLD:
                embed.add_field(name="🎉 Status", value="**Ready to redeem!** Use `/redeem`", inline=False)

            embed.set_footer(text="Keep watching ads to earn more points!")
            embed.timestamp = datetime.utcnow()

            await user.send(embed=embed)

    except Exception as e:
        logger.error(f"Error sending points notification: {e}")
