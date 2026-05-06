from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_current_user, get_admin_user
from database import users_collection, ledger_collection
from datetime import datetime
import time

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    
    # Get user transactions
    tx_cursor = ledger_collection.find({"userId": user_id})
    user_txns = await tx_cursor.to_list(length=None)
    
    now = datetime.utcnow().timestamp() * 1000
    weekly_data = []
    
    for i in range(7):
        day_start = now - (6 - i) * 86400000
        day_end = day_start + 86400000
        day_txns = [t for t in user_txns if day_start <= t["timestamp"] < day_end]
        
        day_str = datetime.fromtimestamp(day_start/1000).strftime('%a')
        credits_sum = sum(t.get("amount", 0) for t in day_txns)
        co2_sum = sum(t.get("co2Reduced", 0.0) for t in day_txns)
        
        weekly_data.append({
            "day": day_str,
            "credits": credits_sum,
            "co2": round(co2_sum, 3),
            "routes": len(day_txns)
        })
        
    score = current_user.get("greenScore", 0)
    tier = "Platinum" if score >= 500 else "Gold" if score >= 200 else "Silver" if score >= 100 else "Bronze"
    tier_color = "#e5e4e2" if score >= 500 else "#ffd700" if score >= 200 else "#c0c0c0" if score >= 100 else "#cd7f32"
    
    # Exclude _id
    user_dict = {k: v for k, v in current_user.items() if k != "_id" and k != "password"}
    user_dict["tier"] = tier
    user_dict["tierColor"] = tier_color
    
    # Sort txns descending
    user_txns.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_txns = [{k: v for k, v in t.items() if k != "_id"} for t in user_txns[:5]]
    
    return {
        "user": user_dict,
        "weeklyData": weekly_data,
        "recentTransactions": recent_txns
    }

@router.get("/admin")
async def get_admin_dashboard(admin_user: dict = Depends(get_admin_user)):
    users_cursor = users_collection.find({})
    all_users = await users_cursor.to_list(length=None)
    
    tx_cursor = ledger_collection.find({})
    all_txns = await tx_cursor.to_list(length=None)
    
    total_credits = sum(t.get("amount", 0) for t in all_txns)
    total_co2 = round(sum(t.get("co2Reduced", 0.0) for t in all_txns), 3)
    total_fuel = round(sum(t.get("fuelSaved", 0.0) for t in all_txns), 2)
    total_routes = sum(u.get("totalRoutes", 0) for u in all_users)
    
    reg_users = [u for u in all_users if u.get("role") != "admin"]
    avg_score = round(sum(u.get("greenScore", 0) for u in all_users) / max(1, len(all_users)))
    
    top_users = sorted(reg_users, key=lambda x: x.get("carbonCredits", 0), reverse=True)[:5]
    
    now = datetime.utcnow().timestamp() * 1000
    daily_stats = []
    
    for i in range(7):
        day_start = now - (6 - i) * 86400000
        day_end = day_start + 86400000
        day_txns = [t for t in all_txns if day_start <= t["timestamp"] < day_end]
        
        day_str = datetime.fromtimestamp(day_start/1000).strftime('%a')
        
        daily_stats.append({
            "day": day_str,
            "credits": sum(t.get("amount", 0) for t in day_txns),
            "routes": len(day_txns),
            "co2": round(sum(t.get("co2Reduced", 0.0) for t in day_txns), 3)
        })
        
    all_txns.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_txns = [{k: v for k, v in t.items() if k != "_id"} for t in all_txns[:10]]
    
    clean_users = [{k: v for k, v in u.items() if k != "_id" and k != "password"} for u in all_users]
    clean_top_users = [{k: v for k, v in u.items() if k != "_id" and k != "password"} for u in top_users]
    
    return {
        "overview": {
            "totalUsers": len(reg_users),
            "totalCreditsIssued": total_credits,
            "totalCO2Reduced": total_co2,
            "totalFuelSaved": total_fuel,
            "totalRoutes": total_routes,
            "avgGreenScore": avg_score,
            "blockHeight": len(all_txns)
        },
        "users": clean_users,
        "topUsers": clean_top_users,
        "dailyStats": daily_stats,
        "recentTransactions": recent_txns
    }
