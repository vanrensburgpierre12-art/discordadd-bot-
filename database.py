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
    amount = db.Column(db.Integer, nullable=False)  # Robux amount
    used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.String(20), nullable=True)  # Discord user ID
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GiftCard {self.code} ({self.amount} Robux)>'

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