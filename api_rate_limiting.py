"""
API Rate Limiting System Module
Handles API rate limiting, throttling, and request management
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from app_context import app, db
from database import User

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API endpoints"""
    
    def __init__(self):
        # Rate limiting configuration
        self.rate_limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'casino': {'requests': 50, 'window': 3600},    # 50 casino games per hour
            'admin': {'requests': 200, 'window': 3600},    # 200 admin requests per hour
            'user_management': {'requests': 20, 'window': 3600},  # 20 user management requests per hour
            'analytics': {'requests': 10, 'window': 3600},  # 10 analytics requests per hour
            'bulk_operations': {'requests': 5, 'window': 3600},   # 5 bulk operations per hour
        }
        
        # Store request timestamps for each user and endpoint
        self.request_history = defaultdict(lambda: defaultdict(deque))
        
        # IP-based rate limiting
        self.ip_requests = defaultdict(lambda: defaultdict(deque))
        
        # Global rate limiting
        self.global_requests = deque()
    
    def check_rate_limit(self, user_id: str, endpoint: str, ip_address: str = None) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        try:
            current_time = time.time()
            
            # Get rate limit config for endpoint
            rate_config = self.rate_limits.get(endpoint, self.rate_limits['default'])
            max_requests = rate_config['requests']
            window_seconds = rate_config['window']
            
            # Check user-based rate limiting
            user_requests = self.request_history[user_id][endpoint]
            self._clean_old_requests(user_requests, current_time, window_seconds)
            
            if len(user_requests) >= max_requests:
                return {
                    "allowed": False,
                    "reason": "user_rate_limit_exceeded",
                    "limit": max_requests,
                    "window": window_seconds,
                    "reset_time": user_requests[0] + window_seconds if user_requests else current_time + window_seconds
                }
            
            # Check IP-based rate limiting (if IP provided)
            if ip_address:
                ip_requests = self.ip_requests[ip_address][endpoint]
                self._clean_old_requests(ip_requests, current_time, window_seconds)
                
                # IP limits are typically higher than user limits
                ip_max_requests = max_requests * 5
                
                if len(ip_requests) >= ip_max_requests:
                    return {
                        "allowed": False,
                        "reason": "ip_rate_limit_exceeded",
                        "limit": ip_max_requests,
                        "window": window_seconds,
                        "reset_time": ip_requests[0] + window_seconds if ip_requests else current_time + window_seconds
                    }
            
            # Check global rate limiting
            self._clean_old_requests(self.global_requests, current_time, window_seconds)
            global_max_requests = 10000  # Global limit
            
            if len(self.global_requests) >= global_max_requests:
                return {
                    "allowed": False,
                    "reason": "global_rate_limit_exceeded",
                    "limit": global_max_requests,
                    "window": window_seconds,
                    "reset_time": self.global_requests[0] + window_seconds if self.global_requests else current_time + window_seconds
                }
            
            # Record the request
            user_requests.append(current_time)
            if ip_address:
                ip_requests.append(current_time)
            self.global_requests.append(current_time)
            
            return {
                "allowed": True,
                "remaining": max_requests - len(user_requests),
                "reset_time": user_requests[0] + window_seconds if user_requests else current_time + window_seconds
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return {
                "allowed": False,
                "reason": "rate_limit_error",
                "error": str(e)
            }
    
    def _clean_old_requests(self, requests: deque, current_time: float, window_seconds: int):
        """Remove old requests outside the time window"""
        cutoff_time = current_time - window_seconds
        while requests and requests[0] < cutoff_time:
            requests.popleft()
    
    def get_rate_limit_status(self, user_id: str, endpoint: str) -> Dict[str, Any]:
        """Get current rate limit status for user and endpoint"""
        try:
            current_time = time.time()
            rate_config = self.rate_limits.get(endpoint, self.rate_limits['default'])
            max_requests = rate_config['requests']
            window_seconds = rate_config['window']
            
            user_requests = self.request_history[user_id][endpoint]
            self._clean_old_requests(user_requests, current_time, window_seconds)
            
            remaining = max(0, max_requests - len(user_requests))
            reset_time = user_requests[0] + window_seconds if user_requests else current_time + window_seconds
            
            return {
                "success": True,
                "endpoint": endpoint,
                "limit": max_requests,
                "remaining": remaining,
                "used": len(user_requests),
                "window_seconds": window_seconds,
                "reset_time": reset_time,
                "reset_in_seconds": max(0, reset_time - current_time)
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {"success": False, "error": str(e)}
    
    def update_rate_limits(self, new_limits: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Update rate limit configurations"""
        try:
            for endpoint, config in new_limits.items():
                if 'requests' in config and 'window' in config:
                    self.rate_limits[endpoint] = {
                        'requests': config['requests'],
                        'window': config['window']
                    }
            
            return {
                "success": True,
                "message": "Rate limits updated",
                "new_limits": self.rate_limits
            }
            
        except Exception as e:
            logger.error(f"Error updating rate limits: {e}")
            return {"success": False, "error": str(e)}
    
    def reset_user_rate_limit(self, user_id: str, endpoint: str = None) -> Dict[str, Any]:
        """Reset rate limit for a specific user"""
        try:
            if endpoint:
                if user_id in self.request_history and endpoint in self.request_history[user_id]:
                    self.request_history[user_id][endpoint].clear()
            else:
                if user_id in self.request_history:
                    self.request_history[user_id].clear()
            
            return {
                "success": True,
                "message": f"Rate limit reset for user {user_id}"
            }
            
        except Exception as e:
            logger.error(f"Error resetting user rate limit: {e}")
            return {"success": False, "error": str(e)}
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        try:
            current_time = time.time()
            
            # Count active rate limit entries
            active_users = 0
            total_requests = 0
            
            for user_id, endpoints in self.request_history.items():
                user_has_requests = False
                for endpoint, requests in endpoints.items():
                    self._clean_old_requests(requests, current_time, 3600)  # 1 hour window
                    if requests:
                        user_has_requests = True
                        total_requests += len(requests)
                
                if user_has_requests:
                    active_users += 1
            
            # Count active IPs
            active_ips = 0
            for ip, endpoints in self.ip_requests.items():
                ip_has_requests = False
                for endpoint, requests in endpoints.items():
                    self._clean_old_requests(requests, current_time, 3600)
                    if requests:
                        ip_has_requests = True
                
                if ip_has_requests:
                    active_ips += 1
            
            return {
                "success": True,
                "stats": {
                    "active_users": active_users,
                    "active_ips": active_ips,
                    "total_requests": total_requests,
                    "rate_limit_configs": len(self.rate_limits),
                    "configured_endpoints": list(self.rate_limits.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {"success": False, "error": str(e)}

class APIRateLimitManager:
    """Manager for API rate limiting"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
    
    def check_endpoint_rate_limit(self, user_id: str, endpoint: str, ip_address: str = None) -> Dict[str, Any]:
        """Check rate limit for specific endpoint"""
        return self.rate_limiter.check_rate_limit(user_id, endpoint, ip_address)
    
    def get_user_rate_limits(self, user_id: str) -> Dict[str, Any]:
        """Get all rate limits for a user"""
        try:
            rate_limits = {}
            for endpoint in self.rate_limiter.rate_limits.keys():
                status = self.rate_limiter.get_rate_limit_status(user_id, endpoint)
                if status['success']:
                    rate_limits[endpoint] = status
            
            return {
                "success": True,
                "user_id": user_id,
                "rate_limits": rate_limits
            }
            
        except Exception as e:
            logger.error(f"Error getting user rate limits: {e}")
            return {"success": False, "error": str(e)}
    
    def create_rate_limit_headers(self, rate_limit_result: Dict[str, Any]) -> Dict[str, str]:
        """Create HTTP headers for rate limiting"""
        headers = {}
        
        if rate_limit_result.get('allowed', False):
            headers['X-RateLimit-Remaining'] = str(rate_limit_result.get('remaining', 0))
            headers['X-RateLimit-Reset'] = str(int(rate_limit_result.get('reset_time', 0)))
        else:
            headers['X-RateLimit-Limit'] = str(rate_limit_result.get('limit', 0))
            headers['X-RateLimit-Reset'] = str(int(rate_limit_result.get('reset_time', 0)))
            headers['Retry-After'] = str(int(rate_limit_result.get('reset_time', 0) - time.time()))
        
        return headers
    
    def is_rate_limited(self, user_id: str, endpoint: str, ip_address: str = None) -> bool:
        """Simple check if request is rate limited"""
        result = self.check_endpoint_rate_limit(user_id, endpoint, ip_address)
        return not result.get('allowed', False)
    
    def get_rate_limit_info(self, user_id: str, endpoint: str) -> Dict[str, Any]:
        """Get detailed rate limit information"""
        return self.rate_limiter.get_rate_limit_status(user_id, endpoint)
    
    def update_rate_limits(self, new_limits: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Update rate limit configurations"""
        return self.rate_limiter.update_rate_limits(new_limits)
    
    def reset_user_limits(self, user_id: str, endpoint: str = None) -> Dict[str, Any]:
        """Reset rate limits for a user"""
        return self.rate_limiter.reset_user_rate_limit(user_id, endpoint)
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global rate limiting statistics"""
        return self.rate_limiter.get_rate_limit_stats()