import discord
from discord.ext import commands
from discord import app_commands, ui
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import aiohttp
import os
import json

# --- IMPORT CONFIG MANAGER ---
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# --- VUE POUR LES BOUTONS ---

# --- MODAL POUR CHOIX D'UN SALON PAR ID ---
class ChooseChannelModal(ui.Modal, title="Choisir un salon"):
    channel_id = ui.TextInput(label="ID du salon", placeholder="Entrez l'ID du salon", required=True)

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.channel_id.value)
            guild_id = str(interaction.guild.id)
            channel = interaction.guild.get_channel(channel_id)
            if channel is None:
                await interaction.response.send_message(f"❌ Salon introuvable pour l'ID {channel_id}.", ephemeral=True)
                return
            self.cog.save_channel(guild_id, channel_id)
            await interaction.response.send_message(f"✅ Les messages de level up seront maintenant envoyés dans {channel.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Erreur : {e}", ephemeral=True)

# --- SÉLECTEUR AVANCÉ POUR LA CONFIGURATION DU SALON ---
class SalonConfigView(ui.View):
    def __init__(self, cog, salon_actuel):
        super().__init__(timeout=120)
        self.cog = cog
        self.salon_actuel = salon_actuel

        self.add_item(SalonSelect(cog))



# --- SÉLECTEUR AVEC EMOJIS ET MISE À JOUR DE L'EMBED ---
class SalonSelect(ui.Select):
    def __init__(self, cog):
        options = [
            discord.SelectOption(label="Définir ce salon", description="Le message sera envoyé dans le salon actuel", value="current", emoji="📌"),
            discord.SelectOption(label="Choisir un salon", description="Ouvre un modal pour saisir l'ID du salon", value="choose", emoji="🔎"),
            discord.SelectOption(label="Salon du message", description="Le message sera envoyé là où l'utilisateur monte de niveau", value="message_channel", emoji="💬"),
            discord.SelectOption(label="Désactiver", description="Aucun message de niveau ne sera envoyé", value="disable", emoji="🚫"),
        ]
        super().__init__(placeholder="Choisissez où envoyer le message de niveau", min_values=1, max_values=1, options=options)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        guild_id = str(interaction.guild.id)
        channel = interaction.channel
        config_changed = False
        if value == "current":
            channel_id = channel.id
            self.cog.save_channel(guild_id, channel_id)
            config_changed = True
        elif value == "choose":
            await interaction.response.send_modal(ChooseChannelModal(self.cog))
            return
        elif value == "message_channel":
            self.cog.save_channel(guild_id, None)
            config_changed = True
        elif value == "disable":
            self.cog.save_channel(guild_id, 0)
            config_changed = True

        if config_changed:
            # Mise à jour de l'embed en temps réel
            salon_id = self.cog.get_configured_channel(guild_id)
            salon = interaction.guild.get_channel(salon_id) if salon_id else None
            if salon_id == 0:
                etat = "Désactivé (aucun message envoyé)"
            elif salon_id is None:
                etat = "Salon du message (là où l'utilisateur monte de niveau)"
            else:
                etat = f"Salon défini : {salon.mention}"
            description = f"**Configuration** : {etat}"
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=interaction.guild,
                    user=interaction.user,
                    bot=self.cog.bot,
                    title="Configuration des niveaux",
                    description=description
                )
            else:
                embed = discord.Embed(
                    title="Configuration des niveaux",
                    description=description,
                    color=discord.Color.blurple()
                )
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            await interaction.response.edit_message(embed=embed, view=self.view)


