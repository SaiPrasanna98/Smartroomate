"""
API Gateway for SmartRoommate+ Microservices
Handles routing, rate limiting, authentication, and load balancing
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import httpx
import redis
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import sys
import time

# Add shared modules to path
sys.path.append('../shared')
from models import APIResponse, RateLimitInfo
from utils import (
    setup_logging, get_config, create_success_response, create_error_response,
    rate_limit, require_auth, verify_token
)

# Configuration
config = get_config()
config.update({
    "service_name": "api-gateway",
    "service_port": 8000,
    "service_host": "0.0.0.0"
})

# Service registry
SERVICE_REGISTRY = {
    "auth-service": {"host": "localhost", "port": 8001},
    "profile-service": {"host": "localhost", "port": 8002},
    "matching-service": {"host": "localhost", "port": 8003}
}

# FastAPI app
app = FastAPI(
    title="SmartRoommate+ API Gateway",
    description="Central gateway for all microservices",
    version="1.0.0"
)

# Logging
logger = setup_logging(config["service_name"])

# Redis for rate limiting
redis_client = None
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {str(e)}")
    redis_client = None

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Rate limiting
class RateLimiter:
    def __init__(self):
        self.redis_client = redis_client
        self.memory_store = {} if not redis_client else None
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit"""
        if self.redis_client:
            return self._redis_rate_limit(key, limit, window)
        else:
            return self._memory_rate_limit(key, limit, window)
    
    def _redis_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Redis-based rate limiting"""
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Use Redis sorted set for sliding window
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_count = results[1]
            
            return current_count < limit
        except Exception as e:
            logger.error(f"Redis rate limiting error: {str(e)}")
            return True  # Allow request if Redis fails
    
    def _memory_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Memory-based rate limiting"""
        current_time = time.time()
        window_start = current_time - window
        
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # Clean old entries
        self.memory_store[key] = [
            req_time for req_time in self.memory_store[key] 
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.memory_store[key]) >= limit:
            return False
        
        # Add current request
        self.memory_store[key].append(current_time)
        return True

rate_limiter = RateLimiter()

# Authentication middleware
async def authenticate_request(request: Request) -> Optional[Dict[str, Any]]:
    """Authenticate incoming request"""
    # Skip authentication for certain endpoints
    skip_auth_paths = ["/health", "/docs", "/openapi.json", "/auth/login", "/auth/register"]
    if request.url.path in skip_auth_paths:
        return None
    
    # Get token from header
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.split(" ")[1]
    secret_key = config["jwt_secret_key"]
    
    try:
        payload = verify_token(token, secret_key)
        return payload
    except HTTPException:
        raise

# Rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Get client identifier
    client_ip = request.client.host
    user_id = request.headers.get("X-User-ID", "anonymous")
    
    # Create rate limit key
    rate_limit_key = f"rate_limit:{client_ip}:{user_id}"
    
    # Check rate limit (100 requests per hour)
    if not rate_limiter.is_allowed(rate_limit_key, 100, 3600):
        return JSONResponse(
            status_code=429,
            content=create_error_response("Rate limit exceeded").dict()
        )
    
    response = await call_next(request)
    return response

