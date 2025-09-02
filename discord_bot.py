import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timedelta

from config import Config
from flask_app import app  # import Flask app for context
from database import db, User, GiftCard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RewardsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        logger.info("Bot setup complete!")

    async def on_ready(self):
        logger.info(f"{self.user} has connected to Discord!")
        await self.change_presence(activity=discord.Game(name="/earn to watch ads!"))

bot = RewardsBot()


@bot.tree.command(name="balance", description="Check your current points balance")
async def balance(interaction: discord.Interaction):
    """Show user's current points balance"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                user = User(id=user_id, username=interaction.user.display_name, points_balance=0)
                db.session.add(user)
                db.session.commit()

            embed = discord.Embed(
                title="💰 Points Balance",
                description=f"**{interaction.user.display_name}**'s current balance",
                color=0x00ff00
            )
            embed.add_field(name="Current Balance", value=f"**{user.points_balance:,}** points", inline=True)
            embed.add_field(name="Total Earned", value=f"**{user.total_earned:,}** points", inline=True)
            embed.add_field(name="Redemption Threshold", value=f"**{Config.REDEMPTION_THRESHOLD:,}** points", inline=True)

            if user.points_balance >= Config.REDEMPTION_THRESHOLD:
                embed.add_field(name="🎉 Status", value="**Ready to redeem!** Use `/redeem`", inline=False)
            else:
                points_needed = Config.REDEMPTION_THRESHOLD - user.points_balance
                embed.add_field(name="📈 Progress", value=f"**{points_needed:,}** more points needed", inline=False)

            embed.set_footer(text=f"User ID: {user_id}")
            embed.timestamp = datetime.utcnow()
            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in balance command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching your balance.", ephemeral=True)


@bot.tree.command(name="earn", description="Get a link to earn points by watching ads")
async def earn(interaction: discord.Interaction):
    """Provide user with a unique offerwall link"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                user = User(id=user_id, username=interaction.user.display_name, points_balance=0)
                db.session.add(user)
                db.session.commit()

            if user.last_earn_time and datetime.utcnow() - user.last_earn_time < timedelta(seconds=Config.EARN_COOLDOWN):
                remaining_time = Config.EARN_COOLDOWN - (datetime.utcnow() - user.last_earn_time).seconds
                await interaction.response.send_message(
                    f"⏰ Please wait **{remaining_time} seconds** before requesting another earn link.",
                    ephemeral=True
                )
                return

            offerwall_url = f"{Config.OFFERWALL_BASE_URL}?uid={user_id}&ref=discord"
            embed = discord.Embed(
                title="🎬 Watch Ads to Earn Points!",
                description="Complete offers and watch ads to earn points towards Roblox gift cards!",
                color=0x0099ff
            )
            embed.add_field(name="📱 Earn Link", value=f"[Click Here to Start Earning]({offerwall_url})", inline=False)
            embed.add_field(name="💰 Points per Ad", value=f"**{Config.POINTS_PER_AD}** points per completed offer", inline=True)
            embed.add_field(name="🎯 Redemption Goal", value=f"**{Config.REDEMPTION_THRESHOLD:,}** points for gift card", inline=True)
            embed.add_field(name="📊 Current Balance", value=f"**{user.points_balance:,}** points", inline=True)

            embed.set_footer(text="Complete offers to earn points automatically!")
            embed.timestamp = datetime.utcnow()

            user.last_earn_time = datetime.utcnow()
            db.session.commit()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in earn command: {e}")
        await interaction.response.send_message("❌ An error occurred while generating your earn link.", ephemeral=True)


@bot.tree.command(name="redeem", description="Redeem points for a Roblox gift card")
async def redeem(interaction: discord.Interaction):
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            if user.points_balance < Config.REDEMPTION_THRESHOLD:
                points_needed = Config.REDEMPTION_THRESHOLD - user.points_balance
                await interaction.response.send_message(
                    f"❌ You need **{points_needed:,}** more points to redeem. Current balance: **{user.points_balance:,}** points",
                    ephemeral=True
                )
                return

            gift_card = GiftCard.query.filter_by(used=False).first()
            if not gift_card:
                await interaction.response.send_message(
                    "❌ No gift cards available at the moment. Please try again later!",
                    ephemeral=True
                )
                return

            user.points_balance -= Config.REDEMPTION_THRESHOLD
            gift_card.used = True
            gift_card.used_by = user_id
            gift_card.used_at = datetime.utcnow()
            db.session.commit()

            try:
                embed = discord.Embed(
                    title="🎁 Roblox Gift Card Redeemed!",
                    description="Congratulations! Here's your Roblox gift card code:",
                    color=0x00ff00
                )
                embed.add_field(name="🎫 Gift Card Code", value=f"**{gift_card.code}**", inline=False)
                embed.add_field(name="💰 Robux Amount", value=f"**{gift_card.amount:,}** Robux", inline=True)
                embed.add_field(name="📊 Points Spent", value=f"**{Config.REDEMPTION_THRESHOLD:,}** points", inline=True)
                embed.add_field(name="💳 New Balance", value=f"**{user.points_balance:,}** points", inline=True)
                embed.set_footer(text="Redeem this code in Roblox to get your Robux!")
                embed.timestamp = datetime.utcnow()

                await interaction.user.send(embed=embed)
                await interaction.response.send_message(
                    f"🎉 **{interaction.user.display_name}** successfully redeemed **{Config.REDEMPTION_THRESHOLD:,}** points for a Roblox gift card!\n📱 Check your DMs for the gift card code.",
                    ephemeral=False
                )

            except discord.Forbidden:
                user.points_balance += Config.REDEMPTION_THRESHOLD
                gift_card.used = False
                gift_card.used_by = None
                gift_card.used_at = None
                db.session.commit()
                await interaction.response.send_message(
                    "❌ I couldn't send you a DM. Please enable DMs from server members and try again.",
                    ephemeral=True
                )

    except Exception as e:
        logger.error(f"Error in redeem command: {e}")
        await interaction.response.send_message("❌ An error occurred while processing your redemption.", ephemeral=True)


def run_bot():
    if not Config.DISCORD_TOKEN:
        logger.error("Discord token not found in environment variables!")
        return

    try:
        bot.run(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Error running bot: {e}")


if __name__ == "__main__":
    run_bot()
