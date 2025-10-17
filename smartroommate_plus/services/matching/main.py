"""
Matching Engine Service for SmartRoommate+
Handles AI-powered roommate matching and compatibility scoring
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any
import os
import sys
import math

# Add shared modules to path
sys.path.append('../shared')
from models import (
    UserProfileCreate, UserProfileResponse, MatchResult, MatchingRequest, APIResponse
)
from utils import (
    setup_logging, get_config, create_success_response, create_error_response,
    calculate_distance, normalize_score
)

# Configuration
config = get_config()
config.update({
    "service_name": "matching-service",
    "service_port": 8003,
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
    user_id = Column(Integer, nullable=False, index=True)
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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MatchHistory(Base):
    __tablename__ = "match_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    matched_user_id = Column(Integer, nullable=False, index=True)
    compatibility_score = Column(Float, nullable=False)
    ai_similarity = Column(Float, nullable=False)
    location_match = Column(Boolean, nullable=False)
    budget_match = Column(Boolean, nullable=False)
    distance_miles = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="SmartRoommate+ Matching Service",
    description="AI-powered roommate matching and compatibility scoring",
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

# AI Matching Engine
class MatchingEngine:
    def __init__(self):
        """Initialize the matching engine with AI model"""
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("AI model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load AI model: {str(e)}")
            raise
    
    def get_coordinates_from_zip(self, zip_code: str) -> tuple:
        """Get coordinates from ZIP code (mock implementation)"""
        mock_coords = {
            "75201": (32.7767, -96.7970),  # Dallas
            "75202": (32.7767, -96.7970),  # Dallas
            "78701": (30.2672, -97.7431),  # Austin
            "78702": (30.2672, -97.7431),  # Austin
            "10001": (40.7505, -73.9934),  # New York
            "90210": (34.0901, -118.4065), # Beverly Hills
        }
        return mock_coords.get(zip_code, (32.7767, -96.7970))
    
    def create_profile_text(self, profile: UserProfile) -> str:
        """Create text representation of profile for AI analysis"""
        text = f"""
        Occupation: {profile.occupation}
        Sleep Schedule: {profile.sleep_schedule}
        Cleanliness: {profile.cleanliness_level}
        Noise Tolerance: {profile.noise_tolerance}
        Hobbies: {profile.hobbies}
        Pet Preference: {profile.pet_preference}
        Smoking Preference: {profile.smoking_preference}
        Lifestyle: {profile.lifestyle_description}
        """
        return text.strip()
    
    def create_profile_text_from_dict(self, profile_data: dict) -> str:
        """Create text representation from profile dictionary"""
        text = f"""
        Occupation: {profile_data.get('occupation', '')}
        Sleep Schedule: {profile_data.get('sleep_schedule', '')}
        Cleanliness: {profile_data.get('cleanliness_level', '')}
        Noise Tolerance: {profile_data.get('noise_tolerance', '')}
        Hobbies: {profile_data.get('hobbies', '')}
        Pet Preference: {profile_data.get('pet_preference', '')}
        Smoking Preference: {profile_data.get('smoking_preference', '')}
        Lifestyle: {profile_data.get('lifestyle_description', '')}
        """
        return text.strip()
    
    def calculate_ai_similarity(self, profile1_text: str, profile2_text: str) -> float:
        """Calculate AI similarity between two profiles"""
        try:
            embeddings = self.model.encode([profile1_text, profile2_text])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            # Convert to percentage (0-100)
            return normalize_score((similarity + 1) * 50)
        except Exception as e:
            logger.error(f"AI similarity calculation error: {str(e)}")
            return 0.0
    
    def check_location_match(self, zip1: str, zip2: str, max_distance: float = 50.0) -> tuple:
        """Check if two locations are within acceptable distance"""
        try:
            lat1, lon1 = self.get_coordinates_from_zip(zip1)
            lat2, lon2 = self.get_coordinates_from_zip(zip2)
            distance = calculate_distance(lat1, lon1, lat2, lon2)
            return distance <= max_distance, distance
        except Exception as e:
            logger.error(f"Location match calculation error: {str(e)}")
            return False, float('inf')
    
    def check_budget_match(self, budget_min1: int, budget_max1: int, 
                          budget_min2: int, budget_max2: int) -> bool:
        """Check if two budgets overlap"""
        return not (budget_max1 < budget_min2 or budget_max2 < budget_min1)
    
    def calculate_compatibility_score(self, profile1: dict, profile2: dict) -> dict:
        """Calculate comprehensive compatibility score"""
        try:
            # Create profile texts
            text1 = self.create_profile_text_from_dict(profile1)
            text2 = self.create_profile_text_from_dict(profile2)
            
            # Calculate AI similarity
            ai_similarity = self.calculate_ai_similarity(text1, text2)
            
            # Check location match
            location_match, distance = self.check_location_match(
                profile1.get('zip_code', ''), profile2.get('zip_code', '')
            )
            
            # Check budget match
            budget_match = self.check_budget_match(
                profile1.get('rent_budget_min', 0), profile1.get('rent_budget_max', 0),
                profile2.get('rent_budget_min', 0), profile2.get('rent_budget_max', 0)
            )
            
            # Calculate final compatibility score
            location_score = 100 if location_match else 0
            budget_score = 100 if budget_match else 0
            
            final_score = (ai_similarity * 0.5) + (location_score * 0.3) + (budget_score * 0.2)
            
            # Generate match reasons
            match_reasons = []
            if ai_similarity > 70:
                match_reasons.append("High lifestyle compatibility")
            if location_match:
                match_reasons.append(f"Close proximity ({distance:.1f} miles)")
            if budget_match:
                match_reasons.append("Budget compatibility")
            if profile1.get('pet_preference') == profile2.get('pet_preference'):
                match_reasons.append("Pet preference match")
            if profile1.get('smoking_preference') == profile2.get('smoking_preference'):
                match_reasons.append("Smoking preference match")
            
            return {
                "compatibility_score": normalize_score(final_score),
                "ai_similarity": ai_similarity,
                "location_match": location_match,
                "budget_match": budget_match,
                "distance_miles": distance if location_match else None,
                "match_reasons": match_reasons
            }
            
        except Exception as e:
            logger.error(f"Compatibility calculation error: {str(e)}")
            return {
                "compatibility_score": 0.0,
                "ai_similarity": 0.0,
                "location_match": False,
                "budget_match": False,
                "distance_miles": None,
                "match_reasons": []
            }

# Initialize matching engine
matching_engine = MatchingEngine()

# Helper functions
def get_user_id_from_token(request: Request) -> int:
    """Extract user ID from JWT token"""
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in request")
    return int(user_id)

# API Endpoints
@app.post("/match", response_model=APIResponse)
async def find_matches(
    matching_request: MatchingRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Find matches for a user profile"""
    try:
        user_id = get_user_id_from_token(request)
        
        # Get all active profiles except the current user
        profiles = db.query(UserProfile).filter(
            UserProfile.is_active == True,
            UserProfile.user_id != user_id
        ).all()
        
        if not profiles:
            return create_success_response(
                "No matches found",
                {"matches": [], "total_profiles": 0}
            )
        
        # Convert request profile to dict
        profile_data = matching_request.user_profile.dict()
        
        # Calculate matches
        matches = []
        for profile in profiles:
            profile_dict = {
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
                "created_at": profile.created_at.isoformat()
            }
            
            # Calculate compatibility
            compatibility = matching_engine.calculate_compatibility_score(
                profile_data, profile_dict
            )
            
            # Only include matches with reasonable compatibility
            if compatibility["compatibility_score"] >= 30:
                match_result = {
                    "user": profile_dict,
                    "compatibility_score": compatibility["compatibility_score"],
                    "location_match": compatibility["location_match"],
                    "budget_match": compatibility["budget_match"],
                    "distance_miles": compatibility["distance_miles"],
                    "ai_similarity": compatibility["ai_similarity"],
                    "match_reasons": compatibility["match_reasons"]
                }
                matches.append(match_result)
        
        # Sort by compatibility score
        matches.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        # Limit results
        max_matches = min(matching_request.max_matches, len(matches))
        matches = matches[:max_matches]
        
        # Save match history
        for match in matches:
            match_history = MatchHistory(
                user_id=user_id,
                matched_user_id=match["user"]["id"],
                compatibility_score=match["compatibility_score"],
                ai_similarity=match["ai_similarity"],
                location_match=match["location_match"],
                budget_match=match["budget_match"],
                distance_miles=match["distance_miles"]
            )
            db.add(match_history)
        
        db.commit()
        
        logger.info(f"Found {len(matches)} matches for user {user_id}")
        
        return create_success_response(
            f"Found {len(matches)} matches",
            {
                "matches": matches,
                "total_profiles": len(profiles),
                "user_id": user_id
            }
        )
        
    except Exception as e:
        logger.error(f"Matching error: {str(e)}")
        return create_error_response("Matching failed", status_code=500)

