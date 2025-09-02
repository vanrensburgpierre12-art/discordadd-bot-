diff --git a/database.py b/database.py
--- a/database.py
+++ b/database.py
@@ -1,26 +1,323 @@
-    created_at = db.Column(db.DateTime, default=datetime.utcnow)
-    last_earn_time = db.Column(db.DateTime, nullable=True)
-    
-    def __repr__(self):
-        return f'<User {self.username} (ID: {self.id})>'
-
-class GiftCard(db.Model):
-    __tablename__ = 'gift_cards'
-    
-    id = db.Column(db.Integer, primary_key=True)
-    code = db.Column(db.String(100), unique=True, nullable=False)
-    amount = db.Column(db.Integer, nullable=False)  # Robux amount
-    used = db.Column(db.Boolean, default=False)
-    used_by = db.Column(db.String(20), nullable=True)  # Discord user ID
-    used_at = db.Column(db.DateTime, nullable=True)
-    created_at = db.Column(db.DateTime, default=datetime.utcnow)
-    
-    def __repr__(self):
-        return f'<GiftCard {self.code} ({self.amount} Robux)>'
-
-class AdCompletion(db.Model):
-    __tablename__ = 'ad_completions'
-                GiftCard(code=f"ROBUX_{uuid.uuid4().hex[:8].upper()}", amount=2000),
-            ]
-            db.session.add_all(sample_cards)
-            db.session.commit()
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    last_earn_time = db.Column(db.DateTime, nullable=True)
+    
+    # User management fields
+    user_status = db.Column(db.String(20), default='active')  # 'active', 'banned', 'suspended'
+    ban_reason = db.Column(db.Text, nullable=True)
+    banned_at = db.Column(db.DateTime, nullable=True)
+    banned_by = db.Column(db.String(20), nullable=True)  # Admin user ID who banned
+    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
+    total_games_played = db.Column(db.Integer, default=0)
+    total_gift_cards_redeemed = db.Column(db.Integer, default=0)
+    
+    def __repr__(self):
+        return f'<User {self.username} (ID: {self.id}, Status: {self.user_status})>'
+
+class GiftCard(db.Model):
+    __tablename__ = 'gift_cards'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    code = db.Column(db.String(100), unique=True, nullable=False)
+    amount = db.Column(db.Integer, nullable=False)  # Amount in currency
+    currency = db.Column(db.String(20), default='Robux')  # Robux, USD, etc.
+    category_id = db.Column(db.Integer, db.ForeignKey('gift_card_categories.id'), nullable=True)
+    used = db.Column(db.Boolean, default=False)
+    used_by = db.Column(db.String(20), nullable=True)  # Discord user ID
+    used_at = db.Column(db.DateTime, nullable=True)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<GiftCard {self.code} ({self.amount} {self.currency})>'
+
+class AdCompletion(db.Model):
+    __tablename__ = 'ad_completions'
+                GiftCard(code=f"ROBUX_{uuid.uuid4().hex[:8].upper()}", amount=2000),
+            ]
+            db.session.add_all(sample_cards)
+            db.session.commit()
+
+# New Models for Enhanced Features
+
+class UserProfile(db.Model):
+    __tablename__ = 'user_profiles'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    user_id = db.Column(db.String(20), nullable=False, unique=True)
+    avatar_url = db.Column(db.String(500), nullable=True)
+    bio = db.Column(db.Text, nullable=True)
+    level = db.Column(db.Integer, default=1)
+    xp = db.Column(db.Integer, default=0)
+    xp_to_next_level = db.Column(db.Integer, default=100)
+    total_wins = db.Column(db.Integer, default=0)
+    total_losses = db.Column(db.Integer, default=0)
+    win_streak = db.Column(db.Integer, default=0)
+    best_win_streak = db.Column(db.Integer, default=0)
+    favorite_game = db.Column(db.String(50), nullable=True)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<UserProfile User: {self.user_id}, Level: {self.level}>'
+
+class Achievement(db.Model):
+    __tablename__ = 'achievements'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    name = db.Column(db.String(100), nullable=False, unique=True)
+    description = db.Column(db.Text, nullable=False)
+    icon = db.Column(db.String(100), nullable=False)  # Emoji or icon name
+    category = db.Column(db.String(50), nullable=False)  # 'casino', 'social', 'economy', 'special'
+    requirement_type = db.Column(db.String(50), nullable=False)  # 'points_earned', 'games_played', 'streak', etc.
+    requirement_value = db.Column(db.Integer, nullable=False)
+    points_reward = db.Column(db.Integer, default=0)
+    is_hidden = db.Column(db.Boolean, default=False)
+    is_active = db.Column(db.Boolean, default=True)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<Achievement {self.name}>'
+
+class UserAchievement(db.Model):
+    __tablename__ = 'user_achievements'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    user_id = db.Column(db.String(20), nullable=False)
+    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
+    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
+    points_awarded = db.Column(db.Integer, default=0)
+    
+    # Composite unique constraint
+    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),)
+    
+    def __repr__(self):
+        return f'<UserAchievement User: {self.user_id}, Achievement: {self.achievement_id}>'
+
+class Challenge(db.Model):
+    __tablename__ = 'challenges'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    name = db.Column(db.String(100), nullable=False)
+    description = db.Column(db.Text, nullable=False)
+    challenge_type = db.Column(db.String(50), nullable=False)  # 'daily', 'weekly', 'monthly'
+    requirement_type = db.Column(db.String(50), nullable=False)  # 'earn_points', 'play_games', 'win_games', etc.
+    requirement_value = db.Column(db.Integer, nullable=False)
+    points_reward = db.Column(db.Integer, nullable=False)
+    bonus_multiplier = db.Column(db.Float, default=1.0)
+    start_date = db.Column(db.DateTime, nullable=False)
+    end_date = db.Column(db.DateTime, nullable=False)
+    is_active = db.Column(db.Boolean, default=True)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<Challenge {self.name} ({self.challenge_type})>'
+
+class UserChallenge(db.Model):
+    __tablename__ = 'user_challenges'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    user_id = db.Column(db.String(20), nullable=False)
+    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
+    progress = db.Column(db.Integer, default=0)
+    completed = db.Column(db.Boolean, default=False)
+    completed_at = db.Column(db.DateTime, nullable=True)
+    points_earned = db.Column(db.Integer, default=0)
+    
+    # Composite unique constraint
+    __table_args__ = (db.UniqueConstraint('user_id', 'challenge_id', name='unique_user_challenge'),)
+    
+    def __repr__(self):
+        return f'<UserChallenge User: {self.user_id}, Challenge: {self.challenge_id}>'
+
+class Leaderboard(db.Model):
+    __tablename__ = 'leaderboards'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    name = db.Column(db.String(100), nullable=False, unique=True)
+    description = db.Column(db.Text, nullable=True)
+    leaderboard_type = db.Column(db.String(50), nullable=False)  # 'points', 'wins', 'streak', 'xp'
+    period = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'all_time'
+    is_active = db.Column(db.Boolean, default=True)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<Leaderboard {self.name} ({self.leaderboard_type})>'
+
+class LeaderboardEntry(db.Model):
+    __tablename__ = 'leaderboard_entries'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    leaderboard_id = db.Column(db.Integer, db.ForeignKey('leaderboards.id'), nullable=False)
+    user_id = db.Column(db.String(20), nullable=False)
+    score = db.Column(db.Integer, nullable=False)
+    rank = db.Column(db.Integer, nullable=True)
+    period_start = db.Column(db.DateTime, nullable=False)
+    period_end = db.Column(db.DateTime, nullable=False)
+    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
+    
+    # Composite unique constraint
+    __table_args__ = (db.UniqueConstraint('leaderboard_id', 'user_id', 'period_start', name='unique_leaderboard_entry'),)
+    
+    def __repr__(self):
+        return f'<LeaderboardEntry User: {self.user_id}, Score: {self.score}, Rank: {self.rank}>'
+
+class Tournament(db.Model):
+    __tablename__ = 'tournaments'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    name = db.Column(db.String(100), nullable=False)
+    description = db.Column(db.Text, nullable=True)
+    game_type = db.Column(db.String(50), nullable=False)  # 'dice', 'slots', 'blackjack', 'roulette', 'poker'
+    entry_fee = db.Column(db.Integer, nullable=False)
+    max_participants = db.Column(db.Integer, nullable=False)
+    prize_pool = db.Column(db.Integer, nullable=False)
+    start_date = db.Column(db.DateTime, nullable=False)
+    end_date = db.Column(db.DateTime, nullable=False)
+    status = db.Column(db.String(20), default='upcoming')  # 'upcoming', 'active', 'completed', 'cancelled'
+    created_by = db.Column(db.String(20), nullable=False)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<Tournament {self.name} ({self.game_type})>'
+
+class TournamentParticipant(db.Model):
+    __tablename__ = 'tournament_participants'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
+    user_id = db.Column(db.String(20), nullable=False)
+    entry_fee_paid = db.Column(db.Boolean, default=False)
+    final_score = db.Column(db.Integer, default=0)
+    final_rank = db.Column(db.Integer, nullable=True)
+    prize_earned = db.Column(db.Integer, default=0)
+    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    # Composite unique constraint
+    __table_args__ = (db.UniqueConstraint('tournament_id', 'user_id', name='unique_tournament_participant'),)
+    
+    def __repr__(self):
+        return f'<TournamentParticipant User: {self.user_id}, Tournament: {self.tournament_id}>'
+
+class Referral(db.Model):
+    __tablename__ = 'referrals'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    referrer_id = db.Column(db.String(20), nullable=False)  # User who referred
+    referred_id = db.Column(db.String(20), nullable=False)  # User who was referred
+    referral_code = db.Column(db.String(20), nullable=False, unique=True)
+    points_earned = db.Column(db.Integer, default=0)
+    is_active = db.Column(db.Boolean, default=True)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<Referral {self.referrer_id} -> {self.referred_id}>'
+
+class DailyBonus(db.Model):
+    __tablename__ = 'daily_bonuses'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    user_id = db.Column(db.String(20), nullable=False, unique=True)
+    current_streak = db.Column(db.Integer, default=0)
+    best_streak = db.Column(db.Integer, default=0)
+    last_claim_date = db.Column(db.Date, nullable=True)
+    total_claimed = db.Column(db.Integer, default=0)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<DailyBonus User: {self.user_id}, Streak: {self.current_streak}>'
+
+class SeasonalEvent(db.Model):
+    __tablename__ = 'seasonal_events'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    name = db.Column(db.String(100), nullable=False)
+    description = db.Column(db.Text, nullable=True)
+    event_type = db.Column(db.String(50), nullable=False)  # 'holiday', 'special', 'anniversary'
+    start_date = db.Column(db.DateTime, nullable=False)
+    end_date = db.Column(db.DateTime, nullable=False)
+    bonus_multiplier = db.Column(db.Float, default=1.0)
+    special_rewards = db.Column(db.Text, nullable=True)  # JSON string of special rewards
+    is_active = db.Column(db.Boolean, default=True)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<SeasonalEvent {self.name}>'
+
+class GiftCardCategory(db.Model):
+    __tablename__ = 'gift_card_categories'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    name = db.Column(db.String(100), nullable=False, unique=True)
+    description = db.Column(db.Text, nullable=True)
+    icon = db.Column(db.String(100), nullable=False)  # Emoji or icon
+    is_active = db.Column(db.Boolean, default=True)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<GiftCardCategory {self.name}>'
+
+class Friend(db.Model):
+    __tablename__ = 'friends'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    user_id = db.Column(db.String(20), nullable=False)  # User who sent the request
+    friend_id = db.Column(db.String(20), nullable=False)  # User who received the request
+    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'blocked'
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    accepted_at = db.Column(db.DateTime, nullable=True)
+    
+    # Composite unique constraint
+    __table_args__ = (db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),)
+    
+    def __repr__(self):
+        return f'<Friend {self.user_id} -> {self.friend_id} ({self.status})>'
+
+class Guild(db.Model):
+    __tablename__ = 'guilds'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    name = db.Column(db.String(100), nullable=False, unique=True)
+    description = db.Column(db.Text, nullable=True)
+    owner_id = db.Column(db.String(20), nullable=False)
+    icon_url = db.Column(db.String(500), nullable=True)
+    level = db.Column(db.Integer, default=1)
+    xp = db.Column(db.Integer, default=0)
+    total_points = db.Column(db.Integer, default=0)
+    member_count = db.Column(db.Integer, default=0)
+    max_members = db.Column(db.Integer, default=50)
+    is_active = db.Column(db.Boolean, default=True)
+    created_at = db.Column(db.DateTime, default=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<Guild {self.name} (Level {self.level})>'
+
+class GuildMember(db.Model):
+    __tablename__ = 'guild_members'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
+    user_id = db.Column(db.String(20), nullable=False)
+    role = db.Column(db.String(20), default='member')  # 'owner', 'admin', 'member'
+    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
+    contributed_points = db.Column(db.Integer, default=0)
+    
+    # Composite unique constraint
+    __table_args__ = (db.UniqueConstraint('guild_id', 'user_id', name='unique_guild_member'),)
+    
+    def __repr__(self):
+        return f'<GuildMember User: {self.user_id}, Guild: {self.guild_id}, Role: {self.role}>'
+
+class UserRanking(db.Model):
+    __tablename__ = 'user_rankings'
+    
+    id = db.Column(db.Integer, primary_key=True)
+    user_id = db.Column(db.String(20), nullable=False, unique=True)
+    overall_rank = db.Column(db.Integer, nullable=True)
+    points_rank = db.Column(db.Integer, nullable=True)
+    wins_rank = db.Column(db.Integer, nullable=True)
+    streak_rank = db.Column(db.Integer, nullable=True)
+    xp_rank = db.Column(db.Integer, nullable=True)
+    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
+    
+    def __repr__(self):
+        return f'<UserRanking User: {self.user_id}, Overall: {self.overall_rank}>'
