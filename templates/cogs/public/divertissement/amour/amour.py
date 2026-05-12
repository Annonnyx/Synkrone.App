import discord
from discord import app_commands
from discord.ext import commands
import random
import hashlib
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import aiohttp
from typing import Optional, Tuple, Dict, List
import traceback
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class Amour(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def calculer_amour(self, id1: int, id2: int) -> int:
        # Si c'est la même personne, on retourne 100%
        if id1 == id2:
            return 100
            
        ids = sorted([id1, id2])
        combo = f"{ids[0]}-{ids[1]}"
        seed = int(hashlib.md5(combo.encode()).hexdigest(), 16)
        random.seed(seed)
        return random.randint(0, 100)

    def message_selon_pourcentage(self, pourcentage: int) -> str:
        if pourcentage == 100:
            return "💘 Âmes sœurs pour la vie !"
        elif pourcentage >= 90:
            return "❤️ C'est chaud entre vous !"
        elif pourcentage >= 70:
            return "💕 Un bel amour en perspective !"
        elif pourcentage >= 50:
            return "💖 Il y a de l'espoir !"
        elif pourcentage >= 30:
            return "💔 Ça va être compliqué..."
        else:
            return "💔 C'est mort entre vous..."
            
    def generer_stats(self, user_id: int) -> Tuple[Dict[str, int], str]:
        """
        Génère des statistiques aléatoires basées sur l'ID de l'utilisateur.
        Répartition : 20% nuls, 60% normaux, 20% très bons
        Retourne un tuple contenant le dictionnaire des stats et une évaluation globale.
        """
        # Vérification de l'utilisateur spécifique
        if user_id == 1366780122891419784:
            stats_dict = {
                "force": 25,
                "charisme": 25,
                "intelligence": 25,
                "richesse": 25
            }
            return stats_dict, "🌟 Des compétences divines !"
            
        random.seed(user_id)  # Pour avoir des résultats cohérents pour le même utilisateur

        # Tirage de la catégorie de score
        roll = random.random() * 100

        if roll < 20:  # 20% de chance d'être "nul"
            # Entre 5 et 20 points (très faible)
            total = random.randint(5, 20)
            evaluations = [
                "💤 Très faible... Il va falloir se réveiller !",
                "🌱 Débutant absolu, mais tout le monde a un début !",
                "🦴 Un squelette a plus de compétences !",
                "❌ C'est pas gagné...",
                "😴 Tu dors au fond de la classe ?"
            ]
            evaluation = random.choice(evaluations)
        elif roll < 80:  # 60% de chance d'être "normal"
            # Entre 30 et 60 points (moyen)
            total = random.randint(30, 60)
            evaluations = [
                "⭐ Dans la moyenne, comme monsieur tout le monde !",
                "🌟 Pas mal, mais rien d'extraordinaire.",
                "✨ Des compétences tout à fait honorables.",
                "💫 Tu t'en sors bien, sans plus.",
                "🌠 Ni le meilleur, ni le pire, c'est déjà ça !"
            ]
            evaluation = random.choice(evaluations)
        else:  # 20% de chance d'être "très bon"
            # Entre 65 et 100 points (très bon)
            total = random.randint(65, 100)
            evaluations = [
                "🔥 Incroyable ! Des compétences exceptionnelles !",
                "🚀 Tu déchires tout, champion(ne) !",
                "🏆 Niveau professionnel !",
                "💎 Un véritable diamant brut !",
                "👑 La classe mondiale !"
            ]
            evaluation = random.choice(evaluations)

        # Répartition des points entre les statistiques
        stats = [1, 1, 1, 1]  # Minimum de 1 point par stat
        remaining = total - 4  # On a déjà attribué 4 points (4 * 1)

        # Répartition aléatoire des points restants
        for _ in range(remaining):
            stats[random.randint(0, 3)] += 1

        # S'assurer qu'aucune stat ne dépasse 25 (pour rester crédible)
        stats = [min(s, 25) for s in stats]
        
        # Mélanger pour plus de variété
        random.shuffle(stats)

        stats_dict = {
            "force": stats[0],
            "charisme": stats[1],
            "intelligence": stats[2],
            "richesse": stats[3]
        }
        return stats_dict, evaluation
        
    def formatter_stats(self, stats: dict, evaluation: str) -> str:
        """Formate les statistiques en une chaîne lisible avec évaluation."""
        return (
            f"💪 Force : {stats['force']}/20\n"
            f"🎭 Charisme : {stats['charisme']}/20\n"
            f"🧠 Intelligence : {stats['intelligence']}/20\n"
            f"💰 Richesse : {stats['richesse']}/20\n\n"
            f"*{evaluation}*"
        )
            
    def couleur_embed(self, pourcentage: int) -> discord.Color:
        if pourcentage >= 80:
            return discord.Color.red()
        elif pourcentage >= 60:
            return discord.Color.orange()
        elif pourcentage >= 40:
            return discord.Color.gold()
        elif pourcentage >= 20:
            return discord.Color.blue()
        else:
            return discord.Color.dark_grey()
            
    def create_circular_mask(self, size: int) -> Image.Image:
        """Crée un masque circulaire pour les avatars."""
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        return mask
        
    def adjust_alpha(self, image: Image.Image, alpha: float) -> Image.Image:
        """Ajuste l'opacité d'une image."""
        if alpha < 0 or alpha > 1:
            return image
            
        # Création d'un nouveau canal alpha
        alpha_channel = image.getchannel('A')
        alpha_channel = alpha_channel.point(lambda p: int(p * alpha))
        
        # Création d'une nouvelle image avec le canal alpha modifié
        result = image.copy()
        result.putalpha(alpha_channel)
        return result

    async def combine_avatars(self, url1: str, url2: str, pourcentage: int, username1: str, username2: str) -> BytesIO:
        # Chemins des assets
        assets_dir = Path(__file__).parent / "assets"
        heart_path = assets_dir / "heart.png"
        banner_path = assets_dir / "banner.png"
        
        # Téléchargement des avatars
        async with aiohttp.ClientSession() as session:
            async with session.get(url1) as resp1:
                avatar1_data = await resp1.read()
            async with session.get(url2) as resp2:
                avatar2_data = await resp2.read()

        # Chargement des images
        avatar_size = 180
        avatar1 = Image.open(BytesIO(avatar1_data)).convert("RGBA").resize((avatar_size, avatar_size))
        avatar2 = Image.open(BytesIO(avatar2_data)).convert("RGBA").resize((avatar_size, avatar_size))
        
        # Chargement de la bannière
        try:
            banner = Image.open(banner_path).convert("RGBA").resize((600, 300), Image.Resampling.LANCZOS)
        except:
            # Si la bannière n'est pas trouvée, on utilise un fond transparent
            banner = Image.new("RGBA", (600, 300), (0, 0, 0, 0))
        
        # Chargement du cœur
        heart = Image.open(heart_path).convert("RGBA")
        
        # Chargement du fond personnalisé
        try:
            fond_profil = Image.open(assets_dir / "fondprofil.png").convert("RGBA")
            # Redimensionner pour couvrir toute l'image
            fond_profil = fond_profil.resize((600, 300), Image.Resampling.LANCZOS)
            # Créer une nouvelle image avec le fond personnalisé
            result = Image.new("RGBA", (600, 300))
            # Coller le fond personnalisé
            result.paste(fond_profil, (0, 0))
            # Coller la bannière par-dessus avec transparence
            result = Image.alpha_composite(result, banner)
        except Exception as e:
            print(f"Erreur lors du chargement du fond personnalisé : {e}")
            result = banner.copy()
            
        draw = ImageDraw.Draw(result)
        
        # Taille des avatars avec bordure
        avatar_with_border_size = 200
        border_size = 10
        
        # Position des éléments
        avatar1_x = 50
        avatar2_x = 350
        avatar_y = 50  # Position verticale des avatars
        
        # Fonction pour dessiner un avatar avec bordure
        def draw_avatar(avatar, x, y, username):
            # Création d'un masque circulaire pour l'avatar
            mask = self.create_circular_mask(avatar_size)
            avatar_circle = Image.new("RGBA", (avatar_size, avatar_size), (0, 0, 0, 0))
            avatar_circle.paste(avatar, (0, 0), mask)
            
            # Charger et redimensionner le fond personnalisé pour le cercle
            try:
                fond_cercle = Image.open(assets_dir / "fondprofil.png").convert("RGBA")
                fond_cercle = fond_cercle.resize((avatar_size + 2*border_size, avatar_size + 2*border_size), Image.Resampling.LANCZOS)
                # Créer un masque circulaire pour le fond
                border_mask = self.create_circular_mask(avatar_size + 2*border_size)
                fond_cercle.putalpha(border_mask)
            except Exception as e:
                print(f"Erreur lors du chargement du fond du cercle : {e}")
                # En cas d'erreur, utiliser un fond blanc comme avant
                fond_cercle = Image.new('RGBA', (avatar_size + 2*border_size, avatar_size + 2*border_size), (255, 255, 255, 200))
                border_mask = self.create_circular_mask(avatar_size + 2*border_size)
                fond_cercle.putalpha(border_mask)
            
            # Positionnement de l'avatar et de la bordure
            avatar_pos = (avatar_with_border_size - avatar_size) // 2
            
            # Création d'une image temporaire pour l'avatar avec bordure
            avatar_with_border = Image.new("RGBA", (avatar_with_border_size, avatar_with_border_size + 60), (0, 0, 0, 0))  # +60 pour l'espace du pseudo plus grand
            
            # Collage du fond personnalisé
            border_pos = (avatar_pos - border_size, avatar_pos - border_size)
            avatar_with_border.alpha_composite(fond_cercle, border_pos)
            
            # Collage de l'avatar
            avatar_with_border.alpha_composite(avatar_circle, (avatar_pos, avatar_pos))
            
            # Collage sur l'image finale
            result.alpha_composite(avatar_with_border, (x, y))
            
            # Ajout du pseudo avec une police plus grande
            try:
                # Utiliser la police arial.ttf du dossier assets
                font_path = Path(__file__).parent / "assets" / "arial.ttf"
                font = ImageFont.truetype(str(font_path), 24)  # Taille augmentée à 24
            except:
                # Fallback : police par défaut mais plus grande
                font = ImageFont.load_default()
                font.size = 24 if hasattr(font, 'size') else 24
            
            # Utiliser le pseudo du serveur (display_name) et mettre une majuscule si besoin
            display_name = username  # username est déjà le display_name passé en paramètre
            formatted_name = display_name[0].upper() + display_name[1:] if display_name and display_name[0].islower() else display_name
            
            # Calcul de la largeur et hauteur du texte
            text_bbox = draw.textbbox((0, 0), formatted_name, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Position du texte (plus bas que précédemment)
            text_x = x + (avatar_with_border_size - text_width) // 2
            text_y = y + avatar_with_border_size + 15  # Position plus basse
            
            # Chargement de la police en gras
            try:
                # Utiliser la police arial.ttf du dossier assets en plus grand
                font_path = Path(__file__).parent / "assets" / "arial.ttf"
                font_bold = ImageFont.truetype(str(font_path), 26)  # Taille plus grande pour simuler du gras
            except:
                font_bold = font  # Fallback sur la police normale

            # Couleurs
            text_color = (255, 255, 255, 255)  # Blanc
            outline_color = (0, 0, 0, 255)     # Noir

            # Dessin du contour (effet de bordure noire)
            for x_offset, y_offset in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                draw.text(
                    (text_x + x_offset, text_y + y_offset),
                    formatted_name,
                    fill=outline_color,
                    font=font_bold,
                    align="center"
                )

            # Dessin du texte principal en blanc
            draw.text(
                (text_x, text_y),
                formatted_name,
                fill=text_color,
                font=font_bold,
                align="center"
            )
        
        # Dessin des avatars
        draw_avatar(avatar1, avatar1_x, avatar_y, username1)
        draw_avatar(avatar2, avatar2_x, avatar_y, username2)
        
        # Positionnement du cœur
        heart_size = 80
        heart = heart.resize((heart_size, heart_size), Image.Resampling.LANCZOS)
        heart_x = 300 - heart_size // 2
        heart_y = 120  # Ajusté pour être aligné avec les avatars
        result.alpha_composite(heart, (heart_x, heart_y))
        
        # Ajout du pourcentage au centre du cœur
        try:
            # Utiliser la police arial.ttf du dossier assets
            font_path = Path(__file__).parent / "assets" / "arial.ttf"
            font = ImageFont.truetype(str(font_path), 24)
        except:
            # Fallback : police par défaut mais plus grande
            font = ImageFont.load_default()
            font.size = 24 if hasattr(font, 'size') else 24
            
        # Positionnement du texte au centre du cœur
        text = f"{pourcentage}%"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = heart_x + (heart_size - text_width) // 2
        text_y = heart_y + (heart_size - text_height) // 2 - 5  # Ajustement manuel pour le centrage
        
        # Contour noir pour une meilleure lisibilité
        for x_offset in [-1, 0, 1]:
            for y_offset in [-1, 0, 1]:
                draw.text((text_x + x_offset, text_y + y_offset), 
                         text, fill="black", font=font, align="center")
        
        # Texte principal en blanc
        draw.text((text_x, text_y), text, fill="white", font=font, align="center")
        
        # Sauvegarde du résultat
        image_binary = BytesIO()
        result.save(image_binary, "PNG", quality=95)
        image_binary.seek(0)
        return image_binary

    async def envoyer_resultat(self, ctx, membre1: discord.Member, membre2: discord.Member):
        """Envoie le résultat du test d'amour entre deux membres avec image combinée et statistiques"""
        is_interaction = isinstance(ctx, discord.Interaction)
        
        try:
            # Calcul du pourcentage et préparation des données
            pourcentage = self.calculer_amour(membre1.id, membre2.id)
            message = self.message_selon_pourcentage(pourcentage)
            
            # Récupération des avatars et combinaison
            avatar1_url = membre1.display_avatar.with_format('png').url
            avatar2_url = membre2.display_avatar.with_format('png').url
            username1 = str(membre1)
            username2 = str(membre2)
            combined_avatar = await self.combine_avatars(avatar1_url, avatar2_url, pourcentage, username1, username2)
            
            # Génération des statistiques pour les deux membres
            stats1, eval1 = self.generer_stats(membre1.id)
            stats2, eval2 = self.generer_stats(membre2.id)
            
            # Récupération du contexte
            guild = ctx.guild if hasattr(ctx, 'guild') else (getattr(ctx, 'guild', None) if hasattr(ctx, 'guild') else None)
            user = getattr(ctx, 'user', None) or getattr(ctx, 'author', None)
            
            # Création de l'embed
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=guild,
                    user=user,
                    bot=self.bot,
                    title=f"💖 Test d'amour",
                    description=f"**Niveau de compatibilité : {pourcentage}%**\n\n{message}",
                    target_id=guild.id if guild else None
                )
            else:
                embed = discord.Embed(
                    title=f"💖 Test d'amour",
                    description=f"**Niveau de compatibilité : {pourcentage}%**\n\n{message}",
                    color=0xFF69B4  # Rose pour l'amour
                )
            
            # Ajout des champs de statistiques
            embed.add_field(
                name=f"📊 {membre1.display_name}",
                value=self.formatter_stats(stats1, eval1),
                inline=True
            )
            
            embed.add_field(
                name=f"📊 {membre2.display_name}",
                value=self.formatter_stats(stats2, eval2),
                inline=True
            )
            
            # Suppression du message d'alchimie magique comme demandé
            
            # Création du fichier image
            file = discord.File(combined_avatar, filename="love_result.png")
            
            # Ajout de la miniature (thumbnail)
            heart_thumb = discord.File(
                str(Path(__file__).parent / "assets" / "heart.png"), 
                filename="heart_thumb.png"
            )
            files = [file, heart_thumb]
            
            # Configuration de l'image principale et de la miniature
            embed.set_image(url="attachment://love_result.png")
            embed.set_thumbnail(url="attachment://heart_thumb.png")
            
            # Envoi du message de base
            base_message = f"Complicité entre {membre1.mention} et {membre2.mention} : {pourcentage}%"
            if is_interaction:
                if ctx.response.is_done():
                    await ctx.followup.send(base_message, files=files, embed=embed)
                else:
                    await ctx.response.send_message(base_message, files=files, embed=embed)
            else:
                await ctx.send(base_message, files=files, embed=embed)
            
        except Exception as e:
            error_msg = f"❌ Une erreur est survenue lors de la génération du test d'amour : {str(e)}"
            if is_interaction:
                if ctx.response.is_done():
                    await ctx.followup.send(error_msg, ephemeral=True)
                else:
                    await ctx.response.send_message(error_msg, ephemeral=True)
            else:
                await ctx.send(error_msg)

    @commands.hybrid_command(name="amour", description="Calcule le pourcentage d'amour entre deux membres")
    @app_commands.describe(
        membre1="Premier membre (laissez vide pour vous-même)",
        membre2="Deuxième membre (laissez vide pour un membre aléatoire)"
    )
    async def amour(
        self,
        ctx: commands.Context | discord.Interaction,
        membre1: Optional[discord.Member] = None,
        membre2: Optional[discord.Member] = None
    ):
        """Calcule le pourcentage d'amour entre deux membres"""
        is_interaction = isinstance(ctx, discord.Interaction)
        interaction = ctx if is_interaction else None
        
        try:
            if is_interaction:
                await ctx.response.defer(ephemeral=False)
            
            auteur = ctx.user if is_interaction else ctx.author
            guild = ctx.guild if hasattr(ctx, 'guild') else (ctx.guild if ctx.guild else None)
            
            # Si pas de membre1, on prend l'auteur et un membre aléatoire
            if membre1 is None:
                # Récupération de la liste des membres (uniquement si dans un serveur)
                if guild:
                    candidats = [m for m in guild.members if not m.bot and m != auteur]
                    if not candidats:
                        msg = "👀 Impossible de trouver quelqu'un d'autre que toi..."
                        return await self.repondre(ctx, msg, is_interaction)
                    
                    cible = random.choice(candidats)
                    await self.envoyer_resultat(interaction or ctx, auteur, cible)
                    return
                else:
                    msg = "❌ Cette commande nécessite un serveur pour fonctionner."
                    return await self.repondre(ctx, msg, is_interaction, ephemeral=True)
            
            # Si membre1 mais pas membre2, on compare l'auteur avec membre1
            if membre2 is None:
                await self.envoyer_resultat(interaction or ctx, auteur, membre1)
            else:
                # Si les deux membres sont spécifiés, on les compare
                await self.envoyer_resultat(interaction or ctx, membre1, membre2)
                
        except Exception as e:
            error_msg = f"❌ Une erreur est survenue : {str(e)}"
            await self.repondre(ctx, error_msg, is_interaction, ephemeral=True)
    
    async def repondre(self, ctx, message: str, is_interaction: bool, ephemeral: bool = False):
        """Utilitaire pour répondre de manière unifiée aux interactions et commandes"""
        if is_interaction:
            if ctx.response.is_done():
                await ctx.followup.send(message, ephemeral=ephemeral)
            else:
                await ctx.response.send_message(message, ephemeral=ephemeral)
        else:
            await ctx.send(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(Amour(bot))