@app.get("/match-history", response_model=APIResponse)
async def get_match_history(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's match history"""
    try:
        user_id = get_user_id_from_token(request)
        
        # Get match history
        query = db.query(MatchHistory).filter(MatchHistory.user_id == user_id)
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        history = query.order_by(MatchHistory.created_at.desc()).offset(offset).limit(per_page).all()
        
        # Format response
        history_data = []
        for match in history:
            history_data.append({
                "id": match.id,
                "matched_user_id": match.matched_user_id,
                "compatibility_score": match.compatibility_score,
                "ai_similarity": match.ai_similarity,
                "location_match": match.location_match,
                "budget_match": match.budget_match,
                "distance_miles": match.distance_miles,
                "created_at": match.created_at.isoformat()
            })
        
        pagination_info = {
            "items": history_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
        
        return create_success_response("Match history retrieved successfully", pagination_info)
        
    except Exception as e:
        logger.error(f"Match history retrieval error: {str(e)}")
        return create_error_response("Match history retrieval failed", status_code=500)

@app.post("/calculate-compatibility", response_model=APIResponse)
async def calculate_compatibility(
    profile1: dict,
    profile2: dict,
    db: Session = Depends(get_db)
):
    """Calculate compatibility between two profiles"""
    try:
        compatibility = matching_engine.calculate_compatibility_score(profile1, profile2)
        
        return create_success_response(
            "Compatibility calculated successfully",
            compatibility
        )
        
    except Exception as e:
        logger.error(f"Compatibility calculation error: {str(e)}")
        return create_error_response("Compatibility calculation failed", status_code=500)

@app.get("/stats", response_model=APIResponse)
async def get_matching_stats(db: Session = Depends(get_db)):
    """Get matching statistics"""
    try:
        # Get total profiles
        total_profiles = db.query(UserProfile).filter(UserProfile.is_active == True).count()
        
        # Get total matches
        total_matches = db.query(MatchHistory).count()
        
        # Get average compatibility score
        avg_score = db.query(MatchHistory.compatibility_score).all()
        avg_compatibility = np.mean([score[0] for score in avg_score]) if avg_score else 0
        
        stats = {
            "total_profiles": total_profiles,
            "total_matches": total_matches,
            "average_compatibility_score": float(avg_compatibility),
            "service_status": "healthy"
        }
        
        return create_success_response("Statistics retrieved successfully", stats)
        
    except Exception as e:
        logger.error(f"Statistics retrieval error: {str(e)}")
        return create_error_response("Statistics retrieval failed", status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "matching-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "ai_model_loaded": matching_engine.model is not None
    }

# Service startup
@app.on_event("startup")
async def startup_event():
    """Service startup event"""
    logger.info(f"Matching service starting on {config['service_host']}:{config['service_port']}")
    logger.info("Database connection established")
    logger.info("AI model loaded successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Service shutdown event"""
    logger.info("Matching service shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["service_host"],
        port=config["service_port"],
        log_level="info"
    )

