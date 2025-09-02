"""
Backup and Restore System Module
Handles database backups, exports, and restoration
"""

import logging
import json
import csv
import os
import zipfile
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, UserProfile, CasinoGame, AdCompletion, GiftCard, Referral, DailyBonus, Guild, Tournament, Achievement, Challenge, Leaderboard

logger = logging.getLogger(__name__)

class BackupRestoreManager:
    """Manages database backups and restoration"""
    
    def __init__(self):
        self.backup_directory = "backups"
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_directory):
            os.makedirs(self.backup_directory)
    
    def create_full_backup(self, backup_name: str = None) -> Dict[str, Any]:
        """Create a full database backup"""
        try:
            with app.app_context():
                if not backup_name:
                    backup_name = f"full_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                
                backup_data = {
                    "backup_info": {
                        "name": backup_name,
                        "created_at": datetime.utcnow().isoformat(),
                        "type": "full_backup",
                        "version": "1.0"
                    },
                    "users": self._export_users(),
                    "user_profiles": self._export_user_profiles(),
                    "casino_games": self._export_casino_games(),
                    "ad_completions": self._export_ad_completions(),
                    "gift_cards": self._export_gift_cards(),
                    "referrals": self._export_referrals(),
                    "daily_bonuses": self._export_daily_bonuses(),
                    "guilds": self._export_guilds(),
                    "tournaments": self._export_tournaments(),
                    "achievements": self._export_achievements(),
                    "challenges": self._export_challenges(),
                    "leaderboards": self._export_leaderboards()
                }
                
                # Save backup to file
                backup_file = os.path.join(self.backup_directory, f"{backup_name}.json")
                with open(backup_file, 'w') as f:
                    json.dump(backup_data, f, indent=2, default=str)
                
                # Create compressed backup
                zip_file = os.path.join(self.backup_directory, f"{backup_name}.zip")
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_file, f"{backup_name}.json")
                
                # Remove uncompressed file
                os.remove(backup_file)
                
                return {
                    "success": True,
                    "backup_name": backup_name,
                    "backup_file": zip_file,
                    "backup_size": os.path.getsize(zip_file),
                    "created_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creating full backup: {e}")
            return {"success": False, "error": f"Failed to create backup: {str(e)}"}
    
    def create_incremental_backup(self, backup_name: str = None, days: int = 1) -> Dict[str, Any]:
        """Create an incremental backup of recent data"""
        try:
            with app.app_context():
                if not backup_name:
                    backup_name = f"incremental_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                backup_data = {
                    "backup_info": {
                        "name": backup_name,
                        "created_at": datetime.utcnow().isoformat(),
                        "type": "incremental_backup",
                        "days": days,
                        "cutoff_date": cutoff_date.isoformat()
                    },
                    "users": self._export_users(cutoff_date),
                    "user_profiles": self._export_user_profiles(cutoff_date),
                    "casino_games": self._export_casino_games(cutoff_date),
                    "ad_completions": self._export_ad_completions(cutoff_date),
                    "gift_cards": self._export_gift_cards(cutoff_date),
                    "referrals": self._export_referrals(cutoff_date),
                    "daily_bonuses": self._export_daily_bonuses(cutoff_date),
                    "guilds": self._export_guilds(cutoff_date),
                    "tournaments": self._export_tournaments(cutoff_date)
                }
                
                # Save backup to file
                backup_file = os.path.join(self.backup_directory, f"{backup_name}.json")
                with open(backup_file, 'w') as f:
                    json.dump(backup_data, f, indent=2, default=str)
                
                # Create compressed backup
                zip_file = os.path.join(self.backup_directory, f"{backup_name}.zip")
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_file, f"{backup_name}.json")
                
                # Remove uncompressed file
                os.remove(backup_file)
                
                return {
                    "success": True,
                    "backup_name": backup_name,
                    "backup_file": zip_file,
                    "backup_size": os.path.getsize(zip_file),
                    "created_at": datetime.utcnow().isoformat(),
                    "days": days
                }
                
        except Exception as e:
            logger.error(f"Error creating incremental backup: {e}")
            return {"success": False, "error": f"Failed to create incremental backup: {str(e)}"}
    
    def restore_from_backup(self, backup_file: str, restore_type: str = 'full') -> Dict[str, Any]:
        """Restore database from backup"""
        try:
            with app.app_context():
                # Extract backup file if it's compressed
                if backup_file.endswith('.zip'):
                    with zipfile.ZipFile(backup_file, 'r') as zipf:
                        json_file = zipf.namelist()[0]
                        backup_data = json.loads(zipf.read(json_file))
                else:
                    with open(backup_file, 'r') as f:
                        backup_data = json.load(f)
                
                backup_info = backup_data.get('backup_info', {})
                restored_tables = []
                
                # Restore users
                if 'users' in backup_data:
                    restored_count = self._restore_users(backup_data['users'])
                    restored_tables.append(f"users: {restored_count}")
                
                # Restore user profiles
                if 'user_profiles' in backup_data:
                    restored_count = self._restore_user_profiles(backup_data['user_profiles'])
                    restored_tables.append(f"user_profiles: {restored_count}")
                
                # Restore casino games
                if 'casino_games' in backup_data:
                    restored_count = self._restore_casino_games(backup_data['casino_games'])
                    restored_tables.append(f"casino_games: {restored_count}")
                
                # Restore ad completions
                if 'ad_completions' in backup_data:
                    restored_count = self._restore_ad_completions(backup_data['ad_completions'])
                    restored_tables.append(f"ad_completions: {restored_count}")
                
                # Restore gift cards
                if 'gift_cards' in backup_data:
                    restored_count = self._restore_gift_cards(backup_data['gift_cards'])
                    restored_tables.append(f"gift_cards: {restored_count}")
                
                # Restore referrals
                if 'referrals' in backup_data:
                    restored_count = self._restore_referrals(backup_data['referrals'])
                    restored_tables.append(f"referrals: {restored_count}")
                
                # Restore daily bonuses
                if 'daily_bonuses' in backup_data:
                    restored_count = self._restore_daily_bonuses(backup_data['daily_bonuses'])
                    restored_tables.append(f"daily_bonuses: {restored_count}")
                
                # Restore guilds
                if 'guilds' in backup_data:
                    restored_count = self._restore_guilds(backup_data['guilds'])
                    restored_tables.append(f"guilds: {restored_count}")
                
                # Restore tournaments
                if 'tournaments' in backup_data:
                    restored_count = self._restore_tournaments(backup_data['tournaments'])
                    restored_tables.append(f"tournaments: {restored_count}")
                
                db.session.commit()
                
                return {
                    "success": True,
                    "backup_name": backup_info.get('name', 'unknown'),
                    "backup_created": backup_info.get('created_at', 'unknown'),
                    "restored_tables": restored_tables,
                    "restored_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            db.session.rollback()
            return {"success": False, "error": f"Failed to restore from backup: {str(e)}"}
    
    def export_to_csv(self, table_name: str, output_file: str = None) -> Dict[str, Any]:
        """Export table data to CSV"""
        try:
            with app.app_context():
                if not output_file:
                    output_file = os.path.join(self.backup_directory, f"{table_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv")
                
                # Get table data
                if table_name == 'users':
                    data = self._export_users()
                elif table_name == 'casino_games':
                    data = self._export_casino_games()
                elif table_name == 'gift_cards':
                    data = self._export_gift_cards()
                else:
                    return {"success": False, "error": f"Table {table_name} not supported for CSV export"}
                
                if not data:
                    return {"success": False, "error": "No data to export"}
                
                # Write to CSV
                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                
                return {
                    "success": True,
                    "table_name": table_name,
                    "output_file": output_file,
                    "record_count": len(data),
                    "file_size": os.path.getsize(output_file)
                }
                
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return {"success": False, "error": f"Failed to export to CSV: {str(e)}"}
    
    def list_backups(self) -> Dict[str, Any]:
        """List all available backups"""
        try:
            backups = []
            
            for filename in os.listdir(self.backup_directory):
                if filename.endswith('.zip'):
                    filepath = os.path.join(self.backup_directory, filename)
                    file_stats = os.stat(filepath)
                    
                    backups.append({
                        "filename": filename,
                        "size": file_stats.st_size,
                        "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                "success": True,
                "backups": backups,
                "count": len(backups)
            }
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return {"success": False, "error": f"Failed to list backups: {str(e)}"}
    
    def delete_backup(self, backup_filename: str) -> Dict[str, Any]:
        """Delete a backup file"""
        try:
            backup_path = os.path.join(self.backup_directory, backup_filename)
            
            if not os.path.exists(backup_path):
                return {"success": False, "error": "Backup file not found"}
            
            os.remove(backup_path)
            
            return {
                "success": True,
                "message": f"Backup {backup_filename} deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return {"success": False, "error": f"Failed to delete backup: {str(e)}"}
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for filename in os.listdir(self.backup_directory):
                if filename.endswith('.zip'):
                    filepath = os.path.join(self.backup_directory, filename)
                    file_created = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    if file_created < cutoff_date:
                        os.remove(filepath)
                        deleted_count += 1
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "days_to_keep": days_to_keep,
                "message": f"Deleted {deleted_count} old backup files"
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return {"success": False, "error": f"Failed to cleanup old backups: {str(e)}"}
    
    # Export methods for each table
    def _export_users(self, cutoff_date: datetime = None):
        """Export users data"""
        query = User.query
        if cutoff_date:
            query = query.filter(User.created_at >= cutoff_date)
        return [self._user_to_dict(user) for user in query.all()]
    
    def _export_user_profiles(self, cutoff_date: datetime = None):
        """Export user profiles data"""
        query = UserProfile.query
        if cutoff_date:
            query = query.filter(UserProfile.created_at >= cutoff_date)
        return [self._user_profile_to_dict(profile) for profile in query.all()]
    
    def _export_casino_games(self, cutoff_date: datetime = None):
        """Export casino games data"""
        query = CasinoGame.query
        if cutoff_date:
            query = query.filter(CasinoGame.played_at >= cutoff_date)
        return [self._casino_game_to_dict(game) for game in query.all()]
    
    def _export_ad_completions(self, cutoff_date: datetime = None):
        """Export ad completions data"""
        query = AdCompletion.query
        if cutoff_date:
            query = query.filter(AdCompletion.completed_at >= cutoff_date)
        return [self._ad_completion_to_dict(ad) for ad in query.all()]
    
    def _export_gift_cards(self, cutoff_date: datetime = None):
        """Export gift cards data"""
        query = GiftCard.query
        if cutoff_date:
            query = query.filter(GiftCard.created_at >= cutoff_date)
        return [self._gift_card_to_dict(card) for card in query.all()]
    
    def _export_referrals(self, cutoff_date: datetime = None):
        """Export referrals data"""
        query = Referral.query
        if cutoff_date:
            query = query.filter(Referral.created_at >= cutoff_date)
        return [self._referral_to_dict(ref) for ref in query.all()]
    
    def _export_daily_bonuses(self, cutoff_date: datetime = None):
        """Export daily bonuses data"""
        query = DailyBonus.query
        if cutoff_date:
            query = query.filter(DailyBonus.created_at >= cutoff_date)
        return [self._daily_bonus_to_dict(bonus) for bonus in query.all()]
    
    def _export_guilds(self, cutoff_date: datetime = None):
        """Export guilds data"""
        query = Guild.query
        if cutoff_date:
            query = query.filter(Guild.created_at >= cutoff_date)
        return [self._guild_to_dict(guild) for guild in query.all()]
    
    def _export_tournaments(self, cutoff_date: datetime = None):
        """Export tournaments data"""
        query = Tournament.query
        if cutoff_date:
            query = query.filter(Tournament.created_at >= cutoff_date)
        return [self._tournament_to_dict(tournament) for tournament in query.all()]
    
    def _export_achievements(self, cutoff_date: datetime = None):
        """Export achievements data"""
        query = Achievement.query
        if cutoff_date:
            query = query.filter(Achievement.created_at >= cutoff_date)
        return [self._achievement_to_dict(achievement) for achievement in query.all()]
    
    def _export_challenges(self, cutoff_date: datetime = None):
        """Export challenges data"""
        query = Challenge.query
        if cutoff_date:
            query = query.filter(Challenge.created_at >= cutoff_date)
        return [self._challenge_to_dict(challenge) for challenge in query.all()]
    
    def _export_leaderboards(self, cutoff_date: datetime = None):
        """Export leaderboards data"""
        query = Leaderboard.query
        if cutoff_date:
            query = query.filter(Leaderboard.created_at >= cutoff_date)
        return [self._leaderboard_to_dict(leaderboard) for leaderboard in query.all()]
    
    # Convert model objects to dictionaries
    def _user_to_dict(self, user):
        return {
            'id': user.id,
            'username': user.username,
            'points_balance': user.points_balance,
            'total_earned': user.total_earned,
            'user_status': user.user_status,
            'ban_reason': user.ban_reason,
            'banned_at': user.banned_at.isoformat() if user.banned_at else None,
            'banned_by': user.banned_by,
            'last_activity': user.last_activity.isoformat() if user.last_activity else None,
            'total_games_played': user.total_games_played,
            'total_gift_cards_redeemed': user.total_gift_cards_redeemed,
            'created_at': user.created_at.isoformat()
        }
    
    def _user_profile_to_dict(self, profile):
        return {
            'id': profile.id,
            'user_id': profile.user_id,
            'avatar_url': profile.avatar_url,
            'bio': profile.bio,
            'level': profile.level,
            'xp': profile.xp,
            'xp_to_next_level': profile.xp_to_next_level,
            'total_wins': profile.total_wins,
            'total_losses': profile.total_losses,
            'win_streak': profile.win_streak,
            'best_win_streak': profile.best_win_streak,
            'favorite_game': profile.favorite_game,
            'created_at': profile.created_at.isoformat(),
            'updated_at': profile.updated_at.isoformat()
        }
    
    def _casino_game_to_dict(self, game):
        return {
            'id': game.id,
            'user_id': game.user_id,
            'game_type': game.game_type,
            'bet_amount': game.bet_amount,
            'win_amount': game.win_amount,
            'result': game.result,
            'played_at': game.played_at.isoformat()
        }
    
    def _ad_completion_to_dict(self, ad):
        return {
            'id': ad.id,
            'user_id': ad.user_id,
            'ad_id': ad.ad_id,
            'points_earned': ad.points_earned,
            'completed_at': ad.completed_at.isoformat()
        }
    
    def _gift_card_to_dict(self, card):
        return {
            'id': card.id,
            'code': card.code,
            'amount': card.amount,
            'currency': card.currency,
            'category_id': card.category_id,
            'used': card.used,
            'used_by': card.used_by,
            'used_at': card.used_at.isoformat() if card.used_at else None,
            'created_at': card.created_at.isoformat()
        }
    
    def _referral_to_dict(self, ref):
        return {
            'id': ref.id,
            'referrer_id': ref.referrer_id,
            'referred_id': ref.referred_id,
            'referral_code': ref.referral_code,
            'points_earned': ref.points_earned,
            'is_active': ref.is_active,
            'created_at': ref.created_at.isoformat()
        }
    
    def _daily_bonus_to_dict(self, bonus):
        return {
            'id': bonus.id,
            'user_id': bonus.user_id,
            'current_streak': bonus.current_streak,
            'best_streak': bonus.best_streak,
            'last_claim_date': bonus.last_claim_date.isoformat() if bonus.last_claim_date else None,
            'total_claimed': bonus.total_claimed,
            'created_at': bonus.created_at.isoformat(),
            'updated_at': bonus.updated_at.isoformat()
        }
    
    def _guild_to_dict(self, guild):
        return {
            'id': guild.id,
            'name': guild.name,
            'description': guild.description,
            'owner_id': guild.owner_id,
            'icon_url': guild.icon_url,
            'level': guild.level,
            'xp': guild.xp,
            'total_points': guild.total_points,
            'member_count': guild.member_count,
            'max_members': guild.max_members,
            'is_active': guild.is_active,
            'created_at': guild.created_at.isoformat()
        }
    
    def _tournament_to_dict(self, tournament):
        return {
            'id': tournament.id,
            'name': tournament.name,
            'description': tournament.description,
            'game_type': tournament.game_type,
            'entry_fee': tournament.entry_fee,
            'max_participants': tournament.max_participants,
            'prize_pool': tournament.prize_pool,
            'start_date': tournament.start_date.isoformat(),
            'end_date': tournament.end_date.isoformat(),
            'status': tournament.status,
            'created_by': tournament.created_by,
            'created_at': tournament.created_at.isoformat()
        }
    
    def _achievement_to_dict(self, achievement):
        return {
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon,
            'category': achievement.category,
            'requirement_type': achievement.requirement_type,
            'requirement_value': achievement.requirement_value,
            'points_reward': achievement.points_reward,
            'is_hidden': achievement.is_hidden,
            'is_active': achievement.is_active,
            'created_at': achievement.created_at.isoformat()
        }
    
    def _challenge_to_dict(self, challenge):
        return {
            'id': challenge.id,
            'name': challenge.name,
            'description': challenge.description,
            'challenge_type': challenge.challenge_type,
            'requirement_type': challenge.requirement_type,
            'requirement_value': challenge.requirement_value,
            'points_reward': challenge.points_reward,
            'bonus_multiplier': challenge.bonus_multiplier,
            'start_date': challenge.start_date.isoformat(),
            'end_date': challenge.end_date.isoformat(),
            'is_active': challenge.is_active,
            'created_at': challenge.created_at.isoformat()
        }
    
    def _leaderboard_to_dict(self, leaderboard):
        return {
            'id': leaderboard.id,
            'name': leaderboard.name,
            'description': leaderboard.description,
            'leaderboard_type': leaderboard.leaderboard_type,
            'period': leaderboard.period,
            'is_active': leaderboard.is_active,
            'created_at': leaderboard.created_at.isoformat()
        }
    
    # Restore methods for each table
    def _restore_users(self, users_data):
        """Restore users data"""
        restored_count = 0
        for user_data in users_data:
            existing_user = User.query.get(user_data['id'])
            if not existing_user:
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    points_balance=user_data['points_balance'],
                    total_earned=user_data['total_earned'],
                    user_status=user_data['user_status'],
                    ban_reason=user_data.get('ban_reason'),
                    banned_at=datetime.fromisoformat(user_data['banned_at']) if user_data.get('banned_at') else None,
                    banned_by=user_data.get('banned_by'),
                    last_activity=datetime.fromisoformat(user_data['last_activity']) if user_data.get('last_activity') else None,
                    total_games_played=user_data.get('total_games_played', 0),
                    total_gift_cards_redeemed=user_data.get('total_gift_cards_redeemed', 0),
                    created_at=datetime.fromisoformat(user_data['created_at'])
                )
                db.session.add(user)
                restored_count += 1
        return restored_count
    
    def _restore_user_profiles(self, profiles_data):
        """Restore user profiles data"""
        restored_count = 0
        for profile_data in profiles_data:
            existing_profile = UserProfile.query.filter_by(user_id=profile_data['user_id']).first()
            if not existing_profile:
                profile = UserProfile(
                    user_id=profile_data['user_id'],
                    avatar_url=profile_data.get('avatar_url'),
                    bio=profile_data.get('bio'),
                    level=profile_data.get('level', 1),
                    xp=profile_data.get('xp', 0),
                    xp_to_next_level=profile_data.get('xp_to_next_level', 100),
                    total_wins=profile_data.get('total_wins', 0),
                    total_losses=profile_data.get('total_losses', 0),
                    win_streak=profile_data.get('win_streak', 0),
                    best_win_streak=profile_data.get('best_win_streak', 0),
                    favorite_game=profile_data.get('favorite_game'),
                    created_at=datetime.fromisoformat(profile_data['created_at']),
                    updated_at=datetime.fromisoformat(profile_data['updated_at'])
                )
                db.session.add(profile)
                restored_count += 1
        return restored_count
    
    def _restore_casino_games(self, games_data):
        """Restore casino games data"""
        restored_count = 0
        for game_data in games_data:
            game = CasinoGame(
                user_id=game_data['user_id'],
                game_type=game_data['game_type'],
                bet_amount=game_data['bet_amount'],
                win_amount=game_data['win_amount'],
                result=game_data['result'],
                played_at=datetime.fromisoformat(game_data['played_at'])
            )
            db.session.add(game)
            restored_count += 1
        return restored_count
    
    def _restore_ad_completions(self, ads_data):
        """Restore ad completions data"""
        restored_count = 0
        for ad_data in ads_data:
            ad = AdCompletion(
                user_id=ad_data['user_id'],
                ad_id=ad_data['ad_id'],
                points_earned=ad_data['points_earned'],
                completed_at=datetime.fromisoformat(ad_data['completed_at'])
            )
            db.session.add(ad)
            restored_count += 1
        return restored_count
    
    def _restore_gift_cards(self, cards_data):
        """Restore gift cards data"""
        restored_count = 0
        for card_data in cards_data:
            card = GiftCard(
                code=card_data['code'],
                amount=card_data['amount'],
                currency=card_data.get('currency', 'Robux'),
                category_id=card_data.get('category_id'),
                used=card_data['used'],
                used_by=card_data.get('used_by'),
                used_at=datetime.fromisoformat(card_data['used_at']) if card_data.get('used_at') else None,
                created_at=datetime.fromisoformat(card_data['created_at'])
            )
            db.session.add(card)
            restored_count += 1
        return restored_count
    
    def _restore_referrals(self, referrals_data):
        """Restore referrals data"""
        restored_count = 0
        for ref_data in referrals_data:
            ref = Referral(
                referrer_id=ref_data['referrer_id'],
                referred_id=ref_data['referred_id'],
                referral_code=ref_data['referral_code'],
                points_earned=ref_data.get('points_earned', 0),
                is_active=ref_data.get('is_active', True),
                created_at=datetime.fromisoformat(ref_data['created_at'])
            )
            db.session.add(ref)
            restored_count += 1
        return restored_count
    
    def _restore_daily_bonuses(self, bonuses_data):
        """Restore daily bonuses data"""
        restored_count = 0
        for bonus_data in bonuses_data:
            bonus = DailyBonus(
                user_id=bonus_data['user_id'],
                current_streak=bonus_data.get('current_streak', 0),
                best_streak=bonus_data.get('best_streak', 0),
                last_claim_date=datetime.fromisoformat(bonus_data['last_claim_date']).date() if bonus_data.get('last_claim_date') else None,
                total_claimed=bonus_data.get('total_claimed', 0),
                created_at=datetime.fromisoformat(bonus_data['created_at']),
                updated_at=datetime.fromisoformat(bonus_data['updated_at'])
            )
            db.session.add(bonus)
            restored_count += 1
        return restored_count
    
    def _restore_guilds(self, guilds_data):
        """Restore guilds data"""
        restored_count = 0
        for guild_data in guilds_data:
            guild = Guild(
                name=guild_data['name'],
                description=guild_data.get('description'),
                owner_id=guild_data['owner_id'],
                icon_url=guild_data.get('icon_url'),
                level=guild_data.get('level', 1),
                xp=guild_data.get('xp', 0),
                total_points=guild_data.get('total_points', 0),
                member_count=guild_data.get('member_count', 1),
                max_members=guild_data.get('max_members', 50),
                is_active=guild_data.get('is_active', True),
                created_at=datetime.fromisoformat(guild_data['created_at'])
            )
            db.session.add(guild)
            restored_count += 1
        return restored_count
    
    def _restore_tournaments(self, tournaments_data):
        """Restore tournaments data"""
        restored_count = 0
        for tournament_data in tournaments_data:
            tournament = Tournament(
                name=tournament_data['name'],
                description=tournament_data.get('description'),
                game_type=tournament_data['game_type'],
                entry_fee=tournament_data['entry_fee'],
                max_participants=tournament_data['max_participants'],
                prize_pool=tournament_data['prize_pool'],
                start_date=datetime.fromisoformat(tournament_data['start_date']),
                end_date=datetime.fromisoformat(tournament_data['end_date']),
                status=tournament_data.get('status', 'upcoming'),
                created_by=tournament_data['created_by'],
                created_at=datetime.fromisoformat(tournament_data['created_at'])
            )
            db.session.add(tournament)
            restored_count += 1
        return restored_count