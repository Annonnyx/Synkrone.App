import discord
from discord.ext import commands
import json
from pathlib import Path
import importlib
import traceback

# --- GESTION DU CONFIG_MANAGER ---
# Importation du config_manager comme dans pingpong.py
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# --- FONCTION UTILITAIRE POUR LES EMBEDS ---
async def create_embed(guild, user, bot, title, description, color=0x2b2d31, **kwargs):
    """
    Crée un embed en utilisant le config_manager si disponible, sinon utilise un format par défaut
    
    Args:
        guild: Le serveur Discord
        user: L'utilisateur concerné par le log
        bot: L'instance du bot
        title: Le titre de l'embed
        description: La description de l'embed
        color: La couleur de l'embed (par défaut: 0x2b2d31)
        **kwargs: Arguments supplémentaires pour le config_manager
    """
    if config_manager:
        try:
            # Utilisation du config_manager pour créer l'embed formaté
            # On passe force_global=True pour utiliser la configuration globale si aucune configuration de serveur n'existe
            embed = config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=bot,
                title=title,
                description=description,
                target_id=guild.id if guild else None,
                force_global=not bool(guild)  # Si pas de serveur, on force la configuration globale
            )
            # Si une couleur est explicitement fournie, on l'applique par-dessus
            if color is not None:
                embed.color = color
            return embed
        except Exception as e:
            print(f"❌ Erreur avec config_manager: {str(e)}")
            traceback.print_exc()
    
    # Fallback si le config_manager n'est pas disponible ou en cas d'erreur
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    # Ajout d'un footer par défaut avec l'icône du bot si disponible
    if hasattr(bot, 'user') and hasattr(bot.user, 'avatar'):
        embed.set_footer(icon_url=bot.user.avatar.url)
    
    if user and hasattr(user, 'display_avatar') and user.display_avatar:
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    elif user:
        embed.set_author(name=str(user))
        
    if user and hasattr(user, 'display_avatar') and user.display_avatar:
        embed.set_thumbnail(url=user.display_avatar.url)
        
    return embed

# --- VUE INTERACTIVE ---
class LogConfigView(discord.ui.View):
    def __init__(self, cog, guild_id, config):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.config = config
        self.update_buttons()

    def update_buttons(self):
        styles = {self.btn_vocal: "log_vocal", self.btn_msg: "log_msg", self.btn_mod: "log_mod", self.btn_server: "log_server"}
        for btn, key in styles.items():
            btn.style = discord.ButtonStyle.green if self.config.get(key) else discord.ButtonStyle.gray

    async def create_embed(self, user, guild):
        title = "⚙️ Configuration des Logs"
        def get_line(emoji, name, key):
            chan_id = self.config.get(key)
            return f"{'🟢' if chan_id else '🔴'} **{emoji} {name}**{f' | <#{chan_id}>' if chan_id else ''}\n"

        desc = "Cliquez sur les boutons pour activer/désactiver les salons de logs.\n\n" + \
               get_line("🔊", "Vocal", "log_vocal") + get_line("💬", "Messages", "log_msg") + \
               get_line("🔨", "Modération", "log_mod") + get_line("⚙️", "Serveur", "log_server")
        
        # On utilise None pour la couleur pour laisser le config_manager décider
        return await create_embed(guild, user, self.cog.bot, title, desc, color=None)

    async def toggle_log(self, interaction, key_chan, name):
        guild = interaction.guild
        self.config = self.cog.get_config(guild.id)
        if self.config.get(key_chan):
            try:
                channel = guild.get_channel(self.config[key_chan])
                if channel: await channel.delete()
            except: pass
            self.config[key_chan] = None
        else:
            # Création de la catégorie avec permission pour les admins uniquement
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                **{role: discord.PermissionOverwrite(read_messages=True) for role in guild.roles if role.permissions.administrator}
            }
            cat = guild.get_channel(self.config.get("category_id")) or await guild.create_category(
                "📂│𝑳𝒐𝒈𝒔-𝑺𝒆𝒓𝒗𝒆𝒖𝒓",
                overwrites=overwrites
            )
            self.config["category_id"] = cat.id
            # Création du salon avec les mêmes permissions que la catégorie
            new_chan = await guild.create_text_channel(
                name,
                category=cat,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True),
                    **{role: discord.PermissionOverwrite(read_messages=True) for role in guild.roles if role.permissions.administrator}
                }
            )
            self.config[key_chan] = new_chan.id
        
        self.cog.save_config(guild.id, self.config)
        self.update_buttons()
        embed = await self.create_embed(interaction.user, guild)
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Configuration mise à jour : {name}", ephemeral=True)

    @discord.ui.button(label="Vocal", emoji="🔊")
    async def btn_vocal(self, i, b): await self.toggle_log(i, 'log_vocal', "🔊│𝑳𝒐𝒈𝒔-𝑽𝒐𝒄𝒂𝒍")
    @discord.ui.button(label="Messages", emoji="💬")
    async def btn_msg(self, i, b): await self.toggle_log(i, 'log_msg', "💬│𝑳𝒐𝒈𝒔-𝑴𝒔𝒈")
    @discord.ui.button(label="Modération", emoji="🔨")
    async def btn_mod(self, i, b): await self.toggle_log(i, 'log_mod', "🔨│𝑳𝒐𝒈𝒔-𝑴𝒐𝒅")
    @discord.ui.button(label="Serveur", emoji="⚙️")
    async def btn_server(self, i, b): await self.toggle_log(i, 'log_server', "⚙️│𝑳𝒐𝒈𝒔-𝑺𝒆𝒓𝒗𝒆𝒓")

# --- COG DE GESTION ---
class LogSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)

    def get_config(self, guild_id):
        path = self.data_dir / f"{guild_id}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        return {"category_id": None, "log_vocal": None, "log_msg": None, "log_mod": None, "log_server": None}

    def save_config(self, guild_id, data):
        with open(self.data_dir / f"{guild_id}.json", "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

    @commands.hybrid_command(name="log")
    @commands.has_permissions(administrator=True)
    async def log_command(self, ctx):
        config = self.get_config(ctx.guild.id)
        view = LogConfigView(self, ctx.guild.id, config)
        embed = await view.create_embed(ctx.author, ctx.guild)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    # Démarrage silencieux du système de logs
    
    # 1. Charger le gestionnaire principal
    manager = LogSystem(bot)
    await bot.add_cog(manager)
    # Gestionnaire principal chargé silencieusement
    
    # 2. Charger dynamiquement tous les modules util_*.py
    log_dir = Path(__file__).parent
    for file in log_dir.glob("util_*.py"):
        module_name = file.stem  # Retire l'extension .py
        try:
            # Importation du module
            full_path = f"{__package__}.{module_name}"
            module = importlib.import_module(full_path, package=__package__)
            
            # Appel de la fonction setup du module
            if hasattr(module, 'setup'):
                await module.setup(bot)
                # Module chargé silencieusement
            else:
                # Module sans setup détecté silencieusement
                pass
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {module_name}: {str(e)}")
            import traceback
            traceback.print_exc()