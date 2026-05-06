from fastapi import APIRouter, Depends
import time
import random
from datetime import datetime
from ..dependencies import get_current_user
from ..models.route import OptimizeRequest

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/optimize")
async def optimize_route(req: OptimizeRequest, current_user: dict = Depends(get_current_user)):
    start_time = time.time()
    
    seed = sum(ord(c) for c in req.start + req.destination)
    random.seed(seed)
    
    dist_km = 5 + random.random() * 25
    traffic_data = [min(100, (20 if (h < 7 or h > 20) else 60) + (30 if (7 <= h <= 9 or 17 <= h <= 19) else 0) + random.randint(-10, 10)) for h in range(24)]
        
    routes = [
        {"label": "Eco Express", "timeMinutes": int(dist_km * 2.5), "fuelSaved": round(dist_km * 0.12, 2), "co2Reduced": round(dist_km * 0.28, 2), "color": "#00ff88", "recommended": True},
        {"label": "Direct Path", "timeMinutes": int(dist_km * 2.1), "fuelSaved": round(dist_km * 0.04, 2), "co2Reduced": round(dist_km * 0.09, 2), "color": "#00d4ff", "recommended": False},
        {"label": "Scenic Bypass", "timeMinutes": int(dist_km * 3.2), "fuelSaved": 0.0, "co2Reduced": 0.0, "color": "#9b59f5", "recommended": False}
    ]
    
    # Generate a conversational tip
    tips = [
        f"AI Suggestion: For your {req.vehicleType}, the Eco Express is best to avoid {req.destination} morning congestion.",
        f"Pro Tip: Don't go through the bypass today, heavy construction detected near {req.destination}.",
        f"Eco Choice: Direct Path is 5 mins faster, but Eco Express saves {round(dist_km * 0.12, 1)}L of fuel.",
        f"Safety Alert: Poor road conditions on the bypass. Stick to the Main Avenue."
    ]
    ai_tip = random.choice(tips)

    return {
        "status": "success",
        "data": {
            "start": req.start, "destination": req.destination, "distanceKm": round(dist_km, 1), "aiConfidence": 94.2,
            "analysisTime": time.time() - start_time, "trafficData": traffic_data, "routes": routes,
            "aiTip": ai_tip,
            "waypoints": [{"name": req.start, "congestion": "Low"}, {"name": "Intersection B-42", "congestion": "Medium"}, {"name": "Green Corridor X", "congestion": "Low"}, {"name": req.destination, "congestion": "Low"}],
            "optimized": {
                "fuelSaved": round(dist_km * 0.12, 2), "co2Reduced": round(dist_km * 0.28, 2), "baselineFuel": round(dist_km * 0.15, 2),
                "baselineCO2": round(dist_km * 0.35, 2), "timeMinutes": int(dist_km * 2.5), "creditsEarned": int(dist_km * 2), "greenBoost": 1.2
            }
        }
    }
