# ==============================
# 2048 Game for Discord
# ==============================
import discord
from discord.ext import commands
import random
import json
import os
from pathlib import Path
from collections import Counter

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================
# Constantes & configs
# ==============================
DEFAULT_COLOR = 0x2C2F33
DATA_DIR = Path("data/public/jeux/data_2048")
SIZE = 4

# Définition des emojis personnalisés pour les tuiles
TUILE_2 = "<:tuile_2:1427325065992867941>"
TUILE_4 = "<:tuile_4:1427325086242832395>"
TUILE_8 = "<:tuile_8:1427325106266312886>"
TUILE_16 = "<:tuile_16:1427325129444298945>"
TUILE_32 = "<:tuile_32:1427325149023047853>"
TUILE_64 = "<:tuile_64:1427325171399921684>"
TUILE_128 = "<:tuile_128:1427325188843901061>"
TUILE_256 = "<:tuile_256:1427325208280305760>"
TUILE_512 = "<:tuile_512:1427325226856874015>"
TUILE_1024 = "<:tuile_1024:1427325259954257920>"
TUILE_2048 = "<:tuile_2048:1427325282846638080>"
TUILE_4096 = "<:tuile_4096:1427325302211608687>"
TUILE_8192 = "<:tuile_8192:1427325319672762420>"
TUILE_16384 = "<:tuile_16384:1427325341575151787>"
TUILE_32768 = "<:tuile_32768:1427325364799275038>"
TUILE_65536 = "<:tuile_65536:1427325382465552454>"
TUILE_131072 = "<:tuile_131072:1427325400794792016>"

# Dictionnaire de correspondance entre les valeurs et les emojis
EMOJI_NUMBERS = {
    0: '⬜',  # Tuile vide
    2: TUILE_2, 4: TUILE_4, 8: TUILE_8, 16: TUILE_16,
    32: TUILE_32, 64: TUILE_64, 128: TUILE_128, 256: TUILE_256,
    512: TUILE_512, 1024: TUILE_1024, 2048: TUILE_2048,
    4096: TUILE_4096, 8192: TUILE_8192, 16384: TUILE_16384,
    32768: TUILE_32768, 65536: TUILE_65536, 131072: TUILE_131072
}

DIRECTION_ORDER = ["up", "down", "left", "right"]

# ==============================
# 🕹 Cog Game2048
# ==============================

