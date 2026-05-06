from fastapi import APIRouter, Depends
import random
import time
from datetime import datetime
from ..dependencies import get_current_user
from ..services.weather import get_weather
from ..models.route import AnalyzeRequest

router = APIRouter(prefix="/api/saferoute", tags=["saferoute"])

@router.post("/analyze")
async def analyze_safe_route(req: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    # Simulating AI analysis time
    start_time = time.time()
    
    # Get weather for the start location
    weather = await get_weather(req.start)
    
    # Mock data generation based on start/dest
    seed = sum(ord(c) for c in req.start + req.destination)
    random.seed(seed)
    
    dist_km = round(5 + random.random() * 20, 1)
    
    # Generate 3 routes: Eco-Safe (Green), Standard (Yellow), Fast/Express (Red)
    routes = [
        {
            "id": "eco-1",
            "name": "Eco-Safe Optimized",
            "type": "eco",
            "recommended": True,
            "timeMinutes": int(dist_km * 2.8),
            "distanceKm": dist_km,
            "safetyRating": 94,
            "ecoScore": 92,
            "accidentRisk": 12,
            "riskLabel": "Low",
            "traffic": 15,
            "trafficLevel": "Free Flow",
            "trafficColor": "green",
            "fuelUsed": round(dist_km * 0.08, 2),
            "co2Emission": round(dist_km * 0.18, 2),
            "avgSpeed": 42,
            "stopFrequency": 2,
            "roadType": "Local Corridor",
            "color": "#00ff88",
            "creditsEarned": int(dist_km * 1.5),
            "warningZones": [
                {"type": "⚠️ Narrow Road", "desc": "Proceed with caution", "km": round(dist_km * 0.4, 1)}
            ]
        },
        {
            "id": "std-1",
            "name": "Standard Path",
            "type": "std",
            "recommended": False,
            "timeMinutes": int(dist_km * 2.2),
            "distanceKm": round(dist_km * 0.9, 1),
            "safetyRating": 78,
            "ecoScore": 65,
            "accidentRisk": 34,
            "riskLabel": "Moderate",
            "traffic": 45,
            "trafficLevel": "Medium",
            "trafficColor": "yellow",
            "fuelUsed": round(dist_km * 0.12, 2),
            "co2Emission": round(dist_km * 0.28, 2),
            "avgSpeed": 55,
            "stopFrequency": 5,
            "roadType": "Main Avenue",
            "color": "#f59e0b",
            "creditsEarned": 0,
            "warningZones": [
                {"type": "🚧 Construction", "desc": "Reduced lane width", "km": round(dist_km * 0.2, 1)},
                {"type": "🛑 Accident Prone", "desc": "Historical hotspot", "km": round(dist_km * 0.7, 1)}
            ]
        },
        {
            "id": "exp-1",
            "name": "Express Route",
            "type": "exp",
            "recommended": False,
            "timeMinutes": int(dist_km * 1.8),
            "distanceKm": round(dist_km * 1.1, 1),
            "safetyRating": 62,
            "ecoScore": 45,
            "accidentRisk": 58,
            "riskLabel": "High",
            "traffic": 85,
            "trafficLevel": "Heavy Traffic",
            "trafficColor": "red",
            "fuelUsed": round(dist_km * 0.18, 2),
            "co2Emission": round(dist_km * 0.42, 2),
            "avgSpeed": 68,
            "stopFrequency": 8,
            "roadType": "Highway / Flyover",
            "color": "#ef4444",
            "creditsEarned": 0,
            "warningZones": [
                {"type": "🛑 Heavy Congestion", "desc": "Significant delays likely", "km": round(dist_km * 0.5, 1)},
                {"type": "🔧 Poor Road", "desc": "Potholes reported", "km": round(dist_km * 0.9, 1)}
            ]
        }
    ]
    
    # Mock Coordinates for Mumbai area
    base_lat, base_lng = 19.0760, 72.8777
    
    map_data = {
        "startCoord": [base_lat, base_lng],
        "destCoord": [base_lat + 0.05, base_lng + 0.05],
        "polylines": []
    }
    
    for i, r in enumerate(routes):
        # Generate some zig-zag paths
        coords = [[base_lat, base_lng]]
        segments = 8
        curr_lat, curr_lng = base_lat, base_lng
        lat_step = (0.05 + random.random() * 0.02) / segments
        lng_step = (0.05 + random.random() * 0.02) / segments
        
        for _ in range(segments):
            curr_lat += lat_step + (random.random() - 0.5) * 0.01
            curr_lng += lng_step + (random.random() - 0.5) * 0.01
            coords.append([curr_lat, curr_lng])
        
        coords.append([base_lat + 0.05, base_lng + 0.05])
        
        # Add markers along the route
        markers = []
        for wz in r["warningZones"]:
            # Pick a middle point for the marker
            idx = int(len(coords) / 2) + random.randint(-1, 1)
            markers.append({
                "lat": coords[idx][0],
                "lng": coords[idx][1],
                "type": wz["type"],
                "desc": wz["desc"],
                "icon": "⚠️" if "Accident" in wz["type"] else "🚧" if "Construction" in wz["type"] else "🛑" if "Heavy" in wz["type"] else "🔧" if "Poor" in wz["type"] else "📍"
            })

        map_data["polylines"].append({
            "routeId": r["id"],
            "coords": coords,
            "color": r["color"],
            "trafficColor": r["trafficColor"],
            "markers": markers,
            "popup": f"<b>{r['name']}</b><br>Traffic: {r['trafficLevel']}<br>Risk: {r['riskLabel']}"
        })

    best_route = routes[0]
    
    return {
        "start": req.start, "destination": req.destination, "routes": routes, "mapData": map_data, "weather": weather,
        "recommendation": {
            "routeId": best_route["id"],
            "routeName": best_route["name"],
            "reasoning": [
                f"Lowest Eco Score ({best_route['ecoScore']})",
                f"Minimal signal stops ({best_route['stopFrequency']})",
                f"Avoids high-risk accident zones (Risk: {best_route['accidentRisk']}%)"
            ]
        }
    }

@router.get("/conditions")
async def get_road_conditions():
    areas = ["Highway A1", "Downtown Tunnel", "Coastal Road", "Eastern Express", "Linking Road"]
    types = ["🚧 Construction", "🛑 Accident", "☔ Waterlogging", "🚜 Maintenance", "🚦 Signal Failure"]
    
    conditions = []
    for _ in range(4):
        conditions.append({
            "area": random.choice(areas),
            "type": random.choice(types),
            "desc": "Traffic slowing down, AI suggests rerouting",
            "severity": random.choice(["low", "medium", "high"])
        })
    return {"conditions": conditions}
