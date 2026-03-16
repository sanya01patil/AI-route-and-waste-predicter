const { v4: uuidv4 } = require('uuid');
const bcrypt = require('bcryptjs');

// ─── In-Memory Data Store ──────────────────────────────────────────────────
const users = new Map();
const sessions = new Map();

// Append-only blockchain ledger (tamper-proof simulation)
const blockchainLedger = Object.freeze({
    _entries: [],
    append(entry) {
        const record = Object.freeze({
            txHash: '0x' + uuidv4().replace(/-/g, ''),
            blockNumber: this._entries.length + 1,
            timestamp: Date.now(),
            ...entry
        });
        this._entries.push(record);
        return record;
    },
    getAll() { return [...this._entries]; },
    getByUser(userId) { return this._entries.filter(e => e.userId === userId); }
});

// ─── Seed Admin User ───────────────────────────────────────────────────────
(async () => {
    const adminId = 'f76698b0-1af0-4983-af1f-d4d8397c6ec0'; // Static ID so sessions survive restarts
    const hashedPassword = await bcrypt.hash('Admin@123', 10);
    users.set(adminId, {
        id: adminId,
        name: 'EcoChain Admin',
        email: 'admin@ecochain.ai',
        password: hashedPassword,
        role: 'admin',
        walletAddress: '0xADM1N' + adminId.replace(/-/g, '').slice(0, 34).toUpperCase(),
        carbonCredits: 0,
        greenScore: 100,
        totalRoutes: 0,
        totalFuelSaved: 0,
        totalCO2Reduced: 0,
        joinedAt: Date.now()
    });
})();

// ─── User Helpers ──────────────────────────────────────────────────────────
function createUser({ name, email, password }) {
    const id = uuidv4();
    const walletAddress = '0x' + id.replace(/-/g, '').slice(0, 40).toUpperCase();
    const user = {
        id,
        name,
        email,
        password,
        role: 'user',
        walletAddress,
        carbonCredits: 0,
        greenScore: 50,
        totalRoutes: 0,
        totalFuelSaved: 0,
        totalCO2Reduced: 0,
        joinedAt: Date.now()
    };
    users.set(id, user);
    return user;
}

function findUserByEmail(email) {
    for (const user of users.values()) {
        if (user.email.toLowerCase() === email.toLowerCase()) return user;
    }
    return null;
}

function findUserById(id) {
    return users.get(id) || null;
}

function updateUser(id, updates) {
    const user = users.get(id);
    if (!user) return null;
    Object.assign(user, updates);
    return user;
}

function getAllUsers() {
    return [...users.values()].map(u => ({
        id: u.id,
        name: u.name,
        email: u.email,
        role: u.role,
        walletAddress: u.walletAddress,
        carbonCredits: u.carbonCredits,
        greenScore: u.greenScore,
        totalRoutes: u.totalRoutes,
        totalFuelSaved: u.totalFuelSaved,
        totalCO2Reduced: u.totalCO2Reduced,
        joinedAt: u.joinedAt
    }));
}

function getPublicUser(user) {
    const { password, ...pub } = user;
    return pub;
}

module.exports = {
    users,
    blockchainLedger,
    createUser,
    findUserByEmail,
    findUserById,
    updateUser,
    getAllUsers,
    getPublicUser
};
