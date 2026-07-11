# Portfolio Backend

FastAPI + SQLite backend for the portfolio site. Runs **locally**.

## Features

| Endpoint | Method | What it does |
|---|---|---|
| `/api/health` | GET | liveness check |
| `/api/content` | GET | public - the editable site content (hero, about, skills, projects, learning, theme) |
| `/api/content` | PUT | admin-only - replace the content blob (drives the whole site) |
| `/api/auth/login` | POST | login `{password}` → sets session cookie |
| `/api/auth/logout` | POST | clear session |
| `/api/auth/me` | GET | `{authenticated}` for the admin UI |
| `/api/projects` | GET | live GitHub stars / language / last-update per repo (cached 10 min) |
| `/api/stats` | GET | GitHub contributions, streaks + yearly heatmap |
| `/api/uptime` | GET | public self-hosted status; optionally enriches from UptimeRobot server-side |
| `/api/guestbook` | GET | recent messages |
| `/api/guestbook` | POST | add a message `{author, message}` |
| `/api/now` | GET | current "what I'm doing" status |
| `/api/now` | PUT | update status `{status, detail, token?}` |
| `/api/contact` | POST | store + optionally email a contact message `{name, email, message}` |
| `/api/docs` | - | interactive Swagger UI |

The app **also serves the static site** (index.html, vids/, new_image/) at `/`,
and the **admin panel** at `/admin`, so once it's running you open
**http://localhost:8000/** (site) or **http://localhost:8000/admin** (panel)
and the frontend talks to the API on the same origin - no CORS setup needed.

If you open `index.html` directly (file://) the frontend detects the missing
API and the form/badges fall back to placeholders without breaking.

## Quick start

### Option A - Docker (recommended)

```bash
cd backend
cp .env.example .env        # edit secrets before production Docker
docker compose up --build
# → http://localhost:8000
```

The SQLite db is persisted in `./data/portfolio.db` (a mounted volume).

### Option B - uvicorn directly

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate        # Windows (Git Bash)
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
```

## Configuration

All settings via env vars (prefix `PORTFOLIO_`), see `.env.example`.

- `PORTFOLIO_GITHUB_USER` / `PORTFOLIO_PROJECTS` - repos shown on the site
- `PORTFOLIO_GITHUB_TOKEN` - optional PAT, raises rate limit 60→5000/h
- `PORTFOLIO_GUESTBOOK_RATE` / `PORTFOLIO_CONTACT_RATE` - per-IP/min limits
- `PORTFOLIO_NOW_TOKEN` - required in production; protects `PUT /api/now`
- `PORTFOLIO_ADMIN_PASSWORD` - password for the `/admin` panel; production refuses `admin`
- `PORTFOLIO_SESSION_SECRET` - cookie signing secret; production requires a real random value
- `PORTFOLIO_SESSION_TTL_HOURS` - login session lifetime (default 12h)
- `PORTFOLIO_SMTP_HOST` (+ USER/PASS/TO) - enables contact email forwarding

- `PORTFOLIO_UPTIME_ROBOT_API_KEY` / `PORTFOLIO_UPTIME_ROBOT_MONITOR_ID` - optional UptimeRobot status badge; keep the key server-side
- `PORTFOLIO_UPTIME_ROBOT_STATUS_PAGE_URL` - optional public status page link

## Admin panel (edit the whole site without touching code)

Open **http://localhost:8000/admin** and log in with `PORTFOLIO_ADMIN_PASSWORD`.
Production Docker will not start with the placeholder/default password.

The panel lets you edit, live, with a save button:

- **Hero** - name, tagline, and the rotating typing phrases
- **About** - paragraphs, the 4 stat tiles, and the "currently building" status
- **Skills** - rows of languages / tools / interests
- **Projects** - add / remove / reorder projects (title, description, stack, GitHub
  repo, badges, featured flag + media)
- **Learning** - courses & projects (link type or certificate-preview type)
- **Theme** - background / accent / text colors via pickers + particle count slider

Changes are saved to SQLite and served to the public site via `/api/content`.
The public page fetches that blob on load and rebuilds itself; if the API is
down it keeps showing the hardcoded fallback, so the site never breaks.

Content is also editable directly over the API:

```bash
# read current content
curl localhost:8000/api/content

# login first (captures the session cookie)
curl -c cj.txt -X POST localhost:8000/api/auth/login \
  -H "Content-Type: application/json" -d '{"password":"admin"}'

# then PUT the full content blob
curl -b cj.txt -X PUT localhost:8000/api/content \
  -H "Content-Type: application/json" -d '{ ...full content json... }'
```

## Updating "now"

```bash
curl -X PUT localhost:8000/api/now \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"learning Docker"}'
```

## Using the API from the static site directly

When opening `index.html` as a file (not via the backend), set the API origin
once in the browser console:

```js
localStorage.setItem('apiBase', 'http://localhost:8000')
```

## Project layout

```
backend/
├── app/
│   ├── main.py          # FastAPI app + static site + /admin serving
│   ├── config.py        # settings (env-driven)
│   ├── db.py            # sqlite schema + content blob + helpers
│   ├── security.py      # HMAC session tokens + auth endpoints
│   ├── github.py        # cached GitHub repo client
│   ├── contributions.py # GitHub calendar scraper (stats/streaks)
│   ├── models.py        # pydantic schemas (incl. SiteContent)
│   └── routers/         # auth, content, contact, guestbook, now, projects, stats
├── data/                # sqlite db + session secret (gitignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
admin/
└── admin.html           # the /admin control panel (self-contained)
```
