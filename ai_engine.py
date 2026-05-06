import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Mock Training Data
# Features: [distance, time_of_day (0=Day, 1=Night), road_type (0=Highway, 1=City, 2=Expressway), vehicle_type (0=Gas, 1=EV)]
# Targets: congestion_penalty, accident_risk

X_train = np.array([
    [15, 0, 0, 0], [15, 1, 0, 0], [5, 0, 1, 0], [5, 1, 1, 0],
    [30, 0, 2, 0], [30, 1, 2, 0], [15, 0, 0, 1], [15, 1, 0, 1]
])

# Congestion penalty (higher in city/day)
y_congestion = np.array([10, 5, 25, 10, 5, 2, 10, 5])

# Accident risk (0-100)
y_risk = np.array([15, 25, 30, 10, 10, 20, 15, 25])

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)

# Models
congestion_model = RandomForestRegressor(n_estimators=10, random_state=42)
congestion_model.fit(X_scaled, y_congestion)

risk_model = RandomForestRegressor(n_estimators=10, random_state=42)
risk_model.fit(X_scaled, y_risk)

def predict_route_metrics(distance: float, is_night: bool, road_type: str, vehicle_type: str, weather_condition: str = "Clear"):
    time_feature = 1 if is_night else 0
    road_feature = 0 if road_type == 'Highway' else (2 if 'Expressway' in road_type else 1)
    veh_feature = 1 if vehicle_type == 'electric' else 0
    
    # Weather impact
    weather_impact = 15 if weather_condition in ["Rain", "Snow", "Thunderstorm"] else (5 if weather_condition == "Clouds" else 0)
    
    features = np.array([[distance, time_feature, road_feature, veh_feature]])
    features_scaled = scaler.transform(features)
    
    congestion = congestion_model.predict(features_scaled)[0]
    risk = risk_model.predict(features_scaled)[0]
    
    # Apply weather impact to risk
    risk += weather_impact
    
    # Introduce some stochastic behavior to mimic live AI
    congestion += np.random.normal(0, 2)
    risk += np.random.normal(0, 1.5)
    
    return {
        "congestion_penalty": max(0, float(congestion)),
        "accident_risk": max(0, min(100, float(risk)))
    }
