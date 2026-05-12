import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
import json
import random
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# CONFIGURATION & CONSTANTES
# ==============================================================================
BASE_PATH = Path("data/public/jeux/data_puissance4")
BASE_PATH.mkdir(parents=True, exist_ok=True)

COLUMNS = 7
ROWS = 6
VIDE = "🔵"
PIONS = ["🟡", "🔴"]
HIGHLIGHT = ["🟨", "🟥"]
LAST_MOVE_EMOJI = "🟣" # Couleur violette pour le dernier pion posé
COLONNES = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
EMOJI_VERS_INDEX = {e: i for i, e in enumerate(COLONNES)}

def format_stats_field(data):
    return (f"✨ **Élo :** `{data['elo']}`\n"
            f"🏆 **Victoires :** `{data['wins']}`\n"
            f"🤝 **Nuls :** `{data['draws']}`\n"
            f"💀 **Défaites :** `{data['losses']}`")

# ==============================================================================
# LOGIQUE DU JEU
# ==============================================================================

class Puissance4Game:
    def __init__(self):
        self.tour = 0
        self.plateau = [[VIDE for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.dernier_coup = None # (y, x)
    
    def plateau_texte(self):
        lignes = []
        for y in range(ROWS):
            row_str = ""
            for x in range(COLUMNS):
                # Si c'est le dernier pion posé, on le met en violet
                if self.dernier_coup == (y, x):
                    row_str += LAST_MOVE_EMOJI
                else:
                    row_str += self.plateau[y][x]
            lignes.append(f"# {row_str}")
        lignes.append(f"# {''.join(COLONNES)}")
        return "\n".join(lignes)
    
    def poser_jeton(self, col):
        for y in reversed(range(ROWS)):
            if self.plateau[y][col] == VIDE:
                self.plateau[y][col] = PIONS[self.tour]
                self.dernier_coup = (y, col)
                return y, col
        return None, None

    def check_victory(self):
        if not self.dernier_coup: return False, []
        r, c = self.dernier_coup
        pion = PIONS[self.tour]
        for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
            positions = [(r, c)]
            for d in [1, -1]:
                nr, nc = r + dr*d, c + dc*d
                while 0 <= nr < ROWS and 0 <= nc < COLUMNS and self.plateau[nr][nc] == pion:
                    positions.append((nr, nc))
                    nr += dr*d
                    nc += dc*d
            if len(positions) >= 4:
                return True, positions[:4]
        return False, []

    def est_plein(self):
        return all(self.plateau[0][c] != VIDE for c in range(COLUMNS))

########################################
# Boutons et Composants
########################################

class ServerLBButton(ui.Button):
    def __init__(self, active):
        super().__init__(label="Serveur", style=discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary, emoji="🏢")
    async def callback(self, interaction: discord.Interaction):
        await self.view.server_callback(interaction)

class GlobalLBButton(ui.Button):
    def __init__(self, active):
        super().__init__(label="Global", style=discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary, emoji="🌍")
    async def callback(self, interaction: discord.Interaction):
        await self.view.global_callback(interaction)

class LobbyLBButton(ui.Button):
    def __init__(self):
        super().__init__(label="Classement", emoji="🏆", style=discord.ButtonStyle.gray, row=0)
    async def callback(self, interaction: discord.Interaction):
        await self.view.lb_lobby_callback(interaction)

class GameLBButton(ui.Button):
    def __init__(self):
        super().__init__(emoji="🏆", label="Classement", style=discord.ButtonStyle.gray, row=3)
    async def callback(self, interaction: discord.Interaction):
        await self.view.lb_game_callback(interaction)

class JoinButton(ui.Button):
    def __init__(self):
        super().__init__(label="Rejoindre", style=discord.ButtonStyle.primary, emoji="🎮", row=0)
    async def callback(self, interaction: discord.Interaction):
        await self.view.join_callback(interaction)

########################################
# Menu avancé de classement inspiré de master.py
########################################

class P4LeaderboardView(ui.View):
    def __init__(self, parent_cog, interaction, mode="server"):
        super().__init__(timeout=600)
        self.parent_cog = parent_cog
        self.interaction = interaction
        self.mode = mode
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        self.add_item(ServerLBButton(self.mode == "server"))
        self.add_item(GlobalLBButton(self.mode == "global"))

    def get_embed(self, interaction: discord.Interaction):
        all_stats = []
        for file in self.parent_cog.data_dir.glob("*.json"):
            try:
                uid = int(file.stem)
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("wins", 0) + data.get("losses", 0) > 0:
                        data["uid"] = uid
                        all_stats.append(data)
            except Exception:
                pass
        
        if self.mode == "server" and interaction.guild:
            member_ids = [m.id for m in interaction.guild.members]
            all_stats = [s for s in all_stats if s["uid"] in member_ids]
            
        all_stats.sort(key=lambda x: x["elo"], reverse=True)
        user_id = interaction.user.id
        user_rank = next((i for i, s in enumerate(all_stats) if s["uid"] == user_id), -1)
        
        desc = "### 👤 Ton Profil\n"
        if user_rank != -1:
            u_data = all_stats[user_rank]
            desc += f"> **Position :** `#{user_rank + 1}`\n"
            desc += f"> **Élo :** `{u_data['elo']}` | **V/D :** `{u_data['wins']}V` / `{u_data['losses']}D`\n\n"
        else:
            desc += "> *Tu n'as encore terminé aucune partie classée.*\n\n"
            
        desc += "### 🏆 Top 10\n"
        if not all_stats:
            desc += "*Aucun joueur classé pour le moment.*"
        else:
            for i, s in enumerate(all_stats[:10]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"`#{i+1:02d}`"
                desc += f"{medal} <@{s['uid']}> — **{s['elo']}** Élo (`{s['wins']}V` / `{s['losses']}D`)\n"
                
        title = "🌍 Classement Interserveur" if self.mode == "global" else f"🏢 Classement {interaction.guild.name if interaction.guild else 'Serveur'}"
        return self.parent_cog.create_base_embed(interaction, title, desc)

    async def server_callback(self, interaction: discord.Interaction):
        self.mode = "server"
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(interaction), view=self)

    async def global_callback(self, interaction: discord.Interaction):
        self.mode = "global"
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(interaction), view=self)

# ==============================================================================
# VIEWS
# ==============================================================================

class P4LobbyView(ui.View):
    def __init__(self, parent_cog, host_user, ctx):
        super().__init__(timeout=180)
        self.parent_cog, self.host_user, self.ctx = parent_cog, host_user, ctx
        self.waiting_list = []

    def get_lobby_embed(self):
        desc = (f"👤 **Hôte :** {self.host_user.mention}\n\n"
                f"👥 **Candidats prêts :**\n" + 
                ("\n".join([f"• <@{uid}>" for uid in self.waiting_list]) if self.waiting_list else "*En attente de joueurs...*"))
        return self.parent_cog.create_base_embed(self.ctx, "⏳ Salon Puissance 4", desc)

    async def update_lobby(self, interaction: discord.Interaction = None):
        self.clear_items()
        self.add_item(JoinButton())
        self.add_item(LobbyLBButton())
        
        if len(self.waiting_list) >= 1:
            options = [discord.SelectOption(label=self.ctx.guild.get_member(uid).display_name, value=str(uid), emoji="🤺") 
                       for uid in self.waiting_list if self.ctx.guild.get_member(uid)]
            if options:
                select = ui.Select(placeholder="Choisis ton adversaire...", options=options, row=1)
                select.callback = self.select_start_callback
                self.add_item(select)

        embed = self.get_lobby_embed()
        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        return embed

    async def join_callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.host_user.id: 
            return await interaction.response.send_message("Tu es déjà l'hôte !", ephemeral=True)
        if interaction.user.id not in self.waiting_list:
            self.waiting_list.append(interaction.user.id)
            await self.update_lobby(interaction)
        else: await interaction.response.send_message("Déjà inscrit !", ephemeral=True)

    async def select_start_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.host_user.id:
            return await interaction.response.send_message("❌ Seul l'hôte peut lancer !", ephemeral=True)
        opponent = self.ctx.guild.get_member(int(interaction.data['values'][0]))
        await self.parent_cog.start_game(interaction, self.host_user, opponent)

    async def lb_lobby_callback(self, interaction: discord.Interaction):
        lb_view = P4LeaderboardView(self.parent_cog, interaction)
        await interaction.response.send_message(embed=lb_view.get_embed(interaction), view=lb_view, ephemeral=True)

class P4GameView(ui.View):
    def __init__(self, parent_cog, joueurs, ctx):
        super().__init__(timeout=600)
        self.parent_cog, self.joueurs, self.ctx = parent_cog, joueurs, ctx
        self.add_item(GameLBButton())

    async def lb_game_callback(self, interaction: discord.Interaction):
        lb_view = P4LeaderboardView(self.parent_cog, interaction)
        await interaction.response.send_message(embed=lb_view.get_embed(interaction), view=lb_view, ephemeral=True)

# ==============================================================================
# COG PRINCIPALE
# ==============================================================================

class Puissance4(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path("data/public/jeux/data_puissance4")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.active_games = {} # msg_id: {game_obj, players_list, view_obj}

    def create_base_embed(self, source, title, description):
        guild = source.guild if hasattr(source, 'guild') else None
        user = source.user if hasattr(source, 'user') else (source.author if hasattr(source, 'author') else None)
        if config_manager:
            return config_manager.get_formatted_embed(guild=guild, user=user, bot=self.bot, title=title, description=description, target_id=guild.id if guild else None)
        return discord.Embed(title=title, description=description, color=0x2b2d31)

    def get_user_data(self, uid):
        path = self.data_dir / f"{uid}.json"
        d = {"wins": 0, "losses": 0, "draws": 0, "elo": 1000}
        if path.exists():
            try:
                with open(path, "r", encoding='utf-8') as f: d.update(json.load(f))
            except: pass
        return d

    def update_stats(self, wid, lid, draw):
        w, l = self.get_user_data(wid), self.get_user_data(lid)
        ew, el = 1/(1+10**((l['elo']-w['elo'])/400)), 1/(1+10**((w['elo']-l['elo'])/400))
        if draw:
            w['draws']+=1; l['draws']+=1
            w['elo']+=round(32*(0.5-ew)); l['elo']+=round(32*(0.5-el))
        else:
            w['wins']+=1; l['losses']+=1
            diff = round(32*(1-ew))
            w['elo']+=diff; l['elo']-=diff
        with open(self.data_dir/f"{wid}.json", "w", encoding='utf-8') as f: json.dump(w, f)
        with open(self.data_dir/f"{lid}.json", "w", encoding='utf-8') as f: json.dump(l, f)

    @commands.hybrid_command(name="puissance4", description="Ouvre un salon de Puissance 4")
    async def puissance4(self, ctx: commands.Context):
        try:
            view = P4LobbyView(self, ctx.author, ctx)
            embed = await view.update_lobby()
            msg = await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            print(f"[DEBUG P4] Erreur dans puissance4: {e}")
            import traceback
            traceback.print_exc()
            await ctx.send(f"❌ Erreur lors de l'ouverture du salon Puissance 4: {str(e)}", ephemeral=True)

    async def start_game(self, interaction, p1, p2):
        game = Puissance4Game()
        players = [p1, p2]
        random.shuffle(players)
        
        view = P4GameView(self, players, interaction)
        embed = self.get_game_embed(interaction, game, players, f"🎮 Début du match ! Au tour de {players[0].display_name}")
        
        await interaction.response.edit_message(embed=embed, view=view)
        msg = await interaction.original_response()
        
        for emoji in COLONNES:
            await msg.add_reaction(emoji)
            
        self.active_games[msg.id] = {"game": game, "players": players, "view": view, "processing": False}

    def get_game_embed(self, source, game, players, status, final=False):
        s0, s1 = self.get_user_data(players[0].id), self.get_user_data(players[1].id)
        embed = self.create_base_embed(source, "🎮 Match Puissance 4", f"### {status}\n\n{game.plateau_texte()}")
        
        mark = " ⬅️ **SON TOUR**"
        embed.add_field(name=f"🟡 {players[0].display_name}{mark if game.tour == 0 and not final else ''}", value=format_stats_field(s0), inline=True)
        embed.add_field(name=f"🔴 {players[1].display_name}{mark if game.tour == 1 and not final else ''}", value=format_stats_field(s1), inline=True)
        return embed

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot or reaction.message.id not in self.active_games: return
        if str(reaction.emoji) not in COLONNES: return

        data = self.active_games[reaction.message.id]
        game, players = data["game"], data["players"]
        
        # Vérification tour
        if user.id != players[game.tour].id:
            return await reaction.remove(user)

        if data["processing"]: return
        data["processing"] = True

        col = EMOJI_VERS_INDEX[str(reaction.emoji)]
        y, x = game.poser_jeton(col)

        if y is None: # Colonne pleine
            data["processing"] = False
            return await reaction.remove(user)

        await reaction.remove(user)
        
        win, line = game.check_victory()
        
        if win:
            # Colorer la ligne gagnante
            for ly, lx in line:
                game.plateau[ly][lx] = HIGHLIGHT[game.tour]
            game.dernier_coup = None # On enlève le violet pour le rendu final
            self.update_stats(players[game.tour].id, players[1-game.tour].id, False)
            embed = self.get_game_embed(reaction.message, game, players, f"🎉 Victoire de {players[game.tour].mention} !", final=True)
            await reaction.message.edit(embed=embed)
            await reaction.message.clear_reactions()
            del self.active_games[reaction.message.id]
        elif game.est_plein():
            game.dernier_coup = None
            self.update_stats(players[0].id, players[1].id, True)
            embed = self.get_game_embed(reaction.message, game, players, "🤝 Match nul !", final=True)
            await reaction.message.edit(embed=embed)
            await reaction.message.clear_reactions()
            del self.active_games[reaction.message.id]
        else:
            game.tour = 1 - game.tour
            embed = self.get_game_embed(reaction.message, game, players, f"⏳ Au tour de {players[game.tour].display_name}")
            await reaction.message.edit(embed=embed)
            data["processing"] = False

async def setup(bot):
    await bot.add_cog(Puissance4(bot))