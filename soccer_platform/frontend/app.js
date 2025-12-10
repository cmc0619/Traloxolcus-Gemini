const API_BASE = '/api';

// Auth Check
const token = localStorage.getItem('token');
if (!token) {
    window.location.href = '/login';
}

async function fetchGames() {
    const grid = document.getElementById('gamesGrid');
    try {
        const res = await fetch(`${API_BASE}/games`);
        const games = await res.json();

        grid.innerHTML = '';

        if (games.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">No matches found. Upload some from the Bench!</p>';
            return;
        }

        games.forEach(game => {
            const card = document.createElement('div');
            card.className = 'game-card';
            card.onclick = () => window.location.href = `/game.html?id=${game.id}`;

            const dateStr = new Date(game.date).toLocaleDateString();
            const statusClass = game.status === 'processed' ? 'status-ready' : 'status-processing';

            card.innerHTML = `
                <div class="card-thumb">
                    <!-- Placeholder or Snapshot if available -->
                    <span>▶️ PREVIEW</span>
                </div>
                <div class="card-info">
                    <h3>${game.id}</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 10px;">Played on ${dateStr}</p>
                    <span class="status-badge ${statusClass}">${game.status}</span>
                </div>
            `;
            grid.appendChild(card);
        });

    } catch (e) {
        console.error(e);
        grid.innerHTML = '<p style="color: red;">Failed to load games.</p>';
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('gamesGrid')) {
        fetchGames();
    }
});
