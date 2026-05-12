import discord
from discord.ext import commands
import math

# Import de ton manager personnalisé
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class RolePaginationView(discord.ui.View):
    """Vue pour la pagination de la liste complète des membres"""
    def __init__(self, members, role, author, bot, guild, per_page=15):
        super().__init__(timeout=180)
        self.members = members
        self.role = role
        self.author = author
        self.bot = bot
        self.guild = guild
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = max(1, math.ceil(len(members) / per_page))

        if self.total_pages > 1:
            self.add_item(PageSelector(self.total_pages))

    async def get_page_embed(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        subset = self.members[start:end]
        
        # Calcul des statistiques
        server_total = self.guild.member_count
        total_members = len(self.members)
        percentage = (total_members / server_total) * 100 if server_total > 0 else 0
        
        # Formatage intelligent du pourcentage (enlève le .0 si c'est un compte rond)
        pct_str = f"{round(percentage, 1):g}"
        
        title = "📜 Informations sur le rôle"
        
        # Liste des membres pour la page actuelle (sans la date)
        if not subset:
            member_list = "Aucun membre ne possède ce rôle actuellement."
        else:
            member_list = "\n".join([
                f"`{i+start+1}.` {m.mention}" 
                for i, m in enumerate(subset)
            ])
        
        # Construction de la description avec le tag du rôle et sans position/mention
        description = (
            f"**{self.role.mention}**\n"
            f"🆔 **ID** : `{self.role.id}`\n"
            f"📅 **Création** : <t:{int(self.role.created_at.timestamp())}:D> (<t:{int(self.role.created_at.timestamp())}:R>)\n"
            f"🌈 **Couleur** : `{str(self.role.color).upper()}`\n"
            f"👥 **Membres** : `{total_members}` ({pct_str}% du serveur)\n"
            f"### Liste des membres\n{member_list}"
        )
        
        page_info = f"Page {self.current_page + 1}/{self.total_pages}"

        if config_manager:
            embed = config_manager.get_formatted_embed(self.guild, self.author, self.bot, title, description, self.guild.id)
            # On récupère le footer de ton config_manager pour ne pas l'écraser
            footer_text = embed.footer.text if embed.footer and embed.footer.text else ""
            footer_icon = embed.footer.icon_url if embed.footer and embed.footer.icon_url else None
            # On fusionne ton footer avec la pagination (sans total)
            new_footer_text = f"{footer_text} • {page_info}" if footer_text else page_info
            if footer_icon:
                embed.set_footer(text=new_footer_text, icon_url=footer_icon)
            else:
                embed.set_footer(text=new_footer_text)
        else:
            embed = discord.Embed(title=title, description=description, color=self.role.color if self.role.color.value != 0 else 0x2b2d31)
            embed.set_footer(text=page_info)
            
        return embed

    @discord.ui.button(label="Précédent", emoji="◀️", style=discord.ButtonStyle.gray)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Tu ne peux pas contrôler ce menu.", ephemeral=True)
        self.current_page = (self.current_page - 1) % self.total_pages
        await interaction.response.edit_message(embed=await self.get_page_embed(), view=self)

    @discord.ui.button(label="Suivant", emoji="▶️", style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Tu ne peux pas contrôler ce menu.", ephemeral=True)
        self.current_page = (self.current_page + 1) % self.total_pages
        await interaction.response.edit_message(embed=await self.get_page_embed(), view=self)

class PageSelector(discord.ui.Select):
    """Sélecteur permettant de sauter directement à une page"""
    def __init__(self, total_pages):
        options = [
            discord.SelectOption(label=f"Page {i+1}", value=str(i)) 
            for i in range(min(total_pages, 25))
        ]
        super().__init__(placeholder="Aller à la page...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.author.id:
            return await interaction.response.send_message("Tu ne peux pas contrôler ce menu.", ephemeral=True)
        self.view.current_page = int(self.values[0])
        await interaction.response.edit_message(embed=await self.view.get_page_embed(), view=self.view)


class RoleInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="role", description="Affiche les informations détaillées d'un rôle.")
    async def role_info(self, ctx: commands.Context, role: discord.Role):
        await ctx.defer()
        guild = ctx.guild
        
        # SÉCURITÉ : On force le bot à charger les membres du serveur s'ils ne sont pas en cache
        if not guild.chunked:
            await guild.chunk()
        
        # TRI PAR OBTENTION (Basé sur joined_at, du plus récent au plus ancien)
        members = sorted(role.members, key=lambda m: (m.joined_at.timestamp() if m.joined_at else 0), reverse=True)
        
        # On initialise directement la vue de pagination
        view = RolePaginationView(members, role, ctx.author, self.bot, guild)
        
        # On récupère l'embed de la première page
        embed = await view.get_page_embed()
        
        # S'il n'y a qu'une seule page ou aucun membre, on peut retirer les boutons/select
        if view.total_pages <= 1:
            view.clear_items()

        # Envoi de l'embed paginé directement
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    if bot.get_command("role"):
        bot.remove_command("role")
    await bot.add_cog(RoleInfoCog(bot))