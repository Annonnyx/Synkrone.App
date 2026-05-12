import discord
from discord.ext import commands

# Import de ton manager personnalisé
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class ChannelInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="channel", description="Affiche les informations détaillées d'un salon.")
    async def channel_info(self, ctx: commands.Context, salon: discord.abc.GuildChannel):
        await ctx.defer()
        guild = ctx.guild
        
        # Titre épuré sans le nom du salon
        title = "📍 Informations du salon"
        
        # Traduction propre des types de salons
        stype = (str(type(salon).__name__)
                 .replace("TextChannel", "Texte")
                 .replace("VoiceChannel", "Vocal")
                 .replace("CategoryChannel", "Catégorie")
                 .replace("ForumChannel", "Forum")
                 .replace("StageChannel", "Stage"))
        
        # Construction de la description avec la mention tout en haut (sans le sujet)
        description = (
            f"**{salon.mention}**\n\n"
            f"🆔 **ID** : `{salon.id}`\n"
            f"📅 **Création** : <t:{int(salon.created_at.timestamp())}:D> (<t:{int(salon.created_at.timestamp())}:R>)\n"
            f"📁 **Catégorie** : {salon.category.mention if salon.category else 'Aucune'}\n"
            f"🏷️ **Type** : `{stype}`\n"
        )

        if config_manager:
            embed = config_manager.get_formatted_embed(guild, ctx.author, self.bot, title, description, guild.id)
            
            # On récupère et préserve le footer de ton config_manager
            footer_text = embed.footer.text if embed.footer and embed.footer.text else ""
            footer_icon = embed.footer.icon_url if embed.footer and embed.footer.icon_url else None
            
            if footer_text:
                if footer_icon:
                    embed.set_footer(text=footer_text, icon_url=footer_icon)
                else:
                    embed.set_footer(text=footer_text)
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)

        await ctx.send(embed=embed)

async def setup(bot):
    if bot.get_command("channel"):
        bot.remove_command("channel")
    await bot.add_cog(ChannelInfo(bot))