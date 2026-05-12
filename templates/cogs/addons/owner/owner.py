import os
import json
from pathlib import Path
from datetime import datetime

import discord
from discord import app_commands, ui
from discord.ext import commands

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ID du Créateur
_creator_env = os.getenv("CREATED_BY")
if _creator_env is None or not _creator_env.isdigit():
    now = datetime.now().strftime("[%d/%m/%y] %H:%M:%S")
    print(f"\033[91m{now} [OWNER] [ERREUR] La variable d'environnement CREATED_BY n'est pas définie ou invalide. Utilisation de 0 par défaut.\033[0m")
    CREATOR_ID = 0
else:
    CREATOR_ID = int(_creator_env)

# --- UTILITAIRES DE PERSISTANCE ---

def _json_path() -> Path:
    # Place le fichier owner.json dans le dossier data/addons/owner à la racine du projet
    base_dir = Path.cwd()
    owner_dir = base_dir / "data" / "addons" / "data_owner"
    return owner_dir / "owner.json"

def ensure_owner_file_exists():
    """Initialise le fichier owner.json et les dossiers si nécessaires."""
    p = _json_path()
    data_dir = p.parents[2]
    addons_dir = p.parents[1]
    owner_dir = p.parent
    
    for d in [data_dir, addons_dir, owner_dir]:
        d.mkdir(parents=True, exist_ok=True)
        
    if not p.exists():
        with p.open("w", encoding="utf-8") as f:
            json.dump([CREATOR_ID], f, ensure_ascii=False, indent=2)
    else:
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            changed = False
            
            if 0 in data and CREATOR_ID != 0:
                data = [CREATOR_ID if x == 0 else x for x in data]
                changed = True
                
            if CREATOR_ID not in data:
                data.insert(0, CREATOR_ID)
                changed = True
                
            if changed:
                with p.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            now = datetime.now().strftime("[%d/%m/%y] %H:%M:%S")
            print(f"\033[91m{now} [OWNER] [ERREUR] Impossible de mettre à jour owner.json : {e}\033[0m")

def load_allowed() -> list[int]:
    p = _json_path()
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [int(x) for x in data][:9]
    except Exception:
        return []

def save_allowed(ids: list[int]) -> None:
    p = _json_path()
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(list(dict.fromkeys([int(x) for x in ids]))[:9], f, ensure_ascii=False, indent=2)

# --- LOGIQUE D'AFFICHAGE ---

async def get_owner_list_data(bot: commands.Bot):
    owner_ids = load_allowed()
    # On isole les IDs pour l'affichage (sans le créateur)
    display_ids = [uid for uid in owner_ids if uid != CREATOR_ID]
    count = len(display_ids)
    
    # 1. Section Créateur (toujours affichée)
    try:
        creator_user = await bot.fetch_user(CREATOR_ID)
        creator_line = f"<@{CREATOR_ID}> - *{creator_user.name.capitalize()}* - `{CREATOR_ID}`"
    except:
        creator_line = f"<@{CREATOR_ID}> - *Inconnu* - `{CREATOR_ID}`"
    
    lines = [f"👑 **Créateur**", f"└ 🏆 {creator_line}\n"]
    
    # 2. Section Owners (sans le créateur)
    lines.append(f"👥 **Liste des Owners ({count}/8)**")

    if not display_ids:
        lines.append("└ *Aucun owner enregistré*")
    else:
        for i, uid in enumerate(display_ids, start=1):
            try:
                user = await bot.fetch_user(uid)
                u_name = user.name.capitalize()
            except:
                u_name = "Inconnu"
            lines.append(f"└ {i}. <@{uid}> - *{u_name}* - `{uid}`")
    
    return "\n".join(lines)

async def generate_select_options(bot: commands.Bot) -> list[discord.SelectOption]:
    """Génère les options du sélecteur avec les pseudos précis fetchés depuis l'API Discord."""
    options = []
    owner_ids = load_allowed()
    display_ids = [uid for uid in owner_ids if uid != CREATOR_ID]
    
    for uid in display_ids:
        try:
            user = await bot.fetch_user(uid)
            # Affiche "Pseudo Serveur/Global - nom d'utilisateur" avec majuscule
            label_str = f"{user.display_name.capitalize()} - {user.name.capitalize()}"
        except:
            label_str = f"Utilisateur Inconnu"
            
        options.append(discord.SelectOption(
            label=label_str[:100], # Max 100 caractères imposé par Discord
            description=str(uid),
            value=str(uid),
            emoji="🗑️"
        ))
    return options

