const express = require('express');
const router = express.Router();
const { findUserById, getAllUsers, blockchainLedger } = require('../store/db');
const { requireAdmin } = require('../middleware/auth');

// GET /api/dashboard/stats  (user's own stats)
router.get('/stats', (req, res) => {
    const user = findUserById(req.user.id);
    if (!user) return res.status(404).json({ error: 'User not found.' });

    const userTxns = blockchainLedger.getByUser(user.id);

    // Build weekly activity (last 7 days)
    const now = Date.now();
    const weeklyData = Array.from({ length: 7 }, (_, i) => {
        const dayStart = now - (6 - i) * 86400000;
        const dayEnd = dayStart + 86400000;
        const dayTxns = userTxns.filter(t => t.timestamp >= dayStart && t.timestamp < dayEnd);
        return {
            day: new Date(dayStart).toLocaleDateString('en-US', { weekday: 'short' }),
            credits: dayTxns.reduce((s, t) => s + t.amount, 0),
            co2: parseFloat(dayTxns.reduce((s, t) => s + (t.co2Reduced || 0), 0).toFixed(3)),
            routes: dayTxns.length
        };
    });

    // Green score tier
    const score = user.greenScore;
    const tier = score >= 500 ? 'Platinum' : score >= 200 ? 'Gold' : score >= 100 ? 'Silver' : 'Bronze';
    const tierColor = score >= 500 ? '#e5e4e2' : score >= 200 ? '#ffd700' : score >= 100 ? '#c0c0c0' : '#cd7f32';

    res.json({
        user: {
            id: user.id,
            name: user.name,
            email: user.email,
            walletAddress: user.walletAddress,
            carbonCredits: user.carbonCredits,
            greenScore: user.greenScore,
            totalRoutes: user.totalRoutes,
            totalFuelSaved: user.totalFuelSaved,
            totalCO2Reduced: user.totalCO2Reduced,
            tier,
            tierColor,
            joinedAt: user.joinedAt
        },
        weeklyData,
        recentTransactions: [...userTxns].reverse().slice(0, 5)
    });
});

// GET /api/dashboard/admin  (admin only)
router.get('/admin', requireAdmin, (req, res) => {
    const allUsers = getAllUsers();
    const allTxns = blockchainLedger.getAll();

    const totalCredits = allTxns.reduce((s, t) => s + t.amount, 0);
    const totalCO2 = parseFloat(allTxns.reduce((s, t) => s + (t.co2Reduced || 0), 0).toFixed(3));
    const totalFuel = parseFloat(allTxns.reduce((s, t) => s + (t.fuelSaved || 0), 0).toFixed(2));
    const totalRoutes = allUsers.reduce((s, u) => s + u.totalRoutes, 0);
    const avgGreenScore = allUsers.length
        ? Math.round(allUsers.reduce((s, u) => s + u.greenScore, 0) / allUsers.length)
        : 0;

    // Top 5 users by credits
    const topUsers = [...allUsers]
        .filter(u => u.role !== 'admin')
        .sort((a, b) => b.carbonCredits - a.carbonCredits)
        .slice(0, 5);

    // Daily credits for last 7 days (platform-wide)
    const now = Date.now();
    const dailyStats = Array.from({ length: 7 }, (_, i) => {
        const dayStart = now - (6 - i) * 86400000;
        const dayEnd = dayStart + 86400000;
        const dayTxns = allTxns.filter(t => t.timestamp >= dayStart && t.timestamp < dayEnd);
        return {
            day: new Date(dayStart).toLocaleDateString('en-US', { weekday: 'short' }),
            credits: dayTxns.reduce((s, t) => s + t.amount, 0),
            routes: dayTxns.length,
            co2: parseFloat(dayTxns.reduce((s, t) => s + (t.co2Reduced || 0), 0).toFixed(3))
        };
    });

    res.json({
        overview: {
            totalUsers: allUsers.filter(u => u.role !== 'admin').length,
            totalCreditsIssued: totalCredits,
            totalCO2Reduced: totalCO2,
            totalFuelSaved: totalFuel,
            totalRoutes,
            avgGreenScore,
            blockHeight: allTxns.length
        },
        users: allUsers,
        topUsers,
        dailyStats,
        recentTransactions: [...allTxns].reverse().slice(0, 10)
    });
});

module.exports = router;
