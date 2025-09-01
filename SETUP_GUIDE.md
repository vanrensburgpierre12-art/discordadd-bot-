# 🚀 Quick Setup Guide

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Discord bot token and other settings
```

### 3. Run the Platform
```bash
python main.py
```

That's it! Your rewards platform is now running. 🎉

---

## 🔧 Detailed Setup

### Discord Bot Setup

1. **Create Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create New Application
   - Go to "Bot" section → Create Bot
   - Copy the bot token

2. **Configure Bot**
   - Enable required intents:
     - ✅ Message Content Intent
     - ✅ Server Members Intent
   - Copy bot token to `.env` file

3. **Invite Bot to Server**
   - Use OAuth2 → URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Administrator` (or customize)
   - Use generated invite link

### Environment Variables

Edit `.env` file:
```bash
# Required
DISCORD_TOKEN=your_bot_token_here
WEBHOOK_SECRET=your_secret_key_here
WEBHOOK_URL=https://your-domain.com/postback

# Optional (with defaults)
DISCORD_GUILD_ID=your_server_id
ADMIN_ROLE_ID=your_admin_role_id
OFFERWALL_BASE_URL=https://my-offerwall.com
REDEMPTION_THRESHOLD=1000
POINTS_PER_AD=20
```

### Test the Platform

1. **Start the platform**: `python main.py`
2. **Test webhook**: `python test_webhook.py`
3. **Check Discord bot**: Use `/balance` command
4. **Test earning**: Use `/earn` command

---

## 🌐 Deployment Options

### Option 1: Local Development
```bash
python main.py
```
- Bot runs on your machine
- Webhook accessible at `http://localhost:5000/postback`
- Good for testing and development

### Option 2: VPS Deployment
```bash
./deploy.sh
```
- Automated deployment script
- Sets up systemd service
- Configures nginx reverse proxy
- Includes monitoring and backup scripts

### Option 3: Docker Deployment
```bash
# With nginx reverse proxy
docker-compose --profile nginx up -d

# Just the platform
docker-compose up -d
```

### Option 4: Heroku/Railway
```bash
# Set environment variables
heroku config:set DISCORD_TOKEN=your_token
heroku config:set WEBHOOK_SECRET=your_secret

# Deploy
git push heroku main
```

---

## 📱 Bot Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/balance` | Check points balance | `/balance` |
| `/earn` | Get offerwall link | `/earn` |
| `/redeem` | Redeem for gift card | `/redeem` |
| `/leaderboard` | Show top users | `/leaderboard` |
| `/addpoints` | Admin: add points | `/addpoints @user 100` |

---

## 🔗 Webhook Integration

### For Ad Networks

Send POST requests to `/postback`:
```json
{
  "uid": "discord_user_id",
  "points": 20,
  "offer_id": "unique_offer_id"
}
```

### Test Webhook
```bash
curl -X POST http://localhost:5000/postback \
  -H "Content-Type: application/json" \
  -d '{"uid": "123456789", "points": 20, "offer_id": "test_offer"}'
```

---

## 🚨 Common Issues

### Bot Not Responding
- ✅ Check bot token in `.env`
- ✅ Verify bot has correct permissions
- ✅ Check bot is online in Discord
- ✅ Ensure intents are enabled

### Webhook Not Working
- ✅ Check webhook URL is correct
- ✅ Verify server is accessible
- ✅ Check firewall settings
- ✅ Review webhook logs

### Points Not Updating
- ✅ Check webhook is being called
- ✅ Verify user exists in database
- ✅ Check for duplicate offer IDs
- ✅ Review application logs

---

## 📊 Monitoring

### Check Status
```bash
# Service status
sudo systemctl status rewards-platform

# Application logs
tail -f rewards_platform.log

# System logs
sudo journalctl -u rewards-platform -f
```

### Health Check
```bash
curl http://localhost:5000/health
```

### Platform Stats
```bash
curl http://localhost:5000/stats
```

---

## 🔄 Updates

### Update Platform
```bash
git pull origin main
pip install -r requirements.txt
sudo systemctl restart rewards-platform
```

### Backup Database
```bash
# Manual backup
cp rewards.db backup_$(date +%Y%m%d).db

# Automated backup (if using deploy script)
/usr/local/bin/backup-rewards-platform
```

---

## 🆘 Need Help?

1. **Check logs**: `tail -f rewards_platform.log`
2. **Verify config**: Check `.env` file
3. **Test endpoints**: Use `python test_webhook.py`
4. **Review README**: Full documentation available
5. **Check status**: Use monitoring commands

---

**Happy Rewarding! 🎮✨**