# Service routing
async def route_to_service(service_name: str, path: str, method: str, 
                          request: Request, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Route request to appropriate microservice"""
    if service_name not in SERVICE_REGISTRY:
        raise HTTPException(status_code=503, detail=f"Service {service_name} not available")
    
    service_info = SERVICE_REGISTRY[service_name]
    url = f"http://{service_info['host']}:{service_info['port']}{path}"
    
    # Prepare headers
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header
    
    # Add user information if authenticated
    auth_info = await authenticate_request(request)
    if auth_info:
        headers["X-User-ID"] = str(auth_info.get("user_id"))
        headers["X-User-Email"] = auth_info.get("email")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
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
            
            return response.json()
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail=f"Service {service_name} timeout")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"Service {service_name} error: {str(e)}")

# Add middleware
app.middleware("http")(rate_limit_middleware)

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return create_success_response(
        "SmartRoommate+ API Gateway",
        {
            "version": "1.0.0",
            "services": list(SERVICE_REGISTRY.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Authentication Service Routes
@app.post("/auth/register")
async def register_user(request: Request):
    """Register new user"""
    data = await request.json()
    return await route_to_service("auth-service", "/register", "POST", request, data)

@app.post("/auth/login")
async def login_user(request: Request):
    """Login user"""
    data = await request.json()
    return await route_to_service("auth-service", "/login", "POST", request, data)

@app.get("/auth/me")
async def get_current_user(request: Request):
    """Get current user info"""
    return await route_to_service("auth-service", "/me", "GET", request)

@app.post("/auth/logout")
async def logout_user(request: Request):
    """Logout user"""
    return await route_to_service("auth-service", "/logout", "POST", request)

@app.put("/auth/change-password")
async def change_password(request: Request):
    """Change user password"""
    data = await request.json()
    return await route_to_service("auth-service", "/change-password", "PUT", request, data)

@app.get("/auth/verify-token")
async def verify_token_endpoint(request: Request):
    """Verify JWT token"""
    return await route_to_service("auth-service", "/verify-token", "GET", request)

# Profile Service Routes
@app.post("/profiles")
async def create_profile(request: Request):
    """Create user profile"""
    data = await request.json()
    return await route_to_service("profile-service", "/profiles", "POST", request, data)

@app.get("/profiles/me")
async def get_my_profile(request: Request):
    """Get current user's profile"""
    return await route_to_service("profile-service", "/profiles/me", "GET", request)

@app.put("/profiles/me")
async def update_my_profile(request: Request):
    """Update current user's profile"""
    data = await request.json()
    return await route_to_service("profile-service", "/profiles/me", "PUT", request, data)

@app.put("/profiles/me/social-links")
async def update_social_links(request: Request):
    """Update social media links"""
    data = await request.json()
    return await route_to_service("profile-service", "/profiles/me/social-links", "PUT", request, data)

@app.get("/profiles")
async def get_all_profiles(request: Request):
    """Get all profiles"""
    return await route_to_service("profile-service", "/profiles", "GET", request)

@app.get("/profiles/{profile_id}")
async def get_profile_by_id(profile_id: int, request: Request):
    """Get profile by ID"""
    return await route_to_service("profile-service", f"/profiles/{profile_id}", "GET", request)

@app.delete("/profiles/me")
async def delete_my_profile(request: Request):
    """Delete current user's profile"""
    return await route_to_service("profile-service", "/profiles/me", "DELETE", request)

# Matching Service Routes
@app.post("/match")
async def find_matches(request: Request):
    """Find roommate matches"""
    data = await request.json()
    return await route_to_service("matching-service", "/match", "POST", request, data)

@app.get("/match-history")
async def get_match_history(request: Request):
    """Get match history"""
    return await route_to_service("matching-service", "/match-history", "GET", request)

@app.post("/calculate-compatibility")
async def calculate_compatibility(request: Request):
    """Calculate compatibility between profiles"""
    data = await request.json()
    return await route_to_service("matching-service", "/calculate-compatibility", "POST", request, data)

@app.get("/stats")
async def get_matching_stats(request: Request):
    """Get matching statistics"""
    return await route_to_service("matching-service", "/stats", "GET", request)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Gateway health check"""
    service_status = {}
    
    # Check each service
    for service_name, service_info in SERVICE_REGISTRY.items():
        try:
            url = f"http://{service_info['host']}:{service_info['port']}/health"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                service_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception as e:
            service_status[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return {
        "gateway": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": service_status,
        "redis": "connected" if redis_client else "disconnected"
    }

@app.get("/health/{service_name}")
async def service_health_check(service_name: str):
    """Check specific service health"""
    if service_name not in SERVICE_REGISTRY:
        raise HTTPException(status_code=404, detail="Service not found")
    
    try:
        return await route_to_service(service_name, "/health", "GET", Request)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service {service_name} is unhealthy: {str(e)}")

# Service discovery
@app.get("/services")
async def list_services():
    """List all registered services"""
    return create_success_response(
        "Services retrieved successfully",
        {
            "services": SERVICE_REGISTRY,
            "total_services": len(SERVICE_REGISTRY)
        }
    )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.detail).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=create_error_response("Internal server error").dict()
    )

# Service startup
@app.on_event("startup")
async def startup_event():
    """Service startup event"""
    logger.info(f"API Gateway starting on {config['service_host']}:{config['service_port']}")
    logger.info(f"Registered services: {list(SERVICE_REGISTRY.keys())}")
    
    if redis_client:
        logger.info("Redis connection established for rate limiting")
    else:
        logger.warning("Redis not available, using memory-based rate limiting")

@app.on_event("shutdown")
async def shutdown_event():
    """Service shutdown event"""
    logger.info("API Gateway shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["service_host"],
        port=config["service_port"],
        log_level="info"
    )

