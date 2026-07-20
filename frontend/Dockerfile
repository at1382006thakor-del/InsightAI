# Stage 1: Install dependencies
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci && npm install --no-save @tailwindcss/oxide-linux-x64-musl

# Stage 2: Build Next.js
FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 3: Run production Next.js server
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "start"]
