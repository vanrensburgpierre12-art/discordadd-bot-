# 🎮 Discord Rewards Platform

A comprehensive Discord bot + backend system that rewards users with Roblox gift cards for watching ads, playing casino games, and subscribing to premium tiers.

## ✨ Features

### 🎯 **Core Rewards System**
- **Ad Network Integration** - Personalized offerwall links for each user
- **Webhook Handling** - Automatic points distribution from ad completions
- **Gift Card System** - Roblox gift card redemption with secure DM delivery
- **Rate Limiting** - Prevents spam and ensures fair usage

### 🎰 **Casino Gaming Platform**
- **Dice Game** - Roll dice and guess numbers for 5x multiplier
- **Slot Machine** - Spin reels for matching symbol combinations
- **Blackjack** - Beat the dealer to 21 with realistic card gameplay
- **Daily Limits** - Configurable daily win/loss limits
- **House Edge** - Configurable casino house edge for sustainability

### 💳 **Wallet & Payment System**
- **Cash Deposits** - Add real money to get bonus points
- **Withdrawal System** - Convert points back to cash via PayPal
- **Deposit Packages** - Tiered packages with bonus percentages
- **Transaction History** - Complete transaction tracking and management

### 💎 **Discord Monetization Integration**
- **Server Boosts** - Reward users for boosting your server
- **Nitro Gifts** - Points for gifting Nitro to the server
- **Server Subscriptions** - Monthly subscription tiers with casino bonuses
- **Tier Benefits** - Higher tiers get better casino odds and exclusive rewards

### 🔧 **Admin Management System**
- **Web Admin Panel** - Full web interface for transaction management
- **Pending Approvals** - Review and approve wallet transactions
- **Server Analytics** - Track server performance and user engagement
- **Admin Commands** - Discord-based admin tools for quick management

### 🛡️ **Security & Anti-Fraud**
- **Webhook Signature Verification** - Secure webhook processing
- **Duplicate Prevention** - Prevents double-spending and fraud
- **Admin Role Verification** - Secure admin-only commands
- **Transaction Validation** - Comprehensive input validation

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

# Points Configuration
REDEMPTION_THRESHOLD=1000
POINTS_PER_AD=20

# Casino Configuration
CASINO_MIN_BET=10
CASINO_MAX_BET=500
CASINO_DAILY_LIMIT=1000
CASINO_HOUSE_EDGE=0.05
CASINO_COOLDOWN=30

# Wallet Configuration
POINTS_PER_DOLLAR=100
MIN_DEPOSIT=5.00
MAX_DEPOSIT=100.00
WALLET_BONUS_PERCENTAGE=0.10

# Rate Limiting
EARN_COOLDOWN=300

# Flask Configuration
FLASK_SECRET_KEY=your_flask_secret_key
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
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

#### 🎯 **Main Commands**
- `/balance` - Check your current points balance
- `/earn` - Get a link to earn points by watching ads
- `/redeem` - Redeem points for a Roblox gift card

#### 🎰 **Casino Commands**
- `/casino` - View casino information and daily limits
- `/dice <bet> <guess>` - Roll the dice and guess the number (1-6)
- `/slots <bet>` - Spin the slot machine
- `/blackjack <bet>` - Play a game of blackjack

#### 💳 **Wallet Commands**
- `/wallet` - View your wallet information and deposit packages
- `/deposit` - Get deposit packages and payment information
- `/withdraw <amount_usd>` - Request a withdrawal (convert points to cash)

#### 💎 **Subscription Commands**
- `/tiers` - View available subscription tiers and their benefits
- `/subscription` - View your current subscription status and benefits

#### 🔧 **Admin Commands**
- `/admin-pending` - View pending transactions requiring approval (Admin only)
- `/admin-panel` - Get link to web admin panel (Admin only)
- `/admin-servers` - View server statistics (Admin only)

## 🌐 Backend API

### Endpoints

#### 🏠 **Public Endpoints**
- `GET /` - Home page with platform info
- `GET /health` - Health check endpoint
- `GET /stats` - Platform statistics

