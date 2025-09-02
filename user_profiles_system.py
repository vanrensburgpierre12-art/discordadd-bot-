"""
User Profiles System Module
Handles user profiles, avatars, levels, and XP system
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, UserProfile, UserRanking

logger = logging.getLogger(__name__)

class UserProfileManager:
    """Manages user profiles and XP system"""
    
    @staticmethod
    def get_or_create_profile(user_id: str) -> UserProfile:
        """Get or create user profile"""
        try:
            with app.app_context():
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                    db.session.commit()
                return profile
        except Exception as e:
            logger.error(f"Error getting/creating profile: {e}")
            return None
    
    @staticmethod
    def get_profile(user_id: str) -> Dict[str, Any]:
        """Get user profile information"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                profile = UserProfileManager.get_or_create_profile(user_id)
                if not profile:
                    return {"success": False, "error": "Failed to get profile"}
                
                # Calculate level and XP requirements
                level_info = UserProfileManager._calculate_level_info(profile.xp)
                
                # Get user ranking
                ranking = UserRanking.query.filter_by(user_id=user_id).first()
                
                return {
                    "success": True,
                    "profile": {
                        'user_id': user_id,
                        'username': user.username,
                        'avatar_url': profile.avatar_url,
                        'bio': profile.bio,
                        'level': level_info['level'],
                        'xp': profile.xp,
                        'xp_to_next_level': level_info['xp_to_next_level'],
                        'xp_progress': level_info['xp_progress'],
                        'total_wins': profile.total_wins,
                        'total_losses': profile.total_losses,
                        'win_streak': profile.win_streak,
                        'best_win_streak': profile.best_win_streak,
                        'favorite_game': profile.favorite_game,
                        'created_at': profile.created_at.isoformat(),
                        'updated_at': profile.updated_at.isoformat(),
                        'ranking': {
                            'overall_rank': ranking.overall_rank if ranking else None,
                            'points_rank': ranking.points_rank if ranking else None,
                            'wins_rank': ranking.wins_rank if ranking else None,
                            'streak_rank': ranking.streak_rank if ranking else None,
                            'xp_rank': ranking.xp_rank if ranking else None
                        } if ranking else None
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return {"success": False, "error": "Failed to get profile"}
    
    @staticmethod
    def update_profile(user_id: str, avatar_url: str = None, bio: str = None) -> Dict[str, Any]:
        """Update user profile information"""
        try:
            with app.app_context():
                profile = UserProfileManager.get_or_create_profile(user_id)
                if not profile:
                    return {"success": False, "error": "Failed to get profile"}
                
                if avatar_url is not None:
                    profile.avatar_url = avatar_url
                
                if bio is not None:
                    profile.bio = bio
                
                profile.updated_at = datetime.utcnow()
                db.session.commit()
                
                return {
                    "success": True,
                    "message": "Profile updated successfully"
                }
                
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to update profile"}
    
    @staticmethod
    def add_xp(user_id: str, xp_amount: int, source: str = "activity") -> Dict[str, Any]:
        """Add XP to user profile"""
        try:
            with app.app_context():
                profile = UserProfileManager.get_or_create_profile(user_id)
                if not profile:
                    return {"success": False, "error": "Failed to get profile"}
                
                old_level = UserProfileManager._calculate_level_info(profile.xp)['level']
                profile.xp += xp_amount
                new_level_info = UserProfileManager._calculate_level_info(profile.xp)
                new_level = new_level_info['level']
                
                level_up = new_level > old_level
                
                profile.updated_at = datetime.utcnow()
                db.session.commit()
                
                return {
                    "success": True,
                    "xp_added": xp_amount,
                    "new_xp": profile.xp,
                    "old_level": old_level,
                    "new_level": new_level,
                    "level_up": level_up,
                    "levels_gained": new_level - old_level,
                    "xp_to_next_level": new_level_info['xp_to_next_level'],
                    "xp_progress": new_level_info['xp_progress']
                }
                
        except Exception as e:
            logger.error(f"Error adding XP: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to add XP"}
    
    @staticmethod
    def update_game_stats(user_id: str, game_type: str, won: bool) -> Dict[str, Any]:
        """Update user's game statistics"""
        try:
            with app.app_context():
                profile = UserProfileManager.get_or_create_profile(user_id)
                if not profile:
                    return {"success": False, "error": "Failed to get profile"}
                
                if won:
                    profile.total_wins += 1
                    profile.win_streak += 1
                    if profile.win_streak > profile.best_win_streak:
                        profile.best_win_streak = profile.win_streak
                else:
                    profile.total_losses += 1
                    profile.win_streak = 0
                
                # Update favorite game
                profile.favorite_game = game_type
                profile.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                return {
                    "success": True,
                    "total_wins": profile.total_wins,
                    "total_losses": profile.total_losses,
                    "win_streak": profile.win_streak,
                    "best_win_streak": profile.best_win_streak,
                    "favorite_game": profile.favorite_game
                }
                
        except Exception as e:
            logger.error(f"Error updating game stats: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to update game stats"}
    
    @staticmethod
    def _calculate_level_info(xp: int) -> Dict[str, Any]:
        """Calculate level information based on XP"""
        # Level formula: Level = floor(sqrt(XP / 100)) + 1
        # This means:
        # Level 1: 0-99 XP
        # Level 2: 100-399 XP
        # Level 3: 400-899 XP
        # Level 4: 900-1599 XP
        # etc.
        
        level = int((xp / 100) ** 0.5) + 1
        
        # Calculate XP required for current level
        current_level_xp = ((level - 1) ** 2) * 100
        
        # Calculate XP required for next level
        next_level_xp = (level ** 2) * 100
        
        # Calculate XP to next level
        xp_to_next_level = next_level_xp - xp
        
        # Calculate progress percentage
        xp_progress = ((xp - current_level_xp) / (next_level_xp - current_level_xp)) * 100
        
        return {
            'level': level,
            'current_level_xp': current_level_xp,
            'next_level_xp': next_level_xp,
            'xp_to_next_level': xp_to_next_level,
            'xp_progress': min(100, max(0, xp_progress))
        }
    
    @staticmethod
    def get_level_leaderboard(limit: int = 10) -> Dict[str, Any]:
        """Get level leaderboard"""
        try:
            with app.app_context():
                profiles = UserProfile.query.order_by(UserProfile.xp.desc()).limit(limit).all()
                
                leaderboard = []
                for i, profile in enumerate(profiles, 1):
                    user = User.query.get(profile.user_id)
                    if user:
                        level_info = UserProfileManager._calculate_level_info(profile.xp)
                        
                        leaderboard.append({
                            'rank': i,
                            'user_id': profile.user_id,
                            'username': user.username,
                            'level': level_info['level'],
                            'xp': profile.xp,
                            'total_wins': profile.total_wins,
                            'best_win_streak': profile.best_win_streak,
                            'favorite_game': profile.favorite_game
                        })
                
                return {
                    "success": True,
                    "leaderboard": leaderboard
                }
                
        except Exception as e:
            logger.error(f"Error getting level leaderboard: {e}")
            return {"success": False, "error": "Failed to get level leaderboard"}
    
    @staticmethod
    def get_profile_stats(user_id: str) -> Dict[str, Any]:
        """Get comprehensive profile statistics"""
        try:
            with app.app_context():
                profile = UserProfileManager.get_or_create_profile(user_id)
                if not profile:
                    return {"success": False, "error": "Failed to get profile"}
                
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                level_info = UserProfileManager._calculate_level_info(profile.xp)
                
                # Calculate win rate
                total_games = profile.total_wins + profile.total_losses
                win_rate = (profile.total_wins / total_games * 100) if total_games > 0 else 0
                
                # Get ranking information
                ranking = UserRanking.query.filter_by(user_id=user_id).first()
                
                return {
                    "success": True,
                    "stats": {
                        'profile': {
                            'level': level_info['level'],
                            'xp': profile.xp,
                            'xp_to_next_level': level_info['xp_to_next_level'],
                            'xp_progress': level_info['xp_progress']
                        },
                        'gaming': {
                            'total_wins': profile.total_wins,
                            'total_losses': profile.total_losses,
                            'total_games': total_games,
                            'win_rate': win_rate,
                            'current_streak': profile.win_streak,
                            'best_streak': profile.best_win_streak,
                            'favorite_game': profile.favorite_game
                        },
                        'economy': {
                            'points_balance': user.points_balance,
                            'total_earned': user.total_earned,
                            'gift_cards_redeemed': user.total_gift_cards_redeemed
                        },
                        'ranking': {
                            'overall_rank': ranking.overall_rank if ranking else None,
                            'points_rank': ranking.points_rank if ranking else None,
                            'wins_rank': ranking.wins_rank if ranking else None,
                            'streak_rank': ranking.streak_rank if ranking else None,
                            'xp_rank': ranking.xp_rank if ranking else None
                        } if ranking else None,
                        'account': {
                            'created_at': user.created_at.isoformat(),
                            'last_activity': user.last_activity.isoformat(),
                            'user_status': user.user_status
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting profile stats: {e}")
            return {"success": False, "error": "Failed to get profile stats"}
    
    @staticmethod
    def get_level_rewards() -> Dict[str, Any]:
        """Get information about level rewards"""
        return {
            "success": True,
            "level_rewards": {
                "description": "Level up to unlock special rewards and bonuses!",
                "rewards": {
                    "level_5": "Unlock special avatar frames",
                    "level_10": "Get bonus daily login rewards",
                    "level_15": "Access to exclusive tournaments",
                    "level_20": "Special achievement badge",
                    "level_25": "VIP status with premium benefits",
                    "level_30": "Legendary status and special rewards"
                },
                "xp_sources": {
                    "casino_games": "10-50 XP per game (based on bet amount)",
                    "daily_bonus": "10-30 XP per day (based on streak)",
                    "achievements": "50-500 XP per achievement",
                    "challenges": "25-200 XP per challenge",
                    "referrals": "100 XP per successful referral",
                    "gift_cards": "10-100 XP per redemption (based on amount)"
                }
            }
        }