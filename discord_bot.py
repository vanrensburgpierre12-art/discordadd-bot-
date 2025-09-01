import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime, timedelta
import requests
from typing import Optional

from config import Config
from database import db, User, GiftCard, AdCompletion

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
        user_id = str(interaction.user.id)
        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            # Create new user if they don't exist
            user = User(
                id=user_id,
                username=interaction.user.display_name,
                points_balance=0
            )
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
        user_id = str(interaction.user.id)
        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            # Create new user if they don't exist
            user = User(
                id=user_id,
                username=interaction.user.display_name,
                points_balance=0
            )
            db.session.add(user)
            db.session.commit()
        
        # Check rate limiting
        if user.last_earn_time and datetime.utcnow() - user.last_earn_time < timedelta(seconds=Config.EARN_COOLDOWN):
            remaining_time = Config.EARN_COOLDOWN - (datetime.utcnow() - user.last_earn_time).seconds
            await interaction.response.send_message(
                f"⏰ Please wait **{remaining_time} seconds** before requesting another earn link.",
                ephemeral=True
            )
            return
        
        # Generate unique offerwall link
        offerwall_url = f"{Config.OFFERWALL_BASE_URL}?uid={user_id}&ref=discord"
        
        embed = discord.Embed(
            title="🎬 Watch Ads to Earn Points!",
            description="Complete offers and watch ads to earn points towards Roblox gift cards!",
            color=0x0099ff
        )
        embed.add_field(
            name="📱 Earn Link",
            value=f"[Click Here to Start Earning]({offerwall_url})",
            inline=False
        )
        embed.add_field(
            name="💰 Points per Ad",
            value=f"**{Config.POINTS_PER_AD}** points per completed offer",
            inline=True
        )
        embed.add_field(
            name="🎯 Redemption Goal",
            value=f"**{Config.REDEMPTION_THRESHOLD:,}** points for gift card",
            inline=True
        )
        embed.add_field(
            name="📊 Current Balance",
            value=f"**{user.points_balance:,}** points",
            inline=True
        )
        
        embed.set_footer(text="Complete offers to earn points automatically!")
        embed.timestamp = datetime.utcnow()
        
        # Update last earn time
        user.last_earn_time = datetime.utcnow()
        db.session.commit()
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in earn command: {e}")
        await interaction.response.send_message("❌ An error occurred while generating your earn link.", ephemeral=True)

@bot.tree.command(name="redeem", description="Redeem points for a Roblox gift card")
async def redeem(interaction: discord.Interaction):
    """Redeem points for a Roblox gift card"""
    try:
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
        
        # Find an available gift card
        gift_card = GiftCard.query.filter_by(used=False).first()
        
        if not gift_card:
            await interaction.response.send_message(
                "❌ No gift cards available at the moment. Please try again later!",
                ephemeral=True
            )
            return
        
        # Process redemption
        user.points_balance -= Config.REDEMPTION_THRESHOLD
        gift_card.used = True
        gift_card.used_by = user_id
        gift_card.used_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send gift card code via DM
        try:
            embed = discord.Embed(
                title="🎁 Roblox Gift Card Redeemed!",
                description="Congratulations! Here's your Roblox gift card code:",
                color=0x00ff00
            )
            embed.add_field(
                name="🎫 Gift Card Code",
                value=f"**{gift_card.code}**",
                inline=False
            )
            embed.add_field(
                name="💰 Robux Amount",
                value=f"**{gift_card.amount:,}** Robux",
                inline=True
            )
            embed.add_field(
                name="📊 Points Spent",
                value=f"**{Config.REDEMPTION_THRESHOLD:,}** points",
                inline=True
            )
            embed.add_field(
                name="💳 New Balance",
                value=f"**{user.points_balance:,}** points",
                inline=True
            )
            
            embed.set_footer(text="Redeem this code in Roblox to get your Robux!")
            embed.timestamp = datetime.utcnow()
            
            await interaction.user.send(embed=embed)
            
            # Confirm redemption in the channel
            await interaction.response.send_message(
                f"🎉 **{interaction.user.display_name}** successfully redeemed **{Config.REDEMPTION_THRESHOLD:,}** points for a Roblox gift card!\n"
                f"📱 Check your DMs for the gift card code.",
                ephemeral=False
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I couldn't send you a DM. Please enable DMs from server members and try again.",
                ephemeral=True
            )
            # Revert the transaction
            user.points_balance += Config.REDEMPTION_THRESHOLD
            gift_card.used = False
            gift_card.used_by = None
            gift_card.used_at = None
            db.session.commit()
            
    except Exception as e:
        logger.error(f"Error in redeem command: {e}")
        await interaction.response.send_message("❌ An error occurred while processing your redemption.", ephemeral=True)

