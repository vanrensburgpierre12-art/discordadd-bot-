import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timedelta

from config import Config
from flask_app import app  # import Flask app for context
from database import db, User, GiftCard, DailyCasinoLimit
from casino_games import DiceGame, SlotsGame, BlackjackGame

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
        await self.change_presence(activity=discord.Game(name="/earn to watch ads! | /casino to play games!"))

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


@bot.tree.command(name="dice", description="Roll the dice and guess the number (1-6)")
async def dice(interaction: discord.Interaction, bet: int, guess: int):
    """Play dice game"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            # Check cooldown
            if user.last_earn_time and datetime.utcnow() - user.last_earn_time < timedelta(seconds=Config.CASINO_COOLDOWN):
                remaining_time = Config.CASINO_COOLDOWN - (datetime.utcnow() - user.last_earn_time).seconds
                await interaction.response.send_message(
                    f"⏰ Please wait **{remaining_time} seconds** before playing again.",
                    ephemeral=True
                )
                return

            # Play dice game
            result = DiceGame.play(user_id, bet, guess)
            
            if not result["success"]:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
                return

            # Update last activity time
            user.last_earn_time = datetime.utcnow()
            db.session.commit()

            # Create embed
            embed = discord.Embed(
                title="🎲 Dice Game Result",
                description=result["result_text"],
                color=0x00ff00 if result["win_amount"] > 0 else 0xff0000
            )
            embed.add_field(name="Your Guess", value=f"**{result['guess']}**", inline=True)
            embed.add_field(name="Dice Roll", value=f"**{result['dice_roll']}**", inline=True)
            embed.add_field(name="Bet Amount", value=f"**{result['bet_amount']:,}** points", inline=True)
            embed.add_field(name="Winnings", value=f"**{result['win_amount']:,}** points", inline=True)
            embed.add_field(name="New Balance", value=f"**{result['new_balance']:,}** points", inline=True)
            
            # Add daily limit info
            daily_limit = DailyCasinoLimit.query.filter_by(
                user_id=user_id, 
                date=datetime.utcnow().date()
            ).first()
            if daily_limit:
                net_result = daily_limit.total_won - daily_limit.total_lost
                embed.add_field(name="Daily Casino Result", value=f"**{net_result:+,}** points", inline=True)

            embed.set_footer(text=f"User ID: {user_id}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed)

    except Exception as e:
        logger.error(f"Error in dice command: {e}")
        await interaction.response.send_message("❌ An error occurred while playing dice.", ephemeral=True)


@bot.tree.command(name="slots", description="Spin the slot machine")
async def slots(interaction: discord.Interaction, bet: int):
    """Play slots game"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            # Check cooldown
            if user.last_earn_time and datetime.utcnow() - user.last_earn_time < timedelta(seconds=Config.CASINO_COOLDOWN):
                remaining_time = Config.CASINO_COOLDOWN - (datetime.utcnow() - user.last_earn_time).seconds
                await interaction.response.send_message(
                    f"⏰ Please wait **{remaining_time} seconds** before playing again.",
                    ephemeral=True
                )
                return

            # Play slots game
            result = SlotsGame.play(user_id, bet)
            
            if not result["success"]:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
                return

            # Update last activity time
            user.last_earn_time = datetime.utcnow()
            db.session.commit()

            # Create embed
            embed = discord.Embed(
                title="🎰 Slot Machine Result",
                description=result["result_text"],
                color=0x00ff00 if result["win_amount"] > 0 else 0xff0000
            )
            embed.add_field(name="Reels", value=f"**{result['reels'][0]} {result['reels'][1]} {result['reels'][2]}**", inline=True)
            embed.add_field(name="Bet Amount", value=f"**{result['bet_amount']:,}** points", inline=True)
            embed.add_field(name="Winnings", value=f"**{result['win_amount']:,}** points", inline=True)
            embed.add_field(name="New Balance", value=f"**{result['new_balance']:,}** points", inline=True)
            
            # Add daily limit info
            daily_limit = DailyCasinoLimit.query.filter_by(
                user_id=user_id, 
                date=datetime.utcnow().date()
            ).first()
            if daily_limit:
                net_result = daily_limit.total_won - daily_limit.total_lost
                embed.add_field(name="Daily Casino Result", value=f"**{net_result:+,}** points", inline=True)

            embed.set_footer(text=f"User ID: {user_id}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed)

    except Exception as e:
        logger.error(f"Error in slots command: {e}")
        await interaction.response.send_message("❌ An error occurred while playing slots.", ephemeral=True)


@bot.tree.command(name="blackjack", description="Play a game of blackjack")
async def blackjack(interaction: discord.Interaction, bet: int):
    """Play blackjack game"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            # Check cooldown
            if user.last_earn_time and datetime.utcnow() - user.last_earn_time < timedelta(seconds=Config.CASINO_COOLDOWN):
                remaining_time = Config.CASINO_COOLDOWN - (datetime.utcnow() - user.last_earn_time).seconds
                await interaction.response.send_message(
                    f"⏰ Please wait **{remaining_time} seconds** before playing again.",
                    ephemeral=True
                )
                return

            # Play blackjack game
            result = BlackjackGame.play(user_id, bet)
            
            if not result["success"]:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
                return

            # Update last activity time
            user.last_earn_time = datetime.utcnow()
            db.session.commit()

            # Create embed
            embed = discord.Embed(
                title="🃏 Blackjack Result",
                description=result["result_text"],
                color=0x00ff00 if result["win_amount"] > 0 else 0xff0000
            )
            embed.add_field(name="Your Cards", value=f"**{result['player_cards']}** ({result['player_score']})", inline=True)
            embed.add_field(name="Dealer Cards", value=f"**{result['dealer_cards']}** ({result['dealer_score']})", inline=True)
            embed.add_field(name="Bet Amount", value=f"**{result['bet_amount']:,}** points", inline=True)
            embed.add_field(name="Winnings", value=f"**{result['win_amount']:,}** points", inline=True)
            embed.add_field(name="New Balance", value=f"**{result['new_balance']:,}** points", inline=True)
            
            # Add daily limit info
            daily_limit = DailyCasinoLimit.query.filter_by(
                user_id=user_id, 
                date=datetime.utcnow().date()
            ).first()
            if daily_limit:
                net_result = daily_limit.total_won - daily_limit.total_lost
                embed.add_field(name="Daily Casino Result", value=f"**{net_result:+,}** points", inline=True)

            embed.set_footer(text=f"User ID: {user_id}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed)

    except Exception as e:
        logger.error(f"Error in blackjack command: {e}")
        await interaction.response.send_message("❌ An error occurred while playing blackjack.", ephemeral=True)


@bot.tree.command(name="casino", description="View casino information and daily limits")
async def casino_info(interaction: discord.Interaction):
    """Show casino information and user's daily limits"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            # Get daily limit info
            daily_limit = DailyCasinoLimit.query.filter_by(
                user_id=user_id, 
                date=datetime.utcnow().date()
            ).first()

            embed = discord.Embed(
                title="🎰 Casino Information",
                description="Welcome to the Rewards Casino! Try your luck with our games.",
                color=0x0099ff
            )
            
            embed.add_field(name="🎲 Dice Game", value=f"Guess 1-6, win 5x your bet if correct!\nMin bet: {Config.CASINO_MIN_BET}, Max bet: {Config.CASINO_MAX_BET}", inline=False)
            embed.add_field(name="🎰 Slot Machine", value=f"Spin for matching symbols!\nMin bet: {Config.CASINO_MIN_BET}, Max bet: {Config.CASINO_MAX_BET}", inline=False)
            embed.add_field(name="🃏 Blackjack", value=f"Beat the dealer to 21!\nMin bet: {Config.CASINO_MIN_BET}, Max bet: {Config.CASINO_MAX_BET}", inline=False)
            
            embed.add_field(name="💰 Your Balance", value=f"**{user.points_balance:,}** points", inline=True)
            embed.add_field(name="⏰ Cooldown", value=f"**{Config.CASINO_COOLDOWN}** seconds", inline=True)
            embed.add_field(name="📊 Daily Limit", value=f"**{Config.CASINO_DAILY_LIMIT:,}** points", inline=True)
            
            if daily_limit:
                net_result = daily_limit.total_won - daily_limit.total_lost
                embed.add_field(name="📈 Today's Result", value=f"**{net_result:+,}** points", inline=True)
                embed.add_field(name="🎮 Games Played", value=f"**{daily_limit.games_played}**", inline=True)
                remaining = Config.CASINO_DAILY_LIMIT - abs(net_result)
                embed.add_field(name="🎯 Remaining", value=f"**{remaining:,}** points", inline=True)
            else:
                embed.add_field(name="📈 Today's Result", value="**0** points", inline=True)
                embed.add_field(name="🎮 Games Played", value="**0**", inline=True)
                embed.add_field(name="🎯 Remaining", value=f"**{Config.CASINO_DAILY_LIMIT:,}** points", inline=True)

            embed.set_footer(text="Use /dice, /slots, or /blackjack to play!")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in casino command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching casino information.", ephemeral=True)


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
