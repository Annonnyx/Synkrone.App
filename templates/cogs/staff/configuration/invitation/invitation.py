import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import json
import os
import asyncio
from typing import Optional

try:
    from ..utils import config_manager
    HAS_CUSTOM_EMBED = True
except ImportError:
    config_manager = None
    HAS_CUSTOM_EMBED = False

# --- Vue pour les boutons de configuration ---
class InvitationView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    def update_buttons(self, guild_id):
        current_mode = self.cog.get_guild_mode(guild_id)
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.style = discord.ButtonStyle.success if item.label == current_mode else discord.ButtonStyle.secondary

    @discord.ui.button(label="Normal", style=discord.ButtonStyle.secondary)
    async def normal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.user.guild_permissions.administrator:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ Vous devez être administrateur pour utiliser cette commande.", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Vous devez être administrateur pour utiliser cette commande.", ephemeral=True)
                return
                
            self.cog.save_guild_config(interaction.guild.id, "Normal")
            self.update_buttons(interaction.guild.id)
            embed = await self.cog.get_config_embed(interaction.guild, interaction.user)
            
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"Erreur dans le bouton Normal: {e}")
            try:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ Une erreur est survenue lors de la mise à jour.", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Une erreur est survenue lors de la mise à jour.", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="Unique", style=discord.ButtonStyle.secondary)
    async def unique_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.user.guild_permissions.administrator:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ Vous devez être administrateur pour utiliser cette commande.", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Vous devez être administrateur pour utiliser cette commande.", ephemeral=True)
                return
                
            # Suppression des anciennes invitations
            invites = await interaction.guild.invites()
            for inv in invites:
                if not inv.inviter.bot: 
                    try: 
                        await inv.delete()
                    except: 
                        pass
                        
            # Création d'une nouvelle invitation permanente
            new_invite = await interaction.channel.create_invite(
                max_age=0,  # Pas d'expiration
                max_uses=0,  # Nombre illimité d'utilisations
                unique=True  # Crée un code d'invitation unique
            )
            
            self.cog.save_guild_config(interaction.guild.id, "Unique", invite_url=new_invite.url)
            self.update_buttons(interaction.guild.id)
            
            embed = await self.cog.get_config_embed(interaction.guild, interaction.user)
            
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Je n'ai pas les permissions nécessaires pour gérer les invitations.", 
                ephemeral=True
            )
        except Exception as e:
            print(f"Erreur dans le bouton Unique: {e}")
            try:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ Une erreur est survenue lors de la mise à jour.", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Une erreur est survenue lors de la mise à jour.", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="Statistiques", style=discord.ButtonStyle.secondary)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.user.guild_permissions.administrator:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ Vous devez être administrateur pour utiliser cette commande.", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Vous devez être administrateur pour utiliser cette commande.", ephemeral=True)
                return
                
            self.cog.save_guild_config(interaction.guild.id, "Statistiques")
            self.update_buttons(interaction.guild.id)
            embed = await self.cog.get_config_embed(interaction.guild, interaction.user)
            
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"Erreur dans le bouton Statistiques: {e}")
            try:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ Une erreur est survenue lors de la mise à jour.", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Une erreur est survenue lors de la mise à jour.", ephemeral=True)
            except:
                pass

