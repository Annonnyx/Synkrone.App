import discord
from discord.ext import commands, tasks
from discord import app_commands, ui
import re
import aiohttp
import asyncio
from typing import Dict, Optional

# Gestion des imports pour le Config Manager
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class EmojiView(ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__(timeout=300)  # Timeout de 5 minutes
        self.bot = bot
        self.user_id = user_id
        self.added_emojis = []
        self.message: Optional[discord.Message] = None
        self.instruction_message: Optional[discord.Message] = None
        self.last_interaction = asyncio.get_event_loop().time()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Vous ne pouvez pas utiliser ce menu.", ephemeral=True)
            return False
        self.last_interaction = asyncio.get_event_loop().time()
        return True
        
    async def delete_after_delay(self, message: discord.Message, delay: int):
        """Supprime un message après un délai donné."""
        try:
            await asyncio.sleep(delay)
            await message.delete()
        except (discord.NotFound, discord.HTTPException):
            pass

    def get_embed(self, guild, user, title, description):
        """Helper pour générer un embed via config_manager ou fallback."""
        if config_manager:
            return config_manager.get_formatted_embed(
                guild, user, self.bot,
                title, description, guild.id
            )
        else:
            # Fallback simple si config_manager n'est pas là
            embed = discord.Embed(title=title, description=description, color=0x5865F2)
            embed.set_footer(text=f"Demandé par {user.display_name}")
            return embed

    async def update_embed(self, interaction: discord.Interaction = None):
        # Déterminer le contexte (interaction ou message stocké)
        guild = interaction.guild if interaction else self.message.guild
        user = interaction.user if interaction else (self.message.interaction.user if self.message.interaction else self.message.author)

        title = "🖼️ Gestion des emojis"
        description = "Utilisez les boutons ci-dessous pour ajouter des emojis au serveur."
        
        # Création de l'embed de base
        embed = self.get_embed(guild, user, title, description)

        # Ajout des champs dynamiques (non gérés directement par le config_manager standard, on les ajoute après)
        if self.added_emojis:
            emojis_text = "\n".join([f"{str(emoji)} `:{emoji.name}:`" for emoji in self.added_emojis[-10:]])
            embed.add_field(
                name="📝 Emojis ajoutés récemment",
                value=emojis_text,
                inline=False
            )
        
        if interaction:
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.edit_original_response(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)

    @ui.button(label="Importer image", style=discord.ButtonStyle.primary, emoji="🖼️", custom_id="import_image")
    async def import_image(self, interaction: discord.Interaction, button: ui.Button):
        """Gère l'importation d'une ou plusieurs images pour en faire des emojis."""
        
        description = ("📤 **Envoyez une ou plusieurs images** pour les convertir en emojis.\n"
                       "Vous pouvez envoyer plusieurs images en un seul message.")
        
        embed = self.get_embed(interaction.guild, interaction.user, "Importation d'emojis", description)
        
        # On utilise followup car on veut un nouveau message, pas éditer le menu principal
        # On differ l'interaction bouton d'abord pour éviter le timeout visuel
        await interaction.response.defer()
        
        self.instruction_message = await interaction.followup.send(embed=embed, ephemeral=False)
        
        # Planifier la suppression du message d'instruction
        if self.instruction_message:
            asyncio.create_task(self.delete_after_delay(self.instruction_message, 15))      
        
        def check(m: discord.Message) -> bool:
            return (m.author.id == interaction.user.id 
                   and bool(m.attachments) 
                   and m.channel.id == interaction.channel_id)
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            added_emojis = []
            errors = []
            
            for attachment in msg.attachments[:10]:  # Limite à 10 images
                try:
                    if not any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                        errors.append(f"❌ `{attachment.filename}` : Format invalide.")
                        continue
                    
                    if attachment.size > 256 * 1024:  # 256KB
                        errors.append(f"❌ `{attachment.filename}` : Trop lourd (>256KB).")
                        continue
                    
                    # Nettoyage du nom
                    emoji_name = ''.join(c for c in attachment.filename.split('.')[0].lower().replace(' ', '_') 
                                        if c.isalnum() or c == '_')
                    if not emoji_name:
                        emoji_name = f"emoji_{len(self.added_emojis) + 1}"
                    
                    data = await attachment.read()
                    new_emoji = await interaction.guild.create_custom_emoji(
                        name=emoji_name[:32],
                        image=data,
                        reason=f"Ajouté par {interaction.user}"
                    )
                    
                    self.added_emojis.append(new_emoji)
                    added_emojis.append(new_emoji)
                    
                except Exception as e:
                    errors.append(f"❌ `{attachment.filename}` : {str(e)}")
            
            # Suppression du message utilisateur
            try:
                await msg.delete()
            except:
                pass
            
            # Mise à jour du menu principal
            await self.update_embed()
            
            # Rapport final
            if added_emojis:
                emoji_list = " ".join(str(e) for e in added_emojis)
                await interaction.followup.send(
                    f"✅ {len(added_emojis)} emoji(s) ajouté(s) : {emoji_list}",
                    ephemeral=True
                )
            
            if errors:
                error_msg = "\n".join(errors[:5])
                await interaction.followup.send(f"⚠️ Erreurs :\n{error_msg}", ephemeral=True)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Temps écoulé.", ephemeral=True)

    @ui.button(label="Copier emoji", style=discord.ButtonStyle.secondary, emoji="📋", custom_id="copy_emoji")
    async def copy_emoji(self, interaction: discord.Interaction, button: ui.Button):
        """Gère la copie d'emojis depuis d'autres serveurs."""
        
        description = ("📤 **Envoyez un ou plusieurs emojis personnalisés** à copier.\n"
                       "Vous pouvez envoyer plusieurs emojis en un seul message.")
        
        embed = self.get_embed(interaction.guild, interaction.user, "Copie d'emojis", description)

        await interaction.response.defer()
        self.instruction_message = await interaction.followup.send(embed=embed, ephemeral=False)
        
        if self.instruction_message:
            asyncio.create_task(self.delete_after_delay(self.instruction_message, 15))      
        
        def check(m: discord.Message) -> bool:
            return (m.author.id == interaction.user.id 
                   and m.channel.id == interaction.channel_id 
                   and bool(re.search(r'<a?:\w+:\d+>', m.content)))
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            emoji_matches = re.finditer(r'<(?P<animated>a?):(?P<name>\w+):(?P<id>\d+)>', msg.content)
            emoji_data = [(m.group('id'), m.group('animated') == 'a', m.group('name')) 
                          for m in emoji_matches]
            
            # Dédoublonnage et limite
            emoji_data = list(dict.fromkeys(emoji_data))[:10]
            
            if not emoji_data:
                try: await msg.delete() 
                except: pass
                return await interaction.followup.send("❌ Aucun emoji valide trouvé.", ephemeral=True)

            added = []
            errors = []
            
            for emoji_id, is_animated, emoji_name in emoji_data:
                try:
                    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if is_animated else 'png'}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status != 200:
                                errors.append(f"❌ `{emoji_name}` : Impossible de télécharger.")
                                continue
                            data = await response.read()
                            
                            # Tentative création
                            try:
                                new_emoji = await interaction.guild.create_custom_emoji(
                                    name=emoji_name[:32],
                                    image=data,
                                    reason=f"Copié par {interaction.user}"
                                )
                                self.added_emojis.append(new_emoji)
                                added.append(new_emoji)
                            except discord.HTTPException as e:
                                errors.append(f"❌ `{emoji_name}` : Erreur Discord ({e.status}).")

                except Exception as e:
                    errors.append(f"❌ `{emoji_name}` : Erreur inconnue.")
            
            try: await msg.delete()
            except: pass
            
            await self.update_embed()
            
            if added:
                emoji_list = " ".join(str(e) for e in added)
                await interaction.followup.send(f"✅ {len(added)} emoji(s) copié(s) : {emoji_list}", ephemeral=True)
            
            if errors:
                error_msg = "\n".join(errors[:5])
                await interaction.followup.send(f"⚠️ Erreurs :\n{error_msg}", ephemeral=True)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Temps écoulé.", ephemeral=True)


