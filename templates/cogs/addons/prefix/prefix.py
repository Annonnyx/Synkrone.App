import discord
from discord.ext import commands
import discord.ui as ui
import json
import os
from pathlib import Path

# --- PRÉFIXE GLOBAL ---
def _get_global_prefix(bot) -> str:
    """Retourne le préfixe global actif : BotAdmin en mémoire → bot_config.json → fallback '!'"""
    try:
        cog = bot.cogs.get('BotAdmin')
        if cog and hasattr(cog, 'default_prefix'):
            return cog.default_prefix
    except Exception:
        pass
    config_path = os.path.join('cogs', 'owner', 'commands', 'panelbot', 'bot_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                prefix = json.load(f).get('prefix')
                if prefix:
                    return prefix
        except Exception:
            pass
    return '!'

# --- CONFIGURATION & IMPORTS ---
# Importation du config_manager comme dans les autres scripts
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# --- FONCTION UTILITAIRE POUR LES EMBEDS ---
async def create_embed(guild, user, bot, title, description, color=0x2b2d31, **kwargs):
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
        color=color
    )
    
    if hasattr(bot, 'user') and hasattr(bot.user, 'avatar'):
        embed.set_footer(icon_url=bot.user.avatar.url)
    
    if user and hasattr(user, 'display_avatar') and user.display_avatar:
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
    elif user:
        embed.set_author(name=str(user))
        
    return embed

