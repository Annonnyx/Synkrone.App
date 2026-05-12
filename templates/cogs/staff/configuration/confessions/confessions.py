import discord
import logging
import json
import os
import shutil
from typing import Dict, Optional
from discord import app_commands, ui
from discord.ext import commands, tasks

# ==============================================================================
# --------------------------- IMPORTATION MANAGER ------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

SALON_NOM_CIBLE = "💌│𝑪𝒐𝒏𝒇𝒆𝒔𝒔𝒊𝒐𝒏𝒔"
BASE_PATH = os.path.join(os.path.dirname(__file__), "data")

# --- Fonctions utilitaires pour l'Embed ---

async def get_themed_embed(bot, guild, user, title, description):
    """Génère un embed via le manager ou un embed standard en fallback"""
    if config_manager:
        embed = config_manager.get_formatted_embed(guild, user, bot, title, description, guild.id)
        # Remplacer l'auteur par l'image du bot et "Confession Anonyme"
        embed.set_author(name="Confession Anonyme", icon_url=bot.user.display_avatar.url)
        return embed
    
    embed = discord.Embed(title=title, description=description, color=0x5865F2)
    embed.set_author(name="Confession Anonyme", icon_url=bot.user.display_avatar.url)
    embed.set_footer(text="Système de Confessions Anonymes")
    return embed

# --- Fonctions de Gestion des Données ---

def get_server_path(guild_id: int):
    path = os.path.join(BASE_PATH, str(guild_id))
    os.makedirs(path, exist_ok=True)
    return path

