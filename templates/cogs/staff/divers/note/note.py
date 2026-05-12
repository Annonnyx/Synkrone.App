import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
import math
import traceback

# ==========================================
# CONSTANTES ET CONFIGURATION
# ==========================================
NOTE_TIMEOUT = 600
NOTES_PER_PAGE = 10
NOTE_COLOR = discord.Color.blue()
DATA_DIR = "./data/note"

# Import dynamique du config_manager
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

def log(mode, message):
    """Système de logs simple selon le cahier des charges."""
    print(f"[NOTE] [{mode.upper()}] {message}")

# ==========================================
# GESTIONNAIRE DE DONNÉES (CRUD)
# ==========================================
class NoteManager:
    def __init__(self):
        # Initialisation silencieuse du NoteManager
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def _get_guild_dir(self, guild_id):
        guild_dir = os.path.join(DATA_DIR, str(guild_id))
        if not os.path.exists(guild_dir):
            os.makedirs(guild_dir)
        return guild_dir

    def get_file_path(self, guild_id, name):
        return os.path.join(self._get_guild_dir(guild_id), f"{name.lower()}.json")

    def create_note(self, guild_id, name, title, short_description, content, author_id):
        filepath = self.get_file_path(guild_id, name)
        if os.path.exists(filepath):
            return False
        
        now = datetime.now().isoformat()
        data = {
            "content": content[:2000],
            "title": title,
            "author_id": author_id,
            "created_at": now,
            "updated_at": now,
            "is_public": True,
            "short_description": short_description[:100],
            "markdown_enabled": False
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        log("crud", f"Note '{name}' créée pour la guilde {guild_id}")
        return True

    def get_note(self, guild_id, name):
        filepath = self.get_file_path(guild_id, name)
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def update_note(self, guild_id, name, data_updates):
        filepath = self.get_file_path(guild_id, name)
        if not os.path.exists(filepath):
            return False
        
        note_data = self.get_note(guild_id, name)
        note_data.update(data_updates)
        note_data["updated_at"] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(note_data, f, indent=4)
        log("crud", f"Note '{name}' mise à jour pour la guilde {guild_id}")
        return True

    def delete_note(self, guild_id, name):
        filepath = self.get_file_path(guild_id, name)
        if os.path.exists(filepath):
            os.remove(filepath)
            log("crud", f"Note '{name}' supprimée pour la guilde {guild_id}")
            return True
        return False

    def get_all_notes(self, guild_id):
        guild_dir = self._get_guild_dir(guild_id)
        notes = {}
        for filename in os.listdir(guild_dir):
            if filename.endswith('.json'):
                name = filename[:-5]
                notes[name] = self.get_note(guild_id, name)
        return notes

# ==========================================
# CLASSES DE BASE ET MODAUX
# ==========================================
class BaseNoteView(discord.ui.View):
    def __init__(self, cog_instance, author_id, timeout=NOTE_TIMEOUT):
        super().__init__(timeout=timeout)
        self.cog_instance = cog_instance
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser ce menu.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if hasattr(self, 'message') and self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    def create_note_embed(self, title, description, guild, user, bot):
        """Méthode centralisée pour générer l'embed avec fallback."""
        if HAS_CUSTOM_EMBED and config_manager and guild and user and bot:
            try:
                return config_manager.get_formatted_embed(
                    title=title,
                    description=description,
                    guild=guild,
                    user=user,
                    bot=bot,
                    target_id=guild.id if guild else None
                )
            except Exception as e:
                log("error", f"Erreur config_manager: {e}")
                
        # Fallback standard
        embed = discord.Embed(title=title, description=description, color=NOTE_COLOR)
        embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
        embed.set_footer(text="Système de Notes")
        return embed

class PageModal(discord.ui.Modal, title="Aller à la page"):
    page_number = discord.ui.TextInput(label="Numéro de page", style=discord.TextStyle.short, required=True)

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            page = int(self.page_number.value)
            if 1 <= page <= self.view.max_pages:
                self.view.current_page = page - 1
                await self.view.update_view(interaction)
            else:
                await interaction.response.send_message("Page invalide.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Veuillez entrer un nombre valide.", ephemeral=True)

class NoteModal(discord.ui.Modal):
    def __init__(self, view, mode="create", note_name=None, note_data=None):
        title_text = "Créer une Note" if mode == "create" else f"Modifier: {note_name}"
        super().__init__(title=title_text[:45])
        self.view = view
        self.mode = mode
        self.note_name = note_name

        # Champ pour le nom de la commande (toujours inclus)
        self.n_name = discord.ui.TextInput(
            label="Nom de la note (commande)", 
            max_length=20, 
            required=True,
            default=note_name if mode == "edit" else None
        )
        self.add_item(self.n_name)

        self.n_title = discord.ui.TextInput(label="Titre affiché", max_length=50, required=True, 
                                            default=note_data.get("title") if note_data else None)
        self.n_short = discord.ui.TextInput(label="Description courte", max_length=100, required=True, 
                                            default=note_data.get("short_description") if note_data else None)
        self.n_content = discord.ui.TextInput(label="Contenu", style=discord.TextStyle.paragraph, max_length=2000, required=True, 
                                              default=note_data.get("content") if note_data else None)
        
        self.add_item(self.n_title)
        self.add_item(self.n_short)
        self.add_item(self.n_content)

    async def on_submit(self, interaction: discord.Interaction):
        manager = self.view.cog_instance.note_manager
        guild_id = interaction.guild.id

        if self.mode == "create":
            name = self.n_name.value.lower().replace(" ", "_")
            success = manager.create_note(guild_id, name, self.n_title.value, self.n_short.value, self.n_content.value, interaction.user.id)
            if not success:
                return await interaction.response.send_message("❌ Une note avec ce nom existe déjà.", ephemeral=True)
        else:
            new_name = self.n_name.value.lower().replace(" ", "_")
            
            # Si le nom a changé, vérifier si le nouveau nom existe déjà
            if new_name != self.note_name:
                existing_note = manager.get_note(guild_id, new_name)
                if existing_note:
                    return await interaction.response.send_message("❌ Une note avec ce nom existe déjà.", ephemeral=True)
                
                # Renommer la note
                note_data = manager.get_note(guild_id, self.note_name)
                if note_data:
                    # Créer la nouvelle note avec le nouveau nom
                    success = manager.create_note(guild_id, new_name, self.n_title.value, self.n_short.value, self.n_content.value, note_data['author_id'])
                    
                    if success:
                        # Copier les autres propriétés
                        updates = {
                            "is_public": note_data.get('is_public', True),
                            "markdown_enabled": note_data.get('markdown_enabled', False),
                            "created_at": note_data['created_at']
                        }
                        manager.update_note(guild_id, new_name, updates)
                        
                        # Supprimer l'ancienne note
                        manager.delete_note(guild_id, self.note_name)
                        
                        # Mettre à jour le nom de la note dans la vue
                        if hasattr(self.view, 'note_name'):
                            self.view.note_name = new_name
                    else:
                        return await interaction.response.send_message("❌ Erreur lors du renommage.", ephemeral=True)
                else:
                    return await interaction.response.send_message("❌ Note introuvable.", ephemeral=True)
            else:
                # Mise à jour normale sans changement de nom
                updates = {
                    "title": self.n_title.value,
                    "short_description": self.n_short.value,
                    "content": self.n_content.value
                }
                manager.update_note(guild_id, self.note_name, updates)

        log("info", f"Note {self.mode}d par {interaction.user}")
        if hasattr(self.view, 'update_view'): # NoteView
            await self.view.update_view(interaction)
        elif hasattr(self.view, 'refresh_menu'): # EditNoteMenuView
            await self.view.refresh_menu(interaction)

# ==========================================
# VUES SPÉCIFIQUES (EDIT & CONFIRM)
# ==========================================
class ConfirmDeleteView(BaseNoteView):
    def __init__(self, cog_instance, author_id, note_name, parent_view):
        super().__init__(cog_instance, author_id)
        self.note_name = note_name
        self.parent_view = parent_view # EditNoteMenuView

    @discord.ui.button(label="Confirmer", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog_instance.note_manager.delete_note(interaction.guild.id, self.note_name)
        # Retour à la liste principale
        if hasattr(self.parent_view, 'parent_view'):
            await self.parent_view.parent_view.update_view(interaction)
        else:
            await interaction.response.send_message("Note supprimée.", ephemeral=True)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.refresh_menu(interaction)

class EditNoteMenuView(BaseNoteView):
    def __init__(self, cog_instance, author_id, note_name, parent_view):
        super().__init__(cog_instance, author_id)
        self.note_name = note_name
        self.parent_view = parent_view # NoteView

    async def refresh_menu(self, interaction: discord.Interaction):
        note_data = self.cog_instance.note_manager.get_note(interaction.guild.id, self.note_name)
        if not note_data:
            return await interaction.response.send_message("Note introuvable.", ephemeral=True)

        content_display = f"```{note_data['content']}```" if note_data['markdown_enabled'] else note_data['content']
        desc = (f"**📝 Nom de la commande:** `!note {self.note_name}`\n"
                f"**🏷️ Titre actuel:** {note_data.get('title', self.note_name)}\n"
                f"**🔐 Visibilité:** {'🌐 Public' if note_data['is_public'] else '🔒 Privé'}\n\n"
                f"**Description courte:**\n {note_data['short_description']}\n\n"
                f"**📄 Contenu:**\n{content_display}")

        embed = self.create_note_embed(f"🔧 {note_data.get('title', self.note_name)}", desc, interaction.guild, interaction.user, self.cog_instance.bot)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Modifier le contenu", style=discord.ButtonStyle.primary, emoji="✏️", row=0)
    async def edit_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"[DEBUG] Tentative de modification de la note: {self.note_name}")
        note_data = self.cog_instance.note_manager.get_note(interaction.guild.id, self.note_name)
        print(f"[DEBUG] Note trouvée: {note_data is not None}")
        if not note_data:
            return await interaction.response.send_message("❌ Note introuvable.", ephemeral=True)
        
        print(f"[DEBUG] Ouverture du modal de modification")
        await interaction.response.send_modal(NoteModal(self, mode="edit", note_name=self.note_name, note_data=note_data))

    @discord.ui.button(label="Markdown", style=discord.ButtonStyle.secondary, emoji="📄", row=0)
    async def toggle_markdown(self, interaction: discord.Interaction, button: discord.ui.Button):
        note_data = self.cog_instance.note_manager.get_note(interaction.guild.id, self.note_name)
        new_status = not note_data["markdown_enabled"]
        self.cog_instance.note_manager.update_note(interaction.guild.id, self.note_name, {"markdown_enabled": new_status})
        await self.refresh_menu(interaction)

    @discord.ui.button(label="Visibilité", style=discord.ButtonStyle.secondary, emoji="🔄", row=0)
    async def toggle_visibility(self, interaction: discord.Interaction, button: discord.ui.Button):
        note_data = self.cog_instance.note_manager.get_note(interaction.guild.id, self.note_name)
        new_status = not note_data["is_public"]
        self.cog_instance.note_manager.update_note(interaction.guild.id, self.note_name, {"is_public": new_status})
        await self.refresh_menu(interaction)

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def delete_note(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConfirmDeleteView(self.cog_instance, self.author_id, self.note_name, self)
        embed = self.create_note_embed("⚠️ Confirmation", f"Voulez-vous vraiment supprimer la note `{self.note_name}` ?", 
                                       interaction.guild, interaction.user, self.cog_instance.bot)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Retour", style=discord.ButtonStyle.success, emoji="◀", row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.update_view(interaction)

# ==========================================
# VUE PRINCIPALE (LISTE DES NOTES)
# ==========================================
class NoteSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Sélectionnez une note pour la modifier...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_note = self.values[0]
        print(f"[DEBUG] Note sélectionnée dans le sélecteur: {selected_note}")
        edit_view = EditNoteMenuView(self.view.cog_instance, self.view.author_id, selected_note, self.view)
        await edit_view.refresh_menu(interaction)

class NoteView(BaseNoteView):
    def __init__(self, cog_instance, author_id):
        super().__init__(cog_instance, author_id)
        self.current_page = 0
        self.notes_list = []
        self.max_pages = 1

    async def update_view(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        all_notes = self.cog_instance.note_manager.get_all_notes(guild_id)
        sorted_keys = sorted(all_notes.keys())
        
        self.max_pages = math.ceil(len(sorted_keys) / NOTES_PER_PAGE) or 1
        self.current_page = max(0, min(self.current_page, self.max_pages - 1))
        
        start = self.current_page * NOTES_PER_PAGE
        end = start + NOTES_PER_PAGE
        page_keys = sorted_keys[start:end]

        # Construction du contenu de l'embed
        desc = ("📝 **Gestion des Notes**\n"
                "**Pourquoi créer une note ?**\n"
                "Ce système te permet de sauvegarder des textes réutilisables.\n"
                "**Exemples d'utilisation**\n"
                "• `!note recrutement`\n"
                "• `!note produit`\n"
                "**Notes existantes**\n")

        if not sorted_keys:
            desc += "*Aucune note créée pour le moment.*"
        else:
            for i, key in enumerate(page_keys, start=start + 1):
                note = all_notes[key]
                icon = "🌐" if note.get("is_public", True) else "🔒"
                desc += f"{i}. {icon} `!note {key}` - {note.get('short_description', 'Pas de description')}\n"

        embed = self.create_note_embed("Système de Notes", desc, interaction.guild, interaction.user, self.cog_instance.bot)
        
        # Mise à jour des composants
        self.clear_items()
        
        # Sélecteur (max 25 notes par page selon Discord)
        if page_keys:
            options = [
                discord.SelectOption(
                    label=f"{i+1}. {k}", 
                    description=all_notes[k].get('short_description', '')[:100],
                    emoji="📄",
                    value=k  # Valeur réelle sans numérotation
                ) for i, k in enumerate(page_keys, start=start + 1)
            ]
            self.add_item(NoteSelect(options))

        # Boutons de navigation
        self.add_item(NavigationButton(emoji="◀", style=discord.ButtonStyle.gray, custom_id="prev", row=2))
        self.add_item(discord.ui.Button(label=f"Page {self.current_page + 1}/{self.max_pages}", disabled=True, row=2))
        self.add_item(NavigationButton(emoji="▶", style=discord.ButtonStyle.gray, custom_id="next", row=2))
        self.add_item(NavigationButton(emoji="➕", label="Ajouter", style=discord.ButtonStyle.success, custom_id="add", row=2))

        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

class NavigationButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        view: NoteView = self.view
        if self.custom_id == "prev":
            view.current_page = (view.current_page - 1) % view.max_pages
        elif self.custom_id == "next":
            view.current_page = (view.current_page + 1) % view.max_pages
        elif self.custom_id == "add":
            return await interaction.response.send_modal(NoteModal(view, mode="create"))
        
        await view.update_view(interaction)

# ==========================================
# COG PRINCIPAL
# ==========================================
class Note(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.note_manager = NoteManager()

    @commands.hybrid_command(name="note", with_app_command=True)
    @commands.has_permissions(administrator=True)
    @app_commands.describe(name="Nom de la note à afficher (optionnel)")
    async def note_cmd(self, ctx: commands.Context, name: str = None):
        """Affiche la liste des notes ou une note spécifique."""
        if name is None:
            # Mode Liste (Menu principal)
            view = NoteView(self, ctx.author.id)
            # Initialisation manuelle pour le premier message
            all_notes = self.note_manager.get_all_notes(ctx.guild.id)
            sorted_keys = sorted(all_notes.keys())
            
            view.max_pages = math.ceil(len(sorted_keys) / NOTES_PER_PAGE) or 1
            view.current_page = 0
            
            start = view.current_page * NOTES_PER_PAGE
            end = start + NOTES_PER_PAGE
            page_keys = sorted_keys[start:end]

            start = view.current_page * NOTES_PER_PAGE
            end = start + NOTES_PER_PAGE
            page_keys = sorted_keys[start:end]

            # Construction du contenu de l'embed
            desc = (" 💡 **Pourquoi créer une note ?**\n"
                    " Ce système te permet de sauvegarder des textes réutilisables.\n"
                    " 🎯 **Exemples d'utilisation**\n"
                    "    • `!note recrutement`\n"
                    "    • `!note pub`\n"
                    " 📋 **Notes existantes**\n")

            if not sorted_keys:
                desc += "     *Aucune note créée pour le moment.*"
            else:
                for i, key in enumerate(page_keys, start=start + 1):
                    note = all_notes[key]
                    icon = "🌐" if note.get("is_public", True) else "🔒"
                    desc += f"     {i}. {icon} `!note {key}` - {note.get('short_description', 'Pas de description')}\n"

            embed = view.create_note_embed("Système de Notes", desc, ctx.guild, ctx.author, self.bot)
            
            # Mise à jour des composants
            view.clear_items()
            
            # Sélecteur (max 25 notes par page selon Discord)
            if page_keys:
                options = [
                    discord.SelectOption(
                        label=f"{i+1}. {k}", 
                        description=all_notes[k].get('short_description', '')[:100],
                        emoji="📄",
                        value=k  # Valeur réelle sans numérotation
                    ) for i, k in enumerate(page_keys, start=start + 1)
                ]
                view.add_item(NoteSelect(options))

            # Boutons de navigation
            view.add_item(NavigationButton(emoji="◀", style=discord.ButtonStyle.gray, custom_id="prev", row=2))
            view.add_item(discord.ui.Button(label=f"Page {view.current_page + 1}/{view.max_pages}", disabled=True, row=2))
            view.add_item(NavigationButton(emoji="▶", style=discord.ButtonStyle.gray, custom_id="next", row=2))
            view.add_item(NavigationButton(emoji="➕", label="Ajouter", style=discord.ButtonStyle.success, custom_id="add", row=2))

            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        # Mode Affichage d'une note spécifique
        note_data = self.note_manager.get_note(ctx.guild.id, name)
        if not note_data:
            return await ctx.send(f"❌ La note `{name}` n'existe pas.")

        # Vérification visibilité
        if not note_data["is_public"] and not ctx.author.guild_permissions.administrator:
            return await ctx.send("🔒 Cette note est privée.")

        content = note_data["content"]
        # Optionnel: formatage markdown simple si activé
        if note_data.get("markdown_enabled"):
            content = f"```md\n{content}\n```"

        # Timestamps Discord
        created_dt = datetime.fromisoformat(note_data["created_at"])

        # Créer l'embed directement
        desc = (f"**👤 Auteur:** <@{note_data['author_id']}>\n"
                f"**🔐 Visibilité:** {'🌐 Public' if note_data['is_public'] else '🔒 Privé'}\n"
                f"**📅 Créée le:** <t:{int(created_dt.timestamp())}:F>\n\n"
                f"**📄 Contenu:**\n{content}")

        # Créer une vue temporaire pour utiliser create_note_embed
        temp_view = BaseNoteView(self, ctx.author.id)
        embed = temp_view.create_note_embed(note_data["title"], desc, ctx.guild, ctx.author, self.bot)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Note(bot))
