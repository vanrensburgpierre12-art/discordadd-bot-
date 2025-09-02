diff --git a/seasonal_events_system.py b/seasonal_events_system.py
--- a/seasonal_events_system.py
+++ b/seasonal_events_system.py
@@ -0,0 +1,345 @@
+"""
+Seasonal Events System Module
+Handles seasonal events, special rewards, and limited-time bonuses
+"""
+
+import logging
+import json
+from datetime import datetime, timedelta
+from typing import Dict, Any, List, Optional
+from app_context import app, db
+from database import User, SeasonalEvent, UserProfile
+
+logger = logging.getLogger(__name__)
+
+class SeasonalEventManager:
+    """Manages seasonal events and special rewards"""
+    
+    @staticmethod
+    def create_seasonal_event(name: str, description: str, event_type: str,
+                             start_date: datetime, end_date: datetime,
+                             bonus_multiplier: float = 1.0,
+                             special_rewards: Dict[str, Any] = None) -> Dict[str, Any]:
+        """Create a new seasonal event"""
+        try:
+            with app.app_context():
+                seasonal_event = SeasonalEvent(
+                    name=name,
+                    description=description,
+                    event_type=event_type,
+                    start_date=start_date,
+                    end_date=end_date,
+                    bonus_multiplier=bonus_multiplier,
+                    special_rewards=json.dumps(special_rewards) if special_rewards else None
+                )
+                
+                db.session.add(seasonal_event)
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "event_id": seasonal_event.id,
+                    "message": f"Seasonal event '{name}' created successfully"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error creating seasonal event: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to create seasonal event"}
+    
+    @staticmethod
+    def get_active_events() -> Dict[str, Any]:
+        """Get all active seasonal events"""
+        try:
+            with app.app_context():
+                now = datetime.utcnow()
+                events = SeasonalEvent.query.filter(
+                    SeasonalEvent.is_active == True,
+                    SeasonalEvent.start_date <= now,
+                    SeasonalEvent.end_date >= now
+                ).all()
+                
+                event_list = []
+                for event in events:
+                    special_rewards = json.loads(event.special_rewards) if event.special_rewards else {}
+                    
+                    event_list.append({
+                        'id': event.id,
+                        'name': event.name,
+                        'description': event.description,
+                        'event_type': event.event_type,
+                        'bonus_multiplier': event.bonus_multiplier,
+                        'special_rewards': special_rewards,
+                        'start_date': event.start_date.isoformat(),
+                        'end_date': event.end_date.isoformat(),
+                        'time_remaining': (event.end_date - now).total_seconds(),
+                        'is_active': True
+                    })
+                
+                return {
+                    "success": True,
+                    "events": event_list
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting active events: {e}")
+            return {"success": False, "error": "Failed to get active events"}
+    
+    @staticmethod
+    def get_event_bonus_multiplier() -> float:
+        """Get current bonus multiplier from active events"""
+        try:
+            with app.app_context():
+                now = datetime.utcnow()
+                active_events = SeasonalEvent.query.filter(
+                    SeasonalEvent.is_active == True,
+                    SeasonalEvent.start_date <= now,
+                    SeasonalEvent.end_date >= now
+                ).all()
+                
+                # Use the highest multiplier from active events
+                max_multiplier = 1.0
+                for event in active_events:
+                    max_multiplier = max(max_multiplier, event.bonus_multiplier)
+                
+                return max_multiplier
+                
+        except Exception as e:
+            logger.error(f"Error getting event bonus multiplier: {e}")
+            return 1.0
+    
+    @staticmethod
+    def apply_event_bonus(user_id: str, base_amount: int, bonus_type: str = "points") -> Dict[str, Any]:
+        """Apply seasonal event bonus to a reward"""
+        try:
+            with app.app_context():
+                multiplier = SeasonalEventManager.get_event_bonus_multiplier()
+                bonus_amount = int(base_amount * (multiplier - 1.0))
+                total_amount = base_amount + bonus_amount
+                
+                if bonus_amount > 0:
+                    # Award bonus to user
+                    user = User.query.get(user_id)
+                    if user:
+                        user.points_balance += bonus_amount
+                        user.total_earned += bonus_amount
+                        
+                        # Update profile XP
+                        profile = UserProfile.query.filter_by(user_id=user_id).first()
+                        if not profile:
+                            profile = UserProfile(user_id=user_id)
+                            db.session.add(profile)
+                        
+                        profile.xp += bonus_amount // 10  # XP based on bonus amount
+                        
+                        db.session.commit()
+                
+                return {
+                    "success": True,
+                    "base_amount": base_amount,
+                    "bonus_amount": bonus_amount,
+                    "total_amount": total_amount,
+                    "multiplier": multiplier,
+                    "has_bonus": bonus_amount > 0
+                }
+                
+        except Exception as e:
+            logger.error(f"Error applying event bonus: {e}")
+            return {"success": False, "error": "Failed to apply event bonus"}
+    
+    @staticmethod
+    def initialize_default_events() -> Dict[str, Any]:
+        """Initialize default seasonal events"""
+        try:
+            with app.app_context():
+                # Check if events already exist
+                if SeasonalEvent.query.count() > 0:
+                    return {"success": True, "message": "Seasonal events already initialized"}
+                
+                now = datetime.utcnow()
+                
+                # Create some example seasonal events
+                default_events = [
+                    {
+                        'name': 'New Year Celebration',
+                        'description': 'Start the year with bonus rewards!',
+                        'event_type': 'holiday',
+                        'start_date': now.replace(month=1, day=1, hour=0, minute=0, second=0),
+                        'end_date': now.replace(month=1, day=7, hour=23, minute=59, second=59),
+                        'bonus_multiplier': 1.5,
+                        'special_rewards': {
+                            'daily_bonus_multiplier': 2.0,
+                            'casino_bonus': 200
+                        }
+                    },
+                    {
+                        'name': 'Valentine\'s Day Special',
+                        'description': 'Share the love with bonus points!',
+                        'event_type': 'holiday',
+                        'start_date': now.replace(month=2, day=14, hour=0, minute=0, second=0),
+                        'end_date': now.replace(month=2, day=14, hour=23, minute=59, second=59),
+                        'bonus_multiplier': 1.3,
+                        'special_rewards': {
+                            'referral_bonus': 1000,
+                            'couple_bonus': 500
+                        }
+                    },
+                    {
+                        'name': 'Summer Festival',
+                        'description': 'Hot summer, hot rewards!',
+                        'event_type': 'special',
+                        'start_date': now.replace(month=7, day=1, hour=0, minute=0, second=0),
+                        'end_date': now.replace(month=7, day=31, hour=23, minute=59, second=59),
+                        'bonus_multiplier': 1.2,
+                        'special_rewards': {
+                            'daily_bonus_multiplier': 1.5,
+                            'achievement_bonus': 300
+                        }
+                    },
+                    {
+                        'name': 'Halloween Spooktacular',
+                        'description': 'Trick or treat with bonus rewards!',
+                        'event_type': 'holiday',
+                        'start_date': now.replace(month=10, day=31, hour=0, minute=0, second=0),
+                        'end_date': now.replace(month=10, day=31, hour=23, minute=59, second=59),
+                        'bonus_multiplier': 1.4,
+                        'special_rewards': {
+                            'casino_bonus': 300,
+                            'mystery_rewards': True
+                        }
+                    },
+                    {
+                        'name': 'Christmas Celebration',
+                        'description': 'The most wonderful time for rewards!',
+                        'event_type': 'holiday',
+                        'start_date': now.replace(month=12, day=25, hour=0, minute=0, second=0),
+                        'end_date': now.replace(month=12, day=31, hour=23, minute=59, second=59),
+                        'bonus_multiplier': 2.0,
+                        'special_rewards': {
+                            'daily_bonus_multiplier': 3.0,
+                            'gift_bonus': 1000,
+                            'special_achievements': True
+                        }
+                    }
+                ]
+                
+                created_count = 0
+                for event_data in default_events:
+                    result = SeasonalEventManager.create_seasonal_event(
+                        name=event_data['name'],
+                        description=event_data['description'],
+                        event_type=event_data['event_type'],
+                        start_date=event_data['start_date'],
+                        end_date=event_data['end_date'],
+                        bonus_multiplier=event_data['bonus_multiplier'],
+                        special_rewards=event_data['special_rewards']
+                    )
+                    if result['success']:
+                        created_count += 1
+                
+                return {
+                    "success": True,
+                    "message": f"Created {created_count} default seasonal events"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error initializing seasonal events: {e}")
+            return {"success": False, "error": "Failed to initialize seasonal events"}
+    
+    @staticmethod
+    def cleanup_expired_events() -> Dict[str, Any]:
+        """Clean up expired seasonal events"""
+        try:
+            with app.app_context():
+                now = datetime.utcnow()
+                expired_events = SeasonalEvent.query.filter(
+                    SeasonalEvent.end_date < now,
+                    SeasonalEvent.is_active == True
+                ).all()
+                
+                for event in expired_events:
+                    event.is_active = False
+                
+                db.session.commit()
+                
+                return {
+                    "success": True,
+                    "message": f"Deactivated {len(expired_events)} expired events"
+                }
+                
+        except Exception as e:
+            logger.error(f"Error cleaning up expired events: {e}")
+            db.session.rollback()
+            return {"success": False, "error": "Failed to cleanup expired events"}
+    
+    @staticmethod
+    def get_event_history(limit: int = 10) -> Dict[str, Any]:
+        """Get recent seasonal events history"""
+        try:
+            with app.app_context():
+                events = SeasonalEvent.query.order_by(
+                    SeasonalEvent.end_date.desc()
+                ).limit(limit).all()
+                
+                event_list = []
+                for event in events:
+                    special_rewards = json.loads(event.special_rewards) if event.special_rewards else {}
+                    
+                    event_list.append({
+                        'id': event.id,
+                        'name': event.name,
+                        'description': event.description,
+                        'event_type': event.event_type,
+                        'bonus_multiplier': event.bonus_multiplier,
+                        'special_rewards': special_rewards,
+                        'start_date': event.start_date.isoformat(),
+                        'end_date': event.end_date.isoformat(),
+                        'is_active': event.is_active,
+                        'created_at': event.created_at.isoformat()
+                    })
+                
+                return {
+                    "success": True,
+                    "events": event_list
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting event history: {e}")
+            return {"success": False, "error": "Failed to get event history"}
+    
+    @staticmethod
+    def get_upcoming_events(limit: int = 5) -> Dict[str, Any]:
+        """Get upcoming seasonal events"""
+        try:
+            with app.app_context():
+                now = datetime.utcnow()
+                events = SeasonalEvent.query.filter(
+                    SeasonalEvent.start_date > now,
+                    SeasonalEvent.is_active == True
+                ).order_by(SeasonalEvent.start_date).limit(limit).all()
+                
+                event_list = []
+                for event in events:
+                    special_rewards = json.loads(event.special_rewards) if event.special_rewards else {}
+                    
+                    event_list.append({
+                        'id': event.id,
+                        'name': event.name,
+                        'description': event.description,
+                        'event_type': event.event_type,
+                        'bonus_multiplier': event.bonus_multiplier,
+                        'special_rewards': special_rewards,
+                        'start_date': event.start_date.isoformat(),
+                        'end_date': event.end_date.isoformat(),
+                        'time_until_start': (event.start_date - now).total_seconds(),
+                        'duration': (event.end_date - event.start_date).total_seconds()
+                    })
+                
+                return {
+                    "success": True,
+                    "events": event_list
+                }
+                
+        except Exception as e:
+            logger.error(f"Error getting upcoming events: {e}")
+            return {"success": False, "error": "Failed to get upcoming events"}
