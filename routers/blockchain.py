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
    creditsEarned: int
    co2Reduced: float
    fuelSaved: float
    greenBoost: float = 0.0

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
        "amount": req.creditsEarned,
        "co2Reduced": req.co2Reduced,
        "fuelSaved": req.fuelSaved
    }
    
    await ledger_collection.insert_one(entry)
    
    # 2. Update user stats
    new_credits = current_user.get("carbonCredits", 0) + req.creditsEarned
    new_score = current_user.get("greenScore", 0) + int(req.creditsEarned / 5)
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
        "newBalance": new_credits,
        "newGreenScore": new_score
    }

@router.get("/wallet")
async def get_wallet(current_user: dict = Depends(get_current_user)):
    return {
        "walletAddress": current_user["walletAddress"],
        "carbonCredits": current_user.get("carbonCredits", 0),
        "greenScore": current_user.get("greenScore", 0),
        "contractAddress": "0xECOChainContractMainnetV1_7f4d3c2e1a",
    }

@router.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    tx_cursor = ledger_collection.find({"userId": user_id})
    user_txns = await tx_cursor.to_list(length=None)
    
    user_txns.sort(key=lambda x: x["timestamp"], reverse=True)
    
    running_balance = current_user.get("carbonCredits", 0)
    history = []
    
    # We simulate the running balance by subtracting amounts backwards
    temp_balance = running_balance
    for tx in user_txns:
        history.append({
            "blockNumber": tx.get("blockNumber", 0),
            "txHash": tx["txHash"],
            "route": tx["route"],
            "co2Reduced": tx.get("co2Reduced", 0.0),
            "amount": tx["amount"],
            "balance": temp_balance,
            "timestamp": tx["timestamp"],
            "status": "CONFIRMED",
            "fuelSaved": tx.get("fuelSaved", 0.0)
        })
        temp_balance -= tx["amount"]
    
    return {
        "count": len(history),
        "transactions": history
    }

@router.get("/leaderboard")
async def get_leaderboard():
    users_cursor = users_collection.find({"role": {"$ne": "admin"}})
    users = await users_cursor.to_list(length=None)
    
    users.sort(key=lambda x: x.get("carbonCredits", 0), reverse=True)
    
    leaderboard = []
    for i, u in enumerate(users):
        rank = i + 1
        badge = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else str(rank)
        
        # Address shortening for privacy
        addr = u.get("walletAddress", "0x...")
        short_addr = addr[:8] + "..." + addr[-6:] if len(addr) > 14 else addr
        
        leaderboard.append({
            "rank": rank,
            "badge": badge,
            "name": u["name"],
            "walletAddress": short_addr,
            "carbonCredits": u.get("carbonCredits", 0),
            "co2Reduced": round(u.get("totalCO2Reduced", 0.0), 2),
            "greenScore": u.get("greenScore", 0),
            "totalRoutes": u.get("totalRoutes", 0)
        })
        
    return {"leaderboard": leaderboard}
