import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import tempfile
import os

# Import your application components
import sys
sys.path.append('backend')
from main import app
from database import get_db, Base
from models import UserProfile
from schemas import UserProfileCreate, MatchResult
from match_engine import MatchingEngine

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        "name": "John Doe",
        "age": 25,
        "gender": "Male",
        "occupation": "Software Engineer",
        "city": "Dallas",
        "zip_code": "75201",
        "rent_budget_min": 600,
        "rent_budget_max": 800,
        "sleep_schedule": "Early Bird",
        "cleanliness_level": "Very Clean",
        "noise_tolerance": "Quiet",
        "hobbies": "Reading, hiking, coding",
        "pet_preference": "Either",
        "smoking_preference": "No",
        "lifestyle_description": "I'm a software engineer who loves outdoor activities and quiet evenings with books."
    }

class TestUserProfile:
    """Test user profile creation and management"""
    
    def test_create_profile_success(self, client, sample_profile_data, setup_database):
        """Test successful profile creation"""
        response = client.post("/api/profiles", json=sample_profile_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["age"] == 25
        assert data["occupation"] == "Software Engineer"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_profile_validation_error(self, client, setup_database):
        """Test profile creation with validation errors"""
        invalid_data = {
            "name": "",  # Empty name should fail
            "age": 15,   # Under 18 should fail
            "gender": "Invalid"  # Invalid gender should fail
        }
        response = client.post("/api/profiles", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_all_profiles(self, client, sample_profile_data, setup_database):
        """Test retrieving all profiles"""
        # Create a profile first
        client.post("/api/profiles", json=sample_profile_data)
        
        # Get all profiles
        response = client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "John Doe"
    
    def test_get_profile_by_id(self, client, sample_profile_data, setup_database):
        """Test retrieving profile by ID"""
        # Create a profile
        create_response = client.post("/api/profiles", json=sample_profile_data)
        profile_id = create_response.json()["id"]
        
        # Get profile by ID
        response = client.get(f"/api/profiles/{profile_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile_id
        assert data["name"] == "John Doe"
    
    def test_get_nonexistent_profile(self, client, setup_database):
        """Test retrieving non-existent profile"""
        response = client.get("/api/profiles/99999")
        assert response.status_code == 404

class TestMatchingEngine:
    """Test the AI matching functionality"""
    
    def test_matching_engine_initialization(self):
        """Test matching engine can be initialized"""
        engine = MatchingEngine()
        assert engine.model is not None
    
    def test_create_profile_text(self):
        """Test profile text creation"""
        engine = MatchingEngine()
        profile = Mock()
        profile.occupation = "Engineer"
        profile.hobbies = "Coding, hiking"
        profile.lifestyle_description = "Love outdoor activities"
        
        text = engine.create_profile_text(profile)
        assert "Engineer" in text
        assert "Coding" in text
        assert "outdoor activities" in text
    
    def test_calculate_distance(self):
        """Test distance calculation"""
        engine = MatchingEngine()
        # Test distance between Dallas and Austin
        distance = engine.calculate_distance(32.7767, -96.7970, 30.2672, -97.7431)
        assert distance > 0
        assert distance < 300  # Should be less than 300 miles
    
    def test_check_budget_match(self):
        """Test budget compatibility"""
        engine = MatchingEngine()
        
        # Overlapping budgets should match
        assert engine.check_budget_match(600, 800, 700, 900) == True
        
        # Non-overlapping budgets should not match
        assert engine.check_budget_match(600, 700, 800, 900) == False
    
    def test_ai_similarity_calculation(self):
        """Test AI similarity calculation"""
        engine = MatchingEngine()
        
        text1 = "I love outdoor activities and quiet evenings"
        text2 = "I enjoy hiking and reading books"
        text3 = "I hate nature and prefer loud parties"
        
        similarity1 = engine.calculate_ai_similarity(text1, text2)
        similarity2 = engine.calculate_ai_similarity(text1, text3)
        
        assert similarity1 > similarity2  # Similar texts should have higher similarity
        assert 0 <= similarity1 <= 100
        assert 0 <= similarity2 <= 100

class TestMatchingAPI:
    """Test the matching API endpoints"""
    
    def test_find_matches_empty_database(self, client, sample_profile_data, setup_database):
        """Test matching with empty database"""
        response = client.post("/api/match", json={"user_profile": sample_profile_data})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # No matches in empty database
    
    def test_find_matches_with_existing_profiles(self, client, setup_database):
        """Test matching with existing profiles"""
        # Create first profile
        profile1 = {
            "name": "Alice",
            "age": 24,
            "gender": "Female",
            "occupation": "Designer",
            "city": "Dallas",
            "zip_code": "75201",
            "rent_budget_min": 600,
            "rent_budget_max": 800,
            "sleep_schedule": "Early Bird",
            "cleanliness_level": "Very Clean",
            "noise_tolerance": "Quiet",
            "hobbies": "Art, reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Creative person who loves nature and quiet spaces."
        }
        
        # Create second profile
        profile2 = {
            "name": "Bob",
            "age": 26,
            "gender": "Male",
            "occupation": "Engineer",
            "city": "Dallas",
            "zip_code": "75202",
            "rent_budget_min": 700,
            "rent_budget_max": 900,
            "sleep_schedule": "Flexible",
            "cleanliness_level": "Moderately Clean",
            "noise_tolerance": "Moderate",
            "hobbies": "Gaming, movies, cooking",
            "pet_preference": "Yes",
            "smoking_preference": "No",
            "lifestyle_description": "Tech enthusiast who enjoys entertainment and cooking."
        }
        
        # Create profiles
        client.post("/api/profiles", json=profile1)
        client.post("/api/profiles", json=profile2)
        
        # Test matching
        response = client.post("/api/match", json={"user_profile": profile1})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # Should find at least one match
        
        # Check match structure
        if len(data) > 0:
            match = data[0]
            assert "user" in match
            assert "compatibility_score" in match
            assert "location_match" in match
            assert "budget_match" in match
            assert 0 <= match["compatibility_score"] <= 100

class TestFrontend:
    """Test frontend endpoints"""
    
    def test_home_page(self, client):
        """Test home page loads"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "SmartRoommate+" in response.text
    
    def test_results_page(self, client):
        """Test results page loads"""
        response = client.get("/results")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Your Roommate Matches" in response.text

class TestDataValidation:
    """Test data validation and edge cases"""
    
    def test_age_validation(self, client, sample_profile_data, setup_database):
        """Test age validation"""
        # Test minimum age
        sample_profile_data["age"] = 17
        response = client.post("/api/profiles", json=sample_profile_data)
        assert response.status_code == 422
        
        # Test maximum age
        sample_profile_data["age"] = 101
        response = client.post("/api/profiles", json=sample_profile_data)
        assert response.status_code == 422
    
    def test_budget_validation(self, client, sample_profile_data, setup_database):
        """Test budget validation"""
        # Test negative budget
        sample_profile_data["rent_budget_min"] = -100
        response = client.post("/api/profiles", json=sample_profile_data)
        assert response.status_code == 422
        
        # Test min > max budget
        sample_profile_data["rent_budget_min"] = 1000
        sample_profile_data["rent_budget_max"] = 500
        response = client.post("/api/profiles", json=sample_profile_data)
        assert response.status_code == 422
    
    def test_required_fields(self, client, setup_database):
        """Test required field validation"""
        incomplete_data = {
            "name": "John",
            "age": 25
            # Missing required fields
        }
        response = client.post("/api/profiles", json=incomplete_data)
        assert response.status_code == 422

# Performance tests
class TestPerformance:
    """Test application performance"""
    
    def test_multiple_profile_creation(self, client, sample_profile_data, setup_database):
        """Test creating multiple profiles quickly"""
        profiles = []
        for i in range(10):
            profile = sample_profile_data.copy()
            profile["name"] = f"User {i}"
            profiles.append(profile)
        
        # Create all profiles
        for profile in profiles:
            response = client.post("/api/profiles", json=profile)
            assert response.status_code == 200
        
        # Verify all profiles were created
        response = client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 10

# Integration tests
class TestIntegration:
    """Test full application integration"""
    
    def test_complete_user_journey(self, client, setup_database):
        """Test complete user journey from profile creation to matching"""
        # Step 1: Create profile
        profile_data = {
            "name": "Test User",
            "age": 25,
            "gender": "Male",
            "occupation": "Developer",
            "city": "Dallas",
            "zip_code": "75201",
            "rent_budget_min": 600,
            "rent_budget_max": 800,
            "sleep_schedule": "Early Bird",
            "cleanliness_level": "Very Clean",
            "noise_tolerance": "Quiet",
            "hobbies": "Coding, reading",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Passionate developer who loves learning and quiet environments."
        }
        
        # Create profile
        create_response = client.post("/api/profiles", json=profile_data)
        assert create_response.status_code == 200
        
        # Step 2: Find matches
        match_response = client.post("/api/match", json={"user_profile": profile_data})
        assert match_response.status_code == 200
        
        # Step 3: Verify profile exists
        profile_id = create_response.json()["id"]
        get_response = client.get(f"/api/profiles/{profile_id}")
        assert get_response.status_code == 200
        
        # Step 4: Access frontend
        home_response = client.get("/")
        assert home_response.status_code == 200
        
        results_response = client.get("/results")
        assert results_response.status_code == 200

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])

