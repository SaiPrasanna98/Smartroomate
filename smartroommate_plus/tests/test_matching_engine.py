import pytest
import os
import tempfile
from unittest.mock import Mock, patch
import sys
sys.path.append('backend')

from match_engine import MatchingEngine
from models import UserProfile
from schemas import UserProfileCreate

class TestMatchingEngineAdvanced:
    """Advanced tests for the matching engine"""
    
    @pytest.fixture
    def matching_engine(self):
        """Create matching engine instance"""
        return MatchingEngine()
    
    def test_model_loading(self, matching_engine):
        """Test that the AI model loads correctly"""
        assert matching_engine.model is not None
        assert hasattr(matching_engine.model, 'encode')
    
    def test_embedding_generation(self, matching_engine):
        """Test embedding generation"""
        text = "I love outdoor activities and quiet evenings"
        embeddings = matching_engine.model.encode([text])
        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0  # Should have vector dimensions
    
    def test_similarity_calculation_edge_cases(self, matching_engine):
        """Test similarity calculation with edge cases"""
        # Identical texts
        text1 = "I love coding"
        text2 = "I love coding"
        similarity = matching_engine.calculate_ai_similarity(text1, text2)
        assert similarity > 90  # Should be very similar
        
        # Completely different texts
        text3 = "I hate coding and prefer sleeping"
        similarity2 = matching_engine.calculate_ai_similarity(text1, text3)
        assert similarity2 < similarity  # Should be less similar
        
        # Empty texts
        similarity3 = matching_engine.calculate_ai_similarity("", "")
        assert 0 <= similarity3 <= 100
    
    def test_coordinate_mapping(self, matching_engine):
        """Test ZIP code to coordinate mapping"""
        # Test known ZIP codes
        coords = matching_engine.get_coordinates("75201")  # Dallas
        assert len(coords) == 2
        assert isinstance(coords[0], float)  # Latitude
        assert isinstance(coords[1], float)  # Longitude
        
        # Test unknown ZIP code (should return default)
        coords2 = matching_engine.get_coordinates("99999")
        assert len(coords2) == 2
    
    def test_distance_calculation_accuracy(self, matching_engine):
        """Test distance calculation accuracy"""
        # Dallas to Austin (approximately 195 miles)
        dallas_lat, dallas_lon = 32.7767, -96.7970
        austin_lat, austin_lon = 30.2672, -97.7431
        
        distance = matching_engine.calculate_distance(dallas_lat, dallas_lon, austin_lat, austin_lon)
        assert 190 <= distance <= 200  # Should be approximately 195 miles
        
        # Same location should be 0 distance
        distance2 = matching_engine.calculate_distance(dallas_lat, dallas_lon, dallas_lat, dallas_lon)
        assert distance2 == 0
    
    def test_location_match_logic(self, matching_engine):
        """Test location matching logic"""
        # Same ZIP code should match
        match, distance = matching_engine.check_location_match("75201", "75201")
        assert match == True
        assert distance == 0
        
        # Different ZIP codes
        match2, distance2 = matching_engine.check_location_match("75201", "75202")
        assert isinstance(match2, bool)
        assert distance2 >= 0
    
    def test_budget_match_scenarios(self, matching_engine):
        """Test various budget matching scenarios"""
        # Exact overlap
        assert matching_engine.check_budget_match(600, 800, 600, 800) == True
        
        # Partial overlap
        assert matching_engine.check_budget_match(600, 800, 700, 900) == True
        
        # No overlap
        assert matching_engine.check_budget_match(600, 700, 800, 900) == False
        
        # Edge case: touching ranges
        assert matching_engine.check_budget_match(600, 700, 700, 800) == True
    
    def test_profile_text_creation(self, matching_engine):
        """Test profile text creation from different sources"""
        # Test with UserProfile object
        profile = Mock()
        profile.occupation = "Software Engineer"
        profile.sleep_schedule = "Early Bird"
        profile.cleanliness_level = "Very Clean"
        profile.noise_tolerance = "Quiet"
        profile.hobbies = "Coding, hiking"
        profile.pet_preference = "Either"
        profile.smoking_preference = "No"
        profile.lifestyle_description = "Love outdoor activities"
        
        text = matching_engine.create_profile_text(profile)
        assert "Software Engineer" in text
        assert "Early Bird" in text
        assert "Very Clean" in text
        assert "Quiet" in text
        assert "Coding" in text
        assert "outdoor activities" in text
    
    def test_profile_text_from_create_schema(self, matching_engine):
        """Test profile text creation from UserProfileCreate"""
        profile_data = UserProfileCreate(
            name="Test User",
            age=25,
            gender="Male",
            occupation="Designer",
            city="Dallas",
            zip_code="75201",
            rent_budget_min=600,
            rent_budget_max=800,
            sleep_schedule="Flexible",
            cleanliness_level="Moderately Clean",
            noise_tolerance="Moderate",
            hobbies="Art, music",
            pet_preference="Yes",
            smoking_preference="No",
            lifestyle_description="Creative person who loves art and music"
        )
        
        text = matching_engine.create_profile_text_from_create(profile_data)
        assert "Designer" in text
        assert "Flexible" in text
        assert "Moderately Clean" in text
        assert "Art" in text
        assert "Creative person" in text
    
    def test_matching_algorithm_integration(self, matching_engine):
        """Test the complete matching algorithm"""
        # Create mock profiles
        profile1_text = "Software engineer who loves coding and quiet evenings"
        profile2_text = "Designer who enjoys art and creative activities"
        profile3_text = "Software developer who loves programming and outdoor activities"
        
        # Test similarity calculations
        sim1 = matching_engine.calculate_ai_similarity(profile1_text, profile2_text)
        sim2 = matching_engine.calculate_ai_similarity(profile1_text, profile3_text)
        
        # Profile 1 and 3 should be more similar (both software-related)
        assert sim2 > sim1
        
        # Test location and budget matching
        location_match, _ = matching_engine.check_location_match("75201", "75202")
        budget_match = matching_engine.check_budget_match(600, 800, 700, 900)
        
        # Calculate final score
        final_score = (sim2 * 0.5) + (100 if location_match else 0) * 0.3 + (100 if budget_match else 0) * 0.2
        assert 0 <= final_score <= 100
    
    def test_error_handling(self, matching_engine):
        """Test error handling in matching engine"""
        # Test with invalid coordinates
        try:
            distance = matching_engine.calculate_distance("invalid", "invalid", 0, 0)
            # Should handle gracefully
        except (ValueError, TypeError):
            pass  # Expected behavior
        
        # Test with None values
        try:
            similarity = matching_engine.calculate_ai_similarity(None, None)
            # Should handle gracefully
        except (AttributeError, TypeError):
            pass  # Expected behavior

