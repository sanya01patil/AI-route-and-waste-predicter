const express = require('express');
const cors = require('cors');
const path = require('path');
const rateLimit = require('express-rate-limit');

const authRoutes = require('./src/routes/auth');
const aiRoutes = require('./src/routes/ai');
const blockchainRoutes = require('./src/routes/blockchain');
const dashboardRoutes = require('./src/routes/dashboard');
const saferouteRoutes = require('./src/routes/saferoute');
const { verifyToken } = require('./src/middleware/auth');
const db = require('./src/store/db');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 200,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/', limiter);

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/ai', verifyToken, aiRoutes);
app.use('/api/blockchain', verifyToken, blockchainRoutes);
app.use('/api/dashboard', verifyToken, dashboardRoutes);
app.use('/api/saferoute', verifyToken, saferouteRoutes);

// Serve frontend pages
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'public', 'index.html')));
app.get('/login', (req, res) => res.sendFile(path.join(__dirname, 'public', 'login.html')));
app.get('/dashboard', (req, res) => res.sendFile(path.join(__dirname, 'public', 'dashboard.html')));
app.get('/optimizer', (req, res) => res.sendFile(path.join(__dirname, 'public', 'optimizer.html')));
app.get('/wallet', (req, res) => res.sendFile(path.join(__dirname, 'public', 'wallet.html')));
app.get('/leaderboard', (req, res) => res.sendFile(path.join(__dirname, 'public', 'leaderboard.html')));
app.get('/admin', (req, res) => res.sendFile(path.join(__dirname, 'public', 'admin.html')));
app.get('/saferoute', (req, res) => res.sendFile(path.join(__dirname, 'public', 'saferoute.html')));

// Health check
app.get('/api/health', (req, res) => res.json({ status: 'ok', platform: 'EcoChain AI', time: new Date().toISOString() }));

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`\n🌿 EcoChain AI Server running on http://localhost:${PORT}`);
  console.log(`📊 Admin credentials: admin@ecochain.ai / Admin@123`);
  console.log(`🔗 Blockchain ledger: active\n`);
});

module.exports = app;
