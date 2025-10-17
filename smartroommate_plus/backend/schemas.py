from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=18, le=100)
    gender: str = Field(..., pattern="^(Male|Female|Non-binary|Other)$")
    occupation: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    zip_code: str = Field(..., min_length=5, max_length=10)
    rent_budget_min: int = Field(..., ge=0)
    rent_budget_max: int = Field(..., ge=0)
    sleep_schedule: str = Field(..., pattern="^(Early Bird|Night Owl|Flexible)$")
    cleanliness_level: str = Field(..., pattern="^(Very Clean|Moderately Clean|Relaxed)$")
    noise_tolerance: str = Field(..., pattern="^(Quiet|Moderate|Loud OK)$")
    hobbies: str = Field(..., min_length=1)
    pet_preference: str = Field(..., pattern="^(Yes|No|Either)$")
    smoking_preference: str = Field(..., pattern="^(Yes|No|Either)$")
    lifestyle_description: str = Field(..., min_length=10)
    
    # Optional social media links
    instagram_link: Optional[str] = Field(None, max_length=200)
    facebook_link: Optional[str] = Field(None, max_length=200)
    linkedin_link: Optional[str] = Field(None, max_length=200)
    twitter_link: Optional[str] = Field(None, max_length=200)

class UserProfileResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    occupation: str
    city: str
    zip_code: str
    rent_budget_min: int
    rent_budget_max: int
    sleep_schedule: str
    cleanliness_level: str
    noise_tolerance: str
    hobbies: str
    pet_preference: str
    smoking_preference: str
    lifestyle_description: str
    
    # Optional social media links
    instagram_link: Optional[str] = None
    facebook_link: Optional[str] = None
    linkedin_link: Optional[str] = None
    twitter_link: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True

class MatchResult(BaseModel):
    user: UserProfileResponse
    compatibility_score: float = Field(..., ge=0, le=100)
    location_match: bool
    budget_match: bool
    distance_miles: Optional[float] = None

class MatchingRequest(BaseModel):
    user_profile: UserProfileCreate
