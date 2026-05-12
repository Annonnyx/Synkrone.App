import re
import discord
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput
import json
from pathlib import Path
from typing import Dict, List
import os

# --- IMPORT CONFIG MANAGER ---
# Importation du config_manager comme dans prefix.py
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# --- FONCTION UTILITAIRE POUR LES EMBEDS ---
def create_embed(guild, user, bot, title, description, color=None, **kwargs):
    """
    Crée un embed en utilisant le config_manager si disponible, sinon utilise un format par défaut
    """
    if config_manager:
        try:
            embed = config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=bot,
                title=title,
                description=description,
                target_id=guild.id if guild else None,
                force_global=not bool(guild)
            )
            if color is not None:
                embed.color = color
            return embed
        except Exception as e:
            print(f"❌ Erreur avec config_manager: {str(e)}")
    # Fallback si le config_manager n'est pas disponible
    embed = discord.Embed(
        title=title,
        description=description,
        color=color if color is not None else 0x660099
    )
    if hasattr(bot, 'user') and hasattr(bot.user, 'avatar'):
        embed.set_thumbnail(url=bot.user.display_avatar.url)
    return embed

# ...existing code...

# === DÉFINITION DE LA CLASSE PRINCIPALE DU COG ===

# ...existing code...

# === FONCTIONS UTILITAIRES EN DEHORS DE LA CLASSE ===

def check_custom_permission(bot, ctx, command_name: str) -> tuple[bool, str]:
    """
    Vérifie si l'utilisateur a la permission d'exécuter la commande demandée selon le système custom.
    Retourne (True, None) si autorisé, sinon (False, message d'erreur).
    Ajoute des prints de debug détaillés.
    """
    print(f"[PERM DEBUG] Commande demandée : {command_name}")
    print(f"[PERM DEBUG] Utilisateur : {ctx.author} (ID: {ctx.author.id}) sur serveur {ctx.guild} (ID: {ctx.guild.id})")
    perm_cog = bot.get_cog('Perm')
    if not perm_cog or not hasattr(perm_cog, 'is_enabled') or not callable(perm_cog.is_enabled):
        print("[PERM DEBUG] Système custom non actif (cog absent ou non conforme)")
        return True, None  # Pas de système custom actif
    if not perm_cog.is_enabled(ctx.guild.id):
        print("[PERM DEBUG] Système custom désactivé pour ce serveur")
        return True, None
    # Owner toujours autorisé
    if ctx.author.id == ctx.guild.owner_id:
        print("[PERM DEBUG] Owner du serveur, accès autorisé")
        return True, None
    # Chercher la permission liée à la commande
    # (Bloc dupliqué supprimé)
    permissions_data = perm_cog.load_server_permissions(ctx.guild.id)
    print(f"[PERM DEBUG] Permissions chargées : {permissions_data}")
    perm_number = None
    for i in range(1, 7):
        perm_data = permissions_data.get(str(i), {})
        cmds = perm_data.get("commandes", "Aucune")
        # Recherche stricte du nom de commande
        if cmds != "Aucune":
            # Supporte séparateur | ou ,
            cmd_list = re.split(r'[|,]', cmds)
            cmd_list = [cmd.strip() for cmd in cmd_list if cmd.strip()]
            print(f"[PERM DEBUG] Permission {i} : commandes = {cmd_list}")
            if command_name in cmd_list:
                perm_number = str(i)
                print(f"[PERM DEBUG] Commande '{command_name}' trouvée dans permission {perm_number}")
                break
    if not perm_number:
        print(f"[PERM DEBUG] Commande '{command_name}' non trouvée dans les permissions")
        return False, f"❌ La commande `{command_name}` n'est liée à aucune permission, accès refusé."
    # Vérifier l'accès utilisateur/rôle
    has_perm = perm_cog.has_permission(ctx.guild.id, ctx.author.id, command_name, ctx.author.roles)
    print(f"[PERM DEBUG] Résultat has_permission pour user {ctx.author.id} sur '{command_name}' : {has_perm}")
    if not has_perm:
        print(f"[PERM DEBUG] Accès refusé à l'utilisateur {ctx.author.id} pour la permission {perm_number}")
        return False, f"❌ Vous devez être explicitement listé dans la Permission {perm_number} pour utiliser la commande `{command_name}`."
    print(f"[PERM DEBUG] Accès autorisé à l'utilisateur {ctx.author.id} pour la permission {perm_number}")
    return True, None
import discord
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput
import json
from pathlib import Path
from typing import Dict, List
import os

# --- IMPORT CONFIG MANAGER ---
# Importation du config_manager comme dans prefix.py
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# --- FONCTION UTILITAIRE POUR LES EMBEDS ---
def create_embed(guild, user, bot, title, description, color=None, **kwargs):
    """
    Crée un embed en utilisant le config_manager si disponible, sinon utilise un format par défaut
    """
    if config_manager:
        try:
            embed = config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=bot,
                title=title,
                description=description,
                target_id=guild.id if guild else None,
                force_global=not bool(guild)
            )
            if color is not None:
                embed.color = color
            return embed
        except Exception as e:
            print(f"❌ Erreur avec config_manager: {str(e)}")
    
    # Fallback si le config_manager n'est pas disponible
    embed = discord.Embed(
        title=title,
        description=description,
        color=color if color is not None else 0x660099
    )
    
    if hasattr(bot, 'user') and hasattr(bot.user, 'avatar'):
        embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    return embed

# Constantes
MAX_ROLES = 3
MAX_USERS = 3
TOTAL_PERMISSIONS = 6

# Hiérarchie des permissions : chaque permission possède celles d'en dessous
PERMISSION_HIERARCHY = {
    "1": ["1", "2", "3", "4", "5", "6"],  # Permission 1 possède tout
    "2": ["2", "3", "4", "5", "6"],      # Permission 2 possède 2,3,4,5,6
    "3": ["3", "4", "5", "6"],            # Permission 3 possède 3,4,5,6
    "4": ["4", "5", "6"],                # Permission 4 possède 4,5,6
    "5": ["5", "6"],                    # Permission 5 possède 5,6
    "6": ["6"]                         # Permission 6 possède seulement 6
}

