from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from dependencies import get_current_user
from database import users_collection, ledger_collection
import uuid
import time
from datetime import datetime

router = APIRouter(prefix="/api/blockchain", tags=["blockchain"])

class MintRequest(BaseModel):
    route: str
    amount: int
    co2Reduced: float
    fuelSaved: float

@router.post("/mint")
async def mint_credits(req: MintRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    
    # 1. Add transaction to ledger
    tx_hash = "0x" + str(uuid.uuid4()).replace("-", "")
    
    # Get block height
    block_number = await ledger_collection.count_documents({}) + 1
    
    entry = {
        "txHash": tx_hash,
        "blockNumber": block_number,
        "timestamp": datetime.utcnow().timestamp() * 1000,
        "userId": user_id,
        "userName": current_user["name"],
        "route": req.route,
        "amount": req.amount,
        "co2Reduced": req.co2Reduced,
        "fuelSaved": req.fuelSaved
    }
    
    await ledger_collection.insert_one(entry)
    
    # 2. Update user stats
    new_credits = current_user.get("carbonCredits", 0) + req.amount
    new_score = current_user.get("greenScore", 0) + int(req.amount / 5)
    new_routes = current_user.get("totalRoutes", 0) + 1
    new_fuel = current_user.get("totalFuelSaved", 0.0) + req.fuelSaved
    new_co2 = current_user.get("totalCO2Reduced", 0.0) + req.co2Reduced
    
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {
            "carbonCredits": new_credits,
            "greenScore": new_score,
            "totalRoutes": new_routes,
            "totalFuelSaved": new_fuel,
            "totalCO2Reduced": new_co2
        }}
    )
    
    del entry["_id"]
    
    return {
        "message": "Credits successfully minted to blockchain",
        "txHash": tx_hash,
        "transaction": entry,
        "newBalance": new_credits
    }

@router.get("/wallet")
async def get_wallet(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    tx_cursor = ledger_collection.find({"userId": user_id})
    user_txns = await tx_cursor.to_list(length=None)
    
    user_txns.sort(key=lambda x: x["timestamp"], reverse=True)
    clean_txns = [{k: v for k, v in t.items() if k != "_id"} for t in user_txns]
    
    return {
        "walletAddress": current_user["walletAddress"],
        "balance": current_user.get("carbonCredits", 0),
        "transactions": clean_txns
    }

@router.get("/leaderboard")
async def get_leaderboard():
    users_cursor = users_collection.find({"role": {"$ne": "admin"}})
    users = await users_cursor.to_list(length=None)
    
    users.sort(key=lambda x: x.get("carbonCredits", 0), reverse=True)
    
    leaderboard = []
    for i, u in enumerate(users):
        leaderboard.append({
            "rank": i + 1,
            "name": u["name"],
            "wallet": u["walletAddress"],
            "credits": u.get("carbonCredits", 0),
            "co2Saved": round(u.get("totalCO2Reduced", 0.0), 2)
        })
        
    return {"leaderboard": leaderboard}
