diff --git a/automated_moderation.py b/automated_moderation.py
--- a/automated_moderation.py
+++ b/automated_moderation.py
@@ -0,0 +1,350 @@
+"""
+Automated Moderation System Module
+Handles automated moderation, spam detection, and user management
+"""
+
+import logging
+import re
+from datetime import datetime, timedelta
+from typing import Dict, Any, List, Optional
+from app_context import app, db
+from database import User, CasinoGame, AdCompletion, UserProfile
+
+logger = logging.getLogger(__name__)
+
+class AutomatedModerationManager:
+    """Manages automated moderation and spam detection"""
+    
+    def __init__(self):
+        # Spam detection patterns
+        self.spam_patterns = [
+            r'(.)\1{4,}',  # Repeated characters (5+)
+            r'https?://\S+',  # URLs
+            r'@\w+',  # Mentions
+            r'#\w+',  # Hashtags
+            r'\b(?:free|win|prize|money|cash|earn|get rich)\b',  # Spam keywords
+        ]
+        
+        # Suspicious behavior thresholds
+        self.thresholds = {
+            'rapid_actions': 10,  # Actions per minute
+            'high_frequency': 100,  # Actions per hour
+            'suspicious_patterns': 5,  # Pattern matches
+            'low_balance_activity': 50,  # Actions with low balance
+        }
+    
+    def check_spam_content(self, content: str) -> Dict[str, Any]:
+        """Check content for spam patterns"""
+        try:
+            spam_score = 0
+            detected_patterns = []
+            
+            for pattern in self.spam_patterns:
+                matches = re.findall(pattern, content, re.IGNORECASE)
+                if matches:
+                    spam_score += len(matches)
+                    detected_patterns.append({
+                        'pattern': pattern,
+                        'matches': matches,
+                        'count': len(matches)
+                    })
+            
+            is_spam = spam_score >= self.thresholds['suspicious_patterns']
+            
+            return {
+                "success": True,
+                "is_spam": is_spam,
+                "spam_score": spam_score,
+                "detected_patterns": detected_patterns,
+                "threshold": self.thresholds['suspicious_patterns']
+            }
+            
+        except Exception as e:
+            logger.error(f"Error checking spam content: {e}")
+            return {"success": False, "error": "Failed to check spam content"}
+    
+    def detect_suspicious_behavior(self, user_id: str) -> Dict[str, Any]:
+        """Detect suspicious user behavior"""
+        try:
+            with app.app_context():
+                user = User.query.get(user_id)
+                if not user:
+                    return {"success": False, "error": "User not found"}
+                
+                now = datetime.utcnow()
+                last_hour = now - timedelta(hours=1)
+                last_minute = now - timedelta(minutes=1)
+                
+                # Check rapid actions (last minute)
+                recent_actions = CasinoGame.query.filter(
+                    CasinoGame.user_id == user_id,
+                    CasinoGame.played_at >= last_minute
+                ).count()
+                
+                # Check high frequency (last hour)
+                hourly_actions = CasinoGame.query.filter(
+                    CasinoGame.user_id == user_id,
+                    CasinoGame.played_at >= last_hour
+                ).count()
+                
+                # Check for suspicious patterns
+                suspicious_patterns = []
+                
+                if recent_actions >= self.thresholds['rapid_actions']:
+                    suspicious_patterns.append({
+                        'type': 'rapid_actions',
+                        'value': recent_actions,
+                        'threshold': self.thresholds['rapid_actions'],
+                        'description': 'Too many actions in short time'
+                    })
+                
+                if hourly_actions >= self.thresholds['high_frequency']:
+                    suspicious_patterns.append({
+                        'type': 'high_frequency',
+                        'value': hourly_actions,
+                        'threshold': self.thresholds['high_frequency'],
+                        'description': 'Too many actions per hour'
+                    })
+                
+                # Check for low balance but high activity
+                if user.points_balance < 100 and hourly_actions > 20:
+                    suspicious_patterns.append({
+                        'type': 'low_balance_activity',
+                        'value': hourly_actions,
+                        'threshold': self.thresholds['low_balance_activity'],
+                        'description': 'High activity with low balance'
+                    })
+                
+                # Check for unusual win patterns
+                recent_games = CasinoGame.query.filter(
+                    CasinoGame.user_id == user_id,
+                    CasinoGame.played_at >= last_hour
+                ).all()
+                
+                if recent_games:
+                    wins = sum(1 for game in recent_games if game.win_amount > 0)
+                    win_rate = wins / len(recent_games) * 100
+                    
+                    if win_rate > 80:  # Suspiciously high win rate
+                        suspicious_patterns.append({
+                            'type': 'suspicious_win_rate',
+                            'value': win_rate,
+                            'threshold': 80,
+                            'description': 'Unusually high win rate'
+                        })
+                
+                is_suspicious = len(suspicious_patterns) > 0
+                risk_level = 'low'
+                
+                if len(suspicious_patterns) >= 3:
+                    risk_level = 'high'
+                elif len(suspicious_patterns) >= 2:
+                    risk_level = 'medium'
+                
+                return {
+                    "success": True,
+                    "is_suspicious": is_suspicious,
+                    "risk_level": risk_level,
+                    "suspicious_patterns": suspicious_patterns,
+                    "recent_actions": recent_actions,
+                    "hourly_actions": hourly_actions
+                }
+                
+        except Exception as e:
+            logger.error(f"Error detecting suspicious behavior: {e}")
+            return {"success": False, "error": "Failed to detect suspicious behavior"}
+    
+    def auto_moderate_user(self, user_id: str, action: str = 'warn') -> Dict[str, Any]:
+        """Automatically moderate a user based on detected behavior"""
+        try:
+            with app.app_context():
+                user = User.query.get(user_id)
+                if not user:
+                    return {"success": False, "error": "User not found"}
+                
+                # Get behavior analysis
+                behavior = self.detect_suspicious_behavior(user_id)
+                if not behavior['success']:
+                    return behavior
+                
+                if not behavior['is_suspicious']:
+                    return {"success": True, "message": "No suspicious behavior detected"}
+                
+                risk_level = behavior['risk_level']
+                moderation_actions = []
+                
+                if action == 'warn' or risk_level == 'low':
+                    # Issue warning
+                    moderation_actions.append({
+                        'action': 'warning',
+                        'description': 'User warned for suspicious behavior',
+                        'timestamp': datetime.utcnow().isoformat()
+                    })
+                    
+                elif action == 'restrict' or risk_level == 'medium':
+                    # Restrict user (limit daily actions)
+                    user.user_status = 'suspended'
+                    moderation_actions.append({
+                        'action': 'restriction',
+                        'description': 'User restricted due to suspicious behavior',
+                        'timestamp': datetime.utcnow().isoformat()
+                    })
+                    
+                elif action == 'ban' or risk_level == 'high':
+                    # Ban user
+                    user.user_status = 'banned'
+                    user.ban_reason = 'Automated moderation: Suspicious behavior detected'
+                    user.banned_at = datetime.utcnow()
+                    user.banned_by = 'system'
+                    moderation_actions.append({
+                        'action': 'ban',
+                        'description': 'User banned for suspicious behavior',
+                        'timestamp': datetime.utcnow().isoformat()
+                    })
+                
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "moderation_actions": moderation_actions,
+                    "risk_level": risk_level,
+                    "user_status": user.user_status
+                }
+                
+        except Exception as e:
+            logger.error(f"Error auto moderating user: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to auto moderate user"}
+    
+    def get_moderation_stats(self) -> Dict[str, Any]:
+        """Get moderation statistics"""
+        try:
+            with app.app_context():
+                # Get user status counts
+                total_users = User.query.count()
+                active_users = User.query.filter(User.user_status == 'active').count()
+                banned_users = User.query.filter(User.user_status == 'banned').count()
+                suspended_users = User.query.filter(User.user_status == 'suspended').count()
+                
+                # Get recent moderation actions
+                recent_bans = User.query.filter(
+                    User.banned_at >= datetime.utcnow() - timedelta(days=7)
+                ).count()
+                
+                # Get users with suspicious patterns
+                suspicious_users = 0
+                users = User.query.filter(User.user_status == 'active').limit(1000).all()
+                
+                for user in users:
+                    behavior = self.detect_suspicious_behavior(user.id)
+                    if behavior['success'] and behavior['is_suspicious']:
+                        suspicious_users += 1
+                
+                return {
+                    "success": True,
+                    "stats": {
+                        "total_users": total_users,
+                        "active_users": active_users,
+                        "banned_users": banned_users,
+                        "suspended_users": suspended_users,
+                        "recent_bans": recent_bans,
+                        "suspicious_users": suspicious_users,
+                        "moderation_rate": (banned_users + suspended_users) / total_users * 100 if total_users > 0 else 0
+                    }
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting moderation stats: {e}")
+            return {"success": False, "error": "Failed to get moderation stats"}
+    
+    def scan_all_users(self) -> Dict[str, Any]:
+        """Scan all active users for suspicious behavior"""
+        try:
+            with app.app_context():
+                users = User.query.filter(User.user_status == 'active').limit(1000).all()
+                
+                suspicious_users = []
+                moderated_users = []
+                
+                for user in users:
+                    behavior = self.detect_suspicious_behavior(user.id)
+                    if behavior['success'] and behavior['is_suspicious']:
+                        suspicious_users.append({
+                            'user_id': user.id,
+                            'username': user.username,
+                            'risk_level': behavior['risk_level'],
+                            'suspicious_patterns': behavior['suspicious_patterns']
+                        })
+                        
+                        # Auto moderate high risk users
+                        if behavior['risk_level'] == 'high':
+                            moderation = self.auto_moderate_user(user.id, 'ban')
+                            if moderation['success']:
+                                moderated_users.append({
+                                    'user_id': user.id,
+                                    'username': user.username,
+                                    'action': 'banned'
+                                })
+                
+                return {
+                    "success": True,
+                    "scan_results": {
+                        "total_scanned": len(users),
+                        "suspicious_users": len(suspicious_users),
+                        "moderated_users": len(moderated_users),
+                        "suspicious_list": suspicious_users,
+                        "moderated_list": moderated_users
+                    }
+                }
+                
+        except Exception as e:
+            logger.error(f"Error scanning all users: {e}")
+            return {"success": False, "error": "Failed to scan all users"}
+    
+    def update_moderation_thresholds(self, new_thresholds: Dict[str, int]) -> Dict[str, Any]:
+        """Update moderation thresholds"""
+        try:
+            for key, value in new_thresholds.items():
+                if key in self.thresholds:
+                    self.thresholds[key] = value
+            
+            return {
+                "success": True,
+                "message": "Moderation thresholds updated",
+                "new_thresholds": self.thresholds
+            }
+            
+        except Exception as e:
+            logger.error(f"Error updating moderation thresholds: {e}")
+            return {"success": False, "error": "Failed to update thresholds"}
+    
+    def get_moderation_log(self, limit: int = 50) -> Dict[str, Any]:
+        """Get moderation action log"""
+        try:
+            with app.app_context():
+                # Get recently banned users
+                recent_bans = User.query.filter(
+                    User.banned_at.isnot(None),
+                    User.banned_at >= datetime.utcnow() - timedelta(days=30)
+                ).order_by(User.banned_at.desc()).limit(limit).all()
+                
+                moderation_log = []
+                for user in recent_bans:
+                    moderation_log.append({
+                        'user_id': user.id,
+                        'username': user.username,
+                        'action': 'ban',
+                        'reason': user.ban_reason,
+                        'timestamp': user.banned_at.isoformat(),
+                        'moderator': user.banned_by
+                    })
+                
+                return {
+                    "success": True,
+                    "moderation_log": moderation_log,
+                    "count": len(moderation_log)
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting moderation log: {e}")
+            return {"success": False, "error": "Failed to get moderation log"}