#### 🎯 **Rewards System**
- `POST /postback` - Webhook for ad networks
- `GET /postback` - Webhook test interface

#### 💳 **Wallet System**
- `GET /wallet` - Wallet management interface
- `POST /wallet/deposit` - Process deposit transactions
- `POST /wallet/withdraw` - Process withdrawal requests
- `GET /wallet/transactions` - Get transaction history

#### 🎰 **Casino System**
- `GET /casino` - Casino game interface
- `POST /casino/dice` - Process dice game
- `POST /casino/slots` - Process slots game
- `POST /casino/blackjack` - Process blackjack game

#### 💎 **Discord Monetization**
- `POST /discord/boost` - Handle server boost rewards
- `POST /discord/nitro` - Handle Nitro gift rewards
- `POST /discord/subscription` - Handle subscription rewards

#### 🔧 **Admin Panel**
- `GET /admin` - Admin panel interface
- `GET /admin/transactions` - View pending transactions
- `POST /admin/approve` - Approve transactions
- `POST /admin/reject` - Reject transactions
- `GET /admin/servers` - Server analytics
- `GET /admin/users` - User management

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

### 👤 **Users Table**
- `id` - Discord user ID (primary key)
- `username` - Discord username
- `points_balance` - Current points balance
- `total_earned` - Total points earned
- `created_at` - Account creation timestamp
- `last_earn_time` - Last earn command usage

### 🎫 **Gift Cards Table**
- `id` - Auto-increment ID
- `code` - Gift card code (unique)
- `amount` - Robux amount
- `used` - Whether code has been redeemed
- `used_by` - Discord user ID who redeemed it
- `used_at` - Redemption timestamp

### 📺 **Ad Completions Table**
- `id` - Auto-increment ID
- `user_id` - Discord user ID
- `offer_id` - Unique offer identifier
- `points_earned` - Points awarded
- `completed_at` - Completion timestamp
- `ip_address` - IP address for security

### 🎰 **Casino Tables**
#### Daily Casino Limits
- `id` - Auto-increment ID
- `user_id` - Discord user ID
- `date` - Date of the limit
- `total_won` - Total points won today
- `total_lost` - Total points lost today
- `games_played` - Number of games played today

### 💳 **Wallet Tables**
#### User Wallets
- `id` - Auto-increment ID
- `user_id` - Discord user ID
- `total_deposited` - Total cash deposited
- `total_withdrawn` - Total cash withdrawn
- `lifetime_bonus` - Total bonus points earned
- `created_at` - Wallet creation timestamp

#### Wallet Transactions
- `id` - Auto-increment ID
- `user_id` - Discord user ID
- `transaction_type` - 'deposit' or 'withdrawal'
- `amount_usd` - Cash amount
- `points_amount` - Points amount
- `status` - 'pending', 'completed', 'rejected'
- `created_at` - Transaction timestamp

### 💎 **Discord Monetization Tables**
#### User Subscriptions
- `id` - Auto-increment ID
- `user_id` - Discord user ID
- `subscription_type` - 'boost', 'nitro', 'subscription'
- `tier_name` - Subscription tier name
- `points_awarded` - Points awarded for subscription
- `casino_bonus` - Casino bonus multiplier
- `started_at` - Subscription start date
- `expires_at` - Subscription expiration date

#### Discord Transactions
- `id` - Auto-increment ID
- `user_id` - Discord user ID
- `transaction_type` - Type of Discord transaction
- `tier_name` - Subscription tier
- `points_awarded` - Points awarded
- `processed_at` - Processing timestamp

### 🏢 **Server Management Tables**
#### Servers
- `id` - Discord server ID
- `server_name` - Server name
- `owner_id` - Server owner Discord ID
- `is_active` - Whether bot is still in server
- `created_at` - Server registration timestamp
- `last_activity` - Last activity timestamp

#### Admin Users
- `id` - Auto-increment ID
- `user_id` - Discord user ID
- `admin_level` - Admin permission level
- `created_at` - Admin assignment timestamp

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

## 🎮 **New Features Guide**

