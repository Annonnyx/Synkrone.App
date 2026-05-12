import discord
from discord.ext import commands
from discord import app_commands

# Modal pour la version Slash
class SayModal(discord.ui.Modal, title="Envoyer un message"):
    message_input = discord.ui.TextInput(
        label="Votre message",
        style=discord.TextStyle.paragraph,
        placeholder="Tapez le contenu ici...",
        required=True,
        max_length=2000
    )

    async def on_submit(self, it: discord.Interaction):
        # Envoi direct du texte sans mention de l'utilisateur pour l'anonymat du bot
        await it.response.send_message("Message envoyé !", ephemeral=True)
        await it.channel.send(self.message_input.value)

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="say",
        description="Fait parler le bot (Modal en slash, direct en préfixe)"
    )
    @app_commands.describe(message="Le message à envoyer (uniquement pour le préfixe)")
    async def say(self, ctx: commands.Context, *, message: str = None):
        # Détection du mode Slash
        if ctx.interaction:
            await ctx.interaction.response.send_modal(SayModal())
            return

        # Mode Préfixe (!say)
        if not message:
            return await ctx.send("❌ Utilisation : `!say <message>`", delete_after=5)

        # Suppression du message original
        try:
            await ctx.message.delete()
        except:
            pass

        await ctx.send(message)

async def setup(bot):
    await bot.add_cog(Say(bot))