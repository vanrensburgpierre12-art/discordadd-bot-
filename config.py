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

    DEFAULT_DB = DATA_DIR / "rewards.db"
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")

    
    # Webhook Configuration
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-secret-key')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-domain.com/postback')
    
    # Offerwall Configuration
    OFFERWALL_BASE_URL = os.getenv('OFFERWALL_BASE_URL', 'https://my-offerwall.com')
    
    # Points Configuration
    REDEMPTION_THRESHOLD = int(os.getenv('REDEMPTION_THRESHOLD', 1000))
    POINTS_PER_AD = int(os.getenv('POINTS_PER_AD', 20))
    
    # Rate Limiting
    EARN_COOLDOWN = int(os.getenv('EARN_COOLDOWN', 300))  # 5 minutes
    
    # Flask Configuration
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-flask-secret-key')
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

