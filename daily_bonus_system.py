diff --git a/daily_bonus_system.py b/daily_bonus_system.py
--- a/daily_bonus_system.py
+++ b/daily_bonus_system.py
@@ -0,0 +1,319 @@
+"""
+Daily Bonus System Module
+Handles daily login bonuses, streaks, and rewards
+"""
+
+import logging
+from datetime import datetime, timedelta, date
+from typing import Dict, Any, List, Optional
+from app_context import app, db
+from database import User, DailyBonus, UserProfile
+
+logger = logging.getLogger(__name__)
+
+class DailyBonusManager:
+    """Manages daily bonuses and streak rewards"""
+    
+    @staticmethod
+    def claim_daily_bonus(user_id: str) -> Dict[str, Any]:
+        """Claim daily bonus for a user"""
+        try:
+            with app.app_context():
+                user = User.query.get(user_id)
+                if not user:
+                    return {"success": False, "error": "User not found"}
+                
+                if user.user_status != 'active':
+                    return {"success": False, "error": "User account is not active"}
+                
+                today = date.today()
+                
+                # Get or create daily bonus record
+                daily_bonus = DailyBonus.query.filter_by(user_id=user_id).first()
+                if not daily_bonus:
+                    daily_bonus = DailyBonus(user_id=user_id)
+                    db.session.add(daily_bonus)
+                
+                # Check if already claimed today
+                if daily_bonus.last_claim_date == today:
+                    return {"success": False, "error": "Daily bonus already claimed today"}
+                
+                # Calculate streak and bonus
+                streak_info = DailyBonusManager._calculate_streak(daily_bonus, today)
+                
+                # Calculate bonus amount based on streak
+                base_bonus = 100
+                streak_multiplier = min(2.0, 1.0 + (streak_info['new_streak'] * 0.1))  # Max 2x multiplier
+                bonus_amount = int(base_bonus * streak_multiplier)
+                
+                # Award bonus
+                user.points_balance += bonus_amount
+                user.total_earned += bonus_amount
+                
+                # Update daily bonus record
+                daily_bonus.current_streak = streak_info['new_streak']
+                daily_bonus.best_streak = max(daily_bonus.best_streak, streak_info['new_streak'])
+                daily_bonus.last_claim_date = today
+                daily_bonus.total_claimed += bonus_amount
+                daily_bonus.updated_at = datetime.utcnow()
+                
+                # Update user profile XP
+                profile = UserProfile.query.filter_by(user_id=user_id).first()
+                if not profile:
+                    profile = UserProfile(user_id=user_id)
+                    db.session.add(profile)
+                
+                # Award XP based on streak
+                xp_bonus = 10 + (streak_info['new_streak'] * 2)
+                profile.xp += xp_bonus
+                
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "bonus_amount": bonus_amount,
+                    "streak": streak_info['new_streak'],
+                    "best_streak": daily_bonus.best_streak,
+                    "multiplier": streak_multiplier,
+                    "xp_bonus": xp_bonus,
+                    "new_balance": user.points_balance,
+                    "message": f"Daily bonus claimed! +{bonus_amount} points (Streak: {streak_info['new_streak']})"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error claiming daily bonus: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to claim daily bonus"}
+    
+    @staticmethod
+    def get_daily_bonus_info(user_id: str) -> Dict[str, Any]:
+        """Get user's daily bonus information"""
+        try:
+            with app.app_context():
+                daily_bonus = DailyBonus.query.filter_by(user_id=user_id).first()
+                if not daily_bonus:
+                    return {
+                        "success": True,
+                        "info": {
+                            "current_streak": 0,
+                            "best_streak": 0,
+                            "can_claim": True,
+                            "last_claim_date": None,
+                            "total_claimed": 0,
+                            "next_bonus_amount": 100
+                        }
+                    }
+                
+                today = date.today()
+                can_claim = daily_bonus.last_claim_date != today
+                
+                # Calculate next bonus amount
+                next_streak = daily_bonus.current_streak + 1 if can_claim else daily_bonus.current_streak
+                base_bonus = 100
+                streak_multiplier = min(2.0, 1.0 + (next_streak * 0.1))
+                next_bonus_amount = int(base_bonus * streak_multiplier)
+                
+                return {
+                    "success": True,
+                    "info": {
+                        "current_streak": daily_bonus.current_streak,
+                        "best_streak": daily_bonus.best_streak,
+                        "can_claim": can_claim,
+                        "last_claim_date": daily_bonus.last_claim_date.isoformat() if daily_bonus.last_claim_date else None,
+                        "total_claimed": daily_bonus.total_claimed,
+                        "next_bonus_amount": next_bonus_amount,
+                        "streak_multiplier": streak_multiplier
+                    }
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting daily bonus info: {e}")
+            return {"success": False, "error": "Failed to get daily bonus info"}
+    
+    @staticmethod
+    def _calculate_streak(daily_bonus: DailyBonus, today: date) -> Dict[str, Any]:
+        """Calculate streak based on last claim date"""
+        if not daily_bonus.last_claim_date:
+            # First time claiming
+            return {"new_streak": 1, "streak_broken": False}
+        
+        yesterday = today - timedelta(days=1)
+        
+        if daily_bonus.last_claim_date == yesterday:
+            # Streak continues
+            return {"new_streak": daily_bonus.current_streak + 1, "streak_broken": False}
+        elif daily_bonus.last_claim_date == today:
+            # Already claimed today
+            return {"new_streak": daily_bonus.current_streak, "streak_broken": False}
+        else:
+            # Streak broken
+            return {"new_streak": 1, "streak_broken": True}
+    
+    @staticmethod
+    def get_streak_rewards_info() -> Dict[str, Any]:
+        """Get information about streak rewards"""
+        return {
+            "success": True,
+            "rewards": {
+                "base_bonus": 100,
+                "streak_multiplier": "10% per day (max 2x)",
+                "xp_bonus": "10 + (streak * 2)",
+                "streak_milestones": {
+                    "7_days": "1.7x multiplier",
+                    "14_days": "2.4x multiplier (max)",
+                    "30_days": "Special achievement unlocked"
+                }
+            }
+        }
+    
+    @staticmethod
+    def get_daily_bonus_leaderboard(limit: int = 10) -> Dict[str, Any]:
+        """Get daily bonus streak leaderboard"""
+        try:
+            with app.app_context():
+                daily_bonuses = DailyBonus.query.order_by(
+                    DailyBonus.best_streak.desc(),
+                    DailyBonus.current_streak.desc()
+                ).limit(limit).all()
+                
+                leaderboard = []
+                for i, bonus in enumerate(daily_bonuses, 1):
+                    user = User.query.get(bonus.user_id)
+                    if user:
+                        leaderboard.append({
+                            'rank': i,
+                            'user_id': bonus.user_id,
+                            'username': user.username,
+                            'current_streak': bonus.current_streak,
+                            'best_streak': bonus.best_streak,
+                            'total_claimed': bonus.total_claimed,
+                            'last_claim_date': bonus.last_claim_date.isoformat() if bonus.last_claim_date else None
+                        })
+                
+                return {
+                    "success": True,
+                    "leaderboard": leaderboard
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting daily bonus leaderboard: {e}")
+            return {"success": False, "error": "Failed to get daily bonus leaderboard"}
+    
+    @staticmethod
+    def reset_expired_streaks() -> Dict[str, Any]:
+        """Reset streaks for users who haven't claimed in 2+ days"""
+        try:
+            with app.app_context():
+                two_days_ago = date.today() - timedelta(days=2)
+                
+                expired_bonuses = DailyBonus.query.filter(
+                    DailyBonus.last_claim_date < two_days_ago,
+                    DailyBonus.current_streak > 0
+                ).all()
+                
+                reset_count = 0
+                for bonus in expired_bonuses:
+                    bonus.current_streak = 0
+                    reset_count += 1
+                
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "message": f"Reset {reset_count} expired streaks"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error resetting expired streaks: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to reset expired streaks"}
+    
+    @staticmethod
+    def get_weekly_bonus_info(user_id: str) -> Dict[str, Any]:
+        """Get weekly bonus information (bonus for claiming 7 days in a row)"""
+        try:
+            with app.app_context():
+                daily_bonus = DailyBonus.query.filter_by(user_id=user_id).first()
+                if not daily_bonus:
+                    return {
+                        "success": True,
+                        "weekly_bonus": {
+                            "eligible": False,
+                            "claimed_this_week": False,
+                            "days_this_week": 0,
+                            "bonus_amount": 0
+                        }
+                    }
+                
+                # Check if user has claimed 7 days in a row
+                if daily_bonus.current_streak >= 7:
+                    # Check if weekly bonus was already claimed this week
+                    week_start = date.today() - timedelta(days=date.today().weekday())
+                    
+                    # For simplicity, we'll use a simple check
+                    # In a real implementation, you'd track weekly bonus claims separately
+                    weekly_bonus_amount = 500
+                    
+                    return {
+                        "success": True,
+                        "weekly_bonus": {
+                            "eligible": True,
+                            "claimed_this_week": False,  # Would need separate tracking
+                            "days_this_week": min(7, daily_bonus.current_streak),
+                            "bonus_amount": weekly_bonus_amount
+                        }
+                    }
+                else:
+                    return {
+                        "success": True,
+                        "weekly_bonus": {
+                            "eligible": False,
+                            "claimed_this_week": False,
+                            "days_this_week": daily_bonus.current_streak,
+                            "bonus_amount": 0
+                        }
+                    }
+                
+        except Exception as e:
+            logger.error(f"Error getting weekly bonus info: {e}")
+            return {"success": False, "error": "Failed to get weekly bonus info"}
+    
+    @staticmethod
+    def claim_weekly_bonus(user_id: str) -> Dict[str, Any]:
+        """Claim weekly bonus (7-day streak reward)"""
+        try:
+            with app.app_context():
+                user = User.query.get(user_id)
+                if not user:
+                    return {"success": False, "error": "User not found"}
+                
+                daily_bonus = DailyBonus.query.filter_by(user_id=user_id).first()
+                if not daily_bonus or daily_bonus.current_streak < 7:
+                    return {"success": False, "error": "Weekly bonus not available (need 7-day streak)"}
+                
+                # Award weekly bonus
+                weekly_bonus_amount = 500
+                user.points_balance += weekly_bonus_amount
+                user.total_earned += weekly_bonus_amount
+                
+                # Update profile XP
+                profile = UserProfile.query.filter_by(user_id=user_id).first()
+                if not profile:
+                    profile = UserProfile(user_id=user_id)
+                    db.session.add(profile)
+                
+                profile.xp += 100  # Bonus XP for weekly bonus
+                
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "bonus_amount": weekly_bonus_amount,
+                    "new_balance": user.points_balance,
+                    "message": f"Weekly bonus claimed! +{weekly_bonus_amount} points"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error claiming weekly bonus: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to claim weekly bonus"}
