import discord
from discord.ext import commands
from discord import app_commands, ui
import random
import traceback

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# ----------------------------- INTERFACES UI ----------------------------------
# ==============================================================================

class ChooseModal(ui.Modal, title="Saisir vos options"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    opt1 = ui.TextInput(label="Option 1", placeholder="Ex: Jouer", required=True, max_length=80)
    opt2 = ui.TextInput(label="Option 2", placeholder="Ex: Travailler", required=True, max_length=80)
    opt3 = ui.TextInput(label="Option 3", placeholder="Optionnel", required=False, max_length=80)
    opt4 = ui.TextInput(label="Option 4", placeholder="Optionnel", required=False, max_length=80)
    opt5 = ui.TextInput(label="Option 5", placeholder="Optionnel", required=False, max_length=80)

    async def on_submit(self, interaction: discord.Interaction):
        # Récupération et filtrage des options
        options = [opt.value.strip() for opt in [self.opt1, self.opt2, self.opt3, self.opt4, self.opt5] if opt.value and opt.value.strip()]
        
        choice = random.choice(options)
        
        # Construction de la description
        desc = (
            f"🎯 **Options configurées :**\n" + 
            "\n".join(f"• {opt}" for opt in options) +
            f"\n\n🏆 **Résultat du tirage :** `{choice}`"
        )

        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=interaction.guild,
                user=interaction.user,
                bot=self.cog.bot,
                title="🎲 Tirage au sort terminé",
                description=desc,
                target_id=interaction.guild.id if interaction.guild else None
            )
        else:
            embed = discord.Embed(title="🎲 Tirage au sort terminé", description=desc, color=0x2b2d31)

        # On envoie un NOUVEAU message avec le résultat et le bouton reste disponible
        # On utilise interaction.response.send_message pour créer un nouveau bloc d'embed
        await interaction.response.send_message(embed=embed, view=ChooseView(self.cog))

class ChooseView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @ui.button(label="Lancer un tirage", style=discord.ButtonStyle.primary, emoji="🎲")
    async def open_modal(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ChooseModal(self.cog))

# ==============================================================================
# ----------------------------- COG CHOOSE -------------------------------------
# ==============================================================================

class Choose(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_help_embed(self, guild, user):
        """Génère l'embed d'aide à la décision"""
        title = "🎲 Aide à la décision"
        description = (
            "Cet outil vous permet de laisser le hasard trancher entre plusieurs propositions.\n\n"
            "**Comment ça marche ?**\n"
            "1. Cliquez sur le bouton **Lancer un tirage** ci-dessous.\n"
            "2. Saisissez entre **2 et 5 choix** possibles.\n"
            "3. Validez pour obtenir instantanément le résultat.\n\n"
        )
        
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=self.bot,
                title=title,
                description=description,
                target_id=guild.id if guild else None
            )
        else:
            return discord.Embed(title=title, description=description, color=0x2b2d31)

    @commands.hybrid_command(
        name="choose", 
        description="Lancer un tirage au sort entre plusieurs propositions."
    )
    async def choose(self, ctx: commands.Context):
        try:
            # Accusé de réception
            await ctx.defer(ephemeral=False)

            embed = await self.get_help_embed(ctx.guild, ctx.author)

            # Envoi initial
            if ctx.interaction:
                await ctx.send(embed=embed, view=ChooseView(self))
            else:
                await ctx.send(embed=embed, view=ChooseView(self), reference=ctx.message, mention_author=True)

        except Exception:
            traceback.print_exc()

async def setup(bot: commands.Bot):
    if bot.get_command("choose"):
        bot.remove_command("choose")
    await bot.add_cog(Choose(bot))