# --- Cog Principal ---
class InvitationManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cog_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.cog_dir, "invitation_data.db")
        self.config_dir = os.path.join(self.cog_dir, "guild_configs")
        
        # Création du dossier de config s'il n'existe pas
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    async def cog_load(self):
        # Initialisation DB SQLite
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    guild_id INTEGER, user_id INTEGER,
                    total_invites INTEGER DEFAULT 0,
                    valid_invites INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            ''')
            await db.commit()

    def get_guild_config(self, guild_id):
        """Récupère la config JSON d'un serveur"""
        file_path = os.path.join(self.config_dir, f"{guild_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return {"mode": "Normal", "unique_url": None}

    def get_guild_mode(self, guild_id):
        return self.get_guild_config(guild_id).get("mode", "Normal")

    def save_guild_config(self, guild_id, mode, invite_url=None):
        """Sauvegarde la config dans le fichier JSON du serveur"""
        file_path = os.path.join(self.config_dir, f"{guild_id}.json")
        data = {"mode": mode, "unique_url": invite_url}
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    async def get_config_embed(self, guild, user=None):
        config = self.get_guild_config(guild.id)
        mode = config["mode"]
        url = config["unique_url"]
        
        title = "📩│Gestion des Invitations"
        description = f"**Mode Actif :** `{mode}`\n"
        if mode == "Unique" and url:
            description += f"🔗 **Lien Permanent :** {url}\n"
        description += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        if mode == "Statistiques":
            async with aiosqlite.connect(self.db_path) as db:
                # Récupération des stats pour le classement
                async with db.execute("""
                    SELECT user_id, total_invites, valid_invites 
                    FROM stats 
                    WHERE guild_id = ? 
                    ORDER BY total_invites DESC 
                    LIMIT 10
                """, (guild.id,)) as cursor:
                    rows = await cursor.fetchall()
                
                if rows:
                    description += "🏆 **CLASSEMENT DES INVITEURS**\n\n"
                    for i, (user_id, total, valid) in enumerate(rows, 1):
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
                        description += f"{medal} <@{user_id}>\n┗ **{total}** Invites • **{valid}** Valides\n"
                else:
                    description += "✨ *Aucune donnée de classement pour le moment.*\n*Invitez des gens pour apparaître ici !*"

        if config_manager:
            return config_manager.get_formatted_embed(guild, user or guild.me, self.bot, title, description, guild.id)
        
        embed = discord.Embed(title=title, description=description, color=0x2b2d31)
        if guild.icon: 
            embed.set_thumbnail(url=guild.icon.url)
        return embed

    @commands.hybrid_command(name="invitation", description="Configuration du système d'invitations (Admin)")
    @commands.has_permissions(administrator=True)
    async def invitation(self, ctx: commands.Context):
        """Configure le système d'invitations (Admin uniquement)"""
        # Suppression du message de commande si c'est une commande texte
        if not ctx.interaction and ctx.message:
            try:
                await ctx.message.delete()
            except:
                pass
            
        view = InvitationView(self)
        view.update_buttons(ctx.guild.id)
        embed = await self.get_config_embed(ctx.guild, ctx.author)
        
        try:
            if isinstance(ctx, commands.Context):
                if ctx.interaction:
                    if not ctx.interaction.response.is_done():
                        await ctx.interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                    else:
                        await ctx.interaction.followup.send(embed=embed, view=view, ephemeral=True)
                else:
                    await ctx.send(embed=embed, view=view, delete_after=60)
        except Exception as e:
            print(f"Erreur dans la commande invitation: {e}")
            try:
                await ctx.send("❌ Une erreur est survenue lors de l'affichage du panneau de configuration.", ephemeral=True)
            except:
                pass

    @commands.hybrid_command(name="invit", description="Voir les statistiques d'invitation")
    @app_commands.describe(membre="Membre dont vous voulez voir les statistiques (optionnel)")
    async def invit(self, ctx: commands.Context, membre: Optional[discord.Member] = None):
        """Affiche les statistiques d'invitation d'un membre ou le classement général"""
        if not ctx.interaction and ctx.message:
            try:
                await ctx.message.delete()
            except:
                pass
            await ctx.message.delete()
            
        config = self.get_guild_config(ctx.guild.id)
        mode = config["mode"]

        if mode == "Normal":
            msg = "❌ Les statistiques ne sont pas activées sur ce serveur."
            return await ctx.send(msg, ephemeral=True, delete_after=10)
            
        if mode == "Unique":
            if config["unique_url"]:
                return await ctx.send(f"🔗 **Lien d'invitation unique :** {config['unique_url']}", ephemeral=True)
            return await ctx.send("❌ Aucun lien unique configuré.", ephemeral=True)

        async with aiosqlite.connect(self.db_path) as db:
            if membre:
                # Affichage des stats d'un membre spécifique
                async with db.execute("""
                    SELECT total_invites, valid_invites, total_messages 
                    FROM stats 
                    WHERE guild_id = ? AND user_id = ?
                """, (ctx.guild.id, membre.id)) as cursor:
                    row = await cursor.fetchone()
                
                total, valides, messages = row if row else (0, 0, 0)
                
                title = f"📊 Statistiques de {membre.display_name}"
                description = (
                    f"**Invitations**\n"
                    f"• Total : **{total}**\n"
                    f"• Valides (7j+) : **{valides}**\n\n"
                    f"**Activité**\n"
                    f"• Messages : **{messages:,}**"
                )
                
                if config_manager:
                    embed = config_manager.get_formatted_embed(ctx.guild, ctx.author, self.bot, title, description, ctx.guild.id)
                else:
                    embed = discord.Embed(title=title, description=description, color=0x2b2d31)
                    embed.set_thumbnail(url=membre.display_avatar.url)
                
                if ctx.interaction:
                    await ctx.interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await ctx.send(embed=embed, delete_after=60)
                    
            else:
                # Affichage du classement
                async with db.execute("""
                    SELECT user_id, total_invites, valid_invites 
                    FROM stats 
                    WHERE guild_id = ? 
                    ORDER BY total_invites DESC 
                    LIMIT 10
                """, (ctx.guild.id,)) as cursor:
                    rows_inv = await cursor.fetchall()
                    
                async with db.execute("""
                    SELECT user_id, total_messages 
                    FROM stats 
                    WHERE guild_id = ? 
                    ORDER BY total_messages DESC 
                    LIMIT 5
                """, (ctx.guild.id,)) as cursor:
                    rows_msg = await cursor.fetchall()

                title = "🏆│Classement des Invitations"
                txt_inv = "\n".join(
                    [f"{i+1}. <@{r[0]}> **[**`{r[1]}`**]** (Valides: `{r[2]}`)" 
                     for i, r in enumerate(rows_inv)]
                ) or "Personne n'a encore d'invitations !"
                
                txt_msg = "\n".join(
                    [f"⭐ <@{r[0]}> : `{r[1]:,}` messages" 
                     for r in rows_msg]
                ) or "Aucune activité pour le moment !"
                
                description = (
                    "**Top 10 des Inviteurs**\n" + 
                    txt_inv + 
                    "\n\n**🔥 Top 5 Activité**\n" + 
                    txt_msg
                )
                
                if config_manager:
                    embed = config_manager.get_formatted_embed(ctx.guild, ctx.author, self.bot, title, description, ctx.guild.id)
                else:
                    embed = discord.Embed(title=title, description=description, color=0x2b2d31)
                    if ctx.guild.icon:
                        embed.set_thumbnail(url=ctx.guild.icon.url)
                
                if ctx.interaction:
                    await ctx.interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await ctx.send(embed=embed, delete_after=60)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if self.get_guild_mode(invite.guild.id) == "Unique" and invite.inviter.id != self.bot.user.id:
            try: await invite.delete()
            except: pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot: return
        if self.get_guild_mode(message.guild.id) == "Statistiques":
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO stats (guild_id, user_id, total_messages) VALUES (?, ?, 1)
                    ON CONFLICT(guild_id, user_id) DO UPDATE SET total_messages = total_messages + 1
                ''', (message.guild.id, message.author.id))
                await db.commit()

async def setup(bot):
    await bot.add_cog(InvitationManager(bot))