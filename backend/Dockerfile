FROM python:3.12-slim

# leaner Python runtime + no .pyc files + unbuffered logs (good for Docker)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# the app reads the site from two levels up, so we copy the whole repo
WORKDIR /app

# install OS deps:
#   - ffmpeg: re-encode the demo video to ~4 MB at build time (see below)
#   - curl/ffmpeg stripped in the same layer; --no-install-recommends keeps it small
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# install deps first for better layer caching
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

# copy backend + the static site + admin panel + deep-dive pages
COPY backend/ ./backend/
COPY index.html impressum.html datenschutz.html og.png ./
COPY vids/ ./vids/
COPY new_image/ ./new_image/
COPY admin/ ./admin/
COPY p/ ./p/
# uploads/ is created at runtime if missing, but seeded here so it persists
RUN mkdir -p uploads backend/data

# ── re-encode the demo video to ~4 MB (480p, H.264, CRF 28) ──────────
# The committed file is high-bitrate (~25 MB). On a 1 GB RAM / 0.125 OCPU
# VM (Oracle E2.1 Micro) that's brutal on egress. We downscale to 854x480
# (plenty for a ~500px-wide card) and re-encode in place. No-op if the
# file is already small or missing.
RUN if [ -f vids/video.mp4 ] && [ "$(stat -c%s vids/video.mp4)" -gt 8000000 ]; then \
      ffmpeg -y -i vids/video.mp4 \
        -vf "scale='min(854,iw)':-2" -c:v libx264 -preset veryslow -crf 28 \
        -c:a aac -b:a 96k -movflags +faststart \
        vids/video_small.mp4 \
      && mv vids/video_small.mp4 vids/video.mp4; \
    else echo "video already small or missing — skipping re-encode"; fi

WORKDIR /app/backend

# persist the sqlite db outside the container
VOLUME ["/app/backend/data"]

EXPOSE 8000
RUN chown -R app:app /app
USER app

# single worker — the E2.1 Micro has 0.125 OCPU, multiple workers just thrash.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
