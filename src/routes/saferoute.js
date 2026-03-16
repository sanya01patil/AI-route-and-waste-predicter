const express = require('express');
const router = express.Router();

// ─── Road Type Database (simulated) ───────────────────────────────────────
const ROAD_TYPES = ['Highway', 'City Road', 'Urban Expressway', 'Ring Road', 'Arterial Road'];
const RISK_ZONES = [
    { type: '⚠️ High-risk zone', desc: 'Accident-prone intersection' },
    { type: '🚧 Construction', desc: 'Active road construction' },
    { type: '🛑 Accident hotspot', desc: 'Recent accident reported' },
    { type: '🔧 Poor condition', desc: 'Road digging / damaged surface' },
];

// ─── Deterministic hash utility ────────────────────────────────────────────
function hash(str) {
    let h = 5381;
    for (let i = 0; i < str.length; i++) h = ((h << 5) + h) ^ str.charCodeAt(i);
    return Math.abs(h);
}

// ─── Core AI Simulation Engine ─────────────────────────────────────────────
function simulateSafeRoute(start, destination, timeOfDay, vehicleType) {
    const seed = hash(start.toLowerCase() + destination.toLowerCase());
    const isNight = timeOfDay === 'night';

    // Simulated distance 8–90 km
    const baseDist = 8 + (seed % 83);

    // Generate 3 route variants
    const routes = [
        buildRoute('Eco Safe Route', 0, seed, baseDist, isNight, vehicleType, '#22c55e', 'eco'),
        buildRoute('Standard Route', 1, seed, baseDist, isNight, vehicleType, '#f59e0b', 'std'),
        buildRoute('Fast Expressway', 2, seed, baseDist, isNight, vehicleType, '#ef4444', 'exp'),
    ];

    // Determine recommended route (lowest mathematical Eco Score)
    let best = routes.reduce((a, b) => a.ecoScore < b.ecoScore ? a : b);
    best.recommended = true;

    // AI recommendation reasoning
    const reasoning = [
        `Recommended: Safest & Most Fuel-Efficient (Eco Score: ${best.ecoScore.toFixed(1)})`,
        `Lowest fuel usage: ${best.fuelUsed} L`,
        `Reduced emissions: ${(routes[2].co2Emission - best.co2Emission).toFixed(1)} kg vs alternate`,
        `Balanced flow: ${best.stopFrequency} signal stops · ${best.avgSpeed} km/h avg`,
    ];

    // Calculate geocoded waypoints for Leaflet map
    const mapData = buildMapData(start, destination, seed, routes);

    return {
        start, destination, timeOfDay, vehicleType,
        routes,
        recommendation: { routeName: best.name, reasoning },
        mapData,
        aiEngine: {
            model: 'SafeRoute-ML v3.1',
            confidence: 82 + (seed % 16),
            processTime: ((180 + seed % 300) / 1000).toFixed(3),
            dataPoints: 14200 + (seed % 8000)
        }
    };
}

