# ─────────────────────────────────────────────────────────────────────────────
# Frontend Dockerfile — Node 20 slim (Vite dev server)
# ─────────────────────────────────────────────────────────────────────────────

FROM node:20-slim

WORKDIR /app

# Install deps first (layer cache)
COPY package.json package-lock.json* ./
RUN npm install

# Copy source (volume-mounted in dev, so mostly for prod builds)
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]