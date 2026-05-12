########################################
# Imports et dépendances
########################################

import random
import discord
from discord.ext import commands
from discord import app_commands, ui
from typing import Optional

# Import du gestionnaire d'embed
try:
    from ..utils import config_manager
    HAS_CUSTOM_EMBED = True
except ImportError:
    try:
        from cogs.addons.embed_type.utils import config_manager
        HAS_CUSTOM_EMBED = True
    except ImportError:
        config_manager = None
        HAS_CUSTOM_EMBED = False

########################################
# Classes pour le modal et le bouton
########################################

class RateModal(ui.Modal, title="Noter quelque chose"):
    element = ui.TextInput(
        label="Quel élément veux-tu noter ?",
        placeholder="Écris ici...",
        min_length=1,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        # On diffère la réponse pour avoir plus de temps
        await interaction.response.defer()
        
        # Génération de la note
        score = round(random.uniform(0, 10), 1)
        bar = get_ascii_bar(score)
        emoji = get_rating_emoji(score)
        
        # Création de l'embed avec le gestionnaire
        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=interaction.guild,
                user=interaction.user,
                bot=interaction.client,
                title="📊 ÉVALUATION",
                description=f"```\n{self.element.value}\n```",  # Added comma here
                target_id=interaction.guild.id if interaction.guild else None
            )
        else:
            embed = discord.Embed(
                title="📊 ÉVALUATION",
                description=f"```\n{self.element.value}\n```",
                color=discord.Color.blue()
            )
        
        # Ajout de la note
        embed.add_field(
            name=f"Note: {score}/10 {emoji}",
            value=f"`{bar}`",
            inline=False
        )
        
        # Message personnalisé selon la note
        if score < 3:
            comment = "C'est pas ouf..."
        elif score < 6:
            comment = "Bof bof..."
        elif score < 8:
            comment = "Pas mal du tout !"
        elif score < 10:
            comment = "Excellent !"
        else:
            comment = "PARFAIT ! 10/10 !"
        
        # Ajout du commentaire
        embed.add_field(name="Commentaire", value=comment, inline=False)
        
        # Création du bouton pour noter à nouveau
        view = RateView()
        
        # Envoi du message avec l'embed et le bouton
        await interaction.followup.send(embed=embed, view=view, ephemeral=False)

class RateButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="Noter quelque chose",
            style=discord.ButtonStyle.primary,
            emoji="⭐"
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RateModal())

class RateView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # 3 minutes de timeout
        self.add_item(RateButton())

########################################
# Fonctions utilitaires
########################################

def get_rating_emoji(score: float) -> str:
    """Retourne un emoji selon la note donnée."""
    if score < 2:
        return "🤮"
    elif score < 4:
        return "💩"
    elif score < 6:
        return "😐"
    elif score < 8:
        return "🙂"
    elif score < 9.5:
        return "😎"
    else:
        return "💯"

def get_ascii_bar(score: float) -> str:
    """Crée une barre ASCII représentant la note (sur 10)."""
    filled = int(round(score))
    empty = 10 - filled
    return "▰" * filled + "▱" * empty

########################################
# Cog Rate
# Commande hybride rate (texte + slash) pour noter quelque chose aléatoirement
########################################

class Rate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="rate",
        description="Ouvre un menu pour noter quelque chose."
    )
    async def rate_command(self, ctx: commands.Context):
        """Ouvre un menu pour noter quelque chose"""
        # Création de l'embed d'accueil avec le gestionnaire
        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=ctx.guild,
                user=ctx.author,
                bot=ctx.bot,
                title="⭐ Système de notation",
                description="Clique sur le bouton ci-dessous pour noter quelque chose !",
                target_id=ctx.guild.id if ctx.guild else None
            )
        else:
            embed = discord.Embed(
                title="⭐ Système de notation",
                description="Clique sur le bouton ci-dessous pour noter quelque chose !",
                color=discord.Color.blue()
            )
        
        # Création de la vue avec le bouton
        view = RateView()
        
        # Envoi du message avec l'embed et le bouton
        if ctx.interaction:
            await ctx.send(embed=embed, view=view, ephemeral=False)
        else:
            await ctx.reply(embed=embed, view=view, mention_author=False)

########################################
# Setup du Cog
########################################

async def setup(bot: commands.Bot):
    await bot.add_cog(Rate(bot))
