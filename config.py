import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord Bot Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))
    ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', 0))
    
    # Database Configuration
    DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
    DATA_DIR.mkdir(parents=True, exist_ok=True)  # make sure dir exists

    # Default to PostgreSQL for production, SQLite for development
    DEFAULT_DB = DATA_DIR / "rewards.db"
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rewards_user:rewards_pass@localhost:5432/rewards_db")

    
    # Webhook Configuration
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-secret-key')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-domain.com/postback')
    
    # Offerwall Configuration
    OFFERWALL_BASE_URL = os.getenv('OFFERWALL_BASE_URL', 'https://my-offerwall.com')
    
    # Points Configuration
    REDEMPTION_THRESHOLD = int(os.getenv('REDEMPTION_THRESHOLD', 1000))
    POINTS_PER_AD = int(os.getenv('POINTS_PER_AD', 20))
    
    # Casino Configuration
    CASINO_MIN_BET = int(os.getenv('CASINO_MIN_BET', 10))
    CASINO_MAX_BET = int(os.getenv('CASINO_MAX_BET', 500))
    CASINO_DAILY_LIMIT = int(os.getenv('CASINO_DAILY_LIMIT', 1000))  # Max points that can be won/lost per day
    CASINO_HOUSE_EDGE = float(os.getenv('CASINO_HOUSE_EDGE', 0.05))  # 5% house edge
    
    # Wallet Configuration
    POINTS_PER_DOLLAR = int(os.getenv('POINTS_PER_DOLLAR', 100))  # 100 points per $1
    MIN_DEPOSIT = float(os.getenv('MIN_DEPOSIT', 5.00))  # Minimum $5 deposit
    MAX_DEPOSIT = float(os.getenv('MAX_DEPOSIT', 100.00))  # Maximum $100 deposit
    WALLET_BONUS_PERCENTAGE = float(os.getenv('WALLET_BONUS_PERCENTAGE', 0.10))  # 10% bonus on deposits
    
    # Discord Monetization
    SERVER_BOOST_REWARDS = {
        "level_1": {"boosts": 2, "points": 1000, "name": "Level 1 Boost"},
        "level_2": {"boosts": 7, "points": 2500, "name": "Level 2 Boost"}, 
        "level_3": {"boosts": 14, "points": 5000, "name": "Level 3 Boost"}
    }
    
    NITRO_GIFT_REWARDS = {
        "nitro_classic": {"price": 4.99, "points": 5000, "name": "Nitro Classic"},
        "nitro_full": {"price": 9.99, "points": 10000, "name": "Nitro Full"}
    }
    
    # Server Subscription Tiers
    SUBSCRIPTION_TIERS = {
        "basic": {"price": 2.99, "points": 2000, "name": "Basic", "casino_bonus": 0.05},
        "premium": {"price": 4.99, "points": 4000, "name": "Premium", "casino_bonus": 0.10},
        "vip": {"price": 9.99, "points": 10000, "name": "VIP", "casino_bonus": 0.15}
    }
    
    # Rate Limiting
    EARN_COOLDOWN = int(os.getenv('EARN_COOLDOWN', 300))  # 5 minutes
    CASINO_COOLDOWN = int(os.getenv('CASINO_COOLDOWN', 30))  # 30 seconds between casino games
    
    # Flask Configuration
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-flask-secret-key')
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

