import discord
from discord import app_commands, ui
from discord.ext import commands
from typing import Optional, Dict, Any
import logging
import json
from pathlib import Path
import os
import traceback
from functools import wraps

# --- Configuration & Chemins ---
EMBED_COLOR = 0x3498db
BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "DB"

# --- SYSTÈME D'IMPORT CONFIG_MANAGER ---
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

def handle_errors(func):
    """Décorateur pour capturer et logger les erreurs"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Erreur dans {func.__name__}: {e}\n{traceback.format_exc()}")
            return None
    return wrapper

class Infinite(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger('bot')
        self.configs: Dict[int, Dict[str, Any]] = {}

    async def cog_load(self):
        """Initialisation au chargement du cog"""
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self._load_all_configs()

    def _load_all_configs(self):
        """Charge les fichiers JSON au démarrage"""
        if not DB_DIR.exists(): return
        for file in os.listdir(DB_DIR):
            if file.endswith('.json'):
                try:
                    gid = int(file.replace('.json', ''))
                    self.load_config_sync(gid)
                except: continue

    def create_custom_embed(self, guild, user, title, description):
        """Utilise le config_manager si disponible, sinon un embed standard"""
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=guild, 
                user=user, 
                bot=self.bot, 
                title=title, 
                description=description
            )
        embed = discord.Embed(title=title, description=description, color=EMBED_COLOR)
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        return embed

    # --- Gestion des Données ---

    def load_config_sync(self, guild_id: int) -> dict:
        if guild_id in self.configs:
            return self.configs[guild_id]

        path = DB_DIR / f"{guild_id}.json"
        default = {
            'command_enabled': False,
            'hardcore_mode': False,
            'channel_id': None,
            'current_number': 1,
            'last_user_id': None 
        }

        if not path.exists():
            self.configs[guild_id] = default
            self.save_config_sync(guild_id, default)
            return default

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                config = {k: v for k, v in data.items() if k in default}
                final_config = {**default, **config}
                self.configs[guild_id] = final_config
                return final_config
        except:
            return default

    def save_config_sync(self, guild_id: int, config: dict):
        self.configs[guild_id] = config
        path = DB_DIR / f"{guild_id}.json"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde JSON {guild_id}: {e}")

    # --- Événement de Jeu ---

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        config = self.load_config_sync(message.guild.id)
        if not config.get('command_enabled') or not config.get('channel_id'):
            return
            
        if message.channel.id != int(config['channel_id']):
            return

        content = message.content.strip().replace(" ", "")
        if not content.isdigit():
            await self.safe_delete(message)
            return

        user_num = int(content)
        expected_num = config.get('current_number', 1)
        last_user = config.get('last_user_id')

        if last_user == message.author.id:
            await self.safe_delete(message)
            return await message.channel.send(
                f"⚠️ {message.author.mention}, quelqu'un d'autre doit répondre avant toi !", 
                delete_after=3
            )

        if user_num == expected_num:
            config['current_number'] = expected_num + 1
            config['last_user_id'] = message.author.id
            self.save_config_sync(message.guild.id, config)
            try: await message.add_reaction('✅')
            except: pass
        else:
            if config.get('hardcore_mode'):
                config['current_number'] = 1
                config['last_user_id'] = None
                self.save_config_sync(message.guild.id, config)
                await message.channel.send(
                    f"💀 **ERREUR !** {message.author.mention} a cassé la chaîne à **{user_num}**. On repart de **1** !"
                )
            else:
                await self.safe_delete(message)
                await message.channel.send(
                    f"❌ Mauvais chiffre {message.author.mention} ! On attendait **{expected_num}**.", 
                    delete_after=3
                )

    async def safe_delete(self, message: discord.Message):
        try: await message.delete()
        except: pass

    # --- Interface Admin ---

    class ConfigView(ui.View):
        def __init__(self, cog, guild, config, user):
            super().__init__(timeout=None)
            self.cog = cog
            self.guild = guild
            self.config = config
            self.user = user

        async def update_embed(self, interaction: discord.Interaction):
            chan_id = self.config.get('channel_id')
            chan_mention = f"<#{chan_id}>" if chan_id else "Non configuré"
            
            desc = (
                f"**État** : {'✅ Activé' if self.config['command_enabled'] else '❌ Désactivé'}\n"
                f"**Salon** : {chan_mention}\n"
                f"**Hardcore** : {'💀 ON' if self.config['hardcore_mode'] else 'ℹ️ OFF'}\n\n"
                f"ℹ️ *Règle Anti-Solo active : un joueur ne peut pas envoyer deux messages de suite.*"
            )
            
            embed = self.cog.create_custom_embed(self.guild, self.user, "⚙️ Configuration Infinite", desc)
            
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)

        @ui.button(label="Activer / Désactiver", style=discord.ButtonStyle.blurple)
        async def toggle(self, interaction: discord.Interaction, button: ui.Button):
            await interaction.response.defer()
            self.config['command_enabled'] = not self.config['command_enabled']
            
            if self.config['command_enabled'] and not self.config['channel_id']:
                overwrites = {self.guild.default_role: discord.PermissionOverwrite(send_messages=True)}
                channel = await self.guild.create_text_channel("♾️│𝑰𝒏𝒇𝒊𝒏𝒊𝒕𝒆", overwrites=overwrites)
                self.config['channel_id'] = channel.id
                await channel.send("✅ **Le jeu commence !**\nEnvoyez **1** pour débuter.")
            
            elif not self.config['command_enabled'] and self.config['channel_id']:
                channel = self.guild.get_channel(self.config['channel_id'])
                if channel:
                    try: await channel.delete()
                    except: pass
                self.config['channel_id'] = None

            self.cog.save_config_sync(self.guild.id, self.config)
            await self.update_embed(interaction)

        @ui.button(label="Mode Hardcore", style=discord.ButtonStyle.danger)
        async def hardcore(self, interaction: discord.Interaction, button: ui.Button):
            self.config['hardcore_mode'] = not self.config['hardcore_mode']
            self.cog.save_config_sync(self.guild.id, self.config)
            await self.update_embed(interaction)

    @commands.hybrid_command(name="infinite", description="Menu de gestion du jeu de compte")
    @commands.has_permissions(administrator=True)
    async def infinite_cmd(self, ctx: commands.Context):
        config = self.load_config_sync(ctx.guild.id)
        view = self.ConfigView(self, ctx.guild, config, ctx.author)
        
        chan_id = config.get('channel_id')
        chan_mention = f"<#{chan_id}>" if chan_id else "Non configuré"
        
        description = (
            f"**État** : {'✅ Activé' if config['command_enabled'] else '❌ Désactivé'}\n"
            f"**Salon** : {chan_mention}\n"
            f"**Hardcore** : {'💀 ON' if config['hardcore_mode'] else 'ℹ️ OFF'}"
        )
        
        embed = self.create_custom_embed(ctx.guild, ctx.author, "⚙️ Configuration Infinite", description)
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Infinite(bot))