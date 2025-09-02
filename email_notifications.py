"""
Email Notification System Module
Handles email notifications, templates, and delivery
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, UserProfile

logger = logging.getLogger(__name__)

class EmailNotificationManager:
    """Manages email notifications and delivery"""
    
    def __init__(self):
        # Email configuration (should be in config)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "noreply@yourplatform.com"
        self.sender_password = "your_password"  # Should be in environment variables
        
        # Email templates
        self.templates = {
            'welcome': {
                'subject': 'Welcome to Our Rewards Platform!',
                'template': '''
                <html>
                <body>
                    <h2>Welcome to Our Rewards Platform!</h2>
                    <p>Hello {username},</p>
                    <p>Welcome to our amazing rewards platform! You've been awarded <strong>{bonus_points} bonus points</strong> to get you started.</p>
                    <p>Here's what you can do:</p>
                    <ul>
                        <li>🎮 Play casino games and win points</li>
                        <li>📺 Watch ads to earn more points</li>
                        <li>🎁 Redeem points for gift cards</li>
                        <li>👥 Refer friends for bonus rewards</li>
                    </ul>
                    <p>Start earning today!</p>
                    <p>Best regards,<br>The Rewards Team</p>
                </body>
                </html>
                '''
            },
            'achievement': {
                'subject': 'Achievement Unlocked! 🏆',
                'template': '''
                <html>
                <body>
                    <h2>Achievement Unlocked! 🏆</h2>
                    <p>Congratulations {username}!</p>
                    <p>You've unlocked the achievement: <strong>{achievement_name}</strong></p>
                    <p>{achievement_description}</p>
                    <p>You've earned <strong>{points_reward} points</strong> and <strong>{xp_reward} XP</strong>!</p>
                    <p>Keep up the great work!</p>
                    <p>Best regards,<br>The Rewards Team</p>
                </body>
                </html>
                '''
            },
            'level_up': {
                'subject': 'Level Up! ⭐',
                'template': '''
                <html>
                <body>
                    <h2>Level Up! ⭐</h2>
                    <p>Congratulations {username}!</p>
                    <p>You've reached <strong>Level {new_level}</strong>!</p>
                    <p>You now have access to:</p>
                    <ul>
                        <li>🎁 Special rewards and bonuses</li>
                        <li>🏆 Exclusive tournaments</li>
                        <li>💎 Premium features</li>
                    </ul>
                    <p>Keep playing to reach even higher levels!</p>
                    <p>Best regards,<br>The Rewards Team</p>
                </body>
                </html>
                '''
            },
            'daily_bonus': {
                'subject': 'Daily Bonus Available! 💰',
                'template': '''
                <html>
                <body>
                    <h2>Daily Bonus Available! 💰</h2>
                    <p>Hello {username},</p>
                    <p>Your daily bonus is ready! You can claim <strong>{bonus_amount} points</strong> today.</p>
                    <p>Current streak: <strong>{streak} days</strong></p>
                    <p>Don't break your streak - claim your bonus now!</p>
                    <p>Best regards,<br>The Rewards Team</p>
                </body>
                </html>
                '''
            },
            'referral_bonus': {
                'subject': 'Referral Bonus Earned! 👥',
                'template': '''
                <html>
                <body>
                    <h2>Referral Bonus Earned! 👥</h2>
                    <p>Hello {username},</p>
                    <p>Great news! Someone used your referral code and you've earned <strong>{bonus_points} points</strong>!</p>
                    <p>Keep sharing your referral code to earn more bonuses!</p>
                    <p>Your referral code: <strong>{referral_code}</strong></p>
                    <p>Best regards,<br>The Rewards Team</p>
                </body>
                </html>
                '''
            },
            'tournament_reminder': {
                'subject': 'Tournament Starting Soon! 🏆',
                'template': '''
                <html>
                <body>
                    <h2>Tournament Starting Soon! 🏆</h2>
                    <p>Hello {username},</p>
                    <p>The tournament "<strong>{tournament_name}</strong>" is starting in {time_remaining}!</p>
                    <p>Entry fee: <strong>{entry_fee} points</strong></p>
                    <p>Prize pool: <strong>{prize_pool} points</strong></p>
                    <p>Don't miss out on this exciting competition!</p>
                    <p>Best regards,<br>The Rewards Team</p>
                </body>
                </html>
                '''
            },
            'account_suspended': {
                'subject': 'Account Status Update',
                'template': '''
                <html>
                <body>
                    <h2>Account Status Update</h2>
                    <p>Hello {username},</p>
                    <p>Your account has been suspended due to: <strong>{reason}</strong></p>
                    <p>If you believe this is an error, please contact support.</p>
                    <p>Best regards,<br>The Rewards Team</p>
                </body>
                </html>
                '''
            }
        }
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> Dict[str, Any]:
        """Send email to user"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return {
                "success": True,
                "message": f"Email sent to {to_email}",
                "subject": subject
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"success": False, "error": f"Failed to send email: {str(e)}"}
    
    def send_template_email(self, to_email: str, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using template"""
        try:
            if template_name not in self.templates:
                return {"success": False, "error": "Template not found"}
            
            template = self.templates[template_name]
            subject = template['subject']
            html_content = template['template']
            
            # Replace variables in template
            for key, value in variables.items():
                html_content = html_content.replace(f'{{{key}}}', str(value))
                subject = subject.replace(f'{{{key}}}', str(value))
            
            return self.send_email(to_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Error sending template email: {e}")
            return {"success": False, "error": f"Failed to send template email: {str(e)}"}
    
    def send_welcome_email(self, user_id: str, bonus_points: int = 100) -> Dict[str, Any]:
        """Send welcome email to new user"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # For demo purposes, we'll use a placeholder email
                # In real implementation, you'd store user emails
                user_email = f"{user.username}@example.com"
                
                variables = {
                    'username': user.username,
                    'bonus_points': bonus_points
                }
                
                return self.send_template_email(user_email, 'welcome', variables)
                
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return {"success": False, "error": f"Failed to send welcome email: {str(e)}"}
    
    def send_achievement_email(self, user_id: str, achievement_name: str, achievement_description: str, points_reward: int, xp_reward: int) -> Dict[str, Any]:
        """Send achievement notification email"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                user_email = f"{user.username}@example.com"
                
                variables = {
                    'username': user.username,
                    'achievement_name': achievement_name,
                    'achievement_description': achievement_description,
                    'points_reward': points_reward,
                    'xp_reward': xp_reward
                }
                
                return self.send_template_email(user_email, 'achievement', variables)
                
        except Exception as e:
            logger.error(f"Error sending achievement email: {e}")
            return {"success": False, "error": f"Failed to send achievement email: {str(e)}"}
    
    def send_level_up_email(self, user_id: str, new_level: int) -> Dict[str, Any]:
        """Send level up notification email"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                user_email = f"{user.username}@example.com"
                
                variables = {
                    'username': user.username,
                    'new_level': new_level
                }
                
                return self.send_template_email(user_email, 'level_up', variables)
                
        except Exception as e:
            logger.error(f"Error sending level up email: {e}")
            return {"success": False, "error": f"Failed to send level up email: {str(e)}"}
    
    def send_daily_bonus_reminder(self, user_id: str, bonus_amount: int, streak: int) -> Dict[str, Any]:
        """Send daily bonus reminder email"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                user_email = f"{user.username}@example.com"
                
                variables = {
                    'username': user.username,
                    'bonus_amount': bonus_amount,
                    'streak': streak
                }
                
                return self.send_template_email(user_email, 'daily_bonus', variables)
                
        except Exception as e:
            logger.error(f"Error sending daily bonus reminder: {e}")
            return {"success": False, "error": f"Failed to send daily bonus reminder: {str(e)}"}
    
    def send_referral_bonus_email(self, user_id: str, bonus_points: int, referral_code: str) -> Dict[str, Any]:
        """Send referral bonus notification email"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                user_email = f"{user.username}@example.com"
                
                variables = {
                    'username': user.username,
                    'bonus_points': bonus_points,
                    'referral_code': referral_code
                }
                
                return self.send_template_email(user_email, 'referral_bonus', variables)
                
        except Exception as e:
            logger.error(f"Error sending referral bonus email: {e}")
            return {"success": False, "error": f"Failed to send referral bonus email: {str(e)}"}
    
    def send_tournament_reminder(self, user_id: str, tournament_name: str, time_remaining: str, entry_fee: int, prize_pool: int) -> Dict[str, Any]:
        """Send tournament reminder email"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                user_email = f"{user.username}@example.com"
                
                variables = {
                    'username': user.username,
                    'tournament_name': tournament_name,
                    'time_remaining': time_remaining,
                    'entry_fee': entry_fee,
                    'prize_pool': prize_pool
                }
                
                return self.send_template_email(user_email, 'tournament_reminder', variables)
                
        except Exception as e:
            logger.error(f"Error sending tournament reminder: {e}")
            return {"success": False, "error": f"Failed to send tournament reminder: {str(e)}"}
    
    def send_account_suspension_email(self, user_id: str, reason: str) -> Dict[str, Any]:
        """Send account suspension notification email"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                user_email = f"{user.username}@example.com"
                
                variables = {
                    'username': user.username,
                    'reason': reason
                }
                
                return self.send_template_email(user_email, 'account_suspended', variables)
                
        except Exception as e:
            logger.error(f"Error sending account suspension email: {e}")
            return {"success": False, "error": f"Failed to send account suspension email: {str(e)}"}
    
    def bulk_send_emails(self, user_ids: List[str], template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk send emails to multiple users"""
        try:
            with app.app_context():
                sent_count = 0
                failed_count = 0
                failed_users = []
                
                for user_id in user_ids:
                    user = User.query.get(user_id)
                    if not user:
                        failed_count += 1
                        failed_users.append({
                            'user_id': user_id,
                            'error': 'User not found'
                        })
                        continue
                    
                    # Add username to variables
                    user_variables = variables.copy()
                    user_variables['username'] = user.username
                    
                    user_email = f"{user.username}@example.com"
                    
                    result = self.send_template_email(user_email, template_name, user_variables)
                    if result['success']:
                        sent_count += 1
                    else:
                        failed_count += 1
                        failed_users.append({
                            'user_id': user_id,
                            'error': result['error']
                        })
                
                return {
                    "success": True,
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "failed_users": failed_users,
                    "message": f"Sent {sent_count} emails, {failed_count} failed"
                }
                
        except Exception as e:
            logger.error(f"Error in bulk send emails: {e}")
            return {"success": False, "error": f"Failed to bulk send emails: {str(e)}"}
    
    def get_email_templates(self) -> Dict[str, Any]:
        """Get available email templates"""
        return {
            "success": True,
            "templates": {
                name: {
                    "subject": template["subject"],
                    "variables": self._extract_template_variables(template["template"])
                }
                for name, template in self.templates.items()
            }
        }
    
    def _extract_template_variables(self, template: str) -> List[str]:
        """Extract variables from template"""
        import re
        variables = re.findall(r'\{(\w+)\}', template)
        return list(set(variables))
    
    def update_email_config(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str) -> Dict[str, Any]:
        """Update email configuration"""
        try:
            self.smtp_server = smtp_server
            self.smtp_port = smtp_port
            self.sender_email = sender_email
            self.sender_password = sender_password
            
            return {
                "success": True,
                "message": "Email configuration updated"
            }
            
        except Exception as e:
            logger.error(f"Error updating email config: {e}")
            return {"success": False, "error": f"Failed to update email config: {str(e)}"}