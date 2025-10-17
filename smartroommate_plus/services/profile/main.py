"""
Profile Management Service for SmartRoommate+
Handles user profile creation, updates, and retrieval
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional, List
import os
import sys

# Add shared modules to path
sys.path.append('../shared')
from models import (
    UserProfileCreate, UserProfileResponse, APIResponse, PaginatedResponse
)
from utils import (
    setup_logging, get_config, create_success_response, create_error_response,
    sanitize_input, validate_zip_code, calculate_distance
)

# Configuration
config = get_config()
config.update({
    "service_name": "profile-service",
    "service_port": 8002,
    "service_host": "0.0.0.0"
})

# Database setup
DATABASE_URL = config["database_url"]
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Reference to auth service
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    occupation = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    zip_code = Column(String(10), nullable=False)
    rent_budget_min = Column(Integer, nullable=False)
    rent_budget_max = Column(Integer, nullable=False)
    sleep_schedule = Column(String(50), nullable=False)
    cleanliness_level = Column(String(50), nullable=False)
    noise_tolerance = Column(String(50), nullable=False)
    hobbies = Column(Text, nullable=False)
    pet_preference = Column(String(20), nullable=False)
    smoking_preference = Column(String(20), nullable=False)
    lifestyle_description = Column(Text, nullable=False)
    
    # Optional social media links
    instagram_link = Column(String(200), nullable=True)
    facebook_link = Column(String(200), nullable=True)
    linkedin_link = Column(String(200), nullable=True)
    twitter_link = Column(String(200), nullable=True)
    
    # Profile metadata
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="SmartRoommate+ Profile Service",
    description="Handles user profile management and retrieval",
    version="1.0.0"
)

# Logging
logger = setup_logging(config["service_name"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def get_user_id_from_token(request: Request) -> int:
    """Extract user ID from JWT token"""
    # This would typically be handled by the API Gateway
    # For now, we'll simulate it
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in request")
    return int(user_id)

def validate_profile_data(profile_data: UserProfileCreate) -> List[str]:
    """Validate profile data"""
    errors = []
    
    # Validate budget range
    if profile_data.rent_budget_min > profile_data.rent_budget_max:
        errors.append("Minimum budget cannot be greater than maximum budget")
    
    # Validate ZIP code format
    if not validate_zip_code(profile_data.zip_code):
        errors.append("Invalid ZIP code format")
    
    # Validate age
    if profile_data.age < 18 or profile_data.age > 100:
        errors.append("Age must be between 18 and 100")
    
    return errors

def get_coordinates_from_zip(zip_code: str) -> tuple:
    """Get coordinates from ZIP code (mock implementation)"""
    # In production, this would use a geocoding service
    mock_coords = {
        "75201": (32.7767, -96.7970),  # Dallas
        "75202": (32.7767, -96.7970),  # Dallas
        "78701": (30.2672, -97.7431),  # Austin
        "78702": (30.2672, -97.7431),  # Austin
        "10001": (40.7505, -73.9934),  # New York
        "90210": (34.0901, -118.4065), # Beverly Hills
    }
    return mock_coords.get(zip_code, (32.7767, -96.7970))

# API Endpoints
@app.post("/profiles", response_model=APIResponse)
async def create_profile(
    profile_data: UserProfileCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new user profile"""
    try:
        # Get user ID from token
        user_id = get_user_id_from_token(request)
        
        # Validate profile data
        validation_errors = validate_profile_data(profile_data)
        if validation_errors:
            return create_error_response("Validation failed", validation_errors, 400)
        
        # Check if profile already exists for this user
        existing_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if existing_profile:
            return create_error_response("Profile already exists for this user", status_code=400)
        
        # Create new profile
        db_profile = UserProfile(
            user_id=user_id,
            name=sanitize_input(profile_data.name),
            age=profile_data.age,
            gender=profile_data.gender.value,
            occupation=sanitize_input(profile_data.occupation),
            city=sanitize_input(profile_data.city),
            zip_code=profile_data.zip_code,
            rent_budget_min=profile_data.rent_budget_min,
            rent_budget_max=profile_data.rent_budget_max,
            sleep_schedule=profile_data.sleep_schedule.value,
            cleanliness_level=profile_data.cleanliness_level.value,
            noise_tolerance=profile_data.noise_tolerance.value,
            hobbies=sanitize_input(profile_data.hobbies),
            pet_preference=profile_data.pet_preference.value,
            smoking_preference=profile_data.smoking_preference.value,
            lifestyle_description=sanitize_input(profile_data.lifestyle_description)
        )
        
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        
        logger.info(f"Profile created for user {user_id}")
        
        return create_success_response(
            "Profile created successfully",
            {
                "profile_id": db_profile.id,
                "user_id": db_profile.user_id,
                "name": db_profile.name
            }
        )
        
    except Exception as e:
        logger.error(f"Profile creation error: {str(e)}")
        return create_error_response("Profile creation failed", status_code=500)

