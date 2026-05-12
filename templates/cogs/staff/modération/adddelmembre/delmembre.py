import discord
from discord.ext import commands
from typing import Optional, Union
import traceback

try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class DelMembre(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, ctx, title, description):
        if config_manager:
            return config_manager.get_formatted_embed(guild=ctx.guild, user=ctx.author, bot=self.bot, title=title, description=description)
        return discord.Embed(title=title, description=description, color=discord.Color.red())

    @commands.hybrid_command(
        name="delmembre", 
        description="Masque le salon pour des membres/rôles ou tout le monde (@everyone)"
    )
    @commands.has_permissions(manage_channels=True)
    async def del_membre(
        self, 
        ctx: commands.Context, 
        cible: Optional[Union[discord.Member, discord.Role]] = None,
        cible2: Optional[Union[discord.Member, discord.Role]] = None,
        cible3: Optional[Union[discord.Member, discord.Role]] = None
    ):
        await ctx.defer(ephemeral=True)
        
        targets = [t for t in [cible, cible2, cible3] if t is not None]
        is_everyone = False
        if not targets:
            targets = [ctx.guild.default_role]
            is_everyone = True

        removed_mentions = []

        try:
            for t in targets:
                if isinstance(t, discord.Role) and t.is_default():
                    # POUR EVERYONE : On masque explicitement le salon
                    await ctx.channel.set_permissions(t, view_channel=False)
                    removed_mentions.append("@everyone")
                else:
                    # POUR MEMBRES/ROLES : On réinitialise (ils perdent leur accès spécifique)
                    await ctx.channel.set_permissions(t, overwrite=None)
                    removed_mentions.append(t.mention)

            title = "🔒 Salon Masqué / Accès Retiré"
            desc = "Le salon est désormais **masqué** (ou accès réinitialisé) pour :\n" + "\n".join([f"• {m}" for m in removed_mentions])
            
            await ctx.send(embed=self.create_embed(ctx, title, desc), ephemeral=True)

        except Exception:
            traceback.print_exc()
            await ctx.send("❌ Erreur lors de la fermeture du salon.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(DelMembre(bot))