class TestPerformanceAndScalability:
    """Test performance and scalability aspects"""
    
    def test_batch_processing(self):
        """Test processing multiple profiles efficiently"""
        engine = MatchingEngine()
        
        # Create multiple profile texts
        profiles = [
            "Software engineer who loves coding",
            "Designer who enjoys art",
            "Teacher who loves education",
            "Doctor who cares about health",
            "Artist who creates beautiful things"
        ]
        
        # Test batch processing
        embeddings = engine.model.encode(profiles)
        assert len(embeddings) == 5
        assert all(len(emb) > 0 for emb in embeddings)
    
    def test_memory_usage(self):
        """Test memory usage with large datasets"""
        engine = MatchingEngine()
        
        # Create large text dataset
        large_texts = [f"Profile {i} with unique characteristics" for i in range(100)]
        
        # Process large dataset
        embeddings = engine.model.encode(large_texts)
        assert len(embeddings) == 100
        
        # Verify all embeddings are valid
        assert all(len(emb) > 0 for emb in embeddings)
    
    def test_concurrent_processing(self):
        """Test concurrent processing capabilities"""
        import threading
        import time
        
        engine = MatchingEngine()
        results = []
        
        def process_text(text):
            similarity = engine.calculate_ai_similarity(text, "Software engineer")
            results.append(similarity)
        
        # Create multiple threads
        threads = []
        texts = [f"Text {i}" for i in range(10)]
        
        for text in texts:
            thread = threading.Thread(target=process_text, args=(text,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(results) == 10
        assert all(0 <= score <= 100 for score in results)

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])

