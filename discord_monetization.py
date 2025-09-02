"""
Discord Monetization Module for Discord Rewards Platform
Handles Discord server boosts, Nitro gifts, and subscription tiers
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask_app import app
from database import db, User, UserSubscription, DiscordTransaction, UserWallet
from config import Config

logger = logging.getLogger(__name__)

class DiscordMonetizationManager:
    """Manages Discord-based monetization features"""
    
    @staticmethod
    def get_user_subscription_tier(user_id: str) -> Optional[str]:
        """Get user's current subscription tier"""
        subscription = UserSubscription.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).first()
        
        if subscription and subscription.expires_at:
            if subscription.expires_at > datetime.utcnow():
                return subscription.subscription_tier
            else:
                # Subscription expired, deactivate
                subscription.is_active = False
                db.session.commit()
        
        return subscription.subscription_tier if subscription else None
    
    @staticmethod
    def get_casino_bonus_multiplier(user_id: str) -> float:
        """Get casino bonus multiplier based on subscription tier"""
        tier = DiscordMonetizationManager.get_user_subscription_tier(user_id)
        
        if tier and tier in Config.SUBSCRIPTION_TIERS:
            return 1.0 + Config.SUBSCRIPTION_TIERS[tier]['casino_bonus']
        
        return 1.0  # No bonus for free users
    
    @staticmethod
    def process_server_boost(user_id: str, boost_level: int) -> Dict[str, Any]:
        """Process server boost and award points"""
        try:
            # Determine boost tier
            if boost_level >= 14:
                tier_key = "level_3"
            elif boost_level >= 7:
                tier_key = "level_2"
            elif boost_level >= 2:
                tier_key = "level_1"
            else:
                return {"success": False, "error": "Insufficient boost level"}
            
            tier_info = Config.SERVER_BOOST_REWARDS[tier_key]
            
            # Get or create user
            user = User.query.filter_by(id=user_id).first()
            if not user:
                user = User(id=user_id, username="Unknown", points_balance=0)
                db.session.add(user)
            
            # Award points
            points_awarded = tier_info['points']
            user.points_balance += points_awarded
            user.total_earned += points_awarded
            
            # Create subscription record
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription:
                subscription = UserSubscription(user_id=user_id)
                db.session.add(subscription)
            
            subscription.subscription_tier = tier_key
            subscription.subscription_type = 'server_boost'
            subscription.points_earned += points_awarded
            subscription.is_active = True
            subscription.started_at = datetime.utcnow()
            subscription.expires_at = None  # Server boosts don't expire
            
            # Record transaction
            transaction = DiscordTransaction(
                user_id=user_id,
                transaction_type='server_boost',
                tier_name=tier_info['name'],
                points_awarded=points_awarded,
                discord_data=json.dumps({"boost_level": boost_level, "tier": tier_key})
            )
            db.session.add(transaction)
            
            # Update wallet stats (for tracking)
            wallet = UserWallet.query.filter_by(user_id=user_id).first()
            if not wallet:
                wallet = UserWallet(user_id=user_id)
                db.session.add(wallet)
            
            # Estimate USD value for tracking
            estimated_usd = points_awarded / Config.POINTS_PER_DOLLAR
            wallet.total_deposited += estimated_usd
            
            db.session.commit()
            
            return {
                "success": True,
                "tier": tier_key,
                "tier_name": tier_info['name'],
                "points_awarded": points_awarded,
                "new_balance": user.points_balance,
                "casino_bonus": Config.SUBSCRIPTION_TIERS.get(tier_key, {}).get('casino_bonus', 0) * 100
            }
            
        except Exception as e:
            logger.error(f"Error processing server boost: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to process server boost"}
    
    @staticmethod
    def process_nitro_gift(user_id: str, nitro_type: str) -> Dict[str, Any]:
        """Process Nitro gift and award points"""
        try:
            if nitro_type not in Config.NITRO_GIFT_REWARDS:
                return {"success": False, "error": "Invalid Nitro type"}
            
            tier_info = Config.NITRO_GIFT_REWARDS[nitro_type]
            
            # Get or create user
            user = User.query.filter_by(id=user_id).first()
            if not user:
                user = User(id=user_id, username="Unknown", points_balance=0)
                db.session.add(user)
            
            # Award points
            points_awarded = tier_info['points']
            user.points_balance += points_awarded
            user.total_earned += points_awarded
            
            # Create subscription record
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription:
                subscription = UserSubscription(user_id=user_id)
                db.session.add(subscription)
            
            subscription.subscription_tier = nitro_type
            subscription.subscription_type = 'nitro_gift'
            subscription.points_earned += points_awarded
            subscription.is_active = True
            subscription.started_at = datetime.utcnow()
            subscription.expires_at = datetime.utcnow() + timedelta(days=30)  # Nitro lasts 30 days
            
            # Record transaction
            transaction = DiscordTransaction(
                user_id=user_id,
                transaction_type='nitro_gift',
                tier_name=tier_info['name'],
                points_awarded=points_awarded,
                discord_data=json.dumps({"nitro_type": nitro_type, "price": tier_info['price']})
            )
            db.session.add(transaction)
            
            # Update wallet stats
            wallet = UserWallet.query.filter_by(user_id=user_id).first()
            if not wallet:
                wallet = UserWallet(user_id=user_id)
                db.session.add(wallet)
            
            wallet.total_deposited += tier_info['price']
            
            db.session.commit()
            
            return {
                "success": True,
                "nitro_type": nitro_type,
                "nitro_name": tier_info['name'],
                "points_awarded": points_awarded,
                "new_balance": user.points_balance,
                "expires_at": subscription.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing Nitro gift: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to process Nitro gift"}
    
    @staticmethod
    def process_subscription(user_id: str, tier: str) -> Dict[str, Any]:
        """Process Discord server subscription"""
        try:
            if tier not in Config.SUBSCRIPTION_TIERS:
                return {"success": False, "error": "Invalid subscription tier"}
            
            tier_info = Config.SUBSCRIPTION_TIERS[tier]
            
            # Get or create user
            user = User.query.filter_by(id=user_id).first()
            if not user:
                user = User(id=user_id, username="Unknown", points_balance=0)
                db.session.add(user)
            
            # Award points
            points_awarded = tier_info['points']
            user.points_balance += points_awarded
            user.total_earned += points_awarded
            
            # Create subscription record
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            if not subscription:
                subscription = UserSubscription(user_id=user_id)
                db.session.add(subscription)
            
            subscription.subscription_tier = tier
            subscription.subscription_type = 'discord_subscription'
            subscription.points_earned += points_awarded
            subscription.is_active = True
            subscription.started_at = datetime.utcnow()
            subscription.expires_at = datetime.utcnow() + timedelta(days=30)  # Monthly subscription
            
            # Record transaction
            transaction = DiscordTransaction(
                user_id=user_id,
                transaction_type='subscription',
                tier_name=tier_info['name'],
                points_awarded=points_awarded,
                discord_data=json.dumps({"tier": tier, "price": tier_info['price']})
            )
            db.session.add(transaction)
            
            # Update wallet stats
            wallet = UserWallet.query.filter_by(user_id=user_id).first()
            if not wallet:
                wallet = UserWallet(user_id=user_id)
                db.session.add(wallet)
            
            wallet.total_deposited += tier_info['price']
            
            db.session.commit()
            
            return {
                "success": True,
                "tier": tier,
                "tier_name": tier_info['name'],
                "points_awarded": points_awarded,
                "new_balance": user.points_balance,
                "casino_bonus": tier_info['casino_bonus'] * 100,
                "expires_at": subscription.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing subscription: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to process subscription"}
    
    @staticmethod
    def get_subscription_info(user_id: str) -> Dict[str, Any]:
        """Get user's subscription information"""
        try:
            subscription = UserSubscription.query.filter_by(user_id=user_id).first()
            
            if not subscription or not subscription.is_active:
                return {
                    "success": True,
                    "has_subscription": False,
                    "tier": None,
                    "casino_bonus": 0,
                    "expires_at": None
                }
            
            # Check if expired
            if subscription.expires_at and subscription.expires_at < datetime.utcnow():
                subscription.is_active = False
                db.session.commit()
                return {
                    "success": True,
                    "has_subscription": False,
                    "tier": None,
                    "casino_bonus": 0,
                    "expires_at": None
                }
            
            casino_bonus = 0
            if subscription.subscription_tier in Config.SUBSCRIPTION_TIERS:
                casino_bonus = Config.SUBSCRIPTION_TIERS[subscription.subscription_tier]['casino_bonus'] * 100
            
            return {
                "success": True,
                "has_subscription": True,
                "tier": subscription.subscription_tier,
                "tier_name": Config.SUBSCRIPTION_TIERS.get(subscription.subscription_tier, {}).get('name', 'Unknown'),
                "subscription_type": subscription.subscription_type,
                "casino_bonus": casino_bonus,
                "points_earned": subscription.points_earned,
                "started_at": subscription.started_at.isoformat(),
                "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription info: {e}")
            return {"success": False, "error": "Failed to get subscription info"}
    
    @staticmethod
    def get_available_tiers() -> Dict[str, Any]:
        """Get all available subscription tiers and their benefits"""
        return {
            "success": True,
            "server_boosts": Config.SERVER_BOOST_REWARDS,
            "nitro_gifts": Config.NITRO_GIFT_REWARDS,
            "subscriptions": Config.SUBSCRIPTION_TIERS
        }