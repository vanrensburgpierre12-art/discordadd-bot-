"""
Advanced Casino Games Module
Implements Roulette, Poker, and Lottery games
"""

import random
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from app_context import app, db
from database import User, CasinoGame, DailyCasinoLimit, UserProfile

logger = logging.getLogger(__name__)

class RouletteGame:
    """Roulette game implementation"""
    
    @staticmethod
    def play(user_id: str, bet_amount: int, bet_type: str, bet_value: str) -> Dict[str, Any]:
        """
        Play roulette game
        bet_type: 'number', 'color', 'even_odd', 'high_low', 'dozen', 'column'
        bet_value: specific value based on bet_type
        """
        try:
            with app.app_context():
                # Check user status and balance
                user = User.query.filter_by(id=user_id).first()
                if not user:
                    return {"success": False, "error": "User not found"}
                
                if user.user_status != 'active':
                    return {"success": False, "error": "User account is not active"}
                
                if user.points_balance < bet_amount:
                    return {"success": False, "error": "Insufficient points"}
                
                # Check daily limits
                daily_limit = DailyCasinoLimit.query.filter_by(user_id=user_id).first()
                if not daily_limit:
                    daily_limit = DailyCasinoLimit(user_id=user_id)
                    db.session.add(daily_limit)
                
                if daily_limit.total_won + daily_limit.total_lost + bet_amount > 1000:
                    return {"success": False, "error": "Daily casino limit reached"}
                
                # Spin the wheel (0-36, where 0 is green)
                winning_number = random.randint(0, 36)
                
                # Determine win/loss and payout
                win_amount = RouletteGame._calculate_payout(bet_type, bet_value, winning_number, bet_amount)
                
                # Update user balance
                user.points_balance -= bet_amount
                if win_amount > 0:
                    user.points_balance += win_amount
                    user.total_earned += win_amount
                
                # Update daily limits
                daily_limit.games_played += 1
                if win_amount > 0:
                    daily_limit.total_won += win_amount
                else:
                    daily_limit.total_lost += bet_amount
                
                # Record game
                game_result = f"Bet: {bet_type} {bet_value}, Winning Number: {winning_number}, Payout: {win_amount}"
                casino_game = CasinoGame(
                    user_id=user_id,
                    game_type='roulette',
                    bet_amount=bet_amount,
                    win_amount=win_amount,
                    result=game_result
                )
                db.session.add(casino_game)
                
                # Update user profile
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                
                if win_amount > 0:
                    profile.total_wins += 1
                    profile.win_streak += 1
                    if profile.win_streak > profile.best_win_streak:
                        profile.best_win_streak = profile.win_streak
                else:
                    profile.total_losses += 1
                    profile.win_streak = 0
                
                profile.favorite_game = 'roulette'
                profile.xp += bet_amount // 10  # XP based on bet amount
                
                db.session.commit()
                
                return {
                    "success": True,
                    "winning_number": winning_number,
                    "bet_type": bet_type,
                    "bet_value": bet_value,
                    "bet_amount": bet_amount,
                    "win_amount": win_amount,
                    "result": "win" if win_amount > 0 else "lose",
                    "new_balance": user.points_balance
                }
                
        except Exception as e:
            logger.error(f"Error in roulette game: {e}")
            db.session.rollback()
            return {"success": False, "error": "Game error occurred"}
    
    @staticmethod
    def _calculate_payout(bet_type: str, bet_value: str, winning_number: int, bet_amount: int) -> int:
        """Calculate payout based on bet type and winning number"""
        
        # Determine number properties
        is_red = winning_number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        is_black = winning_number in [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        is_green = winning_number == 0
        is_even = winning_number != 0 and winning_number % 2 == 0
        is_odd = winning_number % 2 == 1
        is_high = 19 <= winning_number <= 36
        is_low = 1 <= winning_number <= 18
        
        if bet_type == 'number':
            # Direct number bet (35:1 payout)
            if str(winning_number) == bet_value:
                return bet_amount * 36  # 35:1 + original bet
            return 0
            
        elif bet_type == 'color':
            if bet_value == 'red' and is_red:
                return bet_amount * 2  # 1:1 payout
            elif bet_value == 'black' and is_black:
                return bet_amount * 2  # 1:1 payout
            elif bet_value == 'green' and is_green:
                return bet_amount * 36  # 35:1 payout
            return 0
            
        elif bet_type == 'even_odd':
            if bet_value == 'even' and is_even:
                return bet_amount * 2  # 1:1 payout
            elif bet_value == 'odd' and is_odd:
                return bet_amount * 2  # 1:1 payout
            return 0
            
        elif bet_type == 'high_low':
            if bet_value == 'high' and is_high:
                return bet_amount * 2  # 1:1 payout
            elif bet_value == 'low' and is_low:
                return bet_amount * 2  # 1:1 payout
            return 0
            
        elif bet_type == 'dozen':
            # First dozen (1-12), Second dozen (13-24), Third dozen (25-36)
            if bet_value == 'first' and 1 <= winning_number <= 12:
                return bet_amount * 3  # 2:1 payout
            elif bet_value == 'second' and 13 <= winning_number <= 24:
                return bet_amount * 3  # 2:1 payout
            elif bet_value == 'third' and 25 <= winning_number <= 36:
                return bet_amount * 3  # 2:1 payout
            return 0
            
        elif bet_type == 'column':
            # Column 1 (1,4,7,10,13,16,19,22,25,28,31,34)
            # Column 2 (2,5,8,11,14,17,20,23,26,29,32,35)
            # Column 3 (3,6,9,12,15,18,21,24,27,30,33,36)
            column1 = [1,4,7,10,13,16,19,22,25,28,31,34]
            column2 = [2,5,8,11,14,17,20,23,26,29,32,35]
            column3 = [3,6,9,12,15,18,21,24,27,30,33,36]
            
            if bet_value == '1' and winning_number in column1:
                return bet_amount * 3  # 2:1 payout
            elif bet_value == '2' and winning_number in column2:
                return bet_amount * 3  # 2:1 payout
            elif bet_value == '3' and winning_number in column3:
                return bet_amount * 3  # 2:1 payout
            return 0
        
        return 0

class PokerGame:
    """Simple Poker game implementation (5-card draw)"""
    
    @staticmethod
    def play(user_id: str, bet_amount: int) -> Dict[str, Any]:
        """Play 5-card draw poker against dealer"""
        try:
            with app.app_context():
                # Check user status and balance
                user = User.query.filter_by(id=user_id).first()
                if not user:
                    return {"success": False, "error": "User not found"}
                
                if user.user_status != 'active':
                    return {"success": False, "error": "User account is not active"}
                
                if user.points_balance < bet_amount:
                    return {"success": False, "error": "Insufficient points"}
                
                # Check daily limits
                daily_limit = DailyCasinoLimit.query.filter_by(user_id=user_id).first()
                if not daily_limit:
                    daily_limit = DailyCasinoLimit(user_id=user_id)
                    db.session.add(daily_limit)
                
                if daily_limit.total_won + daily_limit.total_lost + bet_amount > 1000:
                    return {"success": False, "error": "Daily casino limit reached"}
                
                # Deal cards
                deck = PokerGame._create_deck()
                random.shuffle(deck)
                
                player_hand = deck[:5]
                dealer_hand = deck[5:10]
                
                # Evaluate hands
                player_rank = PokerGame._evaluate_hand(player_hand)
                dealer_rank = PokerGame._evaluate_hand(dealer_hand)
                
                # Determine winner
                if player_rank > dealer_rank:
                    # Player wins
                    win_amount = bet_amount * 2  # 1:1 payout
                    result = "win"
                elif player_rank < dealer_rank:
                    # Dealer wins
                    win_amount = 0
                    result = "lose"
                else:
                    # Tie - return bet
                    win_amount = bet_amount
                    result = "tie"
                
                # Update user balance
                user.points_balance -= bet_amount
                if win_amount > 0:
                    user.points_balance += win_amount
                    user.total_earned += win_amount
                
                # Update daily limits
                daily_limit.games_played += 1
                if win_amount > 0:
                    daily_limit.total_won += win_amount
                else:
                    daily_limit.total_lost += bet_amount
                
                # Record game
                game_result = f"Player: {PokerGame._hand_to_string(player_hand)} ({PokerGame._rank_to_string(player_rank)}), Dealer: {PokerGame._hand_to_string(dealer_hand)} ({PokerGame._rank_to_string(dealer_rank)}), Result: {result}"
                casino_game = CasinoGame(
                    user_id=user_id,
                    game_type='poker',
                    bet_amount=bet_amount,
                    win_amount=win_amount,
                    result=game_result
                )
                db.session.add(casino_game)
                
                # Update user profile
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                
                if result == "win":
                    profile.total_wins += 1
                    profile.win_streak += 1
                    if profile.win_streak > profile.best_win_streak:
                        profile.best_win_streak = profile.win_streak
                elif result == "lose":
                    profile.total_losses += 1
                    profile.win_streak = 0
                
                profile.favorite_game = 'poker'
                profile.xp += bet_amount // 10
                
                db.session.commit()
                
                return {
                    "success": True,
                    "player_hand": PokerGame._hand_to_string(player_hand),
                    "dealer_hand": PokerGame._hand_to_string(dealer_hand),
                    "player_rank": PokerGame._rank_to_string(player_rank),
                    "dealer_rank": PokerGame._rank_to_string(dealer_rank),
                    "bet_amount": bet_amount,
                    "win_amount": win_amount,
                    "result": result,
                    "new_balance": user.points_balance
                }
                
        except Exception as e:
            logger.error(f"Error in poker game: {e}")
            db.session.rollback()
            return {"success": False, "error": "Game error occurred"}
    
    @staticmethod
    def _create_deck() -> List[Tuple[str, str]]:
        """Create a standard 52-card deck"""
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = []
        for suit in suits:
            for rank in ranks:
                deck.append((rank, suit))
        return deck
    
    @staticmethod
    def _evaluate_hand(hand: List[Tuple[str, str]]) -> int:
        """Evaluate poker hand and return rank (higher is better)"""
        ranks = [card[0] for card in hand]
        suits = [card[1] for card in hand]
        
        # Convert ranks to numbers for comparison
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        values = [rank_values[rank] for rank in ranks]
        values.sort(reverse=True)
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        is_straight = values == list(range(values[0], values[0] - 5, -1))
        
        # Count rank frequencies
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        counts = sorted(rank_counts.values(), reverse=True)
        
        # Determine hand rank
        if is_straight and is_flush:
            return 8  # Straight flush
        elif counts == [4, 1]:
            return 7  # Four of a kind
        elif counts == [3, 2]:
            return 6  # Full house
        elif is_flush:
            return 5  # Flush
        elif is_straight:
            return 4  # Straight
        elif counts == [3, 1, 1]:
            return 3  # Three of a kind
        elif counts == [2, 2, 1]:
            return 2  # Two pair
        elif counts == [2, 1, 1, 1]:
            return 1  # One pair
        else:
            return 0  # High card
    
    @staticmethod
    def _rank_to_string(rank: int) -> str:
        """Convert rank number to string"""
        rank_names = {
            8: "Straight Flush",
            7: "Four of a Kind",
            6: "Full House",
            5: "Flush",
            4: "Straight",
            3: "Three of a Kind",
            2: "Two Pair",
            1: "One Pair",
            0: "High Card"
        }
        return rank_names.get(rank, "Unknown")
    
    @staticmethod
    def _hand_to_string(hand: List[Tuple[str, str]]) -> str:
        """Convert hand to readable string"""
        return " ".join([f"{rank}{suit}" for rank, suit in hand])

class LotteryGame:
    """Lottery game implementation"""
    
    @staticmethod
    def play(user_id: str, bet_amount: int, numbers: List[int]) -> Dict[str, Any]:
        """Play lottery with user-selected numbers"""
        try:
            with app.app_context():
                # Check user status and balance
                user = User.query.filter_by(id=user_id).first()
                if not user:
                    return {"success": False, "error": "User not found"}
                
                if user.user_status != 'active':
                    return {"success": False, "error": "User account is not active"}
                
                if user.points_balance < bet_amount:
                    return {"success": False, "error": "Insufficient points"}
                
                # Validate numbers (1-49, exactly 6 numbers)
                if len(numbers) != 6 or not all(1 <= num <= 49 for num in numbers):
                    return {"success": False, "error": "Please select exactly 6 numbers between 1 and 49"}
                
                if len(set(numbers)) != 6:
                    return {"success": False, "error": "All numbers must be unique"}
                
                # Check daily limits
                daily_limit = DailyCasinoLimit.query.filter_by(user_id=user_id).first()
                if not daily_limit:
                    daily_limit = DailyCasinoLimit(user_id=user_id)
                    db.session.add(daily_limit)
                
                if daily_limit.total_won + daily_limit.total_lost + bet_amount > 1000:
                    return {"success": False, "error": "Daily casino limit reached"}
                
                # Draw winning numbers
                winning_numbers = sorted(random.sample(range(1, 50), 6))
                
                # Count matches
                matches = len(set(numbers) & set(winning_numbers))
                
                # Calculate payout based on matches
                payouts = {
                    6: 1000000,  # Jackpot
                    5: 10000,    # 5 matches
                    4: 1000,     # 4 matches
                    3: 100,      # 3 matches
                    2: 10,       # 2 matches
                    1: 0,        # 1 match (no payout)
                    0: 0         # 0 matches (no payout)
                }
                
                win_amount = payouts.get(matches, 0)
                
                # Update user balance
                user.points_balance -= bet_amount
                if win_amount > 0:
                    user.points_balance += win_amount
                    user.total_earned += win_amount
                
                # Update daily limits
                daily_limit.games_played += 1
                if win_amount > 0:
                    daily_limit.total_won += win_amount
                else:
                    daily_limit.total_lost += bet_amount
                
                # Record game
                game_result = f"Numbers: {numbers}, Winning: {winning_numbers}, Matches: {matches}, Payout: {win_amount}"
                casino_game = CasinoGame(
                    user_id=user_id,
                    game_type='lottery',
                    bet_amount=bet_amount,
                    win_amount=win_amount,
                    result=game_result
                )
                db.session.add(casino_game)
                
                # Update user profile
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile:
                    profile = UserProfile(user_id=user_id)
                    db.session.add(profile)
                
                if win_amount > 0:
                    profile.total_wins += 1
                    profile.win_streak += 1
                    if profile.win_streak > profile.best_win_streak:
                        profile.best_win_streak = profile.win_streak
                else:
                    profile.total_losses += 1
                    profile.win_streak = 0
                
                profile.favorite_game = 'lottery'
                profile.xp += bet_amount // 10
                
                db.session.commit()
                
                return {
                    "success": True,
                    "user_numbers": numbers,
                    "winning_numbers": winning_numbers,
                    "matches": matches,
                    "bet_amount": bet_amount,
                    "win_amount": win_amount,
                    "result": "win" if win_amount > 0 else "lose",
                    "new_balance": user.points_balance
                }
                
        except Exception as e:
            logger.error(f"Error in lottery game: {e}")
            db.session.rollback()
            return {"success": False, "error": "Game error occurred"}