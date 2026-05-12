import discord
from discord.ext import commands
import traceback
import sys
import os

try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# Import pour les permissions
try:
    from .perm.perm import Perm
    HAS_PERMISSION_SYSTEM = True
except ImportError:
    try:
        from cogs.modération.perm.perm import Perm
        HAS_PERMISSION_SYSTEM = True
    except ImportError:
        HAS_PERMISSION_SYSTEM = False

class Derank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_base_embed(self, source, title, description):
        guild = getattr(source, 'guild', None)
        user = getattr(source, 'user', getattr(source, 'author', None))
        if config_manager:
            return config_manager.get_formatted_embed(guild=guild, user=user, bot=self.bot, title=title, description=description)
        return discord.Embed(title=title, description=description, color=0xff4444)

    @commands.hybrid_command(
        name="derank", 
        description="Retire tous les rôles d'un membre (Action définitive)"
    )
    @commands.has_permissions(manage_roles=True)
    async def derank(self, ctx: commands.Context, member: discord.Member):
        # Vérification des permissions personnalisées
        if HAS_PERMISSION_SYSTEM:
            # Récupérer le cog de permissions
            perm_cog = self.bot.get_cog('Perm')
            if perm_cog:
                # Vérifier si l'utilisateur a la permission pour la commande derank
                has_perm = perm_cog.has_permission(ctx.guild.id, ctx.author.id, "derank", ctx.author.roles)
                if not has_perm:
                    return await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        
        # 1. On dit à Discord de patienter (évite "L'application ne répond pas")
        await ctx.defer()
        
        print(f"\n[DERANK LOG] Lancement par {ctx.author} sur {member}")
        
        # Sécurités de base
        if member.id == ctx.guild.owner_id:
            return await ctx.send("❌ Impossible de déclasser le propriétaire.", ephemeral=True)
        
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Hiérarchie : Ce membre est plus haut ou égal à vous.", ephemeral=True)

        # Filtrage (On ignore @everyone et les rôles gérés)
        to_remove = [r for r in member.roles[1:] if not r.managed]
        
        if not to_remove:
            return await ctx.send("ℹ️ Aucun rôle amovible trouvé.", ephemeral=True)

        # Tri : Plus haut au plus bas
        to_remove.sort(key=lambda r: r.position, reverse=True)

        # Nettoyage si préfixe
        if not ctx.interaction:
            try: await ctx.message.delete()
            except: pass

        role_list_text = []
        bot_top_role = ctx.guild.me.top_role

        # 2. Traitement des rôles
        for r in to_remove:
            label = ""
            if r.permissions.administrator: label = " <--- ADMIN"
            elif any([r.permissions.manage_guild, r.permissions.manage_roles, r.permissions.kick_members]):
                label = " <--- GESTION"

            if r.position >= bot_top_role.position:
                print(f"[DERANK LOG] ❌ Impossible de retirer '{r.name}' : Position {r.position} >= Bot {bot_top_role.position}")
                role_list_text.append(f"• {r.mention}{label} (Échec : Hiérarchie bot)")
            else:
                try:
                    await member.remove_roles(r, reason=f"Derank par {ctx.author}")
                    role_list_text.append(f"• {r.mention}{label}")
                    print(f"[DERANK LOG] ✅ Rôle '{r.name}' retiré.")
                except Exception as e:
                    print(f"[DERANK LOG] ❌ Erreur sur '{r.name}' : {e}")
                    role_list_text.append(f"• {r.mention}{label} (Erreur technique)")

        # 3. Envoi de l'Embed de résultat
        desc = (
            f"L'utilisateur {member.mention} a été déclassé.\n\n"
            f"**Rôles retirés :**\n" + "\n".join(role_list_text)
        )
        
        embed = self.create_base_embed(ctx, "📉 Déclassement Effectué", desc)
        
        # En mode Hybrid, après un defer(), on utilise ctx.send normalement
        await ctx.send(embed=embed)
        print("[DERANK LOG] Commande terminée.\n")

async def setup(bot):
    await bot.add_cog(Derank(bot))