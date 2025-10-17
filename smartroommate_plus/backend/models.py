from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    occupation = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    zip_code = Column(String(10), nullable=False)
    rent_budget_min = Column(Integer, nullable=False)
    rent_budget_max = Column(Integer, nullable=False)
    sleep_schedule = Column(String(50), nullable=False)  # Early Bird, Night Owl, Flexible
    cleanliness_level = Column(String(50), nullable=False)  # Very Clean, Moderately Clean, Relaxed
    noise_tolerance = Column(String(50), nullable=False)  # Quiet, Moderate, Loud OK
    hobbies = Column(Text, nullable=False)
    pet_preference = Column(String(20), nullable=False)  # Yes, No, Either
    smoking_preference = Column(String(20), nullable=False)  # Yes, No, Either
    lifestyle_description = Column(Text, nullable=False)
    
    # Optional social media links
    instagram_link = Column(String(200), nullable=True)
    facebook_link = Column(String(200), nullable=True)
    linkedin_link = Column(String(200), nullable=True)
    twitter_link = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserProfile(name='{self.name}', city='{self.city}')>"
