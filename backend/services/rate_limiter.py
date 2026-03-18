"""
Rate limiting configuration for API endpoints.

Protects the API from abuse and ensures fair usage across tenants.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from typing import Callable


def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    
    Uses authenticated user ID if available, otherwise falls back to IP address.
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.get('id', 'unknown')}"
    
    # Fallback to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["100/minute"],  # Global default limit
    storage_uri="redis://localhost:6379",  # Use Redis for distributed rate limiting
    strategy="fixed-window"
)


# Custom rate limits for different endpoint types
RATE_LIMITS = {
    # Authentication endpoints
    "auth": "10/minute",  # Prevent brute force
    
    # ERP connection management
    "erp_connection": "20/minute",  # Allow reasonable configuration changes
    
    # Data extraction (resource intensive)
    "erp_extraction": "5/minute",  # Limit heavy operations
    
    # Webhooks (external systems)
    "webhooks": "100/minute",  # Allow burst traffic from ERP systems
    
    # Metrics and monitoring
    "metrics": "30/minute",  # Reasonable monitoring frequency
    
    # Health checks
    "health_check": "30/minute",
    
    # General API operations
    "general": "60/minute"
}


def get_rate_limit(endpoint_type: str) -> str:
    """Get rate limit string for endpoint type."""
    return RATE_LIMITS.get(endpoint_type, RATE_LIMITS["general"])


# Rate limit decorators for common use cases
def auth_rate_limit():
    """Rate limit decorator for authentication endpoints."""
    return limiter.limit(RATE_LIMITS["auth"])


def erp_connection_rate_limit():
    """Rate limit decorator for ERP connection endpoints."""
    return limiter.limit(RATE_LIMITS["erp_connection"])


def erp_extraction_rate_limit():
    """Rate limit decorator for ERP extraction endpoints."""
    return limiter.limit(RATE_LIMITS["erp_extraction"])


def webhook_rate_limit():
    """Rate limit decorator for webhook endpoints."""
    return limiter.limit(RATE_LIMITS["webhooks"])


def metrics_rate_limit():
    """Rate limit decorator for metrics endpoints."""
    return limiter.limit(RATE_LIMITS["metrics"])


def health_check_rate_limit():
    """Rate limit decorator for health check endpoints."""
    return limiter.limit(RATE_LIMITS["health_check"])


def general_rate_limit():
    """Rate limit decorator for general endpoints."""
    return limiter.limit(RATE_LIMITS["general"])
