"""
Achievement System Module
Handles achievements, badges, and user progress tracking
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, Achievement, UserAchievement, UserProfile, CasinoGame, AdCompletion, Referral

logger = logging.getLogger(__name__)

class AchievementManager:
    """Manages achievements and user progress"""
    
    @staticmethod
    def create_achievement(name: str, description: str, icon: str, category: str,
                          requirement_type: str, requirement_value: int, 
                          points_reward: int = 0, is_hidden: bool = False) -> Dict[str, Any]:
        """Create a new achievement"""
        try:
            with app.app_context():
                achievement = Achievement(
                    name=name,
                    description=description,
                    icon=icon,
                    category=category,
                    requirement_type=requirement_type,
                    requirement_value=requirement_value,
                    points_reward=points_reward,
                    is_hidden=is_hidden
                )
                
                db.session.add(achievement)
                db.session.commit()
                
                return {
                    "success": True,
                    "achievement_id": achievement.id,
                    "message": f"Achievement '{name}' created successfully"
                }
                
        except Exception as e:
            logger.error(f"Error creating achievement: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to create achievement"}
    
    @staticmethod
    def get_achievements(category: str = None, user_id: str = None) -> Dict[str, Any]:
        """Get achievements, optionally filtered by category and user progress"""
        try:
            with app.app_context():
                query = Achievement.query.filter(Achievement.is_active == True)
                
                if category:
                    query = query.filter(Achievement.category == category)
                
                achievements = query.all()
                
                achievement_list = []
                for achievement in achievements:
                    # Skip hidden achievements if user hasn't earned them
                    if achievement.is_hidden and user_id:
                        user_achievement = UserAchievement.query.filter_by(
                            user_id=user_id,
                            achievement_id=achievement.id
                        ).first()
                        if not user_achievement:
                            continue
                    
                    # Get user progress if user_id provided
                    user_progress = None
                    if user_id:
                        user_achievement = UserAchievement.query.filter_by(
                            user_id=user_id,
                            achievement_id=achievement.id
                        ).first()
                        
                        if user_achievement:
                            user_progress = {
                                'earned': True,
                                'earned_at': user_achievement.earned_at.isoformat(),
                                'points_awarded': user_achievement.points_awarded
                            }
                        else:
                            current_progress = AchievementManager._calculate_progress(
                                user_id, achievement.requirement_type
                            )
                            user_progress = {
                                'earned': False,
                                'progress': current_progress,
                                'requirement': achievement.requirement_value,
                                'progress_percentage': min(100, (current_progress / achievement.requirement_value) * 100)
                            }
                    
                    achievement_list.append({
                        'id': achievement.id,
                        'name': achievement.name,
                        'description': achievement.description,
                        'icon': achievement.icon,
                        'category': achievement.category,
                        'requirement_type': achievement.requirement_type,
                        'requirement_value': achievement.requirement_value,
                        'points_reward': achievement.points_reward,
                        'is_hidden': achievement.is_hidden,
                        'user_progress': user_progress
                    })
                
                return {
                    "success": True,
                    "achievements": achievement_list
                }
                
        except Exception as e:
            logger.error(f"Error getting achievements: {e}")
            return {"success": False, "error": "Failed to get achievements"}
    
    @staticmethod
    def get_user_achievements(user_id: str) -> Dict[str, Any]:
        """Get user's earned achievements"""
        try:
            with app.app_context():
                user_achievements = UserAchievement.query.filter_by(user_id=user_id).all()
                
                achievement_list = []
                for user_achievement in user_achievements:
                    achievement = Achievement.query.get(user_achievement.achievement_id)
                    if achievement:
                        achievement_list.append({
                            'id': achievement.id,
                            'name': achievement.name,
                            'description': achievement.description,
                            'icon': achievement.icon,
                            'category': achievement.category,
                            'earned_at': user_achievement.earned_at.isoformat(),
                            'points_awarded': user_achievement.points_awarded
                        })
                
                # Sort by earned date (newest first)
                achievement_list.sort(key=lambda x: x['earned_at'], reverse=True)
                
                return {
                    "success": True,
                    "achievements": achievement_list
                }
                
        except Exception as e:
            logger.error(f"Error getting user achievements: {e}")
            return {"success": False, "error": "Failed to get user achievements"}
    
    @staticmethod
    def check_and_award_achievements(user_id: str) -> Dict[str, Any]:
        """Check if user has earned any new achievements and award them"""
        try:
            with app.app_context():
                # Get all active achievements
                achievements = Achievement.query.filter(Achievement.is_active == True).all()
                
                newly_earned = []
                total_points_awarded = 0
                
                for achievement in achievements:
                    # Check if user already has this achievement
                    existing = UserAchievement.query.filter_by(
                        user_id=user_id,
                        achievement_id=achievement.id
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Check if user meets the requirement
                    current_progress = AchievementManager._calculate_progress(
                        user_id, achievement.requirement_type
                    )
                    
                    if current_progress >= achievement.requirement_value:
                        # Award achievement
                        user_achievement = UserAchievement(
                            user_id=user_id,
                            achievement_id=achievement.id,
                            points_awarded=achievement.points_reward
                        )
                        db.session.add(user_achievement)
                        
                        # Award points to user
                        if achievement.points_reward > 0:
                            user = User.query.filter_by(id=user_id).first()
                            if user:
                                user.points_balance += achievement.points_reward
                                user.total_earned += achievement.points_reward
                                total_points_awarded += achievement.points_reward
                        
                        newly_earned.append({
                            'id': achievement.id,
                            'name': achievement.name,
                            'description': achievement.description,
                            'icon': achievement.icon,
                            'category': achievement.category,
                            'points_reward': achievement.points_reward
                        })
                
                db.session.commit()
                
                return {
                    "success": True,
                    "newly_earned": newly_earned,
                    "total_points_awarded": total_points_awarded,
                    "count": len(newly_earned)
                }
                
        except Exception as e:
            logger.error(f"Error checking achievements: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to check achievements"}
    
    @staticmethod
    def _calculate_progress(user_id: str, requirement_type: str) -> int:
        """Calculate user's progress for a specific requirement type"""
        try:
            if requirement_type == 'points_earned':
                # Total points earned from ads
                ads = AdCompletion.query.filter_by(user_id=user_id).all()
                return sum(ad.points_earned for ad in ads)
            
            elif requirement_type == 'games_played':
                # Total games played
                games = CasinoGame.query.filter_by(user_id=user_id).all()
                return len(games)
            
            elif requirement_type == 'games_won':
                # Total games won
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.win_amount > 0
                ).all()
                return len(games)
            
            elif requirement_type == 'casino_points_earned':
                # Total points earned from casino
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.win_amount > 0
                ).all()
                return sum(game.win_amount for game in games)
            
            elif requirement_type == 'win_streak':
                # Best win streak
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                return profile.best_win_streak if profile else 0
            
            elif requirement_type == 'total_wins':
                # Total wins
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                return profile.total_wins if profile else 0
            
            elif requirement_type == 'level_reached':
                # User level
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                return profile.level if profile else 1
            
            elif requirement_type == 'referrals_made':
                # Total referrals
                referrals = Referral.query.filter_by(referrer_id=user_id).all()
                return len(referrals)
            
            elif requirement_type == 'gift_cards_redeemed':
                # Total gift cards redeemed
                user = User.query.filter_by(id=user_id).first()
                return user.total_gift_cards_redeemed if user else 0
            
            elif requirement_type == 'daily_bonus_streak':
                # Daily bonus streak
                from database import DailyBonus
                daily_bonus = DailyBonus.query.filter_by(user_id=user_id).first()
                return daily_bonus.best_streak if daily_bonus else 0
            
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error calculating progress: {e}")
            return 0
    
    @staticmethod
    def initialize_default_achievements() -> Dict[str, Any]:
        """Initialize default achievements"""
        try:
            with app.app_context():
                # Check if achievements already exist
                if Achievement.query.count() > 0:
                    return {"success": True, "message": "Achievements already initialized"}
                
                default_achievements = [
                    # Casino Achievements
                    {
                        'name': 'First Roll',
                        'description': 'Play your first casino game',
                        'icon': '🎲',
                        'category': 'casino',
                        'requirement_type': 'games_played',
                        'requirement_value': 1,
                        'points_reward': 50
                    },
                    {
                        'name': 'Lucky Start',
                        'description': 'Win your first casino game',
                        'icon': '🍀',
                        'category': 'casino',
                        'requirement_type': 'games_won',
                        'requirement_value': 1,
                        'points_reward': 100
                    },
                    {
                        'name': 'Casino Regular',
                        'description': 'Play 100 casino games',
                        'icon': '🎰',
                        'category': 'casino',
                        'requirement_type': 'games_played',
                        'requirement_value': 100,
                        'points_reward': 500
                    },
                    {
                        'name': 'High Roller',
                        'description': 'Earn 10,000 points from casino games',
                        'icon': '💰',
                        'category': 'casino',
                        'requirement_type': 'casino_points_earned',
                        'requirement_value': 10000,
                        'points_reward': 2000
                    },
                    {
                        'name': 'Streak Master',
                        'description': 'Achieve a 10-game win streak',
                        'icon': '🔥',
                        'category': 'casino',
                        'requirement_type': 'win_streak',
                        'requirement_value': 10,
                        'points_reward': 1000
                    },
                    
                    # Economy Achievements
                    {
                        'name': 'First Earnings',
                        'description': 'Earn your first 100 points',
                        'icon': '💎',
                        'category': 'economy',
                        'requirement_type': 'points_earned',
                        'requirement_value': 100,
                        'points_reward': 25
                    },
                    {
                        'name': 'Point Collector',
                        'description': 'Earn 10,000 points total',
                        'icon': '💵',
                        'category': 'economy',
                        'requirement_type': 'points_earned',
                        'requirement_value': 10000,
                        'points_reward': 1000
                    },
                    {
                        'name': 'Gift Card Hunter',
                        'description': 'Redeem 10 gift cards',
                        'icon': '🎁',
                        'category': 'economy',
                        'requirement_type': 'gift_cards_redeemed',
                        'requirement_value': 10,
                        'points_reward': 500
                    },
                    
                    # Social Achievements
                    {
                        'name': 'Friend Maker',
                        'description': 'Refer 5 friends',
                        'icon': '👥',
                        'category': 'social',
                        'requirement_type': 'referrals_made',
                        'requirement_value': 5,
                        'points_reward': 1000
                    },
                    {
                        'name': 'Social Butterfly',
                        'description': 'Refer 25 friends',
                        'icon': '🦋',
                        'category': 'social',
                        'requirement_type': 'referrals_made',
                        'requirement_value': 25,
                        'points_reward': 5000
                    },
                    
                    # Special Achievements
                    {
                        'name': 'Rising Star',
                        'description': 'Reach level 10',
                        'icon': '⭐',
                        'category': 'special',
                        'requirement_type': 'level_reached',
                        'requirement_value': 10,
                        'points_reward': 1000
                    },
                    {
                        'name': 'Dedicated Player',
                        'description': 'Maintain a 30-day login streak',
                        'icon': '📅',
                        'category': 'special',
                        'requirement_type': 'daily_bonus_streak',
                        'requirement_value': 30,
                        'points_reward': 2000
                    },
                    {
                        'name': 'Legend',
                        'description': 'Win 1000 casino games',
                        'icon': '👑',
                        'category': 'special',
                        'requirement_type': 'games_won',
                        'requirement_value': 1000,
                        'points_reward': 10000,
                        'is_hidden': True
                    }
                ]
                
                created_count = 0
                for achievement_data in default_achievements:
                    result = AchievementManager.create_achievement(
                        name=achievement_data['name'],
                        description=achievement_data['description'],
                        icon=achievement_data['icon'],
                        category=achievement_data['category'],
                        requirement_type=achievement_data['requirement_type'],
                        requirement_value=achievement_data['requirement_value'],
                        points_reward=achievement_data['points_reward'],
                        is_hidden=achievement_data.get('is_hidden', False)
                    )
                    if result['success']:
                        created_count += 1
                
                return {
                    "success": True,
                    "message": f"Created {created_count} default achievements"
                }
                
        except Exception as e:
            logger.error(f"Error initializing achievements: {e}")
            return {"success": False, "error": "Failed to initialize achievements"}
    
    @staticmethod
    def get_achievement_stats(user_id: str) -> Dict[str, Any]:
        """Get user's achievement statistics"""
        try:
            with app.app_context():
                # Get total achievements
                total_achievements = Achievement.query.filter(Achievement.is_active == True).count()
                
                # Get user's earned achievements
                earned_achievements = UserAchievement.query.filter_by(user_id=user_id).count()
                
                # Get achievements by category
                categories = {}
                user_achievements = UserAchievement.query.filter_by(user_id=user_id).all()
                
                for user_achievement in user_achievements:
                    achievement = Achievement.query.get(user_achievement.achievement_id)
                    if achievement:
                        category = achievement.category
                        if category not in categories:
                            categories[category] = {'earned': 0, 'total': 0}
                        categories[category]['earned'] += 1
                
                # Get total achievements by category
                all_achievements = Achievement.query.filter(Achievement.is_active == True).all()
                for achievement in all_achievements:
                    category = achievement.category
                    if category not in categories:
                        categories[category] = {'earned': 0, 'total': 0}
                    categories[category]['total'] += 1
                
                # Calculate total points from achievements
                total_achievement_points = sum(ua.points_awarded for ua in user_achievements)
                
                return {
                    "success": True,
                    "stats": {
                        'total_achievements': total_achievements,
                        'earned_achievements': earned_achievements,
                        'completion_percentage': (earned_achievements / total_achievements * 100) if total_achievements > 0 else 0,
                        'categories': categories,
                        'total_achievement_points': total_achievement_points
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting achievement stats: {e}")
            return {"success": False, "error": "Failed to get achievement stats"}