"""
Tournament System Module
Handles tournaments, competitions, and prize distributions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import User, Tournament, TournamentParticipant, CasinoGame

logger = logging.getLogger(__name__)

class TournamentManager:
    """Manages tournaments and competitions"""
    
    @staticmethod
    def create_tournament(name: str, description: str, game_type: str, 
                         entry_fee: int, max_participants: int, 
                         duration_hours: int, created_by: str) -> Dict[str, Any]:
        """Create a new tournament"""
        try:
            with app.app_context():
                start_date = datetime.utcnow()
                end_date = start_date + timedelta(hours=duration_hours)
                
                # Calculate prize pool (entry fees + house bonus)
                house_bonus = entry_fee * max_participants // 10  # 10% house bonus
                prize_pool = (entry_fee * max_participants) + house_bonus
                
                tournament = Tournament(
                    name=name,
                    description=description,
                    game_type=game_type,
                    entry_fee=entry_fee,
                    max_participants=max_participants,
                    prize_pool=prize_pool,
                    start_date=start_date,
                    end_date=end_date,
                    created_by=created_by
                )
                
                db.session.add(tournament)
                db.session.commit()
                
                return {
                    "success": True,
                    "tournament_id": tournament.id,
                    "message": f"Tournament '{name}' created successfully"
                }
                
        except Exception as e:
            logger.error(f"Error creating tournament: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to create tournament"}
    
    @staticmethod
    def join_tournament(tournament_id: int, user_id: str) -> Dict[str, Any]:
        """Join a tournament"""
        try:
            with app.app_context():
                tournament = Tournament.query.get(tournament_id)
                if not tournament:
                    return {"success": False, "error": "Tournament not found"}
                
                # Check if tournament is still open
                if tournament.status != 'upcoming':
                    return {"success": False, "error": "Tournament is not accepting participants"}
                
                if datetime.utcnow() >= tournament.start_date:
                    return {"success": False, "error": "Tournament has already started"}
                
                # Check if user is already in tournament
                existing_participant = TournamentParticipant.query.filter_by(
                    tournament_id=tournament_id,
                    user_id=user_id
                ).first()
                
                if existing_participant:
                    return {"success": False, "error": "You are already in this tournament"}
                
                # Check if tournament is full
                current_participants = TournamentParticipant.query.filter_by(
                    tournament_id=tournament_id
                ).count()
                
                if current_participants >= tournament.max_participants:
                    return {"success": False, "error": "Tournament is full"}
                
                # Check user balance
                user = User.query.get(user_id)
                if not user:
                    return {"success": False, "error": "User not found"}
                
                if user.points_balance < tournament.entry_fee:
                    return {"success": False, "error": "Insufficient points for entry fee"}
                
                # Deduct entry fee
                user.points_balance -= tournament.entry_fee
                
                # Add participant
                participant = TournamentParticipant(
                    tournament_id=tournament_id,
                    user_id=user_id,
                    entry_fee_paid=True
                )
                db.session.add(participant)
                
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Successfully joined tournament '{tournament.name}'",
                    "entry_fee": tournament.entry_fee,
                    "new_balance": user.points_balance
                }
                
        except Exception as e:
            logger.error(f"Error joining tournament: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to join tournament"}
    
    @staticmethod
    def get_active_tournaments() -> Dict[str, Any]:
        """Get all active tournaments"""
        try:
            with app.app_context():
                now = datetime.utcnow()
                tournaments = Tournament.query.filter(
                    Tournament.status.in_(['upcoming', 'active']),
                    Tournament.end_date > now
                ).order_by(Tournament.start_date).all()
                
                tournament_list = []
                for tournament in tournaments:
                    # Get participant count
                    participant_count = TournamentParticipant.query.filter_by(
                        tournament_id=tournament.id
                    ).count()
                    
                    # Check if user can join
                    can_join = (
                        tournament.status == 'upcoming' and
                        now < tournament.start_date and
                        participant_count < tournament.max_participants
                    )
                    
                    tournament_list.append({
                        'id': tournament.id,
                        'name': tournament.name,
                        'description': tournament.description,
                        'game_type': tournament.game_type,
                        'entry_fee': tournament.entry_fee,
                        'max_participants': tournament.max_participants,
                        'current_participants': participant_count,
                        'prize_pool': tournament.prize_pool,
                        'start_date': tournament.start_date.isoformat(),
                        'end_date': tournament.end_date.isoformat(),
                        'status': tournament.status,
                        'can_join': can_join,
                        'time_until_start': (tournament.start_date - now).total_seconds() if tournament.status == 'upcoming' else 0,
                        'time_remaining': (tournament.end_date - now).total_seconds() if tournament.status == 'active' else 0
                    })
                
                return {
                    "success": True,
                    "tournaments": tournament_list
                }
                
        except Exception as e:
            logger.error(f"Error getting active tournaments: {e}")
            return {"success": False, "error": "Failed to get tournaments"}
    
    @staticmethod
    def get_tournament_details(tournament_id: int) -> Dict[str, Any]:
        """Get detailed tournament information"""
        try:
            with app.app_context():
                tournament = Tournament.query.get(tournament_id)
                if not tournament:
                    return {"success": False, "error": "Tournament not found"}
                
                # Get participants
                participants = TournamentParticipant.query.filter_by(
                    tournament_id=tournament_id
                ).order_by(TournamentParticipant.final_rank.asc().nullslast()).all()
                
                participant_list = []
                for participant in participants:
                    user = User.query.get(participant.user_id)
                    if user:
                        participant_list.append({
                            'user_id': participant.user_id,
                            'username': user.username,
                            'final_score': participant.final_score,
                            'final_rank': participant.final_rank,
                            'prize_earned': participant.prize_earned,
                            'joined_at': participant.joined_at.isoformat()
                        })
                
                return {
                    "success": True,
                    "tournament": {
                        'id': tournament.id,
                        'name': tournament.name,
                        'description': tournament.description,
                        'game_type': tournament.game_type,
                        'entry_fee': tournament.entry_fee,
                        'max_participants': tournament.max_participants,
                        'current_participants': len(participant_list),
                        'prize_pool': tournament.prize_pool,
                        'start_date': tournament.start_date.isoformat(),
                        'end_date': tournament.end_date.isoformat(),
                        'status': tournament.status,
                        'created_by': tournament.created_by,
                        'participants': participant_list
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting tournament details: {e}")
            return {"success": False, "error": "Failed to get tournament details"}
    
    @staticmethod
    def start_tournament(tournament_id: int) -> Dict[str, Any]:
        """Start a tournament"""
        try:
            with app.app_context():
                tournament = Tournament.query.get(tournament_id)
                if not tournament:
                    return {"success": False, "error": "Tournament not found"}
                
                if tournament.status != 'upcoming':
                    return {"success": False, "error": "Tournament is not in upcoming status"}
                
                if datetime.utcnow() < tournament.start_date:
                    return {"success": False, "error": "Tournament start time has not been reached"}
                
                # Check minimum participants
                participant_count = TournamentParticipant.query.filter_by(
                    tournament_id=tournament_id
                ).count()
                
                if participant_count < 2:
                    # Cancel tournament if not enough participants
                    tournament.status = 'cancelled'
                    db.session.commit()
                    return {"success": False, "error": "Tournament cancelled due to insufficient participants"}
                
                # Start tournament
                tournament.status = 'active'
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Tournament '{tournament.name}' has started!",
                    "participant_count": participant_count
                }
                
        except Exception as e:
            logger.error(f"Error starting tournament: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to start tournament"}
    
    @staticmethod
    def end_tournament(tournament_id: int) -> Dict[str, Any]:
        """End a tournament and distribute prizes"""
        try:
            with app.app_context():
                tournament = Tournament.query.get(tournament_id)
                if not tournament:
                    return {"success": False, "error": "Tournament not found"}
                
                if tournament.status != 'active':
                    return {"success": False, "error": "Tournament is not active"}
                
                # Get participants with their scores
                participants = TournamentParticipant.query.filter_by(
                    tournament_id=tournament_id
                ).all()
                
                if not participants:
                    tournament.status = 'completed'
                    db.session.commit()
                    return {"success": True, "message": "Tournament ended with no participants"}
                
                # Calculate scores based on game type
                for participant in participants:
                    score = TournamentManager._calculate_tournament_score(
                        participant.user_id, tournament.game_type, tournament.start_date, tournament.end_date
                    )
                    participant.final_score = score
                
                # Sort by score (descending)
                participants.sort(key=lambda p: p.final_score, reverse=True)
                
                # Assign ranks and distribute prizes
                prize_distribution = TournamentManager._calculate_prize_distribution(
                    tournament.prize_pool, len(participants)
                )
                
                for i, participant in enumerate(participants):
                    participant.final_rank = i + 1
                    if i < len(prize_distribution):
                        participant.prize_earned = prize_distribution[i]
                        
                        # Award prize to user
                        user = User.query.get(participant.user_id)
                        if user and participant.prize_earned > 0:
                            user.points_balance += participant.prize_earned
                            user.total_earned += participant.prize_earned
                
                # Mark tournament as completed
                tournament.status = 'completed'
                db.session.commit()
                
                return {
                    "success": True,
                    "message": f"Tournament '{tournament.name}' completed!",
                    "participant_count": len(participants),
                    "prize_distributed": sum(prize_distribution)
                }
                
        except Exception as e:
            logger.error(f"Error ending tournament: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to end tournament"}
    
    @staticmethod
    def _calculate_tournament_score(user_id: str, game_type: str, start_date: datetime, end_date: datetime) -> int:
        """Calculate user's tournament score"""
        try:
            if game_type == 'dice':
                # Score based on total winnings from dice games
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.game_type == 'dice',
                    CasinoGame.played_at >= start_date,
                    CasinoGame.played_at <= end_date
                ).all()
                return sum(game.win_amount for game in games)
            
            elif game_type == 'slots':
                # Score based on total winnings from slot games
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.game_type == 'slots',
                    CasinoGame.played_at >= start_date,
                    CasinoGame.played_at <= end_date
                ).all()
                return sum(game.win_amount for game in games)
            
            elif game_type == 'blackjack':
                # Score based on total winnings from blackjack games
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.game_type == 'blackjack',
                    CasinoGame.played_at >= start_date,
                    CasinoGame.played_at <= end_date
                ).all()
                return sum(game.win_amount for game in games)
            
            elif game_type == 'roulette':
                # Score based on total winnings from roulette games
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.game_type == 'roulette',
                    CasinoGame.played_at >= start_date,
                    CasinoGame.played_at <= end_date
                ).all()
                return sum(game.win_amount for game in games)
            
            elif game_type == 'poker':
                # Score based on total winnings from poker games
                games = CasinoGame.query.filter(
                    CasinoGame.user_id == user_id,
                    CasinoGame.game_type == 'poker',
                    CasinoGame.played_at >= start_date,
                    CasinoGame.played_at <= end_date
                ).all()
                return sum(game.win_amount for game in games)
            
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error calculating tournament score: {e}")
            return 0
    
    @staticmethod
    def _calculate_prize_distribution(prize_pool: int, participant_count: int) -> List[int]:
        """Calculate prize distribution based on participant count"""
        if participant_count == 0:
            return []
        
        # Prize distribution percentages
        if participant_count == 1:
            return [prize_pool]
        elif participant_count == 2:
            return [int(prize_pool * 0.7), int(prize_pool * 0.3)]
        elif participant_count == 3:
            return [int(prize_pool * 0.5), int(prize_pool * 0.3), int(prize_pool * 0.2)]
        elif participant_count >= 4:
            # Top 4 get prizes
            prizes = [
                int(prize_pool * 0.4),  # 1st place
                int(prize_pool * 0.25), # 2nd place
                int(prize_pool * 0.2),  # 3rd place
                int(prize_pool * 0.15)  # 4th place
            ]
            # Add small consolation prizes for remaining participants
            remaining_prize = prize_pool - sum(prizes)
            consolation_prize = remaining_prize // max(1, participant_count - 4)
            
            for i in range(4, participant_count):
                prizes.append(consolation_prize)
            
            return prizes
        
        return []
    
    @staticmethod
    def get_user_tournaments(user_id: str) -> Dict[str, Any]:
        """Get tournaments user has participated in"""
        try:
            with app.app_context():
                participants = TournamentParticipant.query.filter_by(user_id=user_id).all()
                
                tournament_list = []
                for participant in participants:
                    tournament = Tournament.query.get(participant.tournament_id)
                    if tournament:
                        tournament_list.append({
                            'id': tournament.id,
                            'name': tournament.name,
                            'game_type': tournament.game_type,
                            'entry_fee': tournament.entry_fee,
                            'final_score': participant.final_score,
                            'final_rank': participant.final_rank,
                            'prize_earned': participant.prize_earned,
                            'status': tournament.status,
                            'start_date': tournament.start_date.isoformat(),
                            'end_date': tournament.end_date.isoformat(),
                            'joined_at': participant.joined_at.isoformat()
                        })
                
                # Sort by joined date (newest first)
                tournament_list.sort(key=lambda x: x['joined_at'], reverse=True)
                
                return {
                    "success": True,
                    "tournaments": tournament_list
                }
                
        except Exception as e:
            logger.error(f"Error getting user tournaments: {e}")
            return {"success": False, "error": "Failed to get user tournaments"}