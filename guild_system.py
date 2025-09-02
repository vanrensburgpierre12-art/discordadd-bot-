"""
Guild System Module
Handles guilds, teams, and group competitions
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, Guild, GuildMember, UserProfile
from user_profiles_system import UserProfileManager

logger = logging.getLogger(__name__)

class GuildManager:
    """Manages guilds and team features"""
    
    @staticmethod
    def create_guild(name: str, description: str, owner_id: str, icon_url: str = None) -> Dict[str, Any]:
        """Create a new guild"""
        try:
            with app.app_context():
                # Check if user exists and is active
                user = User.query.get(owner_id)
                if not user or user.user_status != 'active':
                    return {"success": False, "error": "User not found or not active"}
                
                # Check if guild name is already taken
                existing_guild = Guild.query.filter_by(name=name).first()
                if existing_guild:
                    return {"success": False, "error": "Guild name already taken"}
                
                # Check if user is already in a guild
                existing_membership = GuildMember.query.filter_by(user_id=owner_id).first()
                if existing_membership:
                    return {"success": False, "error": "You are already in a guild"}
                
                # Create guild
                guild = Guild(
                    name=name,
                    description=description,
                    owner_id=owner_id,
                    icon_url=icon_url,
                    member_count=1
                )
                
                db.session.add(guild)
                db.session.flush()  # Get the guild ID
                
                # Add owner as member
                owner_member = GuildMember(
                    guild_id=guild.id,
                    user_id=owner_id,
                    role='owner'
                )
                
                db.session.add(owner_member)
                db.session.commit()
                
                return {
                    "success": True,
                    "guild_id": guild.id,
                    "message": f"Guild '{name}' created successfully"
                }
                
        except Exception as e:
            logger.error(f"Error creating guild: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to create guild"}
    
    @staticmethod
    def join_guild(guild_id: int, user_id: str) -> Dict[str, Any]:
        """Join a guild"""
        try:
            with app.app_context():
                # Check if user exists and is active
                user = User.query.get(user_id)
                if not user or user.user_status != 'active':
                    return {"success": False, "error": "User not found or not active"}
                
                # Check if guild exists and is active
                guild = Guild.query.get(guild_id)
                if not guild or not guild.is_active:
                    return {"success": False, "error": "Guild not found or not active"}
                
                # Check if user is already in a guild
                existing_membership = GuildMember.query.filter_by(user_id=user_id).first()
                if existing_membership:
                    return {"success": False, "error": "You are already in a guild"}
                
                # Check if guild is full
                if guild.member_count >= guild.max_members:
                    return {"success": False, "error": "Guild is full"}
                
                # Add member
                member = GuildMember(
                    guild_id=guild_id,
                    user_id=user_id,
                    role='member'
                )
                
                db.session.add(member)
                
                # Update guild member count
                guild.member_count += 1
                
                # Award XP for joining guild
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                
                profile.xp += 50  # XP for joining guild
                
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Successfully joined guild '{guild.name}'",
                    "guild_name": guild.name,
                    "xp_gained": 50
                }
                
        except Exception as e:
            logger.error(f"Error joining guild: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to join guild"}
    
    @staticmethod
    def leave_guild(user_id: str) -> Dict[str, Any]:
        """Leave a guild"""
        try:
            with app.app_context():
                # Find user's membership
                membership = GuildMember.query.filter_by(user_id=user_id).first()
                if not membership:
                    return {"success": False, "error": "You are not in a guild"}
                
                guild = Guild.query.get(membership.guild_id)
                if not guild:
                    return {"success": False, "error": "Guild not found"}
                
                # Check if user is the owner
                if membership.role == 'owner':
                    # If owner is leaving, disband the guild or transfer ownership
                    if guild.member_count == 1:
                        # Disband guild if only owner
                        db.session.delete(guild)
                    else:
                        # Transfer ownership to another member
                        new_owner = GuildMember.query.filter(
                            GuildMember.guild_id == guild.id,
                            GuildMember.user_id != user_id
                        ).first()
                        
                        if new_owner:
                            new_owner.role = 'owner'
                            guild.owner_id = new_owner.user_id
                
                # Remove membership
                db.session.delete(membership)
                
                # Update guild member count
                guild.member_count -= 1
                
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Left guild '{guild.name}'",
                    "guild_name": guild.name
                }
                
        except Exception as e:
            logger.error(f"Error leaving guild: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to leave guild"}
    
    @staticmethod
    def get_guild_info(guild_id: int) -> Dict[str, Any]:
        """Get detailed guild information"""
        try:
            with app.app_context():
                guild = Guild.query.get(guild_id)
                if not guild:
                    return {"success": False, "error": "Guild not found"}
                
                # Get guild members
                members = GuildMember.query.filter_by(guild_id=guild_id).all()
                
                member_list = []
                for member in members:
                    user = User.query.get(member.user_id)
                    if user:
                        profile = UserProfile.query.filter_by(user_id=member.user_id).first()
                        
                        member_list.append({
                            'user_id': member.user_id,
                            'username': user.username,
                            'role': member.role,
                            'joined_at': member.joined_at.isoformat(),
                            'contributed_points': member.contributed_points,
                            'level': UserProfileManager._calculate_level_info(profile.xp)['level'] if profile else 1,
                            'xp': profile.xp if profile else 0
                        })
                
                # Sort members by role (owner first, then admins, then members)
                role_order = {'owner': 0, 'admin': 1, 'member': 2}
                member_list.sort(key=lambda x: (role_order.get(x['role'], 3), x['joined_at']))
                
                return {
                    "success": True,
                    "guild": {
                        'id': guild.id,
                        'name': guild.name,
                        'description': guild.description,
                        'icon_url': guild.icon_url,
                        'level': guild.level,
                        'xp': guild.xp,
                        'total_points': guild.total_points,
                        'member_count': guild.member_count,
                        'max_members': guild.max_members,
                        'owner_id': guild.owner_id,
                        'created_at': guild.created_at.isoformat(),
                        'members': member_list
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting guild info: {e}")
            return {"success": False, "error": "Failed to get guild info"}
    
    @staticmethod
    def get_user_guild(user_id: str) -> Dict[str, Any]:
        """Get user's guild information"""
        try:
            with app.app_context():
                membership = GuildMember.query.filter_by(user_id=user_id).first()
                if not membership:
                    return {
                        "success": True,
                        "guild": None,
                        "message": "User is not in a guild"
                    }
                
                guild = Guild.query.get(membership.guild_id)
                if not guild:
                    return {"success": False, "error": "Guild not found"}
                
                return {
                    "success": True,
                    "guild": {
                        'id': guild.id,
                        'name': guild.name,
                        'description': guild.description,
                        'icon_url': guild.icon_url,
                        'level': guild.level,
                        'xp': guild.xp,
                        'total_points': guild.total_points,
                        'member_count': guild.member_count,
                        'max_members': guild.max_members,
                        'user_role': membership.role,
                        'joined_at': membership.joined_at.isoformat(),
                        'contributed_points': membership.contributed_points
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting user guild: {e}")
            return {"success": False, "error": "Failed to get user guild"}
    
    @staticmethod
    def get_guild_leaderboard(limit: int = 10) -> Dict[str, Any]:
        """Get guild leaderboard"""
        try:
            with app.app_context():
                guilds = Guild.query.filter(
                    Guild.is_active == True
                ).order_by(
                    Guild.total_points.desc(),
                    Guild.xp.desc()
                ).limit(limit).all()
                
                leaderboard = []
                for i, guild in enumerate(guilds, 1):
                    leaderboard.append({
                        'rank': i,
                        'id': guild.id,
                        'name': guild.name,
                        'level': guild.level,
                        'xp': guild.xp,
                        'total_points': guild.total_points,
                        'member_count': guild.member_count,
                        'max_members': guild.max_members,
                        'created_at': guild.created_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "leaderboard": leaderboard
                }
                
        except Exception as e:
            logger.error(f"Error getting guild leaderboard: {e}")
            return {"success": False, "error": "Failed to get guild leaderboard"}
    
    @staticmethod
    def search_guilds(query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for guilds"""
        try:
            with app.app_context():
                guilds = Guild.query.filter(
                    Guild.name.ilike(f'%{query}%'),
                    Guild.is_active == True
                ).limit(limit).all()
                
                guild_list = []
                for guild in guilds:
                    guild_list.append({
                        'id': guild.id,
                        'name': guild.name,
                        'description': guild.description,
                        'icon_url': guild.icon_url,
                        'level': guild.level,
                        'member_count': guild.member_count,
                        'max_members': guild.max_members,
                        'total_points': guild.total_points,
                        'created_at': guild.created_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "guilds": guild_list,
                    "count": len(guild_list)
                }
                
        except Exception as e:
            logger.error(f"Error searching guilds: {e}")
            return {"success": False, "error": "Failed to search guilds"}
    
    @staticmethod
    def contribute_points(user_id: str, points: int) -> Dict[str, Any]:
        """Contribute points to guild"""
        try:
            with app.app_context():
                # Check if user is in a guild
                membership = GuildMember.query.filter_by(user_id=user_id).first()
                if not membership:
                    return {"success": False, "error": "You are not in a guild"}
                
                # Check if user has enough points
                user = User.query.get(user_id)
                if not user or user.points_balance < points:
                    return {"success": False, "error": "Insufficient points"}
                
                guild = Guild.query.get(membership.guild_id)
                if not guild:
                    return {"success": False, "error": "Guild not found"}
                
                # Deduct points from user
                user.points_balance -= points
                
                # Add points to guild
                guild.total_points += points
                guild.xp += points // 10  # Guild XP based on points contributed
                
                # Update member's contribution
                membership.contributed_points += points
                
                # Check for guild level up
                old_level = guild.level
                new_level = GuildManager._calculate_guild_level(guild.xp)
                guild.level = new_level
                
                level_up = new_level > old_level
                
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Contributed {points} points to {guild.name}",
                    "guild_name": guild.name,
                    "points_contributed": points,
                    "guild_total_points": guild.total_points,
                    "guild_level": guild.level,
                    "level_up": level_up,
                    "levels_gained": new_level - old_level if level_up else 0
                }
                
        except Exception as e:
            logger.error(f"Error contributing points: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to contribute points"}
    
    @staticmethod
    def _calculate_guild_level(xp: int) -> int:
        """Calculate guild level based on XP"""
        # Similar to user level calculation but with different scaling
        return int((xp / 1000) ** 0.5) + 1
    
    @staticmethod
    def promote_member(guild_id: int, user_id: str, promoter_id: str) -> Dict[str, Any]:
        """Promote a guild member to admin"""
        try:
            with app.app_context():
                # Check if promoter has permission
                promoter_membership = GuildMember.query.filter_by(
                    guild_id=guild_id,
                    user_id=promoter_id
                ).first()
                
                if not promoter_membership or promoter_membership.role not in ['owner', 'admin']:
                    return {"success": False, "error": "You don't have permission to promote members"}
                
                # Find member to promote
                member = GuildMember.query.filter_by(
                    guild_id=guild_id,
                    user_id=user_id
                ).first()
                
                if not member:
                    return {"success": False, "error": "Member not found"}
                
                if member.role == 'owner':
                    return {"success": False, "error": "Cannot promote the owner"}
                
                if member.role == 'admin':
                    return {"success": False, "error": "Member is already an admin"}
                
                # Promote member
                member.role = 'admin'
                db.session.commit()
                
                user = User.query.get(user_id)
                
                return {
                    "success": True,
                    "message": f"Promoted {user.username} to admin",
                    "username": user.username
                }
                
        except Exception as e:
            logger.error(f"Error promoting member: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to promote member"}
    
    @staticmethod
    def demote_member(guild_id: int, user_id: str, demoter_id: str) -> Dict[str, Any]:
        """Demote a guild admin to member"""
        try:
            with app.app_context():
                # Check if demoter has permission (only owner can demote)
                demoter_membership = GuildMember.query.filter_by(
                    guild_id=guild_id,
                    user_id=demoter_id
                ).first()
                
                if not demoter_membership or demoter_membership.role != 'owner':
                    return {"success": False, "error": "Only the owner can demote members"}
                
                # Find member to demote
                member = GuildMember.query.filter_by(
                    guild_id=guild_id,
                    user_id=user_id
                ).first()
                
                if not member:
                    return {"success": False, "error": "Member not found"}
                
                if member.role == 'owner':
                    return {"success": False, "error": "Cannot demote the owner"}
                
                if member.role == 'member':
                    return {"success": False, "error": "Member is already a regular member"}
                
                # Demote member
                member.role = 'member'
                db.session.commit()
                
                user = User.query.get(user_id)
                
                return {
                    "success": True,
                    "message": f"Demoted {user.username} to member",
                    "username": user.username
                }
                
        except Exception as e:
            logger.error(f"Error demoting member: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to demote member"}