# Use Node.js v20 as the base image
FROM node:20-slim

WORKDIR /app

RUN npm install -g pnpm@8.9.0

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml setup.sh ./
COPY apps/ ./apps/
COPY packages/ ./packages/

RUN pnpm run setup

WORKDIR /app/apps/web

EXPOSE 3000

CMD ["pnpm", "-w", "run", "dev"]