class PermView(discord.ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=None)  # Pas de timeout pour les interactions permanentes
        self.cog = cog
        self.ctx = ctx
        self.current_perm = None
        self.message = None
        self.commands_page = 0
        self.commands_per_page = 23
        self.compatible_commands = self.cog.get_compatible_commands()

        self.usage_button = discord.ui.Button(
            label="📘 Utilisation",
            style=discord.ButtonStyle.blurple,
            custom_id="usage_button"
        )
        self.usage_button.callback = self.usage_callback
        
        # Créer les options pour le sélecteur
        options = self._build_permission_options(ctx.guild.id)
        
        # Ajouter le sélecteur
        self.select = discord.ui.Select(
            placeholder="🔐 Choisissez une permission...",
            options=options,
            min_values=1,
            max_values=1
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)
        self.add_item(self.usage_button)
        
        # Ajouter le bouton retour (initialement caché)
        self.back_button = discord.ui.Button(
            label="⬅️ Retour",
            style=discord.ButtonStyle.gray,
            custom_id="back_button"
        )
        self.back_button.callback = self.back_callback
        self.back_button.disabled = True  # Désactivé au début
        
        # Ajouter le bouton d'association (initialement caché)
        self.associate_button = discord.ui.Button(
            label="🔗 Associer ID",
            style=discord.ButtonStyle.green,
            custom_id="associate_button"
        )
        self.associate_button.callback = self.associate_callback
        self.associate_button.disabled = True  # Désactivé au début

        # Sélecteur paginé des commandes (affiché en vue détail)
        self.commands_select = discord.ui.Select(
            placeholder="⚡ Commandes disponibles",
            options=[discord.SelectOption(label="Aucune commande compatible", value="noop")],
            min_values=1,
            max_values=1,
            disabled=True,
            custom_id="commands_select"
        )
        self.commands_select.callback = self.commands_select_callback
        
        # Sélecteur pour retirer des associations (initialisé dynamiquement)
        self.remove_select = None
    
    def refresh_selector(self):
        """Rafraîchit le sélecteur avec les états à jour des permissions"""
        self.select.options = self._build_permission_options(self.ctx.guild.id)

    def _build_permission_options(self, guild_id: int) -> List[discord.SelectOption]:
        """Construit les options du sélecteur principal des permissions."""
        options = []
        permissions_data = self.cog.load_server_permissions(guild_id)

        for i in range(1, TOTAL_PERMISSIONS + 1):
            perm_data = permissions_data.get(str(i), {"associations": [], "commandes": "Aucune"})
            associations = perm_data.get("associations", [])
            linked_commands = self._parse_linked_commands(perm_data.get("commandes", "Aucune"))

            has_content = len(associations) > 0 or bool(linked_commands)
            status_emoji = "🟢" if has_content else "🔴"
            status_text = "Configuré" if has_content else "Vide"

            number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
            number_emoji = number_emojis[i - 1] if i <= len(number_emojis) else f"#{i}"

            options.append(discord.SelectOption(
                label=f"{number_emoji} Permission {i}",
                value=f"perm_{i}",
                description=f"{status_emoji} {status_text} - {len(linked_commands)} commande(s)"
            ))

        return options

    def _parse_linked_commands(self, commandes_raw: str) -> List[str]:
        """Transforme le champ commandes stocké en liste de commandes propres."""
        if not commandes_raw or commandes_raw == "Aucune":
            return []

        if "|" in commandes_raw:
            parts = commandes_raw.split("|")
        else:
            parts = commandes_raw.split(",")

        cleaned = []
        for part in parts:
            cmd = part.strip().lstrip("!")
            if cmd and cmd not in cleaned:
                cleaned.append(cmd)
        return cleaned

    def _get_commands_usage(self, permissions_data: Dict) -> Dict[str, List[str]]:
        """Retourne les permissions qui utilisent chaque commande."""
        usage: Dict[str, List[str]] = {}

        for perm_number in map(str, range(1, TOTAL_PERMISSIONS + 1)):
            perm_data = permissions_data.get(perm_number, {"commandes": "Aucune"})
            for cmd in self._parse_linked_commands(perm_data.get("commandes", "Aucune")):
                usage.setdefault(cmd, []).append(perm_number)

        return usage

    def _get_visible_commands(self, linked_commands: List[str], commands_usage: Dict[str, List[str]]) -> List[str]:
        """Retourne les commandes affichables pour la permission courante."""
        visible_commands = []
        for cmd in self.compatible_commands:
            if cmd in linked_commands:
                visible_commands.append(cmd)
                continue

            used_by = [perm for perm in commands_usage.get(cmd, []) if perm != self.current_perm]
            if not used_by:
                visible_commands.append(cmd)

        return visible_commands

    def _build_commands_options(self, linked_commands: List[str], commands_usage: Dict[str, List[str]]) -> List[discord.SelectOption]:
        """Construit les options de la page courante pour le sélecteur de commandes."""
        visible_commands = self._get_visible_commands(linked_commands, commands_usage)
        total = len(visible_commands)
        if total == 0:
            self.commands_page = 0
            return [discord.SelectOption(label="Aucune commande disponible", value="noop")]

        total_pages = (total + self.commands_per_page - 1) // self.commands_per_page
        if self.commands_page >= total_pages:
            self.commands_page = max(total_pages - 1, 0)

        start_idx = self.commands_page * self.commands_per_page
        end_idx = min(start_idx + self.commands_per_page, total)

        options = []

        if self.commands_page > 0:
            options.append(discord.SelectOption(
                label="⬅️ Page précédente",
                value="__nav_prev__",
                description=f"Revenir à la page {self.commands_page}"
            ))

        for cmd in visible_commands[start_idx:end_idx]:
            if cmd in linked_commands:
                options.append(discord.SelectOption(
                    label=f"✅ {cmd}",
                    value=cmd,
                    description="Déjà liée à cette permission - Cliquer pour retirer"
                ))
                continue

            options.append(discord.SelectOption(
                label=f"❌ {cmd}",
                value=cmd,
                description="Disponible - Cliquer pour lier"
            ))

        if self.commands_page < total_pages - 1:
            options.append(discord.SelectOption(
                label="➡️ Page suivante",
                value="__nav_next__",
                description=f"Aller à la page {self.commands_page + 2}"
            ))

        return options

    def _sync_commands_components(self, guild_id: int):
        """Met à jour les options du sélecteur de commandes et les contrôles de pagination."""
        if not self.current_perm:
            self.commands_select.options = [discord.SelectOption(label="Aucune commande compatible", value="noop")]
            self.commands_select.placeholder = "⚡ Commandes disponibles"
            self.commands_select.disabled = True
            return

        permissions_data = self.cog.load_server_permissions(guild_id)
        perm_data = permissions_data.get(self.current_perm, {"associations": [], "commandes": "Aucune"})
        linked_commands = self._parse_linked_commands(perm_data.get("commandes", "Aucune"))
        commands_usage = self._get_commands_usage(permissions_data)
        visible_commands = self._get_visible_commands(linked_commands, commands_usage)

        options = self._build_commands_options(linked_commands, commands_usage)
        total = len(visible_commands)
        total_pages = max((total + self.commands_per_page - 1) // self.commands_per_page, 1)

        self.commands_select.options = options
        self.commands_select.disabled = total == 0
        self.commands_select.placeholder = (
            f"⚡ Commandes (Page {self.commands_page + 1}/{total_pages}) - {len(linked_commands)} liée(s)"
            if total > 0 else
            "⚡ Aucune commande compatible"
        )

    def _ensure_detail_components(self):
        """Ajoute les composants de la vue détail s'ils ne sont pas présents."""
        for item in [self.commands_select, self.back_button, self.associate_button]:
            if item in self.children:
                self.remove_item(item)

        self.add_item(self.commands_select)
        self.add_item(self.back_button)
        self.add_item(self.associate_button)

    def _build_permission_embed(self, guild: discord.Guild, user: discord.abc.User) -> discord.Embed:
        """Construit l'embed de détail de la permission active."""
        permissions_data = self.cog.load_server_permissions(guild.id)
        perm_data = permissions_data.get(self.current_perm, {"associations": [], "commandes": "Aucune"})
        associations = perm_data.get("associations", [])

        description = f"**Détails de la Permission {self.current_perm}**\n\n"

        roles, users = self.cog.get_associations_by_type(associations)

        description += f"👥 **{self.cog.get_plural_label(len(users), 'Utilisateur Associé', 'Utilisateurs Associés')}** ({len(users)}/{MAX_USERS}) :\n"
        if users:
            for assoc_user in users:
                description += f"└ {self.cog.format_association_name(assoc_user)}\n"
        else:
            description += "└ Aucun\n"

        description += f"\n🛡️ **{self.cog.get_plural_label(len(roles), 'Rôle Associé', 'Rôles Associés')}** ({len(roles)}/{MAX_ROLES}) :\n"
        if roles:
            for role in roles:
                description += f"└ {self.cog.format_association_name(role)}\n"
        else:
            description += "└ Aucun\n"

        linked_commands = self._parse_linked_commands(perm_data.get("commandes", "Aucune"))
        if linked_commands:
            description += f"\n⚡ **Commandes liées ({len(linked_commands)})** :\n"
            description += " | ".join(f"`{cmd}`" for cmd in linked_commands)
        else:
            description += "\n⚡ **Commandes liées** : Aucune"

        return self.cog.config_manager.get_formatted_embed(
            guild=guild,
            user=user,
            bot=self.cog.bot,
            title=f"🔐 Permission {self.current_perm}",
            description=description
        )

    async def commands_select_callback(self, interaction: discord.Interaction):
        selected_value = interaction.data['values'][0]
        if selected_value == "noop" or not self.current_perm:
            await interaction.response.send_message("ℹ️ Aucune commande sélectionnable.", ephemeral=True)
            return

        if selected_value == "__nav_prev__":
            if self.commands_page > 0:
                self.commands_page -= 1
            self._sync_commands_components(interaction.guild.id)
            embed = self._build_permission_embed(interaction.guild, interaction.user)
            await interaction.response.edit_message(embed=embed, view=self)
            return

        if selected_value == "__nav_next__":
            total = len(self.compatible_commands)
            total_pages = max((total + self.commands_per_page - 1) // self.commands_per_page, 1)
            if self.commands_page < total_pages - 1:
                self.commands_page += 1
            self._sync_commands_components(interaction.guild.id)
            embed = self._build_permission_embed(interaction.guild, interaction.user)
            await interaction.response.edit_message(embed=embed, view=self)
            return

        permissions_data = self.cog.load_server_permissions(interaction.guild.id)
        perm_data = permissions_data.get(self.current_perm, {"associations": [], "commandes": "Aucune"})
        linked_commands = self._parse_linked_commands(perm_data.get("commandes", "Aucune"))
        commands_usage = self._get_commands_usage(permissions_data)

        if selected_value in linked_commands:
            linked_commands = [cmd for cmd in linked_commands if cmd != selected_value]
        else:
            used_by = [perm for perm in commands_usage.get(selected_value, []) if perm != self.current_perm]
            if used_by:
                await interaction.response.send_message(
                    f"❌ `{selected_value}` est déjà liée à la Permission {used_by[0]}. Retirez-la d'abord pour la déplacer.",
                    ephemeral=True
                )
                return
            linked_commands.append(selected_value)

        new_cmds = " | ".join(linked_commands) if linked_commands else "Aucune"

        success, message = self.cog.update_permission(
            interaction.guild.id,
            self.current_perm,
            associate_name=None,
            commandes=new_cmds
        )

        if not success:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
            return

        self._sync_commands_components(interaction.guild.id)
        embed = self._build_permission_embed(interaction.guild, interaction.user)
        await interaction.response.edit_message(embed=embed, view=self)

    async def usage_callback(self, interaction: discord.Interaction):
        """Affiche un guide rapide de fonctionnement du module permissions."""
        description = (
            "**Fonctionnement du module `perm`**\n\n"
            "1. Sélectionnez une permission (1 à 6).\n"
            "2. Associez jusqu'à 3 utilisateurs et 3 rôles via `Associer ID`.\n"
            "3. Dans le sélecteur commandes, cliquez sur une commande pour la lier ou la retirer.\n"
            "4. Une commande ne peut être liée qu'à une seule permission à la fois.\n"
            "5. Les commandes déjà utilisées ailleurs sont masquées du sélecteur.\n\n"
            "**Hiérarchie**\n"
            "La Permission 1 hérite des accès 2 à 6, la Permission 2 hérite de 3 à 6, etc."
        )

        embed = create_embed(
            guild=interaction.guild,
            user=interaction.user,
            bot=self.cog.bot,
            title="📘 Utilisation du module Permissions",
            description=description
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Vérifie que seul l'auteur de la commande peut interagir"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Seul l'auteur de la commande peut interagir avec ce menu.", ephemeral=True)
            return False
        return True
    
    async def select_callback(self, interaction: discord.Interaction):
        """Callback pour la sélection d'une permission"""
        selected_value = interaction.data['values'][0]
        perm_number = selected_value.split('_')[1]
        self.current_perm = perm_number
        self.commands_page = 0
        
        # Charger les permissions depuis le fichier du serveur
        permissions_data = self.cog.load_server_permissions(interaction.guild.id)
        perm_data = permissions_data.get(perm_number, {"associations": [], "commandes": "Aucune"})
        associations = perm_data.get("associations", [])
        
        # Créer le sélecteur de retrait s'il y a des associations
        if associations and len(associations) > 0:
            # Séparer les associations par type pour le tri
            user_options = []
            role_options = []
            
            for i, assoc in enumerate(associations[:25]):  # Limiter à 25 options
                # Extraire le nom réel du rôle ou utilisateur
                if assoc.startswith("Rôle: "):
                    # Extraire l'ID du rôle et obtenir le nom réel
                    role_mention = assoc[6:]  # Enlève "Rôle: "
                    if role_mention.startswith('<@&') and role_mention.endswith('>'):
                        try:
                            role_id = int(role_mention.replace('<', '').replace('>', '').replace('@', '').replace('&', ''))
                            role = interaction.guild.get_role(role_id)
                            display_name = role.name if role else role_mention
                        except (ValueError, AttributeError):
                            display_name = role_mention
                    else:
                        display_name = role_mention
                    
                    # Limiter la longueur du label
                    if len(display_name) > 25:
                        display_name = display_name[:22] + "..."
                    
                    role_options.append(discord.SelectOption(
                        label=display_name,
                        value=f"remove_{i}_{self.current_perm}",
                        description="Rôle"
                    ))
                    
                elif assoc.startswith("Utilisateur: "):
                    # Extraire l'ID de l'utilisateur et obtenir le nom réel
                    user_mention = assoc[12:]  # Enlève "Utilisateur: "
                    print(f"[DEBUG] User mention brute: '{user_mention}'")
                    
                    # Essayer d'extraire l'ID de plusieurs manières
                    user_id = None
                    
                    # Méthode 1: Format de mention standard
                    if user_mention.startswith('<@') and user_mention.endswith('>'):
                        clean_mention = user_mention
                        for char in ['<', '>', '@', '!']:
                            clean_mention = clean_mention.replace(char, '')
                        try:
                            user_id = int(clean_mention)
                            print(f"[DEBUG] ID extrait (méthode 1): {user_id}")
                        except ValueError:
                            pass
                    
                    # Méthode 2: Format <@ID...> (incomplet)
                    elif user_mention.startswith('<@'):
                        try:
                            id_part = user_mention[2:].split('>')[0]  # Prend après <@ et avant >
                            if id_part.isdigit():
                                user_id = int(id_part)
                                print(f"[DEBUG] ID extrait (méthode 2): {user_id}")
                        except (ValueError, IndexError):
                            pass
                    
                    # Méthode 3: Directement un nombre
                    elif user_mention.isdigit():
                        user_id = int(user_mention)
                        print(f"[DEBUG] ID extrait (méthode 3): {user_id}")
                    
                    # Méthode 4: Extraire les chiffres de la chaîne
                    else:
                        import re
                        numbers = re.findall(r'\d+', user_mention)
                        if numbers:
                            user_id = int(numbers[0])
                            print(f"[DEBUG] ID extrait (méthode 4): {user_id}")
                    
                    if user_id:
                        user = interaction.guild.get_member(user_id)
                        if user:
                            display_name = f"👥│{user.display_name if user.display_name else user.name}"
                            print(f"[DEBUG] Utilisateur trouvé - name: {user.name}, display: {user.display_name} -> affiché: {display_name}")
                        else:
                            display_name = f"👥│ID:{user_id}"
                            print(f"[DEBUG] Utilisateur non trouvé, fallback: {display_name}")
                    else:
                        display_name = user_mention
                        print(f"[DEBUG] Impossible d'extraire l'ID, fallback: {user_mention}")
                    
                    # Limiter la longueur du label
                    if len(display_name) > 25:
                        display_name = display_name[:22] + "..."
                    
                    user_options.append(discord.SelectOption(
                        label=display_name,
                        value=f"remove_{i}_{self.current_perm}",
                        description="Utilisateur"
                    ))
                else:
                    display_name = assoc
                    
                    # Limiter la longueur du label
                    if len(display_name) > 25:
                        display_name = display_name[:22] + "..."
                    
                    user_options.append(discord.SelectOption(
                        label=display_name,
                        value=f"remove_{i}_{self.current_perm}",
                        description="Autre"
                    ))
            
            # Combiner les options: utilisateurs en premier, puis rôles
            options = user_options + role_options
            
            self.remove_select = discord.ui.Select(
                placeholder="🗑️ Sélectionner à retirer...",
                options=options,
                min_values=1,
                max_values=min(len(options), 25)
            )
            self.remove_select.callback = self.remove_callback
        else:
            self.remove_select = None

        # Cacher le sélecteur principal et activer les composants de détail
        self.select.disabled = True
        self.back_button.disabled = False
        self.associate_button.disabled = False

        self.remove_item(self.select)
        if self.usage_button in self.children:
            self.remove_item(self.usage_button)
        self._sync_commands_components(interaction.guild.id)
        self._ensure_detail_components()
        
        # Ajouter le sélecteur de retrait s'il y a des associations
        if self.remove_select and self.remove_select not in self.children:
            self.add_item(self.remove_select)

        embed = self._build_permission_embed(interaction.guild, interaction.user)
        
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.NotFound:
            # Le message n'existe plus, on envoie un nouveau
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        except discord.HTTPException as e:
            print(f"[ERROR] Erreur modification message: {e}")
            # En cas d'erreur, on tente d'envoyer un nouveau message
            try:
                await interaction.followup.send(embed=embed, view=self, ephemeral=True)
            except:
                pass  # Si ça échoue aussi, on abandonne silencieusement
    
    async def remove_callback(self, interaction: discord.Interaction):
        """Callback pour le sélecteur de retrait"""
        try:
            # Vérifier que c'est bien une interaction de sélecteur
            if not hasattr(interaction, 'data') or not interaction.data:
                await interaction.response.send_message("❌ Erreur: Interaction invalide", ephemeral=True)
                return
                
            selected_values = interaction.data.get('values', [])
            
            if not selected_values:
                await interaction.response.send_message("❌ Aucune sélection", ephemeral=True)
                return
            
            # Récupérer les associations à retirer
            permissions_data = self.cog.load_server_permissions(interaction.guild.id)
            associations = permissions_data.get(self.current_perm, {}).get("associations", [])
            
            associations_to_remove = []
            for value in selected_values:
                try:
                    # Parser le nouveau format: remove_{index}_{permission}
                    parts = value.split('_')
                    if len(parts) >= 3:
                        index = int(parts[1])
                        if 0 <= index < len(associations):
                            associations_to_remove.append(associations[index])
                except (ValueError, IndexError) as e:
                    print(f"[ERROR] Erreur parsing remove value: {value} - {e}")
                    continue
            
            if associations_to_remove:
                success, message = self.cog.remove_associations(interaction.guild.id, self.current_perm, associations_to_remove)
                
                if success:
                    await interaction.response.send_message(f"✅ {message}", ephemeral=True)
                    # Rafraîchir la vue et le sélecteur
                    await self.refresh_view(interaction)
                    self.refresh_selector()
                else:
                    await interaction.response.send_message(f"❌ {message}", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Aucune association valide à supprimer.", ephemeral=True)
                
        except Exception as e:
            print(f"[ERROR] Erreur dans remove_callback: {e}")
            await interaction.response.send_message(f"❌ Erreur: {e}", ephemeral=True)
    
    async def refresh_view(self, interaction: discord.Interaction):
        """Rafraîchit la vue avec les associations mises à jour"""
        try:
            # Supprimer l'ancien sélecteur de retrait s'il existe
            if self.remove_select:
                self.remove_item(self.remove_select)
                self.remove_select = None
            
            # Recharger les permissions
            permissions_data = self.cog.load_server_permissions(interaction.guild.id)
            perm_data = permissions_data.get(self.current_perm, {"associations": [], "commandes": "Aucune"})
            associations = perm_data.get("associations", [])
            
            # Recréer le sélecteur de retrait s'il y a des associations
            if associations and len(associations) > 0:
                # Séparer les associations par type pour le tri
                user_options = []
                role_options = []
                
                for i, assoc in enumerate(associations[:25]):  # Limiter à 25 options
                    # Extraire le nom réel du rôle ou utilisateur
                    if assoc.startswith("Rôle: "):
                        # Extraire l'ID du rôle et obtenir le nom réel
                        role_mention = assoc[6:]  # Enlève "Rôle: "
                        if role_mention.startswith('<@&') and role_mention.endswith('>'):
                            try:
                                role_id = int(role_mention.replace('<', '').replace('>', '').replace('@', '').replace('&', ''))
                                role = interaction.guild.get_role(role_id)
                                display_name = role.name if role else role_mention
                            except (ValueError, AttributeError):
                                display_name = role_mention
                        else:
                            display_name = role_mention
                        
                        # Limiter la longueur du label
                        if len(display_name) > 25:
                            display_name = display_name[:22] + "..."
                        
                        role_options.append(discord.SelectOption(
                            label=display_name,
                            value=f"remove_{i}_{self.current_perm}_refresh",
                            description="Rôle"
                        ))
                        
                    elif assoc.startswith("Utilisateur: "):
                        # Extraire l'ID de l'utilisateur et obtenir le nom réel
                        user_mention = assoc[12:]  # Enlève "Utilisateur: "
                        print(f"[DEBUG] User mention brute (refresh): '{user_mention}'")
                        
                        # Essayer d'extraire l'ID de plusieurs manières
                        user_id = None
                        
                        # Méthode 1: Format de mention standard
                        if user_mention.startswith('<@') and user_mention.endswith('>'):
                            clean_mention = user_mention
                            for char in ['<', '>', '@', '!']:
                                clean_mention = clean_mention.replace(char, '')
                            try:
                                user_id = int(clean_mention)
                                print(f"[DEBUG] ID extrait (méthode 1 - refresh): {user_id}")
                            except ValueError:
                                pass
                        
                        # Méthode 2: Format <@ID...> (incomplet)
                        elif user_mention.startswith('<@'):
                            try:
                                id_part = user_mention[2:].split('>')[0]  # Prend après <@ et avant >
                                if id_part.isdigit():
                                    user_id = int(id_part)
                                    print(f"[DEBUG] ID extrait (méthode 2 - refresh): {user_id}")
                            except (ValueError, IndexError):
                                pass
                        
                        # Méthode 3: Directement un nombre
                        elif user_mention.isdigit():
                            user_id = int(user_mention)
                            print(f"[DEBUG] ID extrait (méthode 3 - refresh): {user_id}")
                        
                        # Méthode 4: Extraire les chiffres de la chaîne
                        else:
                            import re
                            numbers = re.findall(r'\d+', user_mention)
                            if numbers:
                                user_id = int(numbers[0])
                                print(f"[DEBUG] ID extrait (méthode 4 - refresh): {user_id}")
                        
                        if user_id:
                            user = interaction.guild.get_member(user_id)
                            if user:
                                display_name = f"👥│{user.display_name if user.display_name else user.name}"
                                print(f"[DEBUG] Utilisateur trouvé (refresh) - name: {user.name}, display: {user.display_name} -> affiché: {display_name}")
                            else:
                                display_name = f"👥│ID:{user_id}"
                                print(f"[DEBUG] Utilisateur non trouvé (refresh), fallback: {display_name}")
                        else:
                            display_name = user_mention
                            print(f"[DEBUG] Impossible d'extraire l'ID (refresh), fallback: {user_mention}")
                        
                        # Limiter la longueur du label
                        if len(display_name) > 25:
                            display_name = display_name[:22] + "..."
                        
                        user_options.append(discord.SelectOption(
                            label=display_name,
                            value=f"remove_{i}_{self.current_perm}_refresh",
                            description="Utilisateur"
                        ))
                    else:
                        display_name = assoc
                        
                        # Limiter la longueur du label
                        if len(display_name) > 25:
                            display_name = display_name[:22] + "..."
                        
                        user_options.append(discord.SelectOption(
                            label=display_name,
                            value=f"remove_{i}_{self.current_perm}_refresh",
                            description="Autre"
                        ))
                
                # Combiner les options: utilisateurs en premier, puis rôles
                options = user_options + role_options
                
                self.remove_select = discord.ui.Select(
                    placeholder="🗑️ Sélectionner à retirer...",
                    options=options,
                    min_values=1,
                    max_values=min(len(options), 25)
                )
                self.remove_select.callback = self.remove_callback
                self.add_item(self.remove_select)

            self._sync_commands_components(interaction.guild.id)
            self._ensure_detail_components()
            embed = self._build_permission_embed(interaction.guild, interaction.user)
            
            try:
                await interaction.response.edit_message(embed=embed, view=self)
            except discord.NotFound:
                # Le message n'existe plus, on envoie un nouveau
                await interaction.followup.send(embed=embed, view=self, ephemeral=True)
            except discord.HTTPException as e:
                print(f"[ERROR] Erreur modification message: {e}")
                # En cas d'erreur, on tente d'envoyer un nouveau message
                try:
                    await interaction.followup.send(embed=embed, view=self, ephemeral=True)
                except:
                    pass  # Si ça échoue aussi, on abandonne silencieusement
            
        except Exception as e:
            print(f"[ERROR] Erreur dans refresh_view: {e}")
            await interaction.response.send_message(f"❌ Erreur lors du rafraîchissement: {e}", ephemeral=True)
    
    async def associate_callback(self, interaction: discord.Interaction):
        """Callback pour le bouton d'association"""
        # Ouvrir un modal pour associer un rôle ou un utilisateur
        modal = discord.ui.Modal(title="Associer à la Permission")
        
        associate_input = discord.ui.TextInput(
            label="ID du rôle ou de l'utilisateur",
            placeholder="Ex: 123456789 (ID numérique uniquement)",
            required=True
        )
        
        modal.add_item(associate_input)
        
        async def on_submit(interaction: discord.Interaction):
            try:
                print(f"[DEBUG] Modal on_submit appelé")
                
                # Vérifier que c'est bien une interaction de modal
                if not hasattr(interaction, 'data'):
                    print("[ERROR] Interaction n'a pas d'attribut 'data'")
                    await interaction.response.send_message("❌ Erreur: Interaction invalide", ephemeral=True)
                    return
                
                # Extraire l'ID numérique
                associate_text = associate_input.value.strip()
                print(f"[DEBUG] Texte reçu: {associate_text}")
                
                if not associate_text:
                    await interaction.response.send_message("❌ Veuillez entrer un ID numérique", ephemeral=True)
                    return
                
                # Vérifier que c'est bien un ID numérique
                try:
                    id_num = int(associate_text)
                    print(f"[DEBUG] ID converti: {id_num}")
                except ValueError:
                    await interaction.response.send_message("❌ Veuillez entrer un ID numérique valide", ephemeral=True)
                    return
                
                # Essayer comme rôle d'abord
                role = interaction.guild.get_role(id_num)
                if role:
                    associate_name = f"Rôle: {role.mention}"
                    print(f"[DEBUG] Rôle trouvé: {role.name}")
                else:
                    # Essayer comme utilisateur
                    user = interaction.guild.get_member(id_num)
                    if user:
                        associate_name = f"Utilisateur: {user.mention}"
                        print(f"[DEBUG] Utilisateur trouvé: {user.display_name}")
                    else:
                        await interaction.response.send_message("❌ ID introuvable (ni rôle ni utilisateur)", ephemeral=True)
                        return
                
                # Ajouter l'association
                success, message = self.cog.update_permission(
                    interaction.guild.id, 
                    self.current_perm, 
                    associate_name
                )
                
                if success:
                    print(f"[DEBUG] Association ajoutée avec succès: {associate_name}")
                    # Rafraîchir la vue avec les associations mises à jour
                    await self.refresh_view(interaction)
                else:
                    await interaction.response.send_message(f"❌ {message}", ephemeral=True)
                    
            except Exception as e:
                print(f"[ERROR] Erreur dans on_submit: {e}")
                print(f"[DEBUG] Type d'erreur: {type(e)}")
                import traceback
                traceback.print_exc()
                await interaction.response.send_message(f"❌ Erreur: {e}", ephemeral=True)
        
        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)
    
    async def commands_callback(self, interaction: discord.Interaction):
        """Callback pour le bouton Commands"""
        # Obtenir toutes les commandes protégées
        all_commands = self.cog.get_protected_commands()
        
        # Obtenir les commandes déjà liées à cette permission
        permissions_data = self.cog.load_server_permissions(interaction.guild.id)
        perm_data = permissions_data.get(self.current_perm, {"associations": [], "commandes": "Aucune"})
        commandes = perm_data.get("commandes", "Aucune")
        
        # Extraire les commandes liées
        linked_commands = set()
        if commandes != "Aucune" and commandes.strip():
            if "|" in commandes:
                cmd_list = [cmd.strip() for cmd in commandes.split("|")]
            else:
                cmd_list = [cmd.strip() for cmd in commandes.split(",")]
            linked_commands = {cmd for cmd in cmd_list if cmd.strip()}
        
        # Afficher la première page
        await self.show_commands_page(interaction, all_commands, linked_commands, page=0)
    
    async def show_commands_page(self, interaction, all_commands, linked_commands, page=0):
        """Affiche une page spécifique des commandes"""
        ITEMS_PER_PAGE = 24  # 24 commandes + 1 option de navigation
        
        # Calculer les indices
        start_idx = page * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(all_commands))
        
        # Créer les options pour cette page
        options = []
        
        # Ajouter les commandes de cette page
        for i in range(start_idx, end_idx):
            cmd = all_commands[i]
            cmd_name = cmd['name']
            
            # Vérifier si la commande est liée
            is_linked = cmd_name in linked_commands
            
            # Créer le label avec statut
            status_emoji = "✅" if is_linked else "❌"
            status_text = "Déjà lié" if is_linked else "Non lié"
            
            # Limiter la longueur du label
            label = f"{status_emoji} {cmd_name}"
            if len(label) > 100:
                label = label[:97] + "..."
            
            options.append(discord.SelectOption(
                label=label,
                value=cmd_name,
                description=f"{status_text} - {cmd['description'][:50]}{'...' if len(cmd['description']) > 50 else ''}",
                emoji=status_emoji
            ))
        
        # Ajouter l'option de navigation si nécessaire
        total_pages = (len(all_commands) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        if total_pages > 1:
            if page < total_pages - 1:
                # Il y a une page suivante
                options.append(discord.SelectOption(
                    label="➡️ Page suivante",
                    value="next_page",
                    description=f"Voir la page {page + 2}",
                    emoji="➡️"
                ))
            else:
                # Dernière page
                options.append(discord.SelectOption(
                    label="⏹️ Fin de la liste",
                    value="end_list",
                    description="Toutes les commandes ont été affichées",
                    emoji="⏹️"
                ))
        
        # Créer le sélecteur
        select = discord.ui.Select(
            placeholder=f"🔧 Commandes (Page {page + 1}/{total_pages or 1}) - {len(linked_commands)} liée(s)",
            options=options,
            min_values=1,
            max_values=1
        )
        
        async def select_callback(interaction: discord.Interaction):
            try:
                selected_value = interaction.data['values'][0]
                print(f"[DEBUG] Sélection dans le sélecteur: {selected_value}")
                
                if selected_value == "next_page":
                    # Page suivante
                    await self.show_commands_page(interaction, all_commands, linked_commands, page + 1)
                    
                elif selected_value == "end_list":
                    # Revenir à la première page
                    await self.show_commands_page(interaction, all_commands, linked_commands, 0)
                    
                else:
                    # Gestion d'une commande spécifique
                    cmd_name = selected_value
                    is_linked = cmd_name in linked_commands
                    print(f"[DEBUG] Gestion de la commande: {cmd_name}, déjà liée: {is_linked}")
                    
                    # Recharger les permissions fraîches
                    permissions_data = self.cog.load_server_permissions(interaction.guild.id)
                    perm_data = permissions_data.get(self.current_perm, {"associations": [], "commandes": "Aucune"})
                    current_commandes = perm_data.get("commandes", "Aucune")
                    
                    print(f"[DEBUG] Commandes actuelles dans le fichier: {current_commandes}")
                    
                    if is_linked:
                        # Supprimer la commande
                        print(f"[DEBUG] Suppression de la commande {cmd_name}")
                        
                        if "|" in current_commandes:
                            cmd_list = [cmd.strip() for cmd in current_commandes.split("|")]
                        else:
                            cmd_list = [cmd.strip() for cmd in current_commandes.split(",")]
                        
                        cmd_list = [cmd for cmd in cmd_list if cmd.strip() != cmd_name]
                        
                        if cmd_list:
                            new_cmds = " | ".join(cmd_list)
                        else:
                            new_cmds = "Aucune"
                        
                        print(f"[DEBUG] Nouvelles commandes après suppression: {new_cmds}")
                        
                    else:
                        # Ajouter la commande
                        print(f"[DEBUG] Ajout de la commande {cmd_name}")
                        
                        if current_commandes != "Aucune" and current_commandes.strip():
                            new_cmds = f"{current_commandes} | {cmd_name}"
                        else:
                            new_cmds = cmd_name
                        
                        print(f"[DEBUG] Nouvelles commandes après ajout: {new_cmds}")
                    
                    # Mettre à jour la permission
                    success, message = self.cog.update_permission(
                        interaction.guild.id,
                        self.current_perm,
                        associate_name=None,
                        commandes=new_cmds
                    )
                    
                    print(f"[DEBUG] Résultat de la mise à jour: success={success}, message={message}")
                    
                    if success:
                        # Mettre à jour l'ensemble des commandes liées
                        if is_linked:
                            linked_commands.remove(cmd_name)
                            await interaction.response.send_message(f"✅ Commande `{cmd_name}` retirée de la Permission {self.current_perm}!", ephemeral=True)
                        else:
                            linked_commands.add(cmd_name)
                            await interaction.response.send_message(f"✅ Commande `{cmd_name}` ajoutée à la Permission {self.current_perm}!", ephemeral=True)
                        
                        # Attendre un peu puis rafraîchir avec edit_message
                        import asyncio
                        await asyncio.sleep(0.5)
                        
                        # Créer une nouvelle interaction pour le rafraîchissement
                        try:
                            # On ne peut pas appeler show_commands_page directement car interaction.response est déjà utilisé
                            # On va envoyer un nouveau message à la place
                            await self.show_commands_page_new(interaction, all_commands, linked_commands, page)
                        except:
                            # Si ça échoue, on informe l'utilisateur de rafraîchir manuellement
                            pass
                    else:
                        await interaction.response.send_message(f"❌ Erreur: {message}", ephemeral=True)
                        
            except Exception as e:
                print(f"[ERROR] Erreur dans select_callback: {e}")
                import traceback
                traceback.print_exc()
                await interaction.response.send_message(f"❌ Erreur lors de la gestion de la commande: {e}", ephemeral=True)
        
        select.callback = select_callback
        
        # Créer la vue avec boutons de navigation
        view = discord.ui.View(timeout=None)
        view.add_item(select)
        
        # Ajouter des boutons de navigation si plusieurs pages
        if total_pages > 1:
            # Bouton page précédente
            prev_button = discord.ui.Button(
                label="⬅️ Page précédente",
                style=discord.ButtonStyle.secondary,
                disabled=(page == 0)
            )
            
            async def prev_callback(interaction: discord.Interaction):
                await self.show_commands_page(interaction, all_commands, linked_commands, page - 1)
            
            prev_button.callback = prev_callback
            view.add_item(prev_button)
            
            # Bouton page suivante
            next_button = discord.ui.Button(
                label="➡️ Page suivante",
                style=discord.ButtonStyle.secondary,
                disabled=(page >= total_pages - 1)
            )
            
            async def next_callback(interaction: discord.Interaction):
                await self.show_commands_page(interaction, all_commands, linked_commands, page + 1)
            
            next_button.callback = next_callback
            view.add_item(next_button)
            
            # Indicateur de page
            page_label = discord.ui.Button(
                label=f"Page {page + 1}/{total_pages}",
                style=discord.ButtonStyle.primary,
                disabled=True
            )
            view.add_item(page_label)
        
        # Créer l'embed principal
        description = f"**⚡ Commandes de la Permission {self.current_perm}**\n\n"
        
        # Statut actuel
        if linked_commands:
            description += f"**🔹 Commandes actuellement liées ({len(linked_commands)}) :**\n"
            for cmd in sorted(linked_commands):
                description += f"└ `{cmd}`\n"
        else:
            description += "**🔴 Aucune commande liée**\n"
            description += "Cette permission n'a actuellement aucune commande associée.\n"
        
        description += f"\n**🔧 Actions disponibles :**\n"
        description += "• Sélectionnez une commande dans le menu pour la lier/délier\n"
        description += "• ✅ = Commande déjà liée | ❌ = Commande non liée\n"
        description += "• Utilisez les boutons pour naviguer entre les pages\n\n"
        
        # Statistiques
        total_protected = len(all_commands)
        percentage = (len(linked_commands)/total_protected*100) if total_protected > 0 else 0
        description += f"**📊 Statistiques :**\n"
        description += f"└ Commandes protégées détectées : {total_protected}\n"
        description += f"└ Commandes liées à cette permission : {len(linked_commands)}\n"
        description += f"└ Taux de liaison : {percentage:.1f}%\n"
        
        embed = await create_embed(
            guild=interaction.guild,
            user=interaction.user,
            bot=self.cog.bot,
            title=f"⚡ Commandes de la Permission {self.current_perm}",
            description=description,
            target_id=interaction.guild.id
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def show_commands_page_new(self, interaction, all_commands, linked_commands, page=0):
        """Version alternative pour le rafraîchissement après modification"""
        try:
            # Recréer l'embed et la vue pour la nouvelle page
            ITEMS_PER_PAGE = 24
            
            # Calculer les indices
            start_idx = page * ITEMS_PER_PAGE
            end_idx = min(start_idx + ITEMS_PER_PAGE, len(all_commands))
            
            # Créer les options pour cette page
            options = []
            
            # Ajouter les commandes de cette page
            for i in range(start_idx, end_idx):
                cmd = all_commands[i]
                cmd_name = cmd['name']
                
                # Vérifier si la commande est liée
                is_linked = cmd_name in linked_commands
                
                # Créer le label avec statut
                status_emoji = "✅" if is_linked else "❌"
                status_text = "Déjà lié" if is_linked else "Non lié"
                
                # Limiter la longueur du label
                label = f"{status_emoji} {cmd_name}"
                if len(label) > 100:
                    label = label[:97] + "..."
                
                options.append(discord.SelectOption(
                    label=label,
                    value=cmd_name,
                    description=f"{status_text} - {cmd['description'][:50]}{'...' if len(cmd['description']) > 50 else ''}",
                    emoji=status_emoji
                ))
            
            # Ajouter l'option de navigation si nécessaire
            total_pages = (len(all_commands) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            
            if total_pages > 1:
                if page < total_pages - 1:
                    options.append(discord.SelectOption(
                        label="➡️ Page suivante",
                        value="next_page",
                        description=f"Voir la page {page + 2}",
                        emoji="➡️"
                    ))
                else:
                    options.append(discord.SelectOption(
                        label="⏹️ Fin de la liste",
                        value="end_list",
                        description="Toutes les commandes ont été affichées",
                        emoji="⏹️"
                    ))
            
            # Créer le sélecteur
            select = discord.ui.Select(
                placeholder=f"🔧 Commandes (Page {page + 1}/{total_pages or 1}) - {len(linked_commands)} liée(s)",
                options=options,
                min_values=1,
                max_values=1
            )
            
            # Réutiliser le même callback
            async def select_callback(interaction: discord.Interaction):
                selected_value = interaction.data['values'][0]
                
                if selected_value == "next_page":
                    await self.show_commands_page_new(interaction, all_commands, linked_commands, page + 1)
                elif selected_value == "end_list":
                    await self.show_commands_page_new(interaction, all_commands, linked_commands, 0)
                else:
                    # Pour les commandes, on utilise la logique existante mais sans le rafraîchissement automatique
                    cmd_name = selected_value
                    is_linked = cmd_name in linked_commands
                    
                    # Recharger les permissions fraîches
                    permissions_data = self.cog.load_server_permissions(interaction.guild.id)
                    perm_data = permissions_data.get(self.current_perm, {"associations": [], "commandes": "Aucune"})
                    current_commandes = perm_data.get("commandes", "Aucune")
                    
                    if is_linked:
                        # Supprimer la commande
                        if "|" in current_commandes:
                            cmd_list = [cmd.strip() for cmd in current_commandes.split("|")]
                        else:
                            cmd_list = [cmd.strip() for cmd in current_commandes.split(",")]
                        
                        cmd_list = [cmd for cmd in cmd_list if cmd.strip() != cmd_name]
                        
                        if cmd_list:
                            new_cmds = " | ".join(cmd_list)
                        else:
                            new_cmds = "Aucune"
                    else:
                        # Ajouter la commande
                        if current_commandes != "Aucune" and current_commandes.strip():
                            new_cmds = f"{current_commandes} | {cmd_name}"
                        else:
                            new_cmds = cmd_name
                    
                    # Mettre à jour la permission
                    success, message = self.cog.update_permission(
                        interaction.guild.id,
                        self.current_perm,
                        associate_name=None,
                        commandes=new_cmds
                    )
                    
                    if success:
                        if is_linked:
                            linked_commands.remove(cmd_name)
                            await interaction.response.send_message(f"✅ Commande `{cmd_name}` retirée de la Permission {self.current_perm}!", ephemeral=True)
                        else:
                            linked_commands.add(cmd_name)
                            await interaction.response.send_message(f"✅ Commande `{cmd_name}` ajoutée à la Permission {self.current_perm}!", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"❌ Erreur: {message}", ephemeral=True)
            
            select.callback = select_callback
            
            # Créer la vue avec boutons de navigation
            view = discord.ui.View(timeout=None)
            view.add_item(select)
            
            # Ajouter des boutons de navigation si plusieurs pages
            if total_pages > 1:
                # Bouton page précédente
                prev_button = discord.ui.Button(
                    label="⬅️ Page précédente",
                    style=discord.ButtonStyle.secondary,
                    disabled=(page == 0)
                )
                
                async def prev_callback(interaction: discord.Interaction):
                    await self.show_commands_page_new(interaction, all_commands, linked_commands, page - 1)
                
                prev_button.callback = prev_callback
                view.add_item(prev_button)
                
                # Bouton page suivante
                next_button = discord.ui.Button(
                    label="➡️ Page suivante",
                    style=discord.ButtonStyle.secondary,
                    disabled=(page >= total_pages - 1)
                )
                
                async def next_callback(interaction: discord.Interaction):
                    await self.show_commands_page_new(interaction, all_commands, linked_commands, page + 1)
                
                next_button.callback = next_callback
                view.add_item(next_button)
                
                # Indicateur de page
                page_label = discord.ui.Button(
                    label=f"Page {page + 1}/{total_pages}",
                    style=discord.ButtonStyle.primary,
                    disabled=True
                )
                view.add_item(page_label)
            
            # Créer l'embed principal
            description = f"**⚡ Commandes de la Permission {self.current_perm}**\n\n"
            
            # Statut actuel
            if linked_commands:
                description += f"**🔹 Commandes actuellement liées ({len(linked_commands)}) :**\n"
                for cmd in sorted(linked_commands):
                    description += f"└ `{cmd}`\n"
            else:
                description += "**🔴 Aucune commande liée**\n"
                description += "Cette permission n'a actuellement aucune commande associée.\n"
            
            description += f"\n**🔧 Actions disponibles :**\n"
            description += "• Sélectionnez une commande dans le menu pour la lier/délier\n"
            description += "• ✅ = Commande déjà liée | ❌ = Commande non liée\n"
            description += "• Utilisez les boutons pour naviguer entre les pages\n\n"
            
            # Statistiques
            total_protected = len(all_commands)
            percentage = (len(linked_commands)/total_protected*100) if total_protected > 0 else 0
            description += f"**📊 Statistiques :**\n"
            description += f"└ Commandes protégées détectées : {total_protected}\n"
            description += f"└ Commandes liées à cette permission : {len(linked_commands)}\n"
            description += f"└ Taux de liaison : {percentage:.1f}%\n"
            
            embed = create_embed(
                guild=interaction.guild,
                user=interaction.user,
                bot=self.cog.bot,
                title=f"⚡ Commandes de la Permission {self.current_perm}",
                description=description
            )
            
            # Utiliser followup pour envoyer le nouveau message
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            print(f"[ERROR] Erreur dans show_commands_page_new: {e}")
            # En cas d'erreur, on ne fait rien pour éviter casser l'interaction
    
    async def back_callback(self, interaction: discord.Interaction):
        """Callback pour le bouton retour"""
        self.current_perm = None
        self.commands_page = 0
        
        # Créer l'embed principal avec toutes les permissions configurées uniquement
        description = ""
        configured_perms = 0
        
        # Charger les permissions depuis le fichier du serveur
        permissions_data = self.cog.load_server_permissions(interaction.guild.id)
        
        for i in range(1, TOTAL_PERMISSIONS + 1):
            perm_key = str(i)
            perm_data = permissions_data.get(perm_key, {"associations": [], "commandes": "Aucune"})
            associations = perm_data.get("associations", [])
            commandes = perm_data.get("commandes", "Aucune")
            
            # Vérifier si la permission est configurée
            is_configured = len(associations) > 0 or commandes != "Aucune"
            
            # N'afficher que les permissions configurées
            if is_configured:
                configured_perms += 1
                
                # Séparer les associations par type
                roles, users = self.cog.get_associations_by_type(associations)
                
                description += f"**Permission {i}**\n"
                description += f"└ 🔹 **{self.cog.get_plural_label(len(users), 'Utilisateur Associé', 'Utilisateurs Associés')}** ({len(users)}/{MAX_USERS}) : "
                
                if users:
                    # Afficher tous les utilisateurs sans préfixe
                    formatted_users = [self.cog.format_association_name(user) for user in users]
                    description += ", ".join(formatted_users)
                else:
                    description += "Aucun"
                
                description += f"\n└ 🔹 **{self.cog.get_plural_label(len(roles), 'Rôle Associé', 'Rôles Associés')}** ({len(roles)}/{MAX_ROLES}) : "
                
                if roles:
                    # Afficher tous les rôles sans préfixe
                    formatted_roles = [self.cog.format_association_name(role) for role in roles]
                    description += ", ".join(formatted_roles)
                else:
                    description += "Aucun"
                
                description += f"\n└ 🔸 **{self.cog.get_plural_label(1 if perm_data['commandes'] != 'Aucune' else 0, 'Commande', 'Commandes')}** : {perm_data['commandes']}\n\n"
        
        # Si aucune permission n'est configurée
        if configured_perms == 0:
            # Importer le message depuis le fichier no_perm.txt
            with open(os.path.join(os.path.dirname(self.cog.__file__), 'no_perm.txt'), 'r', encoding='utf-8') as f:
                description = f.read()
        else:
            # Si des permissions sont configurées, afficher l'embed normal
            pass  # Le code existant ci-dessous gère déjà ce cas
        
        embed = create_embed(
            guild=interaction.guild,
            user=interaction.user,
            bot=self.cog.bot,
            title="🔐 Permissions",
            description=description
        )
        
        # Réactiver le sélecteur et désactiver les autres boutons
        self.back_button.disabled = True
        self.associate_button.disabled = True
        
        # Retirer tous les éléments supplémentaires
        self.remove_item(self.back_button)
        self.remove_item(self.associate_button)
        if self.commands_select in self.children:
            self.remove_item(self.commands_select)
        
        if self.remove_select:
            self.remove_item(self.remove_select)
            self.remove_select = None
        
        # Remettre le sélecteur principal
        self.add_item(self.select)
        if self.usage_button not in self.children:
            self.add_item(self.usage_button)
        self.select.disabled = False
        
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.NotFound:
            # Le message n'existe plus, on envoie un nouveau
            await interaction.followup.send(embed=embed, view=self, ephemeral=True)
        except discord.HTTPException as e:
            print(f"[ERROR] Erreur modification message: {e}")
            # En cas d'erreur HTTP, on utilise followup
            try:
                await interaction.followup.send(embed=embed, view=self, ephemeral=True)
            except Exception as e2:
                print(f"[ERROR] Erreur followup: {e2}")
                pass  # Si ça échoue aussi, on abandonne silencieusement
        except Exception as e:
            print(f"[ERROR] Erreur inattendue dans back_callback: {e}")
            # Pour toute autre erreur, on tente followup
            try:
                await interaction.followup.send(embed=embed, view=self, ephemeral=True)
            except:
                pass  # Si ça échoue aussi, on abandonne silencieusement

class Perm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = config_manager
        self.data_dir = Path(__file__).parent / "data"
        if not self.data_dir.exists():
            self.data_dir.mkdir(exist_ok=True)
    
    def get_server_file_path(self, guild_id: int) -> Path:
        """Retourne le chemin du fichier JSON pour un serveur"""
        return self.data_dir / f"server_{guild_id}_permissions.json"
    
    def load_server_permissions(self, guild_id: int) -> Dict:
        """Charge les permissions d'un serveur depuis le fichier JSON"""
        file_path = self.get_server_file_path(guild_id)
        
        if not file_path.exists():
            # Créer le fichier avec les permissions par défaut
            default_permissions = {}
            for i in range(1, TOTAL_PERMISSIONS + 1):
                default_permissions[str(i)] = {
                    "commandes": "Aucune",
                    "description": f"Permission {i} - Non configurée"
                }
            self.save_server_permissions(guild_id, default_permissions)
            return default_permissions
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Nettoyer les anciens fichiers en supprimant le champ "role"
                cleaned_data = {}
                for perm_key, perm_data in data.items():
                    cleaned_data[perm_key] = {
                        k: v for k, v in perm_data.items() if k != "role"
                    }
                # Si des données ont été nettoyées, sauvegarder le fichier nettoyé
                if len(data) > 0 and any("role" in perm_data for perm_data in data.values()):
                    self.save_server_permissions(guild_id, cleaned_data)
                    print(f"[DEBUG] Fichier de permissions nettoyé pour le serveur {guild_id}")
                return cleaned_data
        except (json.JSONDecodeError, Exception) as e:
            print(f"[ERROR] Erreur lors du chargement des permissions du serveur {guild_id}: {e}")
            return self.get_default_permissions()
    
    def save_server_permissions(self, guild_id: int, permissions_data: Dict):
        """Sauvegarde les permissions d'un serveur dans le fichier JSON"""
        file_path = self.get_server_file_path(guild_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(permissions_data, f, indent=4, ensure_ascii=False)
            print(f"[DEBUG] Permissions sauvegardées pour le serveur {guild_id}")
        except Exception as e:
            print(f"[ERROR] Erreur lors de la sauvegarde des permissions du serveur {guild_id}: {e}")
    
    def get_default_permissions(self) -> Dict:
        """Retourne les permissions par défaut"""
        default_permissions = {}
        for i in range(1, TOTAL_PERMISSIONS + 1):
            default_permissions[str(i)] = {
                "associations": [],  # Liste des associations (rôles/utilisateurs)
                "commandes": "Aucune"
            }
        return default_permissions
    
    def update_permission(self, guild_id: int, perm_number: str, associate_name: str = None, commandes: str = None):
        """Ajoute une association ou met à jour les commandes d'une permission spécifique"""
        permissions_data = self.load_server_permissions(guild_id)
        
        if perm_number in permissions_data:
            # Cas 1: Ajout d'une association
            if associate_name:
                associations = permissions_data[perm_number].get("associations", [])
                
                # Séparer les associations par type
                roles, users = self.get_associations_by_type(associations)
                
                # Vérifier les limites selon le type
                if associate_name.startswith("Rôle:"):
                    if len(roles) >= MAX_ROLES:
                        return False, f"Limite de {MAX_ROLES} rôles atteinte"
                elif associate_name.startswith("Utilisateur:"):
                    if len(users) >= MAX_USERS:
                        return False, f"Limite de {MAX_USERS} utilisateurs atteinte"
                
                # Vérifier si l'association n'existe pas déjà
                if associate_name not in associations:
                    associations.append(associate_name)
                    permissions_data[perm_number]["associations"] = associations
                    
                    self.save_server_permissions(guild_id, permissions_data)
                    return True, "Association ajoutée"
                else:
                    return False, "Association déjà existante"
            
            # Cas 2: Mise à jour des commandes uniquement
            elif commandes is not None:
                print(f"[DEBUG] Mise à jour des commandes pour la permission {perm_number}")
                print(f"[DEBUG] Anciennes commandes: {permissions_data[perm_number].get('commandes', 'Aucune')}")
                print(f"[DEBUG] Nouvelles commandes: {commandes}")
                
                permissions_data[perm_number]["commandes"] = commandes
                self.save_server_permissions(guild_id, permissions_data)
                
                # Vérifier que la sauvegarde a bien fonctionné
                saved_data = self.load_server_permissions(guild_id)
                saved_cmds = saved_data.get(perm_number, {}).get("commandes", "Aucune")
                print(f"[DEBUG] Commandes après sauvegarde: {saved_cmds}")
                
                return True, "Commandes mises à jour"
            
            return False, "Aucune modification spécifiée"
        return False, "Permission introuvable"
    
    def remove_associations(self, guild_id: int, perm_number: str, associations_to_remove: list):
        """Retire des associations spécifiques d'une permission"""
        permissions_data = self.load_server_permissions(guild_id)
        
        if perm_number in permissions_data:
            associations = permissions_data[perm_number].get("associations", [])
            
            # Retirer les associations spécifiées
            remaining_associations = [assoc for assoc in associations if assoc not in associations_to_remove]
            permissions_data[perm_number]["associations"] = remaining_associations
            
            self.save_server_permissions(guild_id, permissions_data)
            return True, f"{len(associations_to_remove)} association(s) retirée(s)"
        return False, "Permission introuvable"
    
    def get_compatible_commands(self) -> List[str]:
        """Retourne les commandes compatibles listées dans cmdperm.md."""
        project_root = Path(__file__).resolve().parents[3]
        cmdperm_path = project_root / "cmdperm.md"

        if not cmdperm_path.exists():
            print(f"[WARN] Fichier cmdperm.md introuvable: {cmdperm_path}")
            return []

        commands_list = []
        try:
            with open(cmdperm_path, 'r', encoding='utf-8') as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue

                    line = line.lstrip("-*").strip()
                    line = line.strip("`")
                    if line.startswith("!"):
                        line = line[1:]

                    if line and line not in commands_list:
                        commands_list.append(line)
        except Exception as e:
            print(f"[ERROR] Erreur lecture cmdperm.md: {e}")
            return []

        return commands_list

    def get_protected_commands(self) -> list:
        """Compatibilité descendante: expose les commandes de cmdperm.md au format historique."""
        return [
            {
                'name': command_name,
                'description': "Commande compatible (cmdperm.md)",
                'cog': "cmdperm"
            }
            for command_name in self.get_compatible_commands()
        ]
    
    def get_plural_label(self, count: int, singular: str, plural: str) -> str:
        """Retourne le label singulier ou pluriel selon le count"""
        return singular if count <= 1 else plural
    
    def format_association_name(self, assoc: str) -> str:
        """Formate le nom d'association pour l'affichage (enlève les préfixes)"""
        if assoc.startswith("Rôle: "):
            return assoc[6:]  # Enlève "Rôle: "
        elif assoc.startswith("Utilisateur: "):
            return assoc[12:]  # Enlève "Utilisateur: "
        return assoc

    def has_permission(self, guild_id: int, user_id: int, command_name: str, user_roles: list = None) -> bool:
        """Vérifie si un utilisateur a accès à une commande spécifique en utilisant la hiérarchie, avec logs détaillés"""
        print(f"[DEBUG] has_permission appelé: guild_id={guild_id}, user_id={user_id}, command_name={command_name}")
        permissions_data = self.load_server_permissions(guild_id)
        print(f"[DEBUG] Permissions chargées: {permissions_data}")

        # Récupérer toutes les permissions auxquelles l'utilisateur a accès directement
        direct_permissions = set()
        for i in range(1, TOTAL_PERMISSIONS + 1):
            perm_data = permissions_data.get(str(i), {"associations": []})
            associations = perm_data.get("associations", [])
            print(f"[DEBUG] Permission {i}: associations={associations}")
            for assoc in associations:
                if assoc.startswith("Utilisateur: "):
                    user_mention = assoc[12:]
                    print(f"[DEBUG] Comparaison utilisateur: mention={user_mention} vs user_id={user_id}")
                    if user_mention.startswith('<@') and user_mention.endswith('>'):
                        try:
                            clean_mention = user_mention
                            for char in ['<', '>', '@', '!']:
                                clean_mention = clean_mention.replace(char, '')
                            print(f"[DEBUG] ID extrait: {clean_mention}")
                            if int(clean_mention) == user_id:
                                direct_permissions.add(str(i))
                                print(f"[DEBUG] Utilisateur {user_id} trouvé dans permission {i}")
                                break
                        except ValueError:
                            print(f"[DEBUG] Erreur conversion ID utilisateur: {user_mention}")
                            pass

        # Vérifier les permissions par rôle
        role_permissions = set()
        if user_roles:
            print(f"[DEBUG] Vérification des rôles utilisateur: {[role.id for role in user_roles]}")
            for i in range(1, TOTAL_PERMISSIONS + 1):
                perm_data = permissions_data.get(str(i), {"associations": []})
                associations = perm_data.get("associations", [])
                allowed_role_ids = set()
                for assoc in associations:
                    if assoc.startswith("Rôle: "):
                        role_mention = assoc[6:]
                        print(f"[DEBUG] Comparaison rôle: mention={role_mention}")
                        if role_mention.startswith('<@&') and role_mention.endswith('>'):
                            try:
                                clean_mention = role_mention
                                for char in ['<', '>', '@', '&']:
                                    clean_mention = clean_mention.replace(char, '')
                                print(f"[DEBUG] ID rôle extrait: {clean_mention}")
                                allowed_role_ids.add(int(clean_mention))
                            except ValueError:
                                print(f"[DEBUG] Erreur conversion ID rôle: {role_mention}")
                                pass
                user_role_ids = {role.id for role in user_roles}
                print(f"[DEBUG] Rôles utilisateur: {user_role_ids}, rôles autorisés: {allowed_role_ids}")
                if len(user_role_ids.intersection(allowed_role_ids)) > 0:
                    role_permissions.add(str(i))
                    print(f"[DEBUG] Rôle trouvé pour permission {i}")

        user_permissions = direct_permissions.union(role_permissions)
        print(f"[DEBUG] Permissions utilisateur directes: {direct_permissions}")
        print(f"[DEBUG] Permissions utilisateur par rôle: {role_permissions}")
        print(f"[DEBUG] Permissions utilisateur combinées: {user_permissions}")

        extended_permissions = set()
        for perm in user_permissions:
            if perm in PERMISSION_HIERARCHY:
                extended_permissions.update(PERMISSION_HIERARCHY[perm])
                print(f"[DEBUG] Permission {perm} étendue à: {PERMISSION_HIERARCHY[perm]}")

        print(f"[DEBUG] Permissions étendues: {extended_permissions}")

        for perm in extended_permissions:
            perm_data = permissions_data.get(perm, {"commandes": "Aucune"})
            commandes = perm_data.get("commandes", "Aucune")
            print(f"[DEBUG] Vérification permission {perm}: commandes={commandes}")
            if commandes != "Aucune":
                if "|" in commandes:
                    cmd_list = [cmd.strip() for cmd in commandes.split("|")]
                else:
                    cmd_list = [cmd.strip() for cmd in commandes.split(",")]
                print(f"[DEBUG] Commandes dans permission {perm}: {cmd_list}")
                if command_name in cmd_list:
                    print(f"[DEBUG] Commande {command_name} trouvée dans permission {perm} - ACCÈS AUTORISÉ")
                    return True

        print(f"[DEBUG] Commande {command_name} non trouvée - ACCÈS REFUSÉ")
        return False

    def check_user_permissions(self, guild: discord.Guild, user: discord.Member) -> list:
        """Retourne la liste des permissions auxquelles un utilisateur a accès"""
        user_permissions = []
        
        for i in range(1, TOTAL_PERMISSIONS + 1):
            # Pour vérifier l'accès à une permission spécifique, on utilise le nom de la permission
            if self.has_permission(guild.id, user.id, f"permission_{i}", user.roles):
                user_permissions.append(str(i))
        
        return user_permissions
    
    def get_associations_by_type(self, associations: list) -> tuple:
        """Sépare les associations par type (rôles et utilisateurs)"""
        roles = []
        users = []
        
        for assoc in associations:
            if assoc.startswith("Rôle:"):
                roles.append(assoc)
            elif assoc.startswith("Utilisateur:"):
                users.append(assoc)
        
        return roles, users

    @commands.hybrid_command(name="perm", description="Affiche les permissions disponibles avec un sélecteur")
    @commands.is_owner()
    async def perm(self, ctx):
        """Affiche un embed avec un sélecteur pour choisir une permission"""
        print(f"[DEBUG] Commande perm appelée par {ctx.author}")
        
        # Vérification supplémentaire que l'utilisateur est bien l'owner
        if ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ Seul le propriétaire du serveur peut utiliser cette commande.", ephemeral=True)
            return
        
        if not self.config_manager:
            print("[ERROR] Config manager non disponible")
            await ctx.send("❌ Config manager non disponible")
            return
            
        try:
            # Créer la description avec les permissions configurées uniquement
            description = ""
            configured_perms = 0
            
            # Charger les permissions depuis le fichier du serveur
            permissions_data = self.load_server_permissions(ctx.guild.id)
            
            for i in range(1, TOTAL_PERMISSIONS + 1):
                perm_key = str(i)
                perm_data = permissions_data.get(perm_key, {"associations": [], "commandes": "Aucune"})
                associations = perm_data.get("associations", [])
                commandes = perm_data.get("commandes", "Aucune")
                
                # Vérifier si la permission est configurée
                is_configured = len(associations) > 0 or commandes != "Aucune"
                
                # N'afficher que les permissions configurées
                if is_configured:
                    configured_perms += 1
                    
                    # Séparer les associations par type
                    roles, users = self.get_associations_by_type(associations)
                    
                    # Ajouter l'emoji de numérotation
                    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
                    number_emoji = number_emojis[i-1] if i <= len(number_emojis) else f"#{i}"
                    
                    description += f"**{number_emoji} Permission {i}**\n"
                    description += f"└ 🔹 **{self.get_plural_label(len(users), 'Utilisateur Associé', 'Utilisateurs Associés')}** ({len(users)}/{MAX_USERS}) : "
                    
                    if users:
                        # Afficher tous les utilisateurs sans préfixe avec séparation par |
                        formatted_users = [self.format_association_name(user) for user in users]
                        description += " | ".join(formatted_users)
                    else:
                        description += "Aucun"
                    
                    description += f"\n└ 🔹 **{self.get_plural_label(len(roles), 'Rôle Associé', 'Rôles Associés')}** ({len(roles)}/{MAX_ROLES}) : "
                    
                    if roles:
                        # Afficher tous les rôles sans préfixe avec séparation par |
                        formatted_roles = [self.format_association_name(role) for role in roles]
                        description += " | ".join(formatted_roles)
                    else:
                        description += "Aucun"
                    
                    # Formater les commandes avec des backticks
                    if perm_data['commandes'] != "Aucune":
                        # Séparer les commandes et les formater
                        if "|" in perm_data['commandes']:
                            cmd_list = [cmd.strip() for cmd in perm_data['commandes'].split("|")]
                        else:
                            cmd_list = [cmd.strip() for cmd in perm_data['commandes'].split(",")]
                        
                        formatted_commands = [f"`{cmd}`" for cmd in cmd_list if cmd.strip()]
                        commandes_display = " | ".join(formatted_commands)
                    else:
                        commandes_display = "Aucune"
                    
                    description += f"\n└ 🔸 **{self.get_plural_label(1 if perm_data['commandes'] != 'Aucune' else 0, 'Commande', 'Commandes')}** : {commandes_display}\n\n"
            
            # Si aucune permission n'est configurée
            if configured_perms == 0:
                # Importer le message depuis le fichier no_perm.txt
                with open(os.path.join(os.path.dirname(__file__), 'no_perm.txt'), 'r', encoding='utf-8') as f:
                    description = f.read()
            
            embed = create_embed(
                guild=ctx.guild,
                user=ctx.author,
                bot=self.bot,
                title="🔐 Permissions",
                description=description
            )
            print("[DEBUG] Embed créé avec succès")
            
            view = PermView(self, ctx)
            await ctx.send(embed=embed, view=view)
            print("[DEBUG] Embed et vue envoyés avec succès")
        except Exception as e:
            print(f"[ERROR] Erreur lors de la création/envoi de l'embed: {e}")
            await ctx.send(f"❌ Erreur: {e}")

async def setup(bot):
    await bot.add_cog(Perm(bot))