function buildRoute(name, idx, seed, baseDist, isNight, vehicleType, color, type) {
    const s = seed ^ (idx * 0x9e3779b9);   // vary seed per route

    // Distance with slight variation per route
    const dist = parseFloat((baseDist * [1.15, 1.0, 0.88][idx]).toFixed(1));

    // Traffic score: 0=low, 100=high
    const trafficBase = [25, 52, 78][idx] + (s % 18) - 9;
    const traffic = Math.max(5, Math.min(95, trafficBase));

    const trafficLevel = traffic < 35 ? 'Low' : traffic < 65 ? 'Medium' : 'Heavy';
    const trafficColor = traffic < 35 ? 'green' : traffic < 65 ? 'yellow' : 'red';

    // Stop frequency (based on traffic)
    const stopFrequency = Math.round((traffic / 20) + (dist / 12) + (s % 3));

    // Avg Speed
    const avgSpeed = Math.round(Math.max(15, 85 - traffic * 0.7));
    const timeMin = Math.round((dist / avgSpeed) * 60);

    // ── Fuel Usage Formula ──
    // Fuel Usage = (Base fuel rate × Distance) + (Traffic congestion penalty) + (Signal stop penalty) + (Speed instability factor)
    const baseRates = { car: 0.07, suv: 0.11, motorbike: 0.03, electric: 0.015, bus: 0.22 };
    const baseRate = baseRates[vehicleType] || 0.07;

    const baseFuel = baseRate * dist;
    const congestionPenalty = (traffic / 100) * (baseFuel * 0.4);
    const signalPenalty = stopFrequency * 0.05 * baseRate;
    const instabilityFactor = (traffic > 60 ? (traffic - 60) * 0.01 : 0);

    const fuelUsed = parseFloat((baseFuel + congestionPenalty + signalPenalty + instabilityFactor).toFixed(2));
    const co2Emission = parseFloat((fuelUsed * 2.31).toFixed(2)); // kg CO2/L

    // Accident risk factors
    const densityFactor = traffic * 0.4;
    const nightFactor = isNight ? 18 : 0;
    const roadType = ROAD_TYPES[(s % ROAD_TYPES.length)];
    const highwayBonus = roadType === 'Highway' ? -8 : roadType === 'City Road' ? 10 : 0;
    const histFactor = (s % 25);
    const accidentRisk = Math.max(3, Math.min(92,
        Math.round((densityFactor + nightFactor + highwayBonus + histFactor) / 3)
    ));
    const riskLabel = accidentRisk < 30 ? 'Low' : accidentRisk < 60 ? 'Moderate' : 'High';
    const riskColor = accidentRisk < 30 ? 'green' : accidentRisk < 60 ? 'orange' : 'red';

    // Safety rating
    const safetyRating = Math.max(10, Math.round(100 - accidentRisk * 0.6 - traffic * 0.4));

    // ── Eco Score Formula ──
    // Eco Score = (Low fuel weight 40%) + (Low CO2 weight 30%) + (Smooth flow weight 20%) + (Safety rating weight 10%)
    // Note: For Eco Score, lower is better, so we use inverse weights for positive metrics.
    const flowScore = 100 - (traffic * 0.5 + stopFrequency * 2);

    // We normalize variables to a 0-100 scale for scoring
    const fuelFactor = Math.min(100, (fuelUsed / (baseRate * baseDist * 2)) * 100);
    const co2Factor = Math.min(100, (co2Emission / (baseRate * baseDist * 5)) * 100);
    const safetyFactor = 100 - safetyRating; // inverse because lower Eco Score is better
    const trafficFactor = 100 - flowScore;

    const ecoScore = parseFloat((
        (fuelFactor * 0.4) +
        (co2Factor * 0.3) +
        (trafficFactor * 0.2) +
        (safetyFactor * 0.1)
    ).toFixed(1));

    // Warning zones (1–3 per route)
    const zoneCount = 1 + (s % 3);
    const warningZones = Array.from({ length: zoneCount }, (_, i) => ({
        ...RISK_ZONES[(s + i) % RISK_ZONES.length],
        km: parseFloat((dist * (0.2 + i * 0.25)).toFixed(1))
    }));

    return {
        name, idx, color, type,
        distanceKm: dist,
        timeMinutes: timeMin,
        traffic,
        trafficLevel,
        trafficColor,
        roadType,
        stopFrequency,
        avgSpeed,
        accidentRisk,
        riskLabel,
        riskColor,
        fuelUsed,
        co2Emission,
        safetyRating,
        ecoScore,
        warningZones,
        recommended: false,
        creditsEarned: type === 'eco' ? Math.max(1, Math.round(co2Emission * 0.8)) : 0
    };
}

// ─── Map Data (Leaflet-ready coordinates) ─────────────────────────────────
// We embed a small city lookup table; unknown cities get a randomized position
const CITY_COORDS = {
    'mumbai': [19.076, 72.877],
    'delhi': [28.704, 77.102],
    'bangalore': [12.972, 77.594],
    'new york': [40.712, -74.005],
    'london': [51.505, -0.090],
    'paris': [48.856, 2.352],
    'tokyo': [35.689, 139.691],
    'sydney': [-33.868, 151.209],
    'dubai': [25.204, 55.270],
    'singapore': [1.352, 103.819],
    'chicago': [41.878, -87.630],
    'los angeles': [34.052, -118.244],
    'toronto': [43.651, -79.347],
    'berlin': [52.520, 13.404],
    'airport': [19.089, 72.867],
    'downtown': [19.060, 72.835],
    'mall': [19.075, 72.865],
    'station': [19.050, 72.840],
};

