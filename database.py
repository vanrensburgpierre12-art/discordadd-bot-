from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(20), primary_key=True)  # Discord user ID
    username = db.Column(db.String(100), nullable=False)
    points_balance = db.Column(db.Integer, default=0)
    total_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_earn_time = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<User {self.username} (ID: {self.id})>'

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

def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    
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