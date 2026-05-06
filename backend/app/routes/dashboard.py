from fastapi import APIRouter, Depends
from ..dependencies import get_current_user, get_admin_user
from ..database.connection import users_collection, ledger_collection
from datetime import datetime

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    tx_cursor = await ledger_collection.find({"userId": user_id})
    user_txns = await tx_cursor.to_list(length=None)
    
    now = datetime.utcnow().timestamp() * 1000
    weekly_data = []
    
    for i in range(7):
        day_start = now - (6 - i) * 86400000
        day_end = day_start + 86400000
        day_txns = [t for t in user_txns if day_start <= t["timestamp"] < day_end]
        
        day_str = datetime.fromtimestamp(day_start/1000).strftime('%a')
        weekly_data.append({
            "day": day_str,
            "credits": sum(t.get("amount", 0) for t in day_txns),
            "co2": round(sum(t.get("co2Reduced", 0.0) for t in day_txns), 3),
            "routes": len(day_txns)
        })
        
    score = current_user.get("greenScore", 0)
    user_dict = {k: v for k, v in current_user.items() if k not in ["_id", "password"]}
    user_dict["tier"] = "Platinum" if score >= 500 else "Gold" if score >= 200 else "Silver" if score >= 100 else "Bronze"
    user_dict["tierColor"] = "#e5e4e2" if score >= 500 else "#ffd700" if score >= 200 else "#c0c0c0" if score >= 100 else "#cd7f32"
    
    user_txns.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_txns = [{k: v for k, v in t.items() if k != "_id"} for t in user_txns[:5]]
    
    return {"user": user_dict, "weeklyData": weekly_data, "recentTransactions": recent_txns}

@router.get("/admin")
async def get_admin_dashboard(admin_user: dict = Depends(get_admin_user)):
    users_cursor = await users_collection.find({})
    all_users = await users_cursor.to_list(length=None)
    
    tx_cursor = await ledger_collection.find({})
    all_txns = await tx_cursor.to_list(length=None)
    
    reg_users = [u for u in all_users if u.get("role") != "admin"]
    
    return {
        "overview": {
            "totalUsers": len(reg_users),
            "totalCreditsIssued": sum(t.get("amount", 0) for t in all_txns),
            "totalCO2Reduced": round(sum(t.get("co2Reduced", 0.0) for t in all_txns), 3),
            "totalFuelSaved": round(sum(t.get("fuelSaved", 0.0) for t in all_txns), 2),
            "totalRoutes": sum(u.get("totalRoutes", 0) for u in all_users),
            "blockHeight": len(all_txns)
        },
        "users": [{k: v for k, v in u.items() if k not in ["_id", "password"]} for u in all_users],
        "recentTransactions": [{k: v for k, v in t.items() if k != "_id"} for t in all_txns[:10]]
    }
