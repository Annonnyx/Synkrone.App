import discord
from discord.ext import commands
from discord import ui
import asyncio
import traceback
from typing import Optional, Union

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
    HAS_CUSTOM_EMBED = True
except ImportError:
        config_manager = None
        HAS_CUSTOM_EMBED = False

# ==============================================================================
# ----------------------------- COG REVERSE -----------------------------------
# ==============================================================================

class Reverse(commands.Cog):
    """Commande pour renverser et manipuler du texte de manière créative."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reverse_gif_url = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjAxcHZ3N3VkN2JwZ2VjZ2Z1eTZ4Z2FkZ3V2c3A0cHZ1dGJ1d2N1NGVzZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7btNPefGpfIdLQKk/giphy.gif"

    def reverse_text(self, text: str) -> str:
        """Renverse le texte et applique des effets spéciaux."""
        # Effet miroir avec des caractères spéciaux
        mirrored = ""
        special_chars = {
            '(': ')', ')': '(',
            '[': ']', ']': '[',
            '{': '}', '}': '{',
            '<': '>', '>': '<',
            '/': '\\', '\\': '/',
            '❨': '❩', '❩': '❨',
            '❪': '❫', '❫': '❪',
            '❬': '❭', '❭': '❬',
            '❮': '❯', '❯': '❮',
            '❰': '❱', '❱': '❰',
            '❲': '❳', '❳': '❲',
            '❴': '❵', '❵': '❴'
        }
        
        for char in text[::-1]:
            mirrored += special_chars.get(char, char)
            
        return mirrored

    class ReverseModal(ui.Modal, title="🔁 Renverser du texte"):
        def __init__(self, cog):
            super().__init__()
            self.cog = cog
            # Création du champ de texte
            self.text_input = ui.TextInput(
                label="Texte à renverser",
                placeholder="Écris ton texte ici...",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=1000
            )
            self.add_item(self.text_input)

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer()
            await self.cog.process_reverse_all_modes(interaction, self.text_input.value)
    
    class ReverseView(ui.View):
        def __init__(self, cog):
            super().__init__(timeout=180)
            self.cog = cog
            
        @ui.button(label="Ouvrir l'éditeur", style=discord.ButtonStyle.primary, emoji="🔁")
        async def open_modal(self, interaction: discord.Interaction, button: ui.Button):
            try:
                await interaction.response.send_modal(self.cog.ReverseModal(self.cog))
            except Exception as e:
                print(f"[ERROR - Reverse] Erreur lors de l'ouverture du modal: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Une erreur est survenue lors de l'ouverture de l'éditeur.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Une erreur est survenue lors de l'ouverture de l'éditeur.", ephemeral=True)
    
    @commands.hybrid_command(
        name="reverse",
        description="🔁 Renverse un texte avec style !"
    )
    @discord.app_commands.describe(
        mode="Choisis un mode spécial (optionnel)"
    )
    async def reverse(
        self, 
        ctx: Union[commands.Context, discord.Interaction],
        mode: Optional[str] = None
    ):
        """
        Renvoie ton texte à l'envers avec des effets spéciaux !
        
        Paramètres
        ----------
        mode: Optional[str]
            Choisis un mode spécial :
            - standard : Renverse simplement le texte
            - miroir : Inverse le texte et les caractères spéciaux
            - upside : Transforme le texte en caractères à l'envers
            - binary : Convertit en binaire avant de renverser
        """
        # Si c'est une interaction (slash command)
        if isinstance(ctx, discord.Interaction):
            return await ctx.response.send_modal(self.ReverseModal(self, mode))
            
        # Si c'est une commande de préfixe, on affiche un embed avec un bouton
        if hasattr(ctx, 'author'):
            user = ctx.author
            guild = ctx.guild
        else:
            user = ctx.user
            guild = ctx.guild if hasattr(ctx, 'guild') else None
        
        # Utilisation du gestionnaire d'embed si disponible
        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=self.bot,
                title="🔁 Renverser du texte",
                description="Clique sur le bouton ci-dessous pour ouvrir l'éditeur de texte.",
                target_id=guild.id if guild else None
            )
        else:
            embed = discord.Embed(
                title="🔁 Renverser du texte",
                description="Clique sur le bouton ci-dessous pour ouvrir l'éditeur de texte.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Demandé par {user.display_name}", icon_url=user.display_avatar.url)
        
        # Création et envoi de la vue
        view = self.ReverseView(self)
        try:
            if hasattr(ctx, 'send'):
                await ctx.send(embed=embed, view=view)
            else:
                if ctx.response.is_done():
                    await ctx.followup.send(embed=embed, view=view, ephemeral=False)
                else:
                    await ctx.response.send_message(embed=embed, view=view, ephemeral=False)
        except Exception as e:
            print(f"[ERROR - Reverse] Erreur lors de l'envoi du message: {e}")
            traceback.print_exc()

    @reverse.autocomplete("mode")
    async def reverse_mode_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[discord.app_commands.Choice[str]]:
        modes = [
            ("standard", "Mode Standard (renverse le texte et les caractères spéciaux)"),
            ("upside", "Mode Upside-Down (retourne les caractères)"),
            ("binary", "Mode Binaire (convertit en binaire avant)")
        ]
        return [
            discord.app_commands.Choice(name=name, value=value)
            for value, name in modes if current.lower() in name.lower()
        ][:5]

    async def process_reverse_all_modes(self, interaction: discord.Interaction, text: str):
        """Affiche les modes miroir, upside-down et binaire dans un embed, et édite le message d'origine avec le bouton sous l'embed."""
        try:
            # Miroir (texte inversé avec caractères spéciaux)
            miroir = self.reverse_text(text)
            # Upside-down
            normal = r'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!?.,;:()[]{}\\'
            flipped = r'ɐqɔpǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎzⱯꓭƆᗡƎᖵ⅁HIꞰꓶWNⱢ0ƆꓤX⅄Z⇂zƐᔭ⅃Ɫ9Ɫ86ㄥ0¿¡\'˙\'؛:)(][}{/\\'
            flip_table = str.maketrans(normal, flipped)
            upside = text.translate(flip_table)[::-1]
            # Binaire
            binary = ' '.join(format(ord(char), '08b') for char in text)[::-1]

            description = (
                f"**Miroir :**\n```\n{miroir}\n```\n"
                f"**Upside-Down :**\n```\n{upside}\n```\n"
                f"**Binaire :**\n```\n{binary}\n```"
            )

            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=interaction.guild,
                    user=interaction.user,
                    bot=self.bot,
                    title="🔁 Résultats du reverse",
                    description=description,
                    target_id=interaction.guild.id if interaction.guild else None
                )
            else:
                embed = discord.Embed(
                    title="🔁 Résultats du reverse",
                    description=description,
                    color=discord.Color.blue()
                )
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

            embed.add_field(
                name="Original",
                value=f"```\n{text}\n```",
                inline=False
            )

            # Récupérer le message d'origine pour l'éditer (si possible)
            try:
                # Si le message d'origine est accessible (modal lancé via bouton)
                if interaction.message:
                    view = self.ReverseView(self)
                    await interaction.message.edit(embed=embed, view=view)
                    await interaction.followup.send("✅ Résultat mis à jour !", ephemeral=True)
                    return
            except Exception:
                pass

            # Sinon, fallback : envoyer le résultat normalement avec le bouton
            view = self.ReverseView(self)
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, view=view, ephemeral=False)
            else:
                await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
        except Exception as e:
            error_msg = "❌ Une erreur est survenue lors du traitement de votre texte."
            if interaction.response.is_done():
                await interaction.followup.send(error_msg, ephemeral=True)
            else:
                await interaction.response.send_message(error_msg, ephemeral=True)
            print(f"[ERROR - Reverse] {e}")
            traceback.print_exc()

# ==============================================================================
# ------------------------------- SETUP ---------------------------------------
# ==============================================================================

async def setup(bot: commands.Bot):
    if bot.get_command("reverse"):
        bot.remove_command("reverse")
    await bot.add_cog(Reverse(bot))
