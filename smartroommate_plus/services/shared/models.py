"""
Shared components for SmartRoommate+ microservices
Common models, schemas, and utilities used across services
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Common Enums
class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    NON_BINARY = "Non-binary"
    OTHER = "Other"

class SleepSchedule(str, Enum):
    EARLY_BIRD = "Early Bird"
    NIGHT_OWL = "Night Owl"
    FLEXIBLE = "Flexible"

class CleanlinessLevel(str, Enum):
    VERY_CLEAN = "Very Clean"
    MODERATELY_CLEAN = "Moderately Clean"
    RELAXED = "Relaxed"

class NoiseTolerance(str, Enum):
    QUIET = "Quiet"
    MODERATE = "Moderate"
    LOUD_OK = "Loud OK"

class Preference(str, Enum):
    YES = "Yes"
    NO = "No"
    EITHER = "Either"

# Base Models
class BaseUserProfile(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=18, le=100)
    gender: Gender
    occupation: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    zip_code: str = Field(..., min_length=5, max_length=10)
    rent_budget_min: int = Field(..., ge=0)
    rent_budget_max: int = Field(..., ge=0)
    sleep_schedule: SleepSchedule
    cleanliness_level: CleanlinessLevel
    noise_tolerance: NoiseTolerance
    hobbies: str = Field(..., min_length=1)
    pet_preference: Preference
    smoking_preference: Preference
    lifestyle_description: str = Field(..., min_length=10)

class UserProfileCreate(BaseUserProfile):
    pass

class UserProfileResponse(BaseUserProfile):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Matching Models
class MatchResult(BaseModel):
    user: UserProfileResponse
    compatibility_score: float = Field(..., ge=0, le=100)
    location_match: bool
    budget_match: bool
    distance_miles: Optional[float] = None
    ai_similarity: Optional[float] = None
    match_reasons: List[str] = []

class MatchingRequest(BaseModel):
    user_profile: UserProfileCreate
    max_matches: int = Field(default=5, ge=1, le=20)

# Authentication Models
class UserAuth(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool = True
    created_at: datetime

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    confirm_password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None

# API Response Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

# Service Communication Models
class ServiceRequest(BaseModel):
    service: str
    endpoint: str
    method: str
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None

class ServiceResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: int

# Health Check Models
class HealthCheck(BaseModel):
    service: str
    status: str
    timestamp: datetime
    version: str
    dependencies: Dict[str, str] = {}

# Rate Limiting Models
class RateLimit(BaseModel):
    limit: int
    remaining: int
    reset_time: datetime

class RateLimitInfo(BaseModel):
    user_id: Optional[int] = None
    ip_address: str
    endpoint: str
    limit: int
    remaining: int
    reset_time: datetime

# Error Models
class ErrorDetail(BaseModel):
    field: str
    message: str
    code: str

class ValidationError(BaseModel):
    errors: List[ErrorDetail]
    message: str = "Validation failed"

# Configuration Models
class DatabaseConfig(BaseModel):
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

class ServiceConfig(BaseModel):
    name: str
    host: str = "0.0.0.0"
    port: int
    debug: bool = False
    database: DatabaseConfig
    redis: Optional[RedisConfig] = None

# Utility Functions
def create_api_response(success: bool, message: str, data: Any = None, errors: List[str] = None) -> APIResponse:
    """Create a standardized API response"""
    return APIResponse(
        success=success,
        message=message,
        data=data,
        errors=errors
    )

def create_error_response(message: str, errors: List[str] = None) -> APIResponse:
    """Create an error API response"""
    return create_api_response(False, message, errors=errors)

def create_success_response(message: str, data: Any = None) -> APIResponse:
    """Create a success API response"""
    return create_api_response(True, message, data=data)

