import discord
from discord.ext import commands

# Import de ton manager pour les embeds personnalisés
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class WhoisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="whois", description="Affiche les informations d'un membre.")
    async def whois(self, ctx: commands.Context, membre: discord.Member = None):
        # Informe Discord que le bot traite la demande
        await ctx.defer()
        
        target = membre or ctx.author
        guild = ctx.guild
        title = f"👤 {target.display_name}"
        
        # Récupération des rôles (exclut @everyone, limite à 10 pour l'affichage, ordre du plus haut au plus bas)
        roles = [r.mention for r in reversed(target.roles) if r.name != "@everyone"]

        description = (f"🆔 **ID** : `{target.id}`\n"
                   f"🎂 **Création** : <t:{int(target.created_at.timestamp())}:R>\n"
                   f"🚪 **Arrivée** : <t:{int(target.joined_at.timestamp())}:R>\n\n"
                   f"### Rôles ({len(roles)})\n" + (" ".join(roles[:10]) if roles else "Aucun"))

        # Construction de l'embed via le manager ou par défaut
        if config_manager:
            embed = config_manager.get_formatted_embed(guild, ctx.author, self.bot, title, description, guild.id)
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)

        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    # Sécurité : on retire la commande si elle est déjà enregistrée par un autre fichier
    if bot.get_command("whois"):
        bot.remove_command("whois")
    
    await bot.add_cog(WhoisCog(bot))