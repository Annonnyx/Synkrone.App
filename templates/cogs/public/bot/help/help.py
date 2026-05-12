# Version : 8.0.0 - Full Integration with Config Manager
import discord
from discord.ext import commands
from discord import ui
from pathlib import Path
import json
import traceback

# ===================== IMPORTATION CONFIG MANAGER ====================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ===================== RÉSOLUTION DU PRÉFIXE ========================
def _get_help_prefix(bot, guild_id: int) -> str:
    """
    Retourne le préfixe à afficher dans le help, par priorité :
      1. 1er préfixe personnalisé du serveur (module prefix.py)
      2. Préfixe du cog BotAdmin en mémoire (panelbot)
      3. bot_config.json (panelbot)
      4. Fallback '!'
    """
    import os, json as _json
    # 1. Préfixe serveur (prefix.py)
    try:
        prefix_file = os.path.join(
            'cogs', 'addons', 'prefix', 'data', f'{guild_id}.json'
        )
        if os.path.exists(prefix_file):
            with open(prefix_file, 'r', encoding='utf-8') as f:
                data = _json.load(f)
            server_prefixes = data.get('prefixes', [])
            if server_prefixes:
                return server_prefixes[0]
    except Exception:
        pass
    # 2. BotAdmin en mémoire (panelbot, sans redémarrage)
    try:
        cog = bot.cogs.get('BotAdmin')
        if cog and hasattr(cog, 'default_prefix'):
            return cog.default_prefix
    except Exception:
        pass
    # 3. bot_config.json (panelbot)
    try:
        cfg = os.path.join('cogs', 'owner', 'commands', 'panelbot', 'bot_config.json')
        if os.path.exists(cfg):
            with open(cfg, 'r', encoding='utf-8') as f:
                prefix = _json.load(f).get('prefix')
            if prefix:
                return prefix
    except Exception:
        pass
    return '!'

# Variable pour activer/désactiver la génération automatique des JSON
AUTO_GENERATE_JSON = False

# ==============================================================================
# --------------------------- COMPONENTS ---------------------------------------
# ==============================================================================

class HelpSelect(ui.Select):
    def __init__(self, author, bot, categories_data):
        options = []
        for file_id, data in sorted(categories_data.items()):
            label = data.get("category_name", file_id.capitalize())
            emoji = data.get("emoji", "📂")
            options.append(discord.SelectOption(label=label, value=file_id, emoji=emoji))
        
        super().__init__(placeholder="📍 Choisissez une catégorie...", options=options)
        self.author = author
        self.bot = bot
        self.categories_data = categories_data

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Ce menu ne vous appartient pas.", ephemeral=True)
            
        file_id = self.values[0]
        embed = self.view.create_category_embed(file_id, self.author, interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(ui.View):
    def __init__(self, author, bot, categories_data):
        super().__init__(timeout=180)
        self.author = author
        self.bot = bot
        self.categories_data = categories_data
        if categories_data:
            self.add_item(HelpSelect(author, bot, categories_data))

    def create_category_embed(self, file_id, author, guild):
        data = self.categories_data.get(file_id, {})
        emoji = data.get("emoji", "📂")
        cat_name = data.get("category_name", file_id.capitalize())
        cat_desc = data.get("category_description", "")
        sections = data.get("sections", {})

        # Résolution du préfixe actif pour ce serveur
        prefix = _get_help_prefix(self.bot, guild.id if guild else 0)

        # Construction de la description
        content = f"*{cat_desc}*\n" if cat_desc else ""

        # Ligne des préfixes configurés (si plusieurs)
        try:
            import os as _os, json as _json
            prefix_file = _os.path.join('cogs', 'addons', 'prefix', 'data', f'{guild.id}.json')
            if guild and _os.path.exists(prefix_file):
                with open(prefix_file, 'r', encoding='utf-8') as _f:
                    _data = _json.load(_f)
                server_prefixes = _data.get('prefixes', [])
                if len(server_prefixes) >= 1:
                    prefixes_str = " ".join(f"`{p}`" for p in server_prefixes)
                    content += f"-# *Préfixes configurés : {prefixes_str}*\n"
        except Exception:
            pass
        
        if not sections:
            content += "\n*Aucune section trouvée dans cette catégorie.*"
        else:
            for section_title, commands_list in sections.items():
                content += f"\n**─── {section_title.upper()} ───**\n"
                for cmd_custom, desc in commands_list.items():
                    cmd_display = cmd_custom.replace("{prefix}", prefix)
                    desc_display = desc.replace("{prefix}", prefix) if desc else desc
                    content += f"› {cmd_display} : **{desc_display}**\n"

        title = f"{emoji} Aide : {cat_name}"
        
        # --- UTILISATION DU CONFIG MANAGER (Comme dans pingpong.py) ---
        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=guild,
                user=author,
                bot=self.bot,
                title=title,
                description=content,
                target_id=guild.id if guild else None
            )
        else:
            embed = discord.Embed(title=title, description=content, color=0x2b2d31)
            embed.set_author(name=f"Demandé par {author.display_name}", icon_url=author.display_avatar.url)
            
        return embed

