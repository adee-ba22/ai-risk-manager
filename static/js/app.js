/**
 * AI Risk Manager - Single Page Application Router & State Manager
 */

const state = {
    currentUser: null,
    token: localStorage.getItem('token') || null,
    currentRoute: 'landing',
    risks: [],
    selectedSeverity: 'All',
    selectedStatus: 'All',
    searchQuery: ''
};

// ================= ROUTER =================
const router = {
    navigate: function(route) {
        // Protected route verification
        const publicRoutes = ['landing', 'signin', 'signup'];
        if (!state.token && !publicRoutes.includes(route)) {
            showToast("Please sign in to access protected dashboard routes.", "warning");
            route = 'signin';
        }

        // Admin-only route verification
        if (route === 'admin-users' && state.currentUser && state.currentUser.role !== 'admin') {
            showToast("Access denied. Administrator privileges required.", "error");
            route = 'dashboard';
        }

        state.currentRoute = route;
        window.location.hash = route;

        // Hide all views
        document.querySelectorAll('.view-section').forEach(sec => sec.classList.add('hidden'));

        // Show target view
        const targetView = document.getElementById(`${route}-view`) || document.getElementById(`${route}-page`);
        if (targetView) {
            targetView.classList.remove('hidden');
        }

        // Update header & sidebar UI states
        updateNavigationUI();

        // Trigger view specific loaders
        if (route === 'dashboard') loadDashboardData();
        if (route === 'risk-register') loadRiskRegisterData();
        if (route === 'admin-users') loadAdminUserData();
        if (route === 'settings') loadSettingsData();

        // Refresh Lucide icons
        if (window.lucide) lucide.createIcons();
    }
};

window.addEventListener('hashchange', () => {
    const hash = window.location.hash.replace('#', '') || 'landing';
    router.navigate(hash);
});

// ================= AUTHENTICATION HANDLERS =================

async function initApp() {
    if (state.token) {
        try {
            const res = await apiFetch('/api/auth/me');
            if (res.id) {
                state.currentUser = res;
                updateUserHeaderUI();
                const initialHash = window.location.hash.replace('#', '') || 'dashboard';
                router.navigate(initialHash);
                return;
            }
        } catch (e) {
            console.error("Token verification failed:", e);
            state.token = null;
            localStorage.removeItem('token');
        }
    }
    const initialHash = window.location.hash.replace('#', '') || 'landing';
    router.navigate(initialHash);
}

function updateNavigationUI() {
    const topHeader = document.getElementById('top-header');
    const sidebarNav = document.getElementById('sidebar-nav');
    const adminNavLink = document.getElementById('admin-nav-link');

    if (state.currentUser) {
        topHeader.classList.remove('hidden');
        sidebarNav.classList.remove('hidden');
        
        // Highlight active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            if (item.getAttribute('data-route') === state.currentRoute) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Hide Admin nav link if standard user
        if (adminNavLink) {
            if (state.currentUser.role === 'admin') {
                adminNavLink.classList.remove('hidden');
            } else {
                adminNavLink.classList.add('hidden');
            }
        }
    } else {
        topHeader.classList.add('hidden');
        sidebarNav.classList.add('hidden');
    }
}

function updateUserHeaderUI() {
    if (!state.currentUser) return;
    const nameEl = document.getElementById('nav-user-name');
    const roleEl = document.getElementById('nav-user-role');
    const avatarEl = document.getElementById('nav-user-avatar');

    if (nameEl) nameEl.textContent = state.currentUser.name;
    if (roleEl) roleEl.textContent = state.currentUser.role.toUpperCase();
    if (avatarEl) avatarEl.textContent = state.currentUser.name.charAt(0).toUpperCase();
}

async function handleSignUp(event) {
    event.preventDefault();
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const role = document.getElementById('signup-role').value;

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, role })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Registration failed');

        state.token = data.token;
        state.currentUser = data.user;
        localStorage.setItem('token', data.token);

        updateUserHeaderUI();
        showToast(`Welcome ${data.user.name}! Account created successfully.`, "success");
        router.navigate('dashboard');
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function handleSignIn(event) {
    event.preventDefault();
    const email = document.getElementById('signin-email').value;
    const password = document.getElementById('signin-password').value;

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Sign in failed');

        state.token = data.token;
        state.currentUser = data.user;
        localStorage.setItem('token', data.token);

        updateUserHeaderUI();
        showToast(`Welcome back, ${data.user.name}!`, "success");
        router.navigate('dashboard');
    } catch (err) {
        showToast(err.message, "error");
    }
}

