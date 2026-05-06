import asyncio
import uuid
import os

# ─── Mock Database Layer ──────────────────────────────────────────────────
# This mimics the Motor (MongoDB) and Redis interface using in-memory dicts
# so the application works even if MongoDB/Redis are not installed locally.

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = {} # id -> doc

    async def insert_one(self, doc):
        _id = str(uuid.uuid4())
        doc["_id"] = _id
        self.data[_id] = doc
        return type('obj', (object,), {'inserted_id': _id})

    async def find_one(self, filter_dict):
        for doc in self.data.values():
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc.copy()
        return None

    async def find(self, filter_dict):
        results = []
        for doc in self.data.values():
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(doc.copy())
        
        class Cursor:
            def __init__(self, data): self.data = data
            async def to_list(self, length=None): return self.data
        return Cursor(results)

    async def update_one(self, filter_dict, update_dict):
        doc = await self.find_one(filter_dict)
        if doc:
            _id = doc["_id"]
            if "$set" in update_dict:
                self.data[_id].update(update_dict["$set"])
            return True
        return False

    async def count_documents(self, filter_dict):
        count = 0
        for doc in self.data.values():
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match: count += 1
        return count

    async def create_index(self, key, unique=False):
        pass # Mock

class MockRedis:
    def __init__(self):
        self.data = {}
    async def get(self, key): return self.data.get(key)
    async def set(self, key, val, ex=None): self.data[key] = val
    async def delete(self, key): self.data.pop(key, None)
    @classmethod
    def from_url(cls, url, **kwargs): return cls()

# ─── Initialization ───────────────────────────────────────────────────────

# Set this to True to force mock even if MongoDB is running
USE_MOCK = True 

if USE_MOCK:
    print("WARNING: MongoDB/Redis not found. Using In-Memory Mock Database.")
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
            "joinedAt": 1772637382089
        })
