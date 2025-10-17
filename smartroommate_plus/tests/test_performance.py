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

class TestPerformance:
    """Performance tests for the application"""
    
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
    
    def test_profile_creation_performance(self, test_client):
        """Test profile creation performance"""
        import time
        
        profile_data = {
            "name": "Performance Test User",
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
            "lifestyle_description": "Performance test user with detailed lifestyle description."
        }
        
        # Test single profile creation time
        start_time = time.time()
        response = test_client.post("/api/profiles", json=profile_data)
        creation_time = time.time() - start_time
        
        assert response.status_code == 200
        assert creation_time < 1.0  # Should create profile in less than 1 second
    
    def test_batch_profile_creation_performance(self, test_client):
        """Test batch profile creation performance"""
        import time
        
        # Create multiple profiles
        profiles = []
        for i in range(50):
            profile_data = {
                "name": f"Batch User {i}",
                "age": 20 + (i % 20),
                "gender": "Male" if i % 2 == 0 else "Female",
                "occupation": f"Occupation {i % 10}",
                "city": f"City {i % 5}",
                "zip_code": f"7520{i % 10}",
                "rent_budget_min": 500 + (i * 10),
                "rent_budget_max": 800 + (i * 10),
                "sleep_schedule": ["Early Bird", "Night Owl", "Flexible"][i % 3],
                "cleanliness_level": ["Very Clean", "Moderately Clean", "Relaxed"][i % 3],
                "noise_tolerance": ["Quiet", "Moderate", "Loud OK"][i % 3],
                "hobbies": f"Hobby {i}",
                "pet_preference": ["Yes", "No", "Either"][i % 3],
                "smoking_preference": ["Yes", "No", "Either"][i % 3],
                "lifestyle_description": f"Detailed lifestyle description for batch user {i} with comprehensive information about their preferences and habits."
            }
            profiles.append(profile_data)
        
        # Measure batch creation time
        start_time = time.time()
        for profile_data in profiles:
            response = test_client.post("/api/profiles", json=profile_data)
            assert response.status_code == 200
        batch_creation_time = time.time() - start_time
        
        # Should create 50 profiles in reasonable time (less than 30 seconds)
        assert batch_creation_time < 30.0
        
        # Calculate average creation time per profile
        avg_creation_time = batch_creation_time / 50
        assert avg_creation_time < 0.6  # Less than 600ms per profile
    
    def test_matching_performance(self, test_client):
        """Test matching performance with large dataset"""
        import time
        
        # Create a large dataset of profiles
        profiles = []
        for i in range(100):
            profile_data = {
                "name": f"Match Test User {i}",
                "age": 20 + (i % 20),
                "gender": "Male" if i % 2 == 0 else "Female",
                "occupation": f"Occupation {i % 10}",
                "city": f"City {i % 5}",
                "zip_code": f"7520{i % 10}",
                "rent_budget_min": 500 + (i * 10),
                "rent_budget_max": 800 + (i * 10),
                "sleep_schedule": ["Early Bird", "Night Owl", "Flexible"][i % 3],
                "cleanliness_level": ["Very Clean", "Moderately Clean", "Relaxed"][i % 3],
                "noise_tolerance": ["Quiet", "Moderate", "Loud OK"][i % 3],
                "hobbies": f"Hobby {i}",
                "pet_preference": ["Yes", "No", "Either"][i % 3],
                "smoking_preference": ["Yes", "No", "Either"][i % 3],
                "lifestyle_description": f"Comprehensive lifestyle description for match test user {i} with detailed information about their daily routines, preferences, and living habits."
            }
            profiles.append(profile_data)
        
        # Create all profiles
        for profile_data in profiles:
            response = test_client.post("/api/profiles", json=profile_data)
            assert response.status_code == 200
        
        # Test matching performance
        test_profile = {
            "name": "Performance Test User",
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
            "lifestyle_description": "Performance test user with detailed lifestyle description for matching analysis."
        }
        
        # Measure matching time
        start_time = time.time()
        response = test_client.post("/api/match", json={"user_profile": test_profile})
        matching_time = time.time() - start_time
        
        assert response.status_code == 200
        matches = response.json()
        assert isinstance(matches, list)
        
        # Should find matches quickly even with large dataset (less than 10 seconds)
        assert matching_time < 10.0
    
    def test_database_query_performance(self, test_client):
        """Test database query performance"""
        import time
        
        # Create test data
        profiles = []
        for i in range(200):
            profile_data = {
                "name": f"Query Test User {i}",
                "age": 20 + (i % 20),
                "gender": "Male" if i % 2 == 0 else "Female",
                "occupation": f"Occupation {i % 10}",
                "city": f"City {i % 5}",
                "zip_code": f"7520{i % 10}",
                "rent_budget_min": 500 + (i * 10),
                "rent_budget_max": 800 + (i * 10),
                "sleep_schedule": ["Early Bird", "Night Owl", "Flexible"][i % 3],
                "cleanliness_level": ["Very Clean", "Moderately Clean", "Relaxed"][i % 3],
                "noise_tolerance": ["Quiet", "Moderate", "Loud OK"][i % 3],
                "hobbies": f"Hobby {i}",
                "pet_preference": ["Yes", "No", "Either"][i % 3],
                "smoking_preference": ["Yes", "No", "Either"][i % 3],
                "lifestyle_description": f"Query test user {i} with detailed lifestyle description."
            }
            profiles.append(profile_data)
        
        # Create all profiles
        for profile_data in profiles:
            response = test_client.post("/api/profiles", json=profile_data)
            assert response.status_code == 200
        
        # Test various query performance
        queries = [
            ("Get all profiles", lambda: test_client.get("/api/profiles")),
            ("Get profile by ID", lambda: test_client.get("/api/profiles/1")),
            ("Get profile by ID", lambda: test_client.get("/api/profiles/50")),
            ("Get profile by ID", lambda: test_client.get("/api/profiles/100")),
        ]
        
        for query_name, query_func in queries:
            start_time = time.time()
            response = query_func()
            query_time = time.time() - start_time
            
            assert response.status_code == 200
            assert query_time < 2.0  # All queries should complete in less than 2 seconds
    
    def test_concurrent_requests_performance(self, test_client):
        """Test performance under concurrent requests"""
        import time
        import threading
        import queue
        
        # Create test data
        profiles = []
        for i in range(50):
            profile_data = {
                "name": f"Concurrent Test User {i}",
                "age": 20 + (i % 20),
                "gender": "Male" if i % 2 == 0 else "Female",
                "occupation": f"Occupation {i % 10}",
                "city": f"City {i % 5}",
                "zip_code": f"7520{i % 10}",
                "rent_budget_min": 500 + (i * 10),
                "rent_budget_max": 800 + (i * 10),
                "sleep_schedule": ["Early Bird", "Night Owl", "Flexible"][i % 3],
                "cleanliness_level": ["Very Clean", "Moderately Clean", "Relaxed"][i % 3],
                "noise_tolerance": ["Quiet", "Moderate", "Loud OK"][i % 3],
                "hobbies": f"Hobby {i}",
                "pet_preference": ["Yes", "No", "Either"][i % 3],
                "smoking_preference": ["Yes", "No", "Either"][i % 3],
                "lifestyle_description": f"Concurrent test user {i} with detailed lifestyle description."
            }
            profiles.append(profile_data)
        
        # Create all profiles
        for profile_data in profiles:
            response = test_client.post("/api/profiles", json=profile_data)
            assert response.status_code == 200
        
        # Test concurrent requests
        results = queue.Queue()
        
        def make_request():
            start_time = time.time()
            response = test_client.get("/api/profiles")
            end_time = time.time()
            results.put((response.status_code, end_time - start_time))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        total_time = time.time() - start_time
        
        # Collect results
        response_times = []
        while not results.empty():
            status_code, response_time = results.get()
            assert status_code == 200
            response_times.append(response_time)
        
        # Verify all requests completed successfully
        assert len(response_times) == 10
        assert all(time < 5.0 for time in response_times)  # All requests under 5 seconds
        assert total_time < 10.0  # Total time under 10 seconds
    
    def test_memory_usage(self, test_client):
        """Test memory usage with large datasets"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        profiles = []
        for i in range(100):
            profile_data = {
                "name": f"Memory Test User {i}",
                "age": 20 + (i % 20),
                "gender": "Male" if i % 2 == 0 else "Female",
                "occupation": f"Occupation {i % 10}",
                "city": f"City {i % 5}",
                "zip_code": f"7520{i % 10}",
                "rent_budget_min": 500 + (i * 10),
                "rent_budget_max": 800 + (i * 10),
                "sleep_schedule": ["Early Bird", "Night Owl", "Flexible"][i % 3],
                "cleanliness_level": ["Very Clean", "Moderately Clean", "Relaxed"][i % 3],
                "noise_tolerance": ["Quiet", "Moderate", "Loud OK"][i % 3],
                "hobbies": f"Hobby {i}",
                "pet_preference": ["Yes", "No", "Either"][i % 3],
                "smoking_preference": ["Yes", "No", "Either"][i % 3],
                "lifestyle_description": f"Memory test user {i} with detailed lifestyle description for memory usage analysis."
            }
            profiles.append(profile_data)
        
        # Create all profiles
        for profile_data in profiles:
            response = test_client.post("/api/profiles", json=profile_data)
            assert response.status_code == 200
        
        # Get memory usage after creating profiles
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 100 profiles)
        assert memory_increase < 100.0
        
        # Test matching with large dataset
        test_profile = {
            "name": "Memory Test User",
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
            "lifestyle_description": "Memory test user with detailed lifestyle description."
        }
        
        response = test_client.post("/api/match", json={"user_profile": test_profile})
        assert response.status_code == 200
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        # Total memory increase should still be reasonable
        assert total_memory_increase < 150.0

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])

