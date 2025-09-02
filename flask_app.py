from flask import request, jsonify, render_template_string
from flask_cors import CORS
import logging
import hashlib
import hmac
import time
from datetime import datetime
import threading
import asyncio
import requests
from sqlalchemy import text

from config import Config
from app_context import app, db, init_database
from database import User, GiftCard, AdCompletion, CasinoGame, DailyCasinoLimit, WalletTransaction, UserWallet, UserSubscription, DiscordTransaction, Server, AdminUser
from wallet_manager import WalletManager
from admin_manager import AdminManager
from notifications import send_points_notification 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize CORS
CORS(app)

# Initialize database
try:
    init_database()
    print(">>> Using database:", app.config['SQLALCHEMY_DATABASE_URI'], flush=True)
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    print(f">>> Database initialization failed: {e}", flush=True)


def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature to prevent tampering"""
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False

@app.route('/')
def index():
    """Home page with basic info"""
    try:
        # Simple HTML without complex CSS to avoid formatting issues
        webhook_url = Config.WEBHOOK_URL or 'http://localhost:5000/postback'
        threshold = Config.REDEMPTION_THRESHOLD
        points_per_ad = Config.POINTS_PER_AD
        
        html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rewards Platform Backend</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; text-align: center; }}
            .endpoint {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
            .method {{ background: #007bff; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }}
            .url {{ font-family: monospace; background: #e9ecef; padding: 5px; border-radius: 3px; }}
            .status {{ color: #28a745; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 Rewards Platform Backend</h1>
            <p class="status">✅ Backend is running successfully!</p>
            
            <h2>📡 Available Endpoints</h2>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <span class="url">/postback</span>
                <p>Webhook endpoint for ad network callbacks</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/health</span>
                <p>Health check endpoint</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/stats</span>
                <p>Platform statistics</p>
            </div>
            
            <h2>🎰 Casino Games</h2>
            <p>Users can play casino games with their points:</p>
            <ul>
                <li><strong>🎲 Dice Game:</strong> Guess 1-6, win 5x your bet if correct!</li>
                <li><strong>🎰 Slot Machine:</strong> Spin for matching symbols with various multipliers</li>
                <li><strong>🃏 Blackjack:</strong> Beat the dealer to 21 for 2x winnings</li>
            </ul>
            
            <h2>💳 Wallet System</h2>
            <p>Users can deposit cash to get points with bonuses:</p>
            <ul>
                <li><strong>💎 Deposit Packages:</strong> $5-$100 with 10% bonus points</li>
                <li><strong>💵 Exchange Rate:</strong> 100 points per $1 (110 with bonus)</li>
                <li><strong>💸 Withdrawals:</strong> Convert points back to cash via PayPal</li>
                <li><strong>⚡ Instant Processing:</strong> Deposits processed immediately</li>
            </ul>
            
            <h2>🚀 Discord Monetization</h2>
            <p>Users can support the server and get exclusive benefits:</p>
            <ul>
                <li><strong>🚀 Server Boosts:</strong> Boost server for points and casino bonuses</li>
                <li><strong>💳 Nitro Gifts:</strong> Gift Nitro for points and temporary bonuses</li>
                <li><strong>⭐ Subscriptions:</strong> Monthly tiers with casino bonus multipliers</li>
                <li><strong>🎰 Tier Benefits:</strong> Higher tiers = better casino odds (+5% to +15%)</li>
            </ul>
            
            <h2>🔧 Admin Panel</h2>
            <p>Administrative features for managing the platform:</p>
            <ul>
                <li><strong>📊 Transaction Approval:</strong> Approve/reject pending transactions</li>
                <li><strong>🏢 Multi-Server Support:</strong> Manage multiple Discord servers</li>
                <li><strong>👥 Admin Management:</strong> Add/remove admin users with different permission levels</li>
                <li><strong>📈 Analytics:</strong> View server statistics and user activity</li>
            </ul>
            
            <h2>👥 User Management</h2>
            <p>Admin endpoints for managing users:</p>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/admin/users</span>
                <p>List all users with pagination and filtering</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/admin/users/&lt;user_id&gt;</span>
                <p>Get detailed user information</p>
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <span class="url">/admin/users/&lt;user_id&gt;/ban</span>
                <p>Ban a user with reason</p>
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <span class="url">/admin/users/&lt;user_id&gt;/unban</span>
                <p>Unban a user</p>
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span>
                <span class="url">/admin/users/&lt;user_id&gt;/adjust-points</span>
                <p>Adjust user points balance</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="url">/admin/users/search</span>
                <p>Search users by username or ID</p>
            </div>
            
            <h2>🔧 Configuration</h2>
            <ul>
                <li><strong>Webhook URL:</strong> {webhook_url}</li>
                <li><strong>Redemption Threshold:</strong> {threshold} points</li>
                <li><strong>Points per Ad:</strong> {points_per_ad} points</li>
            </ul>
            
            <h2>📊 Test Webhook</h2>
            <p>Use this curl command to test the webhook:</p>
            <div class="endpoint">
                <code>curl -X POST {webhook_url} \\<br>
                &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                &nbsp;&nbsp;-d '{{"uid": "123456789", "points": 20, "offer_id": "test_offer"}}'</code>
            </div>
        </div>
    </body>
    </html>
    """
    
        return html
    except Exception as e:
        logger.error(f"Error rendering main page: {e}")
        return f"<h1>Rewards Platform Backend</h1><p>Error loading page: {str(e)}</p>", 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection with proper error handling
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            db.session.commit()
        db_status = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'version': '1.0.0'
    })

