import discord
from discord.ext import commands
from discord import app_commands
from .utils import EmbedCustomizerView

class ServEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="servembed", description="Personnaliser l'apparence des embeds du serveur.")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def servembed(self, ctx: commands.Context):
        if ctx.interaction: 
            await ctx.defer(ephemeral=True)
            
        view = EmbedCustomizerView(True, ctx.guild.id, self.bot, ctx.author.id)
        await ctx.send(embed=view.generate_preview_embed(ctx.author, ctx.guild), view=view, ephemeral=True)

    @servembed.error
    async def servembed_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, (commands.MissingPermissions, app_commands.MissingPermissions)):
            if ctx.interaction:
                if ctx.interaction.response.is_done():
                    return await ctx.interaction.followup.send(
                        "❌ Accès restreint aux administrateurs du serveur.",
                        ephemeral=True,
                    )
                return await ctx.interaction.response.send_message(
                    "❌ Accès restreint aux administrateurs du serveur.",
                    ephemeral=True,
                )
            return await ctx.send("❌ Accès restreint aux administrateurs du serveur.")
        raise error

async def setup(bot):
    await bot.add_cog(ServEmbed(bot))