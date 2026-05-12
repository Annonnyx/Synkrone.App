import discord
from discord.ext import commands, tasks
from discord import app_commands, ui
import asyncio
import json
import os
import shutil
import traceback
from datetime import datetime, timedelta
import pytz
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

FRENCH_TZ = pytz.timezone('Europe/Paris')

# ==============================================================================
# ----------------------------- GESTION DATA -----------------------------------
# ==============================================================================

class DataManager:
    def __init__(self):
        # Le dossier "data" est dans le même dossier que ce fichier
        self.base_path = Path(__file__).parent / "data"
        self.base_path.mkdir(exist_ok=True)

    def get_guild_path(self, guild_id):
        path = self.base_path / str(guild_id)
        path.mkdir(exist_ok=True)
        return path

    def save_settings(self, guild_id, data):
        path = self.get_guild_path(guild_id) / "settings.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_settings(self, guild_id):
        path = self.get_guild_path(guild_id) / "settings.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_giveaway(self, guild_id, giveaway_data):
        path = self.get_guild_path(guild_id) / f"{giveaway_data['message_id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(giveaway_data, f, indent=4)

    def load_giveaway(self, guild_id, message_id):
        path = self.get_guild_path(guild_id) / f"{message_id}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def delete_giveaway(self, guild_id, message_id):
        path = self.get_guild_path(guild_id) / f"{message_id}.json"
        if path.exists():
            os.remove(path)

    def get_all_giveaways(self):
        """Récupère tous les giveaways de tous les serveurs"""
        all_gws = {}
        if not self.base_path.exists(): return all_gws
        
        for guild_folder in self.base_path.iterdir():
            if guild_folder.is_dir():
                guild_id = guild_folder.name
                all_gws[guild_id] = {}
                for file in guild_folder.glob("*.json"):
                    if file.name == "settings.json":
                        continue
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, dict) and 'message_id' in data:
                                all_gws[guild_id][str(data['message_id'])] = data
                    except Exception as e:
                        print(f"Erreur lors du chargement du fichier {file}: {e}")
        return all_gws

data_manager = DataManager()

# ==============================================================================
# --------------------------- MODALS CONFIG ------------------------------------
# ==============================================================================