# --- GESTIONNAIRE DE DONNÉES ---
class PrefixManager:
    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
    
    def get_config(self, guild_id):
        """Récupère la configuration des préfixes pour un serveur"""
        path = self.data_dir / f"{guild_id}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"prefixes": [], "disable_global": False}  # Par défaut, aucun préfixe personnalisé et global activé
    
    def save_config(self, guild_id, data):
        """Sauvegarde la configuration des préfixes pour un serveur"""
        with open(self.data_dir / f"{guild_id}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    
    def get_all_prefixes(self, guild_id):
        """Récupère tous les préfixes (serveur + global)"""
        server_config = self.get_config(guild_id)
        server_prefixes = server_config.get("prefixes", [])
        disable_global = server_config.get("disable_global", False)
        
        # Préfixe global par défaut
        global_prefix = "!"
        
        # Si le global est désactivé, n'utiliser que les préfixes de serveur
        if disable_global:
            return server_prefixes if server_prefixes else []
        
        # Sinon, combiner les préfixes de serveur et le préfixe global
        all_prefixes = server_prefixes.copy() if server_prefixes else []
        if global_prefix not in all_prefixes:  # Éviter les doublons
            all_prefixes.append(global_prefix)
        
        return all_prefixes

# --- MODAL DE CONFIGURATION ---
class PrefixModal(ui.Modal, title="Configuration des préfixes"):
    def __init__(self, cog, guild_id, view):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.view = view
        self.config = cog.prefix_manager.get_config(guild_id)
        
        # Créer 5 champs pour les préfixes
        prefixes_list = self.config.get("prefixes", [])
        
        self.prefix1 = ui.TextInput(
            label="Préfixe 1",
            placeholder="Entrez le premier préfixe (ex: !)",
            required=False,
            max_length=5,
            default=prefixes_list[0] if len(prefixes_list) > 0 else ""
        )
        
        self.prefix2 = ui.TextInput(
            label="Préfixe 2", 
            placeholder="Entrez le deuxième préfixe (ex: ?)",
            required=False,
            max_length=5,
            default=prefixes_list[1] if len(prefixes_list) > 1 else ""
        )
        
        self.prefix3 = ui.TextInput(
            label="Préfixe 3",
            placeholder="Entrez le troisième préfixe (ex: $)",
            required=False, 
            max_length=5,
            default=prefixes_list[2] if len(prefixes_list) > 2 else ""
        )
        
        self.prefix4 = ui.TextInput(
            label="Préfixe 4",
            placeholder="Entrez le quatrième préfixe (ex: %)",
            required=False,
            max_length=5,
            default=prefixes_list[3] if len(prefixes_list) > 3 else ""
        )
        
        self.prefix5 = ui.TextInput(
            label="Préfixe 5",
            placeholder="Entrez le cinquième préfixe (ex: &)",
            required=False,
            max_length=5,
            default=prefixes_list[4] if len(prefixes_list) > 4 else ""
        )
        
        self.add_item(self.prefix1)
        self.add_item(self.prefix2)
        self.add_item(self.prefix3)
        self.add_item(self.prefix4)
        self.add_item(self.prefix5)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Récupérer les préfixes non vides
        prefixes = []
        for prefix_field in [self.prefix1, self.prefix2, self.prefix3, self.prefix4, self.prefix5]:
            if prefix_field.value.strip():
                prefixes.append(prefix_field.value.strip())
        
        # Sauvegarder la configuration (sans changer l'état du préfixe global)
        current_config = self.cog.prefix_manager.get_config(self.guild_id)
        self.cog.prefix_manager.save_config(self.guild_id, {
            "prefixes": prefixes,
            "disable_global": current_config.get("disable_global", False)
        })
        
        # Reconstruire la vue et mettre à jour le message
        await interaction.response.defer()
        if interaction.message:
            self.view._build()
            updated_embed = await self.view.create_embed(interaction.user, interaction.guild)
            await interaction.message.edit(embed=updated_embed, view=self.view)

# --- VUE INTERACTIVE ---
class PrefixView(ui.View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self._build()

    def _build(self):
        self.clear_items()
        config = self.cog.prefix_manager.get_config(self.guild_id)
        prefixes = config.get("prefixes", [])
        disable_global = config.get("disable_global", False)

        # --- Ligne 0 : sélecteur multi-choix pour supprimer des préfixes ---
        if prefixes:
            opts = [
                discord.SelectOption(label=f"Préfixe : {p}", value=str(i))
                for i, p in enumerate(prefixes)
            ]
            sel = ui.Select(
                placeholder="Sélectionner les préfixes à supprimer...",
                options=opts,
                min_values=1,
                max_values=len(prefixes),
                row=0,
            )
            sel.callback = self._remove_prefixes
            self.add_item(sel)

        # --- Ligne 1 : boutons d'action ---
        has_custom = bool(prefixes) or disable_global
        btn_config = ui.Button(
            label="Configurer", emoji="⚙️",
            style=discord.ButtonStyle.green if has_custom else discord.ButtonStyle.gray,
            row=1,
        )
        btn_config.callback = self._btn_config
        self.add_item(btn_config)

        btn_toggle = ui.Button(
            label="Activer préfixe" if disable_global else "Désactiver préfixe",
            emoji="🔧",
            style=discord.ButtonStyle.red if disable_global else discord.ButtonStyle.green,
            disabled=not bool(prefixes) and not disable_global,
            row=1,
        )
        btn_toggle.callback = self._btn_toggle_global
        self.add_item(btn_toggle)

        btn_vider = ui.Button(
            label="Vider", emoji="🗑️",
            style=discord.ButtonStyle.red,
            row=1,
        )
        btn_vider.callback = self._btn_reset
        self.add_item(btn_vider)

    async def _check_admin(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Seul un administrateur peut utiliser cette commande.", ephemeral=True
            )
            return False
        return True

    async def _remove_prefixes(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return
        selected_indices = {int(v) for v in interaction.data['values']}
        config = self.cog.prefix_manager.get_config(self.guild_id)
        new_prefixes = [p for i, p in enumerate(config.get("prefixes", [])) if i not in selected_indices]
        self.cog.prefix_manager.save_config(self.guild_id, {
            "prefixes": new_prefixes,
            "disable_global": config.get("disable_global", False),
        })
        self._build()
        await interaction.response.edit_message(
            embed=await self.create_embed(interaction.user, interaction.guild), view=self
        )

    async def _btn_config(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return
        await interaction.response.send_modal(PrefixModal(self.cog, self.guild_id, self))

    async def _btn_toggle_global(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return
        config = self.cog.prefix_manager.get_config(self.guild_id)
        self.cog.prefix_manager.save_config(self.guild_id, {
            "prefixes": config.get("prefixes", []),
            "disable_global": not config.get("disable_global", False),
        })
        self._build()
        await interaction.response.edit_message(
            embed=await self.create_embed(interaction.user, interaction.guild), view=self
        )

    async def _btn_reset(self, interaction: discord.Interaction):
        if not await self._check_admin(interaction):
            return
        self.cog.prefix_manager.save_config(self.guild_id, {"prefixes": [], "disable_global": False})
        self._build()
        await interaction.response.edit_message(
            embed=await self.create_embed(interaction.user, interaction.guild), view=self
        )

    async def create_embed(self, user, guild):
        config = self.cog.prefix_manager.get_config(guild.id)
        prefixes = config.get("prefixes", [])
        disable_global = config.get("disable_global", False)
        global_prefix = _get_global_prefix(self.cog.bot)

        title = "⚙️ Configuration des préfixes"
        status_emoji = "🔴" if disable_global else "🟢"
        global_status = "Désactivé" if disable_global else "Activé"
        description = "Gérez les préfixes de commandes pour ce serveur.\n\n"

        if prefixes:
            prefixes_inline = " ".join(f"`{p}`" for p in prefixes)
            description += f"> 🔤 Préfixes actifs : {prefixes_inline}\n\n"

        description += f"**Préfixe général {status_emoji} `[{global_prefix}]` :** {global_status}"

        embed = await create_embed(guild, user, self.cog.bot, title, description, color=None)

        return embed

# --- COG PRINCIPAL ---
class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prefix_manager = PrefixManager()
    
    @commands.hybrid_command(name="prefix", description="Configure les préfixes de commandes du serveur")
    @commands.has_permissions(administrator=True)
    async def prefix_command(self, ctx):
        """Affiche le panneau de configuration des préfixes"""
        view = PrefixView(self, ctx.guild.id)
        embed = await view.create_embed(ctx.author, ctx.guild)
        await ctx.send(embed=embed, view=view)

# --- SETUP ---
async def setup(bot):
    await bot.add_cog(Prefix(bot))
