from fastapi import APIRouter, Depends
import uuid
from datetime import datetime
from ..dependencies import get_current_user
from ..database.connection import users_collection, ledger_collection
from ..models.blockchain import MintRequest

router = APIRouter(prefix="/api/blockchain", tags=["blockchain"])

@router.post("/mint")
async def mint_credits(req: MintRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    tx_hash = "0x" + str(uuid.uuid4()).replace("-", "")
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
    
    new_credits = current_user.get("carbonCredits", 0) + req.creditsEarned
    new_score = current_user.get("greenScore", 0) + int(req.creditsEarned / 5)
    
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {
            "carbonCredits": new_credits,
            "greenScore": new_score,
            "totalRoutes": current_user.get("totalRoutes", 0) + 1,
            "totalFuelSaved": current_user.get("totalFuelSaved", 0.0) + req.fuelSaved,
            "totalCO2Reduced": current_user.get("totalCO2Reduced", 0.0) + req.co2Reduced
        }}
    )
    
    return {
        "message": "Credits successfully minted",
        "txHash": tx_hash,
        "transaction": {k:v for k,v in entry.items() if k != "_id"},
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
    tx_cursor = await ledger_collection.find({"userId": current_user["id"]})
    user_txns = await tx_cursor.to_list(length=None)
    user_txns.sort(key=lambda x: x["timestamp"], reverse=True)
    
    temp_balance = current_user.get("carbonCredits", 0)
    history = []
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
    
    return {"count": len(history), "transactions": history}

@router.get("/leaderboard")
async def get_leaderboard():
    users_cursor = await users_collection.find({"role": {"$ne": "admin"}})
    users = await users_cursor.to_list(length=None)
    users.sort(key=lambda x: x.get("carbonCredits", 0), reverse=True)
    
    leaderboard = []
    for i, u in enumerate(users):
        rank = i + 1
        addr = u.get("walletAddress", "0x...")
        leaderboard.append({
            "rank": rank,
            "badge": "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else str(rank),
            "name": u["name"],
            "walletAddress": addr[:8] + "..." + addr[-6:] if len(addr) > 14 else addr,
            "carbonCredits": u.get("carbonCredits", 0),
            "co2Reduced": round(u.get("totalCO2Reduced", 0.0), 2),
            "greenScore": u.get("greenScore", 0),
            "totalRoutes": u.get("totalRoutes", 0)
        })
    return {"leaderboard": leaderboard}
