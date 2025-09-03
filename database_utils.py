"""
Database utility functions to prevent memory issues and improve query performance
"""

from typing import List, Optional
from sqlalchemy.orm import Query
from database import User

class DatabaseUtils:
    """Utility class for safe database operations"""
    
    # Default limits to prevent memory issues
    DEFAULT_USER_LIMIT = 1000
    DEFAULT_QUERY_LIMIT = 100
    
    @staticmethod
    def get_active_users(limit: Optional[int] = None) -> List[User]:
        """
        Get active users with a safe limit to prevent memory issues
        
        Args:
            limit: Maximum number of users to return (default: 1000)
            
        Returns:
            List of active users
        """
        if limit is None:
            limit = DatabaseUtils.DEFAULT_USER_LIMIT
            
        return User.query.filter(User.user_status == 'active').limit(limit).all()
    
    @staticmethod
    def get_users_paginated(page: int = 1, per_page: int = 100) -> Query:
        """
        Get users with pagination support
        
        Args:
            page: Page number (1-based)
            per_page: Number of users per page
            
        Returns:
            SQLAlchemy Query object with pagination
        """
        offset = (page - 1) * per_page
        return User.query.filter(User.user_status == 'active').offset(offset).limit(per_page)
    
    @staticmethod
    def count_active_users() -> int:
        """
        Count active users without loading them into memory
        
        Returns:
            Number of active users
        """
        return User.query.filter(User.user_status == 'active').count()
    
    @staticmethod
    def safe_query_execution(query_func, max_retries: int = 3):
        """
        Execute a database query with error handling and retries
        
        Args:
            query_func: Function that executes the database query
            max_retries: Maximum number of retry attempts
            
        Returns:
            Query result or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                return query_func()
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Database query failed after {max_retries} attempts: {e}")
                    return None
                else:
                    print(f"Database query attempt {attempt + 1} failed: {e}")
                    continue
        return None