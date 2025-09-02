diff --git a/friend_system.py b/friend_system.py
--- a/friend_system.py
+++ b/friend_system.py
@@ -0,0 +1,479 @@
+"""
+Friend System Module
+Handles friend requests, friendships, and social features
+"""
+
+import logging
+from datetime import datetime
+from typing import Dict, Any, List, Optional
+from app_context import app, db
+from database import User, Friend, UserProfile
+from user_profiles_system import UserProfileManager
+
+logger = logging.getLogger(__name__)
+
+class FriendManager:
+    """Manages friend system and social features"""
+    
+    @staticmethod
+    def send_friend_request(user_id: str, friend_id: str) -> Dict[str, Any]:
+        """Send a friend request"""
+        try:
+            with app.app_context():
+                # Check if users exist
+                user = User.query.get(user_id)
+                friend = User.query.get(friend_id)
+                
+                if not user or not friend:
+                    return {"success": False, "error": "User not found"}
+                
+                if user.user_status != 'active' or friend.user_status != 'active':
+                    return {"success": False, "error": "User account is not active"}
+                
+                # Check if trying to friend themselves
+                if user_id == friend_id:
+                    return {"success": False, "error": "You cannot send a friend request to yourself"}
+                
+                # Check if friendship already exists
+                existing_friendship = Friend.query.filter(
+                    ((Friend.user_id == user_id) & (Friend.friend_id == friend_id)) |
+                    ((Friend.user_id == friend_id) & (Friend.friend_id == user_id))
+                ).first()
+                
+                if existing_friendship:
+                    if existing_friendship.status == 'accepted':
+                        return {"success": False, "error": "You are already friends"}
+                    elif existing_friendship.status == 'pending':
+                        if existing_friendship.user_id == user_id:
+                            return {"success": False, "error": "Friend request already sent"}
+                        else:
+                            return {"success": False, "error": "This user has already sent you a friend request"}
+                    elif existing_friendship.status == 'blocked':
+                        return {"success": False, "error": "This user is blocked"}
+                
+                # Create friend request
+                friendship = Friend(
+                    user_id=user_id,
+                    friend_id=friend_id,
+                    status='pending'
+                )
+                
+                db.session.add(friendship)
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "message": f"Friend request sent to {friend.username}",
+                    "friend_username": friend.username
+                }
+                
+        except Exception as e:
+            logger.error(f"Error sending friend request: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to send friend request"}
+    
+    @staticmethod
+    def accept_friend_request(user_id: str, friend_id: str) -> Dict[str, Any]:
+        """Accept a friend request"""
+        try:
+            with app.app_context():
+                # Find the friend request
+                friendship = Friend.query.filter(
+                    Friend.user_id == friend_id,
+                    Friend.friend_id == user_id,
+                    Friend.status == 'pending'
+                ).first()
+                
+                if not friendship:
+                    return {"success": False, "error": "No pending friend request found"}
+                
+                # Accept the request
+                friendship.status = 'accepted'
+                friendship.accepted_at = datetime.utcnow()
+                
+                # Award XP for making friends
+                user_profile = UserProfile.query.filter_by(user_id=user_id).first()
+                if not user_profile:
+                    user_profile = UserProfile(user_id=user_id)
+                    db.session.add(user_profile)
+                
+                friend_profile = UserProfile.query.filter_by(user_id=friend_id).first()
+                if not friend_profile:
+                    friend_profile = UserProfile(user_id=friend_id)
+                    db.session.add(friend_profile)
+                
+                # Award XP to both users
+                user_profile.xp += 25
+                friend_profile.xp += 25
+                
+                db.session.commit()
+                
+                # Get friend's username
+                friend = User.query.get(friend_id)
+                
+                return {
+                    "success": True,
+                    "message": f"You are now friends with {friend.username}!",
+                    "friend_username": friend.username,
+                    "xp_gained": 25
+                }
+                
+        except Exception as e:
+            logger.error(f"Error accepting friend request: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to accept friend request"}
+    
+    @staticmethod
+    def decline_friend_request(user_id: str, friend_id: str) -> Dict[str, Any]:
+        """Decline a friend request"""
+        try:
+            with app.app_context():
+                # Find the friend request
+                friendship = Friend.query.filter(
+                    Friend.user_id == friend_id,
+                    Friend.friend_id == user_id,
+                    Friend.status == 'pending'
+                ).first()
+                
+                if not friendship:
+                    return {"success": False, "error": "No pending friend request found"}
+                
+                # Remove the request
+                db.session.delete(friendship)
+                db.session.commit()
+                
+                # Get friend's username
+                friend = User.query.get(friend_id)
+                
+                return {
+                    "success": True,
+                    "message": f"Friend request from {friend.username} declined",
+                    "friend_username": friend.username
+                }
+                
+        except Exception as e:
+            logger.error(f"Error declining friend request: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to decline friend request"}
+    
+    @staticmethod
+    def remove_friend(user_id: str, friend_id: str) -> Dict[str, Any]:
+        """Remove a friend"""
+        try:
+            with app.app_context():
+                # Find the friendship
+                friendship = Friend.query.filter(
+                    ((Friend.user_id == user_id) & (Friend.friend_id == friend_id)) |
+                    ((Friend.user_id == friend_id) & (Friend.friend_id == user_id)),
+                    Friend.status == 'accepted'
+                ).first()
+                
+                if not friendship:
+                    return {"success": False, "error": "Friendship not found"}
+                
+                # Remove the friendship
+                db.session.delete(friendship)
+                db.session.commit()
+                
+                # Get friend's username
+                friend = User.query.get(friend_id)
+                
+                return {
+                    "success": True,
+                    "message": f"Removed {friend.username} from friends",
+                    "friend_username": friend.username
+                }
+                
+        except Exception as e:
+            logger.error(f"Error removing friend: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to remove friend"}
+    
+    @staticmethod
+    def block_user(user_id: str, friend_id: str) -> Dict[str, Any]:
+        """Block a user"""
+        try:
+            with app.app_context():
+                # Check if users exist
+                user = User.query.get(user_id)
+                friend = User.query.get(friend_id)
+                
+                if not user or not friend:
+                    return {"success": False, "error": "User not found"}
+                
+                if user_id == friend_id:
+                    return {"success": False, "error": "You cannot block yourself"}
+                
+                # Remove any existing friendship
+                existing_friendship = Friend.query.filter(
+                    ((Friend.user_id == user_id) & (Friend.friend_id == friend_id)) |
+                    ((Friend.user_id == friend_id) & (Friend.friend_id == user_id))
+                ).first()
+                
+                if existing_friendship:
+                    db.session.delete(existing_friendship)
+                
+                # Create block relationship
+                block = Friend(
+                    user_id=user_id,
+                    friend_id=friend_id,
+                    status='blocked'
+                )
+                
+                db.session.add(block)
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "message": f"Blocked {friend.username}",
+                    "friend_username": friend.username
+                }
+                
+        except Exception as e:
+            logger.error(f"Error blocking user: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to block user"}
+    
+    @staticmethod
+    def unblock_user(user_id: str, friend_id: str) -> Dict[str, Any]:
+        """Unblock a user"""
+        try:
+            with app.app_context():
+                # Find the block
+                block = Friend.query.filter(
+                    Friend.user_id == user_id,
+                    Friend.friend_id == friend_id,
+                    Friend.status == 'blocked'
+                ).first()
+                
+                if not block:
+                    return {"success": False, "error": "User is not blocked"}
+                
+                # Remove the block
+                db.session.delete(block)
+                db.session.commit()
+                
+                # Get friend's username
+                friend = User.query.get(friend_id)
+                
+                return {
+                    "success": True,
+                    "message": f"Unblocked {friend.username}",
+                    "friend_username": friend.username
+                }
+                
+        except Exception as e:
+            logger.error(f"Error unblocking user: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to unblock user"}
+    
+    @staticmethod
+    def get_friends(user_id: str) -> Dict[str, Any]:
+        """Get user's friends list"""
+        try:
+            with app.app_context():
+                # Get accepted friendships
+                friendships = Friend.query.filter(
+                    ((Friend.user_id == user_id) | (Friend.friend_id == user_id)),
+                    Friend.status == 'accepted'
+                ).all()
+                
+                friends = []
+                for friendship in friendships:
+                    # Determine which user is the friend
+                    friend_user_id = friendship.friend_id if friendship.user_id == user_id else friendship.user_id
+                    friend = User.query.get(friend_user_id)
+                    
+                    if friend:
+                        # Get friend's profile
+                        profile = UserProfile.query.filter_by(user_id=friend_user_id).first()
+                        
+                        friends.append({
+                            'user_id': friend_user_id,
+                            'username': friend.username,
+                            'level': UserProfileManager._calculate_level_info(profile.xp)['level'] if profile else 1,
+                            'xp': profile.xp if profile else 0,
+                            'favorite_game': profile.favorite_game if profile else None,
+                            'friends_since': friendship.accepted_at.isoformat() if friendship.accepted_at else None
+                        })
+                
+                # Sort by friends since date (newest first)
+                friends.sort(key=lambda x: x['friends_since'] or '', reverse=True)
+                
+                return {
+                    "success": True,
+                    "friends": friends,
+                    "count": len(friends)
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting friends: {e}")
+            return {"success": False, "error": "Failed to get friends"}
+    
+    @staticmethod
+    def get_pending_requests(user_id: str) -> Dict[str, Any]:
+        """Get pending friend requests"""
+        try:
+            with app.app_context():
+                # Get incoming requests
+                incoming_requests = Friend.query.filter(
+                    Friend.friend_id == user_id,
+                    Friend.status == 'pending'
+                ).all()
+                
+                # Get outgoing requests
+                outgoing_requests = Friend.query.filter(
+                    Friend.user_id == user_id,
+                    Friend.status == 'pending'
+                ).all()
+                
+                incoming = []
+                for request in incoming_requests:
+                    user = User.query.get(request.user_id)
+                    if user:
+                        profile = UserProfile.query.filter_by(user_id=request.user_id).first()
+                        
+                        incoming.append({
+                            'user_id': request.user_id,
+                            'username': user.username,
+                            'level': UserProfileManager._calculate_level_info(profile.xp)['level'] if profile else 1,
+                            'requested_at': request.created_at.isoformat()
+                        })
+                
+                outgoing = []
+                for request in outgoing_requests:
+                    user = User.query.get(request.friend_id)
+                    if user:
+                        profile = UserProfile.query.filter_by(user_id=request.friend_id).first()
+                        
+                        outgoing.append({
+                            'user_id': request.friend_id,
+                            'username': user.username,
+                            'level': UserProfileManager._calculate_level_info(profile.xp)['level'] if profile else 1,
+                            'requested_at': request.created_at.isoformat()
+                        })
+                
+                return {
+                    "success": True,
+                    "incoming_requests": incoming,
+                    "outgoing_requests": outgoing,
+                    "incoming_count": len(incoming),
+                    "outgoing_count": len(outgoing)
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting pending requests: {e}")
+            return {"success": False, "error": "Failed to get pending requests"}
+    
+    @staticmethod
+    def get_blocked_users(user_id: str) -> Dict[str, Any]:
+        """Get user's blocked users list"""
+        try:
+            with app.app_context():
+                blocked_users = Friend.query.filter(
+                    Friend.user_id == user_id,
+                    Friend.status == 'blocked'
+                ).all()
+                
+                blocked = []
+                for block in blocked_users:
+                    user = User.query.get(block.friend_id)
+                    if user:
+                        blocked.append({
+                            'user_id': block.friend_id,
+                            'username': user.username,
+                            'blocked_at': block.created_at.isoformat()
+                        })
+                
+                return {
+                    "success": True,
+                    "blocked_users": blocked,
+                    "count": len(blocked)
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting blocked users: {e}")
+            return {"success": False, "error": "Failed to get blocked users"}
+    
+    @staticmethod
+    def search_users(query: str, limit: int = 20) -> Dict[str, Any]:
+        """Search for users to add as friends"""
+        try:
+            with app.app_context():
+                users = User.query.filter(
+                    User.username.ilike(f'%{query}%'),
+                    User.user_status == 'active'
+                ).limit(limit).all()
+                
+                user_list = []
+                for user in users:
+                    profile = UserProfile.query.filter_by(user_id=user.id).first()
+                    
+                    user_list.append({
+                        'user_id': user.id,
+                        'username': user.username,
+                        'level': UserProfileManager._calculate_level_info(profile.xp)['level'] if profile else 1,
+                        'xp': profile.xp if profile else 0,
+                        'favorite_game': profile.favorite_game if profile else None,
+                        'created_at': user.created_at.isoformat()
+                    })
+                
+                return {
+                    "success": True,
+                    "users": user_list,
+                    "count": len(user_list)
+                }
+                
+        except Exception as e:
+            logger.error(f"Error searching users: {e}")
+            return {"success": False, "error": "Failed to search users"}
+    
+    @staticmethod
+    def get_friend_activity(user_id: str, limit: int = 20) -> Dict[str, Any]:
+        """Get recent activity from friends"""
+        try:
+            with app.app_context():
+                # Get user's friends
+                friends_result = FriendManager.get_friends(user_id)
+                if not friends_result['success']:
+                    return friends_result
+                
+                friend_ids = [friend['user_id'] for friend in friends_result['friends']]
+                
+                if not friend_ids:
+                    return {
+                        "success": True,
+                        "activity": [],
+                        "count": 0
+                    }
+                
+                # Get recent casino games from friends
+                from database import CasinoGame
+                recent_games = CasinoGame.query.filter(
+                    CasinoGame.user_id.in_(friend_ids)
+                ).order_by(CasinoGame.played_at.desc()).limit(limit).all()
+                
+                activity = []
+                for game in recent_games:
+                    user = User.query.get(game.user_id)
+                    if user:
+                        activity.append({
+                            'type': 'casino_game',
+                            'user_id': game.user_id,
+                            'username': user.username,
+                            'game_type': game.game_type,
+                            'bet_amount': game.bet_amount,
+                            'win_amount': game.win_amount,
+                            'result': 'win' if game.win_amount > 0 else 'lose',
+                            'timestamp': game.played_at.isoformat()
+                        })
+                
+                return {
+                    "success": True,
+                    "activity": activity,
+                    "count": len(activity)
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting friend activity: {e}")
+            return {"success": False, "error": "Failed to get friend activity"}
