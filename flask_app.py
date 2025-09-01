from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging
import hashlib
import hmac
import time
from datetime import datetime
import threading
import asyncio
import requests

from config import Config
from database import db, User, GiftCard, AdCompletion, init_db
from discord_bot import send_points_notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize CORS
CORS(app)

# Initialize database
init_db(app)

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
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rewards Platform Backend</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { background: #007bff; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
            .url { font-family: monospace; background: #e9ecef; padding: 5px; border-radius: 3px; }
            .status { color: #28a745; font-weight: bold; }
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
            
            <h2>🔧 Configuration</h2>
            <ul>
                <li><strong>Webhook URL:</strong> {webhook_url}</li>
                <li><strong>Redemption Threshold:</strong> {threshold:,} points</li>
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
    
    return render_template_string(html, 
                                webhook_url=Config.WEBHOOK_URL,
                                threshold=Config.REDEMPTION_THRESHOLD,
                                points_per_ad=Config.POINTS_PER_AD)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
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
        
        return jsonify({
            'total_users': total_users,
            'total_points_in_circulation': total_points,
            'total_points_earned': total_earned,
            'total_redemptions': total_redemptions,
            'available_gift_cards': available_gift_cards,
            'redemption_threshold': Config.REDEMPTION_THRESHOLD,
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