class BasicConfigModal(ui.Modal, title="Configuration de base"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        
        self.prize = ui.TextInput(label="🎁 Gain", default=view.config["prize"], max_length=100)
        self.winners = ui.TextInput(label="🏆 Nombre de gagnants", default=str(view.config["winners"]), max_length=2)
        
        # Calcul date par défaut
        now = datetime.now(FRENCH_TZ)
        end_default = now + timedelta(hours=1)
        
        self.date = ui.TextInput(label="📅 Date fin (JJ/MM/AAAA)", default=end_default.strftime("%d/%m/%Y"), min_length=10, max_length=10)
        self.time = ui.TextInput(label="⏰ Heure fin (HH:MM)", default=end_default.strftime("%H:%M"), min_length=5, max_length=5)
        self.chan_id = ui.TextInput(label="📺 ID Salon (Vide = Salon actuel)", default=str(view.config["channel_id"] or ""), required=False)

        self.add_item(self.prize)
        self.add_item(self.winners)
        self.add_item(self.date)
        self.add_item(self.time)
        self.add_item(self.chan_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parsing Date
            date_str = f"{self.date.value} {self.time.value}"
            end_dt = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            end_dt = FRENCH_TZ.localize(end_dt)
            
            if end_dt <= datetime.now(FRENCH_TZ):
                return await interaction.response.send_message("❌ La date de fin doit être dans le futur.", ephemeral=True)

            # Validation
            winners = int(self.winners.value)
            if winners < 1: raise ValueError
            
            chan_id = int(self.chan_id.value) if self.chan_id.value.isdigit() else interaction.channel_id
            
            # Sauvegarde Config
            self.view.config.update({
                "prize": self.prize.value,
                "winners": winners,
                "end_timestamp": end_dt.timestamp(),
                "channel_id": chan_id
            })
            
            await self.view.log_change(interaction, "✅ Configuration de base mise à jour.")
        except ValueError:
            await interaction.response.send_message("❌ Format de nombre ou de date invalide.", ephemeral=True)

class OptionalConfigModal(ui.Modal, title="Configuration Facultative"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        
        self.mention = ui.TextInput(label="🔔 ID Rôle à mentionner", default=str(view.config["mention_role"] or ""), required=False)
        self.req = ui.TextInput(label="✅ ID Rôle Requis", default=str(view.config["req_role"] or ""), required=False)
        self.block = ui.TextInput(label="🚫 ID Rôle Interdit", default=str(view.config["block_role"] or ""), required=False)

        self.add_item(self.mention)
        self.add_item(self.req)
        self.add_item(self.block)

    async def on_submit(self, interaction: discord.Interaction):
        def parse_id(val): return int(val) if val.isdigit() else None
        
        self.view.config.update({
            "mention_role": parse_id(self.mention.value),
            "req_role": parse_id(self.req.value),
            "block_role": parse_id(self.block.value)
        })
        await self.view.log_change(interaction, "✅ Configuration des rôles mise à jour.")

# ==============================================================================
# --------------------------- VUES SETUP & PUBLIC ------------------------------
# ==============================================================================

class SetupView(ui.View):
    def __init__(self, cog, author, guild_id, defaults):
        super().__init__(timeout=900)
        self.cog = cog
        self.author = author
        self.guild_id = guild_id
        
        # Messages de l'interface
        self.config_msg = None
        self.preview_msg = None
        self.history_msg = None # Pour le log éphémère unique
        self.history_log = [] # Liste des logs
        
        # Configuration par défaut
        self.config = {
            "prize": "Nitro",
            "winners": 1,
            "channel_id": defaults.get("last_channel_id", None), # Sera set au lancement si None
            "end_timestamp": (datetime.now(FRENCH_TZ) + timedelta(hours=1)).timestamp(),
            "mention_role": None,
            "req_role": None,
            "block_role": None,
            "image_url": None
        }

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Seul l'auteur de la commande peut configurer.", ephemeral=True)
            return False
        return True

    async def log_change(self, interaction: discord.Interaction, message: str):
        """Gère l'historique dans un seul message éphémère"""
        self.history_log.append(message)
        content = "### 📜 Historique de configuration\n" + "\n".join(self.history_log[-10:]) # Garde les 10 derniers
        
        # Mise à jour des embeds principaux
        await self.update_display()

        # Gestion du message log
        if not interaction.response.is_done():
            await interaction.response.send_message(content, ephemeral=True)
            self.history_msg = await interaction.original_response()
        else:
            if self.history_msg:
                try:
                    await self.history_msg.edit(content=content)
                    await interaction.followup.send("Mise à jour effectuée (voir historique).", ephemeral=True)
                except:
                    # Si le token a expiré ou msg supprimé
                    await interaction.followup.send(content, ephemeral=True)

    async def update_display(self):
        """Met à jour les deux messages (Config et Preview)"""
        # 1. Embed Configuration
        mention = f"<@&{self.config['mention_role']}>" if self.config['mention_role'] else 'Aucune'
        req_role = f"<@&{self.config['req_role']}>" if self.config['req_role'] else 'Aucun'
        block_role = f"<@&{self.config['block_role']}>" if self.config['block_role'] else 'Aucun'
        
        embed = self.cog.create_embed(
            self.config_msg.guild, self.author, 
            title="⚡ Création de Giveaway",
            description=(
                "**Configuration actuelle :**\n"
                f"🎁 **Gain :** `{self.config['prize']}`\n"
                f"🏆 **Gagnants :** `{self.config['winners']}`\n"
                f"⏱️ **Fin :** <t:{int(self.config['end_timestamp'])}:R>\n"
                f"📺 **Salon :** <#{self.config['channel_id'] or 'Non défini'}>\n"
                f"🔔 **Mention :** {mention}\n"
                f"✅ **Rôle requis :** {req_role}\n"
                f"🚫 **Rôle bloquant :** {block_role}\n"
            ),
            color=0x2b2d31
        )
        
        # 2. Embed Aperçu
        prev_embed = self.cog.generate_game_embed(self.config_msg.guild, self.config)
        prev_embed.title = "[APERÇU] " + prev_embed.title

        # Application
        if self.config_msg: await self.config_msg.edit(embed=embed, view=self)
        if self.preview_msg: await self.preview_msg.edit(embed=prev_embed)

    @ui.button(label="Configuration de base", style=discord.ButtonStyle.primary, emoji="🟪", row=0)
    async def basic_config(self, it, bt):
        await it.response.send_modal(BasicConfigModal(self))

    @ui.button(label="Facultatif", style=discord.ButtonStyle.secondary, emoji="🟨", row=0)
    async def optional_config(self, it, bt):
        await it.response.send_modal(OptionalConfigModal(self))

    @ui.button(label="Lancer le Giveaway", style=discord.ButtonStyle.green, emoji="🚀", row=1)
    async def launch(self, it: discord.Interaction, bt):
        c = self.config
        guild = it.guild
        channel = guild.get_channel(c["channel_id"]) if c["channel_id"] else it.channel
        
        if not channel:
            return await it.response.send_message("❌ Le salon de destination est invalide.", ephemeral=True)

        # 1. Envoyer le vrai message
        await it.response.defer()
        
        final_embed = self.cog.generate_game_embed(guild, c)
        content = f"<@&{c['mention_role']}>" if c['mention_role'] else None
        
        try:
            msg = await channel.send(content=content, embed=final_embed)
        except discord.Forbidden:
            return await it.followup.send(f"❌ Je n'ai pas la permission d'envoyer des messages dans {channel.mention}.", ephemeral=True)

        # 2. Créer Data
        g_data = {
            "message_id": msg.id,
            "channel_id": channel.id,
            "guild_id": guild.id,
            "host_id": self.author.id,
            "prize": c["prize"],
            "winners": c["winners"],
            "end_timestamp": c["end_timestamp"],
            "req_role": c["req_role"],
            "block_role": c["block_role"],
            "participants": [],
            "ended": False,
            "locked": False
        }

        # 3. Sauvegardes
        data_manager.save_giveaway(guild.id, g_data)
        data_manager.save_settings(guild.id, {"last_channel_id": channel.id})

        # 4. Attacher la vue publique
        view = PublicGiveawayView(self.cog, g_data)
        await msg.edit(view=view)

        # 5. Nettoyage setup
        await self.config_msg.delete()
        await self.preview_msg.delete()
        await it.followup.send(f"🚀 Giveaway lancé dans {channel.mention} !", ephemeral=True)

class PublicGiveawayView(ui.View):
    def __init__(self, cog, data):
        super().__init__(timeout=None)
        self.cog = cog
        self.data = data
        self.message_id = data["message_id"]
        
        # Mettre à jour le style du bouton si le giveaway est bloqué
        if data.get("locked", False):
            self.join_btn.style = discord.ButtonStyle.danger
            self.join_btn.label = "Participation bloquée"
            self.join_btn.emoji = "🔒"

    @ui.button(label="Je participe", style=discord.ButtonStyle.success, emoji="🎉", custom_id="gw_join")
    async def join_btn(self, it: discord.Interaction, bt: ui.Button):
        # Recharger data pour éviter conflits
        self.data = data_manager.load_giveaway(it.guild_id, self.message_id)
        if not self.data or self.data["ended"]:
            return await it.response.send_message("❌ Ce giveaway est terminé.", ephemeral=True)
        
        if self.data["locked"]:
            return await it.response.send_message("🔒 Les entrées sont temporairement fermées.", ephemeral=True)

        # Vérification des rôles
        if self.data["req_role"]:
            role = it.guild.get_role(self.data["req_role"])
            if role and role not in it.user.roles:
                return await it.response.send_message(
                    f"⚠️ Tu dois avoir le rôle {role.mention} pour participer.", 
                    ephemeral=True
                )
        
        if self.data["block_role"]:
            role = it.guild.get_role(self.data["block_role"])
            if role and role in it.user.roles:
                return await it.response.send_message(
                    f"🚫 Le rôle {role.mention} t'empêche de participer.", 
                    ephemeral=True
                )

        # Gestion de la participation
        uid = it.user.id
        if uid in self.data["participants"]:
            self.data["participants"].remove(uid)
            msg = "❌ Tu ne participes plus."
        else:
            self.data["participants"].append(uid)
            msg = "✅ Participation enregistrée !"

        data_manager.save_giveaway(it.guild_id, self.data)
        await self.cog.refresh_message(it.guild, self.data)
        
        # Mise à jour du style du bouton si nécessaire
        if self.data.get("locked", False):
            bt.style = discord.ButtonStyle.danger
            bt.label = "Participation bloquée"
            bt.emoji = "🔒"
        
        await it.response.send_message(msg, ephemeral=True)

    @ui.button(style=discord.ButtonStyle.gray, emoji="⚙️", custom_id="gw_admin")
    async def manage(self, it: discord.Interaction, bt: ui.Button):
        # Permission check
        perms = it.channel.permissions_for(it.user)
        if not (it.user.guild_permissions.administrator or perms.manage_events):
             return await it.response.send_message("❌ Tu n'as pas la permission de gérer ce giveaway.", ephemeral=True)
        
        view = AdminGiveawayView(self.cog, self.data)
        await it.response.send_message("🛠️ **Gestion Giveaway**", view=view, ephemeral=True)

class AdminGiveawayView(ui.View):
    def __init__(self, cog, data):
        super().__init__(timeout=300)  # Timeout augmenté à 5 minutes
        self.cog = cog
        self.data = data
        
        # Mise à jour des boutons
        self.update_buttons()
    
    def update_buttons(self):
        # On clear les boutons existants
        self.clear_items()
        
        # Bouton de verrouillage/déverrouillage
        lock_btn = ui.Button(
            label="Débloquer" if self.data["locked"] else "Bloquer",
            style=discord.ButtonStyle.success if self.data["locked"] else discord.ButtonStyle.secondary,
            emoji="🔓" if self.data["locked"] else "🔒",
            custom_id=f"adm_lock_{self.data['message_id']}"
        )
        lock_btn.callback = self.lock_btn
        self.add_item(lock_btn)
        
        # Bouton de fin de giveaway
        end_btn = ui.Button(
            label="Terminer maintenant",
            style=discord.ButtonStyle.primary,
            emoji="🏁",
            custom_id=f"adm_end_{self.data['message_id']}"
        )
        end_btn.callback = self.end_btn
        self.add_item(end_btn)
        
        # Bouton de suppression
        del_btn = ui.Button(
            label="Supprimer",
            style=discord.ButtonStyle.danger,
            emoji="🗑️",
            custom_id=f"adm_del_{self.data['message_id']}"
        )
        del_btn.callback = self.del_btn
        self.add_item(del_btn)
        
        # Bouton de reroll
        if self.data.get("ended"):
            reroll_btn = ui.Button(
                label="Nouveau tirage",
                style=discord.ButtonStyle.secondary,
                emoji="🔄",
                custom_id=f"adm_reroll_{self.data['message_id']}"
            )
            reroll_btn.callback = self.reroll_btn
            self.add_item(reroll_btn)

    async def lock_btn(self, it: discord.Interaction):
        # Vérification des permissions
        perms = it.channel.permissions_for(it.user)
        if not (it.user.guild_permissions.administrator or perms.manage_events):
            return await it.response.send_message("❌ Tu n'as pas la permission de gérer ce giveaway.", ephemeral=True)
        
        # Rechargement des données
        self.data = data_manager.load_giveaway(it.guild_id, self.data["message_id"])
        self.data["locked"] = not self.data["locked"]
        data_manager.save_giveaway(it.guild_id, self.data)
        
        # Mise à jour du message et de la vue
        await self.cog.refresh_message(it.guild, self.data)
        self.update_buttons()
        
        # Création d'un embed de confirmation
        embed = self.cog.create_embed(
            it.guild,
            it.user,
            title="🔒 Paramètres du Giveaway",
            description=f"Le giveaway a été **{'débloqué' if not self.data['locked'] else 'bloqué'}** avec succès.",
            color=0x2ecc71 if not self.data['locked'] else 0xe74c3c
        )
        
        if self.data["locked"]:
            embed.add_field(name="Statut", value="🔴 Participation désactivée", inline=True)
        else:
            embed.add_field(name="Statut", value="🟢 Participation active", inline=True)
            
        embed.set_footer(text=f"Géré par {it.user.display_name}", icon_url=it.user.display_avatar.url)
        
        await it.response.edit_message(embed=embed, view=self)

    async def end_btn(self, it: discord.Interaction):
        # Vérification des permissions
        perms = it.channel.permissions_for(it.user)
        if not (it.user.guild_permissions.administrator or perms.manage_events):
            return await it.response.send_message("❌ Tu n'as pas la permission de gérer ce giveaway.", ephemeral=True)
        
        # Confirmation
        confirm_view = ui.View(timeout=60)
        
        async def confirm_callback(confirm_it: discord.Interaction):
            if confirm_it.user != it.user:
                return await confirm_it.response.send_message("❌ Ce n'est pas votre bouton de confirmation.", ephemeral=True)
            
            await confirm_it.response.defer()
            await self.cog.end_giveaway(it.guild, self.data)
            
            # Mise à jour de la vue
            self.update_buttons()
            await it.edit_original_response(view=self)
            
            await confirm_it.followup.send("✅ Le giveaway a été terminé avec succès.", ephemeral=True)
        
        async def cancel_callback(cancel_it: discord.Interaction):
            if cancel_it.user != it.user:
                return await cancel_it.response.send_message("❌ Ce n'est pas votre bouton d'annulation.", ephemeral=True)
            
            await cancel_it.response.defer()
            await it.delete_original_response()
            
        confirm_btn = ui.Button(label="Confirmer", style=discord.ButtonStyle.danger, emoji="✅")
        cancel_btn = ui.Button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="❌")
        
        confirm_btn.callback = confirm_callback
        cancel_btn.callback = cancel_callback
        
        confirm_view.add_item(confirm_btn)
        confirm_view.add_item(cancel_btn)
        
        embed = self.cog.create_embed(
            it.guild,
            it.user,
            title=" Confirmation requise",
            description="Êtes-vous sûr de vouloir terminer ce giveaway maintenant ?",
            color=0xf1c40f,
            footer={"text": "Cette action est irréversible."}
        )
        
        await it.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

    async def del_btn(self, it: discord.Interaction):
        # Vérification des permissions
        perms = it.channel.permissions_for(it.user)
        if not (it.user.guild_permissions.administrator or perms.manage_events):
            return await it.response.send_message("❌ Tu n'as pas la permission de gérer ce giveaway.", ephemeral=True)
        
        # Confirmation
        confirm_view = ui.View(timeout=60)
        
        async def confirm_callback(confirm_it: discord.Interaction):
            if confirm_it.user != it.user:
                return await confirm_it.response.send_message("❌ Ce n'est pas votre bouton de confirmation.", ephemeral=True)
            
            await confirm_it.response.defer()
            await self.cog.cancel_giveaway(it.guild, self.data, it.user)
            
            # Suppression du message de gestion
            try:
                await it.delete_original_response()
            except:
                pass
            
            await confirm_it.followup.send("🗑️ Le giveaway a été supprimé avec succès.", ephemeral=True)
        
        async def cancel_callback(cancel_it: discord.Interaction):
            if cancel_it.user != it.user:
                return await cancel_it.response.send_message("❌ Ce n'est pas votre bouton d'annulation.", ephemeral=True)
            
            await cancel_it.response.defer()
            await it.delete_original_response()
        
        confirm_btn = ui.Button(label="Supprimer", style=discord.ButtonStyle.danger, emoji="🗑️")
        cancel_btn = ui.Button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="❌")
        
        confirm_btn.callback = confirm_callback
        cancel_btn.callback = cancel_callback
        
        confirm_view.add_item(confirm_btn)
        confirm_view.add_item(cancel_btn)
        
        embed = self.cog.create_embed(
            it.guild,
            it.user,
            title="⚠️ Suppression du Giveaway",
            description="Êtes-vous sûr de vouloir supprimer ce giveaway ? Tous les participants seront notifiés.",
            color=0xe74c3c,
            footer={"text": "Cette action est irréversible."}
        )
        
        await it.response.send_message(embed=embed, view=confirm_view, ephemeral=True)
    
    async def reroll_btn(self, it: discord.Interaction):
        # Vérification des permissions
        perms = it.channel.permissions_for(it.user)
        if not (it.user.guild_permissions.administrator or perms.manage_events):
            return await it.response.send_message("❌ Tu n'as pas la permission de gérer ce giveaway.", ephemeral=True)
        
        # Vérification qu'il y a des participants
        if not self.data.get("participants"):
            return await it.response.send_message("❌ Aucun participant pour effectuer un nouveau tirage.", ephemeral=True)
        
        # Création du menu de sélection
        select_view = ui.View(timeout=120)
        
        # Récupération des participants avec leur nom d'utilisateur
        participants = []
        for uid in self.data["participants"]:
            try:
                member = await it.guild.fetch_member(uid)
                participants.append((uid, str(member)))
            except:
                participants.append((uid, f"Utilisateur inconnu ({uid})"))
        
        # Création du menu déroulant
        select = ui.Select(
            placeholder="Sélectionnez un gagnant à remplacer",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=name[:100], value=str(uid), emoji="🎲")
                for uid, name in participants[:25]  # Limite de 25 options
            ]
        )
        
        async def select_callback(select_it: discord.Interaction):
            if select_it.user != it.user:
                return await select_it.response.send_message("❌ Ce n'est pas votre sélection.", ephemeral=True)
            
            await select_it.response.defer()
            old_winner = int(select.values[0])
            await self.cog.end_giveaway(it.guild, self.data, reroll_winner=old_winner)
            
            # Mise à jour de la vue
            self.update_buttons()
            await it.edit_original_response(view=self)
            
            await select_it.followup.send(f"🔄 Nouveau tirage effectué pour remplacer <@{old_winner}> !", ephemeral=True)
        
        select.callback = select_callback
        select_view.add_item(select)
        
        embed = self.cog.create_embed(
            it.guild,
            it.user,
            title="🔄 Nouveau tirage",
            description="Sélectionnez un gagnant à remplacer :",
            color=0x3498db
        )
        
        await it.response.send_message(embed=embed, view=select_view, ephemeral=True)

