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
# 🥊 Cog Punch
# Commande /punch — Donne un coup de poing virtuel à un membre
########################################

class Punch(commands.Cog):
    """Commande /punch — Donne un coup de poing virtuel à un membre."""

    def __init__(self, bot):
        self.bot = bot
        self.token = None  # Sera défini par setup()
        self.bot = bot
        self.templates = [
            "🥊 {author} frappe {target} avec un direct du droit !",
            "👊 {author} assène un crochet à {target} !",
            "💢 {author} envoie une frappe tonitruante sur {target} !"
        ]

    async def send_punch(self, ctx: commands.Context | discord.Interaction, membre: discord.Member):
        """Fonction pour envoyer un coup de poing, utilisable en commande hybride."""
        is_interaction = isinstance(ctx, discord.Interaction)
        
        try:
            if is_interaction:
                interaction = ctx
                await interaction.response.defer()
            
            # Chemin vers le dossier data
            data_dir = Path(__file__).parent / "data"
            if not data_dir.exists():
                message = "❌ Le dossier data est introuvable."
                if is_interaction:
                    return await interaction.followup.send(message, ephemeral=True)
                return await ctx.send(message)
                
            gif_files = list(data_dir.glob("*.gif"))
            if not gif_files:
                message = "❌ Aucun GIF trouvé dans le dossier data."
                if is_interaction:
                    return await interaction.followup.send(message, ephemeral=True)
                return await ctx.send(message)

            selected_gif = random.choice(gif_files)
            message = random.choice(self.templates).format(
                author=ctx.user.mention if is_interaction else ctx.author.mention,
                target=membre.mention
            )

            try:
                file = discord.File(selected_gif, filename="punch.gif")
                if config_manager:
                    embed = config_manager.get_formatted_embed(
                        guild=interaction.guild if is_interaction else ctx.guild,
                        user=interaction.user if is_interaction else ctx.author,
                        bot=self.bot,
                        title="🥊 Ça fait mal !",
                        description=message,
                        target_id=interaction.guild_id if is_interaction else (ctx.guild.id if ctx.guild else None)
                    )
                else:
                    embed = discord.Embed(
                        title="🥊 Ça fait mal !",
                        description=message,
                        color=0xE74C3C  # Rouge pour punch
                    )
                embed.set_image(url="attachment://punch.gif")

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
                print(f"[punch.py] Erreur lors de la création de l'embed : {e}")
                error_msg = "❌ Une erreur est survenue lors de l'envoi du coup de poing."
                if is_interaction:
                    await interaction.followup.send(error_msg, ephemeral=True)
                else:
                    await ctx.send(error_msg)
                    
        except Exception as e:
            print(f"[punch.py] Erreur inattendue : {e}")
            error_msg = "❌ Une erreur inattendue est survenue."
            if is_interaction:
                if not ctx.response.is_done():
                    await ctx.response.send_message(error_msg, ephemeral=True)
            else:
                await ctx.send(error_msg)

    @commands.hybrid_command(name="punch", description="Frappe un membre.")
    @app_commands.describe(membre="Le membre à frapper")
    async def punch(self, ctx: commands.Context | discord.Interaction, membre: discord.Member):
        """Commande hybride pour frapper un membre."""
        await self.send_punch(ctx, membre)

    ########################################
    # Sync automatique des commandes
    ########################################

    @commands.Cog.listener()
    async def on_ready(self):
        if not getattr(self.bot, "_punch_synced", False):
            try:
                await self.bot.tree.sync()
                self.bot._punch_synced = True
            except:
                pass


########################################
# Setup du Cog
########################################

async def setup(bot: commands.Bot):
    await bot.add_cog(Punch(bot))
