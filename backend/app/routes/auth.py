from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
import uuid
from ..database.connection import users_collection
from ..models.auth import UserCreate, UserLogin

router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET", "ecochain-ai-secret-2024-hackathon")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/signup")
async def signup(user: UserCreate):
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")
    
    user_id = str(uuid.uuid4())
    wallet_address = "0x" + user_id.replace("-", "")[:40].upper()
    
    new_user = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "password": get_password_hash(user.password),
        "role": "user",
        "walletAddress": wallet_address,
        "carbonCredits": 0,
        "greenScore": 50,
        "totalRoutes": 0,
        "totalFuelSaved": 0.0,
        "totalCO2Reduced": 0.0,
        "joinedAt": datetime.utcnow().timestamp() * 1000
    }
    
    await users_collection.insert_one(new_user)
    
    token = create_access_token({"id": user_id, "email": user.email, "role": "user"})
    
    # Return without password
    del new_user["password"]
    del new_user["_id"]
    
    return {"message": "Account created successfully!", "token": token, "user": new_user}

@router.post("/login")
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    token = create_access_token({"id": db_user["id"], "email": db_user["email"], "role": db_user["role"]})
    
    del db_user["password"]
    del db_user["_id"]
    
    return {"message": "Login successful!", "token": token, "user": db_user}
