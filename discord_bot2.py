diff --git a/discord_bot.py b/discord_bot.py
--- a/discord_bot.py
+++ b/discord_bot.py
@@ -1,19 +1,346 @@
-
-bot = RewardsBot()
-
-
-@bot.tree.command(name="balance", description="Check your current points balance")
-async def balance(interaction: discord.Interaction):
-    """Show user's current points balance"""
-    try:
-        with app.app_context():
-            user_id = str(interaction.user.id)
-            user = User.query.filter_by(id=user_id).first()
-
-            if not user:
-        await interaction.response.send_message("❌ An error occurred while fetching server statistics.", ephemeral=True)
-
-
-def run_bot():
-    if not Config.DISCORD_TOKEN:
-        logger.error("Discord token not found in environment variables!")
+
+bot = RewardsBot()
+
+def check_user_status(user_id: str) -> tuple[bool, str]:
+    """Check if user is banned or suspended. Returns (is_allowed, status_message)"""
+    try:
+        with app.app_context():
+            user = User.query.filter_by(id=user_id).first()
+            if not user:
+                return True, ""  # New users are allowed
+            
+            if user.user_status == 'banned':
+                return False, f"🚫 You are banned from using this bot.\n**Reason:** {user.ban_reason or 'No reason provided'}"
+            elif user.user_status == 'suspended':
+                return False, f"⏸️ Your account is suspended. Please contact an administrator."
+            
+            return True, ""
+    except Exception as e:
+        logger.error(f"Error checking user status: {e}")
+        return True, ""  # Allow on error to avoid blocking legitimate users
+
+
+@bot.tree.command(name="balance", description="Check your current points balance")
+async def balance(interaction: discord.Interaction):
+    """Show user's current points balance"""
+    try:
+        user_id = str(interaction.user.id)
+        
+        # Check if user is banned or suspended
+        is_allowed, status_message = check_user_status(user_id)
+        if not is_allowed:
+            await interaction.response.send_message(status_message, ephemeral=True)
+            return
+        
+        with app.app_context():
+            user = User.query.filter_by(id=user_id).first()
+
+            if not user:
+        await interaction.response.send_message("❌ An error occurred while fetching server statistics.", ephemeral=True)
+
+
+@bot.tree.command(name="admin-user", description="View detailed user information (Admin only)")
+async def admin_user_info(interaction: discord.Interaction, user_id: str):
+    """Show detailed information about a specific user"""
+    try:
+        with app.app_context():
+            admin_user_id = str(interaction.user.id)
+            
+            # Check if user is admin
+            if not AdminManager.is_admin(admin_user_id):
+                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
+                return
+            
+            # Get user details
+            result = AdminManager.get_user_details(user_id)
+            
+            if not result['success']:
+                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
+                return
+            
+            user = result['user']
+            
+            # Create embed
+            embed = discord.Embed(
+                title=f"👤 User Profile: {user['username']}",
+                description=f"User ID: `{user['id']}`",
+                color=0x3498db if user['user_status'] == 'active' else 0xe74c3c
+            )
+            
+            # Status indicator
+            status_emoji = "🟢" if user['user_status'] == 'active' else "🔴" if user['user_status'] == 'banned' else "🟡"
+            embed.add_field(name="Status", value=f"{status_emoji} {user['user_status'].title()}", inline=True)
+            
+            # Points information
+            embed.add_field(name="💰 Points Balance", value=f"**{user['points_balance']:,}**", inline=True)
+            embed.add_field(name="📈 Total Earned", value=f"**{user['total_earned']:,}**", inline=True)
+            
+            # Activity information
+            embed.add_field(name="🎮 Games Played", value=f"**{user['total_games_played']}**", inline=True)
+            embed.add_field(name="🎁 Gift Cards Redeemed", value=f"**{user['total_gift_cards_redeemed']}**", inline=True)
+            
+            # Dates
+            embed.add_field(name="📅 Created", value=f"<t:{int(datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
+            embed.add_field(name="🕒 Last Activity", value=f"<t:{int(datetime.fromisoformat(user['last_activity'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
+            
+            if user['last_earn_time']:
+                embed.add_field(name="💎 Last Earn", value=f"<t:{int(datetime.fromisoformat(user['last_earn_time'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
+            
+            # Ban information if banned
+            if user['user_status'] == 'banned':
+                embed.add_field(name="🚫 Ban Reason", value=user['ban_reason'] or "No reason provided", inline=False)
+                if user['banned_at']:
+                    embed.add_field(name="🚫 Banned At", value=f"<t:{int(datetime.fromisoformat(user['banned_at'].replace('Z', '+00:00')).timestamp())}:R>", inline=True)
+                if user['banned_by']:
+                    embed.add_field(name="🚫 Banned By", value=f"<@{user['banned_by']}>", inline=True)
+            
+            # Recent activity
+            if user['recent_games']:
+                games_text = ""
+                for game in user['recent_games'][:3]:
+                    games_text += f"• {game['game_type'].title()}: {game['bet_amount']} → {game['win_amount']}\n"
+                embed.add_field(name="🎮 Recent Games", value=games_text, inline=False)
+            
+            if user['recent_ads']:
+                ads_text = ""
+                for ad in user['recent_ads'][:3]:
+                    ads_text += f"• +{ad['points_earned']} points\n"
+                embed.add_field(name="📺 Recent Ads", value=ads_text, inline=False)
+            
+            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
+            embed.timestamp = datetime.utcnow()
+
+            await interaction.response.send_message(embed=embed, ephemeral=True)
+
+    except Exception as e:
+        logger.error(f"Error in admin-user command: {e}")
+        await interaction.response.send_message("❌ An error occurred while fetching user information.", ephemeral=True)
+
+
+@bot.tree.command(name="admin-users", description="List users with pagination (Admin only)")
+async def admin_list_users(interaction: discord.Interaction, page: int = 1, status: str = None):
+    """List users with pagination and optional status filter"""
+    try:
+        with app.app_context():
+            user_id = str(interaction.user.id)
+            
+            # Check if user is admin
+            if not AdminManager.is_admin(user_id):
+                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
+                return
+            
+            # Validate status filter
+            if status and status not in ['active', 'banned', 'suspended']:
+                await interaction.response.send_message("❌ Invalid status. Use: active, banned, or suspended", ephemeral=True)
+                return
+            
+            # Get users
+            result = AdminManager.get_users(page=page, per_page=10, status=status)
+            
+            if not result['success']:
+                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
+                return
+            
+            embed = discord.Embed(
+                title=f"👥 Users List (Page {page})",
+                description=f"Showing {len(result['users'])} of {result['pagination']['total']} users",
+                color=0x3498db
+            )
+            
+            if status:
+                embed.add_field(name="🔍 Filter", value=f"Status: {status.title()}", inline=True)
+            
+            # User list
+            if result['users']:
+                users_text = ""
+                for user in result['users']:
+                    status_emoji = "🟢" if user['user_status'] == 'active' else "🔴" if user['user_status'] == 'banned' else "🟡"
+                    users_text += f"{status_emoji} **{user['username']}**\n"
+                    users_text += f"   ID: `{user['id']}` | Points: {user['points_balance']:,}\n"
+                    users_text += f"   Status: {user['user_status'].title()}\n\n"
+                
+                embed.add_field(name="👤 Users", value=users_text, inline=False)
+            else:
+                embed.add_field(name="👤 Users", value="No users found", inline=False)
+            
+            # Pagination info
+            pagination = result['pagination']
+            pagination_text = f"Page {pagination['page']} of {pagination['pages']}\n"
+            if pagination['has_prev']:
+                pagination_text += "◀️ Previous page available\n"
+            if pagination['has_next']:
+                pagination_text += "▶️ Next page available"
+            
+            embed.add_field(name="📄 Pagination", value=pagination_text, inline=False)
+            
+            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
+            embed.timestamp = datetime.utcnow()
+
+            await interaction.response.send_message(embed=embed, ephemeral=True)
+
+    except Exception as e:
+        logger.error(f"Error in admin-users command: {e}")
+        await interaction.response.send_message("❌ An error occurred while fetching users list.", ephemeral=True)
+
+
+@bot.tree.command(name="admin-ban", description="Ban a user (Admin only)")
+async def admin_ban_user(interaction: discord.Interaction, user_id: str, reason: str):
+    """Ban a user with a reason"""
+    try:
+        with app.app_context():
+            admin_user_id = str(interaction.user.id)
+            
+            # Check if user is admin
+            if not AdminManager.is_admin(admin_user_id):
+                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
+                return
+            
+            # Ban the user
+            result = AdminManager.ban_user(user_id, reason, admin_user_id)
+            
+            if result['success']:
+                embed = discord.Embed(
+                    title="🚫 User Banned",
+                    description=f"User has been successfully banned",
+                    color=0xe74c3c
+                )
+                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
+                embed.add_field(name="Reason", value=reason, inline=True)
+                embed.add_field(name="Banned By", value=f"<@{admin_user_id}>", inline=True)
+                embed.set_footer(text=f"Admin: {interaction.user.display_name}")
+                embed.timestamp = datetime.utcnow()
+                
+                await interaction.response.send_message(embed=embed, ephemeral=True)
+            else:
+                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
+
+    except Exception as e:
+        logger.error(f"Error in admin-ban command: {e}")
+        await interaction.response.send_message("❌ An error occurred while banning user.", ephemeral=True)
+
+
+@bot.tree.command(name="admin-unban", description="Unban a user (Admin only)")
+async def admin_unban_user(interaction: discord.Interaction, user_id: str):
+    """Unban a user"""
+    try:
+        with app.app_context():
+            admin_user_id = str(interaction.user.id)
+            
+            # Check if user is admin
+            if not AdminManager.is_admin(admin_user_id):
+                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
+                return
+            
+            # Unban the user
+            result = AdminManager.unban_user(user_id, admin_user_id)
+            
+            if result['success']:
+                embed = discord.Embed(
+                    title="✅ User Unbanned",
+                    description=f"User has been successfully unbanned",
+                    color=0x2ecc71
+                )
+                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
+                embed.add_field(name="Unbanned By", value=f"<@{admin_user_id}>", inline=True)
+                embed.set_footer(text=f"Admin: {interaction.user.display_name}")
+                embed.timestamp = datetime.utcnow()
+                
+                await interaction.response.send_message(embed=embed, ephemeral=True)
+            else:
+                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
+
+    except Exception as e:
+        logger.error(f"Error in admin-unban command: {e}")
+        await interaction.response.send_message("❌ An error occurred while unbanning user.", ephemeral=True)
+
+
+@bot.tree.command(name="admin-adjust", description="Adjust user points (Admin only)")
+async def admin_adjust_points(interaction: discord.Interaction, user_id: str, points_change: int, reason: str = None):
+    """Adjust a user's points balance"""
+    try:
+        with app.app_context():
+            admin_user_id = str(interaction.user.id)
+            
+            # Check if user is admin
+            if not AdminManager.is_admin(admin_user_id):
+                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
+                return
+            
+            # Adjust points
+            result = AdminManager.adjust_user_points(user_id, points_change, admin_user_id, reason)
+            
+            if result['success']:
+                embed = discord.Embed(
+                    title="💰 Points Adjusted",
+                    description=f"User points have been successfully adjusted",
+                    color=0xf39c12
+                )
+                embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
+                embed.add_field(name="Points Change", value=f"{points_change:+,}", inline=True)
+                embed.add_field(name="Old Balance", value=f"{result['old_balance']:,}", inline=True)
+                embed.add_field(name="New Balance", value=f"{result['new_balance']:,}", inline=True)
+                if reason:
+                    embed.add_field(name="Reason", value=reason, inline=False)
+                embed.add_field(name="Adjusted By", value=f"<@{admin_user_id}>", inline=True)
+                embed.set_footer(text=f"Admin: {interaction.user.display_name}")
+                embed.timestamp = datetime.utcnow()
+                
+                await interaction.response.send_message(embed=embed, ephemeral=True)
+            else:
+                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
+
+    except Exception as e:
+        logger.error(f"Error in admin-adjust command: {e}")
+        await interaction.response.send_message("❌ An error occurred while adjusting user points.", ephemeral=True)
+
+
+@bot.tree.command(name="admin-search", description="Search for users (Admin only)")
+async def admin_search_users(interaction: discord.Interaction, query: str):
+    """Search for users by username or ID"""
+    try:
+        with app.app_context():
+            user_id = str(interaction.user.id)
+            
+            # Check if user is admin
+            if not AdminManager.is_admin(user_id):
+                await interaction.response.send_message("❌ You don't have admin permissions!", ephemeral=True)
+                return
+            
+            # Search users
+            result = AdminManager.search_users(query, limit=10)
+            
+            if not result['success']:
+                await interaction.response.send_message(f"❌ {result['error']}", ephemeral=True)
+                return
+            
+            embed = discord.Embed(
+                title=f"🔍 Search Results for '{query}'",
+                description=f"Found {result['count']} users",
+                color=0x3498db
+            )
+            
+            if result['users']:
+                users_text = ""
+                for user in result['users']:
+                    status_emoji = "🟢" if user['user_status'] == 'active' else "🔴" if user['user_status'] == 'banned' else "🟡"
+                    users_text += f"{status_emoji} **{user['username']}**\n"
+                    users_text += f"   ID: `{user['id']}` | Points: {user['points_balance']:,}\n"
+                    users_text += f"   Status: {user['user_status'].title()}\n\n"
+                
+                embed.add_field(name="👤 Users", value=users_text, inline=False)
+            else:
+                embed.add_field(name="👤 Users", value="No users found", inline=False)
+            
+            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
+            embed.timestamp = datetime.utcnow()
+
+            await interaction.response.send_message(embed=embed, ephemeral=True)
+
+    except Exception as e:
+        logger.error(f"Error in admin-search command: {e}")
+        await interaction.response.send_message("❌ An error occurred while searching users.", ephemeral=True)
+
+
+def run_bot():
+    if not Config.DISCORD_TOKEN:
+        logger.error("Discord token not found in environment variables!")
