import discord
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput
import traceback
import asyncio

# ==============================================================================
# GESTION DES IMPORTS ET DU CONFIG_MANAGER
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# FONCTIONS UTILITAIRES (RECHERCHE INTELLIGENTE)
# ==============================================================================

async def find_message_in_guild(guild, message_id):
    """Cherche un message par son ID dans tous les salons textuels du serveur."""
    for channel in guild.text_channels:
        # On ignore les salons où le bot ne peut pas lire l'historique pour gagner du temps
        if not channel.permissions_for(guild.me).read_message_history:
            continue
        try:
            return await channel.fetch_message(message_id)
        except:
            continue
    return None

# ==============================================================================
# MODALS (FORMULAIRES)
# ==============================================================================

class CopyEmbedModal(Modal, title="Copier un embed existant"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.message_id = TextInput(label="ID du Message", placeholder="Collez juste l'ID du message...", required=True)
        self.add_item(self.message_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer() # Traitement potentiellement long
        
        msg = await find_message_in_guild(interaction.guild, int(self.message_id.value))
        if not msg or not msg.embeds:
            return await interaction.followup.send("❌ Message introuvable ou sans embed.", delete_after=20)
        
        # Extraction des données
        source = msg.embeds[0]
        title = source.title or " "
        desc = source.description or " "
        
        # Reconstruction via config_manager pour garder le style du bot
        if config_manager:
            new_embed = config_manager.get_formatted_embed(
                interaction.guild, interaction.user, self.parent_view.bot,
                title, desc, interaction.guild.id
            )
        else:
            new_embed = discord.Embed(title=title, description=desc, color=source.color)

        # Récupération des images sources
        if source.image: new_embed.set_image(url=source.image.url)
        if source.thumbnail: new_embed.set_thumbnail(url=source.thumbnail.url)
        
        self.parent_view.embed_preview = new_embed
        await self.parent_view.preview_msg.edit(embed=self.parent_view.embed_preview)
        
        # Passage direct à l'étape 2
        await self.parent_view.show_step_2(interaction)


class TextEditModal(Modal, title="Modifier le texte"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.title_input = TextInput(
            label="Titre", 
            default=str(self.parent_view.embed_preview.title or ""), 
            required=False, max_length=256
        )
        self.desc_input = TextInput(
            label="Description", 
            style=discord.TextStyle.paragraph, 
            default=str(self.parent_view.embed_preview.description or ""), 
            required=False, max_length=4000
        )
        self.add_item(self.title_input)
        self.add_item(self.desc_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Mise à jour via config_manager
        if config_manager:
            new_e = config_manager.get_formatted_embed(
                interaction.guild, interaction.user, self.parent_view.bot, 
                self.title_input.value or " ", self.desc_input.value or " ", 
                interaction.guild.id
            )
            # On remet les images qui étaient présentes
            if self.parent_view.embed_preview.image: 
                new_e.set_image(url=self.parent_view.embed_preview.image.url)
            if self.parent_view.embed_preview.thumbnail: 
                new_e.set_thumbnail(url=self.parent_view.embed_preview.thumbnail.url)
            self.parent_view.embed_preview = new_e
        else:
            self.parent_view.embed_preview.title = self.title_input.value
            self.parent_view.embed_preview.description = self.desc_input.value
        
        await self.parent_view.preview_msg.edit(embed=self.parent_view.embed_preview)
        await interaction.response.send_message("✅ Texte mis à jour !", delete_after=20)


class ImageLinkModal(Modal):
    def __init__(self, parent_view, type_image):
        super().__init__(title=f"Lien pour {type_image}")
        self.parent_view = parent_view
        self.type_image = type_image # "l'Image" ou "la Miniature"
        self.url_input = TextInput(label="Lien URL (http...)", placeholder="https://i.imgur.com/...", required=True)
        self.add_item(self.url_input)

    async def on_submit(self, interaction: discord.Interaction):
        url = self.url_input.value
        try:
            if "Miniature" in self.type_image:
                self.parent_view.embed_preview.set_thumbnail(url=url)
            else:
                self.parent_view.embed_preview.set_image(url=url)
            
            await self.parent_view.preview_msg.edit(embed=self.parent_view.embed_preview)
            # Retour au menu visuel pour voir les changements
            await self.parent_view.show_step_2_bis(interaction)
        except:
            await interaction.response.send_message("❌ Lien invalide.", delete_after=20)


class SendChannelModal(Modal, title="Envoyer dans un salon"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.channel_id = TextInput(label="ID du Salon", placeholder="Ex: 123456789...", required=True)
        self.add_item(self.channel_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel = interaction.guild.get_channel(int(self.channel_id.value))
            await channel.send(embed=self.parent_view.embed_preview)
            await interaction.response.send_message(f"🚀 Embed publié dans {channel.mention} !", delete_after=20)
        except:
            await interaction.response.send_message("❌ ID invalide ou permissions manquantes.", delete_after=20)


class EditMessageModal(Modal, title="Modifier un message existant"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.message_id = TextInput(label="ID du Message", placeholder="Le message doit être de moi...", required=True)
        self.add_item(self.message_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        msg = await find_message_in_guild(interaction.guild, int(self.message_id.value))
        
        if not msg:
            return await interaction.followup.send("❌ Message introuvable sur ce serveur.", delete_after=20)
        if msg.author.id != self.parent_view.bot.user.id:
            return await interaction.followup.send("❌ Je ne peux modifier que mes propres messages.", delete_after=20)
        
        await msg.edit(embed=self.parent_view.embed_preview)
        await interaction.followup.send("✅ Message mis à jour avec succès !", delete_after=20)


# ==============================================================================
# VUE PRINCIPALE (CONTROLEUR)
# ==============================================================================

class ConfigView(View):
    def __init__(self, embed_config, embed_preview, bot):
        super().__init__(timeout=None)
        self.embed_config = embed_config
        self.embed_preview = embed_preview
        self.bot = bot
        self.preview_msg = None
        self.create_step_1()

    # --- Gestionnaire de style pour l'embed de config ---
    def update_config_embed(self, interaction, title, desc):
        """Met à jour l'embed de configuration (celui du haut) en gardant le style."""
        if config_manager:
            self.embed_config = config_manager.get_formatted_embed(
                interaction.guild, interaction.user, self.bot, 
                title, desc, interaction.guild.id
            )
        else:
            self.embed_config.title = title
            self.embed_config.description = desc

    # ==========================================================================
    # ETAPE 1 : DEPART
    # ==========================================================================
    def create_step_1(self):
        self.clear_items()
        select = Select(
            placeholder="Étape 1 : Comment voulez-vous commencer ?", 
            options=[
                discord.SelectOption(label="Nouvel embed vierge", emoji="✨", value="new", description="Partir de zéro"),
                discord.SelectOption(label="Copier un embed existant", emoji="📋", value="copy", description="Importer depuis un ID")
            ]
        )
        
        async def callback(i):
            if select.values[0] == "new": 
                await self.show_step_2(i)
            else: 
                await i.response.send_modal(CopyEmbedModal(self))
        
        select.callback = callback
        self.add_item(select)

    # ==========================================================================
    # ETAPE 2 : MENU PRINCIPAL (TEXTE / CHOIX IMAGE)
    # ==========================================================================
    async def show_step_2(self, interaction: discord.Interaction):
        # Mise à jour titre/desc
        self.update_config_embed(interaction, "Étape 2 : Personnalisation", "Modifiez le contenu textuel ou accédez au menu des images.")
        self.clear_items()

        # Boutons
        btn_back = Button(label="Retour", style=discord.ButtonStyle.red, emoji="⬅️")
        btn_text = Button(label="Texte", style=discord.ButtonStyle.blurple, emoji="📝")
        btn_img_menu = Button(label="Images & Miniatures", style=discord.ButtonStyle.gray, emoji="🖼️")
        btn_next = Button(label="Continuer", style=discord.ButtonStyle.green, emoji="➡️")

        # Callbacks
        btn_back.callback = self.back_confirm_logic
        btn_text.callback = lambda i: i.response.send_modal(TextEditModal(self))
        btn_img_menu.callback = self.show_step_2_bis
        btn_next.callback = self.show_step_3

        self.add_item(btn_back)
        self.add_item(btn_text)
        self.add_item(btn_img_menu)
        self.add_item(btn_next)

        if interaction.response.is_done():
            await interaction.edit_original_response(embed=self.embed_config, view=self)
        else:
            await interaction.response.edit_message(embed=self.embed_config, view=self)

    # ==========================================================================
    # ETAPE 2.5 : GESTION AVANCEE DES IMAGES
    # ==========================================================================
    async def show_step_2_bis(self, interaction: discord.Interaction):
        self.update_config_embed(interaction, "Étape 2.5 : Gestion Visuelle", "Ajoutez, remplacez ou supprimez vos visuels.")
        self.clear_items()

        # 1. Bouton Retour (Toujours à gauche)
        btn_back = Button(label="Retour", style=discord.ButtonStyle.red, emoji="⬅️")
        btn_back.callback = self.show_step_2
        self.add_item(btn_back)

        # 2. Menu déroulant d'ajout
        select_add = Select(placeholder="Ajouter ou Modifier un visuel...", options=[
            discord.SelectOption(label="Image : Via Lien", emoji="🔗", value="img_link"),
            discord.SelectOption(label="Image : Via Envoi (Upload)", emoji="📤", value="img_upload"),
            discord.SelectOption(label="Miniature : Via Lien", emoji="🔗", value="thumb_link"),
            discord.SelectOption(label="Miniature : Via Envoi (Upload)", emoji="📤", value="thumb_upload"),
        ])

        async def add_callback(i):
            val = select_add.values[0]
            
            # Cas 1 : Lien URL (Modal)
            if "link" in val:
                type_str = "la Miniature" if "thumb" in val else "l'Image"
                await i.response.send_modal(ImageLinkModal(self, type_str))
            
            # Cas 2 : Upload (Attente de message)
            else:
                instruction = await i.channel.send(f"📂 {i.user.mention}, envoyez votre image/gif dans ce salon maintenant (30s max).")
                await i.response.defer() # Important pour ne pas crash l'interaction

                def check(m): 
                    return m.author == i.user and m.channel == i.channel and m.attachments

                try:
                    msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                    url = msg.attachments[0].url
                    
                    if "img" in val: self.embed_preview.set_image(url=url)
                    else: self.embed_preview.set_thumbnail(url=url)
                    
                    await self.preview_msg.edit(embed=self.embed_preview)
                    
                    # Nettoyage
                    await msg.delete()
                    await instruction.delete()
                    
                    # Rechargement de la vue pour afficher les boutons supprimer
                    await self.show_step_2_bis(i) # 'i' est déjà répondu, on utilisera edit_original_response via la méthode
                    
                except asyncio.TimeoutError:
                    await instruction.edit(content="❌ Temps écoulé, annulation.", delete_after=5)

        select_add.callback = add_callback
        self.add_item(select_add)

        # 3. Boutons "Retirer" (Conditionnels)
        # On vérifie si l'URL existe pour afficher le bouton
        if self.embed_preview.image and self.embed_preview.image.url:
            btn_rm_img = Button(label="Retirer Image", style=discord.ButtonStyle.danger, emoji="🗑️")
            async def rm_img_cb(i):
                self.embed_preview.set_image(url=None)
                await self.preview_msg.edit(embed=self.embed_preview)
                await i.response.send_message("✅ Image retirée.", delete_after=20)
                await self.show_step_2_bis(i)
            btn_rm_img.callback = rm_img_cb
            self.add_item(btn_rm_img)

        if self.embed_preview.thumbnail and self.embed_preview.thumbnail.url:
            btn_rm_thumb = Button(label="Retirer Miniature", style=discord.ButtonStyle.danger, emoji="🗑️")
            async def rm_thumb_cb(i):
                self.embed_preview.set_thumbnail(url=None)
                await self.preview_msg.edit(embed=self.embed_preview)
                await i.response.send_message("✅ Miniature retirée.", delete_after=20)
                await self.show_step_2_bis(i)
            btn_rm_thumb.callback = rm_thumb_cb
            self.add_item(btn_rm_thumb)

        # Affichage
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=self.embed_config, view=self)
        else:
            await interaction.response.edit_message(embed=self.embed_config, view=self)

    # ==========================================================================
    # ETAPE 3 : PUBLICATION
    # ==========================================================================
    async def show_step_3(self, interaction: discord.Interaction):
        self.update_config_embed(interaction, "Étape 3 : Publication", "Votre embed est prêt. Choisissez comment le diffuser.")
        self.clear_items()

        btn_back = Button(label="Retour", style=discord.ButtonStyle.red, emoji="⬅️")
        btn_back.callback = self.show_step_2
        self.add_item(btn_back)

        select_pub = Select(placeholder="Choisir le mode d'envoi...", options=[
            discord.SelectOption(label="Envoyer dans un salon", emoji="📤", value="send"),
            discord.SelectOption(label="Modifier un message existant", emoji="🔄", value="edit")
        ])

        async def pub_cb(i):
            if select_pub.values[0] == "send":
                await i.response.send_modal(SendChannelModal(self))
            else:
                await i.response.send_modal(EditMessageModal(self))
        
        select_pub.callback = pub_cb
        self.add_item(select_pub)

        await interaction.response.edit_message(embed=self.embed_config, view=self)

    # ==========================================================================
    # LOGIQUE DE RETOUR ET CONFIRMATION
    # ==========================================================================
    async def back_confirm_logic(self, i):
        self.update_config_embed(i, "⚠️ Confirmation requise", "Voulez-vous vraiment revenir au début ?\nToute modification non sauvegardée sera perdue.")
        self.clear_items()
        
        btn_yes = Button(label="Oui, recommencer", style=discord.ButtonStyle.danger)
        btn_no = Button(label="Non, annuler", style=discord.ButtonStyle.gray)

        async def yes_cb(i2):
            self.create_step_1()
            # On réinitialise le texte de config pour l'étape 1
            self.update_config_embed(i2, "Étape 1 : Configuration", "Bienvenue. Sélectionnez une option pour commencer.")
            await i2.response.edit_message(embed=self.embed_config, view=self)

        btn_yes.callback = yes_cb
        btn_no.callback = self.show_step_2
        
        self.add_item(btn_yes)
        self.add_item(btn_no)
        
        await i.response.edit_message(embed=self.embed_config, view=self)


# ==============================================================================
# COG PRINCIPAL
# ==============================================================================

class Test(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="embed", description="Lance l'éditeur d'embed complet.")
    async def test(self, ctx: commands.Context):
        # Suppression du message de commande original pour propreté (si possible)
        try: await ctx.message.delete()
        except: pass

        # Textes initiaux
        t_cfg, d_cfg = "Étape 1 : Configuration", "Bienvenue dans l'éditeur d'embed.\nSélectionnez une option ci-dessous."
        t_pre = "📢 Titre de l'Annonce (Aperçu)"
        d_pre = (
            "Ceci est un texte de remplacement pour visualiser la mise en page.\n"
            "Modifiez ce contenu à l'**Étape 2**.\n\n"
            "• Vous pouvez ajouter des images\n"
            "• Vous pouvez modifier le titre\n"
            "• Le design s'adapte à votre serveur"
        )
        
        # Création des embeds initiaux via Config Manager
        if config_manager:
            e_config = config_manager.get_formatted_embed(ctx.guild, ctx.author, self.bot, t_cfg, d_cfg, ctx.guild.id)
            e_preview = config_manager.get_formatted_embed(ctx.guild, ctx.author, self.bot, t_pre, d_pre, ctx.guild.id)
        else:
            e_config = discord.Embed(title=t_cfg, description=d_cfg, color=0x5865F2)
            e_preview = discord.Embed(title=t_pre, description=d_pre, color=0x2ecc71)

        # Lancement de la Vue
        view = ConfigView(e_config, e_preview, self.bot)
        
        # Envoi des messages (NON EPHEMERES)
        # Message de config (avec boutons)
        msg_config = await ctx.send(embed=e_config, view=view)
        # Message d'aperçu (juste en dessous)
        view.preview_msg = await ctx.send(embed=e_preview)

async def setup(bot: commands.Bot):
    await bot.add_cog(Test(bot))