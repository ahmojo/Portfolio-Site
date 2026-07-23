# Portfolio Site

Architecture of [ahmet-portfolio.ch](https://ahmet-portfolio.ch):

```text
Browser
   |
Cloudflare (DNS, HTTPS, CDN)
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
```

The public frontend and admin panel use the FastAPI API on the same origin.
SQLite stores editable content and privacy-reduced first-party analytics on the
persistent VM volume.
