import discord
from discord.ext import commands

try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class ServerInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="guild", description="Affiche les informations détaillées du serveur.")
    async def guild_info(self, ctx: commands.Context):
        await ctx.defer()
        guild = ctx.guild
        title = f"📊 {guild.name}"
        
        owner = f"{guild.owner.mention if guild.owner else 'Inconnu'}"
        
        # Nouveau visuel sans Région ni Avantages
        description = (
            f"👑 **Propriétaire** : {owner}\n"
            f"📅 **Créé le** : <t:{int(guild.created_at.timestamp())}:D> (<t:{int(guild.created_at.timestamp())}:R>)\n"
            "\n"
            f"✨ **Boosts**\n"
            f"   ├ 📈 Niveau : `{guild.premium_tier}`\n"
            f"   └ 💎 Boosts : `{guild.premium_subscription_count}`\n"
            "\n"
            f"📊 **Statistiques**\n"
            f"   ├ 👥 Membres : `{guild.member_count}`\n"
            f"   ├ 📊 Rôles : `{len(guild.roles)}`\n"
            f"   └ 💬 Salons : `{len(guild.channels)}` (`{len(guild.text_channels)}` Texte / `{len(guild.voice_channels)}` Vocal)"
        )

        if config_manager:
            embed = config_manager.get_formatted_embed(guild, ctx.author, self.bot, title, description, guild.id)
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)

        if guild.icon: 
            embed.set_thumbnail(url=guild.icon.url)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        await ctx.send(embed=embed)

async def setup(bot):
    # Sécurité anti-doublon
    if bot.get_command("guild"):
        bot.remove_command("guild")
    await bot.add_cog(ServerInfoCog(bot))