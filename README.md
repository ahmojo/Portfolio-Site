# Portfolio Site

Architecture of [ahmet-portfolio.ch](https://ahmet-portfolio.ch):

```text
Browser
   |
Cloudflare (DNS, HTTPS, CDN, Bot Fight Mode, Turnstile)
   |
Oracle Cloud VM
   |
Docker Compose
   |
FastAPI
   |-- static portfolio
   |-- admin panel
   |-- content, project, stats and uptime APIs
   `-- SQLite

FastAPI --> GitHub API
FastAPI --> UptimeRobot API
FastAPI --> Cloudflare Turnstile Siteverify
```

The public frontend and admin panel use the FastAPI API on the same origin.
SQLite stores editable content and privacy-reduced, Turnstile-confirmed
first-party analytics on the persistent VM volume.

Strict analytics setup and verification are documented in
[`docs/ANALYTICS_STRICT_MODE.md`](docs/ANALYTICS_STRICT_MODE.md).