# ==============================================================================
# --------------------------- COG HELP -----------------------------------------
# ==============================================================================

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = Path(__file__).parent
        self.json_folder = self.path / "catégorie"
        self.json_folder.mkdir(exist_ok=True)
        
        # Supprime l'aide par défaut pour éviter le conflit initial
        if self.bot.get_command('help'):
            self.bot.remove_command('help')

    @commands.Cog.listener()
    async def on_ready(self):
        if AUTO_GENERATE_JSON:
            self.sync_json_categories()

    def sync_json_categories(self):
        """Scanne les commandes et génère les JSON de base."""
        try:
            found_data = {}
            for command in self.bot.walk_commands():
                if command.hidden or isinstance(command, commands.Group) or not command.cog:
                    continue
                
                module_parts = command.cog.__module__.split('.')
                if len(module_parts) >= 2:
                    folder_name = module_parts[1]
                    if folder_name not in found_data:
                        found_data[folder_name] = {}
                    
                    # Format par défaut pour la génération
                    cmd_key = f"`/{command.name}`"
                    found_data[folder_name][cmd_key] = command.description or "Aucune description."

            for folder, cmds in found_data.items():
                file_path = self.json_folder / f"{folder}.json"
                
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        current_json = json.load(f)
                else:
                    current_json = {
                        "emoji": "📂",
                        "category_name": folder.capitalize(),
                        "category_description": f"Commandes de la catégorie {folder}.",
                        "sections": { "Général": {} }
                    }

                # Vérification de l'existence des commandes dans les sections
                updated = False
                for cmd_name, cmd_desc in cmds.items():
                    exists = False
                    for section in current_json.get("sections", {}).values():
                        if cmd_name in section:
                            exists = True
                            break
                    
                    if not exists:
                        if "sections" not in current_json: current_json["sections"] = {"Général": {}}
                        first_section = list(current_json["sections"].keys())[0]
                        current_json["sections"][first_section][cmd_name] = cmd_desc
                        updated = True

                if updated or not file_path.exists():
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(current_json, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"[HELP ERROR] Sync JSON : {e}")

    def load_json_data(self):
        """Charge les JSON pour le menu."""
        data = {}
        for file in self.json_folder.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data[file.stem] = json.load(f)
            except Exception:
                pass
        return data

    @commands.hybrid_command(name="help", description="Affiche le centre d'aide interactif.")
    async def help(self, ctx: commands.Context):
        try:
            # Pour le help, on peut aussi faire un defer si on a beaucoup de JSON
            if ctx.interaction:
                await ctx.defer(ephemeral=False)

            categories_data = self.load_json_data()
            if not categories_data:
                return await ctx.send("❌ Aucun module d'aide trouvé.")

            view = HelpView(ctx.author, self.bot, categories_data)
            
            # Recherche du module par défaut (premier disponible)
            default_cat = None
            for file_id, data in categories_data.items():
                default_cat = file_id
                break
            
            if not default_cat:
                default_cat = list(categories_data.keys())[0]
                
            embed = view.create_category_embed(default_cat, ctx.author, ctx.guild)
            
            if ctx.interaction:
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(embed=embed, view=view, reference=ctx.message, mention_author=True)

        except Exception:
            traceback.print_exc()
            await ctx.send("❌ Une erreur est survenue lors de l'ouverture du menu d'aide.")

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCommand(bot))