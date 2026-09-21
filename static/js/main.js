(function() {
    'use strict';

    /* ─── CSRF ───────────────────────────────────────────── */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /* ─── AUTO-STYLE DES FORMULAIRES ─────────────────────── */
    function autoStyleForms() {
        document.querySelectorAll('form input:not([type="checkbox"]):not([type="radio"]):not([type="submit"]):not([type="hidden"]):not([type="file"]), form select, form textarea').forEach(field => {
            if (!field.classList.contains('form-control')) field.classList.add('form-control');
        });
        document.querySelectorAll('form label').forEach(label => {
            if (!label.classList.contains('form-label')) label.classList.add('form-label');
        });
    }

    /* ─── THÈME ──────────────────────────────────────────── */
    function setupTheme() {
        const html = document.documentElement;
        const current = localStorage.getItem('theme') || 'light';
        html.setAttribute('data-theme', current);
        updateThemeIcon(current);

        const toggle = document.getElementById('settings-theme-toggle');
        if (!toggle) return;

        toggle.addEventListener('click', function() {
            const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            updateThemeIcon(next);

            const url = '/api/set-theme/';
            fetch(url, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
                body: JSON.stringify({ theme: next })
            }).catch(() => {});
        });
    }

    function updateThemeIcon(theme) {
        const icon = document.getElementById('settings-theme-icon');
        const label = document.getElementById('settings-theme-label');
        if (icon) {
            icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }
        if (label) {
            label.textContent = theme === 'dark' ? 'Mode clair' : 'Mode sombre';
        }
    }

    /* ─── SPLASH SCREEN ──────────────────────────────────── */
    function setupSplash() {
        const splash = document.getElementById('splash-screen');
        if (!splash) return;
        if (sessionStorage.getItem('splashShown') === 'true') {
            splash.style.display = 'none';
            return;
        }
        window.addEventListener('load', function() {
            setTimeout(function() {
                splash.classList.add('hidden');
                sessionStorage.setItem('splashShown', 'true');
                setTimeout(() => splash.style.display = 'none', 600);
            }, 1600);
        });
    }

    /* ─── CARROUSEL HOME ─────────────────────────────────── */
    function setupCarousel() {
        const carousel = document.getElementById('hero-carousel');
        if (!carousel) return;

        const slides = carousel.querySelectorAll('.carousel-slide');
        const dots = carousel.querySelectorAll('.carousel-dot');
        if (slides.length < 2) return;

        let currentIndex = 0;

        function goTo(index) {
            slides.forEach((s, i) => s.classList.toggle('active', i === index));
            dots.forEach((d, i) => d.classList.toggle('active', i === index));
            currentIndex = index;
        }

        dots.forEach((dot, i) => {
            dot.addEventListener('click', e => {
                e.preventDefault();
                e.stopPropagation();
                goTo(i);
            });
        });

        setInterval(() => {
            goTo((currentIndex + 1) % slides.length);
        }, 5000);
    }

    /* ─── LIKE ŒUVRE ─────────────────────────────────────── */
    function setupLikeButtons() {
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.like-btn');
            if (!btn) return;
            e.preventDefault();
            const url = btn.getAttribute('data-like-url');
            if (!url || url === '#') return;

            fetch(url, {
                method: 'POST',
                headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
                body: JSON.stringify({})
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'not_authenticated') {
                    window.location.href = data.redirect_url;
                    return;
                }
                const count = btn.querySelector('.like-count');
                if (count) count.textContent = data.likes_count;
                btn.classList.toggle('liked', data.user_liked);
                const icon = btn.querySelector('i');
                if (icon) icon.className = data.user_liked ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
            })
            .catch(() => {});
        });
    }

    /* ─── LIKE CHAPITRE ──────────────────────────────────── */
    function setupChapterLikes() {
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.chapter-like-btn');
            if (!btn) return;
            e.preventDefault();

            fetch(btn.dataset.url, {
                method: 'POST',
                headers: {'X-CSRFToken': getCookie('csrftoken')}
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'not_authenticated') {
                    window.location.href = data.redirect_url;
                    return;
                }
                const icon = btn.querySelector('i');
                if (data.user_liked) icon.className = 'fa-solid fa-heart';
                else icon.className = 'fa-regular fa-heart';
                const match = btn.dataset.url.match(/\/(\d+)\//);
                if (match) {
                    const count = document.querySelector(`.chapter-like-count-${match[1]}`);
                    if (count) count.textContent = data.likes_count;
                }
            })
            .catch(() => {});
        });
    }

    /* ─── LIKE COMMENTAIRE ───────────────────────────────── */
    function setupCommentLikes() {
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.comment-like-btn');
            if (!btn) return;
            e.preventDefault();

            fetch(btn.dataset.url, {
                method: 'POST',
                headers: {'X-CSRFToken': getCookie('csrftoken')}
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'not_authenticated') {
                    window.location.href = data.redirect_url;
                    return;
                }
                const icon = btn.querySelector('i');
                const count = btn.querySelector('.comment-like-count');
                if (data.user_liked) icon.className = 'fa-solid fa-heart';
                else icon.className = 'fa-regular fa-heart';
                if (count) count.textContent = data.likes_count;
            })
            .catch(() => {});
        });
    }

    /* ─── BOUTON FOLLOW (PROFIL) ─────────────────────────── */
    function setupFollowButton() {
        const btn = document.getElementById('follow-btn');
        if (!btn) return;

        btn.addEventListener('click', function() {
            fetch(btn.dataset.url, {
                method: 'POST',
                headers: {'X-CSRFToken': getCookie('csrftoken')}
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) return;
                const countEl = document.getElementById('followers-count');
                if (countEl) countEl.textContent = data.followers_count;

                if (data.is_following) {
                    btn.className = 'btn btn-outline';
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Abonné';
                } else {
                    btn.className = 'btn btn-primary';
                    btn.innerHTML = '<i class="fa-solid fa-plus"></i> Suivre';
                }
            })
            .catch(() => {});
        });
    }

    /* ─── BOUTONS FOLLOW DANS LES LISTES ─────────────────── */
    function setupFollowListButtons() {
        document.querySelectorAll('.follow-list-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                fetch(btn.dataset.url, {
                    method: 'POST',
                    headers: {'X-CSRFToken': getCookie('csrftoken')}
                })
                .then(r => r.json())
                .then(data => {
                    if (data.error) return;
                    if (data.is_following) {
                        btn.className = 'btn btn-outline follow-list-btn';
                        btn.innerHTML = '<i class="fa-solid fa-check"></i> Abonné';
                    } else {
                        btn.className = 'btn btn-primary follow-list-btn';
                        btn.innerHTML = '<i class="fa-solid fa-plus"></i> Suivre';
                    }
                })
                .catch(() => {});
            });
        });
    }

    /* ─── RÉPONSE COMMENTAIRE ────────────────────────────── */
    function setupCommentReply() {
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.comment-reply-btn');
            if (!btn) return;
            const form = document.querySelector(`.reply-form[data-comment-id="${btn.dataset.commentId}"]`);
            if (form) form.style.display = form.style.display === 'none' ? 'block' : 'none';
        });
    }

    /* ─── BIBLIOTHÈQUE ───────────────────────────────────── */
    function setupLibraryButton() {
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('#library-btn');
            if (!btn) return;
            e.preventDefault();
            const url = btn.getAttribute('data-library-url');
            if (!url || url === '#') return;

            fetch(url, {
                method: 'POST',
                headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
                body: JSON.stringify({})
            })
            .then(r => r.json())
            .then(data => {
                // ═══ Redirection si non connecté ═══
                if (data.status === 'not_authenticated') {
                    window.location.href = data.redirect_url;
                    return;
                }
                // ═══ Sinon comportement normal ═══
                if (data.is_in_library) {
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Dans la bibliothèque';
                    btn.classList.add('active');
                } else {
                    btn.innerHTML = '<i class="fa-solid fa-plus"></i> Ajouter à la bibliothèque';
                    btn.classList.remove('active');
                }
            })
            .catch(() => {});
        });
    }

    /* ─── NOTIFICATIONS ──────────────────────────────────── */
    function setupNotifications() {
        const btn = document.getElementById('notif-toggle');
        const dropdown = document.getElementById('notif-dropdown');
        if (!btn || !dropdown) return;

        function clearAllDots() {
            document.querySelectorAll('.notif-dot').forEach(dot => dot.remove());
            dropdown.querySelectorAll('.notif-item.unread').forEach(el => el.classList.remove('unread'));
        }

        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const settingsDropdown = document.getElementById('settings-dropdown');
            if (settingsDropdown) settingsDropdown.classList.remove('open');
            dropdown.classList.toggle('open');
            if (dropdown.classList.contains('open')) {
                fetch('/notifications/read-all/', {
                    method: 'POST',
                    headers: {'X-CSRFToken': getCookie('csrftoken')}
                }).then(() => clearAllDots()).catch(() => {});
            }
        });

        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
                dropdown.classList.remove('open');
            }
        });

        const markAllBtn = document.getElementById('mark-all-read');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                fetch('/notifications/read-all/', {
                    method: 'POST',
                    headers: {'X-CSRFToken': getCookie('csrftoken')}
                }).then(() => clearAllDots()).catch(() => {});
            });
        }
    }

    /* ─── MENU PARAMÈTRES ────────────────────────────────── */
    function setupSettingsMenu() {
        const btn = document.getElementById('settings-toggle');
        const dropdown = document.getElementById('settings-dropdown');
        if (!btn || !dropdown) return;

        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const notifDropdown = document.getElementById('notif-dropdown');
            if (notifDropdown) notifDropdown.classList.remove('open');
            dropdown.classList.toggle('open');
        });

        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
                dropdown.classList.remove('open');
            }
        });

        const langToggle = document.getElementById('settings-lang-toggle');
        const langSublist = document.getElementById('settings-lang-sublist');
        const langArrow = document.getElementById('settings-lang-arrow');

        if (langToggle && langSublist) {
            langToggle.addEventListener('click', function(e) {
                e.stopPropagation();
                langSublist.classList.toggle('open');
                if (langArrow) langArrow.classList.toggle('open', langSublist.classList.contains('open'));
            });
        }
    }

    /* ─── FOCUS AUTO SUR LA RECHERCHE ────────────────────── */
    function setupSearchFocus() {
        const params = new URLSearchParams(window.location.search);
        if (params.get('focus') === 'search') {
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) {
                setTimeout(() => {
                    searchInput.focus();
                    searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 200);
            }
        }
    }

    /* ─── BARRE DE PROGRESSION DE LECTURE ────────────────── */
    function setupReadingProgress() {
        const bar = document.getElementById('reading-progress-bar');
        const fill = document.getElementById('reading-progress-fill');
        const label = document.getElementById('reading-progress-label');
        if (!bar || !fill) return;

        const workId = document.body.dataset.workId;
        const chapterId = document.body.dataset.chapterId;
        let lastSent = -1;
        let isDragging = false;

        function getMaxScroll() {
            return document.documentElement.scrollHeight - window.innerHeight;
        }

        function updateBarFromScroll() {
            if (isDragging) return;
            const max = getMaxScroll();
            const percent = max > 0 ? (window.scrollY / max) * 100 : 0;
            const clamped = Math.min(100, Math.max(0, percent));
            fill.style.width = clamped + '%';
            if (label) label.textContent = Math.round(clamped) + '%';
            bar.style.setProperty('--pos', clamped + '%');
        }

        function sendProgress(percent) {
            if (!workId || !chapterId) return;
            if (Math.abs(percent - lastSent) < 3 && percent !== 100) return;
            lastSent = percent;

            fetch('/api/reading-progress/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
                body: JSON.stringify({
                    work_id: workId,
                    chapter_id: chapterId,
                    percent: Math.round(percent),
                    scroll_position: Math.round(window.scrollY)
                })
            }).catch(() => {});
        }

        window.addEventListener('scroll', function() {
            updateBarFromScroll();
            clearTimeout(window.__progressTimer);
            window.__progressTimer = setTimeout(function() {
                const max = getMaxScroll();
                const percent = max > 0 ? (window.scrollY / max) * 100 : 0;
                sendProgress(percent);
            }, 800);
        });

        window.addEventListener('resize', updateBarFromScroll);
        updateBarFromScroll();

        function seekFromEvent(clientX) {
            const rect = bar.getBoundingClientRect();
            const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
            const ratio = x / rect.width;
            const max = getMaxScroll();
            window.scrollTo({ top: ratio * max, behavior: 'auto' });

            fill.style.width = (ratio * 100) + '%';
            if (label) label.textContent = Math.round(ratio * 100) + '%';
            bar.style.setProperty('--pos', (ratio * 100) + '%');
        }

        bar.addEventListener('mousedown', function(e) {
            isDragging = true;
            bar.classList.add('dragging');
            seekFromEvent(e.clientX);
        });

        document.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            seekFromEvent(e.clientX);
        });

        document.addEventListener('mouseup', function() {
            if (!isDragging) return;
            isDragging = false;
            bar.classList.remove('dragging');
            const max = getMaxScroll();
            const percent = max > 0 ? (window.scrollY / max) * 100 : 0;
            sendProgress(percent);
        });

        bar.addEventListener('touchstart', function(e) {
            isDragging = true;
            bar.classList.add('dragging');
            seekFromEvent(e.touches[0].clientX);
        }, { passive: true });

        bar.addEventListener('touchmove', function(e) {
            if (!isDragging) return;
            seekFromEvent(e.touches[0].clientX);
        }, { passive: true });

        bar.addEventListener('touchend', function() {
            if (!isDragging) return;
            isDragging = false;
            bar.classList.remove('dragging');
            const max = getMaxScroll();
            const percent = max > 0 ? (window.scrollY / max) * 100 : 0;
            sendProgress(percent);
        });
    }

    /* ─── INIT ───────────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', function() {
        autoStyleForms();
        setupTheme();
        setupSplash();
        setupCarousel();
        setupLikeButtons();
        setupChapterLikes();
        setupCommentLikes();
        setupFollowButton();
        setupFollowListButtons();
        setupCommentReply();
        setupLibraryButton();
        setupNotifications();
        setupSettingsMenu();
        setupSearchFocus();
        setupReadingProgress();
    });
})();