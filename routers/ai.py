from fastapi import APIRouter, Depends
from pydantic import BaseModel
import random
import time
from datetime import datetime
from dependencies import get_current_user
from ai_engine import predict_route_metrics

router = APIRouter(prefix="/api/ai", tags=["ai"])

class OptimizeRequest(BaseModel):
    start: str
    destination: str
    vehicleType: str

@router.post("/optimize")
async def optimize_route(req: OptimizeRequest, current_user: dict = Depends(get_current_user)):
    start_time = time.time()
    
    # Simulate ML analysis complexity
    seed = sum(ord(c) for c in req.start + req.destination)
    random.seed(seed)
    
    dist_km = 5 + random.random() * 25
    is_night = datetime.now().hour < 6 or datetime.now().hour > 20
    
    # Build traffic prediction data (24h)
    traffic_data = []
    for h in range(24):
        base = 20 if (h < 7 or h > 20) else 60
        peak = 30 if (7 <= h <= 9 or 17 <= h <= 19) else 0
        traffic_data.append(min(100, base + peak + random.randint(-10, 10)))
        
    # Build route variants
    routes = [
        {
            "label": "Eco Express",
            "timeMinutes": int(dist_km * 2.5),
            "fuelSaved": round(dist_km * 0.12, 2),
            "co2Reduced": round(dist_km * 0.28, 2),
            "color": "#00ff88",
            "recommended": True
        },
        {
            "label": "Direct Path",
            "timeMinutes": int(dist_km * 2.1),
            "fuelSaved": round(dist_km * 0.04, 2),
            "co2Reduced": round(dist_km * 0.09, 2),
            "color": "#00d4ff",
            "recommended": False
        },
        {
            "label": "Scenic Bypass",
            "timeMinutes": int(dist_km * 3.2),
            "fuelSaved": 0.0,
            "co2Reduced": 0.0,
            "color": "#9b59f5",
            "recommended": False
        }
    ]
    
    # Waypoints
    waypoints = [
        {"name": req.start, "congestion": "Low"},
        {"name": "Intersection B-42", "congestion": "Medium"},
        {"name": "Green Corridor X", "congestion": "Low"},
        {"name": req.destination, "congestion": "Low"}
    ]
    
    credits_earned = int(dist_km * 2)
    
    return {
        "status": "success",
        "data": {
            "start": req.start,
            "destination": req.destination,
            "distanceKm": round(dist_km, 1),
            "aiConfidence": 94.2,
            "analysisTime": time.time() - start_time,
            "trafficData": traffic_data,
            "routes": routes,
            "waypoints": waypoints,
            "optimized": {
                "fuelSaved": round(dist_km * 0.12, 2),
                "co2Reduced": round(dist_km * 0.28, 2),
                "baselineFuel": round(dist_km * 0.15, 2),
                "baselineCO2": round(dist_km * 0.35, 2),
                "timeMinutes": int(dist_km * 2.5),
                "creditsEarned": credits_earned,
                "greenBoost": 1.2
            }
        }
    }
