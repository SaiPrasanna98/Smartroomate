"""
Shared utilities for SmartRoommate+ microservices
Common functions, decorators, and helpers used across services
"""

import os
import logging
import json
import hashlib
import secrets
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from functools import wraps
import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

# Logging Configuration
def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """Setup logging for a service"""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# JWT Utilities
def create_access_token(data: Dict[str, Any], secret_key: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str, secret_key: str) -> Dict[str, Any]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Password Utilities
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        salt, password_hash = hashed_password.split(":")
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except ValueError:
        return False

# Rate Limiting
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window)
        
        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key] 
                if req_time > window_start
            ]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

# Decorators
def rate_limit(limit: int = 100, window: int = 3600):
    """Rate limiting decorator"""
    limiter = RateLimiter()
    
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get client IP
            client_ip = request.client.host
            
            # Check rate limit
            if not limiter.is_allowed(client_ip, limit, window):
                raise HTTPException(
                    status_code=429, 
                    detail="Rate limit exceeded"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_auth(func):
    """Authentication required decorator"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Get token from header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        
        token = authorization.split(" ")[1]
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        
        try:
            payload = verify_token(token, secret_key)
            request.state.user_id = payload.get("user_id")
            request.state.user_email = payload.get("email")
        except HTTPException:
            raise
        
        return await func(request, *args, **kwargs)
    return wrapper

# Error Handling
def handle_exceptions(func):
    """Global exception handler decorator"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger = logging.getLogger(func.__module__)
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper

# Configuration
def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables"""
    return {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./smartroommate.db"),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "jwt_secret_key": os.getenv("JWT_SECRET_KEY", "your-secret-key"),
        "jwt_expire_minutes": int(os.getenv("JWT_EXPIRE_MINUTES", "30")),
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        "service_name": os.getenv("SERVICE_NAME", "smartroommate"),
        "service_port": int(os.getenv("SERVICE_PORT", "8000")),
        "service_host": os.getenv("SERVICE_HOST", "0.0.0.0")
    }

# Service Discovery
class ServiceRegistry:
    """Simple service registry for microservices"""
    
    def __init__(self):
        self.services = {}
    
    def register_service(self, name: str, host: str, port: int, health_endpoint: str = "/health"):
        """Register a service"""
        self.services[name] = {
            "host": host,
            "port": port,
            "health_endpoint": health_endpoint,
            "registered_at": datetime.utcnow()
        }
    
    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service information"""
        return self.services.get(name)
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all registered services"""
        return self.services.copy()

# HTTP Client Utilities
async def make_service_request(service_name: str, endpoint: str, method: str = "GET", 
                             data: Optional[Dict[str, Any]] = None, 
                             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Make HTTP request to another service"""
    import httpx
    
    # Get service info from registry
    registry = ServiceRegistry()
    service_info = registry.get_service(service_name)
    
    if not service_info:
        raise HTTPException(status_code=503, detail=f"Service {service_name} not available")
    
    # Build URL
    url = f"http://{service_info['host']}:{service_info['port']}{endpoint}"
    
    # Make request
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"Service {service_name} error: {str(e)}")

# Validation Utilities
def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[^@]+@[^@]+\.[^@]+$'
    return re.match(pattern, email) is not None

def validate_zip_code(zip_code: str) -> bool:
    """Validate ZIP code format"""
    import re
    pattern = r'^\d{5}(-\d{4})?$'
    return re.match(pattern, zip_code) is not None

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

# Data Processing Utilities
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    import math
    
    R = 3959  # Earth's radius in miles
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def normalize_score(score: float, min_val: float = 0, max_val: float = 100) -> float:
    """Normalize score to specified range"""
    if score < min_val:
        return min_val
    elif score > max_val:
        return max_val
    else:
        return score

# Response Utilities
def create_success_response(message: str, data: Any = None) -> Dict[str, Any]:
    """Create standardized success response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }

def create_error_response(message: str, errors: List[str] = None, status_code: int = 400) -> JSONResponse:
    """Create standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "errors": errors or [],
            "timestamp": datetime.utcnow().isoformat()
        }
    )

