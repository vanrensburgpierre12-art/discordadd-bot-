import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
import time
from datetime import datetime, timedelta

from config import Config
from app_context import app, db  # import Flask app for context
from database import User, GiftCard, DailyCasinoLimit, UserWallet, UserSubscription, Server, AdminUser
from casino_games import DiceGame, SlotsGame, BlackjackGame
from wallet_manager import WalletManager
from discord_monetization import DiscordMonetizationManager
from admin_manager import AdminManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RewardsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix="!", 
            intents=intents,
            heartbeat_timeout=Config.DISCORD_HEARTBEAT_TIMEOUT,
            max_messages=1000
        )
        
        # Connection tracking
        self.connection_attempts = 0
        self.max_connection_attempts = Config.DISCORD_MAX_RECONNECT_ATTEMPTS
        self.last_connection_time = None
        self.is_connected = False
        self.connection_errors = []
        self.reconnect_delay = Config.DISCORD_RECONNECT_DELAY

    async def setup_hook(self):
        await self.tree.sync()
        logger.info("Bot setup complete!")
        
        # Start connection monitoring task
        self.loop.create_task(self.connection_monitor())

    async def on_ready(self):
        logger.info(f"{self.user} has connected to Discord!")
        await self.change_presence(activity=discord.Game(name="/earn | /casino | /wallet | /tiers - Complete Gaming Platform!"))
        
        # Register all servers the bot is in
        for guild in self.guilds:
            try:
                with app.app_context():
                    result = AdminManager.register_server(
                        str(guild.id),
                        guild.name,
                        str(guild.owner_id)
                    )
                    if result['success']:
                        logger.info(f"Registered server: {guild.name} ({guild.id})")
            except Exception as e:
                logger.error(f"Error registering server {guild.name}: {e}")

    async def on_guild_join(self, guild):
        """Handle bot being added to a new server"""
        try:
            with app.app_context():
                result = AdminManager.register_server(
                    str(guild.id),
                    guild.name,
                    str(guild.owner_id)
                )
                if result['success']:
                    logger.info(f"Bot added to new server: {guild.name} ({guild.id})")
                    
                    # Send welcome message to server owner
                    try:
                        owner = guild.owner
                        if owner:
                            embed = discord.Embed(
                                title="🎮 Welcome to Rewards Platform!",
                                description="Thanks for adding me to your server!",
                                color=0x00ff00
                            )
                            embed.add_field(
                                name="🚀 Getting Started",
                                value="• Use `/earn` to get ad links\n• Use `/casino` to play games\n• Use `/tiers` to see subscription benefits",
                                inline=False
                            )
                            embed.add_field(
                                name="💡 Features",
                                value="• Watch ads for points\n• Play casino games\n• Subscribe for better odds\n• Redeem points for gift cards",
                                inline=False
                            )
                            embed.set_footer(text="Use /help for more commands!")
                            await owner.send(embed=embed)
                    except Exception as e:
                        logger.error(f"Error sending welcome message: {e}")
        except Exception as e:
            logger.error(f"Error handling guild join: {e}")

    async def on_guild_remove(self, guild):
        """Handle bot being removed from a server"""
        try:
            with app.app_context():
                server = Server.query.filter_by(id=str(guild.id)).first()
                if server:
                    server.is_active = False
                    server.last_activity = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Bot removed from server: {guild.name} ({guild.id})")
        except Exception as e:
            logger.error(f"Error handling guild remove: {e}")

    async def on_connect(self):
        """Handle successful connection to Discord"""
        self.is_connected = True
        self.connection_attempts = 0
        self.last_connection_time = datetime.utcnow()
        self.connection_errors.clear()
        logger.info("✅ Successfully connected to Discord Gateway")

    async def on_disconnect(self):
        """Handle disconnection from Discord"""
        self.is_connected = False
        logger.warning("⚠️ Disconnected from Discord Gateway")

    async def on_resumed(self):
        """Handle successful session resume"""
        self.is_connected = True
        self.connection_attempts = 0
        self.last_connection_time = datetime.utcnow()
        logger.info("🔄 Successfully resumed Discord session")

    async def on_error(self, event, *args, **kwargs):
        """Handle Discord client errors"""
        error_msg = f"Discord error in {event}: {args}"
        logger.error(f"❌ {error_msg}")
        self.connection_errors.append({
            'timestamp': datetime.utcnow(),
            'event': event,
            'error': str(args)
        })
        
        # Keep only last 10 errors
        if len(self.connection_errors) > 10:
            self.connection_errors = self.connection_errors[-10:]

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        logger.error(f"Command error in {ctx.command}: {error}")
        
        # Send user-friendly error message
        try:
            if isinstance(error, commands.MissingPermissions):
                await ctx.send("❌ You don't have permission to use this command.")
            elif isinstance(error, commands.CommandOnCooldown):
                await ctx.send(f"⏰ This command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"❌ Missing required argument: {error.param}")
            else:
                await ctx.send("❌ An error occurred while processing your command.")
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    def get_connection_status(self):
        """Get current connection status information"""
        return {
            'is_connected': self.is_connected,
            'connection_attempts': self.connection_attempts,
            'last_connection_time': self.last_connection_time,
            'recent_errors': len(self.connection_errors),
            'uptime': (datetime.utcnow() - self.last_connection_time).total_seconds() if self.last_connection_time else 0
        }

    async def connection_monitor(self):
        """Monitor connection health and log status periodically"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                if self.is_connected and self.last_connection_time:
                    uptime = (datetime.utcnow() - self.last_connection_time).total_seconds()
                    if uptime > 3600:  # Log every hour
                        logger.info(f"🟢 Bot connection healthy - uptime: {uptime/3600:.1f} hours, latency: {self.latency*1000:.1f}ms")
                
                # Log connection errors if any
                if self.connection_errors:
                    recent_errors = [e for e in self.connection_errors if (datetime.utcnow() - e['timestamp']).total_seconds() < 3600]
                    if recent_errors:
                        logger.warning(f"⚠️ {len(recent_errors)} connection errors in the last hour")
                        
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

bot = RewardsBot()

def check_user_status(user_id: str) -> tuple[bool, str]:
    """Check if user is banned or suspended. Returns (is_allowed, status_message)"""
    try:
        with app.app_context():
            user = User.query.filter_by(id=user_id).first()
            if not user:
                return True, ""  # New users are allowed
            
            if user.user_status == 'banned':
                return False, f"🚫 You are banned from using this bot.\n**Reason:** {user.ban_reason or 'No reason provided'}"
            elif user.user_status == 'suspended':
                return False, f"⏸️ Your account is suspended. Please contact an administrator."
            
            return True, ""
    except Exception as e:
        logger.error(f"Error checking user status: {e}")
        return True, ""  # Allow on error to avoid blocking legitimate users


@bot.tree.command(name="balance", description="Check your current points balance")
async def balance(interaction: discord.Interaction):
    """Show user's current points balance"""
    try:
        user_id = str(interaction.user.id)
        
        # Check if user is banned or suspended
        is_allowed, status_message = check_user_status(user_id)
        if not is_allowed:
            await interaction.response.send_message(status_message, ephemeral=True)
            return
        
        with app.app_context():
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
            daily_limit = DailyCasinoLimit.query.filter_by(user_id=user_id).first()
            # Only show daily limit info if it's for today
            if daily_limit and daily_limit.date == datetime.utcnow().date():
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
            daily_limit = DailyCasinoLimit.query.filter_by(user_id=user_id).first()
            # Only show daily limit info if it's for today
            if daily_limit and daily_limit.date == datetime.utcnow().date():
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
            daily_limit = DailyCasinoLimit.query.filter_by(user_id=user_id).first()
            # Only show daily limit info if it's for today
            if daily_limit and daily_limit.date == datetime.utcnow().date():
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
            daily_limit = DailyCasinoLimit.query.filter_by(user_id=user_id).first()
            # Only show daily limit info if it's for today
            if daily_limit and daily_limit.date == datetime.utcnow().date():

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
            
            if daily_limit and daily_limit.date == datetime.utcnow().date():
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


@bot.tree.command(name="wallet", description="View your wallet information and deposit packages")
async def wallet_info(interaction: discord.Interaction):
    """Show wallet information and deposit packages"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            # Get wallet info
            wallet_info = WalletManager.get_wallet_info(user_id)
            if not wallet_info['success']:
                await interaction.response.send_message(f"❌ {wallet_info['error']}", ephemeral=True)
                return

            # Get deposit packages
            packages_info = WalletManager.get_deposit_packages()
            
            embed = discord.Embed(
                title="💳 Wallet Information",
                description="Manage your cash deposits and point balance",
                color=0x0099ff
            )
            
            # Wallet stats
            wallet = wallet_info['wallet']
            embed.add_field(name="💰 Current Balance", value=f"**{user.points_balance:,}** points", inline=True)
            embed.add_field(name="💵 Total Deposited", value=f"**${wallet['total_deposited']:.2f}**", inline=True)
            embed.add_field(name="🎁 Lifetime Bonus", value=f"**{wallet['lifetime_bonus']:,}** points", inline=True)
            
            # Recent transactions
            recent_txns = wallet_info['recent_transactions'][:3]  # Show last 3
            if recent_txns:
                txn_text = ""
                for txn in recent_txns:
                    status_emoji = "✅" if txn['status'] == 'completed' else "⏳" if txn['status'] == 'pending' else "❌"
                    txn_text += f"{status_emoji} ${txn['amount_usd']:.2f} ({txn['points_amount']:+,} pts)\n"
                embed.add_field(name="📋 Recent Transactions", value=txn_text or "None", inline=False)
            
            # Deposit packages
            packages_text = ""
            for pkg in packages_info['packages'][:3]:  # Show first 3 packages
                packages_text += f"**${pkg['amount_usd']}** → {pkg['total_points']:,} pts (+{pkg['bonus_percentage']:.0f}% bonus)\n"
            
            embed.add_field(name="💎 Deposit Packages", value=packages_text, inline=False)
            embed.add_field(name="🔗 Deposit Link", value=f"[Add Funds]({Config.WEBHOOK_URL.replace('/postback', '/wallet')})", inline=True)
            embed.add_field(name="📊 Exchange Rate", value=f"**{Config.POINTS_PER_DOLLAR}** pts/$1", inline=True)
            embed.add_field(name="🎁 Bonus", value=f"**+{Config.WALLET_BONUS_PERCENTAGE*100:.0f}%** on deposits", inline=True)
            
            embed.set_footer(text=f"User ID: {user_id}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in wallet command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching wallet information.", ephemeral=True)


@bot.tree.command(name="deposit", description="Get deposit packages and payment information")
async def deposit_info(interaction: discord.Interaction):
    """Show deposit packages and payment options"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            # Get deposit packages
            packages_info = WalletManager.get_deposit_packages()
            
            embed = discord.Embed(
                title="💳 Deposit Packages",
                description="Add cash to your wallet and get bonus points!",
                color=0x00ff00
            )
            
            # Show all packages
            for pkg in packages_info['packages']:
                embed.add_field(
                    name=f"💎 ${pkg['amount_usd']} Package",
                    value=f"**{pkg['total_points']:,}** points\n({pkg['base_points']:,} base + {pkg['bonus_points']:,} bonus)\n**+{pkg['bonus_percentage']:.0f}%** bonus",
                    inline=True
                )
            
            embed.add_field(name="💰 Current Balance", value=f"**{user.points_balance:,}** points", inline=False)
            embed.add_field(name="🔗 Payment Link", value=f"[Add Funds Now]({Config.WEBHOOK_URL.replace('/postback', '/wallet')})", inline=True)
            embed.add_field(name="💳 Payment Methods", value="Stripe, PayPal, Crypto", inline=True)
            embed.add_field(name="⚡ Processing", value="Instant", inline=True)
            
            embed.set_footer(text="Deposits are processed instantly with bonus points!")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in deposit command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching deposit information.", ephemeral=True)


@bot.tree.command(name="withdraw", description="Request a withdrawal (convert points to cash)")
async def withdraw_request(interaction: discord.Interaction, amount_usd: float):
    """Request a withdrawal of points to cash"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            # Create withdrawal request
            result = WalletManager.create_withdrawal_request(user_id, amount_usd)
            
            if not result['success']:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
                return

            embed = discord.Embed(
                title="💸 Withdrawal Request",
                description="Your withdrawal request has been submitted for review",
                color=0xffa500
            )
            
            embed.add_field(name="💰 Amount Requested", value=f"**${amount_usd:.2f}**", inline=True)
            embed.add_field(name="🎯 Points Deducted", value=f"**{result['points_deducted']:,}**", inline=True)
            embed.add_field(name="📊 New Balance", value=f"**{user.points_balance:,}** points", inline=True)
            embed.add_field(name="📋 Transaction ID", value=f"**#{result['transaction_id']}**", inline=True)
            embed.add_field(name="⏳ Status", value="**Pending Review**", inline=True)
            embed.add_field(name="💳 Payment Method", value="PayPal", inline=True)
            
            embed.add_field(
                name="ℹ️ Processing Info", 
                value="Withdrawals are reviewed within 24 hours. You'll receive payment via PayPal once approved.",
                inline=False
            )
            
            embed.set_footer(text=f"User ID: {user_id}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in withdraw command: {e}")
        await interaction.response.send_message("❌ An error occurred while processing withdrawal request.", ephemeral=True)


@bot.tree.command(name="tiers", description="View available subscription tiers and their benefits")
async def subscription_tiers(interaction: discord.Interaction):
    """Show available subscription tiers and benefits"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            # Get user's current subscription
            subscription_info = DiscordMonetizationManager.get_subscription_info(user_id)
            tiers_info = DiscordMonetizationManager.get_available_tiers()
            
            embed = discord.Embed(
                title="💎 Subscription Tiers & Benefits",
                description="Unlock better casino odds and exclusive rewards!",
                color=0x9b59b6
            )
            
            # Current subscription status
            if subscription_info['has_subscription']:
                embed.add_field(
                    name="🎯 Your Current Tier",
                    value=f"**{subscription_info['tier_name']}**\n+{subscription_info['casino_bonus']}% casino bonus\nExpires: {subscription_info['expires_at'][:10] if subscription_info['expires_at'] else 'Never'}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎯 Your Current Tier",
                    value="**Free User**\nNo casino bonuses",
                    inline=False
                )
            
            # Server Boost tiers
            embed.add_field(
                name="🚀 Server Boosts",
                value="Boost this server for points and casino bonuses!",
                inline=False
            )
            
            for tier_key, tier_info in Config.SERVER_BOOST_REWARDS.items():
                casino_bonus = Config.SUBSCRIPTION_TIERS.get(tier_key, {}).get('casino_bonus', 0) * 100
                embed.add_field(
                    name=f"🔹 {tier_info['name']}",
                    value=f"**{tier_info['boosts']}** boosts → **{tier_info['points']:,}** points\n+{casino_bonus}% casino bonus",
                    inline=True
                )
            
            # Nitro Gift tiers
            embed.add_field(
                name="💳 Nitro Gifts",
                value="Gift Nitro to get points and temporary bonuses!",
                inline=False
            )
            
            for nitro_key, nitro_info in Config.NITRO_GIFT_REWARDS.items():
                embed.add_field(
                    name=f"🔹 {nitro_info['name']}",
                    value=f"**${nitro_info['price']}** → **{nitro_info['points']:,}** points\n30-day bonus period",
                    inline=True
                )
            
            # Subscription tiers
            embed.add_field(
                name="⭐ Server Subscriptions",
                value="Subscribe monthly for consistent bonuses!",
                inline=False
            )
            
            for sub_key, sub_info in Config.SUBSCRIPTION_TIERS.items():
                embed.add_field(
                    name=f"🔹 {sub_info['name']}",
                    value=f"**${sub_info['price']}/month** → **{sub_info['points']:,}** points\n+{sub_info['casino_bonus']*100}% casino bonus",
                    inline=True
                )
            
            embed.add_field(
                name="🎰 Casino Benefits",
                value="Higher tiers = Better odds in all casino games!",
                inline=False
            )
            
            embed.set_footer(text="Use Discord's built-in features to subscribe and get rewards!")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in tiers command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching tier information.", ephemeral=True)


@bot.tree.command(name="subscription", description="View your current subscription status and benefits")
async def subscription_status(interaction: discord.Interaction):
    """Show user's current subscription status"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            user = User.query.filter_by(id=user_id).first()

            if not user:
                await interaction.response.send_message("❌ You don't have an account yet. Use `/earn` first!", ephemeral=True)
                return

            # Get subscription info
            subscription_info = DiscordMonetizationManager.get_subscription_info(user_id)
            
            if not subscription_info['success']:
                await interaction.response.send_message(f"❌ {subscription_info['error']}", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="💎 Subscription Status",
                description="Your current subscription and benefits",
                color=0x9b59b6 if subscription_info['has_subscription'] else 0x95a5a6
            )
            
            if subscription_info['has_subscription']:
                embed.add_field(name="🎯 Current Tier", value=f"**{subscription_info['tier_name']}**", inline=True)
                embed.add_field(name="🎰 Casino Bonus", value=f"**+{subscription_info['casino_bonus']}%**", inline=True)
                embed.add_field(name="📊 Points Earned", value=f"**{subscription_info['points_earned']:,}**", inline=True)
                embed.add_field(name="📅 Started", value=f"**{subscription_info['started_at'][:10]}**", inline=True)
                
                if subscription_info['expires_at']:
                    embed.add_field(name="⏰ Expires", value=f"**{subscription_info['expires_at'][:10]}**", inline=True)
                else:
                    embed.add_field(name="⏰ Expires", value="**Never** (Permanent)", inline=True)
                
                embed.add_field(name="💳 Type", value=f"**{subscription_info['subscription_type'].title()}**", inline=True)
                
                embed.add_field(
                    name="🎰 Casino Benefits",
                    value="You get bonus multipliers on all casino winnings!",
                    inline=False
                )
            else:
                embed.add_field(name="🎯 Current Tier", value="**Free User**", inline=True)
                embed.add_field(name="🎰 Casino Bonus", value="**0%**", inline=True)
                embed.add_field(name="📊 Points Earned", value="**0**", inline=True)
                
                embed.add_field(
                    name="💡 Upgrade Benefits",
                    value="Subscribe or boost the server to get:\n• +5-15% casino bonuses\n• Exclusive rewards\n• Better odds in games",
                    inline=False
                )
            
            embed.add_field(
                name="🔗 How to Subscribe",
                value="• **Server Boosts**: Boost this server\n• **Nitro Gifts**: Gift Nitro to the server\n• **Subscriptions**: Use Discord's subscription feature",
                inline=False
            )
            
            embed.set_footer(text=f"User ID: {user_id}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in subscription command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching subscription status.", ephemeral=True)


@bot.tree.command(name="admin-pending", description="View pending transactions requiring approval (Admin only)")
async def admin_pending_transactions(interaction: discord.Interaction):
    """Show pending transactions for admin approval"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            
            # Check if user is admin
            if not AdminManager.is_admin(user_id):
                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
                return
            
            # Get pending transactions
            result = AdminManager.get_pending_transactions(limit=10)
            
            if not result['success']:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="⏳ Pending Transactions",
                description="Transactions awaiting approval",
                color=0xffa500
            )
            
            # Show wallet transactions
            if result['wallet_transactions']:
                wallet_text = ""
                for txn in result['wallet_transactions'][:5]:  # Show first 5
                    wallet_text += f"**#{txn['id']}** {txn['username']} - ${txn['amount_usd']:.2f} ({txn['points_amount']:+,} pts)\n"
                embed.add_field(name="💳 Wallet Transactions", value=wallet_text or "None", inline=False)
            
            # Show Discord transactions
            if result['discord_transactions']:
                discord_text = ""
                for txn in result['discord_transactions'][:5]:  # Show first 5
                    discord_text += f"**#{txn['id']}** {txn['username']} - {txn['tier_name']} ({txn['points_awarded']:+,} pts)\n"
                embed.add_field(name="🎮 Discord Transactions", value=discord_text or "None", inline=False)
            
            if result['total_pending'] == 0:
                embed.add_field(name="✅ Status", value="No pending transactions", inline=False)
            else:
                embed.add_field(name="📊 Total Pending", value=f"**{result['total_pending']}** transactions", inline=False)
            
            embed.add_field(
                name="🔧 Admin Actions",
                value="Use the web admin panel to approve/reject transactions:\n`/admin-panel` for the link",
                inline=False
            )
            
            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in admin-pending command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching pending transactions.", ephemeral=True)


