"""
Casino Games Module for Discord Rewards Platform
Provides various casino games for users to play with their points
"""

import random
import logging
from datetime import datetime, date, timedelta
from typing import Tuple, Dict, Any
from app_context import app, db
from database import User, CasinoGame, DailyCasinoLimit
from config import Config
from discord_monetization import DiscordMonetizationManager

logger = logging.getLogger(__name__)

class CasinoManager:
    """Manages casino games and user limits"""
    
    @staticmethod
    def check_daily_limits(user_id: str) -> Tuple[bool, str]:
        """Check if user has reached daily casino limits"""
        today = date.today()
        
        # Get existing daily limit record (there should only be one per user due to unique constraint)
        daily_limit = DailyCasinoLimit.query.filter_by(user_id=user_id).first()
        
        if not daily_limit:
            # Create new record for this user
            daily_limit = DailyCasinoLimit(
                user_id=user_id,
                date=today,
                total_won=0,
                total_lost=0,
                games_played=0
            )
            db.session.add(daily_limit)
            db.session.commit()
        elif daily_limit.date != today:
            # Reset daily limits for new day
            daily_limit.date = today
            daily_limit.total_won = 0
            daily_limit.total_lost = 0
            daily_limit.games_played = 0
            db.session.commit()
        
        # Check if user has reached daily limit
        net_result = daily_limit.total_won - daily_limit.total_lost
        if abs(net_result) >= Config.CASINO_DAILY_LIMIT:
            return False, f"You've reached your daily casino limit of {Config.CASINO_DAILY_LIMIT} points!"
        
        return True, ""
    
    @staticmethod
    def update_daily_limits(user_id: str, bet_amount: int, win_amount: int):
        """Update daily limits after a game"""
        today = date.today()
        daily_limit = DailyCasinoLimit.query.filter_by(user_id=user_id).first()
        
        if daily_limit:
            # Check if this is a new day and reset if needed
            if daily_limit.date != today:
                daily_limit.date = today
                daily_limit.total_won = 0
                daily_limit.total_lost = 0
                daily_limit.games_played = 0
            
            daily_limit.games_played += 1
            if win_amount > bet_amount:
                daily_limit.total_won += (win_amount - bet_amount)
            else:
                daily_limit.total_lost += (bet_amount - win_amount)
            db.session.commit()
        else:
            # This shouldn't happen if check_daily_limits was called first, but handle it gracefully
            logger.warning(f"Daily limit record not found for user {user_id}. Creating one.")
            try:
                daily_limit = DailyCasinoLimit(
                    user_id=user_id,
                    date=today,
                    total_won=0,
                    total_lost=0,
                    games_played=1
                )
                if win_amount > bet_amount:
                    daily_limit.total_won = (win_amount - bet_amount)
                else:
                    daily_limit.total_lost = (bet_amount - win_amount)
                db.session.add(daily_limit)
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to create daily limit record for user {user_id}: {e}")
                db.session.rollback()

class DiceGame:
    """Dice rolling game"""
    
    @staticmethod
    def play(user_id: str, bet_amount: int, guess: int) -> Dict[str, Any]:
        """Play dice game - user guesses a number 1-6"""
        if not (1 <= guess <= 6):
            return {"success": False, "error": "Guess must be between 1 and 6"}
        
        if not (Config.CASINO_MIN_BET <= bet_amount <= Config.CASINO_MAX_BET):
            return {"success": False, "error": f"Bet must be between {Config.CASINO_MIN_BET} and {Config.CASINO_MAX_BET} points"}
        
        # Check daily limits
        can_play, limit_msg = CasinoManager.check_daily_limits(user_id)
        if not can_play:
            return {"success": False, "error": limit_msg}
        
        # Roll dice
        dice_roll = random.randint(1, 6)
        
        # Get subscription bonus
        bonus_multiplier = DiscordMonetizationManager.get_casino_bonus_multiplier(user_id)
        
        # Calculate winnings
        if dice_roll == guess:
            # Exact match - 5x multiplier with subscription bonus
            base_win = bet_amount * 5
            win_amount = int(base_win * bonus_multiplier)
            bonus_text = f" (+{int((bonus_multiplier - 1) * 100)}% tier bonus)" if bonus_multiplier > 1 else ""
            result_text = f"🎲 **LUCKY!** You rolled {dice_roll} and guessed {guess}! You won **{win_amount:,}** points{bonus_text}!"
        else:
            # No match - lose bet
            win_amount = 0
            result_text = f"🎲 You rolled {dice_roll} but guessed {guess}. You lost **{bet_amount:,}** points."
        
        # Update user balance
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        if user.points_balance < bet_amount:
            return {"success": False, "error": "Insufficient points balance"}
        
        # Deduct bet and add winnings
        user.points_balance -= bet_amount
        user.points_balance += win_amount
        
        # Record game
        game_record = CasinoGame(
            user_id=user_id,
            game_type="dice",
            bet_amount=bet_amount,
            win_amount=win_amount,
            result=f"Rolled {dice_roll}, guessed {guess}"
        )
        db.session.add(game_record)
        
        # Update daily limits
        CasinoManager.update_daily_limits(user_id, bet_amount, win_amount)
        
        db.session.commit()
        
        return {
            "success": True,
            "dice_roll": dice_roll,
            "guess": guess,
            "bet_amount": bet_amount,
            "win_amount": win_amount,
            "new_balance": user.points_balance,
            "result_text": result_text
        }

