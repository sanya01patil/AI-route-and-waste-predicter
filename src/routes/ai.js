const express = require('express');
const router = express.Router();
const { findUserById, updateUser } = require('../store/db');

// ─── AI Heuristic Engine ──────────────────────────────────────────────────
// Deterministic ML-like simulation using location hashing + vehicle factors
const VEHICLE_FACTORS = {
    car: { fuelBase: 0.08, co2Factor: 0.192, label: 'Car (Petrol)' },
    suv: { fuelBase: 0.12, co2Factor: 0.288, label: 'SUV / Van' },
    motorbike: { fuelBase: 0.04, co2Factor: 0.096, label: 'Motorbike' },
    electric: { fuelBase: 0.00, co2Factor: 0.020, label: 'Electric Vehicle' },
    bus: { fuelBase: 0.02, co2Factor: 0.048, label: 'Public Bus (shared)' },
};

const ROUTE_TYPES = [
    { id: 'eco', label: 'Eco Express', savingFactor: 0.38, timeFactor: 1.10, color: '#00ff88' },
    { id: 'std', label: 'Standard', savingFactor: 0.15, timeFactor: 1.00, color: '#ffa500' },
    { id: 'exp', label: 'Expressway', savingFactor: 0.05, timeFactor: 0.85, color: '#ff4444' },
];

function hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
    }
    return Math.abs(hash);
}

function simulateAI(start, destination, vehicleType = 'car') {
    const vehicle = VEHICLE_FACTORS[vehicleType] || VEHICLE_FACTORS.car;
    const seed = hashString(start.toLowerCase() + destination.toLowerCase());

    // Simulate distance: 5–80 km based on input hash
    const distanceKm = 5 + (seed % 76);

    // Baseline fuel consumption (no optimization)
    const baselineFuel = distanceKm * vehicle.fuelBase;
    const baselineCO2 = baselineFuel * (vehicle.co2Factor / vehicle.fuelBase || 1) || distanceKm * vehicle.co2Factor;
    const baselineTime = Math.round(distanceKm * 1.8 + (seed % 15));

    // Optimized route metrics
    const ecoRoute = ROUTE_TYPES[0];
    const fuelSaved = parseFloat((baselineFuel * ecoRoute.savingFactor).toFixed(2));
    const co2Reduced = parseFloat((distanceKm * vehicle.co2Factor * ecoRoute.savingFactor).toFixed(3));
    const optimizedTime = Math.round(baselineTime * ecoRoute.timeFactor);
    const creditsEarned = Math.max(1, Math.round(co2Reduced * 10));
    const greenBoost = Math.min(5, Math.round(co2Reduced));

    // Generate waypoints for visual route (simple city coords simulation)
    const waypoints = generateWaypoints(start, destination, seed);

    // Traffic prediction array (hour 0–23 congestion 0–100)
    const trafficData = Array.from({ length: 24 }, (_, h) => {
        const base = (h >= 8 && h <= 10) || (h >= 17 && h <= 20) ? 75 : h < 6 || h > 22 ? 15 : 40;
        return base + (seed % 20) - 10;
    });

    return {
        start,
        destination,
        vehicleType: vehicle.label,
        distanceKm,
        routes: ROUTE_TYPES.map(r => ({
            ...r,
            fuelSaved: r.id === 'eco' ? fuelSaved : parseFloat((baselineFuel * r.savingFactor).toFixed(2)),
            co2Reduced: r.id === 'eco' ? co2Reduced : parseFloat((distanceKm * vehicle.co2Factor * r.savingFactor).toFixed(3)),
            timeMinutes: Math.round(baselineTime * r.timeFactor),
            recommended: r.id === 'eco'
        })),
        optimized: {
            fuelSaved,
            co2Reduced,
            timeMinutes: optimizedTime,
            creditsEarned,
            greenBoost,
            baselineFuel: parseFloat(baselineFuel.toFixed(2)),
            baselineCO2: parseFloat((distanceKm * vehicle.co2Factor).toFixed(3))
        },
        waypoints,
        trafficData,
        aiConfidence: Math.min(98, 78 + (seed % 20)),
        analysisTime: (150 + (seed % 200)) / 1000
    };
}

function generateWaypoints(start, dest, seed) {
    const count = 4 + (seed % 4);
    return Array.from({ length: count }, (_, i) => ({
        name: i === 0 ? start : i === count - 1 ? dest : `Checkpoint ${i}`,
        congestion: ['Low', 'Medium', 'High'][seed % 3 === i % 3 ? 2 : i % 2],
    }));
}

// POST /api/ai/optimize
router.post('/optimize', (req, res) => {
    try {
        const { start, destination, vehicleType } = req.body;

        if (!start || !destination)
            return res.status(400).json({ error: 'Start and destination are required.' });

        if (start.trim() === destination.trim())
            return res.status(400).json({ error: 'Start and destination must be different.' });

        // Simulate processing delay in response header only
        const result = simulateAI(start.trim(), destination.trim(), vehicleType || 'car');

        res.json({ success: true, data: result });
    } catch (err) {
        console.error('[AI] Error:', err);
        res.status(500).json({ error: 'AI optimization failed.' });
    }
});

// GET /api/ai/vehicles
router.get('/vehicles', (req, res) => {
    res.json({
        vehicles: Object.entries(VEHICLE_FACTORS).map(([id, v]) => ({
            id, label: v.label
        }))
    });
});

module.exports = router;
