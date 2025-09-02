from datetime import datetime
import uuid
from app_context import db

class Server(db.Model):
    __tablename__ = 'servers'
    
    id = db.Column(db.String(20), primary_key=True)  # Discord server ID
    name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Server-specific settings
    points_per_ad = db.Column(db.Integer, default=20)
    redemption_threshold = db.Column(db.Integer, default=1000)
    casino_min_bet = db.Column(db.Integer, default=10)
    casino_max_bet = db.Column(db.Integer, default=500)
    casino_daily_limit = db.Column(db.Integer, default=1000)
    
    def __repr__(self):
        return f'<Server {self.name} (ID: {self.id})>'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(20), primary_key=True)  # Discord user ID
    username = db.Column(db.String(100), nullable=False)
    points_balance = db.Column(db.Integer, default=0)
    total_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_earn_time = db.Column(db.DateTime, nullable=True)
    
    # User management fields
    user_status = db.Column(db.String(20), default='active')  # 'active', 'banned', 'suspended'
    ban_reason = db.Column(db.Text, nullable=True)
    banned_at = db.Column(db.DateTime, nullable=True)
    banned_by = db.Column(db.String(20), nullable=True)  # Admin user ID who banned
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    total_games_played = db.Column(db.Integer, default=0)
    total_gift_cards_redeemed = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<User {self.username} (ID: {self.id}, Status: {self.user_status})>'

class GiftCard(db.Model):
    __tablename__ = 'gift_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Amount in currency
    currency = db.Column(db.String(20), default='Robux')  # Robux, USD, etc.
    category_id = db.Column(db.Integer, db.ForeignKey('gift_card_categories.id'), nullable=True)
    used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.String(20), nullable=True)  # Discord user ID
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GiftCard {self.code} ({self.amount} {self.currency})>'

class AdCompletion(db.Model):
    __tablename__ = 'ad_completions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    offer_id = db.Column(db.String(100), nullable=False)
    points_earned = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    
    def __repr__(self):
        return f'<AdCompletion User: {self.user_id}, Offer: {self.offer_id}>'

class CasinoGame(db.Model):
    __tablename__ = 'casino_games'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)  # 'dice', 'slots', 'blackjack', etc.
    bet_amount = db.Column(db.Integer, nullable=False)
    win_amount = db.Column(db.Integer, default=0)
    result = db.Column(db.String(100), nullable=False)  # Game result details
    played_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CasinoGame User: {self.user_id}, Game: {self.game_type}, Bet: {self.bet_amount}>'

class DailyCasinoLimit(db.Model):
    __tablename__ = 'daily_casino_limits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, unique=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    total_won = db.Column(db.Integer, default=0)
    total_lost = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<DailyCasinoLimit User: {self.user_id}, Date: {self.date}>'

class WalletTransaction(db.Model):
    __tablename__ = 'wallet_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'deposit', 'withdrawal', 'bonus', 'refund'
    amount_usd = db.Column(db.Numeric(10, 2), nullable=False)  # Amount in USD
    points_amount = db.Column(db.Integer, nullable=False)  # Points added/removed
    payment_method = db.Column(db.String(50), nullable=True)  # 'stripe', 'paypal', 'crypto', etc.
    payment_id = db.Column(db.String(100), nullable=True)  # External payment ID
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<WalletTransaction User: {self.user_id}, Type: {self.transaction_type}, Amount: ${self.amount_usd}>'

class UserWallet(db.Model):
    __tablename__ = 'user_wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, unique=True)
    total_deposited = db.Column(db.Numeric(10, 2), default=0.00)  # Total USD deposited
    total_withdrawn = db.Column(db.Numeric(10, 2), default=0.00)  # Total USD withdrawn
    lifetime_bonus = db.Column(db.Integer, default=0)  # Total bonus points received
    last_deposit_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserWallet User: {self.user_id}, Deposited: ${self.total_deposited}>'

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, unique=True)
    subscription_tier = db.Column(db.String(20), nullable=True)  # 'basic', 'premium', 'vip', None
    subscription_type = db.Column(db.String(20), nullable=True)  # 'discord_subscription', 'server_boost', 'nitro_gift'
    points_earned = db.Column(db.Integer, default=0)  # Points earned from this subscription
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # For time-limited subscriptions
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<UserSubscription User: {self.user_id}, Tier: {self.subscription_tier}>'