class EmojiCommand(commands.Cog):
    """Gestion des emojis du serveur avec une interface interactive."""

    def __init__(self, bot):
        self.bot = bot
        self.active_views: Dict[int, EmojiView] = {}
        self.cleanup_task = self.cleanup_old_views.start()
    
    def cog_unload(self):
        if self.cleanup_task:
            self.cleanup_task.cancel()
    
    @tasks.loop(minutes=5)
    async def cleanup_old_views(self):
        """Nettoie les vues inactives."""
        current_time = asyncio.get_event_loop().time()
        to_remove = []
        
        for user_id, view in self.active_views.items():
            if current_time - view.last_interaction > 1800:  # 30 minutes
                to_remove.append(user_id)
                if view.message:
                    try: await view.message.delete()
                    except: pass
        
        for user_id in to_remove:
            self.active_views.pop(user_id, None)

    @commands.hybrid_command(name="emoji", description="🖼️ Ouvre le menu de gestion des emojis")
    @commands.has_permissions(manage_emojis=True)
    @discord.app_commands.guild_only()
    async def emoji_command(self, ctx: commands.Context):
        """Ouvre un menu interactif pour ajouter des emojis au serveur."""
        
        # Vérification bot permission
        if not ctx.guild.me.guild_permissions.manage_emojis:
            return await ctx.send("❌ Je n'ai pas la permission `Gérer les emojis`.", ephemeral=True)

        # Nettoyage ancienne vue si existe
        if ctx.author.id in self.active_views:
            old_view = self.active_views[ctx.author.id]
            if old_view.message:
                try: await old_view.message.delete()
                except: pass

        view = EmojiView(self.bot, ctx.author.id)
        
        # Création de l'embed via Config Manager ou fallback
        title = "🖼️ Gestion des emojis"
        description = "Utilisez les boutons ci-dessous pour ajouter des emojis au serveur."
        
        if config_manager:
            embed = config_manager.get_formatted_embed(
                ctx.guild, ctx.author, self.bot,
                title, description, ctx.guild.id
            )
        else:
            embed = discord.Embed(title=title, description=description, color=0x5865F2)
            embed.set_footer(text=f"Demandé par {ctx.author.display_name}")

        # Envoi du message (compatible slash et prefix grâce à hybrid_command)
        message = await ctx.send(embed=embed, view=view)
        
        # Si c'est une interaction slash, ctx.send renvoie parfois une interaction ou un message selon le contexte
        # On s'assure de récupérer l'objet message réel
        if isinstance(message, discord.Interaction):
             view.message = await message.original_response()
        else:
             view.message = message

        self.active_views[ctx.author.id] = view

async def setup(bot):
    await bot.add_cog(EmojiCommand(bot))