"""
Authentication Service for SmartRoommate+
Handles user registration, login, and JWT token management
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import os
import sys

# Add shared modules to path
sys.path.append('../shared')
from models import UserAuth, UserLogin, UserRegister, Token, TokenData, APIResponse
from utils import (
    setup_logging, create_access_token, verify_token, hash_password, 
    verify_password, get_config, create_success_response, create_error_response,
    validate_email, sanitize_input
)

# Configuration
config = get_config()
config.update({
    "service_name": "auth-service",
    "service_port": 8001,
    "service_host": "0.0.0.0"
})

# Database setup
DATABASE_URL = config["database_url"]
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="SmartRoommate+ Authentication Service",
    description="Handles user authentication and authorization",
    version="1.0.0"
)

# Logging
logger = setup_logging(config["service_name"])

# Security
security = HTTPBearer()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication functions
def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                    db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    secret_key = config["jwt_secret_key"]
    
    try:
        payload = verify_token(token, secret_key)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# API Endpoints
@app.post("/register", response_model=APIResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Validate email format
        if not validate_email(user_data.email):
            return create_error_response("Invalid email format", status_code=400)
        
        # Check if passwords match
        if user_data.password != user_data.confirm_password:
            return create_error_response("Passwords do not match", status_code=400)
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                return create_error_response("Email already registered", status_code=400)
            else:
                return create_error_response("Username already taken", status_code=400)
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        db_user = User(
            email=sanitize_input(user_data.email),
            username=sanitize_input(user_data.username),
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"New user registered: {user_data.email}")
        
        return create_success_response(
            "User registered successfully",
            {
                "user_id": db_user.id,
                "email": db_user.email,
                "username": db_user.username
            }
        )
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return create_error_response("Registration failed", status_code=500)

@app.post("/login", response_model=APIResponse)
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    try:
        # Authenticate user
        user = authenticate_user(db, user_data.email, user_data.password)
        if not user:
            return create_error_response("Invalid email or password", status_code=401)
        
        if not user.is_active:
            return create_error_response("Account is deactivated", status_code=401)
        
        # Create access token
        access_token_expires = timedelta(minutes=config["jwt_expire_minutes"])
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email},
            secret_key=config["jwt_secret_key"],
            expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.email}")
        
        return create_success_response(
            "Login successful",
            {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": config["jwt_expire_minutes"] * 60,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return create_error_response("Login failed", status_code=500)

@app.get("/me", response_model=APIResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return create_success_response(
        "User information retrieved",
        {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat()
        }
    )

@app.post("/logout", response_model=APIResponse)
async def logout_user(current_user: User = Depends(get_current_user)):
    """Logout user (client-side token removal)"""
    logger.info(f"User logged out: {current_user.email}")
    return create_success_response("Logout successful")

@app.put("/deactivate", response_model=APIResponse)
async def deactivate_user(current_user: User = Depends(get_current_user), 
                         db: Session = Depends(get_db)):
    """Deactivate user account"""
    try:
        current_user.is_active = False
        current_user.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"User account deactivated: {current_user.email}")
        return create_success_response("Account deactivated successfully")
        
    except Exception as e:
        logger.error(f"Deactivation error: {str(e)}")
        return create_error_response("Deactivation failed", status_code=500)

@app.put("/change-password", response_model=APIResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(current_password, current_user.hashed_password):
            return create_error_response("Current password is incorrect", status_code=400)
        
        # Hash new password
        new_hashed_password = hash_password(new_password)
        current_user.hashed_password = new_hashed_password
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        return create_success_response("Password changed successfully")
        
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return create_error_response("Password change failed", status_code=500)

@app.get("/verify-token", response_model=APIResponse)
async def verify_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token validity"""
    try:
        token = credentials.credentials
        secret_key = config["jwt_secret_key"]
        
        payload = verify_token(token, secret_key)
        
        return create_success_response(
            "Token is valid",
            {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "expires_at": payload.get("exp")
            }
        )
        
    except HTTPException as e:
        return create_error_response(e.detail, status_code=e.status_code)
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return create_error_response("Token verification failed", status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "auth-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Service startup
@app.on_event("startup")
async def startup_event():
    """Service startup event"""
    logger.info(f"Authentication service starting on {config['service_host']}:{config['service_port']}")
    logger.info("Database connection established")

@app.on_event("shutdown")
async def shutdown_event():
    """Service shutdown event"""
    logger.info("Authentication service shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["service_host"],
        port=config["service_port"],
        log_level="info"
    )