@app.route('/stats')
def platform_stats():
    """Get platform statistics"""
    try:
        total_users = User.query.count()
        total_points = db.session.query(db.func.sum(User.points_balance)).scalar() or 0
        total_earned = db.session.query(db.func.sum(User.total_earned)).scalar() or 0
        total_redemptions = GiftCard.query.filter_by(used=True).count()
        available_gift_cards = GiftCard.query.filter_by(used=False).count()
        
        # Casino statistics
        total_casino_games = CasinoGame.query.count()
        total_casino_bets = db.session.query(db.func.sum(CasinoGame.bet_amount)).scalar() or 0
        total_casino_winnings = db.session.query(db.func.sum(CasinoGame.win_amount)).scalar() or 0
        casino_house_profit = total_casino_bets - total_casino_winnings
        
        # Game type breakdown
        dice_games = CasinoGame.query.filter_by(game_type='dice').count()
        slots_games = CasinoGame.query.filter_by(game_type='slots').count()
        blackjack_games = CasinoGame.query.filter_by(game_type='blackjack').count()
        
        # Wallet statistics
        total_deposits = db.session.query(db.func.sum(WalletTransaction.amount_usd)).filter_by(
            transaction_type='deposit', status='completed'
        ).scalar() or 0
        total_withdrawals = db.session.query(db.func.sum(WalletTransaction.amount_usd)).filter_by(
            transaction_type='withdrawal', status='completed'
        ).scalar() or 0
        total_wallet_transactions = WalletTransaction.query.count()
        active_wallets = UserWallet.query.count()
        
        # Discord monetization statistics
        active_subscriptions = UserSubscription.query.filter_by(is_active=True).count()
        total_discord_transactions = DiscordTransaction.query.count()
        total_discord_points = db.session.query(db.func.sum(DiscordTransaction.points_awarded)).scalar() or 0
        
        # Subscription tier breakdown
        basic_subs = UserSubscription.query.filter_by(subscription_tier='basic', is_active=True).count()
        premium_subs = UserSubscription.query.filter_by(subscription_tier='premium', is_active=True).count()
        vip_subs = UserSubscription.query.filter_by(subscription_tier='vip', is_active=True).count()
        
        return jsonify({
            'total_users': total_users,
            'total_points_in_circulation': total_points,
            'total_points_earned': total_earned,
            'total_redemptions': total_redemptions,
            'available_gift_cards': available_gift_cards,
            'redemption_threshold': Config.REDEMPTION_THRESHOLD,
            'casino': {
                'total_games': total_casino_games,
                'total_bets': total_casino_bets,
                'total_winnings': total_casino_winnings,
                'house_profit': casino_house_profit,
                'game_breakdown': {
                    'dice': dice_games,
                    'slots': slots_games,
                    'blackjack': blackjack_games
                }
            },
            'wallet': {
                'total_deposits_usd': float(total_deposits),
                'total_withdrawals_usd': float(total_withdrawals),
                'net_deposits_usd': float(total_deposits - total_withdrawals),
                'total_transactions': total_wallet_transactions,
                'active_wallets': active_wallets,
                'exchange_rate': Config.POINTS_PER_DOLLAR,
                'bonus_percentage': Config.WALLET_BONUS_PERCENTAGE * 100
            },
            'discord_monetization': {
                'active_subscriptions': active_subscriptions,
                'total_discord_transactions': total_discord_transactions,
                'total_discord_points': total_discord_points,
                'subscription_breakdown': {
                    'basic': basic_subs,
                    'premium': premium_subs,
                    'vip': vip_subs
                },
                'available_tiers': len(Config.SUBSCRIPTION_TIERS),
                'server_boost_levels': len(Config.SERVER_BOOST_REWARDS)
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@app.route('/postback', methods=['POST'])
def webhook_postback():
    """Handle webhook callbacks from ad networks"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract required fields
        user_id = data.get('uid')
        points = data.get('points', Config.POINTS_PER_AD)
        offer_id = data.get('offer_id', 'unknown')
        
        # Validate required fields
        if not user_id:
            return jsonify({'error': 'Missing user ID (uid)'}), 400
        
        # Optional signature verification
        signature = request.headers.get('X-Signature')
        if signature and not verify_webhook_signature(request.data.decode(), signature, Config.WEBHOOK_SECRET):
            logger.warning(f"Invalid signature for webhook from {request.remote_addr}")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Check if this offer completion was already processed
        existing_completion = AdCompletion.query.filter_by(
            user_id=user_id,
            offer_id=offer_id
        ).first()
        
        if existing_completion:
            logger.info(f"Duplicate offer completion detected: {user_id} - {offer_id}")
            return jsonify({'status': 'already_processed', 'message': 'Offer already completed'})
        
        # Get or create user
        user = User.query.filter_by(id=user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        
        # Record the ad completion
        ad_completion = AdCompletion(
            user_id=user_id,
            offer_id=offer_id,
            points_earned=points,
            ip_address=request.remote_addr
        )
        db.session.add(ad_completion)
        
        # Update user's points
        old_balance = user.points_balance
        user.points_balance += points
        user.total_earned += points
        
        db.session.commit()
        
        logger.info(f"Points awarded: {user_id} earned {points} points (balance: {old_balance} -> {user.points_balance})")
        
        # Send Discord notification asynchronously
        def send_notification():
            try:
                # Create new event loop for the thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_points_notification(user_id, points, user.points_balance))
                loop.close()
            except Exception as e:
                logger.error(f"Error sending Discord notification: {e}")
        
        notification_thread = threading.Thread(target=send_notification)
        notification_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': f'Points awarded successfully',
            'user_id': user_id,
            'points_awarded': points,
            'new_balance': user.points_balance,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/postback', methods=['GET'])
def webhook_info():
    """Show webhook information and test form"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Webhook Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
            button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 Webhook Test</h1>
            <p>Test the webhook endpoint with sample data:</p>
            
            <form id="webhookForm">
                <div class="form-group">
                    <label for="uid">User ID:</label>
                    <input type="text" id="uid" name="uid" value="123456789" required>
                </div>
                
                <div class="form-group">
                    <label for="points">Points:</label>
                    <input type="number" id="points" name="points" value="20" min="1" required>
                </div>
                
                <div class="form-group">
                    <label for="offer_id">Offer ID:</label>
                    <input type="text" id="offer_id" name="offer_id" value="test_offer_123" required>
                </div>
                
                <button type="submit">Send Test Webhook</button>
            </form>
            
            <div id="result"></div>
        </div>
        
        <script>
            document.getElementById('webhookForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const data = {
                    uid: formData.get('uid'),
                    points: parseInt(formData.get('points')),
                    offer_id: formData.get('offer_id')
                };
                
                try {
                    const response = await fetch('/postback', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    const resultDiv = document.getElementById('result');
                    
                    if (response.ok) {
                        resultDiv.className = 'result success';
                        resultDiv.innerHTML = `
                            <h3>✅ Success!</h3>
                            <p><strong>Status:</strong> ${result.status}</p>
                            <p><strong>Message:</strong> ${result.message}</p>
                            <p><strong>User ID:</strong> ${result.user_id}</p>
                            <p><strong>Points Awarded:</strong> ${result.points_awarded}</p>
                            <p><strong>New Balance:</strong> ${result.new_balance}</p>
                        `;
                    } else {
                        resultDiv.className = 'result error';
                        resultDiv.innerHTML = `
                            <h3>❌ Error</h3>
                            <p><strong>Status:</strong> ${response.status}</p>
                            <p><strong>Error:</strong> ${result.error}</p>
                        `;
                    }
                } catch (error) {
                    const resultDiv = document.getElementById('result');
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `
                        <h3>❌ Network Error</h3>
                        <p>${error.message}</p>
                    `;
                }
            });
        </script>
    </body>
    </html>
    """
    
    return html

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.route('/wallet/packages')
def wallet_packages():
    """Get available wallet deposit packages"""
    try:
        packages = WalletManager.get_deposit_packages()
        return jsonify(packages)
    except Exception as e:
        logger.error(f"Error getting wallet packages: {e}")
        return jsonify({'error': 'Failed to get wallet packages'}), 500

@app.route('/wallet/deposit', methods=['POST'])
def create_deposit():
    """Create a new deposit transaction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        amount_usd = data.get('amount_usd')
        payment_method = data.get('payment_method', 'stripe')
        
        if not user_id or not amount_usd:
            return jsonify({'error': 'Missing user_id or amount_usd'}), 400
        
        result = WalletManager.create_deposit_transaction(user_id, amount_usd, payment_method)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating deposit: {e}")
        return jsonify({'error': 'Failed to create deposit'}), 500

@app.route('/wallet/complete/<int:transaction_id>', methods=['POST'])
def complete_deposit(transaction_id):
    """Complete a deposit transaction (called by payment processor webhook)"""
    try:
        result = WalletManager.complete_deposit_transaction(transaction_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error completing deposit: {e}")
        return jsonify({'error': 'Failed to complete deposit'}), 500

@app.route('/wallet/info/<user_id>')
def wallet_info(user_id):
    """Get wallet information for a user"""
    try:
        result = WalletManager.get_wallet_info(user_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error getting wallet info: {e}")
        return jsonify({'error': 'Failed to get wallet info'}), 500

@app.route('/wallet/withdraw', methods=['POST'])
def create_withdrawal():
    """Create a withdrawal request"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        amount_usd = data.get('amount_usd')
        payment_method = data.get('payment_method', 'paypal')
        
        if not user_id or not amount_usd:
            return jsonify({'error': 'Missing user_id or amount_usd'}), 400
        
        result = WalletManager.create_withdrawal_request(user_id, amount_usd, payment_method)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating withdrawal: {e}")
        return jsonify({'error': 'Failed to create withdrawal'}), 500

@app.route('/admin/pending-transactions')
def admin_pending_transactions():
    """Get pending transactions for admin approval"""
    try:
        # In a real implementation, you'd verify admin permissions here
        # For now, we'll just return the data
        result = AdminManager.get_pending_transactions()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting pending transactions: {e}")
        return jsonify({'error': 'Failed to get pending transactions'}), 500

@app.route('/admin/approve-transaction', methods=['POST'])
def admin_approve_transaction():
    """Approve a pending transaction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        transaction_id = data.get('transaction_id')
        transaction_type = data.get('transaction_type')
        admin_user_id = data.get('admin_user_id')
        notes = data.get('notes')
        
        if not all([transaction_id, transaction_type, admin_user_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = AdminManager.approve_transaction(transaction_id, transaction_type, admin_user_id, notes)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error approving transaction: {e}")
        return jsonify({'error': 'Failed to approve transaction'}), 500

@app.route('/admin/reject-transaction', methods=['POST'])
def admin_reject_transaction():
    """Reject a pending transaction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        transaction_id = data.get('transaction_id')
        transaction_type = data.get('transaction_type')
        admin_user_id = data.get('admin_user_id')
        reason = data.get('reason')
        
        if not all([transaction_id, transaction_type, admin_user_id, reason]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = AdminManager.reject_transaction(transaction_id, transaction_type, admin_user_id, reason)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error rejecting transaction: {e}")
        return jsonify({'error': 'Failed to reject transaction'}), 500

@app.route('/admin/servers')
def admin_server_stats():
    """Get server statistics for admin panel"""
    try:
        result = AdminManager.get_server_stats()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting server stats: {e}")
        return jsonify({'error': 'Failed to get server statistics'}), 500

@app.route('/admin/register-server', methods=['POST'])
def admin_register_server():
    """Register a new server"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        server_id = data.get('server_id')
        server_name = data.get('server_name')
        owner_id = data.get('owner_id')
        
        if not all([server_id, server_name, owner_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = AdminManager.register_server(server_id, server_name, owner_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error registering server: {e}")
        return jsonify({'error': 'Failed to register server'}), 500

@app.route('/admin/add-admin', methods=['POST'])
def admin_add_admin():
    """Add a new admin user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        username = data.get('username')
        admin_level = data.get('admin_level', 'moderator')
        created_by = data.get('created_by')
        
        if not all([user_id, username]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = AdminManager.add_admin(user_id, username, admin_level, created_by)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return jsonify({'error': 'Failed to add admin'}), 500

# User Management Endpoints
@app.route('/admin/users')
def admin_get_users():
    """Get paginated list of users with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status', None)
        search = request.args.get('search', None)
        
        result = AdminManager.get_users(page=page, per_page=per_page, status=status, search=search)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': 'Failed to get users'}), 500

@app.route('/admin/users/<user_id>')
def admin_get_user_details(user_id):
    """Get detailed information about a specific user"""
    try:
        result = AdminManager.get_user_details(user_id)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return jsonify({'error': 'Failed to get user details'}), 500

@app.route('/admin/users/<user_id>/ban', methods=['POST'])
def admin_ban_user(user_id):
    """Ban a user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        reason = data.get('reason')
        admin_user_id = data.get('admin_user_id')
        
        if not all([reason, admin_user_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = AdminManager.ban_user(user_id, reason, admin_user_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        return jsonify({'error': 'Failed to ban user'}), 500

@app.route('/admin/users/<user_id>/unban', methods=['POST'])
def admin_unban_user(user_id):
    """Unban a user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        admin_user_id = data.get('admin_user_id')
        
        if not admin_user_id:
            return jsonify({'error': 'Missing admin_user_id'}), 400
        
        result = AdminManager.unban_user(user_id, admin_user_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        return jsonify({'error': 'Failed to unban user'}), 500

@app.route('/admin/users/<user_id>/adjust-points', methods=['POST'])
def admin_adjust_user_points(user_id):
    """Adjust a user's points balance"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        points_change = data.get('points_change')
        admin_user_id = data.get('admin_user_id')
        reason = data.get('reason')
        
        if not all([points_change is not None, admin_user_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not isinstance(points_change, int):
            return jsonify({'error': 'points_change must be an integer'}), 400
        
        result = AdminManager.adjust_user_points(user_id, points_change, admin_user_id, reason)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error adjusting user points: {e}")
        return jsonify({'error': 'Failed to adjust user points'}), 500

@app.route('/admin/users/search')
def admin_search_users():
    """Search for users by username or ID"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        result = AdminManager.search_users(query, limit)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        return jsonify({'error': 'Failed to search users'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

def run_flask():
    """Run the Flask application"""
    try:
        logger.info(f"Starting Flask app on {Config.FLASK_HOST}:{Config.FLASK_PORT}")
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG
        )
    except Exception as e:
        logger.error(f"Error running Flask app: {e}")

if __name__ == '__main__':
    run_flask()