@bot.tree.command(name="admin-panel", description="Get link to web admin panel (Admin only)")
async def admin_panel_link(interaction: discord.Interaction):
    """Provide link to web admin panel"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            
            # Check if user is admin
            if not AdminManager.is_admin(user_id):
                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
                return
            
            admin_level = AdminManager.get_admin_level(user_id)
            
            embed = discord.Embed(
                title="🔧 Admin Panel",
                description="Access the web-based admin panel",
                color=0x9b59b6
            )
            
            embed.add_field(
                name="🌐 Web Admin Panel",
                value=f"[Open Admin Panel]({Config.WEBHOOK_URL.replace('/postback', '/admin')})",
                inline=False
            )
            
            embed.add_field(name="👤 Your Level", value=f"**{admin_level.title()}**", inline=True)
            embed.add_field(name="🔑 Permissions", value="Full admin access", inline=True)
            
            embed.add_field(
                name="📋 Available Actions",
                value="• View pending transactions\n• Approve/reject transactions\n• Manage servers\n• View analytics\n• Add/remove admins",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Security Note",
                value="Keep your admin credentials secure. Only share with trusted team members.",
                inline=False
            )
            
            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in admin-panel command: {e}")
        await interaction.response.send_message("❌ An error occurred while generating admin panel link.", ephemeral=True)


@bot.tree.command(name="admin-servers", description="View server statistics (Admin only)")
async def admin_server_stats(interaction: discord.Interaction):
    """Show server statistics for admins"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            
            # Check if user is admin
            if not AdminManager.is_admin(user_id):
                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
                return
            
            # Get server stats
            result = AdminManager.get_server_stats()
            
            if not result['success']:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📊 Server Statistics",
                description="Overview of all connected servers",
                color=0x3498db
            )
            
            embed.add_field(name="🏢 Total Servers", value=f"**{result['total_servers']}**", inline=True)
            embed.add_field(name="✅ Active Servers", value=f"**{len([s for s in result['servers'] if s['is_active']])}**", inline=True)
            
            # Show server details
            if result['servers']:
                server_text = ""
                for server in result['servers'][:5]:  # Show first 5 servers
                    status = "🟢" if server['is_active'] else "🔴"
                    server_text += f"{status} **{server['server_name']}**\n"
                    server_text += f"   Users: {server['user_count']} | Transactions: {server['discord_transactions']}\n"
                
                embed.add_field(name="🏢 Server Details", value=server_text or "No servers", inline=False)
            
            embed.add_field(
                name="📈 Platform Stats",
                value=f"• Total servers: {result['total_servers']}\n• Active servers: {len([s for s in result['servers'] if s['is_active']])}\n• Total users: {sum(s['user_count'] for s in result['servers'])}",
                inline=False
            )
            
            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in admin-servers command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching server statistics.", ephemeral=True)


