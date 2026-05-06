from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..ml.engine import predict_route_metrics
from ..services.weather import get_weather
from ..models.route import AnalyzeRequest

router = APIRouter(prefix="/api/saferoute", tags=["saferoute"])

ROAD_TYPES = ['Highway', 'City Road', 'Urban Expressway']
RISK_ZONES = [
    {'type': '⚠️ High-risk zone', 'desc': 'Accident-prone intersection'},
    {'type': '🚧 Construction', 'desc': 'Active road construction'},
    {'type': '🛑 Accident hotspot', 'desc': 'Recent accident reported'},
    {'type': '🔧 Poor condition', 'desc': 'Road digging / damaged surface'},
]

def hash_str(s: str) -> int:
    h = 5381
    for char in s:
        h = ((h << 5) + h) ^ ord(char)
    return abs(h)

def build_route(name: str, index: int, seed: int, base_dist: float, is_night: bool, vehicle_type: str, color: str, rtype: str, weather_condition: str = "Clear"):
    dist_mult = 1.0 if index == 0 else (1.15 if index == 1 else 1.3)
    dist = base_dist * dist_mult
    road_type = ROAD_TYPES[index % len(ROAD_TYPES)]
    
    preds = predict_route_metrics(dist, is_night, road_type, vehicle_type, weather_condition)
    
    base_rate = 0.05
    if vehicle_type == 'suv': base_rate = 0.08
    elif vehicle_type == 'motorbike': base_rate = 0.03
    elif vehicle_type == 'electric': base_rate = 0.01
    elif vehicle_type == 'bus': base_rate = 0.02
    
    traffic = int((seed % 40) + index * 15 + preds["congestion_penalty"])
    traffic = max(5, min(95, traffic))
    
    stop_freq = int(dist * (0.5 if road_type == 'City Road' else 0.1) * (traffic/50))
    avg_speed = int((100 - traffic) * (1.2 if road_type == 'Highway' else 0.8))
    
    base_fuel = base_rate * dist
    congestion_penalty = (traffic / 100) * (base_fuel * 0.4)
    signal_penalty = stop_freq * 0.05 * base_rate
    instability_factor = (traffic - 60) * 0.01 if traffic > 60 else 0
    
    fuel_used = round(base_fuel + congestion_penalty + signal_penalty + instability_factor, 2)
    co2_emission = round(fuel_used * 2.31, 2) if vehicle_type != 'electric' else round(fuel_used * 0.5, 2)
    
    time_minutes = int((dist / max(1, avg_speed)) * 60)
    
    accident_risk = int(preds["accident_risk"])
    safety_rating = max(10, 100 - accident_risk - int(traffic*0.2))
    
    eco_score = round((min(100, fuel_used * 10) * 0.4) + (min(100, co2_emission * 10) * 0.3) + (traffic * 0.2) + ((100 - safety_rating) * 0.1), 1)
    
    risk_label = "Low" if accident_risk < 20 else "Moderate" if accident_risk < 50 else "High"
    traffic_level = "Low Traffic" if traffic < 40 else "Moderate" if traffic < 75 else "Heavy Congestion"
    
    return {
        "id": f"route_{index}",
        "name": name,
        "type": rtype,
        "distanceKm": round(dist, 1),
        "timeMinutes": time_minutes,
        "fuelUsed": fuel_used,
        "co2Emission": co2_emission,
        "stopFrequency": stop_freq,
        "avgSpeed": avg_speed,
        "traffic": traffic,
        "trafficLevel": traffic_level,
        "trafficColor": "green" if traffic < 40 else "yellow" if traffic < 75 else "red",
        "accidentRisk": accident_risk,
        "safetyRating": safety_rating,
        "ecoScore": eco_score,
        "riskLabel": risk_label,
        "roadType": road_type,
        "color": color,
        "creditsEarned": 50 if index == 0 else 0
    }

@router.post("/analyze")
async def analyze_routes(req: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    seed = hash_str(req.start.lower() + req.destination.lower())
    is_night = req.timeOfDay == 'night'
    base_dist = 8 + (seed % 83)
    
    weather = await get_weather(req.start)
    weather_condition = weather["condition"] if weather else "Clear"
    
    routes = [
        build_route("Eco Safe Route", 0, seed, base_dist, is_night, req.vehicleType, "#22c55e", "eco", weather_condition),
        build_route("Standard Route", 1, seed, base_dist, is_night, req.vehicleType, "#f59e0b", "std", weather_condition),
        build_route("Fast Expressway", 2, seed, base_dist, is_night, req.vehicleType, "#ef4444", "exp", weather_condition),
    ]
    
    best_route = min(routes, key=lambda x: x["ecoScore"])
    for r in routes:
        r["recommended"] = (r["id"] == best_route["id"])
        
    start_coord = [19.07 + (seed%10)*0.01, 72.87 + (seed%10)*0.01]
    dest_coord = [start_coord[0] + base_dist*0.005, start_coord[1] + base_dist*0.005]
    
    map_data = {"startCoord": start_coord, "destCoord": dest_coord, "polylines": []}
    
    for i, r in enumerate(routes):
        offset = i * 0.008
        points = [start_coord, [start_coord[0] + (dest_coord[0]-start_coord[0])/2 + offset, start_coord[1] + (dest_coord[1]-start_coord[1])/2 - offset], dest_coord]
        markers = []
        if r["accidentRisk"] > 30:
            hazard = RISK_ZONES[seed % len(RISK_ZONES)]
            markers.append({"lat": points[1][0], "lng": points[1][1], "icon": hazard["type"].split(" ")[0], "desc": hazard["desc"]})
        
        map_data["polylines"].append({"coords": points, "color": r["color"], "popup": f"<b>{r['name']}</b>", "markers": markers})
        
    return {
        "start": req.start, "destination": req.destination, "routes": routes, "mapData": map_data, "weather": weather,
        "recommendation": {"routeId": best_route["id"], "routeName": best_route["name"]}
    }

@router.get("/conditions")
async def get_conditions():
    return {"conditions": [{"type": "🚧", "area": "Highway A1", "desc": "Maintenance"}]}