class DiscordTransaction(db.Model):
    __tablename__ = 'discord_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    server_id = db.Column(db.String(20), nullable=False)  # Which server the transaction happened in
    transaction_type = db.Column(db.String(20), nullable=False)  # 'server_boost', 'nitro_gift', 'subscription'
    tier_name = db.Column(db.String(50), nullable=False)
    points_awarded = db.Column(db.Integer, nullable=False)
    discord_data = db.Column(db.Text, nullable=True)  # JSON data from Discord
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    approved_by = db.Column(db.String(20), nullable=True)  # Admin who approved
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DiscordTransaction User: {self.user_id}, Type: {self.transaction_type}>'

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False)
    admin_level = db.Column(db.String(20), default='moderator')  # 'moderator', 'admin', 'super_admin'
    can_approve_transactions = db.Column(db.Boolean, default=True)
    can_manage_servers = db.Column(db.Boolean, default=False)
    can_view_all_data = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(20), nullable=True)
    
    def __repr__(self):
        return f'<AdminUser {self.username} (Level: {self.admin_level})>'

class TransactionApproval(db.Model):
    __tablename__ = 'transaction_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, nullable=False)  # References WalletTransaction or DiscordTransaction
    transaction_type = db.Column(db.String(20), nullable=False)  # 'wallet', 'discord'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    requested_by = db.Column(db.String(20), nullable=False)  # User who requested
    approved_by = db.Column(db.String(20), nullable=True)  # Admin who approved
    rejection_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<TransactionApproval Transaction: {self.transaction_id}, Status: {self.status}>'

def init_db():
    """Initialize the database"""
    from app_context import app
    
    with app.app_context():
        db.create_all()
        
        # Add some sample gift cards if none exist
        if GiftCard.query.count() == 0:
            sample_cards = [
                GiftCard(code=f"ROBUX_{uuid.uuid4().hex[:8].upper()}", amount=100),
                GiftCard(code=f"ROBUX_{uuid.uuid4().hex[:8].upper()}", amount=200),
                GiftCard(code=f"ROBUX_{uuid.uuid4().hex[:8].upper()}", amount=500),
                GiftCard(code=f"ROBUX_{uuid.uuid4().hex[:8].upper()}", amount=1000),
                GiftCard(code=f"ROBUX_{uuid.uuid4().hex[:8].upper()}", amount=2000),
            ]
            db.session.add_all(sample_cards)
            db.session.commit()

# New Models for Enhanced Features

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, unique=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    xp_to_next_level = db.Column(db.Integer, default=100)
    total_wins = db.Column(db.Integer, default=0)
    total_losses = db.Column(db.Integer, default=0)
    win_streak = db.Column(db.Integer, default=0)
    best_win_streak = db.Column(db.Integer, default=0)
    favorite_game = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProfile User: {self.user_id}, Level: {self.level}>'

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100), nullable=False)  # Emoji or icon name
    category = db.Column(db.String(50), nullable=False)  # 'casino', 'social', 'economy', 'special'
    requirement_type = db.Column(db.String(50), nullable=False)  # 'points_earned', 'games_played', 'streak', etc.
    requirement_value = db.Column(db.Integer, nullable=False)
    points_reward = db.Column(db.Integer, default=0)
    is_hidden = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Achievement {self.name}>'

class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    points_awarded = db.Column(db.Integer, default=0)
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),)
    
    def __repr__(self):
        return f'<UserAchievement User: {self.user_id}, Achievement: {self.achievement_id}>'

class Challenge(db.Model):
    __tablename__ = 'challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    challenge_type = db.Column(db.String(50), nullable=False)  # 'daily', 'weekly', 'monthly'
    requirement_type = db.Column(db.String(50), nullable=False)  # 'earn_points', 'play_games', 'win_games', etc.
    requirement_value = db.Column(db.Integer, nullable=False)
    points_reward = db.Column(db.Integer, nullable=False)
    bonus_multiplier = db.Column(db.Float, default=1.0)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Challenge {self.name} ({self.challenge_type})>'

class UserChallenge(db.Model):
    __tablename__ = 'user_challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    progress = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    points_earned = db.Column(db.Integer, default=0)
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', name='unique_user_challenge'),)
    
    def __repr__(self):
        return f'<UserChallenge User: {self.user_id}, Challenge: {self.challenge_id}>'

