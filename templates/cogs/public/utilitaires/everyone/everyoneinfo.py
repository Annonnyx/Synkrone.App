import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
from datetime import datetime, timedelta, timezone
from collections import Counter

# ==============================================================================
# --------------------------- IMPORTATION MANAGER ------------------------------
# ==============================================================================
try:
    from .utils import config_manager
except ImportError:
    try:
        from cogs.addons.embed_type.utils import config_manager
    except ImportError:
        config_manager = None

# ==============================================================================
# --------------------------- FONCTION DE CALCUL -------------------------------
# ==============================================================================

async def create_stats_embed(bot, guild, hours, time_text, requester):
    """Génère l'embed des statistiques via le manager sans footer additionnel."""
    
    time_limit = datetime.now(timezone.utc) - timedelta(hours=hours)
    total_pings = 0
    user_pings = Counter()

    for channel in guild.text_channels:
        try:
            if not channel.permissions_for(guild.me).read_message_history:
                continue

            async for message in channel.history(after=time_limit, limit=None):
                if message.mention_everyone:
                    total_pings += 1
                    user_pings[message.author] += 1
        except Exception:
            continue

    title = f"📢 Rapport des Pings - {time_text}"
    
    top_5_text = ""
    if user_pings:
        for i, (user, count) in enumerate(user_pings.most_common(5), 1):
            top_5_text += f"{i}. {user.mention} : `{count}` pings\n"
    else:
        top_5_text = "Aucun ping détecté sur cette période."

    description = (
        f"**Quantité totale**\n"
        f"**{total_pings}** pings (@everyone/@here)\n\n"
        f"**🏆 Top 5 des tagueurs**\n"
        f"{top_5_text}"
    )

    if config_manager:
        embed = config_manager.get_formatted_embed(
            guild=guild, 
            user=requester, 
            bot=bot, 
            title=title, 
            description=description, 
            target_id=guild.id
        )
    else:
        embed = discord.Embed(title=title, description=description, color=discord.Color.orange())

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    return embed

# ==============================================================================
# --------------------------- INTERFACE (UI) -----------------------------------
# ==============================================================================

class TimeSelect(Select):
    def __init__(self, current_value):
        options = [
            discord.SelectOption(label="1 heure", value="1", description="Dernière heure"),
            discord.SelectOption(label="3 heures", value="3", description="Dernières 3 heures"),
            discord.SelectOption(label="6 heures", value="6", description="Dernières 6 heures"),
            discord.SelectOption(label="12 heures", value="12", description="Dernières 12 heures"),
            discord.SelectOption(label="24 heures", value="24", description="Dernières 24 heures"),
            discord.SelectOption(label="48 heures", value="48", description="Derniers 2 jours"),
            discord.SelectOption(label="7 jours", value="168", description="Dernière semaine")
        ]
        
        # Définit l'option sélectionnée comme "default" pour qu'elle reste affichée
        for option in options:
            if option.value == current_value:
                option.default = True
                
        super().__init__(placeholder="Changer la période...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        selected_value = self.values[0]
        time_text = next(opt.label for opt in self.options if opt.value == selected_value)
        
        await interaction.edit_original_response(content=f"🔄 Recalcul pour **{time_text}** en cours...", view=None, embed=None)

        embed = await create_stats_embed(interaction.client, interaction.guild, int(selected_value), time_text, interaction.user)
        
        # On renvoie la vue en précisant la nouvelle valeur sélectionnée
        await interaction.edit_original_response(content=None, embed=embed, view=StatsView(selected_value))

class StatsView(View):
    def __init__(self, current_value="24"):
        super().__init__(timeout=180)
        self.add_item(TimeSelect(current_value))

# ==============================================================================
# ------------------------------- COG ------------------------------------------
# ==============================================================================

class PingStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="everyone", description="Affiche les stats des pings everyone/here")
    async def everyone_command(self, ctx: commands.Context):
        await ctx.defer()
        
        # Valeur par défaut : 24 heures
        default_value = "24"
        
        embed = await create_stats_embed(
            bot=self.bot,
            guild=ctx.guild, 
            hours=int(default_value), 
            time_text="Dernières 24 heures", 
            requester=ctx.author
        )
        
        await ctx.send(embed=embed, view=StatsView(default_value))

async def setup(bot):
    await bot.add_cog(PingStats(bot))