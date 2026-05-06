import os
from .mocks import MockCollection, MockRedis
from datetime import datetime

# ─── Initialization ───────────────────────────────────────────────────────

# Set this to True to force mock even if MongoDB is running
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

users_collection = None
ledger_collection = None
redis_client = None

if USE_MOCK:
    print("WARNING: Using In-Memory Mock Database.")
    users_collection = MockCollection("users")
    ledger_collection = MockCollection("ledger")
    redis_client = MockRedis()
else:
    # Real implementations (requires motor and redis-py)
    try:
        import motor.motor_asyncio
        import redis.asyncio as redis
        MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
        db = client.ecochain_ai
        users_collection = db.users
        ledger_collection = db.ledger
        REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception:
        print("ERROR: Failed to connect to MongoDB/Redis. Falling back to Mock.")
        users_collection = MockCollection("users")
        ledger_collection = MockCollection("ledger")
        redis_client = MockRedis()

async def init_db():
    await users_collection.create_index("email", unique=True)
    
    # Seed Admin if not exists
    admin = await users_collection.find_one({"email": "admin@ecochain.ai"})
    if not admin:
        from passlib.hash import bcrypt
        admin_id = "f76698b0-1af0-4983-af1f-d4d8397c6ec0"
        await users_collection.insert_one({
            "id": admin_id,
            "name": "EcoChain Admin",
            "email": "admin@ecochain.ai",
            "password": bcrypt.hash("Admin@123"),
            "role": "admin",
            "walletAddress": "0xADM1NF76698B01AF04983AF1FD4D8397C6EC0",
            "carbonCredits": 0,
            "greenScore": 100,
            "totalRoutes": 0,
            "totalFuelSaved": 0,
            "totalCO2Reduced": 0,
            "joinedAt": int(datetime.utcnow().timestamp() * 1000)
        })
