diff --git a/admin_manager.py b/admin_manager.py
--- a/admin_manager.py
+++ b/admin_manager.py
@@ -1,11 +1,250 @@
-from datetime import datetime
-from typing import Dict, Any, List, Optional
-from app_context import app, db
-from database import AdminUser, TransactionApproval, WalletTransaction, DiscordTransaction, Server, User
-from config import Config
-
-logger = logging.getLogger(__name__)
-        except Exception as e:
-            logger.error(f"Error registering server: {e}")
-            db.session.rollback()
-            return {"success": False, "error": "Failed to register server"}
+from datetime import datetime
+from typing import Dict, Any, List, Optional
+from app_context import app, db
+from database import AdminUser, TransactionApproval, WalletTransaction, DiscordTransaction, Server, User, CasinoGame, AdCompletion
+from config import Config
+
+logger = logging.getLogger(__name__)
+        except Exception as e:
+            logger.error(f"Error registering server: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to register server"}
+    
+    @staticmethod
+    def get_users(page: int = 1, per_page: int = 50, status: str = None, search: str = None) -> Dict[str, Any]:
+        """Get paginated list of users with optional filtering"""
+        try:
+            query = User.query
+            
+            # Filter by status if provided
+            if status:
+                query = query.filter(User.user_status == status)
+            
+            # Search by username if provided
+            if search:
+                query = query.filter(User.username.ilike(f'%{search}%'))
+            
+            # Order by last activity (most recent first)
+            query = query.order_by(User.last_activity.desc())
+            
+            # Paginate results
+            pagination = query.paginate(
+                page=page, 
+                per_page=per_page, 
+                error_out=False
+            )
+            
+            users = []
+            for user in pagination.items:
+                users.append({
+                    'id': user.id,
+                    'username': user.username,
+                    'points_balance': user.points_balance,
+                    'total_earned': user.total_earned,
+                    'user_status': user.user_status,
+                    'created_at': user.created_at.isoformat(),
+                    'last_activity': user.last_activity.isoformat(),
+                    'total_games_played': user.total_games_played,
+                    'total_gift_cards_redeemed': user.total_gift_cards_redeemed
+                })
+            
+            return {
+                "success": True,
+                "users": users,
+                "pagination": {
+                    "page": page,
+                    "per_page": per_page,
+                    "total": pagination.total,
+                    "pages": pagination.pages,
+                    "has_next": pagination.has_next,
+                    "has_prev": pagination.has_prev
+                }
+            }
+            
+        except Exception as e:
+            logger.error(f"Error getting users: {e}")
+            return {"success": False, "error": "Failed to get users"}
+    
+    @staticmethod
+    def get_user_details(user_id: str) -> Dict[str, Any]:
+        """Get detailed information about a specific user"""
+        try:
+            user = User.query.filter_by(id=user_id).first()
+            if not user:
+                return {"success": False, "error": "User not found"}
+            
+            # Get user's recent activity
+            recent_games = CasinoGame.query.filter_by(user_id=user_id).order_by(CasinoGame.played_at.desc()).limit(10).all()
+            recent_ads = AdCompletion.query.filter_by(user_id=user_id).order_by(AdCompletion.completed_at.desc()).limit(10).all()
+            
+            user_data = {
+                'id': user.id,
+                'username': user.username,
+                'points_balance': user.points_balance,
+                'total_earned': user.total_earned,
+                'user_status': user.user_status,
+                'ban_reason': user.ban_reason,
+                'banned_at': user.banned_at.isoformat() if user.banned_at else None,
+                'banned_by': user.banned_by,
+                'created_at': user.created_at.isoformat(),
+                'last_activity': user.last_activity.isoformat(),
+                'last_earn_time': user.last_earn_time.isoformat() if user.last_earn_time else None,
+                'total_games_played': user.total_games_played,
+                'total_gift_cards_redeemed': user.total_gift_cards_redeemed,
+                'recent_games': [
+                    {
+                        'game_type': game.game_type,
+                        'bet_amount': game.bet_amount,
+                        'win_amount': game.win_amount,
+                        'result': game.result,
+                        'played_at': game.played_at.isoformat()
+                    } for game in recent_games
+                ],
+                'recent_ads': [
+                    {
+                        'offer_id': ad.offer_id,
+                        'points_earned': ad.points_earned,
+                        'completed_at': ad.completed_at.isoformat()
+                    } for ad in recent_ads
+                ]
+            }
+            
+            return {"success": True, "user": user_data}
+            
+        except Exception as e:
+            logger.error(f"Error getting user details: {e}")
+            return {"success": False, "error": "Failed to get user details"}
+    
+    @staticmethod
+    def ban_user(user_id: str, reason: str, admin_user_id: str) -> Dict[str, Any]:
+        """Ban a user"""
+        try:
+            user = User.query.filter_by(id=user_id).first()
+            if not user:
+                return {"success": False, "error": "User not found"}
+            
+            if user.user_status == 'banned':
+                return {"success": False, "error": "User is already banned"}
+            
+            user.user_status = 'banned'
+            user.ban_reason = reason
+            user.banned_at = datetime.utcnow()
+            user.banned_by = admin_user_id
+            
+            db.session.commit()
+            
+            return {
+                "success": True,
+                "message": f"User {user.username} has been banned",
+                "user_id": user_id,
+                "reason": reason
+            }
+            
+        except Exception as e:
+            logger.error(f"Error banning user: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to ban user"}
+    
+    @staticmethod
+    def unban_user(user_id: str, admin_user_id: str) -> Dict[str, Any]:
+        """Unban a user"""
+        try:
+            user = User.query.filter_by(id=user_id).first()
+            if not user:
+                return {"success": False, "error": "User not found"}
+            
+            if user.user_status != 'banned':
+                return {"success": False, "error": "User is not banned"}
+            
+            user.user_status = 'active'
+            user.ban_reason = None
+            user.banned_at = None
+            user.banned_by = None
+            
+            db.session.commit()
+            
+            return {
+                "success": True,
+                "message": f"User {user.username} has been unbanned",
+                "user_id": user_id
+            }
+            
+        except Exception as e:
+            logger.error(f"Error unbanning user: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to unban user"}
+    
+    @staticmethod
+    def adjust_user_points(user_id: str, points_change: int, admin_user_id: str, reason: str = None) -> Dict[str, Any]:
+        """Adjust a user's points balance"""
+        try:
+            user = User.query.filter_by(id=user_id).first()
+            if not user:
+                return {"success": False, "error": "User not found"}
+            
+            old_balance = user.points_balance
+            new_balance = old_balance + points_change
+            
+            # Prevent negative balance
+            if new_balance < 0:
+                return {"success": False, "error": "Cannot set points balance below zero"}
+            
+            user.points_balance = new_balance
+            
+            # Update total earned if adding points
+            if points_change > 0:
+                user.total_earned += points_change
+            
+            db.session.commit()
+            
+            return {
+                "success": True,
+                "message": f"Points adjusted for {user.username}",
+                "user_id": user_id,
+                "old_balance": old_balance,
+                "new_balance": new_balance,
+                "points_change": points_change,
+                "reason": reason
+            }
+            
+        except Exception as e:
+            logger.error(f"Error adjusting user points: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to adjust user points"}
+    
+    @staticmethod
+    def search_users(query: str, limit: int = 20) -> Dict[str, Any]:
+        """Search for users by username or ID"""
+        try:
+            # Search by username (case insensitive)
+            users_by_username = User.query.filter(User.username.ilike(f'%{query}%')).limit(limit).all()
+            
+            # Search by exact ID match
+            user_by_id = User.query.filter_by(id=query).first()
+            
+            # Combine results, avoiding duplicates
+            all_users = list(users_by_username)
+            if user_by_id and user_by_id not in all_users:
+                all_users.insert(0, user_by_id)  # Put exact ID match first
+            
+            users = []
+            for user in all_users[:limit]:
+                users.append({
+                    'id': user.id,
+                    'username': user.username,
+                    'points_balance': user.points_balance,
+                    'user_status': user.user_status,
+                    'created_at': user.created_at.isoformat(),
+                    'last_activity': user.last_activity.isoformat()
+                })
+            
+            return {
+                "success": True,
+                "users": users,
+                "query": query,
+                "count": len(users)
+            }
+            
+        except Exception as e:
+            logger.error(f"Error searching users: {e}")
+            return {"success": False, "error": "Failed to search users"}
