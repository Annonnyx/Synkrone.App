import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import traceback

# --- SYSTÈME D'IMPORT CONFIG_MANAGER ---
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class Meme(commands.Cog):
    """Module dédié à la génération de memes via Reddit."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_url = "https://meme-api.com/gimme"

    @commands.hybrid_command(
        name="meme", 
        description="Affiche un meme aléatoire provenant de Reddit."
    )
    @app_commands.describe(subreddit="Optionnel : nom d'un subreddit spécifique (ex: dankmemes)")
    async def meme(self, ctx: commands.Context, subreddit: str = None):
        """
        Commande hybride pour obtenir un meme.
        Usage : !meme [subreddit] ou /meme [subreddit]
        """
        
        # 1. ACCUSÉ DE RÉCEPTION (Évite le timeout des slash commands)
        await ctx.defer()

        # 2. PRÉPARATION DE L'URL
        target_url = f"{self.api_url}/{subreddit}" if subreddit else self.api_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(target_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Vérification si le contenu est NSFW (sécurité admin)
                        if data.get("nsfw") and not ctx.channel.is_nsfw():
                            return await ctx.send("🔞 Le meme trouvé est classé NSFW. Veuillez utiliser cette commande dans un salon adapté.")

                        # 3. CONSTRUCTION DE L'EMBED
                        title = f"🤣 {data.get('title', 'Meme')}"
                        desc = f"Source : `r/{data.get('subreddit')}` | 👍 {data.get('ups')}"
                        image_url = data.get('url')

                        if config_manager:
                            embed = config_manager.get_formatted_embed(
                                guild=ctx.guild,
                                user=ctx.author,
                                bot=self.bot,
                                title=title,
                                description=desc,
                                target_id=ctx.guild.id if ctx.guild else None
                            )
                        else:
                            embed = discord.Embed(title=title, description=desc, color=0x2b2d31)
                        
                        embed.set_image(url=image_url)
                        embed.set_footer(text=f"Posté par u/{data.get('author')}")

                        # 4. ENVOI
                        if ctx.interaction:
                            await ctx.interaction.followup.send(embed=embed)
                        else:
                            await ctx.send(embed=embed, reference=ctx.message)

                    elif response.status == 404:
                        await ctx.send(f"❌ Le subreddit `r/{subreddit}` semble ne pas exister.")
                    else:
                        await ctx.send("❌ Impossible de récupérer un meme pour le moment.")

        except Exception as e:
            print(f"[ERROR - Meme] {e}")
            traceback.print_exc()
            error_msg = "❌ Une erreur technique est survenue lors de la récupération du meme."
            if ctx.interaction:
                await ctx.interaction.followup.send(error_msg, ephemeral=True)
            else:
                await ctx.send(error_msg)

async def setup(bot: commands.Bot):
    """Initialisation du Cog"""
    await bot.add_cog(Meme(bot))