@app.get("/profiles/me", response_model=APIResponse)
async def get_my_profile(request: Request, db: Session = Depends(get_db)):
    """Get current user's profile"""
    try:
        user_id = get_user_id_from_token(request)
        
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.is_active == True
        ).first()
        
        if not profile:
            return create_error_response("Profile not found", status_code=404)
        
        profile_data = {
            "id": profile.id,
            "user_id": profile.user_id,
            "name": profile.name,
            "age": profile.age,
            "gender": profile.gender,
            "occupation": profile.occupation,
            "city": profile.city,
            "zip_code": profile.zip_code,
            "rent_budget_min": profile.rent_budget_min,
            "rent_budget_max": profile.rent_budget_max,
            "sleep_schedule": profile.sleep_schedule,
            "cleanliness_level": profile.cleanliness_level,
            "noise_tolerance": profile.noise_tolerance,
            "hobbies": profile.hobbies,
            "pet_preference": profile.pet_preference,
            "smoking_preference": profile.smoking_preference,
            "lifestyle_description": profile.lifestyle_description,
            "instagram_link": profile.instagram_link,
            "facebook_link": profile.facebook_link,
            "linkedin_link": profile.linkedin_link,
            "twitter_link": profile.twitter_link,
            "is_verified": profile.is_verified,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }
        
        return create_success_response("Profile retrieved successfully", profile_data)
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        return create_error_response("Profile retrieval failed", status_code=500)

@app.put("/profiles/me", response_model=APIResponse)
async def update_my_profile(
    profile_data: UserProfileCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    try:
        user_id = get_user_id_from_token(request)
        
        # Validate profile data
        validation_errors = validate_profile_data(profile_data)
        if validation_errors:
            return create_error_response("Validation failed", validation_errors, 400)
        
        # Find existing profile
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.is_active == True
        ).first()
        
        if not profile:
            return create_error_response("Profile not found", status_code=404)
        
        # Update profile
        profile.name = sanitize_input(profile_data.name)
        profile.age = profile_data.age
        profile.gender = profile_data.gender.value
        profile.occupation = sanitize_input(profile_data.occupation)
        profile.city = sanitize_input(profile_data.city)
        profile.zip_code = profile_data.zip_code
        profile.rent_budget_min = profile_data.rent_budget_min
        profile.rent_budget_max = profile_data.rent_budget_max
        profile.sleep_schedule = profile_data.sleep_schedule.value
        profile.cleanliness_level = profile_data.cleanliness_level.value
        profile.noise_tolerance = profile_data.noise_tolerance.value
        profile.hobbies = sanitize_input(profile_data.hobbies)
        profile.pet_preference = profile_data.pet_preference.value
        profile.smoking_preference = profile_data.smoking_preference.value
        profile.lifestyle_description = sanitize_input(profile_data.lifestyle_description)
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Profile updated for user {user_id}")
        
        return create_success_response("Profile updated successfully")
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return create_error_response("Profile update failed", status_code=500)