def save_config(guild_id: int, data: dict):
    with open(os.path.join(get_server_path(guild_id), "config.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_config(guild_id: int) -> dict:
    path = os.path.join(get_server_path(guild_id), "config.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"enabled": False, "channel_id": None, "counter": 0}

def delete_server_data(guild_id: int):
    path = os.path.join(BASE_PATH, str(guild_id))
    if os.path.exists(path):
        shutil.rmtree(path)

# --- UI Components ---

class ReplyModal(ui.Modal, title="💬 Répondre à la confession"):
    content = ui.TextInput(label="Votre message", style=discord.TextStyle.paragraph, min_length=1)

    def __init__(self, bot: commands.Bot, thread: discord.Thread, is_anonymous: bool):
        super().__init__()
        self.bot = bot
        self.thread = thread
        self.is_anonymous = is_anonymous

    async def on_submit(self, interaction: discord.Interaction):
        title = "Réponse Anonyme" if self.is_anonymous else interaction.user.display_name
        description = self.content.value
        
        embed = await get_themed_embed(self.bot, interaction.guild, interaction.user, title, description)
        
        if self.is_anonymous:
            embed.set_author(name="Réponse Anonyme", icon_url=self.bot.user.display_avatar.url)

        try:

            await self.thread.send(embed=embed)
            # Journaliser la réponse anonyme dans le .json de la confession
            if self.is_anonymous:
                # Retrouver le message principal lié au thread
                base_path = os.path.join(os.path.dirname(__file__), "data", str(interaction.guild.id))
                # Chercher le .json correspondant au thread
                for fname in os.listdir(base_path):
                    if fname.startswith("msg_") and fname.endswith(".json"):
                        fpath = os.path.join(base_path, fname)
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if data.get("thread_id") == self.thread.id:
                            # Ajouter la réponse anonyme
                            if "anonymous_replies" not in data:
                                data["anonymous_replies"] = []
                            data["anonymous_replies"].append({
                                "user_id": interaction.user.id,
                                "content": description
                            })
                            with open(fpath, "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=4, ensure_ascii=False)
                            break
            await interaction.response.send_message("✅ Réponse envoyée !", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("❌ Impossible d'envoyer dans le fil.", ephemeral=True)

class ConfessModal(ui.Modal, title="💌 Nouvelle confession"):
    content = ui.TextInput(label="Ta confession", style=discord.TextStyle.paragraph, min_length=5)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config(interaction.guild.id)
        channel = interaction.guild.get_channel(config.get("channel_id"))
        
        if not channel:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)

        config["counter"] += 1
        count = config["counter"]
        
        title = f"💌 Confession Anonyme #{count}"
        description = self.content.value
        
        embed = await get_themed_embed(self.bot, interaction.guild, interaction.user, title, description)

        msg = await channel.send(embed=embed)
        thread = await msg.create_thread(name=f"Discussion #{count}", auto_archive_duration=1440)

        # Ajout de l'id de l'auteur dans le .json
        data_msg = {
            "message_id": msg.id,
            "thread_id": thread.id,
            "count": count,
            "author_id": interaction.user.id,
            "content": description,
            "anonymous_replies": []
        }
        with open(os.path.join(get_server_path(interaction.guild.id), f"msg_{msg.id}.json"), "w", encoding="utf-8") as f:
            json.dump(data_msg, f, indent=4, ensure_ascii=False)
        
        save_config(interaction.guild.id, config)

        view = ui.View(timeout=None)
        view.add_item(ui.Button(label="Répondre", style=discord.ButtonStyle.success, custom_id=f"conf_pub_{msg.id}"))
        view.add_item(ui.Button(label="Anonyme", style=discord.ButtonStyle.secondary, custom_id=f"conf_anon_{msg.id}"))
        view.add_item(ui.Button(label="💌 Créer une confession", style=discord.ButtonStyle.primary, custom_id="create_confess_modal"))
        
        await msg.edit(view=view)
        await interaction.response.send_message("✅ Confession publiée !", ephemeral=True)

# --- Cog Principal ---

class Confessions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_channels.start()

    def cog_unload(self):
        self.check_channels.cancel()

    @tasks.loop(seconds=60)
    async def check_channels(self):
        if not os.path.exists(BASE_PATH): return
        for guild_id_str in os.listdir(BASE_PATH):
            try:
                guild_id = int(guild_id_str)
                guild = self.bot.get_guild(guild_id)
                if not guild: continue
                config = load_config(guild_id)
                if config.get("enabled") and config.get("channel_id"):
                    if not guild.get_channel(config["channel_id"]):
                        delete_server_data(guild_id)
            except: continue

    @commands.hybrid_command(name="confess", description="Gérer le système de confessions anonymes")
    @commands.has_permissions(manage_guild=True)
    async def confessions(self, ctx: commands.Context):
        config = load_config(ctx.guild.id)
        chan = ctx.guild.get_channel(config.get("channel_id"))
        status_salon = chan.mention if chan else "⚠️ Salon introuvable"

        title = "⚙️ Configuration des Confessions"
        description = (
            f"**État :** {'`✅ ACTIVÉ`' if config['enabled'] else '`❌ DÉSACTIVÉ`'}\n"
            f"**Salon :** {status_salon}\n"
            f"**Compteur :** `{config['counter']}`"
        )
        
        embed = await get_themed_embed(self.bot, ctx.guild, ctx.author, title, description)
        
        view = ui.View()
        if not config["enabled"]:
            view.add_item(ui.Button(label="Activer le système", style=discord.ButtonStyle.success, custom_id="setup_system"))
        else:
            view.add_item(ui.Button(label="Réinitialiser / Réparer", style=discord.ButtonStyle.primary, custom_id="setup_system"))
            view.add_item(ui.Button(label="Désactiver & Purger", style=discord.ButtonStyle.danger, custom_id="disable_system"))
        
        await ctx.send(embed=embed, view=view, ephemeral=True if ctx.interaction else False)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.data or "custom_id" not in interaction.data: return
        cid = interaction.data["custom_id"]
        guild = interaction.guild

        if cid == "setup_system":
            config = load_config(guild.id)
            channel = guild.get_channel(config["channel_id"]) if config["channel_id"] else None
            
            if not channel:
                channel = discord.utils.get(guild.text_channels, name=SALON_NOM_CIBLE)
                if not channel:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(
                          send_messages=False,       # Empêche d'écrire directement dans le salon principal
                          read_messages=True,        # Permet de voir les confessions
                          send_messages_in_threads=False # PERMET à tout le monde de répondre dans les fils
    ),
                        
                        guild.me: discord.PermissionOverwrite(send_messages=True, manage_messages=True, manage_threads=True, create_public_threads=True)
                    }
                    # Seuls les admins peuvent écrire dans les fils
                    # On applique la permission sur le salon, mais il faut aussi restreindre les threads
                    # Les threads héritent par défaut, mais on va restreindre dans ReplyModal
                    channel = await guild.create_text_channel(SALON_NOM_CIBLE, overwrites=overwrites)
            
            config["enabled"] = True
            config["channel_id"] = channel.id
            save_config(guild.id, config)

            view = ui.View(timeout=None)
            view.add_item(ui.Button(label="💌 Créer une confession", style=discord.ButtonStyle.primary, custom_id="create_confess_modal"))
            
            welcome_embed = await get_themed_embed(self.bot, guild, interaction.user, "💌 Se confesser", "Appuyez sur le bouton pour commencer.")
            await channel.send(embed=welcome_embed, view=view)
            await interaction.response.edit_message(content=f"✅ Système opérationnel dans {channel.mention}", embed=None, view=None)

        elif cid == "create_confess_modal":
            await interaction.response.send_modal(ConfessModal(self.bot))

        elif cid.startswith("conf_pub_") or cid.startswith("conf_anon_"):
            is_anon = "conf_anon_" in cid
            msg_id = int(cid.split("_")[-1])
            path = os.path.join(get_server_path(guild.id), f"msg_{msg_id}.json")
            if not os.path.exists(path):
                return await interaction.response.send_message("❌ Données introuvables.", ephemeral=True)

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            thread = guild.get_thread(data["thread_id"])
            if not thread:
                try:
                    config = load_config(guild.id)
                    chan = guild.get_channel(config["channel_id"])
                    msg = await chan.fetch_message(msg_id)
                    thread = msg.thread or await msg.create_thread(name="Discussion", auto_archive_duration=1440)
                except:
                    return await interaction.response.send_message("❌ Fil introuvable.", ephemeral=True)

            await interaction.response.send_modal(ReplyModal(self.bot, thread, is_anon))

        elif cid == "disable_system":
            config = load_config(guild.id)
            channel = guild.get_channel(config["channel_id"])
            if channel:
                try: await channel.delete()
                except: pass
            delete_server_data(guild.id)
            await interaction.response.edit_message(content="✅ Système et dossier de données supprimés.", embed=None, view=None)

async def setup(bot: commands.Bot):
    if not os.path.exists(BASE_PATH): os.makedirs(BASE_PATH)
    await bot.add_cog(Confessions(bot))