# --- COG PRINCIPAL ---
class LvlUp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        from pathlib import Path
        # Même structure que le module XP
        ROOT = Path(__file__).resolve().parent.parent
        DATA_DIR = ROOT.parent.parent.parent / "data" / "pack" / "statistiques"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.base_data_dir = DATA_DIR
        # Debug désactivé sauf erreur

    # --- MÉTHODES JSON ---
    def get_server_dir(self, guild_id: str):
        """Retourne le dossier spécifique au serveur."""
        server_dir = self.base_data_dir / guild_id
        server_dir.mkdir(parents=True, exist_ok=True)
        # Debug désactivé sauf erreur
        return server_dir
    
    def load_config(self, guild_id: str = None):
        """Charge le fichier JSON contenant les configurations des serveurs."""
        if guild_id:
            # Config spécifique au serveur
            server_dir = self.get_server_dir(guild_id)
            config_path = server_dir / "lvlup_config.json"
            # Debug désactivé sauf erreur
        else:
            # Config global (pour compatibilité)
            config_path = self.base_data_dir / "lvlup_config.json"
            print(f"\033[95m[LvlUp] Loading global config from: {config_path}\033[0m")
        
        if not os.path.exists(config_path):
            # Debug désactivé sauf erreur
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Debug désactivé sauf erreur
                return config
        except json.JSONDecodeError as e:
            print(f"\033[91m[LVLUP] JSON decode error: {e}\033[0m")
            return {}
        except Exception as e:
            print(f"\033[91m[LVLUP] Error loading config: {e}\033[0m")
            return {}

    def save_channel(self, guild_id: str, channel_id: int):
        """Sauvegarde un salon pour un serveur donné."""
        # Debug désactivé sauf erreur
        config = self.load_config(guild_id)
        config["channel_id"] = channel_id
        
        server_dir = self.get_server_dir(guild_id)
        config_path = server_dir / "lvlup_config.json"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            # Debug désactivé sauf erreur
        except Exception as e:
            print(f"\033[91m[LVLUP] Error saving config: {e}\033[0m")

    def remove_channel(self, guild_id: str):
        """Supprime la configuration d'un serveur."""
        # Debug désactivé sauf erreur
        server_dir = self.get_server_dir(guild_id)
        config_path = server_dir / "lvlup_config.json"
        
        try:
            if os.path.exists(config_path):
                os.remove(config_path)
                # Debug désactivé sauf erreur
            else:
                pass
        except Exception as e:
            print(f"\033[91m[LVLUP] Error removing config: {e}\033[0m")

    def get_configured_channel(self, guild_id: str):
        """Récupère l'ID du salon configuré, ou None s'il n'y en a pas."""
        config = self.load_config(guild_id)
        channel_id = config.get("channel_id")
        # Debug désactivé sauf erreur
        return channel_id


    # --- ÉVÉNEMENT & COMMANDES ---

    @commands.Cog.listener()
    async def on_level_up(self, message, old_level, new_level):
        """Note: Cet événement doit être "dispatché" manuellement ailleurs dans ton code via:
           self.bot.dispatch('level_up', message, old_level, new_level)"""
        user = message.author
        guild = message.guild

        salon_id = self.get_configured_channel(str(guild.id)) if guild else None

        # Gestion des 3 modes
        if salon_id == 0:
            # Mode désactivé
            return
        elif salon_id is None:
            # Mode salon du message (là où l'utilisateur monte de niveau)
            salon = message.channel
        else:
            # Mode salon défini
            salon = guild.get_channel(salon_id) if guild else None

        if salon is None:
            return

        try:
            # --- Paramètres image ---
            width, height = 1400, 350
            padding = 30
            avatar_size = 200

            # Couleurs
            COLOR_OWNER_BOT = (255, 0, 0, 255)
            COLOR_OWNER_SERVER = (255, 215, 0, 255)
            COLOR_ADMIN = (0, 0, 0, 255)
            COLOR_BOOSTER = (232, 69, 255, 255)
            COLOR_DEFAULT = (114, 137, 218, 255)

            card_color = COLOR_DEFAULT
            if await self.bot.is_owner(user):
                card_color = COLOR_OWNER_BOT
            elif guild and user.id == guild.owner_id:
                card_color = COLOR_OWNER_SERVER
            elif any(r.permissions.administrator for r in getattr(user, "roles", [])):
                card_color = COLOR_ADMIN
            elif any(r.is_premium_subscriber() for r in getattr(user, "roles", [])):
                card_color = COLOR_BOOSTER

            # Fond
            background = Image.new("RGBA", (width, height), (40, 43, 48, 255))
            draw = ImageDraw.Draw(background)

            # Avatar
            avatar_url = user.display_avatar.replace(size=256, static_format="png").url
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    avatar_bytes = await resp.read()

            avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))
            avatar_x = padding
            avatar_y = (height - avatar_size) // 2
            background.paste(avatar, (avatar_x, avatar_y), avatar)
            draw.rectangle([avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size], outline=card_color, width=6)

            # Polices
            font_path = os.path.join(os.path.dirname(__file__), "..", "assets", "TradeWinds-Regular.ttf")
            if not os.path.exists(font_path):
                font_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "cogs", "pack", "statistiques", "assets", "TradeWinds-Regular.ttf")

            try:
                font_title = ImageFont.truetype(font_path, 70)
            except Exception:
                font_title = ImageFont.load_default()


            # Texte principal : utiliser user.name (nom d'utilisateur Discord, pas display_name)
            pseudo = user.name if hasattr(user, 'name') else str(user)
            pseudo_cap = pseudo[0].upper() + pseudo[1:] if pseudo else "Inconnu"

            # Taille de police dynamique selon la longueur du pseudo
            base_size = 70
            min_size = 32
            max_len = 18
            # Si pseudo > max_len, on réduit la taille
            if len(pseudo_cap) > max_len:
                font_size = max(min_size, base_size - (len(pseudo_cap) - max_len) * 2)
            else:
                font_size = base_size

            try:
                font_title = ImageFont.truetype(font_path, font_size)
            except Exception:
                font_title = ImageFont.load_default()

            text1 = f"Félicitations {pseudo_cap}!"
            text2 = f"Vous êtes passé niveau {new_level}"

            text1_bbox = draw.textbbox((0, 0), text1, font=font_title)
            text1_h = text1_bbox[3] - text1_bbox[1]

            bloc_x = avatar_x + avatar_size + 80
            bloc_y = avatar_y + 40

            draw.text((bloc_x, bloc_y), text1, fill=card_color, font=font_title)
            draw.text((bloc_x, bloc_y + text1_h + 40), text2, fill=(255, 255, 255, 255), font=font_title)

            # Préparation fichier
            buffer = BytesIO()
            background.save(buffer, format="PNG")
            buffer.seek(0)
            file = discord.File(fp=buffer, filename="lvlup.png")

            # Embed
            embed = discord.Embed(
                color=discord.Color.from_rgb(*card_color[:3])
            )
            embed.set_image(url="attachment://lvlup.png")
            embed.set_footer(text="Utilises !lvlup pour gérer ce message.")

            await salon.send(content=f"On dirait que {user.mention} vient de passer un niveau.", embed=embed, file=file)

        except Exception as e:
            await salon.send(f"Level up pour {user.mention} ! *(L'image n'a pas pu être générée : {e})*")


    @commands.hybrid_command(name="lvlup", description="Configurer le salon pour les annonces de niveau supérieur.")
    @commands.has_permissions(administrator=True)
    async def lvlup(self, ctx: commands.Context):
        # Debug désactivé sauf erreur
        
        if not ctx.guild:
            await ctx.send("Cette commande ne peut être utilisée que sur un serveur.", ephemeral=True)
            return

        guild_id = str(ctx.guild.id)
        # Debug désactivé sauf erreur
        salon_id = self.get_configured_channel(guild_id)
        salon = ctx.guild.get_channel(salon_id) if salon_id else None
        # Debug désactivé sauf erreur
        
        # Détermination de l'état de configuration

        if salon_id == 0:
            etat = "Désactivé (aucun message envoyé)"
        elif salon_id is None:
            etat = "Salon du message (là où l'utilisateur monte de niveau)"
        else:
            etat = f"Salon défini : {salon.mention}"

        description = f"**Configuration** : {etat}"

        try:
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=ctx.guild,
                    user=ctx.author,
                    bot=self.bot,
                    title="Configuration des niveaux",
                    description=description
                )
            else:
                embed = discord.Embed(
                    title="Configuration des niveaux",
                    description=description,
                    color=discord.Color.blurple()
                )
            # Ajout du thumbnail avec l'icône du serveur
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
        except Exception as e:
            print(f"\033[91m[LVLUP] Error creating embed: {e}\033[0m")
            return

        view = SalonConfigView(self, salon)
        try:
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            print(f"\033[91m[LVLUP] Error sending message: {e}\033[0m")


async def setup(bot):
    # Debug désactivé sauf erreur
    try:
        await bot.add_cog(LvlUp(bot))
        # Debug désactivé sauf erreur
    except Exception as e:
        print(f"\033[91m[LVLUP] Erreur lors de l'ajout du cog: {e}\033[0m")