async def refresh_dashboard(interaction: discord.Interaction, cog: "ProfilDevCog") -> None:
    """Met à jour l'embed et recrée la vue pour que le Select s'actualise correctement."""
    try:
        title = f"👑 Liste des owners de {interaction.client.user.name}"
        text = await get_owner_list_data(interaction.client)
        
        if config_manager:
            new_embed = config_manager.get_formatted_embed(
                guild=interaction.guild, user=interaction.user, bot=interaction.client,
                title=title, description=text,
                target_id=interaction.guild.id if interaction.guild else None
            )
        else:
            new_embed = discord.Embed(title=title, description=text, color=0x2b2d31)

        # On génère les options correctement avant de créer la vue
        options = await generate_select_options(interaction.client)
        new_view = ManageView(cog, options)

        if interaction.message:
            await interaction.message.edit(embed=new_embed, view=new_view)
        else:
            await interaction.edit_original_response(embed=new_embed, view=new_view)
            
    except Exception as e:
        print(f"Erreur lors de la mise à jour du dashboard owner : {e}")

# --- INTERFACES ---

class IDModal(ui.Modal):
    def __init__(self, action: str, cog: "ProfilDevCog"):
        super().__init__(title="Gestion des accès")
        self.action = action 
        self.cog = cog
        self.id_input = ui.TextInput(label="ID de l'utilisateur", placeholder="Entrez l'ID...", required=True)
        self.add_item(self.id_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.id_input.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ ID invalide.", ephemeral=True)

        owners = load_allowed()
        
        if self.action == 'add':
            if uid == CREATOR_ID or uid in owners:
                return await interaction.response.send_message("Cet utilisateur a déjà les accès.", ephemeral=True)
            if len(owners) >= 9:
                return await interaction.response.send_message("❌ Limite de 9 owners atteinte.", ephemeral=True)
            
            owners.append(uid)
            save_allowed(owners)
        
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=False)
        
        # Met à jour visuellement le tableau de bord
        await refresh_dashboard(interaction, self.cog)

class OwnerSelect(ui.Select):
    def __init__(self, options, cog):
        # row=0 force le menu déroulant à s'afficher en premier (au-dessus du bouton)
        super().__init__(placeholder="Sélectionner un owner à retirer...", min_values=1, max_values=1, options=options, row=0)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        uid = int(self.values[0])
        
        if uid == CREATOR_ID:
            await interaction.response.send_message("❌ Impossible de révoquer le Créateur.", ephemeral=True)
            return
            
        owners_list = load_allowed()
        if uid in owners_list and uid != CREATOR_ID:
            owners_list.remove(uid)
            # S'assure que le créateur reste toujours à la racine de la liste
            if CREATOR_ID not in owners_list:
                owners_list.insert(0, CREATOR_ID)
            save_allowed(owners_list)
        
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=False)
        
        await refresh_dashboard(interaction, self.cog)

class ManageView(ui.View):
    def __init__(self, cog: "ProfilDevCog", select_options: list[discord.SelectOption]):
        super().__init__(timeout=None)
        self.cog = cog

        # Ajoute le sélecteur uniquement s'il y a des options, et toujours sur la ligne 0
        if select_options:
            self.add_item(OwnerSelect(select_options, cog))

    # row=1 force le bouton à s'afficher en dessous du sélecteur
    @ui.button(label="Ajouter", emoji="➕", style=discord.ButtonStyle.green, custom_id="owner_add_btn", row=1)
    async def add_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(IDModal('add', self.cog))


# --- COG ---

class ProfilDevCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="owner", help="Gérer les propriétaires du bot.")
    async def owner(self, ctx: commands.Context):
        owners = load_allowed()
        if ctx.author.id != CREATOR_ID and ctx.author.id not in owners:
            return await ctx.send("❌ Accès restreint aux owners du bot.")

        title = f"👑 Liste des owners de {self.bot.user.name}"
        text = await get_owner_list_data(self.bot)

        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=ctx.guild, user=ctx.author, bot=self.bot,
                title=title, description=text,
                target_id=ctx.guild.id if ctx.guild else None
            )
        else:
            embed = discord.Embed(title=title, description=text, color=0x2b2d31)

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    # Initialisation du fichier de sauvegarde à l'activation du cog
    ensure_owner_file_exists()
    
    # Supprime toute commande owner existante pour éviter les conflits
    if bot.get_command("owner"):
        bot.remove_command("owner")
        
    await bot.add_cog(ProfilDevCog(bot))