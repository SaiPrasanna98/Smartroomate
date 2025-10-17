import pytest
import os
import sys
sys.path.append('backend')

from database import get_db, create_tables, SessionLocal
from models import UserProfile, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestDatabase:
    """Test database operations and models"""
    
    @pytest.fixture
    def test_db():
        """Create test database"""
        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        return TestingSessionLocal, override_get_db
    
    def test_database_connection(self, test_db):
        """Test database connection"""
        session_factory, _ = test_db
        db = session_factory()
        assert db is not None
        db.close()
    
    def test_user_profile_model(self, test_db):
        """Test UserProfile model creation"""
        session_factory, _ = test_db
        db = session_factory()
        
        # Create a user profile
        profile = UserProfile(
            name="Test User",
            age=25,
            gender="Male",
            occupation="Developer",
            city="Dallas",
            zip_code="75201",
            rent_budget_min=600,
            rent_budget_max=800,
            sleep_schedule="Early Bird",
            cleanliness_level="Very Clean",
            noise_tolerance="Quiet",
            hobbies="Coding, reading",
            pet_preference="Either",
            smoking_preference="No",
            lifestyle_description="Passionate developer"
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        assert profile.id is not None
        assert profile.name == "Test User"
        assert profile.age == 25
        assert profile.created_at is not None
        
        db.close()
    
    def test_user_profile_validation(self, test_db):
        """Test UserProfile field validation"""
        session_factory, _ = test_db
        db = session_factory()
        
        # Test required fields
        profile = UserProfile(
            name="Test User",
            age=25,
            gender="Male",
            occupation="Developer",
            city="Dallas",
            zip_code="75201",
            rent_budget_min=600,
            rent_budget_max=800,
            sleep_schedule="Early Bird",
            cleanliness_level="Very Clean",
            noise_tolerance="Quiet",
            hobbies="Coding",
            pet_preference="Either",
            smoking_preference="No",
            lifestyle_description="Test description"
        )
        
        db.add(profile)
        db.commit()
        
        # Verify all fields are saved correctly
        saved_profile = db.query(UserProfile).filter(UserProfile.name == "Test User").first()
        assert saved_profile is not None
        assert saved_profile.name == "Test User"
        assert saved_profile.occupation == "Developer"
        assert saved_profile.city == "Dallas"
        
        db.close()
    
    def test_database_constraints(self, test_db):
        """Test database constraints and relationships"""
        session_factory, _ = test_db
        db = session_factory()
        
        # Test unique constraints (if any)
        profile1 = UserProfile(
            name="User 1",
            age=25,
            gender="Male",
            occupation="Developer",
            city="Dallas",
            zip_code="75201",
            rent_budget_min=600,
            rent_budget_max=800,
            sleep_schedule="Early Bird",
            cleanliness_level="Very Clean",
            noise_tolerance="Quiet",
            hobbies="Coding",
            pet_preference="Either",
            smoking_preference="No",
            lifestyle_description="Test description"
        )
        
        profile2 = UserProfile(
            name="User 2",
            age=26,
            gender="Female",
            occupation="Designer",
            city="Austin",
            zip_code="78701",
            rent_budget_min=700,
            rent_budget_max=900,
            sleep_schedule="Night Owl",
            cleanliness_level="Moderately Clean",
            noise_tolerance="Moderate",
            hobbies="Art",
            pet_preference="Yes",
            smoking_preference="No",
            lifestyle_description="Creative person"
        )
        
        db.add(profile1)
        db.add(profile2)
        db.commit()
        
        # Verify both profiles were created
        profiles = db.query(UserProfile).all()
        assert len(profiles) == 2
        assert profiles[0].name != profiles[1].name
        
        db.close()
    
    def test_database_queries(self, test_db):
        """Test various database queries"""
        session_factory, _ = test_db
        db = session_factory()
        
        # Create test data
        profiles_data = [
            {
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
                "hobbies": "Art, reading",
                "pet_preference": "Either",
                "smoking_preference": "No",
                "lifestyle_description": "Creative person"
            },
            {
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
                "hobbies": "Gaming, movies",
                "pet_preference": "Yes",
                "smoking_preference": "No",
                "lifestyle_description": "Tech enthusiast"
            },
            {
                "name": "Charlie",
                "age": 28,
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
                "lifestyle_description": "Educator who loves nature"
            }
        ]
        
        # Insert test data
        for data in profiles_data:
            profile = UserProfile(**data)
            db.add(profile)
        db.commit()
        
        # Test various queries
        # Query by city
        dallas_profiles = db.query(UserProfile).filter(UserProfile.city == "Dallas").all()
        assert len(dallas_profiles) == 2
        
        # Query by age range
        young_profiles = db.query(UserProfile).filter(UserProfile.age < 27).all()
        assert len(young_profiles) == 2
        
        # Query by occupation
        tech_profiles = db.query(UserProfile).filter(
            UserProfile.occupation.in_(["Engineer", "Designer"])
        ).all()
        assert len(tech_profiles) == 2
        
        # Query by budget range
        budget_profiles = db.query(UserProfile).filter(
            UserProfile.rent_budget_min <= 600,
            UserProfile.rent_budget_max >= 600
        ).all()
        assert len(budget_profiles) >= 1
        
        # Query by multiple criteria
        specific_profile = db.query(UserProfile).filter(
            UserProfile.name == "Alice",
            UserProfile.city == "Dallas",
            UserProfile.age == 24
        ).first()
        assert specific_profile is not None
        assert specific_profile.occupation == "Designer"
        
        db.close()
    
    def test_database_performance(self, test_db):
        """Test database performance with large datasets"""
        session_factory, _ = test_db
        db = session_factory()
        
        # Create many profiles
        profiles = []
        for i in range(100):
            profile = UserProfile(
                name=f"User {i}",
                age=20 + (i % 20),
                gender="Male" if i % 2 == 0 else "Female",
                occupation=f"Occupation {i % 10}",
                city=f"City {i % 5}",
                zip_code=f"7520{i % 10}",
                rent_budget_min=500 + (i * 10),
                rent_budget_max=800 + (i * 10),
                sleep_schedule=["Early Bird", "Night Owl", "Flexible"][i % 3],
                cleanliness_level=["Very Clean", "Moderately Clean", "Relaxed"][i % 3],
                noise_tolerance=["Quiet", "Moderate", "Loud OK"][i % 3],
                hobbies=f"Hobby {i}",
                pet_preference=["Yes", "No", "Either"][i % 3],
                smoking_preference=["Yes", "No", "Either"][i % 3],
                lifestyle_description=f"Description {i}"
            )
            profiles.append(profile)
        
        # Batch insert
        db.add_all(profiles)
        db.commit()
        
        # Test query performance
        import time
        start_time = time.time()
        
        # Complex query
        results = db.query(UserProfile).filter(
            UserProfile.age >= 25,
            UserProfile.age <= 30,
            UserProfile.city.like("City%")
        ).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete quickly (less than 1 second)
        assert query_time < 1.0
        assert len(results) > 0
        
        db.close()
    
    def test_database_transactions(self, test_db):
        """Test database transaction handling"""
        session_factory, _ = test_db
        db = session_factory()
        
        try:
            # Start transaction
            profile1 = UserProfile(
                name="Transaction Test 1",
                age=25,
                gender="Male",
                occupation="Developer",
                city="Dallas",
                zip_code="75201",
                rent_budget_min=600,
                rent_budget_max=800,
                sleep_schedule="Early Bird",
                cleanliness_level="Very Clean",
                noise_tolerance="Quiet",
                hobbies="Coding",
                pet_preference="Either",
                smoking_preference="No",
                lifestyle_description="Test transaction"
            )
            
            db.add(profile1)
            db.commit()
            
            # Verify profile was created
            saved_profile = db.query(UserProfile).filter(UserProfile.name == "Transaction Test 1").first()
            assert saved_profile is not None
            
            # Test rollback scenario
            profile2 = UserProfile(
                name="Transaction Test 2",
                age=26,
                gender="Female",
                occupation="Designer",
                city="Austin",
                zip_code="78701",
                rent_budget_min=700,
                rent_budget_max=900,
                sleep_schedule="Night Owl",
                cleanliness_level="Moderately Clean",
                noise_tolerance="Moderate",
                hobbies="Art",
                pet_preference="Yes",
                smoking_preference="No",
                lifestyle_description="Test rollback"
            )
            
            db.add(profile2)
            db.rollback()  # Rollback the transaction
            
            # Verify profile2 was not saved
            saved_profile2 = db.query(UserProfile).filter(UserProfile.name == "Transaction Test 2").first()
            assert saved_profile2 is None
            
            # Verify profile1 is still there
            saved_profile1 = db.query(UserProfile).filter(UserProfile.name == "Transaction Test 1").first()
            assert saved_profile1 is not None
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

if __name__ == "__main__":
    pytest.main(["-v", "--tb=short"])