function handleLogout() {
    fetch('/api/auth/logout', { method: 'POST' }).finally(() => {
        state.token = null;
        state.currentUser = null;
        localStorage.removeItem('token');
        showToast("Signed out successfully.", "info");
        router.navigate('signin');
    });
}

function quickFillLogin(email, password) {
    document.getElementById('signin-email').value = email;
    document.getElementById('signin-password').value = password;
    showToast(`Autofilled demo login for ${email}`, "info");
}

// ================= DASHBOARD LOADER =================

async function loadDashboardData() {
    try {
        const stats = await apiFetch('/api/dashboard/stats');
        
        // Update Stats Counters
        document.getElementById('dash-stat-score').textContent = stats.avg_risk_score;
        document.getElementById('dash-stat-total').textContent = stats.total_risks;
        document.getElementById('dash-stat-critical').textContent = stats.critical_risks;
        document.getElementById('dash-stat-open').textContent = stats.open_risks;
        document.getElementById('dash-stat-mitigated').textContent = stats.mitigated_risks;

        const levelBadge = document.getElementById('dash-stat-level-badge');
        if (levelBadge) {
            levelBadge.textContent = `${stats.overall_risk_level.toUpperCase()} OVERALL RISK`;
            levelBadge.className = `mt-2 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold ${getSeverityClass(stats.overall_risk_level)}`;
        }

        // Render Charts
        if (window.renderSeverityDistributionChart) {
            renderSeverityDistributionChart(stats.severity_distribution);
        }
        if (window.renderStatusDistributionChart) {
            renderStatusDistributionChart(stats.status_distribution);
        }

        // Render Recent Table
        const recentBody = document.getElementById('dash-recent-table-body');
        if (recentBody) {
            recentBody.innerHTML = stats.recent_risks.map(r => `
                <tr class="hover:bg-slate-800/50 transition cursor-pointer" onclick="openRiskModal(${r.id})">
                    <td class="p-3">
                        <div class="font-bold text-white">${escapeHtml(r.title)}</div>
                        <div class="text-xs text-slate-400">${escapeHtml(r.asset)}</div>
                    </td>
                    <td class="p-3 text-xs text-slate-300">${escapeHtml(r.threat_type)}</td>
                    <td class="p-3 text-xs font-bold text-white">${r.risk_score}</td>
                    <td class="p-3">
                        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold ${getSeverityClass(r.severity)}">
                            ${r.severity}
                        </span>
                    </td>
                    <td class="p-3 text-xs font-semibold ${r.status === 'Mitigated' ? 'text-emerald-400' : 'text-amber-400'}">
                        ${r.status}
                    </td>
                    <td class="p-3 text-right">
                        <button onclick="event.stopPropagation(); openRiskModal(${r.id})" class="text-xs text-indigo-400 hover:underline">View Details</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error("Failed to load dashboard metrics:", e);
    }
}

// ================= RISK ASSESSMENT CALCULATOR =================

function calculateFormScore() {
    const l = parseInt(document.getElementById('form-likelihood').value || 3);
    const i = parseInt(document.getElementById('form-impact').value || 3);
    const score = l * i;

    let sev = "Low";
    let sevClass = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
    if (score >= 16) {
        sev = "CRITICAL";
        sevClass = "bg-rose-500/20 text-rose-400 border-rose-500/30";
    } else if (score >= 10) {
        sev = "HIGH";
        sevClass = "bg-orange-500/20 text-orange-400 border-orange-500/30";
    } else if (score >= 5) {
        sev = "MEDIUM";
        sevClass = "bg-amber-500/20 text-amber-400 border-amber-500/30";
    }

    const scoreDisplay = document.getElementById('calc-score-display');
    const badge = document.getElementById('calc-severity-badge');

    if (scoreDisplay) scoreDisplay.textContent = score;
    if (badge) {
        badge.textContent = `${sev} SEVERITY`;
        badge.className = `inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-bold border ${sevClass}`;
    }
}

async function previewAIRecommendations() {
    const title = document.getElementById('form-title').value;
    const description = document.getElementById('form-description').value;
    const asset = document.getElementById('form-asset').value;
    const threat_type = document.getElementById('form-threat-type').value;
    const likelihood = document.getElementById('form-likelihood').value;
    const impact = document.getElementById('form-impact').value;

    if (!title || !description) {
        showToast("Please enter a title and description to generate AI analysis.", "warning");
        return;
    }

    const container = document.getElementById('ai-preview-container');
    container.innerHTML = `<div class="flex items-center gap-2 text-slate-400"><i data-lucide="loader" class="w-4 h-4 animate-spin"></i> Generating AI Recommendations...</div>`;
    if (window.lucide) lucide.createIcons();

    try {
        const payload = { title, description, asset, threat_type, likelihood, impact };
        const rec = await apiFetch('/api/risks/recommend', 'POST', payload);

        container.innerHTML = `
            <div class="space-y-2">
                <div>
                    <span class="font-bold text-slate-300">Explanation:</span>
                    <p class="text-[11px] text-slate-400 mt-0.5">${escapeHtml(rec.ai_explanation)}</p>
                </div>
                <div>
                    <span class="font-bold text-slate-300">Suggested Controls:</span>
                    <p class="text-[11px] text-cyan-400 font-medium mt-0.5">${escapeHtml(rec.ai_controls)}</p>
                </div>
                <div>
                    <span class="font-bold text-slate-300">Mitigation Steps:</span>
                    <pre class="text-[11px] text-slate-300 whitespace-pre-wrap font-sans mt-0.5 bg-slate-950 p-2 rounded border border-slate-800">${escapeHtml(rec.ai_mitigation)}</pre>
                </div>
            </div>
        `;
        showToast("AI Recommendations preview updated!", "info");
    } catch (err) {
        container.innerHTML = `<p class="text-rose-400">Failed to generate AI recommendation: ${err.message}</p>`;
    }
}

async function handleCreateRisk(event) {
    event.preventDefault();
    const title = document.getElementById('form-title').value;
    const description = document.getElementById('form-description').value;
    const asset = document.getElementById('form-asset').value;
    const threat_type = document.getElementById('form-threat-type').value;
    const likelihood = document.getElementById('form-likelihood').value;
    const impact = document.getElementById('form-impact').value;
    const existing_controls = document.getElementById('form-existing-controls').value;
    const notes = document.getElementById('form-notes').value;

    try {
        const payload = { title, description, asset, threat_type, likelihood, impact, existing_controls, notes };
        const created = await apiFetch('/api/risks', 'POST', payload);
        showToast(`Risk '${created.title}' recorded with score ${created.risk_score} (${created.severity})`, "success");
        
        document.getElementById('assessment-form').reset();
        router.navigate('risk-register');
    } catch (err) {
        showToast(err.message, "error");
    }
}

// ================= RISK REGISTER LOADER & FILTERS =================

async function loadRiskRegisterData() {
    try {
        const risks = await apiFetch('/api/risks');
        state.risks = risks;
        renderRiskRegister();

        const sidebarCount = document.getElementById('sidebar-risk-count');
        if (sidebarCount) sidebarCount.textContent = risks.length;
    } catch (e) {
        console.error("Failed to load risk register:", e);
    }
}

function setSeverityFilter(sev) {
    state.selectedSeverity = sev;
    document.querySelectorAll('.filter-sev-btn').forEach(btn => {
        if (btn.getAttribute('data-sev') === sev) {
            btn.className = 'filter-sev-btn px-2.5 py-1 rounded-lg bg-indigo-600 text-white font-medium';
        } else {
            btn.className = 'filter-sev-btn px-2.5 py-1 rounded-lg text-slate-400 hover:text-white';
        }
    });
    renderRiskRegister();
}

function filterRiskRegister() {
    state.searchQuery = document.getElementById('register-search').value.toLowerCase();
    state.selectedStatus = document.getElementById('register-status-filter').value;
    renderRiskRegister();
}

function renderRiskRegister() {
    const tbody = document.getElementById('risk-register-body');
    if (!tbody) return;

    let filtered = state.risks.filter(r => {
        const matchSev = state.selectedSeverity === 'All' || r.severity === state.selectedSeverity;
        const matchStatus = state.selectedStatus === 'All' || r.status === state.selectedStatus;
        const matchSearch = !state.searchQuery || 
            r.title.toLowerCase().includes(state.searchQuery) ||
            r.asset.toLowerCase().includes(state.searchQuery) ||
            r.threat_type.toLowerCase().includes(state.searchQuery);
        return matchSev && matchStatus && matchSearch;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="p-8 text-center text-slate-400">
                    <i data-lucide="shield-alert" class="w-8 h-8 mx-auto mb-2 text-slate-600"></i>
                    <p class="font-medium">No matching cybersecurity risks found.</p>
                </td>
            </tr>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    tbody.innerHTML = filtered.map(r => `
        <tr class="hover:bg-slate-800/40 transition">
            <td class="p-4">
                <div class="font-bold text-white">${escapeHtml(r.title)}</div>
                <div class="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                    <i data-lucide="server" class="w-3 h-3"></i> ${escapeHtml(r.asset)}
                </div>
            </td>
            <td class="p-4 text-xs text-slate-300 font-medium">${escapeHtml(r.threat_type)}</td>
            <td class="p-4 text-center">
                <span class="font-bold text-white text-base">${r.risk_score}</span>
                <span class="text-[10px] text-slate-500 block">(${r.likelihood}×${r.impact})</span>
            </td>
            <td class="p-4">
                <span class="px-2.5 py-1 rounded-full text-xs font-bold ${getSeverityClass(r.severity)}">
                    ${r.severity}
                </span>
            </td>
            <td class="p-4">
                <select onchange="handleStatusChange(${r.id}, this.value)" class="bg-slate-800 text-xs text-slate-200 px-2 py-1 rounded-lg border border-slate-700 focus:outline-none">
                    <option value="Open" ${r.status === 'Open' ? 'selected' : ''}>Open</option>
                    <option value="In Progress" ${r.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                    <option value="Mitigated" ${r.status === 'Mitigated' ? 'selected' : ''}>Mitigated</option>
                </select>
            </td>
            <td class="p-4 text-xs text-slate-400">${escapeHtml(r.creator_name || 'System')}</td>
            <td class="p-4 text-right space-x-2">
                <button onclick="openRiskModal(${r.id})" class="p-1.5 text-indigo-400 hover:text-white rounded-lg hover:bg-slate-800" title="View Details">
                    <i data-lucide="eye" class="w-4 h-4"></i>
                </button>
                <button onclick="handleDeleteRisk(${r.id})" class="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800" title="Delete Risk">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
            </td>
        </tr>
    `).join('');

    if (window.lucide) lucide.createIcons();
}

async function handleStatusChange(riskId, newStatus) {
    try {
        await apiFetch(`/api/risks/${riskId}/status`, 'PATCH', { status: newStatus });
        showToast(`Risk status updated to ${newStatus}`, "success");
        loadRiskRegisterData();
    } catch (e) {
        showToast(e.message, "error");
    }
}

async function handleDeleteRisk(riskId) {
    if (!confirm("Are you sure you want to delete this risk record?")) return;
    try {
        await apiFetch(`/api/risks/${riskId}`, 'DELETE');
        showToast("Risk record deleted.", "info");
        loadRiskRegisterData();
    } catch (e) {
        showToast(e.message, "error");
    }
}

// ================= RISK DETAILS MODAL =================

async function openRiskModal(riskId) {
    try {
        const risk = await apiFetch(`/api/risks/${riskId}`);
        
        document.getElementById('modal-risk-title').textContent = risk.title;
        document.getElementById('modal-risk-asset').textContent = `Asset: ${risk.asset} | Threat Vector: ${risk.threat_type}`;
        document.getElementById('modal-risk-score').textContent = risk.risk_score;
        document.getElementById('modal-risk-matrix').textContent = `${risk.likelihood} (Likelihood) × ${risk.impact} (Impact)`;
        document.getElementById('modal-risk-status').textContent = risk.status;
        document.getElementById('modal-risk-desc').textContent = risk.description;

        const badge = document.getElementById('modal-sev-badge');
        badge.textContent = risk.severity.toUpperCase();
        badge.className = `px-2.5 py-0.5 rounded-full text-xs font-bold ${getSeverityClass(risk.severity)}`;

        document.getElementById('modal-ai-explanation').textContent = risk.ai_explanation || 'N/A';
        document.getElementById('modal-ai-mitigation').textContent = risk.ai_mitigation || 'N/A';
        document.getElementById('modal-ai-controls').textContent = risk.ai_controls || 'N/A';

        document.getElementById('risk-detail-modal').classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        showToast(e.message, "error");
    }
}

function closeRiskModal() {
    document.getElementById('risk-detail-modal').classList.add('hidden');
}

// ================= ADMIN USER TRACKING LOADER =================

async function loadAdminUserData() {
    const tbody = document.getElementById('admin-users-table-body');
    if (!tbody) return;

    try {
        const data = await apiFetch('/api/admin/users');
        const sessions = data.sessions || [];

        if (sessions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="p-6 text-center text-slate-400">No user sign-in activity recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = sessions.map(s => `
            <tr class="hover:bg-slate-800/40 transition">
                <td class="p-4 font-bold text-white">${escapeHtml(s.name)}</td>
                <td class="p-4 text-xs text-indigo-400">${escapeHtml(s.email)}</td>
                <td class="p-4 text-xs font-semibold ${s.role === 'admin' ? 'text-rose-400' : 'text-slate-300'}">
                    ${s.role.toUpperCase()}
                </td>
                <td class="p-4 text-xs text-slate-300 font-mono">${s.sign_in_time}</td>
                <td class="p-4 text-xs text-slate-400 font-mono">${s.ip_address}</td>
                <td class="p-4">
                    <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Active
                    </span>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-6 text-center text-rose-400">Access Denied: ${err.message}</td></tr>`;
    }
}

// ================= SETTINGS LOADER =================

async function loadSettingsData() {
    try {
        const settings = await apiFetch('/api/settings');
        const input = document.getElementById('setting-gemini-key');
        if (input && settings.masked_gemini_key) {
            input.placeholder = `Configured: ${settings.masked_gemini_key}`;
        }
    } catch (e) {
        console.error("Failed to load settings:", e);
    }
}

async function handleSaveAISettings(event) {
    event.preventDefault();
    const key = document.getElementById('setting-gemini-key').value;
    try {
        await apiFetch('/api/settings', 'PUT', { gemini_api_key: key });
        showToast("AI Key settings saved successfully!", "success");
        document.getElementById('setting-gemini-key').value = '';
        loadSettingsData();
    } catch (e) {
        showToast(e.message, "error");
    }
}

async function handleGeneratePDFReport(event) {
    event.preventDefault();
    const org = document.getElementById('report-org').value;
    const assessor = document.getElementById('report-assessor').value;
    downloadBackendPDFReport(org, assessor);
}

// ================= UTILITIES =================

async function apiFetch(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(endpoint, opts);
    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.error || `HTTP error ${res.status}`);
    }
    return data;
}

function showToast(message, type = "info") {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    let colorClass = "bg-slate-900 border-indigo-500 text-indigo-200";
    if (type === "success") colorClass = "bg-slate-900 border-emerald-500 text-emerald-200";
    if (type === "error") colorClass = "bg-slate-900 border-rose-500 text-rose-200";
    if (type === "warning") colorClass = "bg-slate-900 border-amber-500 text-amber-200";

    toast.className = `p-4 rounded-xl border shadow-2xl text-xs font-medium toast-animate flex items-center justify-between gap-3 ${colorClass}`;
    toast.innerHTML = `
        <span>${escapeHtml(message)}</span>
        <button onclick="this.parentElement.remove()" class="hover:opacity-75"><i data-lucide="x" class="w-4 h-4"></i></button>
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 4000);
}

function getSeverityClass(sev) {
    if (!sev) return "sev-low";
    const s = sev.toLowerCase();
    if (s.includes("critical")) return "sev-critical";
    if (s.includes("high")) return "sev-high";
    if (s.includes("medium")) return "sev-medium";
    return "sev-low";
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function handleGlobalSearch(event) {
    if (event.key === 'Enter') {
        const val = event.target.value;
        if (val) {
            router.navigate('risk-register');
            const regSearch = document.getElementById('register-search');
            if (regSearch) {
                regSearch.value = val;
                filterRiskRegister();
            }
        }
    }
}

// Initialize application on DOM load
document.addEventListener('DOMContentLoaded', () => {
    calculateFormScore();
    initApp();
});
