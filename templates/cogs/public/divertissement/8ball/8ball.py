########################################
# Imports et dépendances
########################################

import discord
from discord.ext import commands
from discord import app_commands
import random
import traceback

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

########################################
# Modal 8Ball
########################################

class EightBallModal(discord.ui.Modal, title="🎱 Pose ta question"):
    question_input = discord.ui.TextInput(
        label="Quelle est ta question ?",
        placeholder="Le destin est-il écrit ?",
        style=discord.TextStyle.short,
        required=True,
        max_length=256
    )

    def __init__(self, parent_cog):
        super().__init__()
        self.parent_cog = parent_cog

    async def on_submit(self, interaction: discord.Interaction):
        response = random.choice(self.parent_cog.responses)
        question = self.question_input.value

        # Mise en forme demandée avec des blocs de code
        title = "🎱 La Boule Magique a parlé"
        description = (
            f"**Question :**\n```\n{question}\n```\n"
            f"**Réponse :**\n```\n{response}\n```"
        )

        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=interaction.guild, user=interaction.user, bot=self.parent_cog.bot,
                title=title, description=description,
                target_id=interaction.guild.id if interaction.guild else None
            )
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)

        # On ajoute à nouveau la vue pour que n'importe qui puisse relancer
        view = EightBallView(self.parent_cog)
        await interaction.response.send_message(embed=embed, view=view)

########################################
# View avec Bouton (Ouverte à tous)
########################################

class EightBallView(discord.ui.View):
    def __init__(self, parent_cog):
        super().__init__(timeout=None) # Persistant pour que le bouton reste actif
        self.parent_cog = parent_cog

    @discord.ui.button(label="Poser ma question", style=discord.ButtonStyle.secondary, emoji="🔮")
    async def ask_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # N'importe qui peut cliquer ici
        await interaction.response.send_modal(EightBallModal(self.parent_cog))

########################################
# Cog EightBall
########################################

class EightBall(commands.Cog):
    """🎱 Module de voyance — Système interactif et communautaire."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.responses = [
            "Oui, absolument.", "C'est certain.", "Sans aucun doute.", 
            "Très probablement.", "Peut-être bien.", "Demande plus tard.", 
            "Mieux vaut ne pas te le dire maintenant.", "Je ne peux pas prédire.", 
            "Ne compte pas là-dessus.", "Ma réponse est non.", "Mes sources disent non."
        ]

    @commands.hybrid_command(
        name="8ball",
        description="Ouvre la fenêtre pour poser une question à la boule magique."
    )
    async def eight_ball(self, ctx: commands.Context):
        """Déclenche le modal (Slash) ou l'embed avec bouton (Prefix)."""
        
        try:
            # SI SLASH COMMAND : Ouverture directe du Modal
            if ctx.interaction:
                await ctx.interaction.response.send_modal(EightBallModal(self))
                return

            # SI PREFIXE : On affiche l'embed d'accueil avec le bouton
            title = "🎱 8-Ball Magique"
            desc = "Clique sur le bouton ci-dessous pour interroger la boule magique."

            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=ctx.guild, user=ctx.author, bot=self.bot,
                    title=title, description=desc,
                    target_id=ctx.guild.id if ctx.guild else None
                )
            else:
                embed = discord.Embed(title=title, description=desc, color=0x2b2d31)

            view = EightBallView(self)
            await ctx.send(embed=embed, view=view, reference=ctx.message)

        except Exception:
            print(f"[ERROR - 8Ball] :")
            traceback.print_exc()

async def setup(bot: commands.Bot):
    if bot.get_command("8ball"):
        bot.remove_command("8ball")
    await bot.add_cog(EightBall(bot))