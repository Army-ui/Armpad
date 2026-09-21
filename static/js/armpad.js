/* ============================================================
   ARMPAD — JavaScript principal v2.1 (amélioré)
   ============================================================ */

// ── Fonction apiFetch (intercepte les 401) ───────────────────
async function apiFetch(url, options = {}) {
  const token = localStorage.getItem('armpad_token');
  const headers = { ...options.headers };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  // Ne pas forcer Content-Type si on envoie du FormData
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    // Token invalide ou expiré
    localStorage.removeItem('armpad_token');
    localStorage.removeItem('armpad_refresh');
    // Rediriger vers la connexion si on est sur une page protégée
    if (!window.location.pathname.startsWith('/connexion') &&
        !window.location.pathname.startsWith('/inscription')) {
      window.location.href = '/connexion/?next=' + encodeURIComponent(window.location.pathname);
    }
  }
  return response;
}

// ── Splash Screen ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const splash = document.getElementById('splash-screen');
  if (!splash) return;
  const shown = sessionStorage.getItem('armpad_splash');
  if (shown) {
    splash.style.display = 'none';
  } else {
    sessionStorage.setItem('armpad_splash', '1');
    setTimeout(() => splash.classList.add('hidden'), 2400);
  }
});

// ── Thème sombre / clair ──────────────────────────────────────
const ThemeManager = {
  key: 'armpad_theme',
  init() {
    const saved = localStorage.getItem(this.key) || 'light';
    this.apply(saved, false);
  },
  apply(theme, sync = true) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.key, theme);
    document.querySelectorAll('.theme-toggle').forEach(btn => {
      btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    });
    if (sync) this.syncToServer(theme);
  },
  toggle() {
    const cur = document.documentElement.getAttribute('data-theme') || 'light';
    this.apply(cur === 'dark' ? 'light' : 'dark');
  },
  async syncToServer(theme) {
    const token = Auth.getToken();
    if (!token) return;
    try {
      await apiFetch('/api/v1/users/me/theme/', {
        method: 'POST',
        body: JSON.stringify({ theme })
      });
    } catch {
      // Ignorer
    }
  }
};

// ── Auth ──────────────────────────────────────────────────────
const Auth = {
  getToken()   { return localStorage.getItem('armpad_token'); },
  setToken(t)  { localStorage.setItem('armpad_token', t); },
  getRefresh() { return localStorage.getItem('armpad_refresh'); },
  clear()      { localStorage.removeItem('armpad_token'); localStorage.removeItem('armpad_refresh'); }
};

// ── Formulaire d'inscription ──────────────────────────────────
function initRegisterForm() {
  const form = document.getElementById('register-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = form.querySelector('[name=username]').value.trim();
    const email    = form.querySelector('[name=email]').value.trim();
    const password = form.querySelector('[name=password]').value;
    const errEl    = document.getElementById('register-error');
    const btn      = form.querySelector('button[type=submit]');

    if (!username || !email || !password) {
      errEl.textContent = 'Tous les champs sont obligatoires.'; return;
    }
    if (password.length < 8) {
      errEl.textContent = 'Le mot de passe doit contenir au moins 8 caractères.'; return;
    }

    btn.disabled = true;
    btn.textContent = 'Création en cours…';
    errEl.textContent = '';

    try {
      const res = await fetch('/api/v1/users/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, password_confirm: password, preferred_language: 'fr' })
      });
      const data = await res.json();
      if (res.ok) {
        window.location.href = '/connexion/?registered=1';
      } else {
        const msgs = Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ');
        errEl.textContent = msgs || 'Erreur lors de la création.';
        btn.disabled = false;
        btn.textContent = '🚀 Créer mon compte';
      }
    } catch {
      errEl.textContent = 'Erreur réseau. Réessayez.';
      btn.disabled = false;
      btn.textContent = '🚀 Créer mon compte';
    }
  });
}

// ── Notifications ─────────────────────────────────────────────
const Notifications = {
  loading: false,
  async load() {
    if (this.loading) return;
    const token = Auth.getToken();
    if (!token) return;
    this.loading = true;
    try {
      const res = await apiFetch('/api/v1/users/notifications/');
      if (!res.ok) return;
      const data = await res.json();
      const count = (data.results || data).filter(n => !n.is_read).length;
      const badge = document.getElementById('notif-badge');
      if (badge) {
        badge.textContent = count > 0 ? count : '';
        badge.style.display = count > 0 ? 'flex' : 'none';
      }
    } catch {
      // silencieux
    } finally {
      this.loading = false;
    }
  },
  async markRead(id) {
    const token = Auth.getToken();
    if (!token) return;
    try {
      await apiFetch(`/api/v1/users/notifications/${id}/read/`, { method: 'POST' });
    } catch {}
  },
  async markAllRead() {
    const token = Auth.getToken();
    if (!token) return;
    try {
      await apiFetch('/api/v1/users/notifications/read-all/', { method: 'POST' });
      this.load();
    } catch {}
  }
};

// ── Gestion des menus déroulants ─────────────────────────────
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.notif-dropdown.open, .dropdown.open').forEach(el => {
      el.classList.remove('open');
    });
  }
});

document.addEventListener('click', (e) => {
  const notifBtn = document.querySelector('.notif-btn');
  if (notifBtn && !notifBtn.contains(e.target)) {
    const dd = document.getElementById('notif-dropdown');
    if (dd) dd.classList.remove('open');
  }
});

window.toggleNotifs = function() {
  const dd = document.getElementById('notif-dropdown');
  if (!dd) return;
  dd.classList.toggle('open');
  if (dd.classList.contains('open')) {
    const list = document.getElementById('notif-list');
    if (list && list.children.length <= 1) {
      loadNotificationDetails();
    }
  }
};

async function loadNotificationDetails() {
  const token = Auth.getToken();
  if (!token) return;
  const list = document.getElementById('notif-list');
  if (!list) return;
  list.innerHTML = '<p style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px;">Chargement…</p>';
  try {
    const res = await apiFetch('/api/v1/users/notifications/');
    if (!res.ok) { list.innerHTML = '<p style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px;">Aucune notification.</p>'; return; }
    const data = await res.json();
    const notifs = data.results || data;
    if (!notifs.length) {
      list.innerHTML = '<p style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px;">Aucune notification.</p>';
      return;
    }
    list.innerHTML = notifs.map(n => `
      <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="readNotif('${n.id}', '${n.link || '/'}')">
        <div class="notif-text">${n.message}</div>
        <div class="notif-time">${new Date(n.created_at).toLocaleDateString('fr-FR')}</div>
      </div>
    `).join('');
  } catch {
    list.innerHTML = '<p style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px;">Erreur de chargement.</p>';
  }
}

window.readNotif = async function(id, link) {
  await Notifications.markRead(id);
  window.location.href = link;
};

window.markAllRead = async function() {
  await Notifications.markAllRead();
  document.getElementById('notif-badge').style.display = 'none';
  await loadNotificationDetails();
};

// ── Init globale ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
  initRegisterForm();
  document.querySelectorAll('.theme-toggle').forEach(btn => {
    btn.addEventListener('click', () => ThemeManager.toggle());
  });
  Notifications.load();
  setInterval(() => Notifications.load(), 60000);
});

// Exposer les APIs globales
window.Auth = Auth;
window.Notifications = Notifications;
window.ThemeManager = ThemeManager;
window.apiFetch = apiFetch;