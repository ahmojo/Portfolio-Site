# Portfolio Site

Source code for my personal portfolio site: <https://ahmet-portfolio.ch>.

The project contains:

- a static HTML/CSS/JavaScript frontend;
- a FastAPI backend with SQLite persistence;
- an admin panel for editing site content;
- Docker deployment configuration for the self-hosted FastAPI app.

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
