import discord, re, json, asyncio
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select, Modal, TextInput
from pathlib import Path

# --- SYSTÈME D'IMPORT CONFIG_MANAGER ---
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class AddUserModal(Modal, title="➕ Ajouter par ID"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        
    user_id = TextInput(
        label="ID de l'utilisateur",
        placeholder="Entrez l'ID Discord de l'utilisateur à ajouter",
        required=True,
        style=discord.TextStyle.short,
        max_length=20
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value.strip())
            member = self.view.ctx.guild.get_member(user_id)
            
            if member and member not in self.view.members and member != interaction.user:
                self.view.members.append(member)
                await self.view.update_message(interaction)
                await interaction.response.send_message(f"✅ {member.mention} ajouté à la liste", ephemeral=True)
            elif not member:
                await interaction.response.send_message(f"❌ ID {user_id} : utilisateur non trouvé sur ce serveur", ephemeral=True)
            elif member == interaction.user:
                await interaction.response.send_message("❌ Vous ne pouvez pas vous bannir vous-même", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {member.mention} est déjà dans la liste", ephemeral=True)
                
        except ValueError:
            await interaction.response.send_message(f"❌ ID '{self.user_id.value}' : format invalide", ephemeral=True)


class DurationModal(Modal, title="⏱️ Durée du bannissement"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        
    duration = TextInput(
        label="⏱️ Durée (ex: 2h, 30m, 1j, 1S, 3M, 1a)",
        placeholder="Entrez la durée avec l'unité (s/m/h/j/S/M/a)",
        required=True,
        style=discord.TextStyle.short,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            units = {'a': 31536000, 'M': 2592000, 'S': 604800, 'j': 86400, 'h': 3600, 'm': 60, 's': 1}
            seconds = 0
            matches = re.findall(r"(\d+)([aSMjhms])", self.duration.value.lower())
            for val, unit in matches:
                seconds += int(val) * units[unit]
            
            if seconds <= 0:
                await interaction.response.send_message("❌ Durée invalide!", ephemeral=True)
                return
                
            self.view.duration = self.duration.value
            self.view.duration_seconds = seconds
            await self.view.update_message(interaction)
            await interaction.response.send_message("✅ Durée enregistrée!", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Format de durée invalide!", ephemeral=True)

class ReasonModal(Modal, title="📝 Motif du bannissement"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        
    reason = TextInput(
        label="📝 Raison du bannissement",
        placeholder="Entrez la raison (minimum 10 caractères)",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500,
        min_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        self.view.reason = self.reason.value
        await self.view.update_message(interaction)
        await interaction.response.send_message("✅ Raison enregistrée!", ephemeral=True)

class TempBanView(View):
    def __init__(self, ctx, members=None):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.author = ctx.author
        self.members = members or []
        self.duration = "24h"  # Durée par défaut
        self.duration_seconds = 86400  # 24h en secondes
        self.reason = None
        self.mode = "main"  # main, users
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Vous n'êtes pas autorisé à utiliser ce menu!", ephemeral=True)
            return False
        return True
    
    # Définir les callbacks directement
    @discord.ui.button(label="Retour", style=discord.ButtonStyle.secondary, custom_id="back", emoji="🔙")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "main"
        await self.update_message(interaction)
        await interaction.response.defer()
    
    @discord.ui.button(label="Ajouter ID", style=discord.ButtonStyle.success, custom_id="add_id", emoji="➕")
    async def add_id_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddUserModal(self))
    
    @discord.ui.button(label="Ajouter Tags", style=discord.ButtonStyle.success, custom_id="add_tags", emoji="🏷️")
    async def add_tags_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🏷️ **Veuillez envoyer les tags des utilisateurs dans ce chat :**\n"
            "Exemple : `@user1 @user2 @user3`\n\n"
            "J'attendrai votre message pendant 30 secondes...",
            ephemeral=True
        )
        
        # Attendre le message de l'utilisateur
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        
        try:
            msg = await self.ctx.bot.wait_for('message', check=check, timeout=30.0)
            
            added = []
            failed = []
            
            pattern = r'<@!?(\d+)>'
            matches = re.findall(pattern, msg.content)
            
            if not matches:
                await interaction.followup.send("❌ Aucun tag valide trouvé. Utilisez @user1 @user2...", ephemeral=True)
                return
            
            for match in matches:
                try:
                    user_id = int(match)
                    member = self.ctx.guild.get_member(user_id)
                    if member and member not in self.members and member != interaction.user:
                        self.members.append(member)
                        added.append(member)
                    elif not member:
                        failed.append(f"Tag {match} : utilisateur non trouvé")
                    elif member == interaction.user:
                        failed.append(f"Tag {match} : vous ne pouvez pas vous bannir")
                    else:
                        failed.append(f"Tag {match} : déjà dans la liste")
                except:
                    failed.append(f"Tag {match} : erreur de parsing")
            
            await self.update_message(interaction)
            
            if added:
                added_text = "\n".join([f"✅ {m.mention}" for m in added])
                message = f"**Utilisateurs ajoutés :**\n{added_text}"
                if failed:
                    message += f"\n\n**Erreurs :**\n" + "\n".join([f"❌ {err}" for err in failed])
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.followup.send(f"**Erreurs :**\n" + "\n".join([f"❌ {err}" for err in failed]), ephemeral=True)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Temps écoulé. Veuillez réessayer.", ephemeral=True)
    
    @discord.ui.button(label="Utilisateurs", style=discord.ButtonStyle.primary, custom_id="users", emoji="👥")
    async def users_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "users"
        await self.update_message(interaction)
        await interaction.response.defer()
    
    @discord.ui.button(label="Durée", style=discord.ButtonStyle.primary, custom_id="duration", emoji="⏱️")
    async def duration_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DurationModal(self))
    
    @discord.ui.button(label="Raison", style=discord.ButtonStyle.primary, custom_id="reason", emoji="📝")
    async def reason_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReasonModal(self))
    
    @discord.ui.button(label="BANNIR", style=discord.ButtonStyle.danger, custom_id="ban", emoji="🔨")
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.execute_ban(interaction)
    
    def create_embed(self):
        if self.mode == "users":
            members_text = "\n".join([f"**{i+1}.** {m.mention} (`{m.id}`)" for i, m in enumerate(self.members)])
            
            # Explications des commandes rapides
            help_text = (
                "💡 **Commandes rapides :**\n"
                "• `!tempban @user 24h Spam` - Bannir directement\n"
                "• `/tempban membres:@user durée:24h raison:Spam` - Version slash\n\n"
                "🎮 **Utilisez le sélecteur ci-dessous pour retirer des utilisateurs**"
            )
            
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=self.ctx.guild, 
                    user=self.author, 
                    bot=self.ctx.bot, 
                    title="👥 Gestion des Utilisateurs",
                    description=f"**Utilisateurs à bannir :**\n{members_text if self.members else '`vide`'}\n\n{help_text}"
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1284145607118348328.png")
            else:
                embed = discord.Embed(
                    title="👥 Gestion des Utilisateurs",
                    description=f"**Utilisateurs à bannir :**\n{members_text if self.members else '`vide`'}\n\n{help_text}",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1284145607118348328.png")
                embed.set_footer(text=f"🎮 Menu contrôlé par {self.author.display_name} • Timeout: 5 minutes", 
                                icon_url=self.author.avatar.url if self.author.avatar else None)
        else:
            members_text = "\n".join([f"**{i+1}.** {m.mention} (`{m.id}`)" for i, m in enumerate(self.members)])
            
            # Statut des champs
            status_members = "✅" if self.members else "❌"
            status_duration = "✅" if self.duration else "❌"
            status_reason = "✅" if self.reason else "❌"
            
            # Explications des commandes rapides
            help_text = (
                "⚡ **Commandes rapides (sans menu) :**\n"
                "• `!tempban @user 24h Spam` - Bannir direct\n"
                "• `!tempban @user1 @user2 3M Multi-comptes` - Plusieurs users\n"
                "• `/tempban membres:@user durée:1j raison:Insultes` - Version slash\n\n"
                f"{'🟢 **Prêt à bannir !**' if self.members and self.duration and self.reason else '🔴 **Veuillez compléter tous les champs**'}"
            )
            
            description = (f"**{status_members} Membre(s) à bannir :**\n{members_text if self.members else '`vide`'}\n\n"
                          f"**{status_duration} ⏱️ Durée du ban :** `{self.duration or 'vide'}`\n\n"
                          f"**{status_reason} 📝 Motif du ban :** `{self.reason or 'vide'}`\n\n"
                          f"{help_text}")
            
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=self.ctx.guild, 
                    user=self.author, 
                    bot=self.ctx.bot, 
                    title="🔨 Menu de Bannissement Temporaire",
                    description=description
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1284145607118348328.png")
            else:
                embed = discord.Embed(
                    title="🔨 Menu de Bannissement Temporaire",
                    description=description,
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1284145607118348328.png")
                embed.set_footer(text=f"🎮 Menu contrôlé par {self.author.display_name} • Timeout: 5 minutes", 
                                icon_url=self.author.avatar.url if self.author.avatar else None)
                
                # Ajouter des champs supplémentaires (uniquement sans config_manager)
                if self.members:
                    embed.add_field(name="👥 Nombre d'utilisateurs", value=f"**{len(self.members)}** utilisateur(s)", inline=True)
                if self.duration:
                    embed.add_field(name="⏱️ Durée", value=f"**{self.duration}**", inline=True)
                if self.reason:
                    embed.add_field(name="📝 Raison", value=f"```{self.reason}```", inline=False)
        
        return embed
    
    async def update_message(self, interaction=None):
        embed = self.create_embed()
        self.clear_items()
        
        if self.mode == "users":
            # Mode sélection utilisateurs - ajouter seulement les boutons nécessaires
            self.add_item(self.back_button)
            self.add_item(self.add_id_button)
            self.add_item(self.add_tags_button)
            
            # Sélecteur de membres
            if self.members:
                options = [
                    discord.SelectOption(
                        label=f"{i+1}. {m.display_name}",
                        description=f"ID: {m.id}",
                        value=str(i),
                        emoji="👤"
                    ) for i, m in enumerate(self.members)
                ]
                select = Select(placeholder="🗑️ Retirer un utilisateur", options=options, custom_id="remove_user")
                select.callback = self.select_callback
                self.add_item(select)
        else:
            # Mode principal - ajouter seulement les boutons nécessaires
            self.add_item(self.users_button)
            self.add_item(self.duration_button)
            self.add_item(self.reason_button)
            
            # Bouton Bannir (uniquement si tout est rempli)
            if self.members and self.duration and self.reason:
                self.add_item(self.ban_button)
        
        if interaction:
            await interaction.message.edit(embed=embed, view=self)
        else:
            return embed
    
    async def button_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        
        if custom_id == "back":
            self.mode = "main"
            await self.update_message(interaction)
            await interaction.response.defer()
            
        elif custom_id == "add":
            await interaction.response.send_message(
                "📝 **Pour ajouter des utilisateurs :**\n"
                "Utilisez `!tempban @user1 @user2` ou `/tempban membres:@user1 @user2`",
                ephemeral=True
            )
            
        elif custom_id == "users":
            self.mode = "users"
            await self.update_message(interaction)
            await interaction.response.defer()
            
        elif custom_id == "duration":
            await interaction.response.send_modal(DurationModal(self))
            
        elif custom_id == "reason":
            await interaction.response.send_modal(ReasonModal(self))
            
        elif custom_id == "ban":
            await self.execute_ban(interaction)
    
    async def select_callback(self, interaction: discord.Interaction):
        index = int(interaction.data["values"][0])
        if 0 <= index < len(self.members):
            removed = self.members.pop(index)
            await self.update_message(interaction)
            await interaction.response.send_message(f"✅ {removed.mention} retiré de la liste", ephemeral=True)
    
    async def execute_ban(self, interaction: discord.Interaction):
        if not self.members or not self.duration or not self.reason:
            await interaction.response.send_message("❌ Veuillez remplir tous les champs!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        success = []
        failed = []
        
        for member in self.members:
            try:
                await self.ctx.guild.ban(member, reason=f"TempBan par {self.author}: {self.reason}", delete_message_days=0)
                
                # Enregistrement des données
                file_path = self.get_data_file(self.ctx.guild.id)
                data = json.loads(file_path.read_text(encoding="utf-8"))
                
                data[str(member.id)] = {
                    "user_id": member.id,
                    "reason": self.reason,
                    "expires_at": discord.utils.utcnow().timestamp() + self.duration_seconds,
                    "type": "global"
                }
                file_path.write_text(json.dumps(data, indent=4), encoding="utf-8")
                
                success.append(member)
                
                try:
                    await member.send(f"🚫 Vous avez été banni de **{self.ctx.guild.name}** pour **{self.duration}**.\n**Raison :** {self.reason}")
                except:
                    pass
                    
            except Exception as e:
                failed.append((member, str(e)))
        
        # Message de résultat
        if success:
            description = f"✅ **{len(success)}** membre(s) banni(s) avec succès pour **{self.duration}**\n\n📝 **Raison :** {self.reason}"
            
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=self.ctx.guild, 
                    user=self.author, 
                    bot=self.ctx.bot, 
                    title="Bannissement(s) Effectué(s)",
                    description=description
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1284145607118348328.png")
            else:
                embed = discord.Embed(
                    title="🔨 Bannissement(s) Effectué(s)",
                    description=description,
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1284145607118348328.png")
                embed.set_footer(text=f"🎮 Action par {self.author.display_name}", 
                                icon_url=self.author.avatar.url if self.author.avatar else None)
            
            await self.ctx.send(embed=embed)
        
        if failed:
            fail_text = "\n".join([f"❌ {m.mention}: {err}" for m, err in failed])
            
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=self.ctx.guild, 
                    user=self.author, 
                    bot=self.ctx.bot, 
                    title="Erreurs de Bannissement",
                    description=fail_text
                )
            else:
                embed = discord.Embed(
                    title="❌ Erreurs de Bannissement",
                    description=fail_text,
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"🎮 Action par {self.author.display_name}", 
                                icon_url=self.author.avatar.url if self.author.avatar else None)
            
            await self.ctx.send(embed=embed, ephemeral=True)
        
        self.stop()
    
    def get_data_file(self, guild_id):
        folder = Path(__file__).parent / "data"
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / f"{guild_id}_global.json"
        if not file_path.exists(): 
            file_path.write_text("{}", encoding="utf-8")
        return file_path

class TempBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, ctx, title, description, color=discord.Color.orange()):
        if config_manager:
            return config_manager.get_formatted_embed(guild=ctx.guild, user=ctx.author, bot=self.bot, title=title, description=description)
        return discord.Embed(title=title, description=description, color=color)

    @commands.hybrid_command(name="tempban", description="🔨 Menu de bannissement temporaire interactif")
    @app_commands.describe(membres="Les membres à bannir (optionnel)")
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, membres: str = None):
        members = []
        
        if membres:
            # Parser les mentions/IDs
            pattern = r'<@!?(\d+)>|(\d{17,19})'
            matches = re.findall(pattern, membres)
            
            for match in matches:
                user_id = int(match[0] if match[0] else match[1])
                member = ctx.guild.get_member(user_id)
                if member and member != ctx.author:
                    members.append(member)
        
        view = TempBanView(ctx, members)
        embed = await view.update_message()
        message = await ctx.send(embed=embed, view=view)

async def setup(bot): 
    await bot.add_cog(TempBan(bot))
