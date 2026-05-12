import logging
logger = logging.getLogger("Leader")
import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from pathlib import Path
import os
import json
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# --- Constantes et Chemins ---
# Correction DATA_DIR : pointer sur le vrai dossier data/pack/statistiques (sans 'cogs')
DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "pack" / "statistiques"
# Harmonisation du chemin de la police avec profil.py
base_dir = Path(__file__).resolve().parent
ASSETS_DIR = base_dir.parent / "assets"
FONT_PATH = ASSETS_DIR / "TradeWinds-Regular.ttf"

TITRES_EMBED = {
    "level": "⭐ Classement par Niveau",
    "vocal": "🎙️ Classement Vocal",
    "textuel": "📝 Classement Textuel"
}

# --- Fonctions utilitaires ---
def format_messages(val):
    return f"{val:,}".replace(",", " ")

def format_time(seconds):
    h, m = seconds // 3600, (seconds % 3600) // 60
    h_str = f"{h:,}".replace(",", " ")
    m_str = f"{m:,}".replace(",", " ")
    return f"{h_str}h {m_str}m"

# --- Interface UI (Select + Pagination) ---
class ClassementSelect(Select):
    def __init__(self, current_type):
        options = [
            discord.SelectOption(label="Niveau", value="level", emoji="⭐", default=(current_type == "level")),
            discord.SelectOption(label="Activité vocale", value="vocal", emoji="🎙️", default=(current_type == "vocal")),
            discord.SelectOption(label="Activité textuelle", value="textuel", emoji="📝", default=(current_type == "textuel")),
        ]
        super().__init__(placeholder="Choisis le classement", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await self.view.change_category(interaction, self.values[0])

class LeaderView(View):
    def __init__(self, bot, guild, author_id, max_page, current_page=1, classement_type="level"):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild
        self.author_id = author_id
        self.current_page = current_page
        self.max_page = max_page
        self.classement_type = classement_type

        # Ajout du menu déroulant
        self.add_item(ClassementSelect(self.classement_type))

        # Boutons de pagination (emoji uniquement)
        self.btn_prev = Button(emoji="◀", style=discord.ButtonStyle.blurple, disabled=(self.current_page <= 1))
        self.btn_prev.callback = self.prev_page
        self.add_item(self.btn_prev)

        # Bouton central pour afficher la page actuelle et ouvrir un modal
        self.btn_page = Button(label=f"{self.page_range_label()}", style=discord.ButtonStyle.gray)
        self.btn_page.callback = self.goto_page_modal
        self.add_item(self.btn_page)

        self.btn_next = Button(emoji="▶", style=discord.ButtonStyle.blurple, disabled=(self.current_page >= self.max_page))
        self.btn_next.callback = self.next_page
        self.add_item(self.btn_next)

    def page_range_label(self):
        start = (self.current_page - 1) * 10 + 1
        end = min(self.current_page * 10, self.max_page * 10)
        return f"{start} à {end}"

    async def goto_page_modal(self, interaction: discord.Interaction):
        class PageModal(discord.ui.Modal, title="Aller à une page"):
            page = discord.ui.TextInput(label="Numéro de page", placeholder="Ex: 54", required=True)

            async def on_submit(self, modal_interaction: discord.Interaction):
                try:
                    page_num = int(self.page.value)
                except ValueError:
                    await modal_interaction.response.send_message("Numéro invalide.", ephemeral=True)
                    return
                if not (1 <= page_num <= self.view.max_page):
                    await modal_interaction.response.send_message(f"Page entre 1 et {self.view.max_page}.", ephemeral=True)
                    return
                self.view.current_page = page_num
                await self.view.update_leaderboard(modal_interaction)

        modal = PageModal()
        modal.view = self
        await interaction.response.send_modal(modal)

    async def prev_page(self, interaction: discord.Interaction):
        self.current_page -= 1
        await self.update_leaderboard(interaction)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page += 1
        await self.update_leaderboard(interaction)

    async def change_category(self, interaction: discord.Interaction, new_type: str):
        self.classement_type = new_type
        self.current_page = 1 # On remet à la page 1 si on change de catégorie
        await self.update_leaderboard(interaction)

    async def update_leaderboard(self, interaction: discord.Interaction):
        # 1. Mise à jour de l'embed pour afficher "Chargement..."
        embed = interaction.message.embeds[0]
        embed.title = f"⏳ Chargement... ({TITRES_EMBED[self.classement_type]})"
        embed.set_image(url=None)
        await interaction.response.edit_message(embed=embed, attachments=[])

        # 2. Génération de la nouvelle image
        embed, file, self.max_page = await generate_leaderboard_image(
            self.bot, self.guild, self.classement_type, self.author_id, self.current_page
        )
        embed.title = TITRES_EMBED[self.classement_type]

        # 3. Affichage de la page dans le footer (en bas à droite)

        # 4. Mise à jour de l'état des boutons
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.max_page)
        self.btn_page.label = self.page_range_label()

        # 5. Envoi
        await interaction.edit_original_response(embed=embed, attachments=[file], view=self)

