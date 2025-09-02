"""
Multi-Language Support System Module
Handles internationalization, translations, and language preferences
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, UserProfile

logger = logging.getLogger(__name__)

class MultiLanguageManager:
    """Manages multi-language support and translations"""
    
    def __init__(self):
        self.default_language = 'en'
        self.supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """Load translation files"""
        try:
            translations_dir = "translations"
            if not os.path.exists(translations_dir):
                os.makedirs(translations_dir)
                self.create_default_translations()
            
            for language in self.supported_languages:
                translation_file = os.path.join(translations_dir, f"{language}.json")
                if os.path.exists(translation_file):
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[language] = json.load(f)
                else:
                    # Create default translation file
                    self.create_language_file(language)
                    
        except Exception as e:
            logger.error(f"Error loading translations: {e}")
    
    def create_default_translations(self):
        """Create default translation files"""
        default_translations = {
            'en': {
                'welcome': 'Welcome to Our Rewards Platform!',
                'balance': 'Balance',
                'points': 'Points',
                'earn': 'Earn',
                'redeem': 'Redeem',
                'casino': 'Casino',
                'games': 'Games',
                'dice': 'Dice',
                'slots': 'Slots',
                'blackjack': 'Blackjack',
                'roulette': 'Roulette',
                'poker': 'Poker',
                'lottery': 'Lottery',
                'play': 'Play',
                'bet': 'Bet',
                'win': 'Win',
                'lose': 'Lose',
                'tie': 'Tie',
                'insufficient_points': 'Insufficient points',
                'daily_bonus': 'Daily Bonus',
                'claim': 'Claim',
                'streak': 'Streak',
                'achievements': 'Achievements',
                'leaderboard': 'Leaderboard',
                'tournaments': 'Tournaments',
                'friends': 'Friends',
                'guild': 'Guild',
                'profile': 'Profile',
                'settings': 'Settings',
                'language': 'Language',
                'logout': 'Logout',
                'admin': 'Admin',
                'user_management': 'User Management',
                'analytics': 'Analytics',
                'reports': 'Reports',
                'moderation': 'Moderation',
                'backup': 'Backup',
                'restore': 'Restore',
                'export': 'Export',
                'import': 'Import',
                'success': 'Success',
                'error': 'Error',
                'warning': 'Warning',
                'info': 'Information',
                'loading': 'Loading...',
                'saving': 'Saving...',
                'deleting': 'Deleting...',
                'confirm': 'Confirm',
                'cancel': 'Cancel',
                'yes': 'Yes',
                'no': 'No',
                'ok': 'OK',
                'close': 'Close',
                'save': 'Save',
                'delete': 'Delete',
                'edit': 'Edit',
                'add': 'Add',
                'remove': 'Remove',
                'search': 'Search',
                'filter': 'Filter',
                'sort': 'Sort',
                'refresh': 'Refresh',
                'next': 'Next',
                'previous': 'Previous',
                'page': 'Page',
                'of': 'of',
                'total': 'Total',
                'results': 'Results',
                'no_results': 'No results found',
                'try_again': 'Try again',
                'contact_support': 'Contact Support',
                'help': 'Help',
                'documentation': 'Documentation',
                'terms': 'Terms of Service',
                'privacy': 'Privacy Policy',
                'about': 'About',
                'version': 'Version',
                'last_updated': 'Last Updated',
                'created_at': 'Created At',
                'updated_at': 'Updated At',
                'status': 'Status',
                'active': 'Active',
                'inactive': 'Inactive',
                'banned': 'Banned',
                'suspended': 'Suspended',
                'pending': 'Pending',
                'completed': 'Completed',
                'cancelled': 'Cancelled',
                'upcoming': 'Upcoming',
                'level': 'Level',
                'xp': 'XP',
                'experience': 'Experience',
                'rank': 'Rank',
                'ranking': 'Ranking',
                'score': 'Score',
                'points_earned': 'Points Earned',
                'games_played': 'Games Played',
                'games_won': 'Games Won',
                'win_rate': 'Win Rate',
                'best_streak': 'Best Streak',
                'current_streak': 'Current Streak',
                'referrals': 'Referrals',
                'referral_code': 'Referral Code',
                'use_referral': 'Use Referral Code',
                'gift_cards': 'Gift Cards',
                'redeem_gift_card': 'Redeem Gift Card',
                'gift_card_code': 'Gift Card Code',
                'amount': 'Amount',
                'currency': 'Currency',
                'category': 'Category',
                'description': 'Description',
                'name': 'Name',
                'username': 'Username',
                'email': 'Email',
                'password': 'Password',
                'confirm_password': 'Confirm Password',
                'avatar': 'Avatar',
                'bio': 'Bio',
                'join_date': 'Join Date',
                'last_activity': 'Last Activity',
                'total_earned': 'Total Earned',
                'total_spent': 'Total Spent',
                'favorite_game': 'Favorite Game',
                'challenges': 'Challenges',
                'daily_challenge': 'Daily Challenge',
                'weekly_challenge': 'Weekly Challenge',
                'monthly_challenge': 'Monthly Challenge',
                'progress': 'Progress',
                'requirement': 'Requirement',
                'reward': 'Reward',
                'bonus': 'Bonus',
                'multiplier': 'Multiplier',
                'special_event': 'Special Event',
                'seasonal_event': 'Seasonal Event',
                'holiday': 'Holiday',
                'anniversary': 'Anniversary',
                'celebration': 'Celebration',
                'new_year': 'New Year',
                'valentine': 'Valentine\'s Day',
                'summer': 'Summer Festival',
                'halloween': 'Halloween',
                'christmas': 'Christmas',
                'vip': 'VIP',
                'premium': 'Premium',
                'exclusive': 'Exclusive',
                'limited': 'Limited',
                'rare': 'Rare',
                'legendary': 'Legendary',
                'epic': 'Epic',
                'common': 'Common',
                'uncommon': 'Uncommon',
                'notification': 'Notification',
                'email': 'Email',
                'push': 'Push',
                'sms': 'SMS',
                'discord': 'Discord',
                'mobile': 'Mobile',
                'desktop': 'Desktop',
                'web': 'Web',
                'api': 'API',
                'rate_limit': 'Rate Limit',
                'throttle': 'Throttle',
                'quota': 'Quota',
                'limit': 'Limit',
                'exceeded': 'Exceeded',
                'reset': 'Reset',
                'expires': 'Expires',
                'expired': 'Expired',
                'valid': 'Valid',
                'invalid': 'Invalid',
                'required': 'Required',
                'optional': 'Optional',
                'public': 'Public',
                'private': 'Private',
                'hidden': 'Hidden',
                'visible': 'Visible',
                'enabled': 'Enabled',
                'disabled': 'Disabled',
                'on': 'On',
                'off': 'Off',
                'true': 'True',
                'false': 'False',
                'null': 'Null',
                'empty': 'Empty',
                'full': 'Full',
                'available': 'Available',
                'unavailable': 'Unavailable',
                'online': 'Online',
                'offline': 'Offline',
                'busy': 'Busy',
                'away': 'Away',
                'idle': 'Idle',
                'dnd': 'Do Not Disturb'
            }
        }
        
        # Create English translation file
        self.create_language_file('en', default_translations['en'])
        
        # Create other language files with basic translations
        for language in self.supported_languages:
            if language != 'en':
                self.create_language_file(language)
    
    def create_language_file(self, language: str, translations: Dict[str, str] = None):
        """Create a language translation file"""
        try:
            translations_dir = "translations"
            if not os.path.exists(translations_dir):
                os.makedirs(translations_dir)
            
            translation_file = os.path.join(translations_dir, f"{language}.json")
            
            if translations is None:
                # Create basic translations (mostly English for now)
                translations = {
                    'welcome': f'Welcome to Our Rewards Platform! ({language.upper()})',
                    'balance': 'Balance',
                    'points': 'Points',
                    'earn': 'Earn',
                    'redeem': 'Redeem',
                    'casino': 'Casino',
                    'games': 'Games',
                    'play': 'Play',
                    'bet': 'Bet',
                    'win': 'Win',
                    'lose': 'Lose',
                    'insufficient_points': 'Insufficient points',
                    'daily_bonus': 'Daily Bonus',
                    'claim': 'Claim',
                    'streak': 'Streak',
                    'achievements': 'Achievements',
                    'leaderboard': 'Leaderboard',
                    'tournaments': 'Tournaments',
                    'friends': 'Friends',
                    'guild': 'Guild',
                    'profile': 'Profile',
                    'settings': 'Settings',
                    'language': 'Language',
                    'success': 'Success',
                    'error': 'Error',
                    'warning': 'Warning',
                    'info': 'Information',
                    'loading': 'Loading...',
                    'confirm': 'Confirm',
                    'cancel': 'Cancel',
                    'yes': 'Yes',
                    'no': 'No',
                    'ok': 'OK',
                    'close': 'Close',
                    'save': 'Save',
                    'delete': 'Delete',
                    'edit': 'Edit',
                    'add': 'Add',
                    'remove': 'Remove',
                    'search': 'Search',
                    'filter': 'Filter',
                    'refresh': 'Refresh',
                    'next': 'Next',
                    'previous': 'Previous',
                    'page': 'Page',
                    'of': 'of',
                    'total': 'Total',
                    'results': 'Results',
                    'no_results': 'No results found',
                    'try_again': 'Try again',
                    'help': 'Help',
                    'about': 'About',
                    'version': 'Version',
                    'status': 'Status',
                    'active': 'Active',
                    'inactive': 'Inactive',
                    'banned': 'Banned',
                    'suspended': 'Suspended',
                    'pending': 'Pending',
                    'completed': 'Completed',
                    'cancelled': 'Cancelled',
                    'level': 'Level',
                    'xp': 'XP',
                    'rank': 'Rank',
                    'score': 'Score',
                    'points_earned': 'Points Earned',
                    'games_played': 'Games Played',
                    'games_won': 'Games Won',
                    'win_rate': 'Win Rate',
                    'best_streak': 'Best Streak',
                    'current_streak': 'Current Streak',
                    'referrals': 'Referrals',
                    'referral_code': 'Referral Code',
                    'gift_cards': 'Gift Cards',
                    'amount': 'Amount',
                    'currency': 'Currency',
                    'category': 'Category',
                    'description': 'Description',
                    'name': 'Name',
                    'username': 'Username',
                    'avatar': 'Avatar',
                    'bio': 'Bio',
                    'join_date': 'Join Date',
                    'last_activity': 'Last Activity',
                    'total_earned': 'Total Earned',
                    'challenges': 'Challenges',
                    'daily_challenge': 'Daily Challenge',
                    'weekly_challenge': 'Weekly Challenge',
                    'monthly_challenge': 'Monthly Challenge',
                    'progress': 'Progress',
                    'requirement': 'Requirement',
                    'reward': 'Reward',
                    'bonus': 'Bonus',
                    'multiplier': 'Multiplier',
                    'special_event': 'Special Event',
                    'seasonal_event': 'Seasonal Event',
                    'holiday': 'Holiday',
                    'notification': 'Notification',
                    'email': 'Email',
                    'mobile': 'Mobile',
                    'desktop': 'Desktop',
                    'web': 'Web',
                    'api': 'API',
                    'rate_limit': 'Rate Limit',
                    'limit': 'Limit',
                    'exceeded': 'Exceeded',
                    'reset': 'Reset',
                    'expires': 'Expires',
                    'expired': 'Expired',
                    'valid': 'Valid',
                    'invalid': 'Invalid',
                    'required': 'Required',
                    'optional': 'Optional',
                    'public': 'Public',
                    'private': 'Private',
                    'hidden': 'Hidden',
                    'visible': 'Visible',
                    'enabled': 'Enabled',
                    'disabled': 'Disabled',
                    'on': 'On',
                    'off': 'Off',
                    'available': 'Available',
                    'unavailable': 'Unavailable',
                    'online': 'Online',
                    'offline': 'Offline'
                }
            
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
            
            # Load the new translations
            self.translations[language] = translations
            
        except Exception as e:
            logger.error(f"Error creating language file for {language}: {e}")
    
    def get_translation(self, key: str, language: str = None, **kwargs) -> str:
        """Get translation for a key"""
        try:
            if language is None:
                language = self.default_language
            
            if language not in self.translations:
                language = self.default_language
            
            translation = self.translations[language].get(key, key)
            
            # Replace placeholders
            if kwargs:
                for placeholder, value in kwargs.items():
                    translation = translation.replace(f'{{{placeholder}}}', str(value))
            
            return translation
            
        except Exception as e:
            logger.error(f"Error getting translation: {e}")
            return key
    
    def set_user_language(self, user_id: str, language: str) -> Dict[str, Any]:
        """Set user's preferred language"""
        try:
            with app.app_context():
                if language not in self.supported_languages:
                    return {"success": False, "error": "Unsupported language"}
                
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                
                # Store language preference in profile (we'll add this field)
                # For now, we'll use a simple approach
                profile.bio = f"Language: {language}" if not profile.bio else profile.bio
                
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Language set to {language}",
                    "language": language
                }
                
        except Exception as e:
            logger.error(f"Error setting user language: {e}")
            db.session.rollback()
            return {"success": False, "error": f"Failed to set language: {str(e)}"}
    
    def get_user_language(self, user_id: str) -> str:
        """Get user's preferred language"""
        try:
            with app.app_context():
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if profile and profile.bio and profile.bio.startswith("Language: "):
                    language = profile.bio.split("Language: ")[1]
                    if language in self.supported_languages:
                        return language
                
                return self.default_language
                
        except Exception as e:
            logger.error(f"Error getting user language: {e}")
            return self.default_language
    
    def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported languages"""
        language_names = {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'ru': 'Русский',
            'ja': '日本語',
            'ko': '한국어',
            'zh': '中文'
        }
        
        return {
            "success": True,
            "supported_languages": [
                {
                    "code": lang,
                    "name": language_names.get(lang, lang.upper()),
                    "is_default": lang == self.default_language
                }
                for lang in self.supported_languages
            ],
            "default_language": self.default_language
        }
    
    def update_translation(self, language: str, key: str, value: str) -> Dict[str, Any]:
        """Update a translation"""
        try:
            if language not in self.supported_languages:
                return {"success": False, "error": "Unsupported language"}
            
            if language not in self.translations:
                self.translations[language] = {}
            
            self.translations[language][key] = value
            
            # Save to file
            translations_dir = "translations"
            translation_file = os.path.join(translations_dir, f"{language}.json")
            
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(self.translations[language], f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "message": f"Translation updated for {language}: {key}",
                "language": language,
                "key": key,
                "value": value
            }
            
        except Exception as e:
            logger.error(f"Error updating translation: {e}")
            return {"success": False, "error": f"Failed to update translation: {str(e)}"}
    
    def get_translations_for_language(self, language: str) -> Dict[str, Any]:
        """Get all translations for a language"""
        try:
            if language not in self.supported_languages:
                return {"success": False, "error": "Unsupported language"}
            
            if language not in self.translations:
                return {"success": False, "error": "Language not loaded"}
            
            return {
                "success": True,
                "language": language,
                "translations": self.translations[language],
                "count": len(self.translations[language])
            }
            
        except Exception as e:
            logger.error(f"Error getting translations for language: {e}")
            return {"success": False, "error": f"Failed to get translations: {str(e)}"}
    
    def add_new_language(self, language_code: str, language_name: str) -> Dict[str, Any]:
        """Add a new supported language"""
        try:
            if language_code in self.supported_languages:
                return {"success": False, "error": "Language already supported"}
            
            self.supported_languages.append(language_code)
            self.create_language_file(language_code)
            
            return {
                "success": True,
                "message": f"Language {language_name} ({language_code}) added successfully",
                "language_code": language_code,
                "language_name": language_name
            }
            
        except Exception as e:
            logger.error(f"Error adding new language: {e}")
            return {"success": False, "error": f"Failed to add language: {str(e)}"}
    
    def remove_language(self, language_code: str) -> Dict[str, Any]:
        """Remove a supported language"""
        try:
            if language_code == self.default_language:
                return {"success": False, "error": "Cannot remove default language"}
            
            if language_code not in self.supported_languages:
                return {"success": False, "error": "Language not supported"}
            
            self.supported_languages.remove(language_code)
            
            # Remove translation file
            translations_dir = "translations"
            translation_file = os.path.join(translations_dir, f"{language_code}.json")
            if os.path.exists(translation_file):
                os.remove(translation_file)
            
            # Remove from memory
            if language_code in self.translations:
                del self.translations[language_code]
            
            return {
                "success": True,
                "message": f"Language {language_code} removed successfully",
                "language_code": language_code
            }
            
        except Exception as e:
            logger.error(f"Error removing language: {e}")
            return {"success": False, "error": f"Failed to remove language: {str(e)}"}
    
    def get_language_stats(self) -> Dict[str, Any]:
        """Get language usage statistics"""
        try:
            with app.app_context():
                # Count users by language preference
                language_counts = {}
                for language in self.supported_languages:
                    count = UserProfile.query.filter(
                        UserProfile.bio.like(f"Language: {language}%")
                    ).count()
                    language_counts[language] = count
                
                total_users = User.query.count()
                
                return {
                    "success": True,
                    "language_stats": {
                        "supported_languages": len(self.supported_languages),
                        "default_language": self.default_language,
                        "language_counts": language_counts,
                        "total_users": total_users,
                        "users_with_language_set": sum(language_counts.values())
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting language stats: {e}")
            return {"success": False, "error": f"Failed to get language stats: {str(e)}"}
    
    def translate_text(self, text: str, from_language: str, to_language: str) -> Dict[str, Any]:
        """Translate text between languages (placeholder for future implementation)"""
        # This would integrate with a translation service like Google Translate
        # For now, return the original text
        return {
            "success": True,
            "original_text": text,
            "translated_text": text,
            "from_language": from_language,
            "to_language": to_language,
            "note": "Translation service not implemented yet"
        }