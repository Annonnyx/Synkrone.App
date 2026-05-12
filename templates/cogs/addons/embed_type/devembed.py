import discord
from discord.ext import commands
import json
import os
from .utils import EmbedCustomizerView

class DevEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="devembed", help="Modifier le style global de l'embed par défaut du bot.")
    async def devembed(self, ctx: commands.Context):
        # Vérification Owner
        if not await ctx.bot.is_owner(ctx.author):
            return await ctx.send("❌ Accès restreint aux owners du bot.")

        view = EmbedCustomizerView(False, None, self.bot, ctx.author.id)
        await ctx.send(embed=view.generate_preview_embed(ctx.author, ctx.guild), view=view)

async def setup(bot):
    await bot.add_cog(DevEmbed(bot))