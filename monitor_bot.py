#!/usr/bin/env python3
"""
Discord Bot Connection Monitor
Simple script to monitor the Discord bot connection status
"""

import requests
import json
import time
import sys
from datetime import datetime

def check_bot_status(base_url="http://localhost:5000"):
    """Check the Discord bot status via the Flask API"""
    try:
        # Check health endpoint
        health_response = requests.get(f"{base_url}/health", timeout=10)
        health_data = health_response.json()
        
        # Check detailed Discord status
        discord_response = requests.get(f"{base_url}/discord-status", timeout=10)
        discord_data = discord_response.json()
        
        return health_data, discord_data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to API: {e}")
        return None, None

def format_uptime(seconds):
    """Format uptime in a human-readable way"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def main():
    """Main monitoring loop"""
    print("🤖 Discord Bot Connection Monitor")
    print("=" * 50)
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    while True:
        try:
            health_data, discord_data = check_bot_status(base_url)
            
            if health_data and discord_data:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Overall status
                overall_status = health_data.get('status', 'unknown')
                status_emoji = "🟢" if overall_status == "healthy" else "🔴"
                print(f"\n[{timestamp}] {status_emoji} Overall Status: {overall_status.upper()}")
                
                # Database status
                db_status = health_data.get('database', 'unknown')
                db_emoji = "🟢" if db_status == "healthy" else "🔴"
                print(f"  📊 Database: {db_emoji} {db_status}")
                
                # Discord bot status
                discord_status = discord_data.get('status', 'unknown')
                discord_emoji = "🟢" if discord_status == "connected" else "🔴"
                print(f"  🤖 Discord Bot: {discord_emoji} {discord_status}")
                
                if discord_status == "connected":
                    # Show detailed info
                    uptime = discord_data.get('uptime_seconds', 0)
                    latency = discord_data.get('latency')
                    guilds = discord_data.get('guilds', 0)
                    users = discord_data.get('users', 0)
                    errors = discord_data.get('recent_errors', 0)
                    
                    print(f"    ⏱️  Uptime: {format_uptime(uptime)}")
                    if latency:
                        print(f"    📡 Latency: {latency}ms")
                    print(f"    🏰 Guilds: {guilds}")
                    print(f"    👥 Users: {users}")
                    if errors > 0:
                        print(f"    ⚠️  Recent Errors: {errors}")
                
                # Connection attempts
                attempts = discord_data.get('connection_attempts', 0)
                if attempts > 0:
                    print(f"    🔄 Connection Attempts: {attempts}")
                
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Unable to connect to API")
            
            # Wait before next check
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()