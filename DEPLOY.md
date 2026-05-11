# Déploiement Synkrone sur VPS — Guide complet

Ce guide suppose un VPS frais sous **Ubuntu 22.04/24.04 LTS** avec accès root ou sudo.

---

## 1. Prérequis sur le VPS

Connecte-toi en SSH puis installe les outils de base :

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git nginx certbot python3-certbot-nginx
```

### Installer Docker + Docker Compose

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Docker Compose (plugin)
docker compose version  # Vérifier l'installation
```

---

## 2. Préparer l'application

### Cloner le repo

```bash
git clone https://github.com/Annonnyx/Synkrone.App.git
cd Synkrone.App
```

### Créer le fichier .env

```bash
cp .env.example .env
nano .env
```

Remplis **obligatoirement** ces variables :

```bash
# Domaine public de ton VPS (avec https)
NEXTAUTH_URL="https://ton-domaine.com"

# Secret aléatoire de 32+ caractères
NEXTAUTH_SECRET="genere-un-secret-avec-openssl-rand-base64-32"

# OAuth Discord (https://discord.com/developers/applications)
DISCORD_CLIENT_ID="ton-client-id"
DISCORD_CLIENT_SECRET="ton-client-secret"

# Base de données (Docker Compose fournit PostgreSQL automatiquement)
DATABASE_URL="postgresql://synkrone:synkrone_pass@db:5432/synkrone?schema=public"
```

> **Générer un NEXTAUTH_SECRET sécurisé :**
> ```bash
> openssl rand -base64 32
> ```
> Copie la sortie dans `NEXTAUTH_SECRET`.

---

## 3. Discord OAuth — Configuration obligatoire

Avant le premier lancement, configure ton application Discord :

1. Va sur [discord.com/developers/applications](https://discord.com/developers/applications)
2. Crée une application (ou ouvre la tienne)
3. Menu **OAuth2** → **General**
4. Dans **Redirects**, ajoute :
   ```
   https://ton-domaine.com/api/auth/callback/discord
   ```
5. Récupère le **Client ID** et le **Client Secret** pour ton `.env`

---

## 4. Lancer avec Docker Compose (recommandé)

Le `docker-compose.yml` du repo lance **PostgreSQL + App** automatiquement.

```bash
docker compose up -d --build
```

Cela construit l'image Node.js et lance 2 containers :
- `synkrone-db` — PostgreSQL 16 avec persistance
- `synkrone-app` — Next.js en production

### Créer les tables + données initiales

```bash
# Appliquer les migrations Prisma
docker compose exec app npx prisma migrate deploy

# Injecter les données de base (commandes, etc.)
docker compose exec app npx prisma db seed
```

### Vérifier que tout tourne

```bash
docker compose ps
docker compose logs -f app
```

L'app écoute sur le port `3000` du container. On va l'exposer via Nginx + HTTPS à l'étape suivante.

---

## 5. HTTPS + Nginx (reverse proxy)

### Configurer Nginx

Crée le fichier de config :

```bash
sudo nano /etc/nginx/sites-available/synkrone
```

Colle ceci (remplace `ton-domaine.com`) :

```nginx
server {
    listen 80;
    server_name ton-domaine.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Active le site :

```bash
sudo ln -s /etc/nginx/sites-available/synkrone /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Obtenir un certificat SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d ton-domaine.com
```

Réponds aux questions. Certbot configure HTTPS et la redirection HTTP → HTTPS automatiquement.

Renouvellement auto activé par défaut. Vérifie avec :

```bash
sudo certbot renew --dry-run
```

---

## 6. Vérification finale

Ouvre `https://ton-domaine.com` dans ton navigateur. Tu devrais voir le site Synkrone.

**Tests rapides :**
- Page d'accueil → OK
- Bouton "Connexion" → redirige vers Discord
- Retour après auth → Dashboard accessible

---

## 7. Mises à jour (prochaines versions)

```bash
cd ~/Synkrone.App  # ou le dossier du repo
git pull origin main

# Rebuild + redémarrer
docker compose up -d --build

# Appliquer les nouvelles migrations si besoin
docker compose exec app npx prisma migrate deploy

# Vérifier les logs
docker compose logs -f app
```

---

## 8. Commandes utiles (Docker)

| Action | Commande |
|---|---|
| Voir les logs | `docker compose logs -f app` |
| Redémarrer l'app | `docker compose restart app` |
| Entrer dans le container | `docker compose exec app sh` |
| Arrêter tout | `docker compose down` |
| Arrêter + supprimer données | `docker compose down -v` |
| Voir l'espace disque | `docker system df` |

---

## 9. Sans Docker (alternative PM2)

Si tu préfères ne pas utiliser Docker :

```bash
# 1. Installer PostgreSQL manuellement
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres createdb synkrone

# 2. Configurer .env avec une connexion locale
# DATABASE_URL="postgresql://postgres:password@localhost:5432/synkrone?schema=public"

# 3. Installer et build
npm install
npx prisma generate
npx prisma migrate deploy
npx prisma db seed
npm run build

# 4. Lancer avec PM2
npm i -g pm2
pm2 start npm --name "synkrone" -- run start
pm2 save
pm2 startup
```

Puis configure Nginx + HTTPS (étape 5) pareil.

---

## Checklist pré-déploiement

- [ ] VPS Ubuntu avec Docker & Docker Compose installés
- [ ] Repo cloné sur le VPS
- [ ] Fichier `.env` créé avec toutes les variables remplies
- [ ] Discord OAuth configuré avec la bonne URL de callback (`https://ton-domaine.com/api/auth/callback/discord`)
- [ ] `docker compose up -d --build` lancé sans erreur
- [ ] Migrations + seed appliqués
- [ ] Nginx configuré avec ton domaine
- [ ] Certificat SSL Let's Encrypt obtenu
- [ ] Site accessible en HTTPS
