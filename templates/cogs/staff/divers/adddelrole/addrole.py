import discord
from discord.ext import commands
from discord import app_commands
import re

# --- IMPORT CONFIG MANAGER ---
try:
    from cogs.staff.developpeur.commands.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class AddRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_role_creations = {}
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
        
        matching_roles = [r for r in ctx.guild.roles if role_input.lower() in r.name.lower()]
        if len(matching_roles) == 1:
            return matching_roles[0]
        
        return None

    def get_embed(self, guild, user, title, description):
        """Génère l'embed via config_manager ou standard"""
        if self.config_manager:
            return self.config_manager.get_formatted_embed(
                guild=guild, user=user, bot=self.bot,
                title=title, description=description
            )
        return discord.Embed(title=title, description=description, color=discord.Color.blue())

    @commands.hybrid_command(name="addrole", description="Ajoute un rôle à un membre")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="Membre à qui ajouter le rôle", role="Rôle à ajouter")
    async def addrole(self, ctx: commands.Context, member: str = None, *, role: str = None):
        if member is None or role is None:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Argument manquant", "Usage: `!addrole [membre] [rôle]`")
            return await ctx.send(embed=embed)
        
        target_member = await self.find_member(ctx, member)
        if target_member is None:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Membre introuvable", f"Impossible de trouver le membre `{member}`.")
            return await ctx.send(embed=embed)
        
        target_role = await self.find_role(ctx, role)
        
        # Si rôle introuvable, proposer la création
        if target_role is None:
            if role.isdigit():
                embed = self.get_embed(ctx.guild, ctx.author, "❌ ID introuvable", f"Aucun rôle trouvé avec l'ID `{role}`.")
                return await ctx.send(embed=embed)
            
            embed = self.get_embed(ctx.guild, ctx.author, "🔍 Rôle introuvable", f"Le rôle `{role}` n'existe pas. Voulez-vous le créer ?")
            view = RoleCreationView(ctx, role, target_member, self.config_manager, self.bot)
            return await ctx.send(embed=embed, view=view)

        # Vérification Hiérarchie
        if target_role.position >= ctx.author.top_role.position and ctx.author.id != ctx.guild.owner_id:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Hiérarchie", "Ce rôle est supérieur ou égal au vôtre.")
            return await ctx.send(embed=embed)
        
        try:
            if target_role in target_member.roles:
                embed = self.get_embed(ctx.guild, ctx.author, "❌ Erreur", f"{target_member.mention} possède déjà ce rôle.")
                return await ctx.send(embed=embed)
            
            await target_member.add_roles(target_role, reason=f"Ajouté par {ctx.author}")
            embed = self.get_embed(ctx.guild, ctx.author, "✅ Rôle ajouté", f"Le rôle {target_role.mention} a été ajouté à {target_member.mention}")
            await ctx.send(embed=embed)
        except Exception as e:
            embed = self.get_embed(ctx.guild, ctx.author, "❌ Erreur", str(e))
            await ctx.send(embed=embed)

class RoleCreationView(discord.ui.View):
    def __init__(self, ctx, role_name, member, config_mgr, bot):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.role_name = role_name
        self.member = member
        self.config_manager = config_mgr
        self.bot = bot

    def get_embed(self, title, description):
        if self.config_manager:
            return self.config_manager.get_formatted_embed(
                guild=self.ctx.guild, user=self.ctx.author, bot=self.bot,
                title=title, description=description
            )
        return discord.Embed(title=title, description=description)

    @discord.ui.button(label="✅ Créer le rôle", style=discord.ButtonStyle.success)
    async def create_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            new_role = await self.ctx.guild.create_role(name=self.role_name, reason=f"Auto-création par {self.ctx.author}")
            await self.member.add_roles(new_role)
            embed = self.get_embed("✅ Succès", f"Rôle {new_role.mention} créé et ajouté à {self.member.mention}")
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            await interaction.response.send_message(f"Erreur : {e}", ephemeral=True)

    @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.get_embed("❌ Annulé", "L'opération a été annulée.")
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(AddRole(bot))