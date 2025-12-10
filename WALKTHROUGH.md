# Walkthrough - Phase 4 Features

We have implemented three "Day 1" features: **Email Notifications**, **Session Statistics**, and **TeamSnap Integration**.

## Features

### 1. Email Notifications

- **Backend**: Integrated `fastapi-mail`.
- **Trigger**: Sends email to Admins/Coaches when video uploads.
- **Config**: Env vars `MAIL_USERNAME`, `MAIL_PASSWORD`, etc.

### 2. Session Statistics

- **Frontend**: **Stats Panel** in `game.html`.
- **Metrics**: Ball Active %, Avg Players, Total Events.

### 3. TeamSnap Integration

- **Backend**: Integrated `TeamSnappier` library (installed via git).
- **Service**: `soccer_platform/services/teamsnap.py` fetches teams/rosters.
- **Endpoint**: `POST /api/teams/sync` imports players as Users (`role=player`).
- **Config**: Env var `TEAMSNAP_TOKEN`.

## Verification

### Email Test

Set `MAIL_` env vars and upload a video. Check inbox.

### Stats Test

View any processed game. Check left-side panel.

### TeamSnap Test

1. Set `TEAMSNAP_TOKEN` in environment.
2. Run database sync manually:

   ```bash
   # Use curl or Postman
   curl -X POST http://localhost:8000/api/teams/sync \
     -H "Authorization: Bearer <ADMIN_TOKEN>"
   ```

3. Check database for new users:

   ```bash
   docker exec -it soccer_platform psql -U soccer soccer_platform -c "SELECT username, role FROM users;"
   ```

## Deployment

Rebuild connecting to GitHub for the new dependency:

```bash
docker-compose -f docker-compose.platform.yml build platform
docker-compose -f docker-compose.platform.yml up -d
```
