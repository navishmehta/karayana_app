# Customer website (Expo web build) served by Caddy, which also proxies /api and serves /media.
# Build context: the repository root.
FROM node:22-alpine AS build
WORKDIR /app
COPY mobile/package.json mobile/package-lock.json ./
RUN npm ci
COPY mobile/ ./
ARG EXPO_PUBLIC_API_URL
ENV EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL}
RUN npx expo export --platform web --output-dir /web

FROM caddy:2.10-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /web /srv/web
