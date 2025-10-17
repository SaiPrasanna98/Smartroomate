from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import os

from database import get_db, create_tables
from models import UserProfile
from schemas import UserProfileCreate, UserProfileResponse, MatchResult, MatchingRequest
from match_engine import MatchingEngine

# Initialize FastAPI app
app = FastAPI(title="SmartRoommate+ API", version="1.0.0")

# Initialize matching engine
matching_engine = MatchingEngine()

# Create database tables
create_tables()

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(current_dir), 'frontend')

# Mount static files
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Templates
templates = Jinja2Templates(directory=frontend_dir)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main form page"""
    with open(os.path.join(frontend_dir, "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/results", response_class=HTMLResponse)
async def read_results():
    """Serve the results page"""
    with open(os.path.join(frontend_dir, "results.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/profiles", response_model=UserProfileResponse)
async def create_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    """Create a new user profile"""
    db_profile = UserProfile(**profile.dict())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@app.post("/api/match", response_model=List[MatchResult])
async def find_matches(request: MatchingRequest, db: Session = Depends(get_db)):
    """Find matches for a user profile"""
    # First, save the profile to the database
    db_profile = UserProfile(**request.user_profile.dict())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    # Find matches
    matches = matching_engine.find_matches(request.user_profile, db)
    
    return matches

@app.get("/api/profiles", response_model=List[UserProfileResponse])
async def get_all_profiles(db: Session = Depends(get_db)):
    """Get all user profiles"""
    profiles = db.query(UserProfile).all()
    return profiles

@app.get("/api/profiles/{profile_id}", response_model=UserProfileResponse)
async def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """Get a specific user profile"""
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
