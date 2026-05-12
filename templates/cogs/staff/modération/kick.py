import discord
from discord.ext import commands
from discord import app_commands
import traceback
import datetime

# Tentative d'importation du gestionnaire de configuration d'embeds
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def create_embed(self, guild, user, title, description, color=0xff0000):
        """Génère l'embed en utilisant le config_manager ou un fallback standard."""
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=self.bot,
                title=title,
                description=description,
                target_id=guild.id if guild else None
            )
        return discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))


    @commands.hybrid_command(
        name="kick",
        description="Expulse un membre du serveur (mention, ID ou pseudo)."
    )
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(membre="Le membre à expulser (mention, ID ou pseudo)", reason="Raison de l'expulsion")
    async def kick(self, ctx: commands.Context, membre: str, *, reason: str = "Aucune raison fournie"):
        """
        Expulse un membre via mention, ID ou pseudo.
        """
        await ctx.defer(ephemeral=True)

        member = None
        # 1. Recherche par mention
        if membre.startswith("<@") and membre.endswith(">"):
            membre_id = membre.replace("<@!","").replace("<@","").replace(">","")
            if membre_id.isdigit():
                member = ctx.guild.get_member(int(membre_id))
        # 2. Recherche par ID
        elif membre.isdigit():
            member = ctx.guild.get_member(int(membre))
        # 3. Recherche par nom
        if member is None:
            member = discord.utils.find(lambda m: m.name == membre or m.display_name == membre, ctx.guild.members)

        if member is None:
            return await ctx.send("❌ Utilisateur introuvable sur ce serveur.", ephemeral=True)

        # Empêcher de s'expulser soi-même
        if member.id == ctx.author.id:
            return await ctx.send("❌ Tu ne peux pas t'expulser toi-même.", ephemeral=True)

        # Empêcher d'expulser le bot
        if member.id == self.bot.user.id:
            return await ctx.send("❌ Je ne peux pas m'auto-expulser. Sympa l'ambiance !", ephemeral=True)

        # Vérification de la hiérarchie des rôles
        if member.top_role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            return await ctx.send("❌ Tu ne peux pas expulser ce membre car il a un rôle supérieur ou égal au tien.", ephemeral=True)

        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("❌ Je ne peux pas expulser ce membre : mon rôle est trop bas dans la hiérarchie.", ephemeral=True)

        try:
            # 2. NOTIFICATION MP
            try:
                dm_title = f"👞 Expulsion de {ctx.guild.name}"
                dm_desc = f"Tu as été expulsé du serveur **{ctx.guild.name}**.\n**Raison :** {reason}"
                dm_embed = self.create_embed(ctx.guild, member, dm_title, dm_desc)
                await member.send(embed=dm_embed)
            except (discord.Forbidden, discord.HTTPException):
                pass

            # 3. ACTION D'EXPULSION
            await member.kick(reason=f"Par: {ctx.author} | Raison: {reason}")

            # 4. RÉPONSE DE CONFIRMATION
            success_title = "✅ Expulsion réussie"
            success_desc = f"**Membre :** {member.mention} (`{member.id}`)\n**Modérateur :** {ctx.author.mention}\n**Raison :** {reason}"
            embed = self.create_embed(ctx.guild, ctx.author, success_title, success_desc, color=0x2ecc71)
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)

        except Exception as e:
            print(f"[ERROR - Kick] : {e}")
            traceback.print_exc()
            error_msg = "❌ Une erreur critique est survenue lors de l'expulsion."
            if ctx.interaction:
                await ctx.interaction.followup.send(error_msg, ephemeral=True)
            else:
                await ctx.send(error_msg)

    @kick.error
    async def kick_error(self, ctx, error):
        """Gestionnaire d'erreurs spécifique pour la commande kick."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tu n'as pas la permission `Expulser des membres`.", ephemeral=True)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Utilisateur introuvable sur ce serveur.", ephemeral=True)
        else:
            await ctx.send(f"⚠️ Une erreur est survenue : {str(error)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Kick(bot))