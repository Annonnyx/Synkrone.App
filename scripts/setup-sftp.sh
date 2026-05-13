#!/bin/bash
# ============================================================
# Setup SFTP pour les serveurs Minecraft Synkrone
# À exécuter EN ROOT sur le VPS (hors Docker)
# ============================================================

set -e

SFTP_GROUP="sftponly"
MC_PATH="/mc"
SSH_CONFIG="/etc/ssh/sshd_config"

echo "=== Setup SFTP pour Minecraft ==="

# 1. Créer le groupe sftp s'il n'existe pas
if ! getent group "$SFTP_GROUP" > /dev/null 2>&1; then
    groupadd "$SFTP_GROUP"
    echo "Groupe '$SFTP_GROUP' créé"
else
    echo "Groupe '$SFTP_GROUP' existe déjà"
fi

# 2. Sauvegarder sshd_config
cp "$SSH_CONFIG" "$SSH_CONFIG.bak.$(date +%s)"

# 3. Ajouter la config SFTP chroot si pas déjà présente
if ! grep -q "Match Group $SFTP_GROUP" "$SSH_CONFIG"; then
    cat >> "$SSH_CONFIG" << 'EOF'

# Synkrone SFTP chroot for Minecraft servers
Match Group sftponly
    ForceCommand internal-sftp
    ChrootDirectory %h
    AllowTcpForwarding no
    X11Forwarding no
    PasswordAuthentication yes
EOF
    echo "Config SSH ajoutée"
else
    echo "Config SSH déjà présente"
fi

# 4. Redémarrer SSH
if command -v systemctl &> /dev/null; then
    systemctl restart sshd || systemctl restart ssh
elif command -v service &> /dev/null; then
    service ssh restart || service sshd restart
fi
echo "SSH redémarré"

# 5. Créer les utilisateurs depuis le JSON
echo "=== Sync des utilisateurs SFTP ==="

USERS_FILE="$MC_PATH/sftp-users.json"
if [ ! -f "$USERS_FILE" ]; then
    echo "Aucun fichier $USERS_FILE — aucun user à créer pour l'instant"
    exit 0
fi

for row in $(cat "$USERS_FILE" | jq -c '.[]'); do
    USER=$(echo "$row" | jq -r '.user')
    PASS=$(echo "$row" | jq -r '.password')
    DIR=$(echo "$row" | jq -r '.dir')

    if id "$USER" &>/dev/null; then
        echo "User '$USER' existe déjà — skip"
        continue
    fi

    # Créer user sans shell, sans home auto, dans le groupe sftponly
    useradd -g "$SFTP_GROUP" -s /sbin/nologin "$USER"
    echo "$USER:$PASS" | chpasswd

    # Créer le chroot dir (doit être owned par root)
    mkdir -p "$DIR"
    chown root:root "$DIR"
    chmod 755 "$DIR"

    # Donner les droits d'écriture dans le dossier au user
    chown "$USER:$SFTP_GROUP" "$DIR"
    chmod 775 "$DIR"

    echo "User '$USER' créé avec chroot $DIR"
done

echo "=== SFTP prêt ==="
echo "Port: 22"
echo "Host: $(hostname -I | awk '{print $1}')"