@app.put("/profiles/me/social-links", response_model=APIResponse)
async def update_social_links(
    instagram_link: Optional[str] = None,
    facebook_link: Optional[str] = None,
    linkedin_link: Optional[str] = None,
    twitter_link: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Update social media links"""
    try:
        user_id = get_user_id_from_token(request)
        
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.is_active == True
        ).first()
        
        if not profile:
            return create_error_response("Profile not found", status_code=404)
        
        # Update social links
        if instagram_link is not None:
            profile.instagram_link = sanitize_input(instagram_link)
        if facebook_link is not None:
            profile.facebook_link = sanitize_input(facebook_link)
        if linkedin_link is not None:
            profile.linkedin_link = sanitize_input(linkedin_link)
        if twitter_link is not None:
            profile.twitter_link = sanitize_input(twitter_link)
        
        profile.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Social links updated for user {user_id}")
        
        return create_success_response("Social links updated successfully")
        
    except Exception as e:
        logger.error(f"Social links update error: {str(e)}")
        return create_error_response("Social links update failed", status_code=500)

@app.get("/profiles", response_model=APIResponse)
async def get_all_profiles(
    page: int = 1,
    per_page: int = 20,
    city: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all profiles with optional filtering"""
    try:
        query = db.query(UserProfile).filter(UserProfile.is_active == True)
        
        # Apply filters
        if city:
            query = query.filter(UserProfile.city.ilike(f"%{city}%"))
        if min_age:
            query = query.filter(UserProfile.age >= min_age)
        if max_age:
            query = query.filter(UserProfile.age <= max_age)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        profiles = query.offset(offset).limit(per_page).all()
        
        # Format response
        profiles_data = []
        for profile in profiles:
            profiles_data.append({
                "id": profile.id,
                "name": profile.name,
                "age": profile.age,
                "gender": profile.gender,
                "occupation": profile.occupation,
                "city": profile.city,
                "zip_code": profile.zip_code,
                "rent_budget_min": profile.rent_budget_min,
                "rent_budget_max": profile.rent_budget_max,
                "sleep_schedule": profile.sleep_schedule,
                "cleanliness_level": profile.cleanliness_level,
                "noise_tolerance": profile.noise_tolerance,
                "hobbies": profile.hobbies,
                "pet_preference": profile.pet_preference,
                "smoking_preference": profile.smoking_preference,
                "lifestyle_description": profile.lifestyle_description,
                "is_verified": profile.is_verified,
                "created_at": profile.created_at.isoformat()
            })
        
        pagination_info = {
            "items": profiles_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
        
        return create_success_response("Profiles retrieved successfully", pagination_info)
        
    except Exception as e:
        logger.error(f"Profiles retrieval error: {str(e)}")
        return create_error_response("Profiles retrieval failed", status_code=500)

@app.get("/profiles/{profile_id}", response_model=APIResponse)
async def get_profile_by_id(profile_id: int, db: Session = Depends(get_db)):
    """Get profile by ID"""
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.id == profile_id,
            UserProfile.is_active == True
        ).first()
        
        if not profile:
            return create_error_response("Profile not found", status_code=404)
        
        profile_data = {
            "id": profile.id,
            "name": profile.name,
            "age": profile.age,
            "gender": profile.gender,
            "occupation": profile.occupation,
            "city": profile.city,
            "zip_code": profile.zip_code,
            "rent_budget_min": profile.rent_budget_min,
            "rent_budget_max": profile.rent_budget_max,
            "sleep_schedule": profile.sleep_schedule,
            "cleanliness_level": profile.cleanliness_level,
            "noise_tolerance": profile.noise_tolerance,
            "hobbies": profile.hobbies,
            "pet_preference": profile.pet_preference,
            "smoking_preference": profile.smoking_preference,
            "lifestyle_description": profile.lifestyle_description,
            "instagram_link": profile.instagram_link,
            "facebook_link": profile.facebook_link,
            "linkedin_link": profile.linkedin_link,
            "twitter_link": profile.twitter_link,
            "is_verified": profile.is_verified,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }
        
        return create_success_response("Profile retrieved successfully", profile_data)
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        return create_error_response("Profile retrieval failed", status_code=500)

@app.delete("/profiles/me", response_model=APIResponse)
async def delete_my_profile(request: Request, db: Session = Depends(get_db)):
    """Delete current user's profile"""
    try:
        user_id = get_user_id_from_token(request)
        
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.is_active == True
        ).first()
        
        if not profile:
            return create_error_response("Profile not found", status_code=404)
        
        # Soft delete
        profile.is_active = False
        profile.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Profile deleted for user {user_id}")
        
        return create_success_response("Profile deleted successfully")
        
    except Exception as e:
        logger.error(f"Profile deletion error: {str(e)}")
        return create_error_response("Profile deletion failed", status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "profile-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Service startup
@app.on_event("startup")
async def startup_event():
    """Service startup event"""
    logger.info(f"Profile service starting on {config['service_host']}:{config['service_port']}")
    logger.info("Database connection established")

@app.on_event("shutdown")
async def shutdown_event():
    """Service shutdown event"""
    logger.info("Profile service shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["service_host"],
        port=config["service_port"],
        log_level="info"
    )