class Leaderboard(db.Model):
    __tablename__ = 'leaderboards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    leaderboard_type = db.Column(db.String(50), nullable=False)  # 'points', 'wins', 'streak', 'xp'
    period = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'all_time'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Leaderboard {self.name} ({self.leaderboard_type})>'

class LeaderboardEntry(db.Model):
    __tablename__ = 'leaderboard_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    leaderboard_id = db.Column(db.Integer, db.ForeignKey('leaderboards.id'), nullable=False)
    user_id = db.Column(db.String(20), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=True)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('leaderboard_id', 'user_id', 'period_start', name='unique_leaderboard_entry'),)
    
    def __repr__(self):
        return f'<LeaderboardEntry User: {self.user_id}, Score: {self.score}, Rank: {self.rank}>'

class Tournament(db.Model):
    __tablename__ = 'tournaments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    game_type = db.Column(db.String(50), nullable=False)  # 'dice', 'slots', 'blackjack', 'roulette', 'poker'
    entry_fee = db.Column(db.Integer, nullable=False)
    max_participants = db.Column(db.Integer, nullable=False)
    prize_pool = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='upcoming')  # 'upcoming', 'active', 'completed', 'cancelled'
    created_by = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tournament {self.name} ({self.game_type})>'

class TournamentParticipant(db.Model):
    __tablename__ = 'tournament_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    user_id = db.Column(db.String(20), nullable=False)
    entry_fee_paid = db.Column(db.Boolean, default=False)
    final_score = db.Column(db.Integer, default=0)
    final_rank = db.Column(db.Integer, nullable=True)
    prize_earned = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('tournament_id', 'user_id', name='unique_tournament_participant'),)
    
    def __repr__(self):
        return f'<TournamentParticipant User: {self.user_id}, Tournament: {self.tournament_id}>'

class Referral(db.Model):
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.String(20), nullable=False)  # User who referred
    referred_id = db.Column(db.String(20), nullable=False)  # User who was referred
    referral_code = db.Column(db.String(20), nullable=False, unique=True)
    points_earned = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Referral {self.referrer_id} -> {self.referred_id}>'

class DailyBonus(db.Model):
    __tablename__ = 'daily_bonuses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, unique=True)
    current_streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    last_claim_date = db.Column(db.Date, nullable=True)
    total_claimed = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DailyBonus User: {self.user_id}, Streak: {self.current_streak}>'

class SeasonalEvent(db.Model):
    __tablename__ = 'seasonal_events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_type = db.Column(db.String(50), nullable=False)  # 'holiday', 'special', 'anniversary'
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    bonus_multiplier = db.Column(db.Float, default=1.0)
    special_rewards = db.Column(db.Text, nullable=True)  # JSON string of special rewards
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SeasonalEvent {self.name}>'

class GiftCardCategory(db.Model):
    __tablename__ = 'gift_card_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(100), nullable=False)  # Emoji or icon
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GiftCardCategory {self.name}>'

class Friend(db.Model):
    __tablename__ = 'friends'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)  # User who sent the request
    friend_id = db.Column(db.String(20), nullable=False)  # User who received the request
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'blocked'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime, nullable=True)
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),)
    
    def __repr__(self):
        return f'<Friend {self.user_id} -> {self.friend_id} ({self.status})>'

class Guild(db.Model):
    __tablename__ = 'guilds'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.String(20), nullable=False)
    icon_url = db.Column(db.String(500), nullable=True)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)
    member_count = db.Column(db.Integer, default=0)
    max_members = db.Column(db.Integer, default=50)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Guild {self.name} (Level {self.level})>'

class GuildMember(db.Model):
    __tablename__ = 'guild_members'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    user_id = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), default='member')  # 'owner', 'admin', 'member'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    contributed_points = db.Column(db.Integer, default=0)
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('guild_id', 'user_id', name='unique_guild_member'),)
    
    def __repr__(self):
        return f'<GuildMember User: {self.user_id}, Guild: {self.guild_id}, Role: {self.role}>'

class UserRanking(db.Model):
    __tablename__ = 'user_rankings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, unique=True)
    overall_rank = db.Column(db.Integer, nullable=True)
    points_rank = db.Column(db.Integer, nullable=True)
    wins_rank = db.Column(db.Integer, nullable=True)
    streak_rank = db.Column(db.Integer, nullable=True)
    xp_rank = db.Column(db.Integer, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserRanking User: {self.user_id}, Overall: {self.overall_rank}>'