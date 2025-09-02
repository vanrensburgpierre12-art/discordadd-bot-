diff --git a/referral_system.py b/referral_system.py
--- a/referral_system.py
+++ b/referral_system.py
@@ -0,0 +1,314 @@
+"""
+Referral System Module
+Handles user referrals, codes, and rewards
+"""
+
+import logging
+import secrets
+import string
+from datetime import datetime
+from typing import Dict, Any, List, Optional
+from app_context import app, db
+from database import User, Referral, UserProfile
+
+logger = logging.getLogger(__name__)
+
+class ReferralManager:
+    """Manages referral system and rewards"""
+    
+    @staticmethod
+    def generate_referral_code(user_id: str) -> Dict[str, Any]:
+        """Generate a unique referral code for a user"""
+        try:
+            with app.app_context():
+                # Check if user already has a referral code
+                existing_referral = Referral.query.filter_by(referrer_id=user_id).first()
+                if existing_referral:
+                    return {
+                        "success": True,
+                        "referral_code": existing_referral.referral_code,
+                        "message": "User already has a referral code"
+                    }
+                
+                # Generate unique referral code
+                referral_code = ReferralManager._generate_unique_code()
+                
+                # Create referral record (this will be updated when someone uses it)
+                referral = Referral(
+                    referrer_id=user_id,
+                    referred_id="",  # Will be updated when someone uses the code
+                    referral_code=referral_code
+                )
+                db.session.add(referral)
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "referral_code": referral_code,
+                    "message": "Referral code generated successfully"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error generating referral code: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to generate referral code"}
+    
+    @staticmethod
+    def use_referral_code(referral_code: str, referred_user_id: str) -> Dict[str, Any]:
+        """Use a referral code to refer a new user"""
+        try:
+            with app.app_context():
+                # Check if referral code exists
+                referral = Referral.query.filter_by(referral_code=referral_code).first()
+                if not referral:
+                    return {"success": False, "error": "Invalid referral code"}
+                
+                # Check if user is trying to refer themselves
+                if referral.referrer_id == referred_user_id:
+                    return {"success": False, "error": "You cannot refer yourself"}
+                
+                # Check if user has already been referred
+                existing_referral = Referral.query.filter_by(referred_id=referred_user_id).first()
+                if existing_referral:
+                    return {"success": False, "error": "You have already been referred"}
+                
+                # Check if referrer exists and is active
+                referrer = User.query.get(referral.referrer_id)
+                if not referrer or referrer.user_status != 'active':
+                    return {"success": False, "error": "Referrer account is not valid"}
+                
+                # Check if referred user exists and is new
+                referred_user = User.query.get(referred_user_id)
+                if not referred_user:
+                    return {"success": False, "error": "Referred user not found"}
+                
+                # Check if referred user is new (created within last 24 hours)
+                if (datetime.utcnow() - referred_user.created_at).total_seconds() > 86400:  # 24 hours
+                    return {"success": False, "error": "Referral code can only be used by new users"}
+                
+                # Update referral record
+                referral.referred_id = referred_user_id
+                referral.is_active = True
+                
+                # Award referral bonus to referrer
+                referrer_bonus = 500  # Points for referrer
+                referrer.points_balance += referrer_bonus
+                referrer.total_earned += referrer_bonus
+                
+                # Award welcome bonus to referred user
+                referred_bonus = 200  # Points for referred user
+                referred_user.points_balance += referred_bonus
+                referred_user.total_earned += referred_bonus
+                
+                # Update referral points earned
+                referral.points_earned = referrer_bonus
+                
+                # Update user profiles
+                referrer_profile = UserProfile.query.filter_by(user_id=referral.referrer_id).first()
+                if not referrer_profile:
+                    referrer_profile = UserProfile(user_id=referral.referrer_id)
+                    db.session.add(referrer_profile)
+                
+                referred_profile = UserProfile.query.filter_by(user_id=referred_user_id).first()
+                if not referred_profile:
+                    referred_profile = UserProfile(user_id=referred_user_id)
+                    db.session.add(referred_profile)
+                
+                # Add XP for referral
+                referrer_profile.xp += 100
+                referred_profile.xp += 50
+                
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "message": "Referral code used successfully!",
+                    "referrer_bonus": referrer_bonus,
+                    "referred_bonus": referred_bonus,
+                    "referrer_username": referrer.username,
+                    "new_balance": referred_user.points_balance
+                }
+                
+        except Exception as e:
+            logger.error(f"Error using referral code: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to use referral code"}
+    
+    @staticmethod
+    def get_referral_stats(user_id: str) -> Dict[str, Any]:
+        """Get user's referral statistics"""
+        try:
+            with app.app_context():
+                # Get user's referral code
+                user_referral = Referral.query.filter_by(referrer_id=user_id).first()
+                referral_code = user_referral.referral_code if user_referral else None
+                
+                # Get referrals made by user
+                referrals_made = Referral.query.filter(
+                    Referral.referrer_id == user_id,
+                    Referral.referred_id != ""  # Only completed referrals
+                ).all()
+                
+                # Get referral that brought this user
+                user_was_referred = Referral.query.filter_by(referred_id=user_id).first()
+                
+                # Calculate statistics
+                total_referrals = len(referrals_made)
+                total_points_earned = sum(ref.points_earned for ref in referrals_made)
+                
+                # Get recent referrals (last 30 days)
+                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
+                recent_referrals = [
+                    ref for ref in referrals_made 
+                    if ref.created_at >= thirty_days_ago
+                ]
+                
+                # Get referred users details
+                referred_users = []
+                for referral in referrals_made:
+                    user = User.query.get(referral.referred_id)
+                    if user:
+                        referred_users.append({
+                            'user_id': referral.referred_id,
+                            'username': user.username,
+                            'referred_at': referral.created_at.isoformat(),
+                            'points_earned': referral.points_earned
+                        })
+                
+                return {
+                    "success": True,
+                    "stats": {
+                        'referral_code': referral_code,
+                        'total_referrals': total_referrals,
+                        'recent_referrals': len(recent_referrals),
+                        'total_points_earned': total_points_earned,
+                        'was_referred_by': user_was_referred.referrer_id if user_was_referred else None,
+                        'referred_users': referred_users
+                    }
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting referral stats: {e}")
+            return {"success": False, "error": "Failed to get referral stats"}
+    
+    @staticmethod
+    def get_referral_leaderboard(limit: int = 10) -> Dict[str, Any]:
+        """Get referral leaderboard"""
+        try:
+            with app.app_context():
+                # Get top referrers
+                referrals = db.session.query(
+                    Referral.referrer_id,
+                    db.func.count(Referral.id).label('referral_count'),
+                    db.func.sum(Referral.points_earned).label('total_points')
+                ).filter(
+                    Referral.referred_id != "",
+                    Referral.is_active == True
+                ).group_by(Referral.referrer_id).order_by(
+                    db.func.count(Referral.id).desc()
+                ).limit(limit).all()
+                
+                leaderboard = []
+                for i, (user_id, count, points) in enumerate(referrals, 1):
+                    user = User.query.get(user_id)
+                    if user:
+                        leaderboard.append({
+                            'rank': i,
+                            'user_id': user_id,
+                            'username': user.username,
+                            'referral_count': count,
+                            'total_points_earned': points or 0
+                        })
+                
+                return {
+                    "success": True,
+                    "leaderboard": leaderboard
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting referral leaderboard: {e}")
+            return {"success": False, "error": "Failed to get referral leaderboard"}
+    
+    @staticmethod
+    def validate_referral_code(referral_code: str) -> Dict[str, Any]:
+        """Validate a referral code"""
+        try:
+            with app.app_context():
+                referral = Referral.query.filter_by(referral_code=referral_code).first()
+                
+                if not referral:
+                    return {"success": False, "error": "Invalid referral code"}
+                
+                if not referral.is_active:
+                    return {"success": False, "error": "Referral code is not active"}
+                
+                # Check if referrer is still active
+                referrer = User.query.get(referral.referrer_id)
+                if not referrer or referrer.user_status != 'active':
+                    return {"success": False, "error": "Referrer account is not valid"}
+                
+                return {
+                    "success": True,
+                    "referrer_username": referrer.username,
+                    "message": "Referral code is valid"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error validating referral code: {e}")
+            return {"success": False, "error": "Failed to validate referral code"}
+    
+    @staticmethod
+    def _generate_unique_code(length: int = 8) -> str:
+        """Generate a unique referral code"""
+        while True:
+            # Generate random code with letters and numbers
+            characters = string.ascii_uppercase + string.digits
+            code = ''.join(secrets.choice(characters) for _ in range(length))
+            
+            # Check if code already exists
+            existing = Referral.query.filter_by(referral_code=code).first()
+            if not existing:
+                return code
+    
+    @staticmethod
+    def get_referral_rewards_info() -> Dict[str, Any]:
+        """Get information about referral rewards"""
+        return {
+            "success": True,
+            "rewards": {
+                "referrer_bonus": 500,
+                "referred_bonus": 200,
+                "referrer_xp": 100,
+                "referred_xp": 50,
+                "description": "When someone uses your referral code, you both get bonus points and XP!"
+            }
+        }
+    
+    @staticmethod
+    def cleanup_inactive_referrals() -> Dict[str, Any]:
+        """Clean up inactive referral codes"""
+        try:
+            with app.app_context():
+                # Find referral codes that haven't been used in 30 days
+                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
+                inactive_referrals = Referral.query.filter(
+                    Referral.referred_id == "",
+                    Referral.created_at < thirty_days_ago
+                ).all()
+                
+                cleaned_count = 0
+                for referral in inactive_referrals:
+                    referral.is_active = False
+                    cleaned_count += 1
+                
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "message": f"Cleaned up {cleaned_count} inactive referral codes"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error cleaning up inactive referrals: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to cleanup inactive referrals"}
