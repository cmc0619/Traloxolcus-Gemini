const API_BASE = '/api';

// Auth Check
const token = localStorage.getItem('token');
if (!token) {
    window.location.href = '/login';
} else {
    // Parse Token
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const userSpan = document.getElementById('userName');
        const avatar = document.getElementById('userAvatar');

        if (userSpan) userSpan.innerText = payload.sub || 'User';
        if (avatar) avatar.innerText = (payload.sub || 'U')[0].toUpperCase();

        // Show Admin Link
        if (payload.role === 'admin') {
            const link = document.getElementById('adminLink');
            if (link) link.style.display = 'block';

            // Also show TeamSnap link
            const tsLink = document.getElementById('tsLink');
            if (tsLink) tsLink.style.display = 'block';
        }
    } catch (e) {
        console.error("Invalid token", e);
    }
}

// Global data
let allGames = [];
let allTeams = [];
let allUsers = []; // Track users for player filter

async function fetchTeams() {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
        const res = await fetch(`${API_BASE}/teams`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            allTeams = await res.json();

            // Populate Team Filter
            const teamSelect = document.getElementById('filterTeam');
            if (teamSelect) {
                const current = teamSelect.value;
                // Maintain 'All'
                let opts = '<option value="all">All Teams</option>';
                allTeams.forEach(t => {
                    opts += `<option value="${t.id}">${t.name}</option>`;
                });
                teamSelect.innerHTML = opts;
                teamSelect.value = current;
                teamSelect.onchange = applyFilters;
            }

            // If games are already loaded, re-render
            if (allGames.length > 0) updateGrid(allGames);
        }
    } catch (e) { console.error("Teams Fetch Error", e); }
}

async function fetchStats() {
    const token = localStorage.getItem('token');
    if (!token) return;

    // 1. Fetch Users
    try {
        const res = await fetch(`${API_BASE}/users`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const users = await res.json();
            const el = document.getElementById('statPlayers');
            if (el) el.innerText = users.filter(u => u.role === 'player').length;

            allUsers = users;
            // Populate Player Filter
            const playerSelect = document.getElementById('filterPlayer');
            if (playerSelect) {
                const current = playerSelect.value;
                let opts = '<option value="all">All Players</option>';
                // Sorting for niceness
                users
                    .filter(u => u.role === 'player')
                    .sort((a, b) => (a.full_name || a.username).localeCompare(b.full_name || b.username))
                    .forEach(u => {
                        opts += `<option value="${u.id}">${u.full_name || u.username}</option>`;
                    });
                playerSelect.innerHTML = opts;
                playerSelect.value = current;
                playerSelect.onchange = applyFilters;
            }
        }
    } catch (e) {
        console.error("Stats User Error", e);
        if (e.message.includes('401') || (e.response && e.response.status === 401)) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    }
}

async function fetchGames() {
    const grid = document.getElementById('gamesGrid');
    const freshToken = localStorage.getItem('token');
    if (!grid) return;

    try {
        const res = await fetch(`${API_BASE}/games`, {
            headers: { 'Authorization': `Bearer ${freshToken}` }
        });
        const games = await res.json();
        allGames = games; // Store for search

        updateGrid(games);

        // Update Stats
        const statGames = document.getElementById('statGames');
        const statVideos = document.getElementById('statVideos');
        if (statGames) statGames.innerText = games.length;
        if (statVideos) statVideos.innerText = games.filter(g => g.video_path).length;

    } catch (e) {
        console.error(e);
        grid.innerHTML = '<p style="color: red;">Failed to load games.</p>';
        if (e.message.includes('401') || (e.response && e.response.status === 401)) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    }
}