class Game2048(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path("data/public/jeux/data_2048")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.saves = self.load_data()
        self.last_member = None

    @commands.hybrid_command(
        name="2048",
        description="Jouer au jeu 2048"
    )
    async def game_2048(self, ctx: commands.Context):
        """Commande hybride pour jouer au 2048"""
        # Utiliser l'interaction pour les commandes slash, le contexte pour les préfixes
        interaction = ctx.interaction or ctx
        
        # Charger la dernière partie existante ou en démarrer une nouvelle
        user_id = str(ctx.author.id)
        has_save = user_id in self.saves and self.saves[user_id].get("board") is not None
        
        if has_save:
            # Charger la partie existante
            data = self.saves[user_id]
            await self.start_game(
                interaction,
                board=data["board"],
                score=data.get("score", 0),
                new_game=False,
                ctx=ctx
            )
        else:
            # Démarrer une nouvelle partie si aucune sauvegarde n'existe
            await self.start_game(interaction, new_game=True, ctx=ctx)

    def get_save_path(self, user_id):
        """Retourne le chemin du fichier de sauvegarde pour un utilisateur"""
        return self.data_dir / f"{user_id}.json"

    def load_data(self):
        """Charge toutes les sauvegardes des utilisateurs"""
        saves = {}
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            return saves
            
        for filename in self.data_dir.glob("*.json"):
            try:
                user_id = filename.stem
                with open(filename, 'r', encoding='utf-8') as f:
                    saves[user_id] = json.load(f)
            except Exception as e:
                    print(f"Erreur lors du chargement de {filename}: {e}")
        return saves

    def save_user_data(self, user_id, data):
        """Sauvegarde les données d'un utilisateur dans son propre fichier"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            save_path = self.get_save_path(user_id)
            
            # Charger les données existantes pour préserver le meilleur score
            existing_data = {}
            if save_path.exists():
                try:
                    with open(save_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except:
                    pass
            
            # Mettre à jour le meilleur score si nécessaire
            current_score = data.get("score", 0)
            best_score = max(existing_data.get("best_score", 0), current_score)
            
            # Fusionner les données
            save_data = {
                **existing_data,
                **data,
                "best_score": best_score
            }
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False, default=str)
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde pour l'utilisateur {user_id}: {e}")

    def create_board(self):
        """Crée un nouveau plateau de jeu"""
        board = [[0] * SIZE for _ in range(SIZE)]
        self.add_random_tile(board)
        return board

    def add_random_tile(self, board):
        """Ajoute une nouvelle tuile aléatoire sur le plateau"""
        empty_cells = [(i, j) for i in range(SIZE) for j in range(SIZE) if board[i][j] == 0]
        if empty_cells:
            i, j = random.choice(empty_cells)
            board[i][j] = 2 if random.random() < 0.9 else 4
        return board

    def move(self, board, direction):
        """Effectue un mouvement dans la direction spécifiée"""
        moved = False
        score_gain = 0
        
        # Faire une copie du plateau pour le modifier
        new_board = [row[:] for row in board]
        
        if direction in ["left", "right"]:
            for i in range(SIZE):
                # Extraire la ligne sans les zéros
                row = [x for x in new_board[i] if x != 0]
                
                # Inverser la ligne si on va vers la droite
                if direction == "right":
                    row = row[::-1]
                
                # Fusionner les tuiles identiques
                j = 0
                while j < len(row) - 1:
                    if row[j] == row[j+1]:
                        row[j] *= 2
                        score_gain += row[j]
                        row.pop(j+1)
                        row.append(0)  # Ajouter un zéro pour maintenir la longueur
                    j += 1
                
                # Supprimer les zéros ajoutés
                row = [x for x in row if x != 0]
                
                # Compléter avec des zéros
                if direction == "left":
                    row += [0] * (SIZE - len(row))
                else:
                    row = [0] * (SIZE - len(row)) + row[::-1]
                
                # Vérifier si la ligne a changé
                if new_board[i] != row:
                    moved = True
                    new_board[i] = row
        
        elif direction in ["up", "down"]:
            # Traiter les colonnes comme des lignes
            for j in range(SIZE):
                # Extraire la colonne sans les zéros
                col = [new_board[i][j] for i in range(SIZE) if new_board[i][j] != 0]
                
                # Inverser la colonne si on va vers le bas
                if direction == "down":
                    col = col[::-1]
                
                # Fusionner les tuiles identiques
                i = 0
                while i < len(col) - 1:
                    if col[i] == col[i+1]:
                        col[i] *= 2
                        score_gain += col[i]
                        col.pop(i+1)
                        col.append(0)  # Ajouter un zéro pour maintenir la longueur
                    i += 1
                
                # Supprimer les zéros ajoutés
                col = [x for x in col if x != 0]
                
                # Compléter avec des zéros
                if direction == "up":
                    col += [0] * (SIZE - len(col))
                else:
                    col = [0] * (SIZE - len(col)) + col[::-1]
                
                # Mettre à jour la colonne
                for i in range(SIZE):
                    if new_board[i][j] != col[i]:
                        moved = True
                        new_board[i][j] = col[i]
        
        return new_board, moved, score_gain

    async def start_game(self, interaction, board=None, score=0, new_game=False, ctx=None):
        """Démarre ou reprend une partie"""
        # Gérer à la fois les interactions et les contextes de commande
        user = interaction.user if hasattr(interaction, 'user') else ctx.author
        user_id = str(user.id)
        
        # Charger les données existantes ou initialiser
        existing_data = self.saves.get(user_id, {"board": None, "score": 0, "best_score": 0})
        
        # Si nouvelle partie demandée ou pas de sauvegarde valide, réinitialiser le plateau et le score
        if new_game or board is None or not existing_data.get("board"):
            board = self.create_board()
            score = 0
            # Si c'était un game over, on nettoie complètement la sauvegarde
            if new_game and user_id in self.saves:
                del self.saves[user_id]
                save_path = self.get_save_path(user_id)
                if save_path.exists():
                    os.remove(save_path)
        else:
            # Vérifier si la partie précédente était terminée
            if self.is_game_over(existing_data.get("board", [])):
                board = self.create_board()
                score = 0
            else:
                board = existing_data.get("board", board)
                score = existing_data.get("score", score)
        
        # Mettre à jour le meilleur score si nécessaire
        best_score = max(existing_data.get("best_score", 0), score)
        
        save_data = {
            "board": board,
            "score": score,
            "best_score": best_score
        }
        
        # Sauvegarder les données
        self.save_user_data(user_id, save_data)
        self.saves[user_id] = save_data
        
        # Créer et afficher l'interface de jeu
        view = GameView(self, user.id)
        
        # Créer la description avec le score et le meilleur score
        description = (
            f"**Score actuel:** {score} points\n"
            f"**Meilleur score:** {best_score} points\n\n"
            f"{self.render_board(board)}"
        )
        
        # Créer l'embed avec le manager s'il est disponible
        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=interaction.guild if hasattr(interaction, 'guild') else (ctx.guild if ctx else None),
                user=user,
                bot=self.bot,
                title="🎮 2048",
                description=description,
                target_id=interaction.guild.id if hasattr(interaction, 'guild') and interaction.guild else None
            )
        else:
            # Fallback si le manager n'est pas disponible
            embed = discord.Embed(
                title="🎮 2048",
                description=description,
                color=discord.Color.blue()
            )
        
        # Ajouter la miniature
        thumbnail_path = Path(__file__).parent / "assets" / "2048.jpg"
        if thumbnail_path.exists():
            file = discord.File(thumbnail_path, filename="2048.jpg")
            embed.set_thumbnail(url=f"attachment://2048.jpg")
            file_to_send = file
        else:
            file_to_send = None
        
        # Gérer l'envoi du message en fonction du type d'interaction
        try:
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                if file_to_send:
                    await interaction.response.send_message(embed=embed, view=view, file=file_to_send)
                else:
                    await interaction.response.send_message(embed=embed, view=view)
            elif hasattr(interaction, 'followup'):
                if file_to_send:
                    await interaction.followup.send(embed=embed, view=view, file=file_to_send)
                else:
                    await interaction.followup.send(embed=embed, view=view)
            elif ctx:
                if file_to_send:
                    await ctx.send(embed=embed, view=view, file=file_to_send)
                else:
                    await ctx.send(embed=embed, view=view)
            else:
                # Dernier recours
                channel = interaction.channel if hasattr(interaction, 'channel') else None
                if channel:
                    if file_to_send:
                        await channel.send(embed=embed, view=view, file=file_to_send)
                    else:
                        await channel.send(embed=embed, view=view)
        except Exception as e:
            print(f"Erreur lors de l'envoi du message: {e}")
            if ctx:
                await ctx.send("Une erreur est survenue lors de l'affichage du jeu.", ephemeral=True)

    def render_board(self, board):
        """Convertit le plateau en chaîne de caractères avec des emojis"""
        result = []
        for row in board:
            row_str = '# '  # Ajoute le préfixe # au début de chaque ligne
            for cell in row:
                if cell == 0:
                    row_str += '⬜'  # Case vide
                else:
                    emoji = EMOJI_NUMBERS[cell]
                    # Si c'est un emoji personnalisé (commence par <:)
                    if isinstance(emoji, str) and emoji.startswith('<:') and '>' in emoji:
                        row_str += emoji  # Utilise directement l'emoji personnalisé
                    else:
                        row_str += str(emoji)  # Pour les emojis standards
            result.append(row_str)
        return '\n'.join(result)

    def get_tile_summary(self, board):
        """Retourne un résumé des tuiles présentes sur le plateau"""
        flat = [cell for row in board for cell in row if cell != 0]
        count = Counter(flat)
        return '\n'.join(f"{EMOJI_NUMBERS[val]} x{qty}" for val, qty in sorted(count.items(), reverse=True))
        
    def is_game_over(self, board):
        """Vérifie si la partie est terminée (plus de mouvements possibles)"""
        # Vérifier s'il y a des cases vides
        for row in board:
            if 0 in row:
                return False
                
        # Vérifier les fusions possibles horizontalement
        for i in range(SIZE):
            for j in range(SIZE - 1):
                if board[i][j] == board[i][j + 1]:
                    return False
                    
        # Vérifier les fusions Possibles verticalement
        for i in range(SIZE - 1):
            for j in range(SIZE):
                if board[i][j] == board[i + 1][j]:
                    return False
                    
        # Aucun mouvement possible, la partie est terminée
        return True

# ==============================
# 🕹 View Menu Principal
# ==============================

class MainMenu(discord.ui.View):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        self.update_buttons()
    
    def update_buttons(self):
        # Supprimer tous les boutons existants
        self.clear_items()
        
        # Ajouter le bouton Reprendre
        self.add_item(ResumeButton())
        
        # Ajouter le bouton Nouvelle partie si nécessaire
        if hasattr(self, 'show_new_game') and self.show_new_game:
            self.add_item(NewGameButton())
            
        # Ajouter le bouton Classement
        self.add_item(LeaderboardButton())

class ResumeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="♻️ Reprendre la partie",
            style=discord.ButtonStyle.primary,
            row=0
        )
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        user_id = str(interaction.user.id)
        data = view.cog.saves.get(user_id, {})
        
        if data.get("board"):
            await view.cog.start_game(interaction, data["board"], data.get("score", 0))
        else:
            # Si aucune partie en cours, en démarrer une nouvelle
            await view.cog.start_game(interaction, None, 0, new_game=True)

class NewGameButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="🆕 Nouvelle partie",
            style=discord.ButtonStyle.danger,
            row=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        await view.cog.start_game(interaction, None, 0, new_game=True)
        view.show_new_game = False
        view.update_buttons()
        await interaction.response.edit_message(view=view)

class LeaderboardButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            emoji="🏆",
            label="",  # Pas de texte, juste l'emoji
            style=discord.ButtonStyle.secondary,
            row=1,
            custom_id="leaderboard_btn"
        )
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # Créer la vue de classement comme flags.py
            lb_view = LeaderboardView(self.view.cog, interaction)
            await interaction.response.send_message(embed=lb_view.get_embed(interaction), view=lb_view, ephemeral=True)
                
        except Exception as e:
            print(f"Erreur dans le classement: {e}")
            import traceback
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Impossible d'afficher le classement.",
                    ephemeral=True
                )

# ==============================
# 🕹 View Jeu
# ==============================

class GameView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=180)  # Timeout de 3 minutes
        self.cog = cog
        self.user_id = user_id
        
        # Création de la grille 3x3 avec 9 boutons au total
        for row in range(3):
            for col in range(3):
                # Bouton flèche du haut (B1)
                if row == 0 and col == 1:
                    self.add_item(GameButton("⬆️", "up", cog, user_id))
                # Bouton flèche de gauche (A2)
                elif row == 1 and col == 0:
                    self.add_item(GameButton("⬅️", "left", cog, user_id))
                # Bouton de classement (B2)
                elif row == 1 and col == 1:
                    self.add_item(LeaderboardButton())
                # Bouton flèche de droite (C2)
                elif row == 1 and col == 2:
                    self.add_item(GameButton("➡️", "right", cog, user_id))
                # Bouton flèche du bas (B3)
                elif row == 2 and col == 1:
                    self.add_item(GameButton("⬇️", "down", cog, user_id))
                # Boutons vides pour compléter la grille
                else:
                    btn = discord.ui.Button(
                        style=discord.ButtonStyle.secondary,
                        emoji="⬜",
                        label="",
                        disabled=True,
                        row=row
                    )
                    self.add_item(btn)

class GameButton(discord.ui.Button):
    def __init__(self, emoji, direction, cog, user_id):
        super().__init__(
            style=discord.ButtonStyle.primary,
            emoji=emoji,
            label=" ",  # Empty label but required
            row=1 if direction in ["left", "right"] else (0 if direction == "up" else 2)
        )
        self.direction = direction
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Ce n'est pas votre partie !",
                    ephemeral=True
                )
            return

        user_id = str(interaction.user.id)
        data = self.cog.saves.get(user_id)
        
        if not data:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Aucune partie en cours trouvée.",
                    ephemeral=True
                )
            return

        board = data["board"]
        score = data.get("score", 0)
        
        # Logique de mouvement
        new_board, moved, score_gain = self.cog.move(board, self.direction)
        
        if moved:
            # Mettre à jour le score
            score += score_gain
            
            # Ajouter une nouvelle tuile si un mouvement a été effectué
            self.cog.add_random_tile(new_board)
            
            # Mettre à jour le plateau
            board = new_board
            
            # Vérifier si la partie est terminée
            game_over = self.cog.is_game_over(board)
            
            # Mettre à jour le meilleur score si nécessaire
            best_score = data.get("best_score", 0)
            if score > best_score:
                best_score = score
            
            # Sauvegarder l'état
            self.cog.saves[user_id] = {
                "board": board,
                "score": score,
                "best_score": best_score
            }
            self.cog.save_user_data(user_id, self.cog.saves[user_id])
            
            # Créer la description avec le score et le meilleur score
            description = (
                f"**Score: {score} points**\n"
                f"**Meilleur score: {best_score} points**\n\n"
                f"{self.cog.render_board(board)}"
            )
            
            # Créer l'embed avec le manager s'il est disponible
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=interaction.guild,
                    user=interaction.user,
                    bot=self.cog.bot,
                    title=f"{TUILE_2048} 2048" if not game_over else "💀 Game Over!",
                    description=description,
                    target_id=interaction.guild.id if interaction.guild else None
                )
            else:
                # Fallback si le manager n'est pas disponible
                embed = discord.Embed(
                    title=f"{TUILE_2048} 2048" if not game_over else "💀 Game Over!",
                    description=description,
                    color=discord.Color.blue()
                )
            
            # Ajouter la miniature
            thumbnail_path = Path(__file__).parent / "assets" / "2048.jpg"
            if thumbnail_path.exists():
                file = discord.File(thumbnail_path, filename="2048.jpg")
                embed.set_thumbnail(url="attachment://2048.jpg")
                file_to_send = file
            else:
                file_to_send = None
            
            if game_over:
                embed.color = discord.Color.red()
                if file_to_send:
                    await interaction.response.edit_message(embed=embed, view=None, attachments=[file_to_send])
                else:
                    await interaction.response.edit_message(embed=embed, view=None)
                return
                
            if file_to_send:
                await interaction.response.edit_message(embed=embed, view=self.view, attachments=[file_to_send])
            else:
                await interaction.response.edit_message(embed=embed, view=self.view)
        else:
            # Aucun mouvement possible dans cette direction
            await interaction.response.defer()
            await interaction.response.edit_message(embed=embed, view=self.view)

# ==============================
# 🏆 Vue de classement inspirée de flags.py
# ==============================

class LeaderboardView(discord.ui.View):
    def __init__(self, parent_cog, interaction, mode="server"):
        super().__init__(timeout=600)
        self.parent_cog = parent_cog
        self.interaction = interaction
        self.mode = mode
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        self.add_item(discord.ui.Button(label="Serveur", style=discord.ButtonStyle.primary if self.mode=="server" else discord.ButtonStyle.secondary, custom_id="lb_server", emoji="🏢"))
        self.add_item(discord.ui.Button(label="Global", style=discord.ButtonStyle.primary if self.mode=="global" else discord.ButtonStyle.secondary, custom_id="lb_global", emoji="🌍"))

    def get_embed(self, interaction):
        all_stats = []
        for file in self.parent_cog.data_dir.glob("*.json"):
            try:
                uid = int(file.stem)
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    best_score = data.get("best_score", 0)
                    if best_score > 0:
                        all_stats.append({"uid": uid, "best_score": best_score})
            except Exception:
                pass
        
        if self.mode == "server" and interaction.guild:
            member_ids = [m.id for m in interaction.guild.members]
            all_stats = [s for s in all_stats if s["uid"] in member_ids]
            
        all_stats.sort(key=lambda x: x["best_score"], reverse=True)
        user_id = interaction.user.id
        user_rank = next((i for i, s in enumerate(all_stats) if s["uid"] == user_id), -1)
        
        desc = "### 👤 Ton Profil\n"
        if user_rank != -1:
            u_data = all_stats[user_rank]
            desc += f"> **Position :** `#{user_rank + 1}`\n"
            desc += f"> **Meilleur score :** `{u_data['best_score']}` points\n\n"
        else:
            desc += "> *Tu n'as encore aucun score enregistré.*\n\n"
            
        desc += "### 🏆 Top 10\n"
        if not all_stats:
            desc += "*Aucun joueur classé pour le moment.*"
        else:
            for i, s in enumerate(all_stats[:10]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"`#{i+1:02d}`"
                desc += f"{medal} <@{s['uid']}> — **{s['best_score']}** points\n"
                
        title = "🌍 Classement Interserveur" if self.mode == "global" else f"� Classement {interaction.guild.name if interaction.guild else 'Serveur'}"
        
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=interaction.guild, 
                user=interaction.user, 
                bot=self.parent_cog.bot, 
                title=title, 
                description=desc, 
                target_id=interaction.guild.id if interaction.guild else None
            )
        return discord.Embed(title=title, description=desc, color=0xffd700)

    async def interaction_check(self, interaction):
        cid = interaction.data.get('custom_id')
        if cid == "lb_server":
            self.mode = "server"
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(interaction), view=self)
        elif cid == "lb_global":
            self.mode = "global"
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(interaction), view=self)
        return False

async def setup(bot):
    await bot.add_cog(Game2048(bot))
