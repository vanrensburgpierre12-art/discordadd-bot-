"""
Ranking System Module
Handles user rankings and competitive features
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, UserRanking, UserProfile, CasinoGame, AdCompletion
from user_profiles_system import UserProfileManager

logger = logging.getLogger(__name__)

class RankingManager:
    """Manages user rankings and competitive features"""
    
    @staticmethod
    def update_all_rankings() -> Dict[str, Any]:
        """Update all user rankings"""
        try:
            with app.app_context():
                # Get all active users
                users = User.query.filter(User.user_status == 'active').all()
                
                # Calculate rankings for each category
                points_rankings = RankingManager._calculate_points_rankings(users)
                wins_rankings = RankingManager._calculate_wins_rankings(users)
                streak_rankings = RankingManager._calculate_streak_rankings(users)
                xp_rankings = RankingManager._calculate_xp_rankings(users)
                
                # Calculate overall rankings
                overall_rankings = RankingManager._calculate_overall_rankings(
                    points_rankings, wins_rankings, streak_rankings, xp_rankings
                )
                
                # Update or create ranking records
                updated_count = 0
                for user_id in [user.id for user in users]:
                    ranking = UserRanking.query.filter_by(user_id=user_id).first()
                    if not ranking:
                        ranking = UserRanking(user_id=user_id)
                        db.session.add(ranking)
                    
                    ranking.points_rank = points_rankings.get(user_id)
                    ranking.wins_rank = wins_rankings.get(user_id)
                    ranking.streak_rank = streak_rankings.get(user_id)
                    ranking.xp_rank = xp_rankings.get(user_id)
                    ranking.overall_rank = overall_rankings.get(user_id)
                    ranking.last_updated = datetime.utcnow()
                    
                    updated_count += 1
                
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Updated rankings for {updated_count} users"
                }
                
        except Exception as e:
            logger.error(f"Error updating rankings: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to update rankings"}
    
    @staticmethod
    def _calculate_points_rankings(users: List[User]) -> Dict[str, int]:
        """Calculate points-based rankings"""
        # Sort users by total_earned (descending)
        sorted_users = sorted(users, key=lambda u: u.total_earned, reverse=True)
        
        rankings = {}
        for i, user in enumerate(sorted_users, 1):
            rankings[user.id] = i
        
        return rankings
    
    @staticmethod
    def _calculate_wins_rankings(users: List[User]) -> Dict[str, int]:
        """Calculate wins-based rankings"""
        # Get user profiles and sort by total_wins
        user_wins = []
        for user in users:
            profile = UserProfile.query.filter_by(user_id=user.id).first()
            wins = profile.total_wins if profile else 0
            user_wins.append((user.id, wins))
        
        # Sort by wins (descending)
        sorted_users = sorted(user_wins, key=lambda x: x[1], reverse=True)
        
        rankings = {}
        for i, (user_id, wins) in enumerate(sorted_users, 1):
            rankings[user_id] = i
        
        return rankings
    
    @staticmethod
    def _calculate_streak_rankings(users: List[User]) -> Dict[str, int]:
        """Calculate streak-based rankings"""
        # Get user profiles and sort by best_win_streak
        user_streaks = []
        for user in users:
            profile = UserProfile.query.filter_by(user_id=user.id).first()
            streak = profile.best_win_streak if profile else 0
            user_streaks.append((user.id, streak))
        
        # Sort by streak (descending)
        sorted_users = sorted(user_streaks, key=lambda x: x[1], reverse=True)
        
        rankings = {}
        for i, (user_id, streak) in enumerate(sorted_users, 1):
            rankings[user_id] = i
        
        return rankings
    
    @staticmethod
    def _calculate_xp_rankings(users: List[User]) -> Dict[str, int]:
        """Calculate XP-based rankings"""
        # Get user profiles and sort by xp
        user_xp = []
        for user in users:
            profile = UserProfile.query.filter_by(user_id=user.id).first()
            xp = profile.xp if profile else 0
            user_xp.append((user.id, xp))
        
        # Sort by XP (descending)
        sorted_users = sorted(user_xp, key=lambda x: x[1], reverse=True)
        
        rankings = {}
        for i, (user_id, xp) in enumerate(sorted_users, 1):
            rankings[user_id] = i
        
        return rankings
    
    @staticmethod
    def _calculate_overall_rankings(points_rankings: Dict[str, int], 
                                  wins_rankings: Dict[str, int],
                                  streak_rankings: Dict[str, int],
                                  xp_rankings: Dict[str, int]) -> Dict[str, int]:
        """Calculate overall rankings based on all categories"""
        # Get all user IDs
        all_user_ids = set(points_rankings.keys()) | set(wins_rankings.keys()) | set(streak_rankings.keys()) | set(xp_rankings.keys())
        
        # Calculate composite scores
        composite_scores = {}
        for user_id in all_user_ids:
            # Weighted average of all rankings (lower rank = better)
            points_rank = points_rankings.get(user_id, 999999)
            wins_rank = wins_rankings.get(user_id, 999999)
            streak_rank = streak_rankings.get(user_id, 999999)
            xp_rank = xp_rankings.get(user_id, 999999)
            
            # Weighted composite score (lower is better)
            composite_score = (
                points_rank * 0.4 +      # 40% weight for points
                wins_rank * 0.3 +        # 30% weight for wins
                xp_rank * 0.2 +          # 20% weight for XP
                streak_rank * 0.1        # 10% weight for streak
            )
            
            composite_scores[user_id] = composite_score
        
        # Sort by composite score (ascending)
        sorted_users = sorted(composite_scores.items(), key=lambda x: x[1])
        
        # Assign overall rankings
        overall_rankings = {}
        for i, (user_id, score) in enumerate(sorted_users, 1):
            overall_rankings[user_id] = i
        
        return overall_rankings
    
    @staticmethod
    def get_user_rankings(user_id: str) -> Dict[str, Any]:
        """Get user's rankings in all categories"""
        try:
            with app.app_context():
                ranking = UserRanking.query.filter_by(user_id=user_id).first()
                if not ranking:
                    return {"success": False, "error": "User rankings not found"}
                
                # Get total counts for percentile calculation
                total_users = User.query.filter(User.user_status == 'active').count()
                
                def calculate_percentile(rank: int) -> float:
                    if rank is None or total_users == 0:
                        return 0
                    return ((total_users - rank + 1) / total_users) * 100
                
                return {
                    "success": True,
                    "rankings": {
                        'overall_rank': ranking.overall_rank,
                        'overall_percentile': calculate_percentile(ranking.overall_rank),
                        'points_rank': ranking.points_rank,
                        'points_percentile': calculate_percentile(ranking.points_rank),
                        'wins_rank': ranking.wins_rank,
                        'wins_percentile': calculate_percentile(ranking.wins_rank),
                        'streak_rank': ranking.streak_rank,
                        'streak_percentile': calculate_percentile(ranking.streak_rank),
                        'xp_rank': ranking.xp_rank,
                        'xp_percentile': calculate_percentile(ranking.xp_rank),
                        'total_users': total_users,
                        'last_updated': ranking.last_updated.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting user rankings: {e}")
            return {"success": False, "error": "Failed to get user rankings"}
    
    @staticmethod
    def get_ranking_leaderboard(category: str = 'overall', limit: int = 10) -> Dict[str, Any]:
        """Get ranking leaderboard for a specific category"""
        try:
            with app.app_context():
                # Determine sort column
                sort_column = {
                    'overall': UserRanking.overall_rank,
                    'points': UserRanking.points_rank,
                    'wins': UserRanking.wins_rank,
                    'streak': UserRanking.streak_rank,
                    'xp': UserRanking.xp_rank
                }.get(category, UserRanking.overall_rank)
                
                # Get rankings
                rankings = UserRanking.query.filter(
                    sort_column.isnot(None)
                ).order_by(sort_column).limit(limit).all()
                
                leaderboard = []
                for ranking in rankings:
                    user = User.query.get(ranking.user_id)
                    if user:
                        profile = UserProfile.query.filter_by(user_id=ranking.user_id).first()
                        
                        leaderboard.append({
                            'rank': getattr(ranking, f'{category}_rank'),
                            'user_id': ranking.user_id,
                            'username': user.username,
                            'overall_rank': ranking.overall_rank,
                            'points_rank': ranking.points_rank,
                            'wins_rank': ranking.wins_rank,
                            'streak_rank': ranking.streak_rank,
                            'xp_rank': ranking.xp_rank,
                            'level': UserProfileManager._calculate_level_info(profile.xp)['level'] if profile else 1,
                            'xp': profile.xp if profile else 0,
                            'total_earned': user.total_earned,
                            'total_wins': profile.total_wins if profile else 0,
                            'best_streak': profile.best_win_streak if profile else 0
                        })
                
                return {
                    "success": True,
                    "category": category,
                    "leaderboard": leaderboard
                }
                
        except Exception as e:
            logger.error(f"Error getting ranking leaderboard: {e}")
            return {"success": False, "error": "Failed to get ranking leaderboard"}
    
    @staticmethod
    def get_ranking_categories() -> Dict[str, Any]:
        """Get available ranking categories"""
        return {
            "success": True,
            "categories": {
                'overall': {
                    'name': 'Overall Ranking',
                    'description': 'Combined ranking based on all categories',
                    'weight': 'Points (40%), Wins (30%), XP (20%), Streak (10%)'
                },
                'points': {
                    'name': 'Points Ranking',
                    'description': 'Ranking based on total points earned',
                    'weight': 'Total points from ads and activities'
                },
                'wins': {
                    'name': 'Wins Ranking',
                    'description': 'Ranking based on casino game wins',
                    'weight': 'Total casino game victories'
                },
                'streak': {
                    'name': 'Streak Ranking',
                    'description': 'Ranking based on best win streak',
                    'weight': 'Longest consecutive win streak'
                },
                'xp': {
                    'name': 'XP Ranking',
                    'description': 'Ranking based on experience points',
                    'weight': 'Total XP from all activities'
                }
            }
        }
    
    @staticmethod
    def get_ranking_stats() -> Dict[str, Any]:
        """Get overall ranking statistics"""
        try:
            with app.app_context():
                # Get total active users
                total_users = User.query.filter(User.user_status == 'active').count()
                
                # Get users with rankings
                users_with_rankings = UserRanking.query.count()
                
                # Get average rankings
                avg_overall = db.session.query(db.func.avg(UserRanking.overall_rank)).scalar() or 0
                avg_points = db.session.query(db.func.avg(UserRanking.points_rank)).scalar() or 0
                avg_wins = db.session.query(db.func.avg(UserRanking.wins_rank)).scalar() or 0
                avg_streak = db.session.query(db.func.avg(UserRanking.streak_rank)).scalar() or 0
                avg_xp = db.session.query(db.func.avg(UserRanking.xp_rank)).scalar() or 0
                
                # Get last update time
                last_update = db.session.query(db.func.max(UserRanking.last_updated)).scalar()
                
                return {
                    "success": True,
                    "stats": {
                        'total_users': total_users,
                        'users_with_rankings': users_with_rankings,
                        'average_rankings': {
                            'overall': round(avg_overall, 2),
                            'points': round(avg_points, 2),
                            'wins': round(avg_wins, 2),
                            'streak': round(avg_streak, 2),
                            'xp': round(avg_xp, 2)
                        },
                        'last_updated': last_update.isoformat() if last_update else None
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting ranking stats: {e}")
            return {"success": False, "error": "Failed to get ranking stats"}
    
    @staticmethod
    def get_user_ranking_history(user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user's ranking history (if implemented)"""
        # This would require a separate table to track ranking history over time
        # For now, return current rankings
        return RankingManager.get_user_rankings(user_id)