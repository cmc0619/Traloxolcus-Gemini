# Walkthrough - Phase 4 Features

We have implemented all "Day 1" features: **Email**, **Stats**, **TeamSnap**, **Mobile CSS**, and **Social Export**.

## Features

### 1. Email Notifications

- **Backend**: `fastapi-mail`. Config: `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_SERVER`.
- **Trigger**: Video upload completion.

### 2. Session Statistics

- **Frontend**: **Stats Panel** in `game.html` (PC).
- **Mobile**: Responsive updates; stats panel becomes a scroller on phones.

### 3. TeamSnap Integration

- **Sync**: `POST /api/teams/sync` imports rosters using `TEAMSNAP_TOKEN`.

### 4. Social Media Export (Vertical Video)

- **Backend Service**: `social.py` uses `MoviePy` and `FFmpeg` to generate 9:16 clips.
- **Auto-Follow**: Uses ML ball tracking to pan the crop window dynamically.
- **Trigger**: `GET /api/games/{id}/social` (returns "Processing" -> check back -> returns URL).

## Verification

### Social Export Test

1. Ensure game has been analyzed (needs `ball_coords` in metadata).
   - *Note*: Old games need re-analysis.
2. Trigger generation:

   ```bash
   curl http://localhost:8000/api/games/{id}/social
   ```

3. Wait ~1 minute. Call again. It should return specific URL.
4. Download and view on phone to verify "Anti-Jitter" ball tracking.

### Mobile Test

1. Open Chrome DevTools -> Device Toolbar -> Select "iPhone 12".
2. Verify layout stacks vertically (Video -> Spotlight -> Stats).

## Deployment

Requires rebuild for `ffmpeg` and `git` dependencies:

```bash
docker-compose -f docker-compose.platform.yml build platform
docker-compose -f docker-compose.platform.yml up -d
```