function updateGrid(games) {
    const grid = document.getElementById('gamesGrid');
    grid.innerHTML = '';

    if (games.length === 0) {
        grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">No matches found.</p>';
        return;
    }

    games.forEach(game => {
        const card = document.createElement('div');
        card.className = 'game-card';
        card.onclick = () => window.location.href = `/game?id=${game.id}`;

        const dateStr = new Date(game.date).toLocaleDateString();
        const statusClass = game.status === 'processed' ? 'status-ready' : 'status-processing';

        // Resolve Team Name
        const team = allTeams.find(t => t.id === game.team_id);
        const teamName = team ? team.name : 'My Team';

        card.innerHTML = `
            <div class="card-thumb">
                <!-- Placeholder or Snapshot if available -->
                <span>▶️ PREVIEW</span>
            </div>
            <div class="card-info">
                <h3>${teamName} vs ${game.opponent || 'Opponent'}</h3>
                <p style="color: var(--text-muted); margin-bottom: 10px;">${dateStr} ${game.location ? 'at ' + game.location : ''}</p>
                <span class="status-badge ${statusClass}">${game.status}</span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function setupSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');

    if (!searchBtn || !searchInput) return;

    if (!searchBtn || !searchInput) return;

    searchBtn.onclick = applyFilters;
    searchInput.onkeyup = (e) => {
        if (e.key === 'Enter') applyFilters();
    };
}

function applyFilters() {
    const teamId = document.getElementById('filterTeam') ? document.getElementById('filterTeam').value : 'all';
    const playerId = document.getElementById('filterPlayer') ? document.getElementById('filterPlayer').value : 'all';
    const query = document.getElementById('searchInput') ? document.getElementById('searchInput').value.toLowerCase() : '';

    // Determine player's team if playerId is selected
    let playerTeamIds = [];
    if (playerId !== 'all') {
        const p = allUsers.find(u => u.id == playerId);
        if (p && p.teams) {
            playerTeamIds = p.teams.map(t => typeof t === 'object' ? (t.team_id || t.id) : t);
            // Note: API /users returns eager loaded teams usually with shape { team: {...}, team_id, ... } or just list of teams?
            // Let's rely on how admin_users.html saw u.teams -> array of { team: {id, ...} }
            // Wait, fetchStats called /users endpoint. Does /users endpoint return full team details?
            // services/users.py endpoint for /users: "response_model=List[UserSchema]"
            // UserSchema includes `teams: List[UserTeamSchema] = []`
            // UserTeamSchema has `team_id` and `team: Optional[TeamSchema]`
            // So yes.
            playerTeamIds = p.teams.map(ut => ut.team_id);
        }
    }

    const filtered = allGames.filter(g => {
        // 1. Text Search
        const matchesText = g.id.toLowerCase().includes(query) ||
            (g.opponent && g.opponent.toLowerCase().includes(query)) ||
            (g.location && g.location.toLowerCase().includes(query));

        // 2. Team Filter
        const matchesTeam = (teamId === 'all') || (g.team_id === teamId);

        // 3. Player Filter (Show games where player's team matches game's team)
        const matchesPlayer = (playerId === 'all') || (playerTeamIds.includes(g.team_id));

        return matchesText && matchesTeam && matchesPlayer;
    });

    updateGrid(filtered);
}

async function checkTeamSnap() {
    // Check settings for token presence
    const el = document.getElementById('statTeamSnap');
    if (!el) return;

    try {
        const res = await fetch(`${API_BASE}/settings`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
        if (res.ok) {
            const settings = await res.json();
            const hasToken = settings.some(s => s.key === 'TEAMSNAP_TOKEN' || s.key === 'TEAMSNAP_CLIENT_ID');
            // Better check: If we have a client ID, we are configured. If we have token, we are active.
            // Since API doesn't return secret usually? 
            // Let's assume if CLIENT_ID is there, it's 'Configured', if TOKEN is there 'Active'.
            // Actually settings endpoint returns everything.

            const token = settings.find(s => s.key === 'TEAMSNAP_TOKEN')?.value;
            const clientId = settings.find(s => s.key === 'TEAMSNAP_CLIENT_ID')?.value;

            if (token) {
                el.innerText = "Active";
                el.style.color = "var(--primary)";
            } else if (clientId) {
                el.innerText = "Setup";
                el.style.color = "#d97706"; // amber
            } else {
                el.innerText = "Inactive";
                el.style.color = "var(--text-muted)";
            }
        }
    } catch (e) {
        el.innerText = "Error";
        if (e.message.includes('401') || (e.response && e.response.status === 401)) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    fetchTeams(); // Start fetching teams
    fetchStats();
    fetchGames();
    checkTeamSnap();
    setupSearch();
});
