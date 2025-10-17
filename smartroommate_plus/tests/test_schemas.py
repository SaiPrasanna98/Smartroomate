import pytest
import os
import sys
sys.path.append('backend')

from schemas import UserProfileCreate, UserProfileResponse, MatchResult, MatchingRequest
from pydantic import ValidationError

class TestSchemas:
    """Test Pydantic schemas and validation"""
    
    def test_user_profile_create_valid(self):
        """Test valid UserProfileCreate"""
        valid_data = {
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
        
        profile = UserProfileCreate(**valid_data)
        assert profile.name == "John Doe"
        assert profile.age == 25
        assert profile.gender == "Male"
        assert profile.occupation == "Software Engineer"
    
    def test_user_profile_create_invalid_age(self):
        """Test invalid age validation"""
        invalid_data = {
            "name": "John Doe",
            "age": 15,  # Under 18
            "gender": "Male",
            "occupation": "Software Engineer",
            "city": "Dallas",
            "zip_code": "75201",
            "rent_budget_min": 600,
            "rent_budget_max": 800,
            "sleep_schedule": "Early Bird",
            "cleanliness_level": "Very Clean",
            "noise_tolerance": "Quiet",
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "age" in str(exc_info.value)
    
    def test_user_profile_create_invalid_gender(self):
        """Test invalid gender validation"""
        invalid_data = {
            "name": "John Doe",
            "age": 25,
            "gender": "Invalid",  # Invalid gender
            "occupation": "Software Engineer",
            "city": "Dallas",
            "zip_code": "75201",
            "rent_budget_min": 600,
            "rent_budget_max": 800,
            "sleep_schedule": "Early Bird",
            "cleanliness_level": "Very Clean",
            "noise_tolerance": "Quiet",
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "gender" in str(exc_info.value)
    
    def test_user_profile_create_invalid_sleep_schedule(self):
        """Test invalid sleep schedule validation"""
        invalid_data = {
            "name": "John Doe",
            "age": 25,
            "gender": "Male",
            "occupation": "Software Engineer",
            "city": "Dallas",
            "zip_code": "75201",
            "rent_budget_min": 600,
            "rent_budget_max": 800,
            "sleep_schedule": "Invalid",  # Invalid sleep schedule
            "cleanliness_level": "Very Clean",
            "noise_tolerance": "Quiet",
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "sleep_schedule" in str(exc_info.value)
    
    def test_user_profile_create_invalid_cleanliness_level(self):
        """Test invalid cleanliness level validation"""
        invalid_data = {
            "name": "John Doe",
            "age": 25,
            "gender": "Male",
            "occupation": "Software Engineer",
            "city": "Dallas",
            "zip_code": "75201",
            "rent_budget_min": 600,
            "rent_budget_max": 800,
            "sleep_schedule": "Early Bird",
            "cleanliness_level": "Invalid",  # Invalid cleanliness level
            "noise_tolerance": "Quiet",
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "cleanliness_level" in str(exc_info.value)
    
    def test_user_profile_create_invalid_noise_tolerance(self):
        """Test invalid noise tolerance validation"""
        invalid_data = {
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
            "noise_tolerance": "Invalid",  # Invalid noise tolerance
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "noise_tolerance" in str(exc_info.value)
    
    def test_user_profile_create_invalid_pet_preference(self):
        """Test invalid pet preference validation"""
        invalid_data = {
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
            "hobbies": "Reading, hiking",
            "pet_preference": "Invalid",  # Invalid pet preference
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "pet_preference" in str(exc_info.value)
    
    def test_user_profile_create_invalid_smoking_preference(self):
        """Test invalid smoking preference validation"""
        invalid_data = {
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
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "Invalid",  # Invalid smoking preference
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "smoking_preference" in str(exc_info.value)
    
    def test_user_profile_create_missing_required_fields(self):
        """Test missing required fields"""
        incomplete_data = {
            "name": "John Doe",
            "age": 25,
            # Missing required fields
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**incomplete_data)
        
        # Should have multiple validation errors
        assert len(exc_info.value.errors()) > 1
    
    def test_user_profile_create_empty_strings(self):
        """Test empty string validation"""
        invalid_data = {
            "name": "",  # Empty name
            "age": 25,
            "gender": "Male",
            "occupation": "",  # Empty occupation
            "city": "Dallas",
            "zip_code": "75201",
            "rent_budget_min": 600,
            "rent_budget_max": 800,
            "sleep_schedule": "Early Bird",
            "cleanliness_level": "Very Clean",
            "noise_tolerance": "Quiet",
            "hobbies": "",  # Empty hobbies
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        # Should have validation errors for empty strings
        assert any("name" in str(error) for error in exc_info.value.errors())
    
    def test_user_profile_create_short_lifestyle_description(self):
        """Test lifestyle description minimum length"""
        invalid_data = {
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
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Short"  # Too short
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "lifestyle_description" in str(exc_info.value)
    
    def test_user_profile_create_negative_budget(self):
        """Test negative budget validation"""
        invalid_data = {
            "name": "John Doe",
            "age": 25,
            "gender": "Male",
            "occupation": "Software Engineer",
            "city": "Dallas",
            "zip_code": "75201",
            "rent_budget_min": -100,  # Negative budget
            "rent_budget_max": 800,
            "sleep_schedule": "Early Bird",
            "cleanliness_level": "Very Clean",
            "noise_tolerance": "Quiet",
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "rent_budget_min" in str(exc_info.value)
    
    def test_user_profile_create_invalid_zip_code(self):
        """Test invalid ZIP code validation"""
        invalid_data = {
            "name": "John Doe",
            "age": 25,
            "gender": "Male",
            "occupation": "Software Engineer",
            "city": "Dallas",
            "zip_code": "123",  # Too short
            "rent_budget_min": 600,
            "rent_budget_max": 800,
            "sleep_schedule": "Early Bird",
            "cleanliness_level": "Very Clean",
            "noise_tolerance": "Quiet",
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserProfileCreate(**invalid_data)
        
        assert "zip_code" in str(exc_info.value)
    
    def test_user_profile_response(self):
        """Test UserProfileResponse schema"""
        from datetime import datetime
        
        response_data = {
            "id": 1,
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
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description",
            "created_at": datetime.now()
        }
        
        response = UserProfileResponse(**response_data)
        assert response.id == 1
        assert response.name == "John Doe"
        assert response.created_at is not None
    
    def test_match_result(self):
        """Test MatchResult schema"""
        from datetime import datetime
        
        user_data = {
            "id": 1,
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
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description",
            "created_at": datetime.now()
        }
        
        user_response = UserProfileResponse(**user_data)
        
        match_data = {
            "user": user_response,
            "compatibility_score": 85.5,
            "location_match": True,
            "budget_match": True,
            "distance_miles": 5.2
        }
        
        match_result = MatchResult(**match_data)
        assert match_result.compatibility_score == 85.5
        assert match_result.location_match == True
        assert match_result.budget_match == True
        assert match_result.distance_miles == 5.2
        assert match_result.user.name == "John Doe"
    
    def test_matching_request(self):
        """Test MatchingRequest schema"""
        profile_data = {
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
            "hobbies": "Reading, hiking",
            "pet_preference": "Either",
            "smoking_preference": "No",
            "lifestyle_description": "Test description"
        }
        
        user_profile = UserProfileCreate(**profile_data)
        
        request_data = {
            "user_profile": user_profile
        }
        
        matching_request = MatchingRequest(**request_data)
        assert matching_request.user_profile.name == "John Doe"
        assert matching_request.user_profile.age == 25

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])

