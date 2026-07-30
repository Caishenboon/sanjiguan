FROM node:22.17.1-alpine3.22 AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/pnpm-lock.yaml apps/web/pnpm-workspace.yaml ./
COPY packages/sanji-ui /packages/sanji-ui
RUN corepack enable && corepack prepare pnpm@11.9.0 --activate && pnpm install --frozen-lockfile

FROM node:22.17.1-alpine3.22 AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./
COPY packages/sanji-ui /packages/sanji-ui
ENV NEXT_TELEMETRY_DISABLED=1
RUN corepack enable && corepack prepare pnpm@11.9.0 --activate && pnpm build

FROM node:22.17.1-alpine3.22
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
RUN addgroup -S sanji && adduser -S sanji -G sanji
COPY --from=build --chown=sanji:sanji /app ./
USER sanji
EXPOSE 3000
CMD ["node_modules/.bin/next", "start", "-H", "0.0.0.0", "-p", "3000"]
