import discord
from discord.ext import commands
from discord import app_commands
import traceback

# --- SYSTÈME D'IMPORT CONFIG_MANAGER ---
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None


from discord import ui
import re

def parse_time_arg(arg: str) -> int:
    """
    Parse une chaîne de temps (ex: 10s, 2m, 1h, 0, 0s, 0m, 0h) en secondes.
    Retourne -1 si invalide.
    """
    arg = str(arg).strip().lower()
    if arg in ("0", "0s", "0m", "0h"):
        return 0
    match = re.fullmatch(r"(\d+)([smh]?)", arg)
    if not match:
        return -1
    value, unit = match.groups()
    value = int(value)
    if unit == "" or unit == "s":
        return value
    elif unit == "m":
        return value * 60
    elif unit == "h":
        return value * 3600
    return -1

class SlowmodeModal(ui.Modal, title="Modifier le slowmode"):
    temps = ui.TextInput(label="Nouveau délai (ex: 10s, 2m, 1h, 0)", placeholder="0 pour désactiver", required=True)

    def __init__(self, cog, ctx):
        super().__init__()
        self.cog = cog
        self.ctx = ctx

    async def on_submit(self, interaction: discord.Interaction):
        seconds = parse_time_arg(self.temps.value)
        if seconds == -1 or seconds < 0 or seconds > 21600:
            await interaction.response.send_message("❌ Veuillez entrer un délai valide entre 0 et 6h (ex: 10s, 2m, 1h, 0)", ephemeral=True)
            return
        try:
            await interaction.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                title = "🔓 Slowmode Désactivé"
                description = f"Le mode lent a été retiré de {interaction.channel.mention}."
                color = 0x2ecc71
            else:
                title = "⏳ Slowmode Activé"
                description = f"Le délai entre les messages est maintenant de **{seconds} secondes** dans {interaction.channel.mention}."
                color = 0xe67e22
            embed = self.cog.create_custom_embed(interaction.guild, interaction.user, title, description, color)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Je n'ai pas les permissions nécessaires pour modifier ce salon.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("❌ Une erreur est survenue lors de la configuration du slowmode.", ephemeral=True)

class SlowmodeView(ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx

    @ui.button(label="Modifier le slowmode", style=discord.ButtonStyle.primary, custom_id="slowmode_modify")
    async def modify(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Vous n'avez pas la permission `Gérer les salons`.", ephemeral=True)
            return
        await interaction.response.send_modal(SlowmodeModal(self.cog, self.ctx))

class Slowmode(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def create_custom_embed(self, guild, user, title, description, color=0x3498db):
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=guild, user=user, bot=self.bot, title=title, description=description, target_id=guild.id if guild else None
            )
        return discord.Embed(title=title, description=description, color=color)

    @commands.hybrid_command(name="slowmode", description="Affiche ou modifie le délai de slowmode du salon.")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, temps: str = None):
        """
        Affiche ou modifie le slowmode du salon.
        - Sans argument : affiche l'état actuel + bouton de modification.
        - Avec argument : modifie directement (ex: !slowmode 10s, !slowmode 2m, !slowmode 1h, !slowmode 0)
        """
        if temps is None:
            delay = ctx.channel.slowmode_delay
            if delay == 0:
                desc = f"Aucun slowmode n'est actif dans {ctx.channel.mention}."
            else:
                desc = f"Le délai actuel entre chaque message est de **{delay} secondes** dans {ctx.channel.mention}."
            embed = self.create_custom_embed(ctx.guild, ctx.author, "⏳ Slowmode actuel", desc)
            view = SlowmodeView(self, ctx)
            await ctx.send(embed=embed, view=view)
            return

        seconds = parse_time_arg(temps)
        if seconds == -1 or seconds < 0 or seconds > 21600:
            await ctx.send("❌ Veuillez entrer un délai valide entre 0 et 6h (ex: 10s, 2m, 1h, 0)", ephemeral=True)
            return
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                title = "🔓 Slowmode Désactivé"
                description = f"Le mode lent a été retiré de {ctx.channel.mention}."
                color = 0x2ecc71
            else:
                title = "⏳ Slowmode Activé"
                description = f"Le délai entre les messages est maintenant de **{seconds} secondes** dans {ctx.channel.mention}."
                color = 0xe67e22
            embed = self.create_custom_embed(ctx.guild, ctx.author, title, description, color)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas les permissions nécessaires pour modifier ce salon.", ephemeral=True)
        except Exception as e:
            await ctx.send("❌ Une erreur est survenue lors de la configuration du slowmode.", ephemeral=True)

    @slowmode.error
    async def slowmode_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Vous n'avez pas la permission `Gérer les salons` pour utiliser cette commande.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Veuillez entrer un délai valide (ex: 10s, 2m, 1h, 0)", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Slowmode(bot))