class SlotsGame:
    """Slot machine game"""
    
    @staticmethod
    def play(user_id: str, bet_amount: int) -> Dict[str, Any]:
        """Play slots game"""
        if not (Config.CASINO_MIN_BET <= bet_amount <= Config.CASINO_MAX_BET):
            return {"success": False, "error": f"Bet must be between {Config.CASINO_MIN_BET} and {Config.CASINO_MAX_BET} points"}
        
        # Check daily limits
        can_play, limit_msg = CasinoManager.check_daily_limits(user_id)
        if not can_play:
            return {"success": False, "error": limit_msg}
        
        # Spin the slots
        symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "⭐", "💎", "7️⃣"]
        reels = [random.choice(symbols) for _ in range(3)]
        
        # Get subscription bonus
        bonus_multiplier = DiscordMonetizationManager.get_casino_bonus_multiplier(user_id)
        
        # Calculate winnings based on combinations
        win_amount = 0
        result_text = ""
        
        if reels[0] == reels[1] == reels[2]:
            # Three of a kind
            if reels[0] == "💎":
                base_win = bet_amount * 50  # Diamond jackpot
                win_amount = int(base_win * bonus_multiplier)
                bonus_text = f" (+{int((bonus_multiplier - 1) * 100)}% tier bonus)" if bonus_multiplier > 1 else ""
                result_text = f"🎰 **JACKPOT!** 💎💎💎 You won **{win_amount:,}** points{bonus_text}!"
            elif reels[0] == "7️⃣":
                base_win = bet_amount * 20  # Lucky 7s
                win_amount = int(base_win * bonus_multiplier)
                bonus_text = f" (+{int((bonus_multiplier - 1) * 100)}% tier bonus)" if bonus_multiplier > 1 else ""
                result_text = f"🎰 **LUCKY 7s!** 7️⃣7️⃣7️⃣ You won **{win_amount:,}** points{bonus_text}!"
            elif reels[0] == "⭐":
                base_win = bet_amount * 15  # Stars
                win_amount = int(base_win * bonus_multiplier)
                bonus_text = f" (+{int((bonus_multiplier - 1) * 100)}% tier bonus)" if bonus_multiplier > 1 else ""
                result_text = f"🎰 **STAR POWER!** ⭐⭐⭐ You won **{win_amount:,}** points{bonus_text}!"
            else:
                base_win = bet_amount * 10  # Other three of a kind
                win_amount = int(base_win * bonus_multiplier)
                bonus_text = f" (+{int((bonus_multiplier - 1) * 100)}% tier bonus)" if bonus_multiplier > 1 else ""
                result_text = f"🎰 **THREE OF A KIND!** {reels[0]}{reels[1]}{reels[2]} You won **{win_amount:,}** points{bonus_text}!"
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            # Two of a kind
            base_win = bet_amount * 2
            win_amount = int(base_win * bonus_multiplier)
            bonus_text = f" (+{int((bonus_multiplier - 1) * 100)}% tier bonus)" if bonus_multiplier > 1 else ""
            result_text = f"🎰 **TWO OF A KIND!** {reels[0]}{reels[1]}{reels[2]} You won **{win_amount:,}** points{bonus_text}!"
        else:
            # No match
            win_amount = 0
            result_text = f"🎰 {reels[0]}{reels[1]}{reels[2]} No match. You lost **{bet_amount:,}** points."
        
        # Update user balance
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        if user.points_balance < bet_amount:
            return {"success": False, "error": "Insufficient points balance"}
        
        # Deduct bet and add winnings
        user.points_balance -= bet_amount
        user.points_balance += win_amount
        
        # Record game
        game_record = CasinoGame(
            user_id=user_id,
            game_type="slots",
            bet_amount=bet_amount,
            win_amount=win_amount,
            result=f"Reels: {reels[0]}{reels[1]}{reels[2]}"
        )
        db.session.add(game_record)
        
        # Update daily limits
        CasinoManager.update_daily_limits(user_id, bet_amount, win_amount)
        
        db.session.commit()
        
        return {
            "success": True,
            "reels": reels,
            "bet_amount": bet_amount,
            "win_amount": win_amount,
            "new_balance": user.points_balance,
            "result_text": result_text
        }

