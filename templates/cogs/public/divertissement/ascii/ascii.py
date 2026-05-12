import discord
from discord.ext import commands
from discord import ui
import re
import pyfiglet
import traceback

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# ----------------------------- MODAL ASCII ------------------------------------
# ==============================================================================

class AsciiModal(ui.Modal, title="🎨 Générateur d'ASCII Art"):
    def __init__(self, bot: commands.Bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.allowed_chars = re.compile(r'^[a-zA-Z0-9\s]*$')
        self.max_length = 10 
        
        self.texte = ui.TextInput(
            label=f'Texte (max {self.max_length} caractères)',
            placeholder='Exemple: Brutal...',
            max_length=self.max_length,
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.texte)
    
    async def on_submit(self, interaction: discord.Interaction):
        text = self.texte.value.strip()
        
        if not self.allowed_chars.fullmatch(text):
            return await interaction.response.send_message(
                "❌ Seules les lettres (a-z, A-Z) et les chiffres (0-9) sont autorisés.",
                ephemeral=True
            )
            
        try:
            # Génération de l'ASCII
            ascii_art = pyfiglet.figlet_format(text, font="small", width=100)
            ascii_art = '\n'.join(line.rstrip() for line in ascii_art.split('\n') if line.strip())
             
            title = f"ASCII : `{text}`"
            description = f"```\n{ascii_art}\n```"

            # On réutilise la vue pour que le bouton reste présent sous l'embed modifié
            view = AsciiView(self.bot)

            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=interaction.guild,
                    user=interaction.user,
                    bot=self.bot,
                    title=title,
                    description=description,
                    target_id=interaction.guild_id if interaction.guild else None
                )
            else:
                embed = discord.Embed(title=title, description=description, color=0x2b2d31)
            
            # CRUCIAL : On utilise edit_message pour modifier l'existant au lieu d'en créer un nouveau
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception:
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Erreur de génération.", ephemeral=True)

# ==============================================================================
# ----------------------------- VIEW ASCII -------------------------------------
# ==============================================================================

class AsciiView(ui.View):
    """Vue persistante pour gérer le bouton de modification"""
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(label="Modifier le texte ASCII", style=discord.ButtonStyle.primary, emoji="🎨")
    async def create_ascii(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(AsciiModal(self.bot))

# ==============================================================================
# ------------------------------ COG ASCII -------------------------------------
# ==============================================================================

class Ascii(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ascii", 
        description="Transforme un texte en art ASCII."
    )
    async def ascii(self, ctx: commands.Context):
        invit_title = "🎨 Générateur ASCII"
        invit_desc = "Cliquez sur le bouton pour générer ou modifier l'ASCII Art dans ce message."
        
        # On définit la vue
        view = AsciiView(self.bot)

        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=ctx.guild,
                user=ctx.author,
                bot=self.bot,
                title=invit_title,
                description=invit_desc,
                target_id=ctx.guild.id if ctx.guild else None
            )
        else:
            embed = discord.Embed(title=invit_title, description=invit_desc, color=0x2b2d31)

        if ctx.interaction:
            # En Slash command
            await ctx.interaction.response.send_message(embed=embed, view=view)
        else:
            # En commande classique
            await ctx.send(embed=embed, view=view, reference=ctx.message)

async def setup(bot: commands.Bot) -> None:
    if bot.get_command("ascii"):
        bot.remove_command("ascii")
    await bot.add_cog(Ascii(bot))