@bot.tree.command(name="addpoints", description="Admin command to add points to a user")
@app_commands.describe(
    user="The user to add points to",
    amount="Amount of points to add (can be negative)"
)
async def addpoints(interaction: discord.Interaction, user: discord.Member, amount: int):
    """Admin command to manually add/remove points from a user"""
    try:
        # Check if user has admin role
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        user_id = str(user.id)
        db_user = User.query.filter_by(id=user_id).first()
        
        if not db_user:
            # Create new user if they don't exist
            db_user = User(
                id=user_id,
                username=user.display_name,
                points_balance=0
            )
            db.session.add(db_user)
        
        old_balance = db_user.points_balance
        db_user.points_balance += amount
        
        if amount > 0:
            db_user.total_earned += amount
        
        db.session.commit()
        
        embed = discord.Embed(
            title="👑 Admin Points Update",
            description=f"Points updated for **{user.display_name}**",
            color=0xff9900
        )
        embed.add_field(name="User", value=f"**{user.display_name}** ({user_id})", inline=True)
        embed.add_field(name="Points Change", value=f"**{amount:+}** points", inline=True)
        embed.add_field(name="Old Balance", value=f"**{old_balance:,}** points", inline=True)
        embed.add_field(name="New Balance", value=f"**{db_user.points_balance:,}** points", inline=True)
        embed.add_field(name="Total Earned", value=f"**{db_user.total_earned:,}** points", inline=True)
        
        embed.set_footer(text=f"Updated by {interaction.user.display_name}")
        embed.timestamp = datetime.utcnow()
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Notify the user via DM if possible
        try:
            user_embed = discord.Embed(
                title="💰 Points Updated",
                description=f"An administrator has updated your points balance.",
                color=0x00ff00
            )
            user_embed.add_field(name="Points Change", value=f"**{amount:+}** points", inline=True)
            user_embed.add_field(name="New Balance", value=f"**{db_user.points_balance:,}** points", inline=True)
            user_embed.set_footer(text=f"Updated by {interaction.user.display_name}")
            user_embed.timestamp = datetime.utcnow()
            
            await user.send(embed=user_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
        
    except Exception as e:
        logger.error(f"Error in addpoints command: {e}")
        await interaction.response.send_message("❌ An error occurred while updating points.", ephemeral=True)

@bot.tree.command(name="leaderboard", description="Show top users by points")
async def leaderboard(interaction: discord.Interaction):
    """Show the top users by points balance"""
    try:
        top_users = User.query.order_by(User.points_balance.desc()).limit(10).all()
        
        if not top_users:
            await interaction.response.send_message("❌ No users found.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏆 Points Leaderboard",
            description="Top users by points balance",
            color=0xffd700
        )
        
        for i, user in enumerate(top_users, 1):
            try:
                member = await interaction.guild.fetch_member(int(user.id))
                username = member.display_name
            except:
                username = user.username
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            embed.add_field(
                name=f"{medal} {username}",
                value=f"**{user.points_balance:,}** points",
                inline=False
            )
        
        embed.set_footer(text="Updated in real-time")
        embed.timestamp = datetime.utcnow()
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
        
    except Exception as e:
        logger.error(f"Error in leaderboard command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching the leaderboard.", ephemeral=True)

async def send_points_notification(user_id: str, points_earned: int, new_balance: int):
    """Send a DM notification when user earns points"""
    try:
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

def run_bot():
    """Run the Discord bot"""
    if not Config.DISCORD_TOKEN:
        logger.error("Discord token not found in environment variables!")
        return
    
    try:
        bot.run(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Error running bot: {e}")

if __name__ == "__main__":
    run_bot()