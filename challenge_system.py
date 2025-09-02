"""
Challenge System Module
Handles daily, weekly, and monthly challenges
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, Challenge, UserChallenge, UserProfile, CasinoGame, AdCompletion

logger = logging.getLogger(__name__)

class ChallengeManager:
    """Manages challenges and user progress"""
    
    @staticmethod
    def create_challenge(name: str, description: str, challenge_type: str, 
                        requirement_type: str, requirement_value: int, 
                        points_reward: int, duration_days: int = 1) -> Dict[str, Any]:
        """Create a new challenge"""
        try:
            with app.app_context():
                start_date = datetime.utcnow()
                end_date = start_date + timedelta(days=duration_days)
                
                challenge = Challenge(
                    name=name,
                    description=description,
                    challenge_type=challenge_type,
                    requirement_type=requirement_type,
                    requirement_value=requirement_value,
                    points_reward=points_reward,
                    start_date=start_date,
                    end_date=end_date
                )
                
                db.session.add(challenge)
                db.session.commit()
                
                return {
                    "success": True,
                    "challenge_id": challenge.id,
                    "message": f"Challenge '{name}' created successfully"
                }
                
        except Exception as e:
            logger.error(f"Error creating challenge: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to create challenge"}
    
    @staticmethod
    def get_active_challenges() -> Dict[str, Any]:
        """Get all active challenges"""
        try:
            with app.app_context():
                now = datetime.utcnow()
                challenges = Challenge.query.filter(
                    Challenge.is_active == True,
                    Challenge.start_date <= now,
                    Challenge.end_date >= now
                ).all()
                
                challenge_list = []
                for challenge in challenges:
                    challenge_list.append({
                        'id': challenge.id,
                        'name': challenge.name,
                        'description': challenge.description,
                        'challenge_type': challenge.challenge_type,
                        'requirement_type': challenge.requirement_type,
                        'requirement_value': challenge.requirement_value,
                        'points_reward': challenge.points_reward,
                        'start_date': challenge.start_date.isoformat(),
                        'end_date': challenge.end_date.isoformat(),
                        'time_remaining': (challenge.end_date - now).total_seconds()
                    })
                
                return {
                    "success": True,
                    "challenges": challenge_list
                }
                
        except Exception as e:
            logger.error(f"Error getting active challenges: {e}")
            return {"success": False, "error": "Failed to get challenges"}
    
    @staticmethod
    def get_user_challenges(user_id: str) -> Dict[str, Any]:
        """Get user's challenge progress"""
        try:
            with app.app_context():
                # Get active challenges
                now = datetime.utcnow()
                active_challenges = Challenge.query.filter(
                    Challenge.is_active == True,
                    Challenge.start_date <= now,
                    Challenge.end_date >= now
                ).all()
                
                user_challenges = []
                for challenge in active_challenges:
                    # Get user's progress for this challenge
                    user_challenge = UserChallenge.query.filter_by(
                        user_id=user_id,
                        challenge_id=challenge.id
                    ).first()
                    
                    if not user_challenge:
                        # Create new user challenge entry
                        user_challenge = UserChallenge(
                            user_id=user_id,
                            challenge_id=challenge.id,
                            progress=0,
                            completed=False
                        )
                        db.session.add(user_challenge)
                        db.session.commit()
                    
                    # Calculate current progress
                    current_progress = ChallengeManager._calculate_progress(
                        user_id, challenge.requirement_type, challenge.start_date
                    )
                    
                    user_challenge.progress = current_progress
                    
                    # Check if challenge is completed
                    if current_progress >= challenge.requirement_value and not user_challenge.completed:
                        user_challenge.completed = True
                        user_challenge.completed_at = datetime.utcnow()
                        user_challenge.points_earned = challenge.points_reward
                        
                        # Award points to user
                        user = User.query.filter_by(id=user_id).first()
                        if user:
                            user.points_balance += challenge.points_reward
                            user.total_earned += challenge.points_reward
                    
                    db.session.commit()
                    
                    user_challenges.append({
                        'challenge_id': challenge.id,
                        'name': challenge.name,
                        'description': challenge.description,
                        'challenge_type': challenge.challenge_type,
                        'requirement_type': challenge.requirement_type,
                        'requirement_value': challenge.requirement_value,
                        'points_reward': challenge.points_reward,
                        'progress': current_progress,
                        'completed': user_challenge.completed,
                        'completed_at': user_challenge.completed_at.isoformat() if user_challenge.completed_at else None,
                        'points_earned': user_challenge.points_earned,
                        'time_remaining': (challenge.end_date - now).total_seconds()
                    })
                
                return {
                    "success": True,
                    "user_challenges": user_challenges
                }
                
        except Exception as e:
            logger.error(f"Error getting user challenges: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to get user challenges"}
    
    @staticmethod
    def _calculate_progress(user_id: str, requirement_type: str, start_date: datetime) -> int:
        """Calculate user's progress for a specific requirement type"""
        try:
            if requirement_type == 'earn_points':
                # Count points earned from ads since start date
                ads = AdCompletion.query.filter(
                    AdCompletion.user_id == user_id,
                    AdCompletion.completed_at >= start_date
                ).all()
                return sum(ad.points_earned for ad in ads)
            
            elif requirement_type == 'play_games':
                # Count games played since start date
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.played_at >= start_date
                ).all()
                return len(games)
            
            elif requirement_type == 'win_games':
                # Count games won since start date
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.played_at >= start_date,
                    CasinoGame.win_amount > 0
                ).all()
                return len(games)
            
            elif requirement_type == 'earn_casino_points':
                # Count points earned from casino games since start date
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.played_at >= start_date,
                    CasinoGame.win_amount > 0
                ).all()
                return sum(game.win_amount for game in games)
            
            elif requirement_type == 'daily_login':
                # Count days logged in since start date
                # This would need to be tracked separately, for now return 0
                return 0
            
            elif requirement_type == 'refer_friends':
                # Count referrals since start date
                from database import Referral
                referrals = Referral.query.filter(
                    Referral.referrer_id == user_id,
                    Referral.created_at >= start_date
                ).all()
                return len(referrals)
            
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error calculating progress: {e}")
            return 0
    
    @staticmethod
    def create_daily_challenges() -> Dict[str, Any]:
        """Create daily challenges automatically"""
        try:
            with app.app_context():
                # Check if daily challenges already exist for today
                today = datetime.utcnow().date()
                existing_daily = Challenge.query.filter(
                    Challenge.challenge_type == 'daily',
                    Challenge.start_date >= datetime.combine(today, datetime.min.time()),
                    Challenge.start_date < datetime.combine(today + timedelta(days=1), datetime.min.time())
                ).count()
                
                if existing_daily > 0:
                    return {"success": True, "message": "Daily challenges already exist for today"}
                
                # Create daily challenges
                daily_challenges = [
                    {
                        'name': 'Daily Earner',
                        'description': 'Earn 100 points from watching ads',
                        'requirement_type': 'earn_points',
                        'requirement_value': 100,
                        'points_reward': 50
                    },
                    {
                        'name': 'Casino Player',
                        'description': 'Play 5 casino games',
                        'requirement_type': 'play_games',
                        'requirement_value': 5,
                        'points_reward': 100
                    },
                    {
                        'name': 'Lucky Winner',
                        'description': 'Win 3 casino games',
                        'requirement_type': 'win_games',
                        'requirement_value': 3,
                        'points_reward': 200
                    }
                ]
                
                created_count = 0
                for challenge_data in daily_challenges:
                    result = ChallengeManager.create_challenge(
                        name=challenge_data['name'],
                        description=challenge_data['description'],
                        challenge_type='daily',
                        requirement_type=challenge_data['requirement_type'],
                        requirement_value=challenge_data['requirement_value'],
                        points_reward=challenge_data['points_reward'],
                        duration_days=1
                    )
                    if result['success']:
                        created_count += 1
                
                return {
                    "success": True,
                    "message": f"Created {created_count} daily challenges"
                }
                
        except Exception as e:
            logger.error(f"Error creating daily challenges: {e}")
            return {"success": False, "error": "Failed to create daily challenges"}
    
    @staticmethod
    def create_weekly_challenges() -> Dict[str, Any]:
        """Create weekly challenges automatically"""
        try:
            with app.app_context():
                # Check if weekly challenges already exist for this week
                today = datetime.utcnow().date()
                week_start = today - timedelta(days=today.weekday())
                
                existing_weekly = Challenge.query.filter(
                    Challenge.challenge_type == 'weekly',
                    Challenge.start_date >= datetime.combine(week_start, datetime.min.time()),
                    Challenge.start_date < datetime.combine(week_start + timedelta(days=7), datetime.min.time())
                ).count()
                
                if existing_weekly > 0:
                    return {"success": True, "message": "Weekly challenges already exist for this week"}
                
                # Create weekly challenges
                weekly_challenges = [
                    {
                        'name': 'Weekly Grinder',
                        'description': 'Earn 1000 points from watching ads',
                        'requirement_type': 'earn_points',
                        'requirement_value': 1000,
                        'points_reward': 500
                    },
                    {
                        'name': 'Casino Master',
                        'description': 'Play 50 casino games',
                        'requirement_type': 'play_games',
                        'requirement_value': 50,
                        'points_reward': 1000
                    },
                    {
                        'name': 'High Roller',
                        'description': 'Earn 2000 points from casino games',
                        'requirement_type': 'earn_casino_points',
                        'requirement_value': 2000,
                        'points_reward': 1500
                    }
                ]
                
                created_count = 0
                for challenge_data in weekly_challenges:
                    result = ChallengeManager.create_challenge(
                        name=challenge_data['name'],
                        description=challenge_data['description'],
                        challenge_type='weekly',
                        requirement_type=challenge_data['requirement_type'],
                        requirement_value=challenge_data['requirement_value'],
                        points_reward=challenge_data['points_reward'],
                        duration_days=7
                    )
                    if result['success']:
                        created_count += 1
                
                return {
                    "success": True,
                    "message": f"Created {created_count} weekly challenges"
                }
                
        except Exception as e:
            logger.error(f"Error creating weekly challenges: {e}")
            return {"success": False, "error": "Failed to create weekly challenges"}
    
    @staticmethod
    def cleanup_expired_challenges() -> Dict[str, Any]:
        """Clean up expired challenges"""
        try:
            with app.app_context():
                now = datetime.utcnow()
                expired_challenges = Challenge.query.filter(
                    Challenge.end_date < now,
                    Challenge.is_active == True
                ).all()
                
                for challenge in expired_challenges:
                    challenge.is_active = False
                
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Deactivated {len(expired_challenges)} expired challenges"
                }
                
        except Exception as e:
            logger.error(f"Error cleaning up expired challenges: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to cleanup expired challenges"}