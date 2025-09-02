"""
Gift Card Categories System Module
Handles multiple gift card categories and types
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, GiftCard, GiftCardCategory

logger = logging.getLogger(__name__)

class GiftCardCategoryManager:
    """Manages gift card categories and types"""
    
    @staticmethod
    def create_category(name: str, description: str, icon: str) -> Dict[str, Any]:
        """Create a new gift card category"""
        try:
            with app.app_context():
                category = GiftCardCategory(
                    name=name,
                    description=description,
                    icon=icon
                )
                
                db.session.add(category)
                db.session.commit()
                
                return {
                    "success": True,
                    "category_id": category.id,
                    "message": f"Gift card category '{name}' created successfully"
                }
                
        except Exception as e:
            logger.error(f"Error creating gift card category: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to create gift card category"}
    
    @staticmethod
    def get_categories() -> Dict[str, Any]:
        """Get all active gift card categories"""
        try:
            with app.app_context():
                categories = GiftCardCategory.query.filter(
                    GiftCardCategory.is_active == True
                ).all()
                
                category_list = []
                for category in categories:
                    # Get available gift cards count for this category
                    available_cards = GiftCard.query.filter(
                        GiftCard.category_id == category.id,
                        GiftCard.used == False
                    ).count()
                    
                    category_list.append({
                        'id': category.id,
                        'name': category.name,
                        'description': category.description,
                        'icon': category.icon,
                        'available_cards': available_cards,
                        'created_at': category.created_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "categories": category_list
                }
                
        except Exception as e:
            logger.error(f"Error getting gift card categories: {e}")
            return {"success": False, "error": "Failed to get gift card categories"}
    
    @staticmethod
    def add_gift_cards(category_id: int, amounts: List[int], count_per_amount: int = 1) -> Dict[str, Any]:
        """Add gift cards to a category"""
        try:
            with app.app_context():
                category = GiftCardCategory.query.get(category_id)
                if not category:
                    return {"success": False, "error": "Gift card category not found"}
                
                added_count = 0
                for amount in amounts:
                    for _ in range(count_per_amount):
                        # Generate unique code based on category
                        code_prefix = category.name.upper()[:3]
                        unique_code = f"{code_prefix}_{uuid.uuid4().hex[:8].upper()}"
                        
                        gift_card = GiftCard(
                            code=unique_code,
                            amount=amount,
                            currency=GiftCardCategoryManager._get_currency_for_category(category.name),
                            category_id=category_id
                        )
                        
                        db.session.add(gift_card)
                        added_count += 1
                
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Added {added_count} gift cards to {category.name}",
                    "added_count": added_count
                }
                
        except Exception as e:
            logger.error(f"Error adding gift cards: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to add gift cards"}
    
    @staticmethod
    def get_available_gift_cards(category_id: int = None, limit: int = 50) -> Dict[str, Any]:
        """Get available gift cards, optionally filtered by category"""
        try:
            with app.app_context():
                query = GiftCard.query.filter(GiftCard.used == False)
                
                if category_id:
                    query = query.filter(GiftCard.category_id == category_id)
                
                gift_cards = query.limit(limit).all()
                
                card_list = []
                for card in gift_cards:
                    category = GiftCardCategory.query.get(card.category_id) if card.category_id else None
                    
                    card_list.append({
                        'id': card.id,
                        'code': card.code,
                        'amount': card.amount,
                        'currency': card.currency,
                        'category': {
                            'id': category.id,
                            'name': category.name,
                            'icon': category.icon
                        } if category else None,
                        'created_at': card.created_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "gift_cards": card_list,
                    "count": len(card_list)
                }
                
        except Exception as e:
            logger.error(f"Error getting available gift cards: {e}")
            return {"success": False, "error": "Failed to get gift cards"}
    
    @staticmethod
    def redeem_gift_card(user_id: str, category_id: int, amount: int) -> Dict[str, Any]:
        """Redeem a gift card for a user"""
        try:
            with app.app_context():
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                if user.user_status != 'active':
                    return {"success": False, "error": "User account is not active"}
                
                # Find available gift card
                gift_card = GiftCard.query.filter(
                    GiftCard.category_id == category_id,
                    GiftCard.amount == amount,
                    GiftCard.used == False
                ).first()
                
                if not gift_card:
                    return {"success": False, "error": "No gift cards available for this amount"}
                
                # Mark gift card as used
                gift_card.used = True
                gift_card.used_by = user_id
                gift_card.used_at = datetime.utcnow()
                
                # Update user stats
                user.total_gift_cards_redeemed += 1
                
                # Update user profile
                from database import UserProfile
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                
                # Award XP for gift card redemption
                profile.xp += amount // 10  # XP based on gift card amount
                
                db.session.commit()
                
                return {
                    "success": True,
                    "gift_card": {
                        'code': gift_card.code,
                        'amount': gift_card.amount,
                        'currency': gift_card.currency,
                        'redeemed_at': gift_card.used_at.isoformat()
                    },
                    "message": f"Gift card redeemed successfully! Code: {gift_card.code}"
                }
                
        except Exception as e:
            logger.error(f"Error redeeming gift card: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to redeem gift card"}
    
    @staticmethod
    def _get_currency_for_category(category_name: str) -> str:
        """Get currency type for a gift card category"""
        currency_map = {
            'Roblox': 'Robux',
            'Steam': 'USD',
            'Amazon': 'USD',
            'PlayStation': 'USD',
            'Xbox': 'USD',
            'Nintendo': 'USD',
            'Google Play': 'USD',
            'Apple': 'USD',
            'Spotify': 'USD',
            'Netflix': 'USD'
        }
        
        return currency_map.get(category_name, 'USD')
    
    @staticmethod
    def initialize_default_categories() -> Dict[str, Any]:
        """Initialize default gift card categories"""
        try:
            with app.app_context():
                # Check if categories already exist
                if GiftCardCategory.query.count() > 0:
                    return {"success": True, "message": "Gift card categories already initialized"}
                
                default_categories = [
                    {
                        'name': 'Roblox',
                        'description': 'Roblox gift cards for Robux',
                        'icon': '🎮'
                    },
                    {
                        'name': 'Steam',
                        'description': 'Steam gift cards for games and software',
                        'icon': '🎯'
                    },
                    {
                        'name': 'Amazon',
                        'description': 'Amazon gift cards for shopping',
                        'icon': '📦'
                    },
                    {
                        'name': 'PlayStation',
                        'description': 'PlayStation Store gift cards',
                        'icon': '🎮'
                    },
                    {
                        'name': 'Xbox',
                        'description': 'Xbox Store gift cards',
                        'icon': '🎮'
                    },
                    {
                        'name': 'Nintendo',
                        'description': 'Nintendo eShop gift cards',
                        'icon': '🎮'
                    },
                    {
                        'name': 'Google Play',
                        'description': 'Google Play Store gift cards',
                        'icon': '📱'
                    },
                    {
                        'name': 'Apple',
                        'description': 'Apple App Store gift cards',
                        'icon': '🍎'
                    },
                    {
                        'name': 'Spotify',
                        'description': 'Spotify Premium gift cards',
                        'icon': '🎵'
                    },
                    {
                        'name': 'Netflix',
                        'description': 'Netflix subscription gift cards',
                        'icon': '📺'
                    }
                ]
                
                created_count = 0
                for category_data in default_categories:
                    result = GiftCardCategoryManager.create_category(
                        name=category_data['name'],
                        description=category_data['description'],
                        icon=category_data['icon']
                    )
                    if result['success']:
                        created_count += 1
                
                return {
                    "success": True,
                    "message": f"Created {created_count} default gift card categories"
                }
                
        except Exception as e:
            logger.error(f"Error initializing gift card categories: {e}")
            return {"success": False, "error": "Failed to initialize gift card categories"}
    
    @staticmethod
    def get_category_stats(category_id: int) -> Dict[str, Any]:
        """Get statistics for a gift card category"""
        try:
            with app.app_context():
                category = GiftCardCategory.query.get(category_id)
                if not category:
                    return {"success": False, "error": "Category not found"}
                
                # Get gift card statistics
                total_cards = GiftCard.query.filter(GiftCard.category_id == category_id).count()
                available_cards = GiftCard.query.filter(
                    GiftCard.category_id == category_id,
                    GiftCard.used == False
                ).count()
                used_cards = total_cards - available_cards
                
                # Get total value
                total_value = db.session.query(db.func.sum(GiftCard.amount)).filter(
                    GiftCard.category_id == category_id
                ).scalar() or 0
                
                used_value = db.session.query(db.func.sum(GiftCard.amount)).filter(
                    GiftCard.category_id == category_id,
                    GiftCard.used == True
                ).scalar() or 0
                
                return {
                    "success": True,
                    "stats": {
                        'category': {
                            'id': category.id,
                            'name': category.name,
                            'description': category.description,
                            'icon': category.icon
                        },
                        'total_cards': total_cards,
                        'available_cards': available_cards,
                        'used_cards': used_cards,
                        'total_value': total_value,
                        'used_value': used_value,
                        'available_value': total_value - used_value,
                        'usage_rate': (used_cards / total_cards * 100) if total_cards > 0 else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting category stats: {e}")
            return {"success": False, "error": "Failed to get category stats"}
    
    @staticmethod
    def get_user_redemption_history(user_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get user's gift card redemption history"""
        try:
            with app.app_context():
                gift_cards = GiftCard.query.filter(
                    GiftCard.used_by == user_id
                ).order_by(GiftCard.used_at.desc()).limit(limit).all()
                
                redemption_list = []
                for card in gift_cards:
                    category = GiftCardCategory.query.get(card.category_id) if card.category_id else None
                    
                    redemption_list.append({
                        'id': card.id,
                        'code': card.code,
                        'amount': card.amount,
                        'currency': card.currency,
                        'category': {
                            'id': category.id,
                            'name': category.name,
                            'icon': category.icon
                        } if category else None,
                        'redeemed_at': card.used_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "redemptions": redemption_list,
                    "count": len(redemption_list)
                }
                
        except Exception as e:
            logger.error(f"Error getting redemption history: {e}")
            return {"success": False, "error": "Failed to get redemption history"}