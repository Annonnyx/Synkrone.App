import os
import json
from pathlib import Path

import discord
from discord.ext import commands
from discord.ui import View, Select, Modal, TextInput, Button


# --- FONCTIONS UTILITAIRES (JSON & Embed) ---

def get_file_path(guild_id: int) -> Path:
    """Récupère ou crée le chemin vers le fichier lvl.json du serveur."""
    # Correction : pointer vers le dossier data/pack/statistiques/ à la racine du projet
    base_path = Path(__file__).resolve().parents[4] / "data" / "pack" / "statistiques" / str(guild_id)
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path / "lvl.json"

def read_levels(guild_id: int) -> list:
    """Lit et retourne les données des niveaux."""
    file_path = get_file_path(guild_id)
    if file_path.exists():
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def write_levels(guild_id: int, data: list):
    """Sauvegarde les données en les triant par niveau."""
    # Trie automatiquement par niveau (ordre croissant)
    data.sort(key=lambda x: int(x.get("niveau", 0)) if str(x.get("niveau", "")).isdigit() else 9999)
    with open(get_file_path(guild_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_level_menu(guild) -> discord.Embed:
    """Génère l'embed mis à jour avec les configurations actuelles."""
    guild_id = guild.id
    data = read_levels(guild_id)
    config_lines = []
    if data:
        for idx, palier in enumerate(data, 1):
            niveau = palier.get("niveau", "?")
            role_id = palier.get("role_id", "")
            titre = palier.get("titre", "")
            parts = [f"# {idx}", f"Niv. {niveau}"]
            if role_id:
                parts.append(f"<@&{role_id}>")
            if titre:
                parts.append(f"`{titre}`")
            config_lines.append(" - ".join(parts))
    else:
        config_lines.append("Aucune configuration enregistrée.")

    embed = discord.Embed(
        title=f"⚙️ Paliers de niveaux de {guild.name}",
        description="Voici la liste des paliers de niveau configurés sur le serveur.",
        color=0x000000
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    value_text = "\n".join(config_lines)
    if len(value_text) > 1024:
        value_text = value_text[:1020] + "..."

    embed.add_field(
        name="Configurations existantes",
        value=value_text,
        inline=False
    )
    return embed


# --- 1. MODALS ET VUES INTERMÉDIAIRES ---

class AddEditLevelModal(Modal):
    """Modal commun pour Ajouter ou Modifier un niveau."""
    def __init__(self, original_message, mode="add", default_niveau="", default_role="", default_titre=""):
        title = "Ajouter un palier" if mode == "add" else f"Modifier le palier {default_niveau}"
        super().__init__(title=title)
        
        self.original_message = original_message
        self.mode = mode
        self.old_niveau = default_niveau

        self.niveau = TextInput(
            label="Niveau",
            placeholder="Ex: 10",
            default=default_niveau,
            style=discord.TextStyle.short,
            required=True,
            max_length=4
        )
        self.role_id = TextInput(
            label="ID du rôle",
            placeholder="Ex: 123456789101112131",
            default=default_role,
            style=discord.TextStyle.short,
            required=False,
            max_length=20
        )
        self.titre = TextInput(
            label="Titre",
            placeholder="Ex: Membre Vétéran",
            default=default_titre,
            style=discord.TextStyle.short,
            required=False,
            max_length=16 # Limité à 16 caractères comme demandé
        )

        self.add_item(self.niveau)
        self.add_item(self.role_id)
        self.add_item(self.titre)

    async def on_submit(self, interaction: discord.Interaction):
        titre_val = self.titre.value.strip()
        role_val = self.role_id.value.strip()
        niveau_val = self.niveau.value.strip()

        if not titre_val and not role_val:
            await interaction.response.send_message("❌ Merci de renseigner au moins un titre ou un rôle.", ephemeral=True)
            return

        guild = interaction.guild
        guild_id = guild.id
        data = read_levels(guild_id)

        if self.mode == "add":
            if any(str(p.get("niveau")) == niveau_val for p in data):
                await interaction.response.send_message("❌ Ce niveau existe déjà ! Choisis 'Modifier' dans le menu.", ephemeral=True)
                return
            data.append({"niveau": niveau_val, "role_id": role_val, "titre": titre_val})
            msg = f"✅ Palier **Niveau {niveau_val}** ajouté avec succès !"
            
        elif self.mode == "edit":
            found = False
            for p in data:
                if str(p.get("niveau")) == self.old_niveau:
                    p["niveau"] = niveau_val 
                    p["role_id"] = role_val
                    p["titre"] = titre_val
                    found = True
                    break
            if not found:
                data.append({"niveau": niveau_val, "role_id": role_val, "titre": titre_val})
            msg = f"✅ Palier **Niveau {niveau_val}** modifié avec succès !"

        # Sauvegarder & Mettre à jour l'embed ET restaurer la vue (Select) verrouillée sur l'auteur
        write_levels(guild_id, data)
        await self.original_message.edit(embed=generate_level_menu(guild), view=LevelMenuView(interaction.user.id))
        await interaction.response.send_message(msg, ephemeral=True)


class EditChoiceView(View):
    """Vue intermédiaire générée après avoir cherché un niveau à modifier."""
    def __init__(self, original_message, niveau, palier, menu_embed, author_id):
        super().__init__(timeout=None)
        self.original_message = original_message
        self.niveau = niveau
        self.palier = palier
        self.menu_embed = menu_embed
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Vérifie que seul l'auteur de la commande peut utiliser les boutons."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Seule la personne qui a exécuté la commande peut utiliser ces boutons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Modifier ce palier", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_button(self, interaction: discord.Interaction, button: Button):
        modal = AddEditLevelModal(
            original_message=self.original_message,
            mode="edit",
            default_niveau=str(self.palier.get("niveau", "")),
            default_role=str(self.palier.get("role_id", "")),
            default_titre=str(self.palier.get("titre", ""))
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Retour", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(embed=self.menu_embed, view=LevelMenuView(self.author_id))


class AskEditLevelModal(Modal, title="Modifier un palier"):
    """Modal étape 1 : Demande quel niveau l'utilisateur souhaite modifier."""
    niveau = TextInput(
        label="Quel niveau voulez-vous modifier ?", 
        placeholder="Ex: 10", 
        required=True
    )

    def __init__(self, original_message):
        super().__init__()
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id = guild.id
        data = read_levels(guild_id)
        niveau_recherche = self.niveau.value.strip()

        palier = next((p for p in data if str(p.get("niveau")) == niveau_recherche), None)
        if not palier:
            await interaction.response.send_message(f"❌ Le niveau `{niveau_recherche}` n'existe pas.", ephemeral=True)
            return

        menu_embed = generate_level_menu(guild)
        view = EditChoiceView(self.original_message, niveau_recherche, palier, menu_embed, interaction.user.id)
        await interaction.response.edit_message(embed=menu_embed, view=view)


class DeleteLevelModal(Modal, title="Supprimer un palier"):
    """Modal pour supprimer une ligne."""
    niveau = TextInput(
        label="Quel niveau voulez-vous supprimer ?", 
        placeholder="Ex: 10", 
        required=True
    )

    def __init__(self, original_message):
        super().__init__()
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id = guild.id
        data = read_levels(guild_id)
        niveau_val = self.niveau.value.strip()

        new_data = [p for p in data if str(p.get("niveau")) != niveau_val]

        if len(data) == len(new_data):
            await interaction.response.send_message(f"❌ Aucun palier trouvé pour le niveau `{niveau_val}`.", ephemeral=True)
            return

        write_levels(guild_id, new_data)
        await self.original_message.edit(embed=generate_level_menu(guild), view=LevelMenuView(interaction.user.id))
        await interaction.response.send_message(f"🗑️ Le palier de niveau `{niveau_val}` a été supprimé.", ephemeral=True)


# --- 2. VUE PRINCIPALE ET SELECT ---

class LevelSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Ajouter", description="Ajouter un nouveau palier", emoji="➕", value="add"),
            discord.SelectOption(label="Modifier", description="Modifier un palier existant", emoji="✏️", value="edit"),
            discord.SelectOption(label="Supprimer", description="Supprimer un palier", emoji="❌", value="delete"),
        ]
        super().__init__(placeholder="Que souhaitez-vous faire ?", options=options)

    async def callback(self, interaction: discord.Interaction):
        choix = self.values[0]
        
        if choix == "add":
            await interaction.response.send_modal(AddEditLevelModal(original_message=interaction.message, mode="add"))
        elif choix == "edit":
            await interaction.response.send_modal(AskEditLevelModal(original_message=interaction.message))
        elif choix == "delete":
            await interaction.response.send_modal(DeleteLevelModal(original_message=interaction.message))


class LevelMenuView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.add_item(LevelSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Vérifie que seul l'auteur de la commande peut utiliser le menu déroulant."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Seule la personne qui a exécuté la commande peut utiliser ce menu.", ephemeral=True)
            return False
        return True


# --- 3. COMMANDE ET COG ---

class LevelSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="lvl", description="Affiche ou gère la configuration des niveaux.")
    async def lvl_menu(self, ctx: commands.Context):
        guild = ctx.guild
        if not guild:
            await ctx.send("Cette commande doit être exécutée sur un serveur.")
            return

        embed = generate_level_menu(guild)
        # Vérifie si l'utilisateur possède la permission Administrateur
        if ctx.author.guild_permissions.administrator:
            view = LevelMenuView(ctx.author.id)
            await ctx.send(embed=embed, view=view)
        else:
            # S'il n'est pas admin, il voit juste l'embed sans le menu de sélection
            await ctx.send(embed=embed)


# --- CHARGEMENT DU COG ---

async def setup(bot):
    await bot.add_cog(LevelSettings(bot))