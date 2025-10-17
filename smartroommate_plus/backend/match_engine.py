from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from models import UserProfile
from schemas import UserProfileCreate, MatchResult, UserProfileResponse
import numpy as np
from typing import List, Tuple
import math

class MatchingEngine:
    def __init__(self):
        # Load the sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 3959  # Earth's radius in miles
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def get_coordinates(self, zip_code: str) -> Tuple[float, float]:
        """Mock function to get coordinates from ZIP code"""
        # In a real implementation, you'd use a geocoding service
        # For demo purposes, we'll use mock coordinates
        mock_coords = {
            "75201": (32.7767, -96.7970),  # Dallas
            "10001": (40.7505, -73.9934),  # New York
            "90210": (34.0901, -118.4065), # Beverly Hills
            "60601": (41.8781, -87.6298),  # Chicago
            "02101": (42.3601, -71.0589),  # Boston
        }
        return mock_coords.get(zip_code, (32.7767, -96.7970))  # Default to Dallas
    
    def create_profile_text(self, profile: UserProfile) -> str:
        """Create a text representation of the profile for AI matching"""
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
    
    def calculate_ai_similarity(self, profile1_text: str, profile2_text: str) -> float:
        """Calculate AI similarity between two profiles using embeddings"""
        embeddings = self.model.encode([profile1_text, profile2_text])
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        # Convert to percentage (0-100)
        return max(0, min(100, (similarity + 1) * 50))
    
    def check_location_match(self, zip1: str, zip2: str, max_distance: float = 50.0) -> Tuple[bool, float]:
        """Check if two locations are within acceptable distance"""
        try:
            lat1, lon1 = self.get_coordinates(zip1)
            lat2, lon2 = self.get_coordinates(zip2)
            distance = self.calculate_distance(lat1, lon1, lat2, lon2)
            return distance <= max_distance, distance
        except:
            return False, float('inf')
    
    def check_budget_match(self, budget_min1: int, budget_max1: int, 
                          budget_min2: int, budget_max2: int) -> bool:
        """Check if two budgets overlap"""
        return not (budget_max1 < budget_min2 or budget_max2 < budget_min1)
    
    def find_matches(self, new_profile: UserProfileCreate, db: Session, limit: int = 5) -> List[MatchResult]:
        """Find the best matches for a new profile"""
        # Get all existing profiles
        existing_profiles = db.query(UserProfile).all()
        
        if not existing_profiles:
            return []
        
        matches = []
        new_profile_text = self.create_profile_text_from_create(new_profile)
        
        for existing_profile in existing_profiles:
            # Calculate AI similarity
            existing_text = self.create_profile_text(existing_profile)
            ai_similarity = self.calculate_ai_similarity(new_profile_text, existing_text)
            
            # Check location match
            location_match, distance = self.check_location_match(
                new_profile.zip_code, existing_profile.zip_code
            )
            
            # Check budget match
            budget_match = self.check_budget_match(
                new_profile.rent_budget_min, new_profile.rent_budget_max,
                existing_profile.rent_budget_min, existing_profile.rent_budget_max
            )
            
            # Calculate final compatibility score
            location_score = 100 if location_match else 0
            budget_score = 100 if budget_match else 0
            
            final_score = (ai_similarity * 0.5) + (location_score * 0.3) + (budget_score * 0.2)
            
            # Only include matches with reasonable compatibility
            if final_score >= 30:  # Minimum threshold
                match_result = MatchResult(
                    user=UserProfileResponse.from_orm(existing_profile),
                    compatibility_score=round(final_score, 1),
                    location_match=location_match,
                    budget_match=budget_match,
                    distance_miles=round(distance, 1) if location_match else None
                )
                matches.append(match_result)
        
        # Sort by compatibility score and return top matches
        matches.sort(key=lambda x: x.compatibility_score, reverse=True)
        return matches[:limit]
    
    def create_profile_text_from_create(self, profile: UserProfileCreate) -> str:
        """Create text representation from UserProfileCreate"""
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
