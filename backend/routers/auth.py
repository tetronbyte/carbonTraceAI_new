from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
import uuid
from database import users_collection, organizations_collection
from schemas import UserCreate, UserLogin, UserResponse, Token, OrganizationCreate, OrganizationResponse
from services.auth_service import (
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_user_by_email
)
from typing import List

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    existing = await get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "full_name": user_data.full_name,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await users_collection.insert_one(user)
    
    # Create default organization
    org_id = str(uuid.uuid4())
    org = {
        "id": org_id,
        "name": f"{user_data.full_name or user_data.email.split('@')[0]}'s Organization",
        "industry": None,
        "country": None,
        "owner_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await organizations_collection.insert_one(org)
    
    return {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "is_active": True,
        "created_at": user["created_at"]
    }

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login and get access token"""
    user = await authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "is_active": current_user.get("is_active", True),
        "created_at": current_user.get("created_at")
    }

@router.get("/organizations", response_model=List[OrganizationResponse])
async def get_organizations(current_user: dict = Depends(get_current_user)):
    """Get user's organizations"""
    orgs = await organizations_collection.find(
        {"owner_id": current_user["id"]}, 
        {"_id": 0}
    ).to_list(100)
    return orgs

@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new organization"""
    org_id = str(uuid.uuid4())
    org = {
        "id": org_id,
        "name": org_data.name,
        "industry": org_data.industry,
        "country": org_data.country,
        "owner_id": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await organizations_collection.insert_one(org)
    
    return {
        "id": org_id,
        "name": org_data.name,
        "industry": org_data.industry,
        "country": org_data.country,
        "created_at": org["created_at"]
    }
