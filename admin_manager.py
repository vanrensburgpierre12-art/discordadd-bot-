"""
Admin Management Module for Discord Rewards Platform
Handles admin permissions, transaction approvals, and multi-server management
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app_context import app, db
from database import AdminUser, TransactionApproval, WalletTransaction, DiscordTransaction, Server, User
from config import Config

logger = logging.getLogger(__name__)

class AdminManager:
    """Manages admin operations and transaction approvals"""
    
    @staticmethod
    def is_admin(user_id: str) -> bool:
        """Check if user is an admin"""
        admin = AdminUser.query.filter_by(user_id=user_id).first()
        return admin is not None
    
    @staticmethod
    def get_admin_level(user_id: str) -> Optional[str]:
        """Get admin level of user"""
        admin = AdminUser.query.filter_by(user_id=user_id).first()
        return admin.admin_level if admin else None
    
    @staticmethod
    def can_approve_transactions(user_id: str) -> bool:
        """Check if user can approve transactions"""
        admin = AdminUser.query.filter_by(user_id=user_id).first()
        return admin and admin.can_approve_transactions
    
    @staticmethod
    def can_manage_servers(user_id: str) -> bool:
        """Check if user can manage servers"""
        admin = AdminUser.query.filter_by(user_id=user_id).first()
        return admin and admin.can_manage_servers
    
    @staticmethod
    def can_view_all_data(user_id: str) -> bool:
        """Check if user can view all data"""
        admin = AdminUser.query.filter_by(user_id=user_id).first()
        return admin and admin.can_view_all_data
    
    @staticmethod
    def add_admin(user_id: str, username: str, admin_level: str = 'moderator', created_by: str = None) -> Dict[str, Any]:
        """Add a new admin user"""
        try:
            # Check if user is already an admin
            existing_admin = AdminUser.query.filter_by(user_id=user_id).first()
            if existing_admin:
                return {"success": False, "error": "User is already an admin"}
            
            # Set permissions based on admin level
            permissions = {
                'moderator': {
                    'can_approve_transactions': True,
                    'can_manage_servers': False,
                    'can_view_all_data': False
                },
                'admin': {
                    'can_approve_transactions': True,
                    'can_manage_servers': True,
                    'can_view_all_data': True
                },
                'super_admin': {
                    'can_approve_transactions': True,
                    'can_manage_servers': True,
                    'can_view_all_data': True
                }
            }
            
            if admin_level not in permissions:
                return {"success": False, "error": "Invalid admin level"}
            
            admin = AdminUser(
                user_id=user_id,
                username=username,
                admin_level=admin_level,
                created_by=created_by,
                **permissions[admin_level]
            )
            
            db.session.add(admin)
            db.session.commit()
            
            return {
                "success": True,
                "admin_id": admin.id,
                "admin_level": admin_level,
                "permissions": permissions[admin_level]
            }
            
        except Exception as e:
            logger.error(f"Error adding admin: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to add admin"}
    
    @staticmethod
    def get_pending_transactions(limit: int = 50) -> Dict[str, Any]:
        """Get all pending transactions requiring approval"""
        try:
            # Get pending wallet transactions
            pending_wallet = WalletTransaction.query.filter_by(status='pending').limit(limit).all()
            
            # Get pending Discord transactions
            pending_discord = DiscordTransaction.query.filter_by(status='pending').limit(limit).all()
            
            wallet_transactions = []
            for txn in pending_wallet:
                user = User.query.filter_by(id=txn.user_id).first()
                wallet_transactions.append({
                    "id": txn.id,
                    "type": "wallet",
                    "user_id": txn.user_id,
                    "username": user.username if user else "Unknown",
                    "transaction_type": txn.transaction_type,
                    "amount_usd": float(txn.amount_usd),
                    "points_amount": txn.points_amount,
                    "payment_method": txn.payment_method,
                    "created_at": txn.created_at.isoformat(),
                    "status": txn.status
                })
            
            discord_transactions = []
            for txn in pending_discord:
                user = User.query.filter_by(id=txn.user_id).first()
                server = Server.query.filter_by(id=txn.server_id).first()
                discord_transactions.append({
                    "id": txn.id,
                    "type": "discord",
                    "user_id": txn.user_id,
                    "username": user.username if user else "Unknown",
                    "server_id": txn.server_id,
                    "server_name": server.name if server else "Unknown Server",
                    "transaction_type": txn.transaction_type,
                    "tier_name": txn.tier_name,
                    "points_awarded": txn.points_awarded,
                    "created_at": txn.created_at.isoformat(),
                    "status": txn.status
                })
            
            return {
                "success": True,
                "wallet_transactions": wallet_transactions,
                "discord_transactions": discord_transactions,
                "total_pending": len(wallet_transactions) + len(discord_transactions)
            }
            
        except Exception as e:
            logger.error(f"Error getting pending transactions: {e}")
            return {"success": False, "error": "Failed to get pending transactions"}
    
    @staticmethod
    def approve_transaction(transaction_id: int, transaction_type: str, admin_user_id: str, notes: str = None) -> Dict[str, Any]:
        """Approve a pending transaction"""
        try:
            if transaction_type == 'wallet':
                transaction = WalletTransaction.query.get(transaction_id)
            elif transaction_type == 'discord':
                transaction = DiscordTransaction.query.get(transaction_id)
            else:
                return {"success": False, "error": "Invalid transaction type"}
            
            if not transaction:
                return {"success": False, "error": "Transaction not found"}
            
            if transaction.status != 'pending':
                return {"success": False, "error": f"Transaction already {transaction.status}"}
            
            # Update transaction status
            transaction.status = 'approved'
            transaction.approved_by = admin_user_id
            transaction.approved_at = datetime.utcnow()
            
            # If it's a wallet transaction, complete the deposit
            if transaction_type == 'wallet' and transaction.transaction_type == 'deposit':
                from wallet_manager import WalletManager
                result = WalletManager.complete_deposit_transaction(transaction_id)
                if not result['success']:
                    return {"success": False, "error": f"Failed to complete deposit: {result['error']}"}
            
            # Create approval record
            approval = TransactionApproval(
                transaction_id=transaction_id,
                transaction_type=transaction_type,
                status='approved',
                requested_by=transaction.user_id,
                approved_by=admin_user_id,
                processed_at=datetime.utcnow()
            )
            db.session.add(approval)
            
            db.session.commit()
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "status": "approved",
                "approved_by": admin_user_id,
                "approved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error approving transaction: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to approve transaction"}
    
    @staticmethod
    def reject_transaction(transaction_id: int, transaction_type: str, admin_user_id: str, reason: str) -> Dict[str, Any]:
        """Reject a pending transaction"""
        try:
            if transaction_type == 'wallet':
                transaction = WalletTransaction.query.get(transaction_id)
            elif transaction_type == 'discord':
                transaction = DiscordTransaction.query.get(transaction_id)
            else:
                return {"success": False, "error": "Invalid transaction type"}
            
            if not transaction:
                return {"success": False, "error": "Transaction not found"}
            
            if transaction.status != 'pending':
                return {"success": False, "error": f"Transaction already {transaction.status}"}
            
            # Update transaction status
            transaction.status = 'rejected'
            transaction.approved_by = admin_user_id
            transaction.approved_at = datetime.utcnow()
            
            # Create approval record
            approval = TransactionApproval(
                transaction_id=transaction_id,
                transaction_type=transaction_type,
                status='rejected',
                requested_by=transaction.user_id,
                approved_by=admin_user_id,
                rejection_reason=reason,
                processed_at=datetime.utcnow()
            )
            db.session.add(approval)
            
            db.session.commit()
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "status": "rejected",
                "rejected_by": admin_user_id,
                "rejection_reason": reason,
                "rejected_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error rejecting transaction: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to reject transaction"}
    
    @staticmethod
    def get_server_stats() -> Dict[str, Any]:
        """Get statistics for all servers"""
        try:
            servers = Server.query.filter_by(is_active=True).all()
            
            server_stats = []
            for server in servers:
                # Get user count for this server
                user_count = User.query.count()  # This would need to be server-specific in a real implementation
                
                # Get transaction counts
                wallet_txns = WalletTransaction.query.count()  # Would need server filtering
                discord_txns = DiscordTransaction.query.filter_by(server_id=server.id).count()
                
                server_stats.append({
                    "server_id": server.id,
                    "server_name": server.name,
                    "owner_id": server.owner_id,
                    "is_active": server.is_active,
                    "created_at": server.created_at.isoformat(),
                    "last_activity": server.last_activity.isoformat(),
                    "user_count": user_count,
                    "wallet_transactions": wallet_txns,
                    "discord_transactions": discord_txns,
                    "settings": {
                        "points_per_ad": server.points_per_ad,
                        "redemption_threshold": server.redemption_threshold,
                        "casino_min_bet": server.casino_min_bet,
                        "casino_max_bet": server.casino_max_bet,
                        "casino_daily_limit": server.casino_daily_limit
                    }
                })
            
            return {
                "success": True,
                "servers": server_stats,
                "total_servers": len(server_stats)
            }
            
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            return {"success": False, "error": "Failed to get server statistics"}
    
    @staticmethod
    def register_server(server_id: str, server_name: str, owner_id: str) -> Dict[str, Any]:
        """Register a new server"""
        try:
            # Check if server already exists
            existing_server = Server.query.filter_by(id=server_id).first()
            if existing_server:
                # Update last activity
                existing_server.last_activity = datetime.utcnow()
                existing_server.is_active = True
                db.session.commit()
                return {"success": True, "message": "Server already registered, updated activity"}
            
            # Create new server
            server = Server(
                id=server_id,
                name=server_name,
                owner_id=owner_id,
                is_active=True
            )
            
            db.session.add(server)
            db.session.commit()
            
            return {
                "success": True,
                "server_id": server_id,
                "server_name": server_name,
                "message": "Server registered successfully"
            }
            
        except Exception as e:
            logger.error(f"Error registering server: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to register server"}