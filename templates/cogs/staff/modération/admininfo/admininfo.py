import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio

# Gestion des imports pour le Config Manager
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class AdminInfoView(View):
    def __init__(self, bot, author_id):
        super().__init__(timeout=300)  # 5 minutes
        self.bot = bot
        self.author_id = author_id
        self.embed_type = "admins"  # Par défaut : Admins
        
        # Bouton Toggle
        self.toggle_button = Button(
            label="Voir les Bots",
            style=discord.ButtonStyle.primary,
            emoji="🤖"
        )
        self.toggle_button.callback = self.toggle_view
        self.add_item(self.toggle_button)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Optionnel : Restreindre l'interaction à l'auteur de la commande
        # if interaction.user.id != self.author_id:
        #     await interaction.response.send_message("❌ Vous ne pouvez pas interagir avec ce menu.", ephemeral=True)
        #     return False
        return True

    async def toggle_view(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Bascule du mode
        if self.embed_type == "admins":
            self.embed_type = "bots"
            self.toggle_button.label = "Voir les Admins"
            self.toggle_button.emoji = "👑"
            
            title = f"🤖 Bots de {interaction.guild.name}"
            desc = self.get_bots_description(interaction.guild)
            
        else:
            self.embed_type = "admins"
            self.toggle_button.label = "Voir les Bots"
            self.toggle_button.emoji = "🤖"
            
            title = f"👑 Administration de {interaction.guild.name}"
            desc = self.get_admins_description(interaction.guild)

        # Génération de l'embed via Config Manager
        if config_manager:
            embed = config_manager.get_formatted_embed(
                interaction.guild, interaction.user, self.bot,
                title, desc, interaction.guild.id
            )
        else:
            embed = discord.Embed(title=title, description=desc, color=0x5865F2)
            embed.set_footer(text=f"Demandé par {interaction.user.display_name}")

        await interaction.edit_original_response(embed=embed, view=self)

    def get_bots_description(self, guild):
        bots = [m for m in guild.members if m.bot]
        bots = sorted(bots, key=lambda x: x.name.lower())
        
        if not bots:
            return "Aucun bot trouvé sur ce serveur."
            
        # Pagination simple (50 premiers)
        bots_list = bots[:50]
        bot_count = len(bots)
        truncated = bot_count > 50
        
        desc = f"**{bot_count} bot{'s' if bot_count > 1 else ''} trouvé{'' if bot_count <= 1 else 's'}**\n\n"
        
        lines = []
        for bot in bots_list:
            flags = "🔒 Admin" if bot.guild_permissions.administrator else ""
            lines.append(f"• {bot.mention} - `{bot.name}` {flags}")
            
        desc += "\n".join(lines)
        
        if truncated:
            desc += f"\n\n*... et {bot_count - 50} autres bots.*"
            
        return desc

    def get_admins_description(self, guild):
        owner = guild.owner
        admins = [
            m for m in guild.members 
            if m.guild_permissions.administrator 
            and not m.bot 
            and (owner is None or m.id != owner.id)
        ]
        admins = sorted(admins, key=lambda x: x.name.lower())

        desc = ""
        
        # Propriétaire
        if owner:
            desc += f"👑 **Propriétaire**\n{owner.mention} - `{owner.name}`\n\n"
        
        # Administrateurs
        if not admins and not owner:
            return "Aucun administrateur trouvé sur ce serveur."
        
        if admins:
            desc += f"**Administrateurs ({len(admins)})**\n"
            desc += "\n".join(f"• {admin.mention} - `{admin.name}`" for admin in admins)
        elif owner and not admins:
            desc += "Aucun autre administrateur trouvé."
            
        return desc


class AdminInfoCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="admininfo", description="👑 Affiche les administrateurs et bots du serveur.")
    @discord.app_commands.guild_only()
    async def admininfo(self, ctx: commands.Context):
        if not ctx.guild:
            return await ctx.send("❌ Cette commande ne peut être utilisée que dans un serveur.", ephemeral=True)

        # Defer car le chunking peut être long
        await ctx.defer()

        try:
            # Forcer le chargement des membres (cache) pour avoir les listes complètes
            if not ctx.guild.chunked:
                await ctx.guild.chunk(cache=True)
        except Exception:
            pass # On continue même si le chunk échoue (ex: timeout)

        # Préparation des données initiales (Vue Admins)
        view = AdminInfoView(self.bot, ctx.author.id)
        title = f"👑 Administration de {ctx.guild.name}"
        description = view.get_admins_description(ctx.guild)

        # Création de l'embed avec Config Manager
        if config_manager:
            embed = config_manager.get_formatted_embed(
                ctx.guild, ctx.author, self.bot,
                title, description, ctx.guild.id
            )
        else:
            embed = discord.Embed(title=title, description=description, color=0x5865F2)
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            embed.set_footer(text=f"Demandé par {ctx.author.display_name}")

        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminInfoCommand(bot))