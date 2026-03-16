const express = require('express');
const router = express.Router();
const { findUserById, updateUser, getAllUsers, blockchainLedger } = require('../store/db');

// GET /api/blockchain/wallet
router.get('/wallet', (req, res) => {
    const user = findUserById(req.user.id);
    if (!user) return res.status(404).json({ error: 'User not found.' });

    res.json({
        walletAddress: user.walletAddress,
        carbonCredits: user.carbonCredits,
        greenScore: user.greenScore,
        networkId: 'EcoChain-Mainnet-v1',
        contractAddress: '0xECO' + 'CHAIN2024HACKATHON'.padEnd(37, '0').slice(0, 37),
        currency: 'ECO'
    });
});

// POST /api/blockchain/mint
router.post('/mint', (req, res) => {
    try {
        const { creditsEarned, greenBoost, fuelSaved, co2Reduced, route } = req.body;

        if (!creditsEarned || creditsEarned <= 0)
            return res.status(400).json({ error: 'Invalid credit amount.' });

        const user = findUserById(req.user.id);
        if (!user) return res.status(404).json({ error: 'User not found.' });

        // Mint credits
        const newBalance = user.carbonCredits + creditsEarned;
        const newGreenScore = Math.min(1000, user.greenScore + (greenBoost || 1));
        const newRoutes = user.totalRoutes + 1;
        const newFuel = parseFloat((user.totalFuelSaved + (fuelSaved || 0)).toFixed(2));
        const newCO2 = parseFloat((user.totalCO2Reduced + (co2Reduced || 0)).toFixed(3));

        updateUser(user.id, {
            carbonCredits: newBalance,
            greenScore: newGreenScore,
            totalRoutes: newRoutes,
            totalFuelSaved: newFuel,
            totalCO2Reduced: newCO2
        });

        // Append to immutable ledger
        const tx = blockchainLedger.append({
            userId: user.id,
            userEmail: user.email,
            userName: user.name,
            walletAddress: user.walletAddress,
            type: 'MINT',
            amount: creditsEarned,
            balance: newBalance,
            route: route || 'Eco Route',
            fuelSaved: fuelSaved || 0,
            co2Reduced: co2Reduced || 0,
            status: 'CONFIRMED'
        });

        res.json({
            success: true,
            transaction: tx,
            newBalance,
            newGreenScore,
            message: `${creditsEarned} ECO credits minted successfully!`
        });
    } catch (err) {
        console.error('[Blockchain] Mint error:', err);
        res.status(500).json({ error: 'Minting failed.' });
    }
});

// GET /api/blockchain/history
router.get('/history', (req, res) => {
    const userTxns = blockchainLedger.getByUser(req.user.id);
    // Return newest first
    res.json({
        transactions: [...userTxns].reverse(),
        count: userTxns.length,
        ledgerImmutable: true,
        networkConsensus: '100%'
    });
});

// GET /api/blockchain/leaderboard
router.get('/leaderboard', (req, res) => {
    const allUsers = getAllUsers()
        .filter(u => u.role !== 'admin')
        .sort((a, b) => b.carbonCredits - a.carbonCredits)
        .slice(0, 10)
        .map((u, i) => ({
            rank: i + 1,
            name: u.name,
            walletAddress: u.walletAddress.slice(0, 10) + '...' + u.walletAddress.slice(-6),
            carbonCredits: u.carbonCredits,
            greenScore: u.greenScore,
            totalRoutes: u.totalRoutes,
            co2Reduced: u.totalCO2Reduced,
            badge: i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '🌿'
        }));

    res.json({ leaderboard: allUsers });
});

// GET /api/blockchain/global-stats
router.get('/global-stats', (req, res) => {
    const allTxns = blockchainLedger.getAll();
    const totalCredits = allTxns.reduce((s, t) => s + t.amount, 0);
    const totalCO2 = allTxns.reduce((s, t) => s + (t.co2Reduced || 0), 0);
    const totalFuel = allTxns.reduce((s, t) => s + (t.fuelSaved || 0), 0);

    res.json({
        totalTransactions: allTxns.length,
        totalCreditsIssued: totalCredits,
        totalCO2Reduced: parseFloat(totalCO2.toFixed(3)),
        totalFuelSaved: parseFloat(totalFuel.toFixed(2)),
        blockHeight: allTxns.length
    });
});

module.exports = router;