@bot.tree.command(name="admin-user", description="View detailed user information (Admin only)")
async def admin_user_info(interaction: discord.Interaction, user_id: str):
    """Show detailed information about a specific user"""
    try:
        with app.app_context():
            admin_user_id = str(interaction.user.id)
            
            # Check if user is admin
            if not AdminManager.is_admin(admin_user_id):
                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
                return
            
            # Get user details
            result = AdminManager.get_user_details(user_id)
            
            if not result['success']:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
                return
            
            user = result['user']
            
            # Create embed
            embed = discord.Embed(
                title=f"👤 User Profile: {user['username']}",
                description=f"User ID: `{user['id']}`",
                color=0x3498db if user['user_status'] == 'active' else 0xe74c3c
            )
            
            # Status indicator
            status_emoji = "🟢" if user['user_status'] == 'active' else "🔴" if user['user_status'] == 'banned' else "🟡"
            embed.add_field(name="Status", value=f"{status_emoji} {user['user_status'].title()}", inline=True)
            
            # Points information
            embed.add_field(name="💰 Points Balance", value=f"**{user['points_balance']:,}**", inline=True)
            embed.add_field(name="📈 Total Earned", value=f"**{user['total_earned']:,}**", inline=True)
            
            # Activity information
            embed.add_field(name="🎮 Games Played", value=f"**{user['total_games_played']}**", inline=True)
            embed.add_field(name="🎁 Gift Cards Redeemed", value=f"**{user['total_gift_cards_redeemed']}**", inline=True)
            
            # Dates
            embed.add_field(name="📅 Created", value=f"<t:{int(datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
            embed.add_field(name="🕒 Last Activity", value=f"<t:{int(datetime.fromisoformat(user['last_activity'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
            
            if user['last_earn_time']:
                embed.add_field(name="💎 Last Earn", value=f"<t:{int(datetime.fromisoformat(user['last_earn_time'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
            
            # Ban information if banned
            if user['user_status'] == 'banned':
                embed.add_field(name="🚫 Ban Reason", value=user['ban_reason'] or "No reason provided", inline=False)
                if user['banned_at']:
                    embed.add_field(name="🚫 Banned At", value=f"<t:{int(datetime.fromisoformat(user['banned_at'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
                if user['banned_by']:
                    embed.add_field(name="🚫 Banned By", value=f"<@{user['banned_by']}>", inline=True)
            
            # Recent activity
            if user['recent_games']:
                games_text = ""
                for game in user['recent_games'][:3]:
                    games_text += f"• {game['game_type'].title()}: {game['bet_amount']} → {game['win_amount']}\n"
                embed.add_field(name="🎮 Recent Games", value=games_text, inline=False)
            
            if user['recent_ads']:
                ads_text = ""
                for ad in user['recent_ads'][:3]:
                    ads_text += f"• +{ad['points_earned']} points\n"
                embed.add_field(name="📺 Recent Ads", value=ads_text, inline=False)
            
            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in admin-user command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching user information.", ephemeral=True)


@bot.tree.command(name="admin-users", description="List users with pagination (Admin only)")
async def admin_list_users(interaction: discord.Interaction, page: int = 1, status: str = None):
    """List users with pagination and optional status filter"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            
            # Check if user is admin
            if not AdminManager.is_admin(user_id):
                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
                return
            
            # Validate status filter
            if status and status not in ['active', 'banned', 'suspended']:
                await interaction.response.send_message("❌ Invalid status. Use: active, banned, or suspended", ephemeral=True)
                return
            
            # Get users
            result = AdminManager.get_users(page=page, per_page=10, status=status)
            
            if not result['success']:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"👥 Users List (Page {page})",
                description=f"Showing {len(result['users'])} of {result['pagination']['total']} users",
                color=0x3498db
            )
            
            if status:
                embed.add_field(name="🔍 Filter", value=f"Status: {status.title()}", inline=True)
            
            # User list
            if result['users']:
                users_text = ""
                for user in result['users']:
                    status_emoji = "🟢" if user['user_status'] == 'active' else "🔴" if user['user_status'] == 'banned' else "🟡"
                    users_text += f"{status_emoji} **{user['username']}**\n"
                    users_text += f"   ID: `{user['id']}` | Points: {user['points_balance']:,}\n"
                    users_text += f"   Status: {user['user_status'].title()}\n\n"
                
                embed.add_field(name="👤 Users", value=users_text, inline=False)
            else:
                embed.add_field(name="👤 Users", value="No users found", inline=False)
            
            # Pagination info
            pagination = result['pagination']
            pagination_text = f"Page {pagination['page']} of {pagination['pages']}\n"
            if pagination['has_prev']:
                pagination_text += "◀️ Previous page available\n"
            if pagination['has_next']:
                pagination_text += "▶️ Next page available"
            
            embed.add_field(name="📄 Pagination", value=pagination_text, inline=False)
            
            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
            embed.timestamp = datetime.utcnow()

            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in admin-users command: {e}")
        await interaction.response.send_message("❌ An error occurred while fetching users list.", ephemeral=True)


@bot.tree.command(name="admin-ban", description="Ban a user (Admin only)")
async def admin_ban_user(interaction: discord.Interaction, user_id: str, reason: str):
    """Ban a user with a reason"""
    try:
        with app.app_context():
            admin_user_id = str(interaction.user.id)
            
            # Check if user is admin
            if not AdminManager.is_admin(admin_user_id):
                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
                return
            
            # Ban the user
            result = AdminManager.ban_user(user_id, reason, admin_user_id)
            
            if result['success']:
                embed = discord.Embed(
                    title="🚫 User Banned",
                    description=f"User has been successfully banned",
                    color=0xe74c3c
                )
                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
                embed.add_field(name="Reason", value=reason, inline=True)
                embed.add_field(name="Banned By", value=f"<@{admin_user_id}>", inline=True)
                embed.set_footer(text=f"Admin: {interaction.user.display_name}")
                embed.timestamp = datetime.utcnow()
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)

    except Exception as e:
        logger.error(f"Error in admin-ban command: {e}")
        await interaction.response.send_message("❌ An error occurred while banning user.", ephemeral=True)


@bot.tree.command(name="admin-unban", description="Unban a user (Admin only)")
async def admin_unban_user(interaction: discord.Interaction, user_id: str):
    """Unban a user"""
    try:
        with app.app_context():
            admin_user_id = str(interaction.user.id)
            
            # Check if user is admin
            if not AdminManager.is_admin(admin_user_id):
                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
                return
            
            # Unban the user
            result = AdminManager.unban_user(user_id, admin_user_id)
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ User Unbanned",
                    description=f"User has been successfully unbanned",
                    color=0x2ecc71
                )
                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
                embed.add_field(name="Unbanned By", value=f"<@{admin_user_id}>", inline=True)
                embed.set_footer(text=f"Admin: {interaction.user.display_name}")
                embed.timestamp = datetime.utcnow()
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)

    except Exception as e:
        logger.error(f"Error in admin-unban command: {e}")
        await interaction.response.send_message("❌ An error occurred while unbanning user.", ephemeral=True)


@bot.tree.command(name="admin-adjust", description="Adjust user points (Admin only)")
async def admin_adjust_points(interaction: discord.Interaction, user_id: str, points_change: int, reason: str = None):
    """Adjust a user's points balance"""
    try:
        with app.app_context():
            admin_user_id = str(interaction.user.id)
            
            # Check if user is admin
            if not AdminManager.is_admin(admin_user_id):
                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
                return
            
            # Adjust points
            result = AdminManager.adjust_user_points(user_id, points_change, admin_user_id, reason)
            
            if result['success']:
                embed = discord.Embed(
                    title="💰 Points Adjusted",
                    description=f"User points have been successfully adjusted",
                    color=0xf39c12
                )
                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
                embed.add_field(name="Points Change", value=f"{points_change:+,}", inline=True)
                embed.add_field(name="Old Balance", value=f"{result['old_balance']:,}", inline=True)
                embed.add_field(name="New Balance", value=f"{result['new_balance']:,}", inline=True)
                if reason:
                    embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Adjusted By", value=f"<@{admin_user_id}>", inline=True)
                embed.set_footer(text=f"Admin: {interaction.user.display_name}")
                embed.timestamp = datetime.utcnow()
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)

    except Exception as e:
        logger.error(f"Error in admin-adjust command: {e}")
        await interaction.response.send_message("❌ An error occurred while adjusting user points.", ephemeral=True)


@bot.tree.command(name="admin-search", description="Search for users (Admin only)")
async def admin_search_users(interaction: discord.Interaction, query: str):
    """Search for users by username or ID"""
    try:
        with app.app_context():
            user_id = str(interaction.user.id)
            
            # Check if user is admin
            if not AdminManager.is_admin(user_id):
                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
                return
            
            # Search users
            result = AdminManager.search_users(query, limit=10)
            
            if not result['success']:
                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🔍 Search Results for '{query}'",
                description=f"Found {result['count']} users",
                color=0x3498db
            )
            
            if result['users']:
                users_text = ""
                for user in result['users']:
                    status_emoji = "🟢" if user['user_status'] == 'active' else "🔴" if user['user_status'] == 'banned' else "🟡"
                    users_text += f"{status_emoji} **{user['username']}**\n"
                    users_text += f"   ID: `{user['id']}` | Points: {user['points_balance']:,}\n"
                    users_text += f"   Status: {user['user_status'].title()}\n\n"
                
                embed.add_field(name="👤 Users", value=users_text, inline=False)
            else:
                embed.add_field(name="👤 Users", value="No users found", inline=False)
            
            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
            embed.timestamp = datetime.utcnow()
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        logger.error(f"Error in admin-search command: {e}")
        await interaction.response.send_message("❌ An error occurred while searching users.", ephemeral=True)


def run_bot():
    if not Config.DISCORD_TOKEN:
        logger.error("Discord token not found in environment variables!")
        return

    async def start_bot():
        """Start the bot with proper error handling and reconnection logic"""
        while True:
            try:
                logger.info("🤖 Starting Discord bot...")
                await bot.start(Config.DISCORD_TOKEN)
                break  # If we get here, the bot shut down normally
            except discord.LoginFailure:
                logger.error("❌ Invalid Discord token! Please check your DISCORD_TOKEN environment variable.")
                break
            except discord.ConnectionClosed as e:
                logger.error(f"❌ Discord connection closed: {e}")
                if e.code == 1000:  # Normal closure
                    logger.info("🔄 Connection closed normally, attempting to reconnect...")
                elif e.code == 4004:  # Authentication failed
                    logger.error("❌ Authentication failed. Check your bot token.")
                    break
                elif e.code == 4009:  # Session timed out
                    logger.warning("⏰ Session timed out, reconnecting...")
                else:
                    logger.warning(f"⚠️ Unexpected connection closure (code {e.code}), reconnecting...")
                
                # Wait before reconnecting
                await asyncio.sleep(bot.reconnect_delay)
                continue
            except discord.HTTPException as e:
                logger.error(f"❌ Discord HTTP error: {e}")
                if e.status == 401:  # Unauthorized
                    logger.error("❌ Bot token is invalid!")
                    break
                elif e.status == 429:  # Rate limited
                    logger.warning("⏰ Rate limited, waiting before retry...")
                    await asyncio.sleep(60)
                    continue
                else:
                    await asyncio.sleep(10)
                    continue
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                await asyncio.sleep(10)
                continue

    # Run the bot with proper event loop handling
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Fatal error running bot: {e}")
    finally:
        logger.info("✅ Bot shutdown complete")


if __name__ == "__main__":
    run_bot()
