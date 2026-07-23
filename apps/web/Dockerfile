FROM node:22-alpine AS deps
WORKDIR /app
COPY apps/web/package.json ./
RUN npm install

FROM node:22-alpine
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./
ENV NEXT_TELEMETRY_DISABLED=1
EXPOSE 3000
CMD ["npm", "run", "dev"]
