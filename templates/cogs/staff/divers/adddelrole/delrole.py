import discord
from discord.ext import commands
from discord import app_commands
import re

# --- IMPORT CONFIG MANAGER ---
# Utilisation du chemin absolu avec fallback pour éviter l'erreur ModuleNotFoundError
try:
    from cogs.staff.developpeur.commands.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class DelRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = config_manager

    async def find_member(self, ctx, member_input):
        """Recherche un membre par ID, mention ou nom"""
        if member_input.startswith('<@') and member_input.endswith('>'):
            try:
                member_id = int(member_input.strip('<@!>'))
                return ctx.guild.get_member(member_id)
            except ValueError:
                pass
        
        if member_input.isdigit():
            return ctx.guild.get_member(int(member_input))
        
        for member in ctx.guild.members:
            if member.name.lower() == member_input.lower() or member.display_name.lower() == member_input.lower():
                return member
        return None
    
    async def find_role(self, ctx, role_input):
        """Recherche un rôle par ID, mention ou nom"""
        if role_input.startswith('<@&') and role_input.endswith('>'):
            try:
                role_id = int(role_input.strip('<@&>'))
                return ctx.guild.get_role(role_id)
            except ValueError:
                pass
        
        if role_input.isdigit():
            return ctx.guild.get_role(int(role_input))
        
        for role in ctx.guild.roles:
            if role.name.lower() == role_input.lower():
                return role
        return None

    def get_embed(self, guild, user, title, description):
        """Génère l'embed via config_manager ou standard si absent"""
        if self.config_manager:
            return self.config_manager.get_formatted_embed(
                guild=guild, user=user, bot=self.bot,
                title=title, description=description
            )
        return discord.Embed(title=title, description=description, color=discord.Color.red())

    @commands.hybrid_command(name="delrole", description="Retire un rôle d'un membre")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="Membre à qui retirer le rôle", role="Rôle à retirer")
    async def delrole(self, ctx: commands.Context, member: str = None, role: str = None):
        """Retire un rôle d'un membre"""
        
        if member is None or role is None:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Argument manquant", "Veuillez spécifier un membre et un rôle.\nUsage: `!delrole [membre] [rôle]`")
            return await ctx.send(embed=embed)
        
        # Recherche du membre
        target_member = await self.find_member(ctx, member)
        if target_member is None:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Membre introuvable", f"Impossible de trouver le membre `{member}`.")
            return await ctx.send(embed=embed)
        
        # Recherche du rôle
        target_role = await self.find_role(ctx, role)
        if target_role is None:
            # Recherche de suggestions
            similar_roles = [r.name for r in ctx.guild.roles if role.lower() in r.name.lower()][:5]
            suggestions = "💡 **Suggestions :**\n" + "\n".join([f"• `{r}`" for r in similar_roles]) if similar_roles else "Aucune suggestion."
            
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Rôle introuvable", f"Le rôle `{role}` n'existe pas.\n\n{suggestions}")
            return await ctx.send(embed=embed)
        
        # Vérification de la hiérarchie
        if target_role.position >= ctx.author.top_role.position and ctx.author.id != ctx.guild.owner_id:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Hiérarchie", "Vous ne pouvez pas retirer un rôle supérieur ou égal au vôtre.")
            return await ctx.send(embed=embed)
        
        if target_role.position >= ctx.guild.me.top_role.position:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Hiérarchie du bot", "Ce rôle est au-dessus de mes capacités (hiérarchie).")
            return await ctx.send(embed=embed)
        
        try:
            if target_role not in target_member.roles:
                embed = self.get_embed(ctx.guild, ctx.author, "❌ Rôle non possédé", f"{target_member.mention} n'a pas le rôle `{target_role.name}`.")
                return await ctx.send(embed=embed)
            
            await target_member.remove_roles(target_role, reason=f"Retiré par {ctx.author}")
            embed = self.get_embed(ctx.guild, ctx.author, "✅ Rôle retiré", f"Le rôle {target_role.mention} a été retiré à {target_member.mention}.")
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Permission refusée", "Je n'ai pas les permissions nécessaires pour modifier ce rôle.")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Erreur", f"Une erreur est survenue : `{str(e)}`")
            await ctx.send(embed=embed)

    @delrole.error
    async def delrole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Permission refusée", "Vous n'avez pas la permission de gérer les rôles.")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DelRole(bot))