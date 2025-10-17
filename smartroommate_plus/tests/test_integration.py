import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.append('backend')

from main import app
from fastapi.testclient import TestClient
from database import get_db, create_tables, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestIntegration:
    """Integration tests for the complete application"""
    
    @pytest.fixture
    def test_client(self):
        """Create test client with test database"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create test database
        SQLALCHEMY_DATABASE_URL = f"sqlite:///{self.temp_db.name}"
        engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        yield client
        
        # Cleanup
        app.dependency_overrides.clear()
        os.unlink(self.temp_db.name)
    
    def test_complete_user_journey(self, test_client):
        """Test complete user journey from profile creation to matching"""
        # Step 1: Access home page
        response = test_client.get("/")
        assert response.status_code == 200
        assert "SmartRoommate+" in response.text
        
        # Step 2: Create a profile
        profile_data = {
            "name": "Alice Johnson",
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
        
        # Create profile
        create_response = test_client.post("/api/profiles", json=profile_data)
        assert create_response.status_code == 200
        created_profile = create_response.json()
        assert created_profile["name"] == "Alice Johnson"
        assert created_profile["id"] is not None
        
        # Step 3: Create another profile for matching
        profile2_data = {
            "name": "Bob Smith",
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
        
        create_response2 = test_client.post("/api/profiles", json=profile2_data)
        assert create_response2.status_code == 200
        
        # Step 4: Find matches
        match_response = test_client.post("/api/match", json={"user_profile": profile_data})
        assert match_response.status_code == 200
        matches = match_response.json()
        assert isinstance(matches, list)
        
        # Step 5: Verify profile exists in database
        get_response = test_client.get(f"/api/profiles/{created_profile['id']}")
        assert get_response.status_code == 200
        retrieved_profile = get_response.json()
        assert retrieved_profile["name"] == "Alice Johnson"
        
        # Step 6: Get all profiles
        all_profiles_response = test_client.get("/api/profiles")
        assert all_profiles_response.status_code == 200
        all_profiles = all_profiles_response.json()
        assert len(all_profiles) >= 2
        
        # Step 7: Access results page
        results_response = test_client.get("/results")
        assert results_response.status_code == 200
        assert "Your Roommate Matches" in results_response.text
    
    def test_error_handling_flow(self, test_client):
        """Test error handling throughout the application"""
        # Test invalid profile creation
        invalid_profile = {
            "name": "",  # Empty name
            "age": 15,   # Under 18
            "gender": "Invalid"  # Invalid gender
        }
        
        response = test_client.post("/api/profiles", json=invalid_profile)
        assert response.status_code == 422
        
        # Test non-existent profile retrieval
        response = test_client.get("/api/profiles/99999")
        assert response.status_code == 404
        
        # Test invalid matching request
        invalid_match_request = {
            "user_profile": {
                "name": "Test",
                "age": 15,  # Invalid age
                "gender": "Male",
                "occupation": "Test",
                "city": "Test",
                "zip_code": "123",  # Invalid ZIP
                "rent_budget_min": -100,  # Invalid budget
                "rent_budget_max": 500,
                "sleep_schedule": "Invalid",
                "cleanliness_level": "Invalid",
                "noise_tolerance": "Invalid",
                "hobbies": "",
                "pet_preference": "Invalid",
                "smoking_preference": "Invalid",
                "lifestyle_description": "Short"  # Too short
            }
        }
        
        response = test_client.post("/api/match", json=invalid_match_request)
        assert response.status_code == 422
    
    def test_api_endpoints_integration(self, test_client):
        """Test all API endpoints work together"""
        # Create multiple profiles
        profiles_data = [
            {
                "name": "User 1",
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
                "lifestyle_description": "Passionate developer who loves learning."
            },
            {
                "name": "User 2",
                "age": 27,
                "gender": "Female",
                "occupation": "Designer",
                "city": "Dallas",
                "zip_code": "75202",
                "rent_budget_min": 700,
                "rent_budget_max": 900,
                "sleep_schedule": "Flexible",
                "cleanliness_level": "Moderately Clean",
                "noise_tolerance": "Moderate",
                "hobbies": "Art, music",
                "pet_preference": "Yes",
                "smoking_preference": "No",
                "lifestyle_description": "Creative designer who loves art and music."
            },
            {
                "name": "User 3",
                "age": 23,
                "gender": "Male",
                "occupation": "Teacher",
                "city": "Austin",
                "zip_code": "78701",
                "rent_budget_min": 500,
                "rent_budget_max": 700,
                "sleep_schedule": "Early Bird",
                "cleanliness_level": "Very Clean",
                "noise_tolerance": "Quiet",
                "hobbies": "Reading, hiking",
                "pet_preference": "No",
                "smoking_preference": "No",
                "lifestyle_description": "Dedicated teacher who loves nature and education."
            }
        ]
        
        created_profiles = []
        
        # Create all profiles
        for profile_data in profiles_data:
            response = test_client.post("/api/profiles", json=profile_data)
            assert response.status_code == 200
            created_profiles.append(response.json())
        
        # Test getting all profiles
        response = test_client.get("/api/profiles")
        assert response.status_code == 200
        all_profiles = response.json()
        assert len(all_profiles) == 3
        
        # Test getting individual profiles
        for profile in created_profiles:
            response = test_client.get(f"/api/profiles/{profile['id']}")
            assert response.status_code == 200
            retrieved_profile = response.json()
            assert retrieved_profile["name"] == profile["name"]
        
        # Test matching for each profile
        for profile_data in profiles_data:
            response = test_client.post("/api/match", json={"user_profile": profile_data})
            assert response.status_code == 200
            matches = response.json()
            assert isinstance(matches, list)
            # Should find matches with other profiles
    
    def test_frontend_backend_integration(self, test_client):
        """Test frontend and backend integration"""
        # Test static file serving
        response = test_client.get("/static/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers.get("content-type", "")
        
        # Test JavaScript file serving
        response = test_client.get("/static/app.js")
        assert response.status_code == 200
        assert "application/javascript" in response.headers.get("content-type", "")
        
        # Test HTML pages
        response = test_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        
        response = test_client.get("/results")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_data_consistency(self, test_client):
        """Test data consistency across operations"""
        # Create a profile
        profile_data = {
            "name": "Consistency Test",
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
            "hobbies": "Coding",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test for data consistency."
        }
        
        # Create profile
        create_response = test_client.post("/api/profiles", json=profile_data)
        assert create_response.status_code == 200
        created_profile = create_response.json()
        
        # Verify data consistency
        assert created_profile["name"] == profile_data["name"]
        assert created_profile["age"] == profile_data["age"]
        assert created_profile["gender"] == profile_data["gender"]
        assert created_profile["occupation"] == profile_data["occupation"]
        assert created_profile["city"] == profile_data["city"]
        assert created_profile["zip_code"] == profile_data["zip_code"]
        assert created_profile["rent_budget_min"] == profile_data["rent_budget_min"]
        assert created_profile["rent_budget_max"] == profile_data["rent_budget_max"]
        assert created_profile["sleep_schedule"] == profile_data["sleep_schedule"]
        assert created_profile["cleanliness_level"] == profile_data["cleanliness_level"]
        assert created_profile["noise_tolerance"] == profile_data["noise_tolerance"]
        assert created_profile["hobbies"] == profile_data["hobbies"]
        assert created_profile["pet_preference"] == profile_data["pet_preference"]
        assert created_profile["smoking_preference"] == profile_data["smoking_preference"]
        assert created_profile["lifestyle_description"] == profile_data["lifestyle_description"]
        
        # Verify profile exists in all profiles list
        all_profiles_response = test_client.get("/api/profiles")
        assert all_profiles_response.status_code == 200
        all_profiles = all_profiles_response.json()
        
        found_profile = None
        for profile in all_profiles:
            if profile["id"] == created_profile["id"]:
                found_profile = profile
                break
        
        assert found_profile is not None
        assert found_profile["name"] == profile_data["name"]
    
    def test_performance_with_multiple_users(self, test_client):
        """Test performance with multiple users"""
        import time
        
        # Create multiple profiles
        profiles = []
        for i in range(20):
            profile_data = {
                "name": f"User {i}",
                "age": 20 + (i % 15),
                "gender": "Male" if i % 2 == 0 else "Female",
                "occupation": f"Occupation {i % 5}",
                "city": f"City {i % 3}",
                "zip_code": f"7520{i % 10}",
                "rent_budget_min": 500 + (i * 20),
                "rent_budget_max": 800 + (i * 20),
                "sleep_schedule": ["Early Bird", "Night Owl", "Flexible"][i % 3],
                "cleanliness_level": ["Very Clean", "Moderately Clean", "Relaxed"][i % 3],
                "noise_tolerance": ["Quiet", "Moderate", "Loud OK"][i % 3],
                "hobbies": f"Hobby {i}",
                "pet_preference": ["Yes", "No", "Either"][i % 3],
                "smoking_preference": ["Yes", "No", "Either"][i % 3],
                "lifestyle_description": f"Description for user {i} with more details about their lifestyle and preferences."
            }
            profiles.append(profile_data)
        
        # Measure creation time
        start_time = time.time()
        for profile_data in profiles:
            response = test_client.post("/api/profiles", json=profile_data)
            assert response.status_code == 200
        creation_time = time.time() - start_time
        
        # Should create 20 profiles quickly (less than 10 seconds)
        assert creation_time < 10.0
        
        # Test matching performance
        start_time = time.time()
        response = test_client.post("/api/match", json={"user_profile": profiles[0]})
        assert response.status_code == 200
        matching_time = time.time() - start_time
        
        # Should find matches quickly (less than 5 seconds)
        assert matching_time < 5.0
        
        # Test getting all profiles performance
        start_time = time.time()
        response = test_client.get("/api/profiles")
        assert response.status_code == 200
        retrieval_time = time.time() - start_time
        
        # Should retrieve all profiles quickly (less than 2 seconds)
        assert retrieval_time < 2.0

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])

