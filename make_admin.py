#!/usr/bin/env python3
"""
Make Admin Script
Add yourself or another user as an admin to the Discord Rewards Platform
"""

import sys
import os
from app_context import app, db
from admin_manager import AdminManager
from database import AdminUser

def make_admin(user_id: str, username: str = None, admin_level: str = 'admin'):
    """Make a user an admin"""
    try:
        with app.app_context():
            # Check if user is already an admin
            existing_admin = AdminUser.query.filter_by(user_id=user_id).first()
            if existing_admin:
                print(f"❌ User {user_id} is already an admin with level: {existing_admin.admin_level}")
                return False
            
            # Add the admin
            result = AdminManager.add_admin(
                user_id=user_id,
                username=username or f"Admin_{user_id}",
                admin_level=admin_level,
                created_by="system"
            )
            
            if result['success']:
                print(f"✅ Successfully added {username or user_id} as {admin_level}!")
                print(f"   Admin ID: {result['admin_id']}")
                print(f"   Permissions: {result['permissions']}")
                return True
            else:
                print(f"❌ Failed to add admin: {result['error']}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_admins():
    """List all current admins"""
    try:
        with app.app_context():
            admins = AdminUser.query.all()
            if not admins:
                print("📋 No admins found")
                return
            
            print("📋 Current Admins:")
            for admin in admins:
                print(f"   • {admin.username} ({admin.user_id}) - {admin.admin_level}")
                print(f"     Created: {admin.created_at}")
                print(f"     Permissions: Approve={admin.can_approve_transactions}, Manage={admin.can_manage_servers}, View={admin.can_view_all_data}")
                print()
                
    except Exception as e:
        print(f"❌ Error listing admins: {e}")

def main():
    """Main function"""
    print("🔧 Discord Rewards Platform - Admin Management")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 make_admin.py <discord_user_id> [username] [admin_level]")
        print("  python3 make_admin.py list")
        print()
        print("Admin levels: moderator, admin, super_admin")
        print("Example: python3 make_admin.py 123456789012345678 YourUsername admin")
        return
    
    if sys.argv[1] == "list":
        list_admins()
        return
    
    user_id = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) > 2 else None
    admin_level = sys.argv[3] if len(sys.argv) > 3 else 'admin'
    
    # Validate admin level
    valid_levels = ['moderator', 'admin', 'super_admin']
    if admin_level not in valid_levels:
        print(f"❌ Invalid admin level. Must be one of: {', '.join(valid_levels)}")
        return
    
    # Validate user ID (should be numeric and 17-19 digits)
    if not user_id.isdigit() or len(user_id) < 17 or len(user_id) > 19:
        print("❌ Invalid Discord user ID. Must be 17-19 digits.")
        print("   To get your Discord user ID:")
        print("   1. Enable Developer Mode in Discord")
        print("   2. Right-click your username and select 'Copy User ID'")
        return
    
    print(f"🔄 Adding {username or user_id} as {admin_level}...")
    success = make_admin(user_id, username, admin_level)
    
    if success:
        print("\n🎉 Admin added successfully!")
        print("   You can now use admin commands in Discord:")
        print("   • /admin-panel - Access web admin panel")
        print("   • /admin-pending - View pending transactions")
        print("   • /admin-servers - View server statistics")

if __name__ == "__main__":
    main()