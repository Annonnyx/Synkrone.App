########################################
# Imports et dépendances
########################################

import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path
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
# View & Select pour les dés
########################################

class DiceSelect(discord.ui.Select):
    def __init__(self, parent_cog, ctx):
        self.parent_cog = parent_cog
        self.ctx = ctx
        options = [
            discord.SelectOption(label="1 Dé", value="1", emoji="🎲"),
            discord.SelectOption(label="2 Dés", value="2", emoji="🎲"),
            discord.SelectOption(label="3 Dés", value="3", emoji="🎲"),
            discord.SelectOption(label="4 Dés", value="4", emoji="🎲"),
            discord.SelectOption(label="5 Dés", value="5", emoji="🎲"),
        ]
        super().__init__(placeholder="Modifier le nombre de dés...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Ce menu ne vous appartient pas.", ephemeral=True)
        
        count = int(self.values[0])
        rolls = [random.randint(1, 6) for _ in range(count)]
        total = sum(rolls)
        
        # Récupération du GIF pour le premier dé du nouveau lancer
        gif_path = self.parent_cog.data_dir / f"dice_{rolls[0]}.gif"
        if not gif_path.exists():
            gif_path = self.parent_cog.data_dir / "dice.gif"

        title = "🎲 Lancer de dés"
        results_formatted = " | ".join([f"**{r}**" for r in rolls])
        description = f"Résultat(s) : {results_formatted}\n\n> **Total : `{total}`**"

        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=interaction.guild, user=interaction.user, bot=self.parent_cog.bot,
                title=title, description=description,
                target_id=interaction.guild.id if interaction.guild else None
            )
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)

        if gif_path.exists():
            file = discord.File(str(gif_path), filename="dice.gif")
            embed.set_image(url="attachment://dice.gif")
            # On conserve la vue pour permettre de re-changer le nombre de dés
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)

class DiceView(discord.ui.View):
    def __init__(self, parent_cog, ctx):
        super().__init__(timeout=600)  # 10 minutes de timeout
        self.add_item(DiceSelect(parent_cog, ctx))

########################################
# Cog Dice
########################################

class Dice(commands.Cog):
    """🎲 Module Dice — Lancer instantané avec sélecteur de quantité."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_dir = Path(__file__).parent / "data"

    @commands.hybrid_command(
        name="dice",
        description="Lance un dé instantanément et permet d'en ajouter."
    )
    async def dice(self, ctx: commands.Context):
        """Affiche un premier résultat et le sélecteur."""
        try:
            # 1. LANCER INITIAL (1 DÉ)
            roll = random.randint(1, 6)
            gif_path = self.data_dir / f"dice_{roll}.gif"
            if not gif_path.exists():
                gif_path = self.data_dir / "dice.gif"

            title = "🎲 Premier jet !"
            description = f"Le dé s'est arrêté sur **{roll}**.\n\n*Utilise le menu ci-dessous pour lancer plus de dés.*"

            # 2. CONSTRUCTION DE L'EMBED
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=ctx.guild, user=ctx.author, bot=self.bot,
                    title=title, description=description,
                    target_id=ctx.guild.id if ctx.guild else None
                )
            else:
                embed = discord.Embed(title=title, description=description, color=0x2b2d31)

            # 3. GESTION DU FICHIER ET DE LA VUE
            view = DiceView(self, ctx)
            file = None
            if gif_path.exists():
                file = discord.File(str(gif_path), filename="dice.gif")
                embed.set_image(url="attachment://dice.gif")

            # 4. ENVOI
            if ctx.interaction:
                await ctx.send(embed=embed, file=file, view=view)
            else:
                await ctx.send(embed=embed, file=file, view=view, reference=ctx.message)

        except Exception:
            print(f"[ERROR - Dice] :")
            traceback.print_exc()

async def setup(bot: commands.Bot):
    if bot.get_command("dice"):
        bot.remove_command("dice")
    await bot.add_cog(Dice(bot))