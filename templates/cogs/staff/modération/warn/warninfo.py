import os
import json
import discord
import asyncio
import math
import traceback
from discord.ext import commands
from discord import app_commands, ui
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
    HAS_CUSTOM_EMBED = True
except ImportError:
    config_manager = None
    HAS_CUSTOM_EMBED = False

# --- CONFIGURATION DES CHEMINS ---
CURRENT_DIR = Path(__file__).parent
DATA_PATH = CURRENT_DIR / "data"

# ==============================================================================
# -------------------------- SYSTÈME DE CONFIRMATION ---------------------------
# ==============================================================================

class WarnConfirmView(ui.View):
    """Vue de confirmation avant suppression définitive"""
    def __init__(self, target_user, guild_id, index, parent_view):
        super().__init__(timeout=30)
        self.target_user = target_user
        self.guild_id = guild_id
        self.index = index
        self.parent_view = parent_view

    @ui.button(label="Confirmer la suppression", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        file_path = DATA_PATH / str(self.guild_id) / f"{self.target_user.id}.json"
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if len(data["warns"]) > self.index:
                data["warns"].pop(self.index)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                self.parent_view.data = data
                self.parent_view.update_components()
                
                await interaction.response.edit_message(content="✅ Avertissement supprimé avec succès.", embed=None, view=None)
                await asyncio.sleep(2)
                await interaction.edit_original_response(content=None, embed=self.parent_view.get_embed(interaction.guild), view=self.parent_view)
            else:
                await interaction.response.send_message("❌ Cet avertissement n'existe plus.", ephemeral=True)
        except Exception as e:
            print(f"Erreur suppression: {e}")

    @ui.button(label="Annuler", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content=None, embed=self.parent_view.get_embed(interaction.guild), view=self.parent_view)

# ==============================================================================
# -------------------------- SYSTÈME DE PAGINATION -----------------------------
# ==============================================================================

class WarnDeleteSelect(ui.Select):
    def __init__(self, options, target_user, guild_id, parent_view):
        super().__init__(placeholder="❌ Sélectionner un avertissement à supprimer...", options=options)
        self.target_user = target_user
        self.guild_id = guild_id
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if not (interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.moderate_members):
            return await interaction.response.send_message("🚫 Permissions insuffisantes.", ephemeral=True)

        index_to_remove = int(self.values[0])
        confirm_view = WarnConfirmView(self.target_user, self.guild_id, index_to_remove, self.parent_view)
        await interaction.response.edit_message(content=f"⚠️ Voulez-vous vraiment supprimer l'avertissement **#{index_to_remove + 1}** ?", embed=None, view=confirm_view)

class WarnPaginationView(ui.View):
    def __init__(self, bot, data, user, guild_id, page=0):
        super().__init__(timeout=120)
        self.bot = bot
        self.data = data
        self.user = user
        self.guild_id = guild_id
        self.page = page
        self.per_page = 10 # Changé à 10 par page
        self.update_components()

    def update_components(self):
        self.clear_items()
        self.max_pages = max(1, math.ceil(len(self.data['warns']) / self.per_page))
        if self.page >= self.max_pages: self.page = max(0, self.max_pages - 1)

        # 1. AJOUT DU SÉLECTEUR (Avertissements de la page actuelle uniquement)
        start = self.page * self.per_page
        current_warns = self.data['warns'][start : start + self.per_page]
        
        if current_warns:
            options = []
            for i, _ in enumerate(current_warns):
                real_index = start + i
                options.append(discord.SelectOption(
                    label=f"Supprimer l'avertissement #{real_index + 1}", 
                    value=str(real_index)
                ))
            self.add_item(WarnDeleteSelect(options, self.user, self.guild_id, self))

        # 2. AJOUT DES BOUTONS (Sous le sélecteur)
        prev_btn = ui.Button(label="⬅️", style=discord.ButtonStyle.gray, disabled=(self.page == 0))
        prev_btn.callback = self.prev_page
        self.add_item(prev_btn)

        next_btn = ui.Button(label="➡️", style=discord.ButtonStyle.gray, disabled=(self.page >= self.max_pages - 1))
        next_btn.callback = self.next_page
        self.add_item(next_btn)

    def get_embed(self, guild):
        start = self.page * self.per_page
        end = start + self.per_page
        content = ""
        
        for i, w in enumerate(self.data['warns'][start:end]):
            raison_texte = w.get('raison') or w.get('reason') or "Aucune raison"
            staff_nom = w.get('staff_name') or w.get('mod_name') or "Inconnu"
            content += f"**#{start+i+1}** • Staff: **{staff_nom}** • {w.get('timestamp', 'Inconnue')}\n```\n{raison_texte}\n```\n"

        title = f"Casier de {self.user.display_name}"
        description = f"👤 **Utilisateur :** {self.user.mention}\n📊 **Total :** `{len(self.data['warns'])}` avertissement(s)\n\n{content or '*Aucun avertissement.*'}\n\n-# Page {self.page + 1}/{self.max_pages}"
        
        if config_manager:
            embed = config_manager.get_formatted_embed(guild, self.user, self.bot, title, description, guild.id)
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)
        
        embed.set_thumbnail(url=self.user.display_avatar.url)
        return embed

    async def prev_page(self, interaction: discord.Interaction):
        self.page -= 1
        self.update_components()
        await interaction.response.edit_message(embed=self.get_embed(interaction.guild), view=self)

    async def next_page(self, interaction: discord.Interaction):
        self.page += 1
        self.update_components()
        await interaction.response.edit_message(embed=self.get_embed(interaction.guild), view=self)

# ==============================================================================
# ------------------------------- COG WARNINFO ---------------------------------
# ==============================================================================

class WarnInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_styled_embed(self, guild, user, title, description):
        if config_manager:
            return config_manager.get_formatted_embed(guild, user, self.bot, title, description, guild.id)
        return discord.Embed(title=title, description=description, color=0x2b2d31)

    @commands.hybrid_command(name="warninfo", description="Consulter le casier judiciaire d'un membre")
    @app_commands.describe(utilisateur="Le membre à inspecter")
    @commands.check_any(commands.has_permissions(administrator=True), commands.has_permissions(moderate_members=True))
    async def warninfo(self, ctx: commands.Context, utilisateur: discord.User):
        file_path = DATA_PATH / str(ctx.guild.id) / f"{utilisateur.id}.json"
        
        if not file_path.exists():
            return await ctx.send(f"✅ **{utilisateur.display_name}** possède un casier vierge.", ephemeral=True)
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not data.get('warns'):
            return await ctx.send(f"✅ **{utilisateur.display_name}** possède un casier vierge.", ephemeral=True)

        view = WarnPaginationView(self.bot, data, utilisateur, ctx.guild.id)
        embed = view.get_embed(ctx.guild)
        
        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=embed, view=view)
        else:
            await ctx.send(embed=embed, view=view, reference=ctx.message)

    @warninfo.error
    async def warninfo_error(self, ctx, error):
        if isinstance(error, (commands.MissingPermissions, commands.CheckAnyFailure)):
            embed = self.get_styled_embed(ctx.guild, ctx.author, "🚫 Accès restreint", "Vous n'avez pas les permissions requises pour consulter les casiers.")
            await ctx.send(embed=embed, ephemeral=True)
        else:
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(WarnInfo(bot))