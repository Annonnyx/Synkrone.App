########################################
# Imports et dépendances
########################################

import discord
from discord.ext import commands
from discord import app_commands, ui
from pathlib import Path
import random

# Import du gestionnaire d'embed
try:
    from cogs.addons.embed_type.utils import config_manager
    HAS_CUSTOM_EMBED = True
except ImportError:
    config_manager = None
    HAS_CUSTOM_EMBED = False

########################################
# Classes pour le bouton et la vue
########################################

class CoinFlipButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="Lancer la pièce",
            style=discord.ButtonStyle.primary,
            emoji="🪙"
        )
    
    async def callback(self, interaction: discord.Interaction):
        try:
            gif_path = Path(__file__).parent / "data" / "pileface.gif"
            if not gif_path.exists():
                return await interaction.response.send_message(
                    "❌ Le fichier GIF est introuvable.", ephemeral=True
                )
            
            result = random.choice(["Pile", "Face"])
            file = discord.File(str(gif_path), filename="pileface.gif")
            
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=interaction.guild,
                    user=interaction.user,
                    bot=interaction.client,
                    title="🪙 Pile ou face",
                    description=f"```\n{result} !\n```",
                    target_id=interaction.guild.id if interaction.guild else None
                )
            else:
                embed = discord.Embed(
                    title="🪙 Pile ou face",
                    description=f"```\n{result} !\n```",
                    color=discord.Color.blue()
                )
            
            embed.set_image(url="attachment://pileface.gif")
            
            # On recrée la vue pour garder le bouton actif
            view = CoinFlipView()
            
            # edit_message remplace le contenu actuel par le nouveau (embed + fichier)
            await interaction.response.edit_message(embed=embed, attachments=[file], view=view)
            
        except Exception as e:
            # Gestion d'erreur propre selon si l'interaction a déjà été répondue ou non
            error_msg = f"❌ Une erreur est survenue : {str(e)}"
            if not interaction.response.is_done():
                await interaction.response.send_message(error_msg, ephemeral=True)
            else:
                await interaction.followup.send(error_msg, ephemeral=True)

class CoinFlipView(ui.View):
    """Vue pour le bouton de coinflip"""
    def __init__(self):
        super().__init__(timeout=None)  # timeout=None pour que le bouton ne se désactive jamais
        self.add_item(CoinFlipButton())

########################################
# Cog CoinFlip
########################################

class CoinFlip(commands.Cog):
    """Commande /coinflip — Pile ou face avec bouton interactif."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="coinflip",
        description="Lance une pièce : pile ou face."
    )
    async def coinflip(self, ctx: commands.Context):
        """Lance une pièce et affiche le résultat avec un GIF animé."""
        try:
            # Chemin vers le fichier GIF
            gif_path = Path(__file__).parent / "data" / "pileface.gif"
            
            if not gif_path.exists():
                return await ctx.send(
                    "❌ Le fichier GIF est introuvable.",
                    ephemeral=True
                )
            
            # Génération du résultat
            result = random.choice(["Pile", "Face"])
            
            # Lecture du fichier GIF
            file = discord.File(str(gif_path), filename="pileface.gif")
            
            # Création de l'embed avec le gestionnaire
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=ctx.guild,
                    user=ctx.author,
                    bot=ctx.bot,
                    title="🪙 Pile ou face",
                    description=f"```\n{result} !\n```",
                    target_id=ctx.guild.id if ctx.guild else None
                )
            else:
                embed = discord.Embed(
                    title="🪙 Pile ou face",
                    description=f"```\n{result} !\n```",
                    color=discord.Color.blue()
                )
            
            # Configuration de l'image de l'embed
            embed.set_image(url="attachment://pileface.gif")
            
            # Création de la vue avec le bouton
            view = CoinFlipView()
            
            # Envoi du message avec l'embed, le fichier et le bouton
            await ctx.send(embed=embed, file=file, view=view)
            
        except Exception as e:
            await ctx.send(
                f"❌ Une erreur est survenue : {str(e)}",
                ephemeral=True
            )

########################################
# Setup du Cog
########################################

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))