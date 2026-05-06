// ─── API Helper ───────────────────────────────────────────────────────────
const BASE = '';

function getToken() {
    return localStorage.getItem('ecochain_token');
}

function getUser() {
    try {
        return JSON.parse(localStorage.getItem('ecochain_user') || 'null');
    } catch { return null; }
}

function setSession(token, user) {
    localStorage.setItem('ecochain_token', token);
    localStorage.setItem('ecochain_user', JSON.stringify(user));
}

function clearSession() {
    localStorage.removeItem('ecochain_token');
    localStorage.removeItem('ecochain_user');
}

async function apiFetch(path, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(options.headers || {})
    };

    const res = await fetch(BASE + path, {
        ...options,
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined
    });

    const data = await res.json().catch(() => ({}));

    if (res.status === 401 || res.status === 403) {
        clearSession();
        window.location.href = '/login';
        return;
    }

    if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}`);
    }

    return data;
}

// Convenience methods
const API = {
    post: (path, body) => apiFetch(path, { method: 'POST', body }),
    get: (path) => apiFetch(path, { method: 'GET' }),
    put: (path, body) => apiFetch(path, { method: 'PUT', body }),
};

// ─── Auth Guard ────────────────────────────────────────────────────────────
function requireAuth() {
    if (!getToken()) window.location.href = '/login';
}

function requireAdmin() {
    const user = getUser();
    if (!user || user.role !== 'admin') window.location.href = '/dashboard';
}

// ─── Toast System ──────────────────────────────────────────────────────────
function showToast(message, type = 'success', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = { success: '✅', error: '❌', info: 'ℹ️', warn: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
    <span class="toast-icon">${icons[type] || '💬'}</span>
    <span class="toast-msg">${message}</span>
  `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ─── Number Animation ──────────────────────────────────────────────────────
function animateNumber(el, target, duration = 1200, decimals = 0) {
    const start = parseFloat(el.textContent.replace(/,/g, '')) || 0;
    const startTime = performance.now();
    const diff = target - start;

    function update(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease out cubic
        const value = start + diff * eased;
        el.textContent = decimals > 0 ? value.toFixed(decimals) : Math.round(value).toLocaleString();
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ─── Sidebar Helpers ───────────────────────────────────────────────────────
function populateSidebar() {
    const user = getUser();
    if (!user) return;

    const nameEl = document.getElementById('sidebar-user-name');
    const roleEl = document.getElementById('sidebar-user-role');
    const avatarEl = document.getElementById('sidebar-avatar');

    if (nameEl) nameEl.textContent = user.name;
    if (roleEl) roleEl.textContent = user.role === 'admin' ? '⚡ Admin' : '🌿 Eco User';
    if (avatarEl) avatarEl.textContent = (user.name || 'U').charAt(0).toUpperCase();

    // Mark active nav
    const links = document.querySelectorAll('.nav-item');
    links.forEach(link => {
        if (link.href && window.location.pathname.startsWith(new URL(link.href).pathname)) {
            link.classList.add('active');
        }
    });

    // Credit display
    const creditEl = document.getElementById('sidebar-credits');
    if (creditEl) creditEl.textContent = (user.carbonCredits || 0).toLocaleString();
}

function logout() {
    clearSession();
    window.location.href = '/login';
}

// ─── Copy to Clipboard ─────────────────────────────────────────────────────
function copyToClipboard(text, feedbackEl) {
    navigator.clipboard.writeText(text).then(() => {
        if (feedbackEl) {
            const orig = feedbackEl.textContent;
            feedbackEl.textContent = '✓';
            setTimeout(() => { feedbackEl.textContent = orig; }, 1500);
        }
        showToast('Copied to clipboard!', 'success', 2000);
    });
}

// ─── Particles ────────────────────────────────────────────────────────────
function initParticles(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = Array.from({ length: 40 }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 1.5 + 0.5,
        speed: Math.random() * 0.4 + 0.1,
        opacity: Math.random() * 0.5 + 0.1,
        dx: (Math.random() - 0.5) * 0.3
    }));

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0,255,136,${p.opacity})`;
            ctx.fill();
            p.y -= p.speed;
            p.x += p.dx;
            if (p.y < -5) { p.y = canvas.height + 5; p.x = Math.random() * canvas.width; }
        });
        requestAnimationFrame(draw);
    }

    draw();
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// ─── Format Utilities ──────────────────────────────────────────────────────
function formatDate(ts) {
    return new Date(ts).toLocaleString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
}

function shortenAddr(addr) {
    if (!addr || addr.length < 12) return addr;
    return addr.slice(0, 8) + '...' + addr.slice(-6);
}

// ─── WebSocket Live Traffic ────────────────────────────────────────────────
function initLiveTraffic() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'alert' || data.type === 'clear') {
                const toastType = data.severity === 'high' ? 'error' : (data.severity === 'moderate' ? 'warn' : 'info');
                const msg = `<b>${data.icon} ${data.area}</b><br>${data.desc}`;
                showToast(msg, toastType, 6000);
            }
        } catch (e) {
            console.log("WebSocket message:", event.data);
        }
    };

    ws.onclose = () => {
        console.log("Live traffic stream disconnected. Reconnecting in 5s...");
        setTimeout(initLiveTraffic, 5000);
    };
}

// Start WebSocket connection on load
window.addEventListener('load', initLiveTraffic);