# --- Fonction de génération d'image ---
async def generate_leaderboard_image(bot, guild, classement_type, author_id, page=1):
    stats = []
    server_dir = DATA_DIR / str(guild.id)

    # 1. Gestion des données inexistantes
    if not server_dir.exists():
        logger.error(f"Dossier data introuvable : {server_dir} (guild.id={guild.id})")
        embed = discord.Embed(description=f"Aucune donnée trouvée pour ce serveur.\nChemin cherché : {server_dir}\nGuild ID : {guild.id}", color=discord.Color.red())
        return embed, None, 1

    try:
        for file in os.listdir(server_dir):
            if file.endswith(".json"):
                filename_no_ext = file[:-5]
                if not filename_no_ext.isdigit():
                    # On ignore les fichiers non numériques (ex: lvlup_config.json, lvl.json, etc)
                    continue
                try:
                    with open(server_dir / file, encoding="utf-8") as f:
                        data = json.load(f)
                    user_id = int(filename_no_ext)
                    stats.append({
                        "user_id": user_id,
                        "level": data.get("level", 1),
                        "xp": data.get("xp", 0),
                        "xp_textuel": data.get("xp_textuel", 0),
                        "xp_vocal": data.get("xp_vocal", 0),
                        "messages_envoyes": data.get("messages_envoyes", 0),
                        "temps_vocal": data.get("temps_vocal", 0)
                    })
                except Exception as e:
                    logger.error(f"Impossible de lire {file} dans {server_dir} : {e}")
    except Exception as e:
        logger.error(f"Impossible de lister les fichiers dans {server_dir} : {e}")

    if not stats:
        logger.error(f"Aucune donnée utilisateur trouvée dans {server_dir} (guild.id={guild.id})")

    # 2. Tri et définition des variables
    if classement_type == "level":
        stats.sort(key=lambda x: (x["level"], x["xp"]), reverse=True)
        titre = "Classement par Niveau Total"
        nb_cols = 5
    elif classement_type == "vocal":
        stats.sort(key=lambda x: x["xp_vocal"], reverse=True)
        titre = "Classement par Activité Vocale"
        nb_cols = 6
    else:
        stats.sort(key=lambda x: x["xp_textuel"], reverse=True)
        titre = "Classement par Activité Textuelle"
        nb_cols = 6

    # --- Logique de Pagination ---
    top_n = 10
    max_page = max(1, math.ceil(len(stats) / top_n))
    page = max(1, min(page, max_page)) # Sécurité pour ne pas déborder
    
    start_idx = (page - 1) * top_n
    end_idx = start_idx + top_n
    page_stats = stats[start_idx:end_idx]

    # 3. Calcul de l'UI
    padding_side = 80
    needed_cols_space = [150, 160, 900, 350, 450, 450]
    active_col_reqs = needed_cols_space[:nb_cols]
    
    width = sum(active_col_reqs) + (padding_side * 2) 
    row_height = 140
    height = 260 + row_height * (top_n + 5)
    
    # Dessin du fond
    base_color = (30, 50, 30, 255)
    accent_color = (46, 204, 113, 255)
    gradient = Image.new("RGBA", (1, height), base_color)
    draw_grad = ImageDraw.Draw(gradient)
    for y in range(height):
        ratio = y / height
        r = int(base_color[0] + (accent_color[0] - base_color[0]) * ratio * 0.3)
        g = int(base_color[1] + (accent_color[1] - base_color[1]) * ratio * 0.3)
        b = int(base_color[2] + (accent_color[2] - base_color[2]) * ratio * 0.3)
        draw_grad.line([(0, y), (0, y)], fill=(r, g, b, 255))
    background = gradient.resize((width, height))
    
    stripe_width = 36
    stripe_color_1 = (60, 90, 60, 60)
    stripe_color_2 = (200, 255, 200, 18)
    for x in range(-height, width, stripe_width):
        for y in range(height):
            if ((x + y) // stripe_width) % 2 == 0:
                color = stripe_color_1
            else:
                color = stripe_color_2
            px = x + y
            if 0 <= px < width:
                bg_px = background.getpixel((px, y))
                new_px = tuple(min(255, int(bg_px[i] * (1 - color[3]/255) + color[i] * (color[3]/255))) for i in range(4))
                background.putpixel((px, y), new_px)
                
    img = background
    draw = ImageDraw.Draw(img)

    # Polices
    try:
        font_title = ImageFont.truetype(str(FONT_PATH), 120)
        font_entry = ImageFont.truetype(str(FONT_PATH), 64)
        font_small = ImageFont.truetype(str(FONT_PATH), 42)
    except Exception:
        font_title = font_entry = font_small = ImageFont.load_default()

    draw.text((width//2, 180), f"{titre}", font=font_title, fill=(255, 235, 150, 255), anchor="mm")

    col_x = [padding_side]
    for i in range(1, nb_cols):
        col_x.append(col_x[-1] + active_col_reqs[i-1])
        
    y_header = 340

    draw.text((col_x[0], y_header), "#", font=font_entry, fill=(255,255,255,230), anchor="lm")
    draw.text((col_x[1], y_header), "Utilisateur", font=font_entry, fill=(255,255,255,230), anchor="lm")
    draw.text((col_x[3], y_header), "Niveau", font=font_entry, fill=(255,255,255,230), anchor="lm")
    
    if classement_type == "level":
        draw.text((col_x[4], y_header), "XP", font=font_entry, fill=(255,255,255,230), anchor="lm")
    elif classement_type == "vocal":
        draw.text((col_x[4], y_header), "XP", font=font_entry, fill=(255,255,255,230), anchor="lm")
        draw.text((col_x[5], y_header), "Temps vocal", font=font_entry, fill=(255,255,255,230), anchor="lm")
    else:
        draw.text((col_x[4], y_header), "XP", font=font_entry, fill=(255,255,255,230), anchor="lm")
        draw.text((col_x[5], y_header), "Messages", font=font_entry, fill=(255,255,255,230), anchor="lm")

    def format_xp(val):
        if val >= 1_000_000:
            return f"{val // 1_000_000}M{(val % 1_000_000) // 100_000 if (val % 1_000_000) // 100_000 else ''} XP"
        elif val >= 1_000:
            return f"{val // 1_000}K{(val % 1_000) // 100 if (val % 1_000) // 100 else ''} XP"
        return f"{val} XP"

    async def draw_user_row(y_pos, rank, entry, bg_color, text_color):
        rect_left = padding_side - 40
        rect_right = width - padding_side + 40
        
        draw.rounded_rectangle([rect_left, y_pos-20, rect_right, y_pos+row_height-30], radius=30, fill=bg_color)
        center_y = y_pos + (row_height - 50) // 2

        draw.text((col_x[0], center_y), f"#{rank}", font=font_entry, fill=text_color, anchor="lm")

        if not entry:
            for i in range(2, len(col_x)):
                draw.text((col_x[i], center_y), "-", font=font_entry, fill=text_color, anchor="lm")
            return

        user = guild.get_member(entry["user_id"])
        pseudo = user.name.capitalize() if user else f"Inconnu ({entry['user_id']})"

        COLOR_OWNER_BOT = (255, 0, 0, 255)
        COLOR_OWNER_SERVER = (255, 215, 0, 255)
        COLOR_ADMIN = (0, 0, 0, 255)
        COLOR_BOOSTER = (232, 69, 255, 255)
        COLOR_DEFAULT = (114, 137, 218, 255)
        
        avatar_contour = COLOR_DEFAULT
        if user:
            if await bot.is_owner(user):
                avatar_contour = COLOR_OWNER_BOT
            elif guild.owner_id == user.id:
                avatar_contour = COLOR_OWNER_SERVER
            elif user.guild_permissions.administrator:
                avatar_contour = COLOR_ADMIN
            elif user.premium_since is not None:
                avatar_contour = COLOR_BOOSTER

        avatar_size = 100
        avatar_y = center_y - (avatar_size // 2)

        if user and user.display_avatar:
            try:
                avatar_bytes = await user.display_avatar.replace(size=128, static_format="png").read()
                avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))
                mask = Image.new("L", (avatar_size, avatar_size), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
                avatar_img.putalpha(mask)
                
                contour_size = avatar_size + 16
                contour = Image.new("RGBA", (contour_size, contour_size), (0,0,0,0))
                contour_draw = ImageDraw.Draw(contour)
                contour_draw.ellipse([0, 0, contour_size-1, contour_size-1], fill=(40,40,40,255), outline=avatar_contour, width=8)
                
                img.paste(contour, (col_x[1]-8, avatar_y-8), contour)
                img.paste(avatar_img, (col_x[1], avatar_y), avatar_img)
            except Exception:
                pass

        draw.text((col_x[2], center_y), pseudo, font=font_entry, fill=text_color, anchor="lm")
        draw.text((col_x[3], center_y), f"Niv. {entry['level']}", font=font_entry, fill=text_color, anchor="lm")

        if classement_type == "level":
            draw.text((col_x[4], center_y), format_xp(entry['xp']), font=font_entry, fill=text_color, anchor="lm")
        elif classement_type == "vocal":
            draw.text((col_x[4], center_y), format_xp(entry['xp_vocal']), font=font_entry, fill=text_color, anchor="lm")
            draw.text((col_x[5], center_y), format_time(int(entry['temps_vocal'])), font=font_entry, fill=text_color, anchor="lm")
        else:
            draw.text((col_x[4], center_y), format_xp(entry['xp_textuel']), font=font_entry, fill=text_color, anchor="lm")
            draw.text((col_x[5], center_y), f"{format_messages(entry['messages_envoyes'])} msg", font=font_entry, fill=text_color, anchor="lm")

    y = y_header + row_height

    # 4. Dessiner la ligne de l'utilisateur appelant
    # Attention, on cherche son rank global, pas seulement sur la page !
    user_rank = next((i for i, e in enumerate(stats) if e['user_id'] == author_id), None)
    user_entry = stats[user_rank] if user_rank is not None else None

    user_stats_bg = (50, 50, 50, 255)
    user_stats_text = (240, 240, 240, 255)

    if user_entry:
        await draw_user_row(y, user_rank + 1, user_entry, bg_color=user_stats_bg, text_color=user_stats_text)
    else:
        rect_left = padding_side - 40
        rect_right = width - padding_side + 40
        draw.rounded_rectangle([rect_left, y-20, rect_right, y+row_height-30], radius=30, fill=user_stats_bg)
        draw.text((col_x[2], y + (row_height - 50) // 2), "Tu n'es pas classé", font=font_entry, fill=user_stats_text, anchor="lm")

    y += row_height + 40

    # 5. Dessiner le top 10 (ou le reste de la page)
    slots = page_stats + [None] * (top_n - len(page_stats))

    for i, entry in enumerate(slots):
        rank = start_idx + i + 1
        
        if rank == 1 and entry is not None:
            bg, txt = (235, 180, 20, 220), (50, 40, 0, 255)    
        elif rank == 2 and entry is not None:
            bg, txt = (220, 220, 220, 220), (40, 40, 40, 255)
        elif rank == 3 and entry is not None:
            bg, txt = (205, 127, 50, 220), (50, 25, 0, 255)   
        else:
            bg, txt = (230, 230, 230, 255), (40, 40, 40, 255) 

        await draw_user_row(y, rank, entry, bg, txt)
        y += row_height

    # 6. Pied de page
    footer_y = height - 90
    date_now = datetime.now().strftime("%d/%m/%Y - %H:%M")
    server_name = guild.name if guild else ""
    footer_text = f"{server_name}   |   {date_now}"
    
    icon_size = 90
    icon_x = padding_side - 40
    icon_y = footer_y - (icon_size // 2)
    text_x = icon_x

    if guild and guild.icon:
        try:
            icon_bytes = await guild.icon.replace(size=128, static_format="png").read()
            icon_img = Image.open(BytesIO(icon_bytes)).convert("RGBA").resize((icon_size, icon_size))
            
            mask = Image.new("L", (icon_size, icon_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, icon_size, icon_size), fill=255)
            icon_img.putalpha(mask)
            
            contour_s = icon_size + 6
            contour = Image.new("RGBA", (contour_s, contour_s), (0,0,0,0))
            ImageDraw.Draw(contour).ellipse([0, 0, contour_s-1, contour_s-1], fill=(255,255,255,255))
            
            img.paste(contour, (icon_x - 3, icon_y - 3), contour)
            img.paste(icon_img, (icon_x, icon_y), icon_img)
            
            text_x = icon_x + icon_size + 30
        except Exception:
            pass

    draw.text((text_x, footer_y), footer_text, font=font_small, fill=(200, 200, 200, 255), anchor="lm")
    page_text = f"Page {page} / {max_page}"
    draw.text((width - padding_side, height - 40), page_text, font=font_small, fill=(200, 200, 200, 255), anchor="rd")

    # 7. Sauvegarde
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    file = discord.File(fp=buffer, filename="leaderboard.png")
    
    embed = discord.Embed(color=discord.Color.from_rgb(30, 50, 30))
    embed.set_image(url="attachment://leaderboard.png")
    
    return embed, file, max_page

# --- Commande Discord ---
class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="leader", description="Affiche le classement du serveur.")
    async def leader(self, ctx):
        await ctx.defer() # Indispensable pour éviter que l'interaction n'expire
        
        classement_type = "level"
        page = 1
        
        embed, file, max_page = await generate_leaderboard_image(self.bot, ctx.guild, classement_type, ctx.author.id, page)
        
        # S'il n'y a pas de stats
        if file is None:
            await ctx.send(embed=embed)
            return

        embed.title = TITRES_EMBED[classement_type]
        view = LeaderView(self.bot, ctx.guild, ctx.author.id, max_page, page, classement_type)
        await ctx.send(embed=embed, file=file, view=view)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))