### 🎰 **Casino System**
The casino system includes three games with configurable odds and daily limits:

- **Dice Game**: Guess 1-6, win 5x your bet if correct
- **Slot Machine**: Match symbols for various multipliers
- **Blackjack**: Beat the dealer to 21 with realistic gameplay

**Casino Configuration:**
- Set `CASINO_DAILY_LIMIT` to control max daily wins/losses
- Adjust `CASINO_HOUSE_EDGE` for sustainability (default 5%)
- Configure `CASINO_COOLDOWN` between games (default 30 seconds)

### 💳 **Wallet System**
Users can deposit real money and withdraw points as cash:

- **Deposits**: Add cash via Stripe/PayPal for bonus points
- **Withdrawals**: Convert points to cash via PayPal
- **Packages**: Tiered deposit packages with bonus percentages
- **Admin Approval**: All withdrawals require admin approval

### 💎 **Discord Monetization**
Integrate with Discord's monetization features:

- **Server Boosts**: Reward users for boosting your server
- **Nitro Gifts**: Points for gifting Nitro to the server
- **Subscriptions**: Monthly tiers with casino bonuses
- **Tier Benefits**: Higher tiers get better casino odds

### 🔧 **Admin Panel**
Full web-based admin interface for managing the platform:

- **Transaction Management**: Approve/reject wallet transactions
- **Server Analytics**: Track server performance and engagement
- **User Management**: View user statistics and activity
- **System Monitoring**: Health checks and performance metrics

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check bot token
   - Verify bot permissions
   - Check intents configuration
   - Run `python3 force_sync.py` to sync commands

2. **Commands not visible**
   - Run the command sync script: `python3 force_sync.py`
   - Restart the bot: `./restart_bot.sh`
   - Check Discord permissions and bot role

3. **Database errors**
   - Verify database file permissions
   - Check PostgreSQL connection
   - Review database schema migrations

4. **Webhook not working**
   - Check webhook URL
   - Verify signature verification
   - Check firewall settings

5. **Points not updating**
   - Check webhook logs
   - Verify user exists in database
   - Check offer completion tracking

6. **Casino games not working**
   - Check daily limits configuration
   - Verify user has sufficient points
   - Check cooldown settings

7. **Wallet transactions failing**
   - Check payment processor configuration
   - Verify admin approval workflow
   - Check transaction status in admin panel

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=True
python main.py

# Check bot logs
docker-compose logs -f rewards-platform

# Force command sync
python3 force_sync.py
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

## 🛠️ **Utility Scripts**

The platform includes several utility scripts for maintenance and troubleshooting:

### 🔄 **Command Sync Script**
```bash
# Force sync Discord slash commands
python3 force_sync.py
```
Use this when commands aren't visible in Discord.

### 🔄 **Bot Restart Script**
```bash
# Restart the entire bot with clean build
./restart_bot.sh
```
Use this for a complete bot restart with fresh command registration.

### 🧪 **Test Scripts**
```bash
# Test webhook functionality
python3 test_webhook.py

# Test individual components
python3 -c "from casino_games import DiceGame; print('Casino games working!')"
```

## 🎯 **Quick Commands Reference**

### For Users:
- `/balance` - Check points
- `/earn` - Get ad links
- `/casino` - Play games
- `/wallet` - Manage money
- `/tiers` - View subscriptions

### For Admins:
- `/admin-panel` - Web admin interface
- `/admin-pending` - Review transactions
- `/admin-servers` - Server stats

## 🚀 **Getting Started Checklist**

- [ ] Set up Discord bot and get token
- [ ] Configure environment variables
- [ ] Set up database (PostgreSQL recommended)
- [ ] Configure webhook URL
- [ ] Set up payment processors (Stripe/PayPal)
- [ ] Add gift card inventory
- [ ] Test all commands and features
- [ ] Set up admin users
- [ ] Configure server boost rewards
- [ ] Deploy to production

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
- Use the utility scripts for common issues

---

**Happy Rewarding! 🎉**

*Complete Gaming Platform with Casino, Wallet, and Discord Monetization*