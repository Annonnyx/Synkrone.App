# Installation du cron de billing (VPS)

## 1. Créer le dossier de config

```bash
sudo mkdir -p /etc/synkrone
sudo sh -c 'echo "CRON_SECRET=ton_secret_ici" > /etc/synkrone/cron.env'
```

## 2. Copier les fichiers systemd

```bash
sudo cp synkrone-billing.service /etc/systemd/system/
sudo cp synkrone-billing.timer /etc/systemd/system/
```

## 3. Activer et démarrer

```bash
sudo systemctl daemon-reload
sudo systemctl enable synkrone-billing.timer
sudo systemctl start synkrone-billing.timer
```

## 4. Vérifier

```bash
systemctl status synkrone-billing.timer
journalctl -u synkrone-billing.service --since "1 hour ago"
```

Le cron tourne **toutes les heures** et débite automatiquement les Kr des utilisateurs pour leurs bots et serveurs Minecraft actifs.