class BlackjackGame:
    """Simple Blackjack game"""
    
    @staticmethod
    def play(user_id: str, bet_amount: int) -> Dict[str, Any]:
        """Play blackjack game"""
        if not (Config.CASINO_MIN_BET <= bet_amount <= Config.CASINO_MAX_BET):
            return {"success": False, "error": f"Bet must be between {Config.CASINO_MIN_BET} and {Config.CASINO_MAX_BET} points"}
        
        # Check daily limits
        can_play, limit_msg = CasinoManager.check_daily_limits(user_id)
        if not can_play:
            return {"success": False, "error": limit_msg}
        
        # Deal initial cards
        player_cards = [random.randint(1, 11) for _ in range(2)]
        dealer_cards = [random.randint(1, 11) for _ in range(2)]
        
        # Calculate scores
        player_score = sum(player_cards)
        dealer_score = sum(dealer_cards)
        
        # Simple blackjack logic (no hit/stand for now)
        win_amount = 0
        result_text = ""
        
        if player_score == 21 and dealer_score != 21:
            # Player blackjack
            win_amount = int(bet_amount * 2.5)
            result_text = f"🃏 **BLACKJACK!** Your {player_cards} (21) vs Dealer {dealer_cards} ({dealer_score}). You won **{win_amount:,}** points!"
        elif player_score > 21:
            # Player bust
            result_text = f"🃏 **BUST!** Your {player_cards} ({player_score}) vs Dealer {dealer_cards} ({dealer_score}). You lost **{bet_amount:,}** points."
        elif dealer_score > 21:
            # Dealer bust
            win_amount = bet_amount * 2
            result_text = f"🃏 **DEALER BUST!** Your {player_cards} ({player_score}) vs Dealer {dealer_cards} ({dealer_score}). You won **{win_amount:,}** points!"
        elif player_score > dealer_score:
            # Player wins
            win_amount = bet_amount * 2
            result_text = f"🃏 **YOU WIN!** Your {player_cards} ({player_score}) vs Dealer {dealer_cards} ({dealer_score}). You won **{win_amount:,}** points!"
        elif player_score < dealer_score:
            # Dealer wins
            result_text = f"🃏 **DEALER WINS!** Your {player_cards} ({player_score}) vs Dealer {dealer_cards} ({dealer_score}). You lost **{bet_amount:,}** points."
        else:
            # Tie
            win_amount = bet_amount
            result_text = f"🃏 **PUSH!** Your {player_cards} ({player_score}) vs Dealer {dealer_cards} ({dealer_score}). You get your bet back: **{win_amount:,}** points."
        
        # Update user balance
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        if user.points_balance < bet_amount:
            return {"success": False, "error": "Insufficient points balance"}
        
        # Deduct bet and add winnings
        user.points_balance -= bet_amount
        user.points_balance += win_amount
        
        # Record game
        game_record = CasinoGame(
            user_id=user_id,
            game_type="blackjack",
            bet_amount=bet_amount,
            win_amount=win_amount,
            result=f"Player {player_cards} ({player_score}) vs Dealer {dealer_cards} ({dealer_score})"
        )
        db.session.add(game_record)
        
        # Update daily limits
        CasinoManager.update_daily_limits(user_id, bet_amount, win_amount)
        
        db.session.commit()
        
        return {
            "success": True,
            "player_cards": player_cards,
            "dealer_cards": dealer_cards,
            "player_score": player_score,
            "dealer_score": dealer_score,
            "bet_amount": bet_amount,
            "win_amount": win_amount,
            "new_balance": user.points_balance,
            "result_text": result_text
        }