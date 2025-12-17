function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
        document.body.classList.toggle('sidebar-open');
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function (event) {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.mobile-nav-toggle');

    if (document.body.classList.contains('sidebar-open') && sidebar && toggle) {
        if (!sidebar.contains(event.target) && !toggle.contains(event.target)) {
            toggleSidebar();
        }
    }
});

/**
 * Renders the shared sidebar into the <nav class="sidebar"> element.
 * @param {string} activePage - The ID of the active page (dashboard, roster, games, admin)
 */
function renderSidebar(activePage) {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    // Default Links
    const links = [
        { id: 'dashboard', icon: '📊', text: 'Dashboard', href: '/' },
        { id: 'roster', icon: '👥', text: 'Roster', href: '/roster' },
        { id: 'games', icon: '📅', text: 'Schedule', href: '/games' },
        { id: 'admin', icon: '⚙️', text: 'Admin', href: '/admin' },
        { id: 'teamsnap', icon: '🔗', text: 'TeamSnap', href: '/teamsnap' }
    ];

    // Build Nav Links HTML
    const navHtml = links.map(link => {
        const isActive = activePage === link.id ? 'active' : '';
        return `<a href="${link.href}" class="nav-item ${isActive}"><span>${link.icon}</span> ${link.text}</a>`;
    }).join('');

    // User Profile Logic (from local storage)
    let userName = 'User';
    let userRole = 'Member';
    let userInitial = 'U';

    try {
        const token = localStorage.getItem('token');
        if (token) {
            const payload = JSON.parse(atob(token.split('.')[1]));
            userName = payload.sub || payload.username || 'User';
            // Role mapping or simple display
            userRole = (payload.role || 'Member').charAt(0).toUpperCase() + (payload.role || 'Member').slice(1);
            userInitial = userName.charAt(0).toUpperCase();

            // Override Full Name if available in payload? 
            // JWT usually has sub. If we updated backend to include full_name in JWT, we could use it.
            // For now, sub is username or email.
            if (payload.full_name) userName = payload.full_name;
        }
    } catch (e) { }

    sidebar.innerHTML = `
        <div class="logo">⚽ Traloxolcus</div>
        <div class="nav-links">
            ${navHtml}
        </div>
        <div class="user-profile">
            <div class="avatar">${userInitial}</div>
            <div style="display:flex; flex-direction:column;">
                <span style="font-weight:600;">${userName}</span>
                <span style="font-size:0.8rem; color:var(--text-muted);">${userRole}</span>
                ${activePage !== 'login' ? '<span onclick="logout()" style="font-size:0.7rem; color: #ef4444; cursor:pointer; margin-top:2px;">Logout</span>' : ''}
            </div>
        </div>
    `;
}

const LOGIN_PATH = '/login';

function logout() {
    localStorage.removeItem('token');
    window.location.href = LOGIN_PATH;
}
