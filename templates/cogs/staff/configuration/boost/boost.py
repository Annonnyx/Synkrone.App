import discord
import json
import datetime
import asyncio
import traceback
from pathlib import Path
from discord.ext import commands, tasks
from discord import app_commands, ui, File

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
# On tente d'importer le gestionnaire de config pour le style unifié (comme pingpong.py)
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# --------------------------- CONFIGURATION & CHEMINS --------------------------
# ==============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data' / 'boosters'
DATA_DIR.mkdir(parents=True, exist_ok=True)

THUMBNAIL_PATH = BASE_DIR / "thumbnail.gif"
IMAGE_PATH = BASE_DIR / "image.gif"
BOOSTER_COLOR = 0xFF73FA

# ==============================================================================
# ----------------------------- GESTION JSON -----------------------------------
# ==============================================================================

def get_guild_file(guild_id: int) -> Path:
    return DATA_DIR / f"{guild_id}.json"

def load_guild_config(guild_id: int) -> dict:
    file_path = get_guild_file(guild_id)
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception: 
            pass
    return {"enabled": False, "channel_id": None, "message_id": None}

def save_guild_config(guild_id: int, data: dict):
    with open(get_guild_file(guild_id), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# ==============================================================================
# --------------------------- MODULE BOOSTERS ----------------------------------
# ==============================================================================

class BoostersModule(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Démarre la boucle de vérification au chargement."""
        if not self.update_task_loop.is_running():
            self.update_task_loop.start()

    def cog_unload(self):
        """Arrête la boucle au déchargement."""
        self.update_task_loop.cancel()

    # --- BOUCLE DE MISE À JOUR (Tableau d'Honneur) ---
    @tasks.loop(minutes=5)
    async def update_task_loop(self):
        """Met à jour le panneau régulièrement."""
        await self.bot.wait_until_ready()
        for file in DATA_DIR.glob("*.json"):
            try:
                guild_id = int(file.stem)
                config = load_guild_config(guild_id)
                if not config.get('enabled'): continue
                
                guild = self.bot.get_guild(guild_id)
                if guild:
                    channel = guild.get_channel(config.get('channel_id'))
                    if channel: 
                        await self.update_boosters_embed(guild, channel, config)
            except Exception: 
                continue

    # --- LOGIQUE D'AFFICHAGE DU TABLEAU D'HONNEUR ---
    async def update_boosters_embed(self, guild: discord.Guild, channel: discord.TextChannel, config: dict):
        """
        Génère le récapitulatif global.
        LOGIQUE : Supprime l'ancien message et renvoie le nouveau pour qu'il soit toujours en bas.
        """
        try:
            # 1. Données & Tri
            boosters = [m for m in guild.members if m.premium_since]
            boosters.sort(key=lambda x: x.premium_since)

            now_ts = int(datetime.datetime.now().timestamp())
            
            title = "✨ Remerciements aux Boosters"
            description = (
                f"Dernière mise à jour : <t:{now_ts}:R>\n\n"
                "Un immense merci à nos précieux boosters qui font vivre le serveur ! 🚀\n"
                "Votre soutien permet de débloquer des fonctionnalités exclusives pour tous."
            )

            # 2. Construction de l'Embed (Avec config_manager si dispo)
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=guild,
                    user=self.bot.user,
                    bot=self.bot,
                    title=title,
                    description=description,
                    target_id=guild.id
                )
            else:
                embed = discord.Embed(title=title, description=description, color=BOOSTER_COLOR)

            # 3. Liste des contributeurs
            list_text = ""
            for m in boosters[:25]:
                date_unix = int(m.premium_since.timestamp())
                list_text += f"• {m.mention} • <t:{date_unix}:d>\n"

            embed.add_field(
                name=f"🚀 Liste des contributeurs ({len(boosters)})",
                value=list_text if list_text else "Aucun boost actif actuellement.",
                inline=False
            )

            stats_text = (
                f"• Boosts actifs : **{guild.premium_subscription_count}**\n"
                f"• Niveau du serveur : **Niveau {guild.premium_tier}**"
            )
            embed.add_field(name="📊 Statistiques", value=stats_text, inline=False)

            # 4. Fichiers (Utilisation de TES gifs)
            files = []
            if THUMBNAIL_PATH.exists():
                files.append(File(str(THUMBNAIL_PATH), filename="thumb.gif"))
                embed.set_thumbnail(url="attachment://thumb.gif")
            
            if IMAGE_PATH.exists():
                files.append(File(str(IMAGE_PATH), filename="banner.gif"))
                embed.set_image(url="attachment://banner.gif")

            # 5. Suppression et Remplacement (Logique "Toujours dernier message")
            if config.get('message_id'):
                try:
                    old_msg = await channel.fetch_message(config['message_id'])
                    await old_msg.delete()
                except: 
                    pass 

            # Envoi du nouveau message
            new_msg = await channel.send(embed=embed, files=files)
            
            # Sauvegarde du nouvel ID
            config['message_id'] = new_msg.id
            save_guild_config(guild.id, config)

        except Exception:
            traceback.print_exc()

    # --- ÉVÉNEMENT : CÉLÉBRATION INDIVIDUELLE ---
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Détecte quand quelqu'un boost, envoie une célébration, 
        puis remet le tableau d'honneur en bas.
        """
        if before.premium_since is None and after.premium_since is not None:
            config = load_guild_config(after.guild.id)
            if not config.get('enabled'): return

            channel = after.guild.get_channel(config['channel_id'])
            if not channel: return

            # --- A. MESSAGE DE CÉLÉBRATION INDIVIDUEL ---
            title_celeb = "❤️ NOUVEAU BOOSTER !"
            desc_celeb = (
                f"Un immense merci à {after.mention} qui vient de booster le serveur !\n"
                f"Nous sommes maintenant à **{after.guild.premium_subscription_count}** boosts. ✨"
            )

            if config_manager:
                embed_celeb = config_manager.get_formatted_embed(
                    guild=after.guild,
                    user=after,
                    bot=self.bot,
                    title=title_celeb,
                    description=desc_celeb,
                    target_id=after.guild.id
                )
            else:
                embed_celeb = discord.Embed(title=title_celeb, description=desc_celeb, color=BOOSTER_COLOR)
            
            embed_celeb.set_author(name=after.display_name, icon_url=after.display_avatar.url)

            files_celeb = []
            if IMAGE_PATH.exists():
                files_celeb.append(File(str(IMAGE_PATH), filename="celebration.gif"))
                embed_celeb.set_image(url="attachment://celebration.gif")

            await channel.send(embed=embed_celeb, files=files_celeb)

            # --- B. MISE À JOUR DU TABLEAU D'HONNEUR ---
            await asyncio.sleep(2)
            await self.update_boosters_embed(after.guild, channel, config)

    # --- COMMANDE DE CONFIGURATION ---
    @commands.hybrid_command(name="boost", description="Configuration du système de boosters.")
    @commands.has_permissions(manage_guild=True)
    async def boost(self, ctx: commands.Context):
        """Interface de configuration (!boost ou /boost)"""
        guild_id = ctx.guild.id
        config = load_guild_config(guild_id)
        
        # --- CORRECTION DE LA SYNTAXE ICI ---
        statut_txt = "`🟢 Activé`" if config.get('enabled') else "`🔴 Désactivé`"
        salon_txt = f"<#{config['channel_id']}>" if config.get('channel_id') else "`Non configuré`"
        
        embed = discord.Embed(
            title="🚀 Configuration Boosters",
            description=(
                "Gérez l'affichage automatique des remerciements.\n\n"
                f"**Statut :** {statut_txt}\n"
                f"**Salon :** {salon_txt}"
            ),
            color=BOOSTER_COLOR
        )
        embed.set_footer(text="Le tableau d'honneur restera toujours le dernier message.")
        
        files_cfg = []
        if THUMBNAIL_PATH.exists():
            files_cfg.append(File(str(THUMBNAIL_PATH), filename="thumb.gif"))
            embed.set_thumbnail(url="attachment://thumb.gif")

        class BoosterControl(ui.View):
            def __init__(self, cog, gid):
                super().__init__(timeout=60)
                self.cog = cog
                self.gid = gid

            @ui.button(label="Activer / Setup", style=discord.ButtonStyle.success, emoji="✅")
            async def enable(self, interaction: discord.Interaction, button: ui.Button):
                target_name = "🚀│𝑩𝒐𝒐𝒔𝒕"
                guild = interaction.guild
                
                channel = discord.utils.get(guild.text_channels, name=target_name)
                if not channel:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(send_messages=False),
                        guild.me: discord.PermissionOverwrite(send_messages=True, embed_links=True, attach_files=True)
                    }
                    channel = await guild.create_text_channel(target_name, overwrites=overwrites)
                
                new_config = {"enabled": True, "channel_id": channel.id, "message_id": None}
                save_guild_config(self.gid, new_config)
                
                await interaction.response.send_message(f"✨ Module activé dans {channel.mention}", ephemeral=True)
                await self.cog.update_boosters_embed(guild, channel, new_config)

            @ui.button(label="Désactiver", style=discord.ButtonStyle.danger, emoji="🛑")
            async def disable(self, interaction: discord.Interaction, button: ui.Button):
                conf = load_guild_config(self.gid)
                conf["enabled"] = False
                save_guild_config(self.gid, conf)
                await interaction.response.send_message("Le système a été désactivé.", ephemeral=True)

        await ctx.send(embed=embed, view=BoosterControl(self, guild_id), files=files_cfg, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BoostersModule(bot))