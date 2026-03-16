const express = require('express');
const bcrypt = require('bcryptjs');
const router = express.Router();

const { generateToken } = require('../middleware/auth');
const { createUser, findUserByEmail, getPublicUser } = require('../store/db');

// POST /api/auth/signup
router.post('/signup', async (req, res) => {
    try {
        const { name, email, password } = req.body;

        if (!name || !email || !password)
            return res.status(400).json({ error: 'Name, email and password are required.' });

        if (password.length < 6)
            return res.status(400).json({ error: 'Password must be at least 6 characters.' });

        if (findUserByEmail(email))
            return res.status(409).json({ error: 'Email already registered.' });

        const hashed = await bcrypt.hash(password, 10);
        const user = createUser({ name, email, password: hashed });

        const token = generateToken({ id: user.id, email: user.email, role: user.role });

        res.status(201).json({
            message: 'Account created successfully!',
            token,
            user: getPublicUser(user)
        });
    } catch (err) {
        console.error('[Auth] Signup error:', err);
        res.status(500).json({ error: 'Signup failed.' });
    }
});

// POST /api/auth/login
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        if (!email || !password)
            return res.status(400).json({ error: 'Email and password are required.' });

        const user = findUserByEmail(email);
        if (!user) return res.status(401).json({ error: 'Invalid credentials.' });

        const valid = await bcrypt.compare(password, user.password);
        if (!valid) return res.status(401).json({ error: 'Invalid credentials.' });

        const token = generateToken({ id: user.id, email: user.email, role: user.role });

        res.json({
            message: 'Login successful!',
            token,
            user: getPublicUser(user)
        });
    } catch (err) {
        console.error('[Auth] Login error:', err);
        res.status(500).json({ error: 'Login failed.' });
    }
});

// GET /api/auth/me
router.get('/me', require('../middleware/auth').verifyToken, (req, res) => {
    const { findUserById } = require('../store/db');
    const user = findUserById(req.user.id);
    if (!user) return res.status(404).json({ error: 'User not found.' });
    res.json({ user: getPublicUser(user) });
});

module.exports = router;
