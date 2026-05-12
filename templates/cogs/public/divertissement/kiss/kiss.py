########################################
# Imports et dépendances
########################################

import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path
import random
import traceback

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None


########################################
# 💋 Cog Kiss
# Commande /kiss — Envoie un bisou virtuel à un membre
########################################

class Kiss(commands.Cog):
    """Commande /kiss — Envoie un bisou virtuel à un membre."""

    def __init__(self, bot):
        self.bot = bot
        self.token = None  # Sera défini par setup()
        self.bot = bot

    async def send_kiss(self, ctx: commands.Context | discord.Interaction, membre: discord.Member):
        """Fonction pour envoyer un bisou, utilisable en commande hybride."""
        is_interaction = isinstance(ctx, discord.Interaction)
        
        try:
            if is_interaction:
                interaction = ctx
                await interaction.response.defer()
            
            # Chemin vers le dossier data local (à côté de kiss.py)
            data_dir = Path(__file__).parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            gif_files = list(data_dir.glob("*.gif"))
            if not gif_files:
                message = "❌ Aucun GIF trouvé dans le dossier data."
                if is_interaction:
                    return await interaction.followup.send(message, ephemeral=True)
                return await ctx.send(message)

            selected_gif = random.choice(gif_files)
            
            try:
                file = discord.File(selected_gif, filename="kiss.gif")
                if config_manager:
                    embed = config_manager.get_formatted_embed(
                        guild=interaction.guild if is_interaction else ctx.guild,
                        user=interaction.user if is_interaction else ctx.author,
                        bot=self.bot,
                        title="😘 Un bisou doux comme tout !",
                        description=f"{ctx.user.mention if is_interaction else ctx.author.mention} fait un bisou à {membre.mention} 💋",
                        target_id=interaction.guild_id if is_interaction else (ctx.guild.id if ctx.guild else None)
                    )
                else:
                    embed = discord.Embed(
                        title="😘 Un bisou doux comme tout !",
                        description=f"{ctx.user.mention if is_interaction else ctx.author.mention} fait un bisou à {membre.mention} 💋",
                        color=0xE91E63  # Rose pour les bisous
                    )
                embed.set_image(url="attachment://kiss.gif")

                if is_interaction:
                    await interaction.followup.send(
                        content=membre.mention,
                        embed=embed,
                        file=file
                    )
                else:
                    await ctx.send(
                        content=membre.mention,
                        embed=embed,
                        file=file
                    )
                    
            except Exception as e:
                print(f"[kiss.py] Erreur lors de la création de l'embed : {e}")
                error_msg = "❌ Une erreur est survenue lors de l'envoi du bisou."
                if is_interaction:
                    await interaction.followup.send(error_msg, ephemeral=True)
                else:
                    await ctx.send(error_msg)
                    
        except Exception as e:
            print(f"[kiss.py] Erreur inattendue : {e}")
            error_msg = "❌ Une erreur inattendue est survenue."
            if is_interaction:
                if not ctx.response.is_done():
                    await ctx.response.send_message(error_msg, ephemeral=True)
            else:
                await ctx.send(error_msg)

    @commands.hybrid_command(name="kiss", description="Envoie un bisou à un membre.")
    @app_commands.describe(membre="Le membre à embrasser")
    async def kiss(self, ctx: commands.Context | discord.Interaction, membre: discord.Member):
        """Commande hybride pour envoyer un bisou."""
        await self.send_kiss(ctx, membre)

    ########################################
    # Sync automatique des commandes
    ########################################

    @commands.Cog.listener()
    async def on_ready(self):
        if not getattr(self.bot, "_kiss_synced", False):
            try:
                await self.bot.tree.sync()
                self.bot._kiss_synced = True
            except Exception as e:
                print(f"❌ [kiss.py] Erreur de synchronisation : {e}")


########################################
# Setup du Cog
########################################

async def setup(bot: commands.Bot):
    await bot.add_cog(Kiss(bot))
