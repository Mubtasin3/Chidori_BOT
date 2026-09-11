# ---- Build the BgUtils PO-token provider ----
FROM node:26-bookworm-slim AS bgutil-build

WORKDIR /provider
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch 2.0.0 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git .
RUN npm ci --omit=dev --no-audit --no-fund
RUN npm ci --no-audit --no-fund
RUN npx tsc

# ---- Chidori bot ----
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DENO_DIR=/root/.cache/deno

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Current yt-dlp stable + dependencies are installed above.
# Copy the BgUtils provider server into this same container.
COPY --from=bgutil-build /provider/build /opt/bgutil/build
COPY --from=bgutil-build /provider/node_modules /opt/bgutil/node_modules
COPY --from=bgutil-build /provider/package.json /opt/bgutil/package.json

COPY . .

# Start the local PO-token server, then the Discord bot.
CMD ["sh", "-c", "node /opt/bgutil/build/main.js --host 127.0.0.1 & exec python bot.py"]
