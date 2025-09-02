"""
Quest System Module
Handles quests, missions, and story-driven content
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, UserProfile, CasinoGame, AdCompletion, Referral, DailyBonus

logger = logging.getLogger(__name__)

class QuestManager:
    """Manages quests and missions"""
    
    def __init__(self):
        # Quest types
        self.quest_types = ['tutorial', 'daily', 'weekly', 'story', 'achievement', 'seasonal', 'special']
        
        # Quest statuses
        self.quest_statuses = ['locked', 'available', 'active', 'completed', 'expired', 'failed']
        
        # Quest requirements
        self.requirement_types = [
            'earn_points', 'play_games', 'win_games', 'lose_games', 'earn_casino_points',
            'watch_ads', 'refer_friends', 'claim_daily_bonus', 'reach_level', 'earn_xp',
            'complete_achievements', 'join_guild', 'create_guild', 'participate_tournament',
            'redeem_gift_card', 'maintain_streak', 'spend_points', 'play_specific_game'
        ]
    
    def create_quest(self, name: str, description: str, quest_type: str, 
                    requirements: List[Dict[str, Any]], rewards: Dict[str, Any],
                    prerequisites: List[int] = None, time_limit: int = None) -> Dict[str, Any]:
        """Create a new quest"""
        try:
            with app.app_context():
                if quest_type not in self.quest_types:
                    return {"success": False, "error": "Invalid quest type"}
                
                # Validate requirements
                for req in requirements:
                    if req.get('type') not in self.requirement_types:
                        return {"success": False, "error": f"Invalid requirement type: {req.get('type')}"}
                
                # Create quest data structure
                quest_data = {
                    'id': len(self.get_all_quests().get('quests', [])) + 1,
                    'name': name,
                    'description': description,
                    'quest_type': quest_type,
                    'requirements': requirements,
                    'rewards': rewards,
                    'prerequisites': prerequisites or [],
                    'time_limit': time_limit,  # in hours
                    'created_at': datetime.utcnow().isoformat(),
                    'is_active': True
                }
                
                # Save quest (in a real implementation, this would be in database)
                quests = self.get_all_quests().get('quests', [])
                quests.append(quest_data)
                
                return {
                    "success": True,
                    "quest_id": quest_data['id'],
                    "message": f"Quest '{name}' created successfully",
                    "quest": quest_data
                }
                
        except Exception as e:
            logger.error(f"Error creating quest: {e}")
            return {"success": False, "error": f"Failed to create quest: {str(e)}"}
    
    def get_all_quests(self) -> Dict[str, Any]:
        """Get all available quests"""
        try:
            # In a real implementation, this would query the database
            # For now, return some example quests
            example_quests = [
                {
                    'id': 1,
                    'name': 'First Steps',
                    'description': 'Complete your first casino game to get started!',
                    'quest_type': 'tutorial',
                    'requirements': [
                        {'type': 'play_games', 'value': 1, 'description': 'Play 1 casino game'}
                    ],
                    'rewards': {
                        'points': 100,
                        'xp': 50,
                        'items': ['welcome_badge']
                    },
                    'prerequisites': [],
                    'time_limit': None,
                    'created_at': datetime.utcnow().isoformat(),
                    'is_active': True
                },
                {
                    'id': 2,
                    'name': 'Daily Grinder',
                    'description': 'Earn 500 points from watching ads today',
                    'quest_type': 'daily',
                    'requirements': [
                        {'type': 'earn_points', 'value': 500, 'description': 'Earn 500 points from ads'}
                    ],
                    'rewards': {
                        'points': 200,
                        'xp': 100
                    },
                    'prerequisites': [],
                    'time_limit': 24,  # 24 hours
                    'created_at': datetime.utcnow().isoformat(),
                    'is_active': True
                },
                {
                    'id': 3,
                    'name': 'Casino Master',
                    'description': 'Win 10 casino games this week',
                    'quest_type': 'weekly',
                    'requirements': [
                        {'type': 'win_games', 'value': 10, 'description': 'Win 10 casino games'}
                    ],
                    'rewards': {
                        'points': 1000,
                        'xp': 500,
                        'items': ['casino_master_badge']
                    },
                    'prerequisites': [],
                    'time_limit': 168,  # 7 days
                    'created_at': datetime.utcnow().isoformat(),
                    'is_active': True
                },
                {
                    'id': 4,
                    'name': 'Social Butterfly',
                    'description': 'Refer 3 friends to the platform',
                    'quest_type': 'story',
                    'requirements': [
                        {'type': 'refer_friends', 'value': 3, 'description': 'Refer 3 friends'}
                    ],
                    'rewards': {
                        'points': 1500,
                        'xp': 750,
                        'items': ['social_butterfly_badge', 'referral_boost']
                    },
                    'prerequisites': [1],  # Requires completing "First Steps"
                    'time_limit': None,
                    'created_at': datetime.utcnow().isoformat(),
                    'is_active': True
                },
                {
                    'id': 5,
                    'name': 'High Roller',
                    'description': 'Earn 5000 points from casino games',
                    'quest_type': 'achievement',
                    'requirements': [
                        {'type': 'earn_casino_points', 'value': 5000, 'description': 'Earn 5000 points from casino'}
                    ],
                    'rewards': {
                        'points': 2000,
                        'xp': 1000,
                        'items': ['high_roller_badge', 'vip_status']
                    },
                    'prerequisites': [1, 3],  # Requires completing "First Steps" and "Casino Master"
                    'time_limit': None,
                    'created_at': datetime.utcnow().isoformat(),
                    'is_active': True
                }
            ]
            
            return {
                "success": True,
                "quests": example_quests,
                "count": len(example_quests)
            }
            
        except Exception as e:
            logger.error(f"Error getting all quests: {e}")
            return {"success": False, "error": f"Failed to get quests: {str(e)}"}
    
    def get_user_quests(self, user_id: str) -> Dict[str, Any]:
        """Get user's quest progress"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # Get all available quests
                all_quests = self.get_all_quests().get('quests', [])
                
                # Get user's quest progress (in real implementation, this would be in database)
                user_quest_progress = self._get_user_quest_progress(user_id)
                
                user_quests = []
                for quest in all_quests:
                    if not quest['is_active']:
                        continue
                    
                    # Check if user meets prerequisites
                    if not self._check_prerequisites(user_id, quest['prerequisites']):
                        quest_status = 'locked'
                    else:
                        quest_status = 'available'
                    
                    # Get user's progress for this quest
                    progress = user_quest_progress.get(quest['id'], {
                        'status': quest_status,
                        'progress': {},
                        'started_at': None,
                        'completed_at': None
                    })
                    
                    # Calculate current progress
                    current_progress = self._calculate_quest_progress(user_id, quest['requirements'])
                    
                    # Check if quest is completed
                    is_completed = self._is_quest_completed(quest['requirements'], current_progress)
                    
                    if is_completed and progress['status'] != 'completed':
                        progress['status'] = 'completed'
                        progress['completed_at'] = datetime.utcnow().isoformat()
                        
                        # Award rewards
                        self._award_quest_rewards(user_id, quest['rewards'])
                    
                    user_quests.append({
                        'quest_id': quest['id'],
                        'name': quest['name'],
                        'description': quest['description'],
                        'quest_type': quest['quest_type'],
                        'requirements': quest['requirements'],
                        'rewards': quest['rewards'],
                        'status': progress['status'],
                        'progress': current_progress,
                        'started_at': progress['started_at'],
                        'completed_at': progress['completed_at'],
                        'time_limit': quest['time_limit'],
                        'is_completed': is_completed
                    })
                
                return {
                    "success": True,
                    "user_quests": user_quests,
                    "count": len(user_quests)
                }
                
        except Exception as e:
            logger.error(f"Error getting user quests: {e}")
            return {"success": False, "error": f"Failed to get user quests: {str(e)}"}
    
    def start_quest(self, user_id: str, quest_id: int) -> Dict[str, Any]:
        """Start a quest for a user"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # Get quest details
                all_quests = self.get_all_quests().get('quests', [])
                quest = next((q for q in all_quests if q['id'] == quest_id), None)
                
                if not quest:
                    return {"success": False, "error": "Quest not found"}
                
                if not quest['is_active']:
                    return {"success": False, "error": "Quest is not active"}
                
                # Check prerequisites
                if not self._check_prerequisites(user_id, quest['prerequisites']):
                    return {"success": False, "error": "Prerequisites not met"}
                
                # Check if quest is already started or completed
                user_quest_progress = self._get_user_quest_progress(user_id)
                current_progress = user_quest_progress.get(quest_id, {})
                
                if current_progress.get('status') in ['active', 'completed']:
                    return {"success": False, "error": "Quest already started or completed"}
                
                # Start the quest
                user_quest_progress[quest_id] = {
                    'status': 'active',
                    'progress': {},
                    'started_at': datetime.utcnow().isoformat(),
                    'completed_at': None
                }
                
                # Save progress (in real implementation, this would be in database)
                self._save_user_quest_progress(user_id, user_quest_progress)
                
                return {
                    "success": True,
                    "message": f"Quest '{quest['name']}' started successfully",
                    "quest_id": quest_id,
                    "started_at": user_quest_progress[quest_id]['started_at']
                }
                
        except Exception as e:
            logger.error(f"Error starting quest: {e}")
            return {"success": False, "error": f"Failed to start quest: {str(e)}"}
    
    def complete_quest(self, user_id: str, quest_id: int) -> Dict[str, Any]:
        """Complete a quest for a user"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                # Get quest details
                all_quests = self.get_all_quests().get('quests', [])
                quest = next((q for q in all_quests if q['id'] == quest_id), None)
                
                if not quest:
                    return {"success": False, "error": "Quest not found"}
                
                # Check if quest is completed
                current_progress = self._calculate_quest_progress(user_id, quest['requirements'])
                is_completed = self._is_quest_completed(quest['requirements'], current_progress)
                
                if not is_completed:
                    return {"success": False, "error": "Quest requirements not met"}
                
                # Get user's quest progress
                user_quest_progress = self._get_user_quest_progress(user_id)
                current_quest_progress = user_quest_progress.get(quest_id, {})
                
                if current_quest_progress.get('status') == 'completed':
                    return {"success": False, "error": "Quest already completed"}
                
                # Complete the quest
                user_quest_progress[quest_id] = {
                    'status': 'completed',
                    'progress': current_progress,
                    'started_at': current_quest_progress.get('started_at'),
                    'completed_at': datetime.utcnow().isoformat()
                }
                
                # Award rewards
                rewards_awarded = self._award_quest_rewards(user_id, quest['rewards'])
                
                # Save progress
                self._save_user_quest_progress(user_id, user_quest_progress)
                
                return {
                    "success": True,
                    "message": f"Quest '{quest['name']}' completed successfully",
                    "quest_id": quest_id,
                    "completed_at": user_quest_progress[quest_id]['completed_at'],
                    "rewards_awarded": rewards_awarded
                }
                
        except Exception as e:
            logger.error(f"Error completing quest: {e}")
            return {"success": False, "error": f"Failed to complete quest: {str(e)}"}
    
    def _check_prerequisites(self, user_id: str, prerequisites: List[int]) -> bool:
        """Check if user meets quest prerequisites"""
        if not prerequisites:
            return True
        
        user_quest_progress = self._get_user_quest_progress(user_id)
        
        for prereq_id in prerequisites:
            prereq_progress = user_quest_progress.get(prereq_id, {})
            if prereq_progress.get('status') != 'completed':
                return False
        
        return True
    
    def _calculate_quest_progress(self, user_id: str, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate user's progress for quest requirements"""
        progress = {}
        
        for req in requirements:
            req_type = req['type']
            req_value = req['value']
            
            if req_type == 'earn_points':
                # Count points earned from ads
                ads = AdCompletion.query.filter_by(user_id=user_id).all()
                current_value = sum(ad.points_earned for ad in ads)
            elif req_type == 'play_games':
                # Count total games played
                games = CasinoGame.query.filter_by(user_id=user_id).all()
                current_value = len(games)
            elif req_type == 'win_games':
                # Count games won
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.win_amount > 0
                ).all()
                current_value = len(games)
            elif req_type == 'lose_games':
                # Count games lost
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.win_amount == 0
                ).all()
                current_value = len(games)
            elif req_type == 'earn_casino_points':
                # Count points earned from casino
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.win_amount > 0
                ).all()
                current_value = sum(game.win_amount for game in games)
            elif req_type == 'watch_ads':
                # Count ads watched
                ads = AdCompletion.query.filter_by(user_id=user_id).all()
                current_value = len(ads)
            elif req_type == 'refer_friends':
                # Count referrals
                referrals = Referral.query.filter_by(referrer_id=user_id).all()
                current_value = len(referrals)
            elif req_type == 'claim_daily_bonus':
                # Count daily bonuses claimed
                daily_bonus = DailyBonus.query.filter_by(user_id=user_id).first()
                current_value = daily_bonus.total_claimed if daily_bonus else 0
            elif req_type == 'reach_level':
                # Get user level
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                current_value = profile.level if profile else 1
            elif req_type == 'earn_xp':
                # Get user XP
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                current_value = profile.xp if profile else 0
            else:
                current_value = 0
            
            progress[req_type] = {
                'current': current_value,
                'required': req_value,
                'completed': current_value >= req_value,
                'percentage': min(100, (current_value / req_value * 100)) if req_value > 0 else 100
            }
        
        return progress
    
    def _is_quest_completed(self, requirements: List[Dict[str, Any]], progress: Dict[str, Any]) -> bool:
        """Check if quest is completed based on progress"""
        for req in requirements:
            req_type = req['type']
            if req_type not in progress or not progress[req_type]['completed']:
                return False
        return True
    
    def _award_quest_rewards(self, user_id: str, rewards: Dict[str, Any]) -> Dict[str, Any]:
        """Award quest rewards to user"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                awarded_rewards = {}
                
                # Award points
                if 'points' in rewards:
                    points = rewards['points']
                    user.points_balance += points
                    user.total_earned += points
                    awarded_rewards['points'] = points
                
                # Award XP
                if 'xp' in rewards:
                    xp = rewards['xp']
                    profile = UserProfile.query.filter_by(user_id=user_id).first()
                    if not profile:
                        profile = UserProfile(user_id=user_id)
                        db.session.add(profile)
                    
                    profile.xp += xp
                    awarded_rewards['xp'] = xp
                
                # Award items (placeholder)
                if 'items' in rewards:
                    items = rewards['items']
                    awarded_rewards['items'] = items
                
                db.session.commit()
                
                return {
                    "success": True,
                    "awarded_rewards": awarded_rewards
                }
                
        except Exception as e:
            logger.error(f"Error awarding quest rewards: {e}")
            db.session.rollback()
            return {"success": False, "error": f"Failed to award rewards: {str(e)}"}
    
    def _get_user_quest_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's quest progress (placeholder for database)"""
        # In a real implementation, this would query the database
        # For now, return empty progress
        return {}
    
    def _save_user_quest_progress(self, user_id: str, progress: Dict[str, Any]):
        """Save user's quest progress (placeholder for database)"""
        # In a real implementation, this would save to database
        pass
    
    def get_quest_categories(self) -> Dict[str, Any]:
        """Get quest categories and types"""
        return {
            "success": True,
            "quest_types": [
                {
                    "type": "tutorial",
                    "name": "Tutorial",
                    "description": "Learn the basics of the platform"
                },
                {
                    "type": "daily",
                    "name": "Daily Quests",
                    "description": "Complete daily tasks for rewards"
                },
                {
                    "type": "weekly",
                    "name": "Weekly Quests",
                    "description": "Complete weekly challenges"
                },
                {
                    "type": "story",
                    "name": "Story Quests",
                    "description": "Follow the main storyline"
                },
                {
                    "type": "achievement",
                    "name": "Achievement Quests",
                    "description": "Unlock special achievements"
                },
                {
                    "type": "seasonal",
                    "name": "Seasonal Quests",
                    "description": "Limited-time seasonal content"
                },
                {
                    "type": "special",
                    "name": "Special Quests",
                    "description": "Unique and rare quests"
                }
            ],
            "requirement_types": self.requirement_types,
            "quest_statuses": self.quest_statuses
        }
    
    def get_quest_rewards_info(self) -> Dict[str, Any]:
        """Get information about quest rewards"""
        return {
            "success": True,
            "reward_types": {
                "points": {
                    "description": "Platform currency",
                    "range": "10-10000 points"
                },
                "xp": {
                    "description": "Experience points for leveling",
                    "range": "10-5000 XP"
                },
                "items": {
                    "description": "Special items and badges",
                    "types": ["badges", "boosters", "exclusive_items"]
                },
                "status": {
                    "description": "Special status or privileges",
                    "types": ["vip_status", "premium_access", "exclusive_features"]
                }
            }
        }