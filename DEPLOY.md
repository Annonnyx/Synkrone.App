# Déploiement Synkrone — Guide de mise en production

## Prérequis

- Node.js 20+
- PostgreSQL (base de données)
- Un compte Discord (OAuth2 app configurée)
- Un hébergeur supportant Node.js (VPS / PaaS)

## 1. Variables d'environnement

Créer un fichier `.env` à la racine (`.env.local` en dev) :

```bash
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/synkrone?schema=public"

# NextAuth / Discord OAuth
NEXTAUTH_URL="https://ton-domaine.com"
NEXTAUTH_SECRET="ta-secret-key-aleatoire-min-32-caracteres"
DISCORD_CLIENT_ID="ton-discord-client-id"
DISCORD_CLIENT_SECRET="ton-discord-client-secret"

# Optionnel
SMTP_HOST=""
SMTP_PORT=""
SMTP_USER=""
SMTP_PASS=""
```

> **IMPORTANT** : Ne jamais commiter `.env*` — ils sont déjà dans `.gitignore`.

## 2. Installation & Build

```bash
# 1. Cloner le repo
git clone https://github.com/Annonnyx/Synkrone.App.git
cd Synkrone.App

# 2. Installer les dépendances
npm install

# 3. Générer le client Prisma
npx prisma generate

# 4. Push le schema en base
npx prisma db push

# 5. Build (obligatoire avant prod)
npm run build
```

## 3. Lancer en production

```bash
npm run start
```

Le serveur écoute par défaut sur le port défini par `PORT` ou `3000`.

## 4. Déploiement Vercel (recommandé pour le front)

```bash
npm i -g vercel
vercel --prod
```

**Avec base de données Vercel Postgres :**
1. Créer un projet sur [vercel.com](https://vercel.com)
2. Ajouter l'intégration "Postgres"
3. Connecter la variable `DATABASE_URL` automatiquement
4. Ajouter manuellement `NEXTAUTH_SECRET`, `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`

## 5. Déploiement VPS

### Option A — Docker Compose (recommandé)

Un `docker-compose.yml` et un `Dockerfile` sont déjà dans le repo.

```bash
# 1. Configurer les variables
cp .env.example .env
nano .env   # Remplir DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, NEXTAUTH_SECRET

# 2. Lancer (PostgreSQL + App)
docker compose up -d --build

# 3. Push le schema Prisma
docker compose exec app npx prisma db push
```

L'app sera disponible sur `http://localhost:3000`.

### Option B — Docker seul

```bash
docker build -t synkrone .
docker run -p 3000:3000 --env-file .env synkrone
```

### Option C — Sans Docker (PM2)

```bash
# Prérequis : PostgreSQL installé et accessible
npm install
npx prisma generate
npx prisma db push
npm run build

# PM2
npm i -g pm2
pm2 start npm --name "synkrone" -- run start
pm2 save
pm2 startup
```

## 6. Post-déploiement

- **Configurer l'URL de callback Discord** : `https://ton-domaine.com/api/auth/callback/discord`
- **Vérifier la connexion DB** via le dashboard
- **Activer les webhooks** si nécessaire

## 7. Mises à jour

```bash
git pull origin main
npm install
npx prisma generate
npm run build
# Redémarrer le service (PM2 : pm2 restart synkrone)
```

## Checklist pré-déploiement

- [ ] `npm run build` passe sans erreur
- [ ] Variables d'environnement configurées
- [ ] Base de données accessible
- [ ] OAuth Discord configuré avec la bonne URL de callback
- [ ] HTTPS activé (Let's Encrypt / Vercel / Cloudflare)
