"""
Analytics System Module
Handles advanced analytics, user behavior tracking, and reporting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, CasinoGame, AdCompletion, UserProfile, GiftCard, Referral, DailyBonus, Guild, Tournament

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Manages analytics and reporting"""
    
    @staticmethod
    def get_platform_overview() -> Dict[str, Any]:
        """Get comprehensive platform overview"""
        try:
            with app.app_context():
                # Basic stats
                total_users = User.query.count()
                active_users = User.query.filter(User.user_status == 'active').count()
                banned_users = User.query.filter(User.user_status == 'banned').count()
                
                # Revenue stats
                total_points_earned = db.session.query(db.func.sum(User.total_earned)).scalar() or 0
                total_points_balance = db.session.query(db.func.sum(User.points_balance)).scalar() or 0
                
                # Gaming stats
                total_games_played = CasinoGame.query.count()
                total_games_won = CasinoGame.query.filter(CasinoGame.win_amount > 0).count()
                total_casino_winnings = db.session.query(db.func.sum(CasinoGame.win_amount)).scalar() or 0
                
                # Gift card stats
                total_gift_cards = GiftCard.query.count()
                redeemed_gift_cards = GiftCard.query.filter(GiftCard.used == True).count()
                
                # Referral stats
                total_referrals = Referral.query.filter(Referral.referred_id != "").count()
                
                # Guild stats
                total_guilds = Guild.query.filter(Guild.is_active == True).count()
                total_guild_members = db.session.query(db.func.sum(Guild.member_count)).scalar() or 0
                
                # Tournament stats
                total_tournaments = Tournament.query.count()
                active_tournaments = Tournament.query.filter(Tournament.status == 'active').count()
                
                return {
                    "success": True,
                    "overview": {
                        "users": {
                            "total": total_users,
                            "active": active_users,
                            "banned": banned_users,
                            "active_percentage": (active_users / total_users * 100) if total_users > 0 else 0
                        },
                        "revenue": {
                            "total_points_earned": total_points_earned,
                            "total_points_balance": total_points_balance,
                            "points_in_circulation": total_points_balance
                        },
                        "gaming": {
                            "total_games_played": total_games_played,
                            "total_games_won": total_games_won,
                            "win_rate": (total_games_won / total_games_played * 100) if total_games_played > 0 else 0,
                            "total_casino_winnings": total_casino_winnings
                        },
                        "gift_cards": {
                            "total_cards": total_gift_cards,
                            "redeemed_cards": redeemed_gift_cards,
                            "redemption_rate": (redeemed_gift_cards / total_gift_cards * 100) if total_gift_cards > 0 else 0
                        },
                        "social": {
                            "total_referrals": total_referrals,
                            "total_guilds": total_guilds,
                            "total_guild_members": total_guild_members
                        },
                        "tournaments": {
                            "total_tournaments": total_tournaments,
                            "active_tournaments": active_tournaments
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting platform overview: {e}")
            return {"success": False, "error": "Failed to get platform overview"}
    
    @staticmethod
    def get_user_behavior_analytics(days: int = 30) -> Dict[str, Any]:
        """Get user behavior analytics"""
        try:
            with app.app_context():
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # User activity patterns
                daily_active_users = []
                for i in range(days):
                    date = start_date + timedelta(days=i)
                    next_date = date + timedelta(days=1)
                    
                    # Users who had activity on this day
                    dau = db.session.query(User.id).join(CasinoGame, User.id == CasinoGame.user_id).filter(
                        CasinoGame.played_at >= date,
                        CasinoGame.played_at < next_date
                    ).distinct().count()
                    
                    daily_active_users.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "active_users": dau
                    })
                
                # Game preference analysis
                game_stats = db.session.query(
                    CasinoGame.game_type,
                    db.func.count(CasinoGame.id).label('games_played'),
                    db.func.sum(CasinoGame.bet_amount).label('total_bet'),
                    db.func.sum(CasinoGame.win_amount).label('total_winnings')
                ).filter(
                    CasinoGame.played_at >= start_date
                ).group_by(CasinoGame.game_type).all()
                
                game_preferences = []
                for stat in game_stats:
                    game_preferences.append({
                        "game_type": stat.game_type,
                        "games_played": stat.games_played,
                        "total_bet": stat.total_bet or 0,
                        "total_winnings": stat.total_winnings or 0,
                        "house_edge": ((stat.total_bet - stat.total_winnings) / stat.total_bet * 100) if stat.total_bet > 0 else 0
                    })
                
                # User engagement levels
                engagement_levels = {
                    "highly_active": User.query.filter(User.last_activity >= start_date).count(),
                    "moderately_active": User.query.filter(
                        User.last_activity >= start_date - timedelta(days=7),
                        User.last_activity < start_date
                    ).count(),
                    "inactive": User.query.filter(User.last_activity < start_date - timedelta(days=7)).count()
                }
                
                # Retention analysis
                new_users = User.query.filter(User.created_at >= start_date).count()
                retained_users = User.query.filter(
                    User.created_at >= start_date,
                    User.last_activity >= start_date
                ).count()
                
                retention_rate = (retained_users / new_users * 100) if new_users > 0 else 0
                
                return {
                    "success": True,
                    "analytics": {
                        "period_days": days,
                        "daily_active_users": daily_active_users,
                        "game_preferences": game_preferences,
                        "engagement_levels": engagement_levels,
                        "retention": {
                            "new_users": new_users,
                            "retained_users": retained_users,
                            "retention_rate": retention_rate
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting user behavior analytics: {e}")
            return {"success": False, "error": "Failed to get user behavior analytics"}
    
    @staticmethod
    def get_revenue_analytics(days: int = 30) -> Dict[str, Any]:
        """Get revenue analytics and reports"""
        try:
            with app.app_context():
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Daily revenue breakdown
                daily_revenue = []
                for i in range(days):
                    date = start_date + timedelta(days=i)
                    next_date = date + timedelta(days=1)
                    
                    # Points earned from ads
                    ad_revenue = db.session.query(db.func.sum(AdCompletion.points_earned)).filter(
                        AdCompletion.completed_at >= date,
                        AdCompletion.completed_at < next_date
                    ).scalar() or 0
                    
                    # Casino activity
                    casino_bets = db.session.query(db.func.sum(CasinoGame.bet_amount)).filter(
                        CasinoGame.played_at >= date,
                        CasinoGame.played_at < next_date
                    ).scalar() or 0
                    
                    casino_winnings = db.session.query(db.func.sum(CasinoGame.win_amount)).filter(
                        CasinoGame.played_at >= date,
                        CasinoGame.played_at < next_date
                    ).scalar() or 0
                    
                    casino_net = casino_bets - casino_winnings
                    
                    daily_revenue.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "ad_revenue": ad_revenue,
                        "casino_bets": casino_bets,
                        "casino_winnings": casino_winnings,
                        "casino_net": casino_net,
                        "total_revenue": ad_revenue + casino_net
                    })
                
                # Revenue sources breakdown
                total_ad_revenue = sum(day["ad_revenue"] for day in daily_revenue)
                total_casino_net = sum(day["casino_net"] for day in daily_revenue)
                total_revenue = total_ad_revenue + total_casino_net
                
                revenue_sources = {
                    "ad_revenue": {
                        "amount": total_ad_revenue,
                        "percentage": (total_ad_revenue / total_revenue * 100) if total_revenue > 0 else 0
                    },
                    "casino_net": {
                        "amount": total_casino_net,
                        "percentage": (total_casino_net / total_revenue * 100) if total_revenue > 0 else 0
                    }
                }
                
                # Top earning users
                top_earners = db.session.query(
                    User.id,
                    User.username,
                    User.total_earned
                ).filter(
                    User.total_earned > 0
                ).order_by(User.total_earned.desc()).limit(10).all()
                
                top_earners_list = []
                for user in top_earners:
                    top_earners_list.append({
                        "user_id": user.id,
                        "username": user.username,
                        "total_earned": user.total_earned
                    })
                
                return {
                    "success": True,
                    "revenue": {
                        "period_days": days,
                        "total_revenue": total_revenue,
                        "daily_revenue": daily_revenue,
                        "revenue_sources": revenue_sources,
                        "top_earners": top_earners_list
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {e}")
            return {"success": False, "error": "Failed to get revenue analytics"}
    
    @staticmethod
    def get_user_segmentation() -> Dict[str, Any]:
        """Get user segmentation analysis"""
        try:
            with app.app_context():
                # Segment users by activity level
                highly_active = User.query.filter(
                    User.last_activity >= datetime.utcnow() - timedelta(days=1)
                ).count()
                
                moderately_active = User.query.filter(
                    User.last_activity >= datetime.utcnow() - timedelta(days=7),
                    User.last_activity < datetime.utcnow() - timedelta(days=1)
                ).count()
                
                low_activity = User.query.filter(
                    User.last_activity >= datetime.utcnow() - timedelta(days=30),
                    User.last_activity < datetime.utcnow() - timedelta(days=7)
                ).count()
                
                inactive = User.query.filter(
                    User.last_activity < datetime.utcnow() - timedelta(days=30)
                ).count()
                
                # Segment by spending behavior
                high_spenders = User.query.filter(User.total_earned >= 10000).count()
                medium_spenders = User.query.filter(
                    User.total_earned >= 1000,
                    User.total_earned < 10000
                ).count()
                low_spenders = User.query.filter(
                    User.total_earned > 0,
                    User.total_earned < 1000
                ).count()
                non_spenders = User.query.filter(User.total_earned == 0).count()
                
                # Segment by gaming behavior
                casino_players = db.session.query(User.id).join(CasinoGame, User.id == CasinoGame.user_id).distinct().count()
                ad_watchers = db.session.query(User.id).join(AdCompletion, User.id == AdCompletion.user_id).distinct().count()
                
                return {
                    "success": True,
                    "segmentation": {
                        "activity_levels": {
                            "highly_active": highly_active,
                            "moderately_active": moderately_active,
                            "low_activity": low_activity,
                            "inactive": inactive
                        },
                        "spending_behavior": {
                            "high_spenders": high_spenders,
                            "medium_spenders": medium_spenders,
                            "low_spenders": low_spenders,
                            "non_spenders": non_spenders
                        },
                        "gaming_behavior": {
                            "casino_players": casino_players,
                            "ad_watchers": ad_watchers
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting user segmentation: {e}")
            return {"success": False, "error": "Failed to get user segmentation"}
    
    @staticmethod
    def get_performance_metrics() -> Dict[str, Any]:
        """Get platform performance metrics"""
        try:
            with app.app_context():
                # User growth metrics
                total_users = User.query.count()
                new_users_today = User.query.filter(
                    User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                ).count()
                
                new_users_week = User.query.filter(
                    User.created_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
                
                new_users_month = User.query.filter(
                    User.created_at >= datetime.utcnow() - timedelta(days=30)
                ).count()
                
                # Engagement metrics
                daily_active_users = db.session.query(User.id).join(CasinoGame, User.id == CasinoGame.user_id).filter(
                    CasinoGame.played_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                ).distinct().count()
                
                # Conversion metrics
                users_with_gift_cards = db.session.query(User.id).join(GiftCard, User.id == GiftCard.used_by).distinct().count()
                gift_card_conversion_rate = (users_with_gift_cards / total_users * 100) if total_users > 0 else 0
                
                # Retention metrics
                users_created_week_ago = User.query.filter(
                    User.created_at >= datetime.utcnow() - timedelta(days=7),
                    User.created_at < datetime.utcnow() - timedelta(days=6)
                ).count()
                
                retained_users = User.query.filter(
                    User.created_at >= datetime.utcnow() - timedelta(days=7),
                    User.created_at < datetime.utcnow() - timedelta(days=6),
                    User.last_activity >= datetime.utcnow() - timedelta(days=1)
                ).count()
                
                retention_rate = (retained_users / users_created_week_ago * 100) if users_created_week_ago > 0 else 0
                
                return {
                    "success": True,
                    "metrics": {
                        "user_growth": {
                            "total_users": total_users,
                            "new_users_today": new_users_today,
                            "new_users_week": new_users_week,
                            "new_users_month": new_users_month
                        },
                        "engagement": {
                            "daily_active_users": daily_active_users,
                            "dau_percentage": (daily_active_users / total_users * 100) if total_users > 0 else 0
                        },
                        "conversion": {
                            "gift_card_conversion_rate": gift_card_conversion_rate,
                            "users_with_gift_cards": users_with_gift_cards
                        },
                        "retention": {
                            "retention_rate": retention_rate,
                            "retained_users": retained_users,
                            "cohort_size": users_created_week_ago
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"success": False, "error": "Failed to get performance metrics"}
    
    @staticmethod
    def export_analytics_data(format: str = 'json') -> Dict[str, Any]:
        """Export analytics data in various formats"""
        try:
            with app.app_context():
                # Get all analytics data
                overview = AnalyticsManager.get_platform_overview()
                behavior = AnalyticsManager.get_user_behavior_analytics(30)
                revenue = AnalyticsManager.get_revenue_analytics(30)
                segmentation = AnalyticsManager.get_user_segmentation()
                metrics = AnalyticsManager.get_performance_metrics()
                
                export_data = {
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "overview": overview.get("overview", {}),
                    "behavior": behavior.get("analytics", {}),
                    "revenue": revenue.get("revenue", {}),
                    "segmentation": segmentation.get("segmentation", {}),
                    "metrics": metrics.get("metrics", {})
                }
                
                if format == 'csv':
                    # Convert to CSV format (simplified)
                    csv_data = "Metric,Value\n"
                    csv_data += f"Total Users,{export_data['overview']['users']['total']}\n"
                    csv_data += f"Active Users,{export_data['overview']['users']['active']}\n"
                    csv_data += f"Total Revenue,{export_data['revenue']['total_revenue']}\n"
                    csv_data += f"Daily Active Users,{export_data['metrics']['engagement']['daily_active_users']}\n"
                    
                    return {
                        "success": True,
                        "format": "csv",
                        "data": csv_data
                    }
                else:
                    return {
                        "success": True,
                        "format": "json",
                        "data": export_data
                    }
                
        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            return {"success": False, "error": "Failed to export analytics data"}