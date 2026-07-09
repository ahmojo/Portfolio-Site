# Portfolio Site

Source code for my personal portfolio site: <https://ahmet-portfolio.ch>.

The project contains:

- a static HTML/CSS/JavaScript frontend;
- a FastAPI backend with SQLite persistence;
- an admin panel for editing site content;
- Docker Compose and Render deployment configuration.

## What is intentionally not included

This public repository excludes private or runtime-only files:

- real `.env` files;
- SQLite databases and generated session secrets;
- uploaded files;
- Python caches and local virtual environments;
- large/private media files such as demo videos and certificate images;
- VM-specific deployment notes and scripts.

Placeholder folders are kept for media paths so Docker builds still have the
expected directory structure.

## Local development

```bash
cd backend
cp .env.example .env
# edit .env values before any public deployment
docker compose up --build
```

For more backend details, see [backend/README.md](backend/README.md).
