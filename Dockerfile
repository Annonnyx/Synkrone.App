FROM node:20-alpine AS base

# Dépendances système: openssl (Prisma), bash (terminal), openjdk (Minecraft), python3 (bots)
RUN apk add --no-cache openssl bash openjdk17-jre python3 py3-pip

# PM2 global pour gérer les processus bots/minecraft
RUN npm install -g pm2

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
