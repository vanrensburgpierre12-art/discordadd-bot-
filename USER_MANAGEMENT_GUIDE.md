# 👥 User Management System - Complete Implementation Guide

## 🎯 Overview

We have successfully implemented a comprehensive user management system for your Discord rewards platform. This system allows you to manage users, ban/unban them, adjust their points, and view detailed user information both through API endpoints and Discord bot commands.

## 🗄️ Database Changes

### Updated User Model
Added the following fields to the `User` table:

```python
# User management fields
user_status = db.Column(db.String(20), default='active')  # 'active', 'banned', 'suspended'
ban_reason = db.Column(db.Text, nullable=True)
banned_at = db.Column(db.DateTime, nullable=True)
banned_by = db.Column(db.String(20), nullable=True)  # Admin user ID who banned
last_activity = db.Column(db.DateTime, default=datetime.utcnow)
total_games_played = db.Column(db.Integer, default=0)
total_gift_cards_redeemed = db.Column(db.Integer, default=0)
```

## 🌐 API Endpoints

### User Management Endpoints

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| `GET` | `/admin/users` | List users with pagination | `page`, `per_page`, `status`, `search` |
| `GET` | `/admin/users/<user_id>` | Get detailed user information | `user_id` |
| `POST` | `/admin/users/<user_id>/ban` | Ban a user | `reason`, `admin_user_id` |
| `POST` | `/admin/users/<user_id>/unban` | Unban a user | `admin_user_id` |
| `POST` | `/admin/users/<user_id>/adjust-points` | Adjust user points | `points_change`, `admin_user_id`, `reason` |
| `GET` | `/admin/users/search` | Search users | `q`, `limit` |

### Example API Usage

#### List Users
```bash
curl "http://localhost:5000/admin/users?page=1&per_page=10&status=active"
```

#### Search Users
```bash
curl "http://localhost:5000/admin/users/search?q=john&limit=5"
```

#### Ban User
```bash
curl -X POST "http://localhost:5000/admin/users/123456789/ban" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Violating terms of service", "admin_user_id": "987654321"}'
```

#### Adjust User Points
```bash
curl -X POST "http://localhost:5000/admin/users/123456789/adjust-points" \
  -H "Content-Type: application/json" \
  -d '{"points_change": 1000, "admin_user_id": "987654321", "reason": "Bonus for good behavior"}'
```

## 🤖 Discord Bot Commands

### Admin Commands (Admin Only)

| Command | Description | Parameters |
|---------|-------------|------------|
| `/admin-user <user_id>` | View detailed user information | `user_id` |
| `/admin-users [page] [status]` | List users with pagination | `page` (optional), `status` (optional) |
| `/admin-ban <user_id> <reason>` | Ban a user with reason | `user_id`, `reason` |
| `/admin-unban <user_id>` | Unban a user | `user_id` |
| `/admin-adjust <user_id> <points> [reason]` | Adjust user points | `user_id`, `points`, `reason` (optional) |
| `/admin-search <query>` | Search for users | `query` |

### Example Discord Commands

```
/admin-user 123456789012345678
/admin-users 1 active
/admin-ban 123456789012345678 "Spamming in chat"
/admin-unban 123456789012345678
/admin-adjust 123456789012345678 500 "Welcome bonus"
/admin-search john
```

## 🔧 AdminManager Functions

### New Functions Added

```python
# User listing and search
AdminManager.get_users(page=1, per_page=50, status=None, search=None)
AdminManager.get_user_details(user_id)
AdminManager.search_users(query, limit=20)

# User management
AdminManager.ban_user(user_id, reason, admin_user_id)
AdminManager.unban_user(user_id, admin_user_id)
AdminManager.adjust_user_points(user_id, points_change, admin_user_id, reason=None)
```

## 🛡️ Security Features

### User Status Checking
- Banned users cannot use regular bot commands
- Suspended users are blocked from all interactions
- Admin commands require proper admin permissions
- All actions are logged with admin user IDs

### Ban System
- Users can be banned with specific reasons
- Ban information includes who banned them and when
- Banned users receive clear messages when trying to use commands
- Easy unban functionality for admins

## 📊 User Information Display

### Detailed User Profiles Include:
- Basic info (username, ID, status)
- Points balance and total earned
- Activity statistics (games played, gift cards redeemed)
- Recent activity (last 10 games and ads)
- Ban information (if applicable)
- Account creation and last activity dates

### User Lists Include:
- Pagination support
- Status filtering (active, banned, suspended)
- Search functionality
- Compact display with key information

## 🚀 Getting Started

### 1. Database Migration
The new fields will be automatically added when you restart the application. No manual migration needed.

### 2. Test the System
Run the test script to verify everything works:
```bash
python test_user_management.py
```

### 3. Add Your First Admin
Use the existing admin system to add admin users:
```bash
curl -X POST "http://localhost:5000/admin/add-admin" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "YOUR_DISCORD_ID", "username": "YourUsername", "admin_level": "admin"}'
```

### 4. Start Using Commands
Once you're an admin, you can use all the Discord commands listed above.

## 🎯 Use Cases

### Common Admin Tasks

1. **Ban a Problem User**
   ```
   /admin-ban 123456789012345678 "Spamming and harassment"
   ```

2. **Give Bonus Points**
   ```
   /admin-adjust 123456789012345678 1000 "Event participation bonus"
   ```

3. **Check User Activity**
   ```
   /admin-user 123456789012345678
   ```

4. **Find Users by Name**
   ```
   /admin-search john
   ```

5. **List All Banned Users**
   ```
   /admin-users 1 banned
   ```

## 🔍 Monitoring and Analytics

### User Statistics Tracked:
- Total games played
- Total gift cards redeemed
- Last activity timestamp
- Account creation date
- Points balance and total earned

### Admin Actions Logged:
- Who performed each action
- When actions were performed
- Reasons for bans and adjustments
- All changes are auditable

## 🎉 What You Can Now Do

✅ **View all users** with pagination and filtering  
✅ **Search users** by username or ID  
✅ **Ban/unban users** with reasons  
✅ **Adjust user points** manually  
✅ **View detailed user profiles** with activity history  
✅ **Monitor user activity** and statistics  
✅ **Block banned users** from using commands  
✅ **Audit all admin actions** with timestamps  

## 🚨 Important Notes

1. **Admin Permissions**: Only users with admin status can use these commands
2. **User Status**: Banned users are automatically blocked from all bot interactions
3. **Data Integrity**: All actions are logged and reversible
4. **Performance**: Pagination is implemented for large user lists
5. **Security**: All endpoints validate admin permissions

## 🎯 Next Steps

Your user management system is now complete and ready to use! You have full control over your Discord rewards platform users with both web API and Discord bot interfaces.

The system is production-ready and includes proper error handling, security checks, and user-friendly interfaces.