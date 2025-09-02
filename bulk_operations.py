"""
Bulk Operations System Module
Handles bulk user operations, mass actions, and batch processing
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, UserProfile, CasinoGame, AdCompletion, GiftCard, Referral, DailyBonus

logger = logging.getLogger(__name__)

class BulkOperationsManager:
    """Manages bulk operations and mass actions"""
    
    @staticmethod
    def bulk_update_user_status(user_ids: List[str], new_status: str, reason: str = None) -> Dict[str, Any]:
        """Bulk update user status"""
        try:
            with app.app_context():
                if new_status not in ['active', 'banned', 'suspended']:
                    return {"success": False, "error": "Invalid status"}
                
                updated_count = 0
                failed_updates = []
                
                for user_id in user_ids:
                    try:
                        user = User.query.get(user_id)
                        if user:
                            old_status = user.user_status
                            user.user_status = new_status
                            
                            if new_status == 'banned':
                                user.ban_reason = reason or 'Bulk operation'
                                user.banned_at = datetime.utcnow()
                                user.banned_by = 'admin'
                            elif new_status == 'active':
                                user.ban_reason = None
                                user.banned_at = None
                                user.banned_by = None
                            
                            updated_count += 1
                        else:
                            failed_updates.append({
                                'user_id': user_id,
                                'error': 'User not found'
                            })
                    except Exception as e:
                        failed_updates.append({
                            'user_id': user_id,
                            'error': str(e)
                        })
                
                db.session.commit()
                
                return {
                    "success": True,
                    "updated_count": updated_count,
                    "failed_count": len(failed_updates),
                    "failed_updates": failed_updates,
                    "message": f"Updated {updated_count} users to {new_status}"
                }
                
        except Exception as e:
            logger.error(f"Error in bulk update user status: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to bulk update user status"}
    
    @staticmethod
    def bulk_adjust_points(user_ids: List[str], points_change: int, reason: str = None) -> Dict[str, Any]:
        """Bulk adjust user points"""
        try:
            with app.app_context():
                updated_count = 0
                failed_updates = []
                total_points_adjusted = 0
                
                for user_id in user_ids:
                    try:
                        user = User.query.get(user_id)
                        if user:
                            old_balance = user.points_balance
                            new_balance = old_balance + points_change
                            
                            # Prevent negative balance
                            if new_balance < 0:
                                failed_updates.append({
                                    'user_id': user_id,
                                    'error': 'Would result in negative balance'
                                })
                                continue
                            
                            user.points_balance = new_balance
                            
                            if points_change > 0:
                                user.total_earned += points_change
                            
                            updated_count += 1
                            total_points_adjusted += points_change
                        else:
                            failed_updates.append({
                                'user_id': user_id,
                                'error': 'User not found'
                            })
                    except Exception as e:
                        failed_updates.append({
                            'user_id': user_id,
                            'error': str(e)
                        })
                
                db.session.commit()
                
                return {
                    "success": True,
                    "updated_count": updated_count,
                    "failed_count": len(failed_updates),
                    "total_points_adjusted": total_points_adjusted,
                    "failed_updates": failed_updates,
                    "message": f"Adjusted points for {updated_count} users"
                }
                
        except Exception as e:
            logger.error(f"Error in bulk adjust points: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to bulk adjust points"}
    
    @staticmethod
    def bulk_reset_user_data(user_ids: List[str], reset_type: str = 'all') -> Dict[str, Any]:
        """Bulk reset user data"""
        try:
            with app.app_context():
                if reset_type not in ['all', 'points', 'stats', 'profile']:
                    return {"success": False, "error": "Invalid reset type"}
                
                updated_count = 0
                failed_updates = []
                
                for user_id in user_ids:
                    try:
                        user = User.query.get(user_id)
                        if not user:
                            failed_updates.append({
                                'user_id': user_id,
                                'error': 'User not found'
                            })
                            continue
                        
                        if reset_type in ['all', 'points']:
                            user.points_balance = 0
                            user.total_earned = 0
                        
                        if reset_type in ['all', 'stats']:
                            # Reset casino game stats
                            CasinoGame.query.filter_by(user_id=user_id).delete()
                            
                            # Reset ad completion stats
                            AdCompletion.query.filter_by(user_id=user_id).delete()
                        
                        if reset_type in ['all', 'profile']:
                            # Reset user profile
                            profile = UserProfile.query.filter_by(user_id=user_id).first()
                            if profile:
                                profile.xp = 0
                                profile.total_wins = 0
                                profile.total_losses = 0
                                profile.win_streak = 0
                                profile.best_win_streak = 0
                                profile.favorite_game = None
                        
                        updated_count += 1
                    except Exception as e:
                        failed_updates.append({
                            'user_id': user_id,
                            'error': str(e)
                        })
                
                db.session.commit()
                
                return {
                    "success": True,
                    "updated_count": updated_count,
                    "failed_count": len(failed_updates),
                    "reset_type": reset_type,
                    "failed_updates": failed_updates,
                    "message": f"Reset {reset_type} data for {updated_count} users"
                }
                
        except Exception as e:
            logger.error(f"Error in bulk reset user data: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to bulk reset user data"}
    
    @staticmethod
    def bulk_create_gift_cards(category_id: int, amounts: List[int], count_per_amount: int = 1) -> Dict[str, Any]:
        """Bulk create gift cards"""
        try:
            with app.app_context():
                created_count = 0
                gift_cards = []
                
                for amount in amounts:
                    for _ in range(count_per_amount):
                        # Generate unique code
                        import uuid
                        code = f"BULK_{uuid.uuid4().hex[:8].upper()}"
                        
                        gift_card = GiftCard(
                            code=code,
                            amount=amount,
                            category_id=category_id
                        )
                        
                        db.session.add(gift_card)
                        gift_cards.append({
                            'code': code,
                            'amount': amount,
                            'category_id': category_id
                        })
                        created_count += 1
                
                db.session.commit()
                
                return {
                    "success": True,
                    "created_count": created_count,
                    "gift_cards": gift_cards,
                    "message": f"Created {created_count} gift cards"
                }
                
        except Exception as e:
            logger.error(f"Error in bulk create gift cards: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to bulk create gift cards"}
    
    @staticmethod
    def bulk_cleanup_inactive_users(days_inactive: int = 30) -> Dict[str, Any]:
        """Bulk cleanup inactive users"""
        try:
            with app.app_context():
                cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
                
                # Find inactive users
                inactive_users = User.query.filter(
                    User.last_activity < cutoff_date,
                    User.user_status == 'active',
                    User.points_balance == 0,
                    User.total_earned == 0
                ).all()
                
                user_ids = [user.id for user in inactive_users]
                
                if not user_ids:
                    return {
                        "success": True,
                        "message": "No inactive users found for cleanup",
                        "cleanup_count": 0
                    }
                
                # Delete user data
                deleted_count = 0
                for user_id in user_ids:
                    try:
                        # Delete related data
                        CasinoGame.query.filter_by(user_id=user_id).delete()
                        AdCompletion.query.filter_by(user_id=user_id).delete()
                        UserProfile.query.filter_by(user_id=user_id).delete()
                        Referral.query.filter_by(referrer_id=user_id).delete()
                        Referral.query.filter_by(referred_id=user_id).delete()
                        DailyBonus.query.filter_by(user_id=user_id).delete()
                        
                        # Delete user
                        User.query.filter_by(id=user_id).delete()
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting user {user_id}: {e}")
                
                db.session.commit()
                
                return {
                    "success": True,
                    "cleanup_count": deleted_count,
                    "days_inactive": days_inactive,
                    "message": f"Cleaned up {deleted_count} inactive users"
                }
                
        except Exception as e:
            logger.error(f"Error in bulk cleanup inactive users: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to bulk cleanup inactive users"}
    
    @staticmethod
    def bulk_export_user_data(user_ids: List[str]) -> Dict[str, Any]:
        """Bulk export user data"""
        try:
            with app.app_context():
                exported_users = []
                
                for user_id in user_ids:
                    user = User.query.get(user_id)
                    if not user:
                        continue
                    
                    # Get user profile
                    profile = UserProfile.query.filter_by(user_id=user_id).first()
                    
                    # Get user statistics
                    total_games = CasinoGame.query.filter_by(user_id=user_id).count()
                    total_wins = CasinoGame.query.filter(
                        CasinoGame.user_id == user_id,
                        CasinoGame.win_amount > 0
                    ).count()
                    
                    total_ads = AdCompletion.query.filter_by(user_id=user_id).count()
                    total_ad_points = db.session.query(db.func.sum(AdCompletion.points_earned)).filter_by(user_id=user_id).scalar() or 0
                    
                    # Get referral data
                    referrals_made = Referral.query.filter_by(referrer_id=user_id).count()
                    was_referred = Referral.query.filter_by(referred_id=user_id).first() is not None
                    
                    user_data = {
                        'user_id': user.id,
                        'username': user.username,
                        'user_status': user.user_status,
                        'points_balance': user.points_balance,
                        'total_earned': user.total_earned,
                        'created_at': user.created_at.isoformat(),
                        'last_activity': user.last_activity.isoformat(),
                        'profile': {
                            'level': profile.level if profile else 1,
                            'xp': profile.xp if profile else 0,
                            'total_wins': profile.total_wins if profile else 0,
                            'total_losses': profile.total_losses if profile else 0,
                            'win_streak': profile.win_streak if profile else 0,
                            'best_win_streak': profile.best_win_streak if profile else 0,
                            'favorite_game': profile.favorite_game
                        } if profile else None,
                        'statistics': {
                            'total_games': total_games,
                            'total_wins': total_wins,
                            'win_rate': (total_wins / total_games * 100) if total_games > 0 else 0,
                            'total_ads': total_ads,
                            'total_ad_points': total_ad_points,
                            'referrals_made': referrals_made,
                            'was_referred': was_referred
                        }
                    }
                    
                    exported_users.append(user_data)
                
                return {
                    "success": True,
                    "exported_count": len(exported_users),
                    "users": exported_users,
                    "export_timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in bulk export user data: {e}")
            return {"success": False, "error": "Failed to bulk export user data"}
    
    @staticmethod
    def bulk_import_users(user_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk import users"""
        try:
            with app.app_context():
                imported_count = 0
                failed_imports = []
                
                for user_info in user_data:
                    try:
                        user_id = user_info.get('user_id')
                        username = user_info.get('username')
                        
                        if not user_id or not username:
                            failed_imports.append({
                                'data': user_info,
                                'error': 'Missing user_id or username'
                            })
                            continue
                        
                        # Check if user already exists
                        existing_user = User.query.get(user_id)
                        if existing_user:
                            failed_imports.append({
                                'user_id': user_id,
                                'error': 'User already exists'
                            })
                            continue
                        
                        # Create user
                        user = User(
                            id=user_id,
                            username=username,
                            points_balance=user_info.get('points_balance', 0),
                            total_earned=user_info.get('total_earned', 0),
                            user_status=user_info.get('user_status', 'active')
                        )
                        
                        db.session.add(user)
                        
                        # Create profile if data provided
                        profile_data = user_info.get('profile')
                        if profile_data:
                            profile = UserProfile(
                                user_id=user_id,
                                level=profile_data.get('level', 1),
                                xp=profile_data.get('xp', 0),
                                total_wins=profile_data.get('total_wins', 0),
                                total_losses=profile_data.get('total_losses', 0),
                                win_streak=profile_data.get('win_streak', 0),
                                best_win_streak=profile_data.get('best_win_streak', 0),
                                favorite_game=profile_data.get('favorite_game')
                            )
                            db.session.add(profile)
                        
                        imported_count += 1
                    except Exception as e:
                        failed_imports.append({
                            'data': user_info,
                            'error': str(e)
                        })
                
                db.session.commit()
                
                return {
                    "success": True,
                    "imported_count": imported_count,
                    "failed_count": len(failed_imports),
                    "failed_imports": failed_imports,
                    "message": f"Imported {imported_count} users"
                }
                
        except Exception as e:
            logger.error(f"Error in bulk import users: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to bulk import users"}
    
    @staticmethod
    def get_bulk_operation_status() -> Dict[str, Any]:
        """Get status of bulk operations"""
        try:
            with app.app_context():
                # Get counts for bulk operations
                total_users = User.query.count()
                active_users = User.query.filter(User.user_status == 'active').count()
                banned_users = User.query.filter(User.user_status == 'banned').count()
                suspended_users = User.query.filter(User.user_status == 'suspended').count()
                
                # Get inactive users count
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                inactive_users = User.query.filter(
                    User.last_activity < cutoff_date,
                    User.user_status == 'active'
                ).count()
                
                # Get gift card counts
                total_gift_cards = GiftCard.query.count()
                available_gift_cards = GiftCard.query.filter(GiftCard.used == False).count()
                
                return {
                    "success": True,
                    "status": {
                        "users": {
                            "total": total_users,
                            "active": active_users,
                            "banned": banned_users,
                            "suspended": suspended_users,
                            "inactive_30_days": inactive_users
                        },
                        "gift_cards": {
                            "total": total_gift_cards,
                            "available": available_gift_cards,
                            "used": total_gift_cards - available_gift_cards
                        },
                        "bulk_operations_available": [
                            "bulk_update_status",
                            "bulk_adjust_points",
                            "bulk_reset_data",
                            "bulk_create_gift_cards",
                            "bulk_cleanup_inactive",
                            "bulk_export_data",
                            "bulk_import_users"
                        ]
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting bulk operation status: {e}")
            return {"success": False, "error": "Failed to get bulk operation status"}