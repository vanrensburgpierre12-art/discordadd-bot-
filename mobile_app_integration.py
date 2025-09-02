"""
Mobile App Integration System Module
Handles mobile app features, push notifications, and mobile-specific functionality
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, UserProfile, CasinoGame, AdCompletion, Referral, DailyBonus

logger = logging.getLogger(__name__)

class MobileAppIntegrationManager:
    """Manages mobile app integration and features"""
    
    def __init__(self):
        # Mobile app features
        self.mobile_features = {
            'push_notifications': True,
            'offline_mode': True,
            'biometric_auth': True,
            'dark_mode': True,
            'haptic_feedback': True,
            'voice_commands': False,
            'ar_features': False,
            'location_services': False
        }
        
        # Push notification types
        self.notification_types = [
            'daily_bonus_reminder',
            'achievement_unlocked',
            'level_up',
            'friend_request',
            'guild_invite',
            'tournament_starting',
            'quest_completed',
            'referral_bonus',
            'special_event',
            'maintenance_notice'
        ]
    
    def register_mobile_device(self, user_id: str, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Register a mobile device for a user"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # In a real implementation, you would store device info in database
                # For now, we'll just return success
                
                device_id = device_info.get('device_id')
                platform = device_info.get('platform', 'unknown')
                app_version = device_info.get('app_version', '1.0.0')
                push_token = device_info.get('push_token')
                
                return {
                    "success": True,
                    "message": "Mobile device registered successfully",
                    "device_id": device_id,
                    "platform": platform,
                    "app_version": app_version,
                    "registered_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error registering mobile device: {e}")
            return {"success": False, "error": f"Failed to register device: {str(e)}"}
    
    def send_push_notification(self, user_id: str, notification_type: str, title: str, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send push notification to user's mobile device"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                if notification_type not in self.notification_types:
                    return {"success": False, "error": "Invalid notification type"}
                
                # In a real implementation, you would integrate with FCM, APNs, etc.
                # For now, we'll simulate the notification
                
                notification_data = {
                    "user_id": user_id,
                    "notification_type": notification_type,
                    "title": title,
                    "message": message,
                    "data": data or {},
                    "sent_at": datetime.utcnow().isoformat(),
                    "status": "sent"
                }
                
                return {
                    "success": True,
                    "message": "Push notification sent successfully",
                    "notification": notification_data
                }
                
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return {"success": False, "error": f"Failed to send notification: {str(e)}"}
    
    def send_daily_bonus_reminder(self, user_id: str) -> Dict[str, Any]:
        """Send daily bonus reminder notification"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # Check if user can claim daily bonus
                from daily_bonus_system import DailyBonusManager
                bonus_info = DailyBonusManager.get_daily_bonus_info(user_id)
                
                if bonus_info['success'] and bonus_info['info']['can_claim']:
                    title = "Daily Bonus Available! 💰"
                    message = f"Your daily bonus of {bonus_info['info']['next_bonus_amount']} points is ready to claim!"
                    
                    return self.send_push_notification(
                        user_id=user_id,
                        notification_type='daily_bonus_reminder',
                        title=title,
                        message=message,
                        data={
                            'bonus_amount': bonus_info['info']['next_bonus_amount'],
                            'streak': bonus_info['info']['current_streak']
                        }
                    )
                else:
                    return {"success": False, "error": "Daily bonus not available"}
                
        except Exception as e:
            logger.error(f"Error sending daily bonus reminder: {e}")
            return {"success": False, "error": f"Failed to send reminder: {str(e)}"}
    
    def send_achievement_notification(self, user_id: str, achievement_name: str, achievement_description: str) -> Dict[str, Any]:
        """Send achievement unlocked notification"""
        try:
            title = "Achievement Unlocked! 🏆"
            message = f"You've unlocked: {achievement_name}"
            
            return self.send_push_notification(
                user_id=user_id,
                notification_type='achievement_unlocked',
                title=title,
                message=message,
                data={
                    'achievement_name': achievement_name,
                    'achievement_description': achievement_description
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending achievement notification: {e}")
            return {"success": False, "error": f"Failed to send notification: {str(e)}"}
    
    def send_level_up_notification(self, user_id: str, new_level: int) -> Dict[str, Any]:
        """Send level up notification"""
        try:
            title = "Level Up! ⭐"
            message = f"Congratulations! You've reached Level {new_level}!"
            
            return self.send_push_notification(
                user_id=user_id,
                notification_type='level_up',
                title=title,
                message=message,
                data={
                    'new_level': new_level
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending level up notification: {e}")
            return {"success": False, "error": f"Failed to send notification: {str(e)}"}
    
    def send_tournament_reminder(self, user_id: str, tournament_name: str, time_remaining: str) -> Dict[str, Any]:
        """Send tournament starting reminder"""
        try:
            title = "Tournament Starting Soon! 🏆"
            message = f"'{tournament_name}' starts in {time_remaining}!"
            
            return self.send_push_notification(
                user_id=user_id,
                notification_type='tournament_starting',
                title=title,
                message=message,
                data={
                    'tournament_name': tournament_name,
                    'time_remaining': time_remaining
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending tournament reminder: {e}")
            return {"success": False, "error": f"Failed to send reminder: {str(e)}"}
    
    def get_mobile_app_config(self, user_id: str) -> Dict[str, Any]:
        """Get mobile app configuration for user"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                    db.session.commit()
                
                # Get user's preferences
                user_preferences = self._get_user_mobile_preferences(user_id)
                
                return {
                    "success": True,
                    "app_config": {
                        "user_id": user_id,
                        "username": user.username,
                        "level": profile.level,
                        "xp": profile.xp,
                        "points_balance": user.points_balance,
                        "features": self.mobile_features,
                        "preferences": user_preferences,
                        "notification_settings": self._get_notification_settings(user_id),
                        "theme_settings": self._get_theme_settings(user_id),
                        "app_version": "1.0.0",
                        "last_updated": datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting mobile app config: {e}")
            return {"success": False, "error": f"Failed to get app config: {str(e)}"}
    
    def update_mobile_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's mobile app preferences"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # In a real implementation, you would store preferences in database
                # For now, we'll just return success
                
                return {
                    "success": True,
                    "message": "Mobile preferences updated successfully",
                    "preferences": preferences,
                    "updated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error updating mobile preferences: {e}")
            return {"success": False, "error": f"Failed to update preferences: {str(e)}"}
    
    def get_offline_data(self, user_id: str) -> Dict[str, Any]:
        """Get data for offline mode"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                    db.session.commit()
                
                # Get recent data for offline use
                recent_games = CasinoGame.query.filter_by(user_id=user_id).order_by(CasinoGame.played_at.desc()).limit(10).all()
                recent_ads = AdCompletion.query.filter_by(user_id=user_id).order_by(AdCompletion.completed_at.desc()).limit(10).all()
                
                offline_data = {
                    "user_info": {
                        "user_id": user_id,
                        "username": user.username,
                        "points_balance": user.points_balance,
                        "total_earned": user.total_earned,
                        "user_status": user.user_status
                    },
                    "profile_info": {
                        "level": profile.level,
                        "xp": profile.xp,
                        "total_wins": profile.total_wins,
                        "total_losses": profile.total_losses,
                        "win_streak": profile.win_streak,
                        "best_win_streak": profile.best_win_streak,
                        "favorite_game": profile.favorite_game
                    },
                    "recent_activity": {
                        "games": [
                            {
                                "game_type": game.game_type,
                                "bet_amount": game.bet_amount,
                                "win_amount": game.win_amount,
                                "result": game.result,
                                "played_at": game.played_at.isoformat()
                            }
                            for game in recent_games
                        ],
                        "ads": [
                            {
                                "ad_id": ad.ad_id,
                                "points_earned": ad.points_earned,
                                "completed_at": ad.completed_at.isoformat()
                            }
                            for ad in recent_ads
                        ]
                    },
                    "offline_timestamp": datetime.utcnow().isoformat()
                }
                
                return {
                    "success": True,
                    "offline_data": offline_data
                }
                
        except Exception as e:
            logger.error(f"Error getting offline data: {e}")
            return {"success": False, "error": f"Failed to get offline data: {str(e)}"}
    
    def sync_offline_data(self, user_id: str, offline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync data from offline mode"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # In a real implementation, you would process offline data
                # and sync it with the server
                
                return {
                    "success": True,
                    "message": "Offline data synced successfully",
                    "synced_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error syncing offline data: {e}")
            return {"success": False, "error": f"Failed to sync offline data: {str(e)}"}
    
    def get_mobile_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get mobile app usage analytics"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # In a real implementation, you would track mobile app usage
                # For now, we'll return basic analytics
                
                analytics = {
                    "app_usage": {
                        "total_sessions": 0,
                        "total_time_spent": 0,
                        "average_session_duration": 0,
                        "last_active": datetime.utcnow().isoformat()
                    },
                    "feature_usage": {
                        "casino_games": 0,
                        "daily_bonus": 0,
                        "achievements": 0,
                        "leaderboards": 0,
                        "tournaments": 0
                    },
                    "performance": {
                        "app_crashes": 0,
                        "load_times": [],
                        "error_rate": 0
                    }
                }
                
                return {
                    "success": True,
                    "analytics": analytics
                }
                
        except Exception as e:
            logger.error(f"Error getting mobile analytics: {e}")
            return {"success": False, "error": f"Failed to get analytics: {str(e)}"}
    
    def _get_user_mobile_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's mobile preferences"""
        # In a real implementation, this would query the database
        return {
            "push_notifications": True,
            "sound_notifications": True,
            "vibration": True,
            "dark_mode": False,
            "haptic_feedback": True,
            "auto_claim_daily_bonus": False,
            "low_data_mode": False
        }
    
    def _get_notification_settings(self, user_id: str) -> Dict[str, Any]:
        """Get user's notification settings"""
        # In a real implementation, this would query the database
        return {
            "daily_bonus_reminder": True,
            "achievement_notifications": True,
            "level_up_notifications": True,
            "friend_requests": True,
            "guild_invites": True,
            "tournament_reminders": True,
            "quest_completions": True,
            "referral_bonuses": True,
            "special_events": True,
            "maintenance_notices": True
        }
    
    def _get_theme_settings(self, user_id: str) -> Dict[str, Any]:
        """Get user's theme settings"""
        # In a real implementation, this would query the database
        return {
            "theme": "light",
            "accent_color": "#007bff",
            "font_size": "medium",
            "animations": True,
            "reduced_motion": False
        }
    
    def get_mobile_features_info(self) -> Dict[str, Any]:
        """Get information about mobile app features"""
        return {
            "success": True,
            "mobile_features": {
                "description": "Mobile app features and capabilities",
                "features": {
                    "push_notifications": {
                        "description": "Real-time push notifications",
                        "types": self.notification_types,
                        "enabled": self.mobile_features['push_notifications']
                    },
                    "offline_mode": {
                        "description": "Use app without internet connection",
                        "capabilities": ["View profile", "Check balance", "View recent activity"],
                        "enabled": self.mobile_features['offline_mode']
                    },
                    "biometric_auth": {
                        "description": "Fingerprint and face recognition login",
                        "enabled": self.mobile_features['biometric_auth']
                    },
                    "dark_mode": {
                        "description": "Dark theme for better night viewing",
                        "enabled": self.mobile_features['dark_mode']
                    },
                    "haptic_feedback": {
                        "description": "Vibration feedback for interactions",
                        "enabled": self.mobile_features['haptic_feedback']
                    }
                },
                "platforms": {
                    "ios": {
                        "supported": True,
                        "min_version": "12.0",
                        "features": ["push_notifications", "biometric_auth", "haptic_feedback"]
                    },
                    "android": {
                        "supported": True,
                        "min_version": "8.0",
                        "features": ["push_notifications", "biometric_auth", "haptic_feedback"]
                    }
                }
            }
        }