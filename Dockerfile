FROM node:20-alpine AS base

# Dépendances système pour Prisma (openssl)
RUN apk add --no-cache openssl bash

WORKDIR /app

# Dépendances
COPY package*.json ./
RUN npm ci

# Prisma
COPY prisma ./prisma
RUN npx prisma generate

# Code source + build
COPY . .
RUN npm run build

# Runtime
ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

CMD ["npm", "run", "start"]
