import os
import json
import discord
import asyncio
import datetime
import traceback
from discord.ext import commands
from discord import app_commands, ui
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    # Utilisation du chemin spécifique fourni
    from cogs.addons.embed_type.utils import config_manager
    HAS_CUSTOM_EMBED = True
except ImportError:
    config_manager = None
    HAS_CUSTOM_EMBED = False

# --- CONFIGURATION DES CHEMINS ---
CURRENT_DIR = Path(__file__).parent
DATA_PATH = CURRENT_DIR / "data"

# ==============================================================================
# ----------------------------- MODAL DE WARN ----------------------------------
# ==============================================================================

class WarnModal(ui.Modal, title="Sanctionner un utilisateur"):
    # Champ de texte en français
    raison = ui.TextInput(
        label="Raison de l'avertissement", 
        style=discord.TextStyle.paragraph, 
        placeholder="Indiquez la raison précise de la sanction...", 
        required=True, 
        min_length=4
    )

    def __init__(self, bot, cible_user, cog_instance):
        super().__init__()
        self.bot = bot
        self.cible_user = cible_user
        self.cog = cog_instance

    async def on_submit(self, interaction: discord.Interaction):
        # Transmission à la logique de sauvegarde avec la valeur du modal
        await self.cog.save_and_send_warn(interaction, self.cible_user, self.raison.value)

# ==============================================================================
# ------------------------------- COG WARN -------------------------------------
# ==============================================================================

class ModerationWarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        DATA_PATH.mkdir(parents=True, exist_ok=True)

    def get_styled_embed(self, guild, user, title, description):
        """Génère l'embed avec le config_manager (Auteur, Footer, Couleur)"""
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=self.bot,
                title=title,
                description=description,
                target_id=guild.id if guild else None
            )
        return discord.Embed(title=title, description=description, color=0x2b2d31)

    def get_staff_rank(self, member: discord.Member):
        """Détermine le rang du staff"""
        if member.guild.owner_id == member.id:
            return "Propriétaire"
        elif member.guild_permissions.administrator:
            return "Administrateur"
        else:
            return "Modérateur"

    async def save_and_send_warn(self, interaction_or_ctx, cible_user, raison):
        """Logique centrale : Sauvegarde, Affichage Salon et DM"""
        guild = interaction_or_ctx.guild
        author = interaction_or_ctx.user if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx.author
        
        # 1. SAUVEGARDE
        guild_id = str(guild.id)
        user_id = str(cible_user.id)
        folder_path = DATA_PATH / guild_id
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / f"{user_id}.json"

        staff_rank = self.get_staff_rank(author)
        warn_id = os.urandom(4).hex()

        warn_data = {
            "id": warn_id,
            "staff_id": author.id,
            "staff_name": author.display_name,
            "staff_rank": staff_rank,
            "raison": raison,
            "timestamp": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
        }

        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f: data = json.load(f)
        else:
            data = {"user_name": cible_user.display_name, "warns": []}

        data["warns"].append(warn_data)
        with open(file_path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

        # 2. CONSTRUCTION DE L'EMBED
        desc = (
            f"👤 **Cible :** {cible_user.mention} (`{cible_user.id}`)\n"
            f"🛡️ **Staff :** {author.mention} ({staff_rank})\n\n"
            f"📝 **Raison :**\n```\n{raison}\n```"
        )
        embed = self.get_styled_embed(guild, author, "⚠️ Avertissement Appliqué", desc)

        # 3. ENVOI DM
        try: await cible_user.send(embed=embed)
        except: pass

        # 4. RÉPONSE
        if isinstance(interaction_or_ctx, discord.Interaction):
            if interaction_or_ctx.response.is_done():
                await interaction_or_ctx.followup.send(embed=embed)
            else:
                await interaction_or_ctx.response.send_message(embed=embed)
        else:
            await interaction_or_ctx.send(embed=embed, reference=interaction_or_ctx.message)

    @commands.hybrid_command(name="warn", description="Avertir un membre")
    @app_commands.describe(
        utilisateur="Le membre à avertir", 
        raison="La raison (Optionnel en slash pour ouvrir le modal)"
    )
    # Permissions : Admin ou permission de mute (moderate_members)
    @commands.check_any(commands.has_permissions(administrator=True), commands.has_permissions(moderate_members=True))
    async def warn(self, ctx: commands.Context, utilisateur: discord.Member, *, raison: str = None):
        
        # Sécurités
        if utilisateur.id == ctx.author.id:
            return await ctx.send("❌ Vous ne pouvez pas vous avertir vous-même.", ephemeral=True)
        if utilisateur.bot:
            return await ctx.send("❌ Vous ne pouvez pas avertir un bot.", ephemeral=True)
        
        # LOGIQUE SLASH : Si aucune raison n'est donnée, on ouvre le Modal
        if ctx.interaction and raison is None:
            await ctx.interaction.response.send_modal(WarnModal(self.bot, utilisateur, self))
            return

        # LOGIQUE TEXTE : La raison est obligatoire
        if not raison:
            return await ctx.send(f"❌ Vous ne pouvez pas warn sans justifier une raison.\nUsage : `!warn {utilisateur.mention} <raison>`", ephemeral=True)

        await self.save_and_send_warn(ctx, utilisateur, raison)

    # --------------------------- GESTION ERREURS ----------------------------------
    # ==============================================================================

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, (commands.MissingPermissions, commands.CheckAnyFailure)):
            embed = self.get_styled_embed(ctx.guild, ctx.author, "🚫 Accès restreint", "Vous n'avez pas les permissions requises (Administrateur ou Mute) pour utiliser cette commande.")
            return await ctx.send(embed=embed, ephemeral=True)
        
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"❌ Usage incorrect.\n`!warn <@utilisateur> <raison>`", ephemeral=True)

        traceback.print_exc()

async def setup(bot):
    await bot.add_cog(ModerationWarn(bot))