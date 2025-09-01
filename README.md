# 🎮 Discord Rewards Platform

A comprehensive Discord bot + backend system that rewards users with Roblox gift cards for watching ads and completing offers.

## ✨ Features

- **Discord Bot Commands**
  - `/balance` - Check your points balance
  - `/earn` - Get a unique offerwall link to earn points
  - `/redeem` - Redeem points for Roblox gift cards
  - `/addpoints` - Admin command to manually adjust points
  - `/leaderboard` - Show top users by points

- **Ad Network Integration**
  - Personalized offerwall links for each user
  - Webhook handling for ad completion callbacks
  - Automatic points distribution
  - Duplicate prevention and security measures

- **Gift Card System**
  - Roblox gift card redemption
  - Configurable redemption threshold
  - Secure code delivery via DM
  - Gift card inventory management

- **Security Features**
  - Rate limiting on earn commands
  - Webhook signature verification
  - Duplicate offer completion prevention
  - Admin-only commands

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Discord Bot Token
- Offerwall/Ad Network Account
- VPS or hosting service

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd discord-rewards-platform

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 3. Configuration

Edit `.env` file with your settings:

```bash
# Discord Bot
DISCORD_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_server_id_here
ADMIN_ROLE_ID=your_admin_role_id_here

# Webhook
WEBHOOK_SECRET=your_secret_key_here
WEBHOOK_URL=https://your-domain.com/postback

# Offerwall
OFFERWALL_BASE_URL=https://your-offerwall.com
```

### 4. Run the Platform

```bash
# Run both bot and backend
python main.py

# Or run separately:
# Terminal 1: Discord Bot
python discord_bot.py

# Terminal 2: Flask Backend
python flask_app.py
```

## 🔧 Discord Bot Setup

### 1. Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application
3. Go to "Bot" section
4. Create bot and copy token
5. Enable required intents:
   - Message Content Intent
   - Server Members Intent

### 2. Invite Bot to Server

Use this invite link (replace `YOUR_CLIENT_ID`):
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2147483648&scope=bot%20applications.commands
```

### 3. Bot Commands

The bot automatically registers slash commands on startup:

- `/balance` - View your points balance
- `/earn` - Get offerwall link to earn points
- `/redeem` - Redeem points for gift card
- `/leaderboard` - View top users
- `/addpoints <user> <amount>` - Admin command

## 🌐 Backend API

### Endpoints

- `GET /` - Home page with platform info
- `GET /health` - Health check
- `GET /stats` - Platform statistics
- `POST /postback` - Webhook for ad networks
- `GET /postback` - Webhook test interface

### Webhook Format

Ad networks should send POST requests to `/postback`:

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

## 🗄️ Database Schema

### Users Table
- `id` - Discord user ID (primary key)
- `username` - Discord username
- `points_balance` - Current points balance
- `total_earned` - Total points earned
- `created_at` - Account creation timestamp
- `last_earn_time` - Last earn command usage

### Gift Cards Table
- `id` - Auto-increment ID
- `code` - Gift card code (unique)
- `amount` - Robux amount
- `used` - Whether code has been redeemed
- `used_by` - Discord user ID who redeemed it
- `used_at` - Redemption timestamp

### Ad Completions Table
- `id` - Auto-increment ID
- `user_id` - Discord user ID
- `offer_id` - Unique offer identifier
- `points_earned` - Points awarded
- `completed_at` - Completion timestamp
- `ip_address` - IP address for security

## 🚀 Deployment

### VPS Deployment

1. **Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install nginx (optional, for reverse proxy)
sudo apt install nginx -y
```

2. **Application Setup**
```bash
# Create app directory
mkdir /opt/rewards-platform
cd /opt/rewards-platform

# Copy application files
# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your values
```

3. **Systemd Service**
```bash
sudo nano /etc/systemd/system/rewards-platform.service
```

```ini
[Unit]
Description=Discord Rewards Platform
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/rewards-platform
Environment=PATH=/opt/rewards-platform/venv/bin
ExecStart=/opt/rewards-platform/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. **Enable and Start**
```bash
sudo systemctl daemon-reload
sudo systemctl enable rewards-platform
sudo systemctl start rewards-platform
sudo systemctl status rewards-platform
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "main.py"]
```

```bash
docker build -t rewards-platform .
docker run -d --name rewards-platform -p 5000:5000 --env-file .env rewards-platform
```

### Heroku Deployment

1. **Create Heroku App**
```bash
heroku create your-rewards-app
heroku config:set DISCORD_TOKEN=your_token
heroku config:set WEBHOOK_SECRET=your_secret
# Set other environment variables
```

2. **Deploy**
```bash
git push heroku main
```

## 🔒 Security Considerations

### Webhook Security
- Use HTTPS for production
- Implement signature verification
- Rate limit webhook endpoints
- Validate all incoming data

### Bot Security
- Keep bot token secret
- Use environment variables
- Implement role-based permissions
- Rate limit commands

### Database Security
- Use prepared statements
- Validate user input
- Implement proper access controls
- Regular backups

## 📊 Monitoring & Maintenance

### Logs
- Application logs: `rewards_platform.log`
- System logs: `journalctl -u rewards-platform`

### Health Checks
- `/health` endpoint for monitoring
- Database connection checks
- Bot status monitoring

### Backup
```bash
# Database backup
sqlite3 rewards.db ".backup backup_$(date +%Y%m%d).db"

# Configuration backup
cp .env .env.backup
```

## 🧪 Testing

### Local Testing
```bash
# Test Discord bot
python discord_bot.py

# Test Flask backend
python flask_app.py

# Test webhook
curl -X POST http://localhost:5000/postback \
  -H "Content-Type: application/json" \
  -d '{"uid": "test_user", "points": 50, "offer_id": "test_123"}'
```

### Integration Testing
1. Set up test Discord server
2. Configure test offerwall
3. Test complete user flow
4. Verify points and redemptions

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check bot token
   - Verify bot permissions
   - Check intents configuration

2. **Database errors**
   - Verify database file permissions
   - Check SQLite installation
   - Review database schema

3. **Webhook not working**
   - Check webhook URL
   - Verify signature verification
   - Check firewall settings

4. **Points not updating**
   - Check webhook logs
   - Verify user exists in database
   - Check offer completion tracking

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=True
python main.py
```

## 📈 Scaling Considerations

### Database
- Migrate to PostgreSQL/MySQL for production
- Implement connection pooling
- Add database indexes

### Performance
- Implement caching (Redis)
- Add load balancing
- Use async processing

### Monitoring
- Add metrics collection
- Implement alerting
- Performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for errors

---

**Happy Rewarding! 🎉**