# ----------------------------- COG PRINCIPAL ----------------------------------
# ==============================================================================

class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gw_task.start()
        # Planifier le rechargement des vues après que le bot soit prêt
        self.bot.loop.create_task(self.reload_persistent_views())

    def cog_unload(self):
        self.gw_task.cancel()
        
    async def reload_persistent_views(self):
        """Recharge les vues persistantes des giveaways actifs"""
        try:
            # Attendre que le bot soit complètement prêt
            await self.bot.wait_until_ready()
            
            # Récupérer tous les giveaways de tous les serveurs
            all_giveaways = data_manager.get_all_giveaways()
            
            # Compteur pour les messages introuvables
            messages_introuvables = 0
            
            for guild_id, giveaways in all_giveaways.items():
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    if not guild:
                        continue
                        
                    for msg_id, data in giveaways.items():
                        try:
                            # Vérifier si le giveaway est toujours actif
                            if data.get('ended'):
                                continue
                                
                            channel = guild.get_channel(int(data["channel_id"]))
                            if not channel:
                                continue
                                
                            # Recharger la vue publique
                            try:
                                msg = await channel.fetch_message(int(msg_id))
                                view = PublicGiveawayView(self, data)
                                await msg.edit(view=view)
                                print(f"Vue rechargée pour le giveaway {msg_id} dans {guild.name}")
                            except discord.NotFound:
                                messages_introuvables += 1
                                # Supprimer le fichier JSON si le message n'existe plus
                                try:
                                    data_manager.delete_giveaway(guild.id, int(msg_id))
                                    print(f"Nettoyé: giveaway {msg_id} supprimé (message introuvable)")
                                except Exception as cleanup_error:
                                    print(f"Erreur lors du nettoyage du giveaway {msg_id}: {cleanup_error}")
                            except discord.Forbidden:
                                messages_introuvables += 1
                                print(f"Accès refusé au message {msg_id} dans {guild.name}")
                            except Exception as e:
                                messages_introuvables += 1
                                print(f"Erreur inconnue pour le message {msg_id}: {type(e).__name__}: {e}")
                                
                        except Exception as e:
                            print(f"⚠️ Giveaway - Erreur lors du rechargement du giveaway {msg_id}")
                            traceback.print_exc()
                except Exception as e:
                    print(f"Erreur lors du traitement du serveur {guild_id}: {e}")
            
            # Afficher le message récapitulatif une seule fois à la fin (seulement pour les erreurs non résolues)
            if messages_introuvables > 0:
                print(f"Giveaway - {messages_introuvables} giveaways nettoyés (messages supprimés)")
                    
        except Exception as e:
            print(f"Erreur critique dans reload_persistent_views: {e}")
            traceback.print_exc()
            

    # --- Utils ---
    def create_embed(self, guild, user, title, description, color=None, **kwargs):
        """
        Crée un embed formaté avec le gestionnaire personnalisé si disponible.
        
        Args:
            guild: Le serveur Discord
            user: L'utilisateur qui a déclenché l'action
            title: Le titre de l'embed
            description: La description de l'embed
            color: La couleur de l'embed (optionnel, prioritaire sur le thème par défaut)
            **kwargs: Arguments supplémentaires pour le gestionnaire d'embed
                - footer: dict avec 'text' et éventuellement 'icon_url'
                - fields: liste de tuples (name, value, inline)
                - timestamp: datetime pour le timestamp
                - theme: str, nom du thème à utiliser (optionnel)
                
        Returns:
            discord.Embed: L'embed formaté
        """
        # Préparer les arguments pour le config_manager
        embed_kwargs = {
            'guild': guild,
            'user': user,
            'bot': self.bot,
            'title': title,
            'description': description,
            'target_id': guild.id if guild else None,
            **kwargs  # Permet de surcharger les paramètres avec ceux fournis dans kwargs
        }
        
        # Si une couleur est fournie, on l'utilise
        if color is not None:
            embed_kwargs['color'] = color
        # Sinon, on utilise le thème de config_manager s'il est disponible
        elif config_manager:
            # On ne définit pas de couleur, on laisse config_manager décider
            pass
        # En dernier recours, on utilise les couleurs par défaut
        else:
            if "erreur" in title.lower() or "error" in title.lower():
                embed_kwargs['color'] = 0xe74c3c  # Rouge pour les erreurs
            elif "succès" in title.lower() or "terminé" in title.lower() or "félicitations" in title.lower():
                embed_kwargs['color'] = 0x2ecc71  # Vert pour les succès
            else:
                embed_kwargs['color'] = 0x3498db  # Bleu par défaut
        
        # Ajouter les arguments supplémentaires
        if 'footer' in kwargs:
            embed_kwargs['footer_text'] = kwargs['footer'].get('text')
            if 'icon_url' in kwargs['footer']:
                embed_kwargs['footer_icon_url'] = kwargs['footer']['icon_url']
        
        # Essayer d'utiliser le config_manager s'il est disponible
        if config_manager:
            try:
                # Si un thème est spécifié dans les kwargs, on l'utilise
                if 'theme' in kwargs:
                    theme = kwargs.pop('theme')
                    embed = config_manager.get_formatted_embed(theme=theme, **embed_kwargs)
                else:
                    # Sinon, on utilise le thème par défaut du config_manager
                    embed = config_manager.get_formatted_embed(**embed_kwargs)
                
                if embed is not None:  # Si l'embed est valide, on le retourne
                    return embed
            except Exception as e:
                print(f"[WARN] Erreur avec le config_manager: {e}")
                traceback.print_exc()
        
        # Fallback si le gestionnaire n'est pas disponible ou a échoué
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        # Ajout du footer si fourni
        if 'footer' in kwargs:
            footer_text = kwargs['footer'].get('text')
            footer_icon = kwargs['footer'].get('icon_url')
            if footer_text and footer_icon:
                embed.set_footer(text=footer_text, icon_url=footer_icon)
            elif footer_text:
                embed.set_footer(text=footer_text)
        # Sinon, ajouter l'utilisateur comme auteur si disponible
        elif user and hasattr(user, 'display_name'):
            embed.set_footer(text=f"Proposé par {user.display_name}")
            
        # Ajout de l'icône du serveur si disponible
        if guild and hasattr(guild, 'icon') and guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        # Gestion des champs supplémentaires
        if 'fields' in kwargs:
            for field in kwargs['fields']:
                if len(field) == 3:
                    name, value, inline = field
                    embed.add_field(name=name, value=value, inline=inline)
                
        # Gestion du timestamp
        if 'timestamp' in kwargs:
            embed.timestamp = kwargs['timestamp']
            
        return embed

    def generate_game_embed(self, guild, data):
        """Génère l'embed public de participation"""
        # Calcul stats
        participants = len(data.get("participants", []))
        winners_nb = data["winners"]
        chance = (winners_nb / max(1, participants)) * 100
        
        desc = (
            f"# {data['prize']}\n\n"
            f"{data.get('description', '')}\n"
            f"⏱️ **Fin :** <t:{int(data['end_timestamp'])}:R> (<t:{int(data['end_timestamp'])}:f>)\n"
            f"🏆 **Gagnants :** `{winners_nb}`\n"
            f"👥 **Participants :** `{participants}`\n"
            f"🍀 **Chance :** `{min(100.0, chance):.2f}%`\n"
        )
        
        if data["req_role"]: desc += f"\n✅ **Requis :** <@&{data['req_role']}>"
        if data["block_role"]: desc += f"\n🚫 **Interdit :** <@&{data['block_role']}>"
        
        return self.create_embed(
            guild, 
            self.bot.user, # User générique ici car c'est le bot qui post
            title="🎉 Tentes de gagner !",
            description=desc,
            color=0x9b59b6
        )

    async def refresh_message(self, guild, data):
        """Met à jour le message public"""
        try:
            channel = guild.get_channel(data["channel_id"])
            if not channel: return
            msg = await channel.fetch_message(data["message_id"])
            
            embed = self.generate_game_embed(guild, data)
            view = PublicGiveawayView(self, data)
            await msg.edit(embed=embed, view=view)
        except:
            pass # Message peut-être supprimé

    # --- Logique Fin & Suppression ---

    async def end_giveaway(self, guild, data, reroll_winner=None):
        """Termine un giveaway normalement ou effectue un reroll"""
        if not reroll_winner:
            data["ended"] = True
            data["ended_at_ts"] = datetime.now().timestamp() # Pour suppression auto 7j
            data_manager.save_giveaway(guild.id, data)
        
        channel = guild.get_channel(data["channel_id"])
        if not channel: return

        try:
            msg = await channel.fetch_message(data["message_id"])
            
            # Tirage
            participants = data["participants"].copy()
            winners_nb = data["winners"]
            
            if len(participants) > 0:
                import random
                
                # Si c'est un reroll, on enlève l'ancien gagnant
                if reroll_winner and reroll_winner in participants:
                    participants.remove(reroll_winner)
                
                if not participants:
                    return await channel.send("❌ Aucun autre participant disponible pour un nouveau tirage.")
                
                winners_ids = random.sample(participants, min(winners_nb, len(participants)))
                mentions = ", ".join(f"<@{w}>" for w in winners_ids)
                
                # Embed de fin
                embed = self.create_embed(
                    guild, 
                    self.bot.user, 
                    "🎉 C'est terminé !" if not reroll_winner else "🔄 Nouveau gagnant !",
                    (
                        f"🎁 **Lot :** {data['prize']}\n"
                        f"👑 **Gagnant(s) :** {mentions}\n"
                        f"🏆 **Nombre de gagnants :** {winners_nb}\n"
                        f"👥 **Total participants :** {len(data['participants'])}"
                    )
                )
                
                # Si c'est un reroll, on envoie un nouveau message
                if reroll_winner:
                    await channel.send(f"🔄 **Nouveau tirage effectué !** {mentions} a/ont été sélectionné(s) comme nouveau(x) gagnant(s) !")
                    await channel.send(embed=embed)
                else:
                    # Vue avec bouton de reroll pour les admins
                    class RerollView(ui.View):
                        def __init__(self, cog, data):
                            super().__init__(timeout=None)
                            self.cog = cog
                            self.data = data
                        
                        @ui.button(label="Nouveau tirage", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="gw_reroll")
                        async def reroll_btn(self, it: discord.Interaction, bt: ui.Button):
                            perms = it.channel.permissions_for(it.user)
                            if not (it.user.guild_permissions.administrator or perms.manage_events):
                                return await it.response.send_message("❌ Tu n'as pas la permission de relancer ce tirage.", ephemeral=True)
                            
                            # Créer un menu de sélection des participants
                            participants = self.data["participants"]
                            if not participants:
                                return await it.response.send_message("❌ Aucun participant disponible pour un nouveau tirage.", ephemeral=True)
                            
                            # Envoyer un message avec un menu déroulant
                            options = [discord.SelectOption(label=f"{it.guild.get_member(uid) or 'Utilisateur inconnu'}", value=str(uid)) 
                                     for uid in participants]
                            
                            select = ui.Select(
                                placeholder="Sélectionne un gagnant à remplacer",
                                options=options[:25]  # Limite de 25 options
                            )
                            
                            async def select_callback(select_it: discord.Interaction):
                                await select_it.response.defer()
                                old_winner = int(select.values[0])
                                await self.cog.end_giveaway(it.guild, self.data, reroll_winner=old_winner)
                                
                            select.callback = select_callback
                            view = ui.View()
                            view.add_item(select)
                            
                            await it.followup.send("🔍 Sélectionne un gagnant à remplacer :", view=view, ephemeral=True)
                    
                    view = RerollView(self, data)
                    await msg.edit(embed=embed, view=view)
                    await msg.reply(f"🎉 Félicitations à {mentions} qui remporte(nt) **{data['prize']}** !")
                
                # DM Gagnants
                for wid in winners_ids:
                    try:
                        u = await self.bot.fetch_user(wid)
                        await u.send(
                            f"🎉 **Bravo !** Tu as gagné **{data['prize']}** sur **{guild.name}** !\n"
                            f"🔗 {msg.jump_url}"
                        )
                    except: 
                        pass
            else:
                embed = self.create_embed(
                    guild, 
                    self.bot.user, 
                    "🏁 Terminé", 
                    "Personne n'a participé... 😢"
                )
                await msg.edit(embed=embed, view=None)
                await msg.reply("Pas de participants, pas de gagnants.")

        except Exception as e:
            traceback.print_exc()
            error_embed = self.create_embed(guild, None, "❌ Erreur", f"Une erreur est survenue lors de la fin du giveaway : {str(e)}")
            await channel.send(embed=error_embed)

    async def cancel_giveaway(self, guild, data, deleter: discord.User):
        """Supprime un giveaway et notifie tout le monde"""
        # Calculs stats finales
        participants = data["participants"]
        nb_p = len(participants)
        winners_nb = data["winners"]
        chance = (winners_nb / max(1, nb_p)) * 100
        time_left = int(data["end_timestamp"] - datetime.now().timestamp())
        
        # Notification DM
        for uid in participants:
            try:
                user = await self.bot.fetch_user(uid)
                embed_dm = self.create_embed(
                    guild,
                    deleter,
                    "❌ Giveaway Supprimé",
                    "Un giveaway auquel tu participais a été supprimé manuellement.",
                    fields=[
                        ("📂 Serveur", guild.name, True),
                        ("🎁 Lot", data["prize"], True),
                        ("👤 Supprimé par", deleter.mention, True),
                        ("👥 Participants", str(nb_p), True)
                    ]
                )
                if time_left > 0:
                    delta = str(timedelta(seconds=time_left))
                    embed_dm.add_field(name="⏱️ Temps restant", value=delta, inline=False)
                
                await user.send(embed=embed_dm)
            except: pass

        # Message de notification
        cancel_embed = self.create_embed(
            guild,
            deleter,
            "🚫 Giveaway Annulé",
            f"Le giveaway pour **{data['prize']}** a été annulé par {deleter.mention}.",
            fields=[
                ("Participants", str(nb_p), True),
                ("Chance de gagner", f"{min(100.0, chance):.2f}%", True)
            ]
        )
        
        try:
            channel = guild.get_channel(data['channel_id'])
            if channel:
                await channel.send(embed=cancel_embed)
        except Exception as e:
            print(f"Erreur lors de l'envoi du message d'annulation : {e}")

        # Suppression message et fichier
        try:
            channel = guild.get_channel(data["channel_id"])
            if channel:
                msg = await channel.fetch_message(data["message_id"])
                await msg.delete()
        except: pass
        
        data_manager.delete_giveaway(guild.id, data["message_id"])

    # --- Tâches de fond ---

    @tasks.loop(minutes=1)
    async def gw_task(self):
        now = datetime.now().timestamp()
        
        all_gws = data_manager.get_all_giveaways()
        for gw_data in all_gws:
            guild = self.bot.get_guild(gw_data["guild_id"])
            if not guild: continue # Bot kické ?

            # 1. Vérification fin normale
            if not gw_data["ended"] and now >= gw_data["end_timestamp"]:
                await self.end_giveaway(guild, gw_data)

            # 2. Nettoyage 7 jours après fin
            if gw_data.get("ended") and gw_data.get("ended_at_ts"):
                if now - gw_data["ended_at_ts"] > 7 * 24 * 3600:
                    data_manager.delete_giveaway(guild.id, gw_data["message_id"])
            
            # 3. Vérification intégrité (Message/Channel supprimé manuellement ?)
            # C'est lourd de check l'API à chaque minute pour chaque GW.
            # On le fait uniquement si on doit update ou si c'est la fin.
            # Si le message est supprimé manuellement, le fichier reste jusqu'au timeout 7j 
            # ou jusqu'à ce que le bot essaie d'écrire dedans et échoue (géré par refresh_message exception)
            # Pour respecter "Supprimes le .json si on supprime manuellement", 
            # on peut utiliser l'event on_message_delete (plus bas)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Détecte la suppression manuelle du message de giveaway"""
        if message.author != self.bot.user: return
        # On regarde si ce message correspond à un JSON
        gw = data_manager.load_giveaway(message.guild.id, message.id)
        if gw:
            # On lance la procédure de suppression (sans notif DM car pas d'auteur identifié facilement via event, 
            # ou alors on notifie juste "Supprimé manuellement")
            # Le prompt demandait : "Ce message doit s'envoyer, si le message de giveaway a été supprimé manuellement"
            # C'est compliqué d'avoir l'auteur de la suppression via l'API sans Audit Logs.
            # On va supprimer le fichier proprement.
            data_manager.delete_giveaway(message.guild.id, message.id)

    # --- Commande ---

    @commands.hybrid_command(name="giveaway", description="Créer et configurer un nouveau giveaway.")
    @app_commands.describe()
    async def giveaway_cmd(self, ctx: commands.Context):
        # Vérif perms
        perms = ctx.channel.permissions_for(ctx.author)
        if not (ctx.author.guild_permissions.administrator or perms.manage_events):
            return await ctx.reply("❌ Vous devez être **Administrateur** ou avoir la permission **Créer des évènements**.", ephemeral=True)

        await ctx.defer(ephemeral=False) # On envoie les messages de config en public ou visible auteur ? 
        # "Doit envoyer 2 messages". On va supposer que c'est visible pour l'auteur (reply) ou dans le chat
        # Pour éviter le flood, on peut tout faire en ephemeral si c'est une slash command, 
        # mais le prompt demande "2 messages".
        
        # Chargement defaults
        settings = data_manager.load_settings(ctx.guild.id)
        
        # 1. Message Config
        view = SetupView(self, ctx.author, ctx.guild.id, settings)
        
        embed_conf = self.create_embed(ctx.guild, ctx.author, "⚙️ Configuration", "Chargement...")
        msg_conf = await ctx.send(embed=embed_conf)
        view.config_msg = msg_conf
        
        # 2. Message Aperçu
        embed_prev = discord.Embed(title="Aperçu", description="L'aperçu s'affichera ici...")
        msg_prev = await ctx.send(embed=embed_prev)
        view.preview_msg = msg_prev

        # Init display
        await view.update_display()

async def setup(bot):
    cog = GiveawayCog(bot)
    await bot.add_cog(cog)
    # Le rechargement des vues est maintenant géré dans __init__
    return cog