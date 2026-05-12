import discord
from discord.ext import commands
from pathlib import Path
import asyncio
import traceback

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# ----------------------------- COG PINGPONG -----------------------------------
# ==============================================================================

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ping_gif_path = Path(__file__).parent / "pingpong.gif"

    @commands.hybrid_command(
        name="ping", 
        description="Affiche la latence du bots."
    )
    async def ping(self, ctx: commands.Context):
        
        try:
            # 1. ACCUSÉ DE RÉCEPTION (Utile pour les Slash Commands)
            await ctx.defer(ephemeral=False)

            # 2. CONSTRUCTION DE L'EMBED
            title_loading = "⌛ Recherche en cours..."
            desc_loading = "Calcul de la latence de vos services..."

            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=ctx.guild,
                    user=ctx.author,
                    bot=self.bot,
                    title=title_loading,
                    description=desc_loading,
                    target_id=ctx.guild.id if ctx.guild else None
                )
            else:
                embed = discord.Embed(title=title_loading, description=desc_loading, color=0x2b2d31)

            # 3. GESTION DU GIF
            file = None
            if self.ping_gif_path.exists():
                file = discord.File(str(self.ping_gif_path), filename="pingpong.gif")
                embed.set_image(url="attachment://pingpong.gif")

            # 4. ENVOI INITIAL AVEC RÉPONSE NATIVE
            # On vérifie si c'est une interaction (Slash) ou un message (Prefix)
            if ctx.interaction:
                # Pour Slash, on utilise followup puisqu'on a fait un defer()
                msg = await ctx.send(embed=embed, file=file)
            else:
                # Pour Prefix, on utilise l'argument reference pour "Répondre" au message
                # mention_author=True simule le comportement d'une réponse avec ping
                msg = await ctx.send(embed=embed, file=file, reference=ctx.message, mention_author=True)

            # 5. CALCUL LATENCE
            await asyncio.sleep(0.5) 
            latency = round(self.bot.latency * 1000)
            
            embed.title = "⌛ Pong !"
            embed.description = f"Ma latence est de **{latency}ms**"

            # 6. MISE À JOUR
            if ctx.interaction:
                await ctx.interaction.edit_original_response(embed=embed)
            else:
                await msg.edit(embed=embed)

        except Exception as e:
            print(f"[ERROR - Ping] Une erreur est survenue :")
            traceback.print_exc()
            
            error_msg = "❌ Une erreur est survenue lors de l'exécution de la commande."
            if ctx.interaction:
                await ctx.interaction.followup.send(error_msg, ephemeral=True)
            else:
                await ctx.send(error_msg, reference=ctx.message)

async def setup(bot: commands.Bot):
    if bot.get_command("ping"):
        bot.remove_command("ping")
    await bot.add_cog(Ping(bot))