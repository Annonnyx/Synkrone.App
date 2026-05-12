import os
import json
import discord
import asyncio
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
# -------------------------- SYSTÈME DE PAGINATION -----------------------------
# ==============================================================================

class WarnPagination(ui.View):
    def __init__(self, pages, current_page, embed_base_func, guild, author):
        super().__init__(timeout=60)
        self.pages = pages
        self.current_page = current_page
        self.embed_base_func = embed_base_func
        self.guild = guild
        self.author = author

    async def update_view(self, interaction: discord.Interaction):
        embed = self.embed_base_func(self.guild, self.author, self.pages[self.current_page], self.current_page + 1, len(self.pages))
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="⬅️", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_view(interaction)
        else:
            await interaction.response.send_message("Vous êtes déjà sur la première page.", ephemeral=True)

    @ui.button(label="➡️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_view(interaction)
        else:
            await interaction.response.send_message("Vous êtes déjà sur la dernière page.", ephemeral=True)

# ==============================================================================
# ----------------------------- COG WARNLIST -----------------------------------
# ==============================================================================

class WarnList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        DATA_PATH.mkdir(parents=True, exist_ok=True)

    def get_styled_embed(self, guild, user, title, description):
        """Utilise le manager d'embed pour le style (Auteur, Footer, etc)"""
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=guild, user=user, bot=self.bot,
                title=title, description=description,
                target_id=guild.id if guild else None
            )
        return discord.Embed(title=title, description=description, color=0x2b2d31)

    def format_page_embed(self, guild, author, content, page_num, total_pages):
        """Génère l'embed avec le numéro de page en bas de description"""
        full_content = f"{content}\n\n-# Page {page_num}/{total_pages} - `/warninfo @Utilisateur`"
        embed = self.get_styled_embed(guild, author, "📋 Liste des Avertissements", full_content)
        return embed

    @commands.hybrid_command(name="warnlist", description="Affiche les avertissements du serveur")
    @commands.check_any(commands.has_permissions(administrator=True), commands.has_permissions(moderate_members=True))
    async def warnlist(self, ctx: commands.Context):
        try:
            await ctx.defer()

            guild_path = DATA_PATH / str(ctx.guild.id)
            all_warns = []
            user_counts = []

            # 1. RÉCUPÉRATION DES DONNÉES
            if guild_path.exists():
                for file in guild_path.glob("*.json"):
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            warns = data.get('warns', [])
                            if warns:
                                user_id = file.stem
                                user_counts.append((user_id, len(warns)))
                                for w in warns:
                                    w['cible_id'] = user_id
                                    all_warns.append(w)
                    except: continue

            if not all_warns:
                return await ctx.send("✨ Aucun avertissement enregistré sur ce serveur.")

            # 2. LES 3 DERNIERS WARNS (Triés par date)
            # Format : [Date] Heure - @Cible warn par @Staff - <Raison>
            recent_warns = sorted(all_warns, key=lambda x: x.get('timestamp', ''), reverse=True)[:3]
            
            recent_text = "### 🕒 3 Derniers Avertissements\n"
            for w in recent_warns:
                cible_mention = f"<@{w['cible_id']}>"
                staff_mention = f"<@{w['staff_id']}>"
                date_str = w.get('timestamp', 'Inconnue').replace(' à ', ' - ')
                raison = w.get('raison', 'Aucune')
                recent_text += f"[{date_str}] {cible_mention} warn par {staff_mention} - {raison}\n"

            # 3. TOP CLASSEMENT ET PAGINATION
            user_counts.sort(key=lambda x: x[1], reverse=True)
            
            pages_content = []
            for i in range(0, len(user_counts), 25):
                chunk = user_counts[i:i + 25]
                page_text = recent_text + "\n### 🏆 Classement\n"
                
                for index, (u_id, count) in enumerate(chunk, i + 1):
                    member = ctx.guild.get_member(int(u_id))
                    mention = member.mention if member else f"Utilisateur inconnu (`{u_id}`)"
                    medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"`#{index}`"
                    page_text += f"{medal} {mention} : **{count}** warn(s)\n"
                
                pages_content.append(page_text)

            # 4. ENVOI
            current_page = 0
            embed = self.format_page_embed(ctx.guild, ctx.author, pages_content[current_page], 1, len(pages_content))
            
            view = WarnPagination(pages_content, current_page, self.format_page_embed, ctx.guild, ctx.author) if len(pages_content) > 1 else None
            
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed, view=view)
            else:
                await ctx.send(embed=embed, view=view, reference=ctx.message)

        except Exception as e:
            print(f"[ERROR - WarnList] {e}")
            traceback.print_exc()

    @warnlist.error
    async def warnlist_error(self, ctx, error):
        if isinstance(error, (commands.MissingPermissions, commands.CheckAnyFailure)):
            embed = self.get_styled_embed(ctx.guild, ctx.author, "🚫 Accès restreint", "Vous n'avez pas les permissions requises pour voir cette liste.")
            await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WarnList(bot))