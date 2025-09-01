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