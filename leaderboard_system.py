diff --git a/leaderboard_system.py b/leaderboard_system.py
--- a/leaderboard_system.py
+++ b/leaderboard_system.py
@@ -0,0 +1,400 @@
+"""
+Leaderboard System Module
+Handles leaderboards, rankings, and competitive features
+"""
+
+import logging
+from datetime import datetime, timedelta
+from typing import Dict, Any, List, Optional
+from app_context import app, db
+from database import User, Leaderboard, LeaderboardEntry, UserProfile, UserRanking
+
+logger = logging.getLogger(__name__)
+
+class LeaderboardManager:
+    """Manages leaderboards and rankings"""
+    
+    @staticmethod
+    def create_leaderboard(name: str, description: str, leaderboard_type: str, 
+                          period: str) -> Dict[str, Any]:
+        """Create a new leaderboard"""
+        try:
+            with app.app_context():
+                leaderboard = Leaderboard(
+                    name=name,
+                    description=description,
+                    leaderboard_type=leaderboard_type,
+                    period=period
+                )
+                
+                db.session.add(leaderboard)
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "leaderboard_id": leaderboard.id,
+                    "message": f"Leaderboard '{name}' created successfully"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error creating leaderboard: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to create leaderboard"}
+    
+    @staticmethod
+    def get_leaderboard(leaderboard_id: int, limit: int = 10) -> Dict[str, Any]:
+        """Get leaderboard entries"""
+        try:
+            with app.app_context():
+                leaderboard = Leaderboard.query.get(leaderboard_id)
+                if not leaderboard:
+                    return {"success": False, "error": "Leaderboard not found"}
+                
+                # Get current period
+                period_start, period_end = LeaderboardManager._get_period_dates(leaderboard.period)
+                
+                # Get entries for current period
+                entries = LeaderboardEntry.query.filter(
+                    LeaderboardEntry.leaderboard_id == leaderboard_id,
+                    LeaderboardEntry.period_start == period_start,
+                    LeaderboardEntry.period_end == period_end
+                ).order_by(LeaderboardEntry.score.desc()).limit(limit).all()
+                
+                entry_list = []
+                for i, entry in enumerate(entries, 1):
+                    user = User.query.get(entry.user_id)
+                    if user:
+                        entry_list.append({
+                            'rank': i,
+                            'user_id': entry.user_id,
+                            'username': user.username,
+                            'score': entry.score,
+                            'updated_at': entry.updated_at.isoformat()
+                        })
+                
+                return {
+                    "success": True,
+                    "leaderboard": {
+                        'id': leaderboard.id,
+                        'name': leaderboard.name,
+                        'description': leaderboard.description,
+                        'type': leaderboard.leaderboard_type,
+                        'period': leaderboard.period,
+                        'period_start': period_start.isoformat(),
+                        'period_end': period_end.isoformat(),
+                        'entries': entry_list
+                    }
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting leaderboard: {e}")
+            return {"success": False, "error": "Failed to get leaderboard"}
+    
+    @staticmethod
+    def get_user_rank(user_id: str, leaderboard_id: int) -> Dict[str, Any]:
+        """Get user's rank in a specific leaderboard"""
+        try:
+            with app.app_context():
+                leaderboard = Leaderboard.query.get(leaderboard_id)
+                if not leaderboard:
+                    return {"success": False, "error": "Leaderboard not found"}
+                
+                # Get current period
+                period_start, period_end = LeaderboardManager._get_period_dates(leaderboard.period)
+                
+                # Get user's entry
+                user_entry = LeaderboardEntry.query.filter(
+                    LeaderboardEntry.leaderboard_id == leaderboard_id,
+                    LeaderboardEntry.user_id == user_id,
+                    LeaderboardEntry.period_start == period_start,
+                    LeaderboardEntry.period_end == period_end
+                ).first()
+                
+                if not user_entry:
+                    return {"success": False, "error": "User not found in leaderboard"}
+                
+                # Get rank (count of users with higher scores)
+                rank = LeaderboardEntry.query.filter(
+                    LeaderboardEntry.leaderboard_id == leaderboard_id,
+                    LeaderboardEntry.period_start == period_start,
+                    LeaderboardEntry.period_end == period_end,
+                    LeaderboardEntry.score > user_entry.score
+                ).count() + 1
+                
+                # Get total participants
+                total_participants = LeaderboardEntry.query.filter(
+                    LeaderboardEntry.leaderboard_id == leaderboard_id,
+                    LeaderboardEntry.period_start == period_start,
+                    LeaderboardEntry.period_end == period_end
+                ).count()
+                
+                return {
+                    "success": True,
+                    "rank": rank,
+                    "score": user_entry.score,
+                    "total_participants": total_participants,
+                    "percentile": ((total_participants - rank + 1) / total_participants * 100) if total_participants > 0 else 0
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting user rank: {e}")
+            return {"success": False, "error": "Failed to get user rank"}
+    
+    @staticmethod
+    def update_leaderboard_scores(leaderboard_id: int) -> Dict[str, Any]:
+        """Update all scores for a leaderboard"""
+        try:
+            with app.app_context():
+                leaderboard = Leaderboard.query.get(leaderboard_id)
+                if not leaderboard:
+                    return {"success": False, "error": "Leaderboard not found"}
+                
+                # Get current period
+                period_start, period_end = LeaderboardManager._get_period_dates(leaderboard.period)
+                
+                # Get all users
+                users = User.query.filter(User.user_status == 'active').all()
+                
+                updated_count = 0
+                for user in users:
+                    # Calculate user's score based on leaderboard type
+                    score = LeaderboardManager._calculate_score(user.id, leaderboard.leaderboard_type, period_start, period_end)
+                    
+                    # Get or create entry
+                    entry = LeaderboardEntry.query.filter(
+                        LeaderboardEntry.leaderboard_id == leaderboard_id,
+                        LeaderboardEntry.user_id == user.id,
+                        LeaderboardEntry.period_start == period_start,
+                        LeaderboardEntry.period_end == period_end
+                    ).first()
+                    
+                    if not entry:
+                        entry = LeaderboardEntry(
+                            leaderboard_id=leaderboard_id,
+                            user_id=user.id,
+                            score=score,
+                            period_start=period_start,
+                            period_end=period_end
+                        )
+                        db.session.add(entry)
+                    else:
+                        entry.score = score
+                        entry.updated_at = datetime.utcnow()
+                    
+                    updated_count += 1
+                
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "message": f"Updated {updated_count} leaderboard entries"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error updating leaderboard scores: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to update leaderboard scores"}
+    
+    @staticmethod
+    def _calculate_score(user_id: str, leaderboard_type: str, period_start: datetime, period_end: datetime) -> int:
+        """Calculate user's score for a specific leaderboard type and period"""
+        try:
+            if leaderboard_type == 'points':
+                # Total points earned in period
+                from database import AdCompletion
+                ads = AdCompletion.query.filter(
+                    AdCompletion.user_id == user_id,
+                    AdCompletion.completed_at >= period_start,
+                    AdCompletion.completed_at <= period_end
+                ).all()
+                return sum(ad.points_earned for ad in ads)
+            
+            elif leaderboard_type == 'wins':
+                # Total wins in period
+                from database import CasinoGame
+                games = CasinoGame.query.filter(
+                    CasinoGame.user_id == user_id,
+                    CasinoGame.played_at >= period_start,
+                    CasinoGame.played_at <= period_end,
+                    CasinoGame.win_amount > 0
+                ).all()
+                return len(games)
+            
+            elif leaderboard_type == 'streak':
+                # Best win streak in period
+                profile = UserProfile.query.filter_by(user_id=user_id).first()
+                return profile.best_win_streak if profile else 0
+            
+            elif leaderboard_type == 'xp':
+                # Total XP in period
+                profile = UserProfile.query.filter_by(user_id=user_id).first()
+                return profile.xp if profile else 0
+            
+            elif leaderboard_type == 'games_played':
+                # Total games played in period
+                from database import CasinoGame
+                games = CasinoGame.query.filter(
+                    CasinoGame.user_id == user_id,
+                    CasinoGame.played_at >= period_start,
+                    CasinoGame.played_at <= period_end
+                ).all()
+                return len(games)
+            
+            else:
+                return 0
+                
+        except Exception as e:
+            logger.error(f"Error calculating score: {e}")
+            return 0
+    
+    @staticmethod
+    def _get_period_dates(period: str) -> tuple[datetime, datetime]:
+        """Get start and end dates for a period"""
+        now = datetime.utcnow()
+        
+        if period == 'daily':
+            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
+            end = start + timedelta(days=1)
+        elif period == 'weekly':
+            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
+            end = start + timedelta(days=7)
+        elif period == 'monthly':
+            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
+            if start.month == 12:
+                end = start.replace(year=start.year + 1, month=1)
+            else:
+                end = start.replace(month=start.month + 1)
+        else:  # all_time
+            start = datetime(2020, 1, 1)  # Arbitrary start date
+            end = now + timedelta(days=1)
+        
+        return start, end
+    
+    @staticmethod
+    def initialize_default_leaderboards() -> Dict[str, Any]:
+        """Initialize default leaderboards"""
+        try:
+            with app.app_context():
+                # Check if leaderboards already exist
+                if Leaderboard.query.count() > 0:
+                    return {"success": True, "message": "Leaderboards already initialized"}
+                
+                default_leaderboards = [
+                    {
+                        'name': 'Daily Points',
+                        'description': 'Most points earned today',
+                        'leaderboard_type': 'points',
+                        'period': 'daily'
+                    },
+                    {
+                        'name': 'Weekly Points',
+                        'description': 'Most points earned this week',
+                        'leaderboard_type': 'points',
+                        'period': 'weekly'
+                    },
+                    {
+                        'name': 'Monthly Points',
+                        'description': 'Most points earned this month',
+                        'leaderboard_type': 'points',
+                        'period': 'monthly'
+                    },
+                    {
+                        'name': 'All-Time Points',
+                        'description': 'Most points earned ever',
+                        'leaderboard_type': 'points',
+                        'period': 'all_time'
+                    },
+                    {
+                        'name': 'Daily Wins',
+                        'description': 'Most casino wins today',
+                        'leaderboard_type': 'wins',
+                        'period': 'daily'
+                    },
+                    {
+                        'name': 'Weekly Wins',
+                        'description': 'Most casino wins this week',
+                        'leaderboard_type': 'wins',
+                        'period': 'weekly'
+                    },
+                    {
+                        'name': 'Win Streak',
+                        'description': 'Best win streaks',
+                        'leaderboard_type': 'streak',
+                        'period': 'all_time'
+                    },
+                    {
+                        'name': 'Level Leaderboard',
+                        'description': 'Highest levels',
+                        'leaderboard_type': 'xp',
+                        'period': 'all_time'
+                    }
+                ]
+                
+                created_count = 0
+                for leaderboard_data in default_leaderboards:
+                    result = LeaderboardManager.create_leaderboard(
+                        name=leaderboard_data['name'],
+                        description=leaderboard_data['description'],
+                        leaderboard_type=leaderboard_data['leaderboard_type'],
+                        period=leaderboard_data['period']
+                    )
+                    if result['success']:
+                        created_count += 1
+                
+                return {
+                    "success": True,
+                    "message": f"Created {created_count} default leaderboards"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error initializing leaderboards: {e}")
+            return {"success": False, "error": "Failed to initialize leaderboards"}
+    
+    @staticmethod
+    def update_all_leaderboards() -> Dict[str, Any]:
+        """Update all active leaderboards"""
+        try:
+            with app.app_context():
+                leaderboards = Leaderboard.query.filter(Leaderboard.is_active == True).all()
+                
+                updated_count = 0
+                for leaderboard in leaderboards:
+                    result = LeaderboardManager.update_leaderboard_scores(leaderboard.id)
+                    if result['success']:
+                        updated_count += 1
+                
+                return {
+                    "success": True,
+                    "message": f"Updated {updated_count} leaderboards"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error updating all leaderboards: {e}")
+            return {"success": False, "error": "Failed to update leaderboards"}
+    
+    @staticmethod
+    def get_leaderboard_list() -> Dict[str, Any]:
+        """Get list of all leaderboards"""
+        try:
+            with app.app_context():
+                leaderboards = Leaderboard.query.filter(Leaderboard.is_active == True).all()
+                
+                leaderboard_list = []
+                for leaderboard in leaderboards:
+                    leaderboard_list.append({
+                        'id': leaderboard.id,
+                        'name': leaderboard.name,
+                        'description': leaderboard.description,
+                        'type': leaderboard.leaderboard_type,
+                        'period': leaderboard.period,
+                        'created_at': leaderboard.created_at.isoformat()
+                    })
+                
+                return {
+                    "success": True,
+                    "leaderboards": leaderboard_list
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting leaderboard list: {e}")
+            return {"success": False, "error": "Failed to get leaderboard list"}
