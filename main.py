#!/usr/bin/env python3
"""
Main entry point for the Rewards Platform
Runs both the Discord bot and Flask backend simultaneously
"""

import asyncio
import threading
import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

from discord_bot import run_bot
from flask_app import run_flask
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rewards_platform.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class RewardsPlatform:
    def __init__(self):
        self.running = False
        self.bot_thread = None
        self.flask_thread = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def start(self):
        """Start both the Discord bot and Flask backend"""
        try:
            logger.info("🚀 Starting Rewards Platform...")
            
            # Start Flask backend in a separate thread
            logger.info("📡 Starting Flask backend...")
            self.flask_thread = threading.Thread(target=run_flask, daemon=True)
            self.flask_thread.start()
            
            # Give Flask a moment to start up
            import time
            time.sleep(2)
            
            # Start Discord bot in the main thread
            logger.info("🤖 Starting Discord bot...")
            self.running = True
            
            # Run the bot (this will block the main thread)
            run_bot()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Error starting platform: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the platform gracefully"""
        logger.info("🛑 Shutting down Rewards Platform...")
        self.running = False
        
        if self.executor:
            self.executor.shutdown(wait=True)
        
        logger.info("✅ Platform shutdown complete")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Validate configuration
    if not Config.DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not set in environment variables!")
        logger.error("Please set your Discord bot token and try again.")
        sys.exit(1)
    
    if not Config.DISCORD_GUILD_ID:
        logger.warning("⚠️  DISCORD_GUILD_ID not set. Bot will work in all servers.")
    
    # Print configuration summary
    logger.info("🔧 Configuration Summary:")
    logger.info(f"   Discord Bot: {'✅ Ready' if Config.DISCORD_TOKEN else '❌ No Token'}")
    logger.info(f"   Database: {Config.DATABASE_URL}")
    logger.info(f"   Webhook URL: {Config.WEBHOOK_URL}")
    logger.info(f"   Redemption Threshold: {Config.REDEMPTION_THRESHOLD:,} points")
    logger.info(f"   Points per Ad: {Config.POINTS_PER_AD} points")
    logger.info(f"   Flask Host: {Config.FLASK_HOST}:{Config.FLASK_PORT}")
    
    # Start the platform
    platform = RewardsPlatform()
    platform.start()

if __name__ == "__main__":
    main()