function fuzzyGeo(name, seed) {
    const lower = name.toLowerCase();
    for (const [key, coords] of Object.entries(CITY_COORDS)) {
        if (lower.includes(key)) return [...coords];
    }
    // Fallback: random city-like coordinate
    const lat = -60 + (seed % 130);
    const lng = -170 + (seed % 340);
    return [lat, lng];
}

function buildMapData(start, destination, seed, routes) {
    const startCoord = fuzzyGeo(start, seed);
    const destCoord = fuzzyGeo(destination, seed ^ 0xdeadbeef);

    // Generate route polylines (3 curves between same endpoints)
    const polylines = routes.map((r, i) => {
        const midLat = (startCoord[0] + destCoord[0]) / 2;
        const midLng = (startCoord[1] + destCoord[1]) / 2;

        // Perpendicular offset to make routes visually distinct
        const dlat = destCoord[0] - startCoord[0];
        const dlng = destCoord[1] - startCoord[1];
        const perp = [-dlng, dlat];
        const mag = Math.sqrt(perp[0] ** 2 + perp[1] ** 2) || 1;
        const offsets = [-0.015, 0.0, 0.015];
        const scale = offsets[i] / mag;

        const via1 = [midLat + perp[0] * scale * 0.7 + (startCoord[0] - midLat) * 0.3,
        midLng + perp[1] * scale * 0.7 + (startCoord[1] - midLng) * 0.3];
        const via2 = [midLat + perp[0] * scale,
        midLng + perp[1] * scale];
        const via3 = [midLat + perp[0] * scale * 0.7 + (destCoord[0] - midLat) * 0.3,
        midLng + perp[1] * scale * 0.7 + (destCoord[1] - midLng) * 0.3];

        // Warning zone markers along route
        const markers = r.warningZones.map((z, j) => {
            const t = 0.2 + j * 0.25;
            return {
                lat: startCoord[0] + (destCoord[0] - startCoord[0]) * t + perp[0] * scale * 0.5,
                lng: startCoord[1] + (destCoord[1] - startCoord[1]) * t + perp[1] * scale * 0.5,
                icon: z.type.split(' ')[0],
                desc: z.type + ' — ' + z.desc,
                routeIdx: i
            };
        });

        return {
            routeIdx: i,
            color: r.color,
            coords: [startCoord, via1, via2, via3, destCoord],
            markers,
            popup: `${r.name}<br>${r.distanceKm}km · ${r.timeMinutes}min · Risk: ${r.riskLabel}`
        };
    });

    return { startCoord, destCoord, polylines };
}

// ─── Routes ───────────────────────────────────────────────────────────────
// POST /api/saferoute/analyze
router.post('/analyze', (req, res) => {
    try {
        const { start, destination, timeOfDay = 'day', vehicleType = 'car' } = req.body;

        if (!start || !destination)
            return res.status(400).json({ error: 'Start and destination are required.' });
        if (start.trim() === destination.trim())
            return res.status(400).json({ error: 'Start and destination must be different.' });

        const result = simulateSafeRoute(start.trim(), destination.trim(), timeOfDay, vehicleType);
        res.json({ success: true, data: result });
    } catch (err) {
        console.error('[SafeRoute] Error:', err);
        res.status(500).json({ error: 'Route analysis failed.' });
    }
});

// GET /api/saferoute/conditions
router.get('/conditions', (req, res) => {
    // Simulate live road condition feed
    const NOW = Date.now();
    const CONDITIONS = [
        { area: 'Highway NH-48, Km 24', type: '🚧', desc: 'Lane narrowing – construction', severity: 'medium' },
        { area: 'City Centre Crossroads', type: '⚠️', desc: 'High accident density zone', severity: 'high' },
        { area: 'Airport Link Road', type: '🛑', desc: 'Accident cleared 20 min ago', severity: 'low' },
        { area: 'Industrial Ring Road', type: '🔧', desc: 'Pothole repairs in progress', severity: 'medium' },
        { area: 'Expressway Entry Ramp', type: '⚠️', desc: 'Merge conflict – slow traffic', severity: 'high' },
    ];
    res.json({ conditions: CONDITIONS, updatedAt: NOW });
});

module.exports = router;
