import json

import discord
from discord.ext import commands
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import os
from datetime import datetime
import random
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource

class Profil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="profil", description="Affiche le profil de l'utilisateur.")
    async def profil(self, ctx: commands.Context, membre: discord.Member = None):
        await ctx.defer()
        membre = membre or ctx.author


        try:
            # 1. Chargement des polices (chemin robuste)
            from pathlib import Path
            base_dir = Path(__file__).resolve().parent
            # Correction : pointer vers le bon dossier assets
            assets_dir = base_dir.parent / "assets"
            font_path = assets_dir / "TradeWinds-Regular.ttf"
            try:
                fonts = {
                    "pseudo": ImageFont.truetype(str(font_path), 60),
                    "titre": ImageFont.truetype(str(font_path), 40),
                    "niveau": ImageFont.truetype(str(font_path), 50),
                    "stats_label": ImageFont.truetype(str(font_path), 30),
                    "stats_value": ImageFont.truetype(str(font_path), 40),
                    "info": ImageFont.truetype(str(font_path), 28),
                    "xp": ImageFont.truetype(str(font_path), 28)
                }
                font_error = False
            except Exception as e:
                print(f"[Profil] Erreur chargement police: {e}")
                default_font = ImageFont.load_default()
                fonts = {k: default_font for k in ["pseudo", "titre", "niveau", "stats_label", "stats_value", "info", "xp"]}
                font_error = True

            # 2. Lecture des vraies stats utilisateur (serveur + user)
            server_id = str(ctx.guild.id) if ctx.guild else None
            user_id = str(membre.id)
            stats_path = os.path.abspath(os.path.join(base_dir, "..", "..", "..", "..", "data", "pack", "statistiques", server_id, f"{user_id}.json")) if server_id else None
            if stats_path and os.path.exists(stats_path):
                with open(stats_path, encoding="utf-8") as f:
                    stats_json = json.load(f)
                niveau = int(stats_json.get("level", 1))
                xp_textuel = int(stats_json.get("xp_textuel", 0))
                xp_vocal = int(stats_json.get("xp_vocal", 0))
                messages_envoyes = int(stats_json.get("messages_envoyes", 0))
                temps_vocal_sec = int(stats_json.get("temps_vocal", 0))
            else:
                niveau = 1
                xp_textuel = 0
                xp_vocal = 0
                messages_envoyes = 0
                temps_vocal_sec = 0

            # Lecture du lvl.json pour trouver le titre du plus haut palier atteint
            titre_value = None
            lvl_path = os.path.abspath(os.path.join(base_dir, "..", "..", "..", "..", "data", "pack", "statistiques", server_id, "lvl.json")) if server_id else None
            if lvl_path and os.path.exists(lvl_path):
                with open(lvl_path, encoding="utf-8") as f:
                    lvls = json.load(f)
                # Trie par niveau croissant
                lvls.sort(key=lambda x: int(x.get("niveau", 0)) if str(x.get("niveau", "")).isdigit() else 9999)
                titre_value = None
                for palier in lvls:
                    palier_lvl = int(palier.get("niveau", 0)) if str(palier.get("niveau", "")).isdigit() else 0
                    if niveau >= palier_lvl and palier.get("titre"):
                        titre_value = palier.get("titre")
                if not titre_value:
                    titre_value = "Aucun titre"
            else:
                titre_value = "Aucun titre"
            pseudo = membre.name
            pseudo_display = pseudo[0].upper() + pseudo[1:] if pseudo else "Inconnu"
            date_join = membre.joined_at.strftime('%d/%m/%Y') if membre.joined_at else '??/??/????'
            jours_depuis = (discord.utils.utcnow() - membre.joined_at).days if membre.joined_at else 0
            jours_texte = "1 jour" if jours_depuis <= 1 else f"{jours_depuis} jours"

            total_seconds = int(temps_vocal_sec)
            heures = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secondes = total_seconds % 60
            temps_vocal = f"{heures}h {minutes}m {secondes}s"

            xp_actuel = xp_textuel + xp_vocal
            # XP max pour le niveau suivant (lecture rules.json)
            rules_path = os.path.join(assets_dir, "rules.json")
            if os.path.exists(rules_path):
                with open(rules_path, encoding="utf-8") as f:
                    rules = json.load(f)
                levels = rules.get("levels_requirements", {})
                xp_max = levels.get(str(niveau+1), xp_actuel+1)
            else:
                xp_max = xp_actuel+1
            pourcentage_xp = xp_actuel / xp_max if xp_max > 0 else 0

            stats_data = [
                ("📝 XP Textuel", f"{xp_textuel:,}".replace(",", " ") + " Xp"),
                ("🎙️ XP Vocal", f"{xp_vocal:,}".replace(",", " ") + " Xp"),
                ("📨 Messages envoyés", f"{messages_envoyes:,}".replace(",", " ")),
                ("⏳ Temps en vocal", temps_vocal)
            ]

            # 3. Couleurs
            COLOR_OWNER_BOT = (255, 0, 0, 255)
            COLOR_OWNER_SERVER = (255, 215, 0, 255)
            COLOR_ADMIN = (0, 0, 0, 255)
            COLOR_BOOSTER = (232, 69, 255, 255)
            COLOR_DEFAULT = (114, 137, 218, 255)

            # Couleurs de titre (cohérentes par rôle)
            ROLE_TITLE_COLORS = {
                "leader": (255, 0, 0, 255),
                "superviseur": (66, 165, 245, 255),
                "manager": (255, 152, 0, 255),
                "elite": (171, 71, 188, 255),
                "dev": (41, 182, 246, 255),
                "test": (76, 175, 80, 255),
                "redacteur": (255, 193, 7, 255),
                "rédacteur": (255, 193, 7, 255),
                "support": (244, 143, 177, 255)
            }

            def get_titre_color(titre: str):
                if not titre:
                    return (186, 104, 255, 255)

                titre_lower = titre.lower()
                for key, color in ROLE_TITLE_COLORS.items():
                    if key in titre_lower:
                        return color

                return (186, 104, 255, 255)

            card_color = COLOR_DEFAULT
            notion_role = "Utilisateur"

            if await self.bot.is_owner(membre):
                card_color = COLOR_OWNER_BOT
                notion_role = "Owner du bot"
                statut_color = COLOR_OWNER_BOT
            elif ctx.guild and membre.id == ctx.guild.owner_id:
                card_color = COLOR_OWNER_SERVER
                notion_role = "Owner du serveur"
                statut_color = COLOR_OWNER_SERVER
            elif any(r.permissions.administrator for r in getattr(membre, "roles", [])):
                card_color = COLOR_ADMIN
                notion_role = "Administrateur"
                statut_color = COLOR_ADMIN
            elif any(r.is_premium_subscriber() for r in getattr(membre, "roles", [])):
                card_color = COLOR_BOOSTER
                notion_role = "Booster"
                statut_color = COLOR_BOOSTER
            else:
                statut_color = COLOR_DEFAULT

            # 4. Dimensions
            width, height = 900, 720
            padding = 40
            avatar_size = 256
            col_gauche_x = padding
            col_droite_x = padding + avatar_size + 60

            # 5. Fond et effet carbone
            base_color = (40, 43, 48, 255)
            gradient = Image.new("RGBA", (1, height), base_color)
            draw_grad = ImageDraw.Draw(gradient)
            for y in range(height):
                ratio = y / height
                r = int(base_color[0] + (card_color[0] - base_color[0]) * ratio * 0.3)
                g = int(base_color[1] + (card_color[1] - base_color[1]) * ratio * 0.3)
                b = int(base_color[2] + (card_color[2] - base_color[2]) * ratio * 0.3)
                draw_grad.line([(0, y), (0, y)], fill=(r, g, b, 255))
            background = gradient.resize((width, height))
            
            stripe_width = 18
            stripe_color_1 = (60, 60, 70, 60)
            stripe_color_2 = (255, 255, 255, 18)
            for x in range(-height, width, stripe_width):
                for y in range(height):
                    if ((x + y) // stripe_width) % 2 == 0:
                        color = stripe_color_1
                    else:
                        color = stripe_color_2
                    px = x + y
                    if 0 <= px < width:
                        bg_px = background.getpixel((px, y))
                        new_px = tuple(
                            min(255, int(bg_px[i] * (1 - color[3]/255) + color[i] * (color[3]/255)))
                            for i in range(4)
                        )
                        background.putpixel((px, y), new_px)
            
            draw = ImageDraw.Draw(background)

            # 6. Avatar
            avatar_url = membre.display_avatar.replace(size=256, static_format="png").url
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    avatar_bytes = await resp.read()
            
            avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))
            avatar_y = padding
            background.paste(avatar, (col_gauche_x, avatar_y), avatar)

            contour_color = card_color if card_color != COLOR_DEFAULT else (114, 137, 218, 255)
            draw.rectangle([col_gauche_x, avatar_y, col_gauche_x + avatar_size, avatar_y + avatar_size], outline=contour_color, width=6)

            # --- TEXTES ---
            draw.text((col_droite_x, padding), pseudo_display, fill=(255, 255, 255, 255), font=fonts["pseudo"])

            info_start_y = padding + 90
            couleur_info = (200, 200, 200, 255)

            # Statut
            statut_y = info_start_y
            for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
                draw.text((col_droite_x+dx, statut_y+dy), notion_role, fill=statut_color, font=fonts["titre"])

            decal = 50
            draw.text((col_droite_x, info_start_y + decal), f"Rejoint le : {date_join}", fill=couleur_info, font=fonts["info"])
            draw.text((col_droite_x, info_start_y + decal + 40), f"Il y a {jours_texte}", fill=couleur_info, font=fonts["info"])
            draw.text((col_droite_x, info_start_y + decal + 80), f"ID : {membre.id}", fill=couleur_info, font=fonts["info"])

            # Niveau & Titre
            level_y = avatar_y + avatar_size + 40
            level_text = f"Niveau {niveau:,}".replace(",", " ")
            draw.text((padding, level_y), level_text, fill=(255, 255, 255, 255), font=fonts["niveau"])

            try:
                # Utilise str(font_path) pour garantir la compatibilité
                from pathlib import Path
                titre_font = ImageFont.truetype(str(font_path), 55)
            except Exception as e:
                print(f"[Profil] Erreur chargement police titre: {e}")
                titre_font = fonts["titre"]
            titre_bbox = draw.textbbox((0, 0), titre_value, font=titre_font)
            titre_width = titre_bbox[2] - titre_bbox[0]
            titre_x = width - padding - titre_width
            couleur_titre = get_titre_color(titre_value)
            for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
                draw.text((titre_x+dx, level_y - 7+dy), titre_value, fill=couleur_titre, font=titre_font)

            # Barre XP
            bar_y = level_y + 70
            bar_width = width - (2 * padding)
            bar_height = 51
            draw.rectangle([padding, bar_y, padding + bar_width, bar_y + bar_height], fill=(60, 60, 60, 255), outline=(200, 200, 200, 255), width=2)

            couleur_verte = (46, 204, 113, 255)
            if pourcentage_xp > 0:
                xp_fill_width = int(bar_width * min(pourcentage_xp, 1))
                draw.rectangle([padding, bar_y, padding + xp_fill_width, bar_y + bar_height], fill=couleur_verte)

            percent_xp = int(pourcentage_xp * 100)
            xp_text = f"{xp_actuel:,} XP".replace(",", " ") if xp_actuel >= xp_max else f"{xp_actuel:,} / {xp_max:,} XP  ({percent_xp}%)".replace(",", " ")
            xp_bbox = draw.textbbox((0, 0), xp_text, font=fonts["xp"])
            xp_text_width = xp_bbox[2] - xp_bbox[0]
            xp_text_height = xp_bbox[3] - xp_bbox[1]
            xp_text_x = padding + (bar_width - xp_text_width) // 2
            xp_text_y = bar_y + (bar_height - xp_text_height) // 2
            draw.text((xp_text_x, xp_text_y), xp_text, fill=(0, 0, 0, 255), font=fonts["xp"])

            # Stats
            stats_y = bar_y + bar_height + 40
            col_stat_1_x = padding
            col_stat_2_x = width // 2 + 50
            
            with Pilmoji(background, source=GoogleEmojiSource) as pilmoji:
                for i, (label, value) in enumerate(stats_data):
                    x = col_stat_1_x if i % 2 == 0 else col_stat_2_x
                    y = stats_y + (i // 2) * 85
                    pilmoji.text((x, y), label.upper(), fill=(200, 200, 200, 255), font=fonts["stats_label"])
                    draw.text((x, y + 30), value, fill=couleur_verte, font=fonts["stats_value"])

            # --- AJOUT DATE & ICÔNE SERVEUR (BAS GAUCHE) ---
            date_now = datetime.now().strftime("%d/%m/%Y - %H:%M")
            server_name = ctx.guild.name if ctx.guild and ctx.guild.name else None
            date_font_size = 22
            date_font = fonts["info"] if "info" in fonts else ImageFont.load_default()
            date_color = (170, 170, 180, 230)
            shadow_color = (30, 30, 40, 120)
            # Texte : date, heure, nom serveur (sans ' - ' si nom serveur absent)
            if server_name:
                date_text = f"{date_now}   {server_name}"
            else:
                date_text = date_now
            # Calcul dynamique de la position X pour aligner parfaitement à droite de l'icône
            # Valeurs par défaut si pas d'icône serveur
            icon_size = 28
            contour_size = 36
            contour_width = 4
            ombre_size = 40
            icon_x = 18
            icon_width = contour_size
            padding_left = 16
            # Calcul de la hauteur pour aligner verticalement avec le texte
            date_y = height - date_font_size - 18
            # Centrage parfait de l'icône sur la ligne
            icon_y = date_y + (date_font_size // 2) - (contour_size // 2) + 1
            date_x = icon_x + icon_width + padding_left
            date_y = height - date_font_size - 18
            # Ombre légère pour le texte
            draw.text((date_x+1, date_y+1), date_text, fill=shadow_color, font=date_font)
            draw.text((date_x, date_y), date_text, fill=date_color, font=date_font)

            if ctx.guild and ctx.guild.icon:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(ctx.guild.icon.url) as resp:
                            icon_bytes = await resp.read()
                    server_icon = Image.open(BytesIO(icon_bytes)).convert("RGBA").resize((icon_size, icon_size))
                    # Masque circulaire
                    mask = Image.new("L", (icon_size, icon_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0, icon_size, icon_size), fill=255)
                    server_icon_rounded = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
                    server_icon_rounded.paste(server_icon, (0, 0), mask)
                    # Ombre légère (centrée)
                    ombre = Image.new("RGBA", (ombre_size, ombre_size), (0, 0, 0, 0))
                    ombre_draw = ImageDraw.Draw(ombre)
                    ombre_draw.ellipse([
                        (ombre_size - contour_size) // 2 + 2,
                        (ombre_size - contour_size) // 2 + 2,
                        (ombre_size + contour_size) // 2 - 2,
                        (ombre_size + contour_size) // 2 - 2
                    ], fill=(30, 30, 40, 50))
                    # Contour blanc très net
                    contour = Image.new("RGBA", (contour_size, contour_size), (0, 0, 0, 0))
                    contour_draw = ImageDraw.Draw(contour)
                    contour_draw.ellipse([0, 0, contour_size-1, contour_size-1], outline=(255, 255, 255, 255), width=contour_width)
                    contour.paste(server_icon_rounded, ((contour_size-icon_size)//2, (contour_size-icon_size)//2), server_icon_rounded)
                    # Fusion ombre + contour
                    # Collage sur le fond, bien centré
                    final_icon = Image.alpha_composite(ombre.crop((2, 2, 2+contour_size, 2+contour_size)), contour)
                    background.paste(final_icon, (icon_x, icon_y), final_icon)
                except Exception:
                    pass

            # 7. Envoi
            buffer = BytesIO()
            background.save(buffer, format="PNG")
            buffer.seek(0)

            file = discord.File(fp=buffer, filename="profil.png")
            embed_color = discord.Color.from_rgb(*card_color[:3]) 
            embed = discord.Embed(description=f"👤 𝑷𝒓𝒐𝒇𝒊𝒍 𝒅𝒆 {membre.mention}", color=embed_color)
            embed.set_image(url="attachment://profil.png")
            
            footer_text = f"𝑺𝒕𝒂𝒕𝒊𝒔𝒕𝒊𝒒𝒖𝒆 𝒅𝒖 𝒔𝒆𝒓𝒗𝒆𝒖𝒓 {server_name}"
            if ctx.guild and ctx.guild.icon:
                embed.set_footer(text=footer_text, icon_url=ctx.guild.icon.url)
            else:
                embed.set_footer(text=footer_text)

            await ctx.send(embed=embed, file=file)

        except Exception as e:
            import traceback
            traceback.print_exc()
            await ctx.send("Une erreur est survenue lors de la création du profil.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Profil(bot))