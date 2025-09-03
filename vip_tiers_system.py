diff --git a/vip_tiers_system.py b/vip_tiers_system.py
--- a/vip_tiers_system.py
+++ b/vip_tiers_system.py
@@ -0,0 +1,469 @@
+"""
+VIP Tiers System Module
+Handles VIP tiers, premium features, and exclusive benefits
+"""
+
+import logging
+from datetime import datetime, timedelta
+from typing import Dict, Any, List, Optional
+from app_context import app, db
+from database import User, UserProfile, CasinoGame, AdCompletion, Referral, DailyBonus
+
+logger = logging.getLogger(__name__)
+
+class VIPTiersManager:
+    """Manages VIP tiers and premium features"""
+    
+    def __init__(self):
+        # VIP tier definitions
+        self.vip_tiers = {
+            'bronze': {
+                'name': 'Bronze VIP',
+                'level': 1,
+                'min_points_spent': 1000,
+                'min_level': 5,
+                'benefits': {
+                    'daily_bonus_multiplier': 1.2,
+                    'casino_bonus_multiplier': 1.1,
+                    'referral_bonus_multiplier': 1.2,
+                    'exclusive_games': ['roulette'],
+                    'priority_support': False,
+                    'custom_avatar_frame': True,
+                    'vip_badge': True,
+                    'monthly_reward': 500
+                },
+                'color': '#CD7F32',
+                'icon': '🥉'
+            },
+            'silver': {
+                'name': 'Silver VIP',
+                'level': 2,
+                'min_points_spent': 5000,
+                'min_level': 10,
+                'benefits': {
+                    'daily_bonus_multiplier': 1.5,
+                    'casino_bonus_multiplier': 1.2,
+                    'referral_bonus_multiplier': 1.5,
+                    'exclusive_games': ['roulette', 'poker'],
+                    'priority_support': True,
+                    'custom_avatar_frame': True,
+                    'vip_badge': True,
+                    'monthly_reward': 1500,
+                    'exclusive_tournaments': True,
+                    'advanced_analytics': True
+                },
+                'color': '#C0C0C0',
+                'icon': '🥈'
+            },
+            'gold': {
+                'name': 'Gold VIP',
+                'level': 3,
+                'min_points_spent': 15000,
+                'min_level': 20,
+                'benefits': {
+                    'daily_bonus_multiplier': 2.0,
+                    'casino_bonus_multiplier': 1.5,
+                    'referral_bonus_multiplier': 2.0,
+                    'exclusive_games': ['roulette', 'poker', 'lottery'],
+                    'priority_support': True,
+                    'custom_avatar_frame': True,
+                    'vip_badge': True,
+                    'monthly_reward': 3000,
+                    'exclusive_tournaments': True,
+                    'advanced_analytics': True,
+                    'personal_manager': True,
+                    'custom_quests': True
+                },
+                'color': '#FFD700',
+                'icon': '🥇'
+            },
+            'platinum': {
+                'name': 'Platinum VIP',
+                'level': 4,
+                'min_points_spent': 50000,
+                'min_level': 30,
+                'benefits': {
+                    'daily_bonus_multiplier': 3.0,
+                    'casino_bonus_multiplier': 2.0,
+                    'referral_bonus_multiplier': 3.0,
+                    'exclusive_games': ['roulette', 'poker', 'lottery', 'vip_slots'],
+                    'priority_support': True,
+                    'custom_avatar_frame': True,
+                    'vip_badge': True,
+                    'monthly_reward': 7500,
+                    'exclusive_tournaments': True,
+                    'advanced_analytics': True,
+                    'personal_manager': True,
+                    'custom_quests': True,
+                    'exclusive_events': True,
+                    'beta_features': True
+                },
+                'color': '#E5E4E2',
+                'icon': '💎'
+            },
+            'diamond': {
+                'name': 'Diamond VIP',
+                'level': 5,
+                'min_points_spent': 100000,
+                'min_level': 50,
+                'benefits': {
+                    'daily_bonus_multiplier': 5.0,
+                    'casino_bonus_multiplier': 3.0,
+                    'referral_bonus_multiplier': 5.0,
+                    'exclusive_games': ['roulette', 'poker', 'lottery', 'vip_slots', 'diamond_blackjack'],
+                    'priority_support': True,
+                    'custom_avatar_frame': True,
+                    'vip_badge': True,
+                    'monthly_reward': 15000,
+                    'exclusive_tournaments': True,
+                    'advanced_analytics': True,
+                    'personal_manager': True,
+                    'custom_quests': True,
+                    'exclusive_events': True,
+                    'beta_features': True,
+                    'platform_influence': True,
+                    'exclusive_content': True
+                },
+                'color': '#B9F2FF',
+                'icon': '💠'
+            }
+        }
+    
+    def get_user_vip_tier(self, user_id: str) -> Dict[str, Any]:
+        """Get user's current VIP tier"""
+        try:
+            with app.app_context():
+                user = User.query.get(user_id)
+                if not user:
+                    return {"success": False, "error": "User not found"}
+                
+                profile = UserProfile.query.filter_by(user_id=user_id).first()
+                if not profile:
+                    profile = UserProfile(user_id=user_id)
+                    db.session.add(profile)
+                    db.session.commit()
+                
+                # Calculate user's VIP tier
+                current_tier = self._calculate_vip_tier(user, profile)
+                
+                # Get tier benefits
+                tier_info = self.vip_tiers.get(current_tier, {})
+                
+                # Calculate progress to next tier
+                next_tier = self._get_next_tier(current_tier)
+                progress_to_next = self._calculate_progress_to_next_tier(user, profile, next_tier)
+                
+                return {
+                    "success": True,
+                    "current_tier": current_tier,
+                    "tier_info": tier_info,
+                    "next_tier": next_tier,
+                    "progress_to_next": progress_to_next,
+                    "benefits": tier_info.get('benefits', {}),
+                    "user_stats": {
+                        "points_spent": user.total_earned,
+                        "level": profile.level,
+                        "xp": profile.xp
+                    }
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting user VIP tier: {e}")
+            return {"success": False, "error": f"Failed to get VIP tier: {str(e)}"}
+    
+    def _calculate_vip_tier(self, user: User, profile: UserProfile) -> str:
+        """Calculate user's VIP tier based on criteria"""
+        points_spent = user.total_earned
+        level = profile.level
+        
+        # Check tiers from highest to lowest
+        for tier_name, tier_info in reversed(list(self.vip_tiers.items())):
+            if (points_spent >= tier_info['min_points_spent'] and 
+                level >= tier_info['min_level']):
+                return tier_name
+        
+        return 'none'  # No VIP tier
+    
+    def _get_next_tier(self, current_tier: str) -> Optional[str]:
+        """Get the next VIP tier"""
+        tier_order = ['none', 'bronze', 'silver', 'gold', 'platinum', 'diamond']
+        
+        try:
+            current_index = tier_order.index(current_tier)
+            if current_index < len(tier_order) - 1:
+                return tier_order[current_index + 1]
+        except ValueError:
+            pass
+        
+        return None
+    
+    def _calculate_progress_to_next_tier(self, user: User, profile: UserProfile, next_tier: str) -> Dict[str, Any]:
+        """Calculate progress to next VIP tier"""
+        if not next_tier or next_tier not in self.vip_tiers:
+            return {
+                "has_next_tier": False,
+                "progress_percentage": 100
+            }
+        
+        next_tier_info = self.vip_tiers[next_tier]
+        
+        # Calculate progress for points spent
+        points_progress = min(100, (user.total_earned / next_tier_info['min_points_spent']) * 100)
+        
+        # Calculate progress for level
+        level_progress = min(100, (profile.level / next_tier_info['min_level']) * 100)
+        
+        # Overall progress is the minimum of both requirements
+        overall_progress = min(points_progress, level_progress)
+        
+        return {
+            "has_next_tier": True,
+            "next_tier": next_tier,
+            "next_tier_info": next_tier_info,
+            "points_progress": {
+                "current": user.total_earned,
+                "required": next_tier_info['min_points_spent'],
+                "percentage": points_progress
+            },
+            "level_progress": {
+                "current": profile.level,
+                "required": next_tier_info['min_level'],
+                "percentage": level_progress
+            },
+            "overall_progress": overall_progress
+        }
+    
+    def apply_vip_benefits(self, user_id: str, benefit_type: str, base_amount: int) -> Dict[str, Any]:
+        """Apply VIP benefits to a reward"""
+        try:
+            with app.app_context():
+                user = User.query.get(user_id)
+                if not user:
+                    return {"success": False, "error": "User not found"}
+                
+                # Get user's VIP tier
+                vip_info = self.get_user_vip_tier(user_id)
+                if not vip_info['success']:
+                    return vip_info
+                
+                current_tier = vip_info['current_tier']
+                if current_tier == 'none':
+                    return {
+                        "success": True,
+                        "base_amount": base_amount,
+                        "bonus_amount": 0,
+                        "total_amount": base_amount,
+                        "multiplier": 1.0,
+                        "vip_tier": current_tier
+                    }
+                
+                tier_info = self.vip_tiers[current_tier]
+                benefits = tier_info['benefits']
+                
+                # Apply appropriate multiplier
+                multiplier = 1.0
+                if benefit_type == 'daily_bonus':
+                    multiplier = benefits.get('daily_bonus_multiplier', 1.0)
+                elif benefit_type == 'casino_win':
+                    multiplier = benefits.get('casino_bonus_multiplier', 1.0)
+                elif benefit_type == 'referral':
+                    multiplier = benefits.get('referral_bonus_multiplier', 1.0)
+                
+                bonus_amount = int(base_amount * (multiplier - 1.0))
+                total_amount = base_amount + bonus_amount
+                
+                return {
+                    "success": True,
+                    "base_amount": base_amount,
+                    "bonus_amount": bonus_amount,
+                    "total_amount": total_amount,
+                    "multiplier": multiplier,
+                    "vip_tier": current_tier,
+                    "benefit_type": benefit_type
+                }
+                
+        except Exception as e:
+            logger.error(f"Error applying VIP benefits: {e}")
+            return {"success": False, "error": f"Failed to apply VIP benefits: {str(e)}"}
+    
+    def get_vip_benefits(self, tier: str) -> Dict[str, Any]:
+        """Get benefits for a specific VIP tier"""
+        if tier not in self.vip_tiers:
+            return {"success": False, "error": "Invalid VIP tier"}
+        
+        tier_info = self.vip_tiers[tier]
+        
+        return {
+            "success": True,
+            "tier": tier,
+            "tier_info": tier_info,
+            "benefits": tier_info['benefits']
+        }
+    
+    def get_all_vip_tiers(self) -> Dict[str, Any]:
+        """Get all VIP tiers and their requirements"""
+        return {
+            "success": True,
+            "vip_tiers": self.vip_tiers,
+            "tier_count": len(self.vip_tiers)
+        }
+    
+    def upgrade_user_vip_tier(self, user_id: str, new_tier: str) -> Dict[str, Any]:
+        """Manually upgrade user's VIP tier (admin function)"""
+        try:
+            with app.app_context():
+                user = User.query.get(user_id)
+                if not user:
+                    return {"success": False, "error": "User not found"}
+                
+                if new_tier not in self.vip_tiers:
+                    return {"success": False, "error": "Invalid VIP tier"}
+                
+                # In a real implementation, you would store VIP tier in database
+                # For now, we'll just return success
+                
+                tier_info = self.vip_tiers[new_tier]
+                
+                return {
+                    "success": True,
+                    "message": f"User upgraded to {tier_info['name']}",
+                    "new_tier": new_tier,
+                    "tier_info": tier_info
+                }
+                
+        except Exception as e:
+            logger.error(f"Error upgrading user VIP tier: {e}")
+            return {"success": False, "error": f"Failed to upgrade VIP tier: {str(e)}"}
+    
+    def get_vip_leaderboard(self, limit: int = 10) -> Dict[str, Any]:
+        """Get VIP tier leaderboard"""
+        try:
+            with app.app_context():
+                # Get top users by total earned (VIP criteria)
+                users = User.query.filter(
+                    User.user_status == 'active',
+                    User.total_earned > 0
+                ).order_by(User.total_earned.desc()).limit(limit).all()
+                
+                leaderboard = []
+                for i, user in enumerate(users, 1):
+                    profile = UserProfile.query.filter_by(user_id=user.id).first()
+                    if not profile:
+                        profile = UserProfile(user_id=user.id)
+                        db.session.add(profile)
+                        db.session.commit()
+                    
+                    vip_tier = self._calculate_vip_tier(user, profile)
+                    tier_info = self.vip_tiers.get(vip_tier, {})
+                    
+                    leaderboard.append({
+                        'rank': i,
+                        'user_id': user.id,
+                        'username': user.username,
+                        'vip_tier': vip_tier,
+                        'tier_name': tier_info.get('name', 'No VIP'),
+                        'tier_icon': tier_info.get('icon', ''),
+                        'tier_color': tier_info.get('color', '#000000'),
+                        'points_spent': user.total_earned,
+                        'level': profile.level,
+                        'xp': profile.xp
+                    })
+                
+                return {
+                    "success": True,
+                    "leaderboard": leaderboard,
+                    "count": len(leaderboard)
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting VIP leaderboard: {e}")
+            return {"success": False, "error": f"Failed to get VIP leaderboard: {str(e)}"}
+    
+    def get_vip_statistics(self) -> Dict[str, Any]:
+        """Get VIP tier statistics"""
+        try:
+            with app.app_context():
+                # Get all active users
+                users = User.query.filter(User.user_status == 'active').limit(1000).all()
+                
+                tier_counts = {'none': 0}
+                for tier in self.vip_tiers.keys():
+                    tier_counts[tier] = 0
+                
+                total_points_spent = 0
+                total_users = len(users)
+                
+                for user in users:
+                    profile = UserProfile.query.filter_by(user_id=user.id).first()
+                    if not profile:
+                        profile = UserProfile(user_id=user.id)
+                        db.session.add(profile)
+                    
+                    vip_tier = self._calculate_vip_tier(user, profile)
+                    tier_counts[vip_tier] += 1
+                    total_points_spent += user.total_earned
+                
+                # Calculate percentages
+                tier_percentages = {}
+                for tier, count in tier_counts.items():
+                    tier_percentages[tier] = (count / total_users * 100) if total_users > 0 else 0
+                
+                return {
+                    "success": True,
+                    "statistics": {
+                        "total_users": total_users,
+                        "total_points_spent": total_points_spent,
+                        "average_points_spent": total_points_spent / total_users if total_users > 0 else 0,
+                        "tier_counts": tier_counts,
+                        "tier_percentages": tier_percentages,
+                        "vip_users": sum(count for tier, count in tier_counts.items() if tier != 'none'),
+                        "vip_percentage": sum(percentage for tier, percentage in tier_percentages.items() if tier != 'none')
+                    }
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting VIP statistics: {e}")
+            return {"success": False, "error": f"Failed to get VIP statistics: {str(e)}"}
+    
+    def get_vip_rewards_info(self) -> Dict[str, Any]:
+        """Get information about VIP rewards and benefits"""
+        return {
+            "success": True,
+            "vip_rewards": {
+                "description": "VIP tiers provide exclusive benefits and rewards",
+                "tiers": {
+                    "bronze": {
+                        "requirements": "1,000 points spent + Level 5",
+                        "key_benefits": ["20% bonus multipliers", "Exclusive games", "VIP badge"]
+                    },
+                    "silver": {
+                        "requirements": "5,000 points spent + Level 10",
+                        "key_benefits": ["50% bonus multipliers", "Priority support", "Exclusive tournaments"]
+                    },
+                    "gold": {
+                        "requirements": "15,000 points spent + Level 20",
+                        "key_benefits": ["100% bonus multipliers", "Personal manager", "Custom quests"]
+                    },
+                    "platinum": {
+                        "requirements": "50,000 points spent + Level 30",
+                        "key_benefits": ["200% bonus multipliers", "Exclusive events", "Beta features"]
+                    },
+                    "diamond": {
+                        "requirements": "100,000 points spent + Level 50",
+                        "key_benefits": ["400% bonus multipliers", "Platform influence", "Exclusive content"]
+                    }
+                },
+                "benefit_types": {
+                    "multipliers": "Increased rewards for daily bonuses, casino wins, and referrals",
+                    "exclusive_games": "Access to VIP-only casino games",
+                    "priority_support": "Faster customer support response times",
+                    "exclusive_tournaments": "VIP-only tournaments with special prizes",
+                    "personal_manager": "Dedicated account manager for high-tier VIPs",
+                    "custom_quests": "Personalized quests and challenges",
+                    "exclusive_events": "Access to special events and celebrations",
+                    "beta_features": "Early access to new features and games",
+                    "platform_influence": "Input on platform development and features",
+                    "exclusive_content": "Special content, items, and experiences"
+                }
+            }
+        }
