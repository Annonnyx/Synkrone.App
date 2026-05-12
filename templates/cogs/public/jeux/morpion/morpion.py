import discord
from discord.ext import commands
import json
import random
import asyncio
import traceback
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

EMOJIS_POS = ["↖️", "⬆️", "↗️", "⬅️", "🎯", "➡️", "↙️", "⬇️", "↘️"]
JOUEURS_SYM = ["⭕", "❌"]

def format_stats_field(data):
    return (f"✨ **Élo :** `{data['elo']}`\n"
            f"🏆 **Victoires :** `{data['wins']}`\n"
            f"🤝 **Nuls :** `{data['draws']}`\n"
            f"💀 **Défaites :** `{data['losses']}`")

########################################
# View du Lobby
########################################


# Nouveau leaderboard/profil inspiré de Mastermind
class MorpionLeaderboardView(discord.ui.View):
    def __init__(self, cog, interaction, mode="server"):
        super().__init__(timeout=600)
        self.cog = cog
        self.interaction = interaction
        self.mode = mode
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        self.add_item(discord.ui.Button(label="Serveur", style=discord.ButtonStyle.primary if self.mode=="server" else discord.ButtonStyle.secondary, custom_id="lb_server", emoji="🏢"))
        self.add_item(discord.ui.Button(label="Global", style=discord.ButtonStyle.primary if self.mode=="global" else discord.ButtonStyle.secondary, custom_id="lb_global", emoji="🌍"))

    def get_embed(self, interaction):
        all_stats = []
        for file in self.cog.data_dir.glob("*.json"):
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
        return self.cog.create_base_embed(interaction, title, desc)

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

class MorpionLobbyView(discord.ui.View):
    def __init__(self, parent_cog, host_user, ctx):
        super().__init__(timeout=600)
        self.parent_cog = parent_cog
        self.host_user = host_user
        self.ctx = ctx
        self.waiting_list = []
        self.update_lobby()

    def get_lobby_embed(self):
        desc = (f"👤 **Hôte :** {self.host_user.mention}\n\n"
                f"🧠 **Mode :** Duel Morpion\n\n"
                f"👥 **Candidats en attente :**\n" + 
                ("\n".join([f"• <@{uid}>" for uid in self.waiting_list]) if self.waiting_list else "> *En attente d'adversaires...*"))
        return self.parent_cog.create_base_embed(self.ctx, "⏳ Salon Morpion", desc)

    def update_lobby(self, interaction=None):
        self.clear_items()
        self.add_item(discord.ui.Button(label="Rejoindre", style=discord.ButtonStyle.primary, custom_id="join", emoji="🎮"))
        self.add_item(discord.ui.Button(label="Classement", style=discord.ButtonStyle.gray, custom_id="lb", emoji="🏆"))
        if self.waiting_list:
            options = []
            for uid in self.waiting_list[:25]:
                member = self.ctx.guild.get_member(uid) if self.ctx.guild else self.parent_cog.bot.get_user(uid)
                name = member.display_name if member else f"Joueur inconnu ({uid})"
                options.append(discord.SelectOption(label=name[:100], value=str(uid), emoji="⚔️"))
            if options:
                self.add_item(discord.ui.Select(placeholder="Choisir l'adversaire...", options=options, custom_id="select_adv"))

    async def interaction_check(self, interaction: discord.Interaction):
        cid = interaction.data.get('custom_id')
        if cid == "join":
            if interaction.user.id == self.host_user.id:
                return await interaction.response.send_message("Tu es déjà l'hôte !", ephemeral=True)
            if interaction.user.id not in self.waiting_list:
                self.waiting_list.append(interaction.user.id)
                self.update_lobby()
                await interaction.response.edit_message(embed=self.get_lobby_embed(), view=self)
            else:
                await interaction.response.send_message("Tu es déjà inscrit !", ephemeral=True)
        elif cid == "lb":
            lb_view = MorpionLeaderboardView(self.parent_cog, interaction)
            await interaction.response.send_message(embed=lb_view.get_embed(interaction), view=lb_view, ephemeral=True)
        elif cid == "select_adv":
            if interaction.user.id != self.host_user.id:
                return await interaction.response.send_message("Seul l'hôte peut choisir l'adversaire.", ephemeral=True)
            target_id = int(interaction.data['values'][0])
            target = self.ctx.guild.get_member(target_id) if self.ctx.guild else await self.parent_cog.bot.fetch_user(target_id)
            if not target:
                return await interaction.response.send_message("❌ Joueur introuvable.", ephemeral=True)
            self.stop()
            players = [self.host_user, target]
            random.shuffle(players)
            game_view = MorpionView(self.parent_cog, players, self.ctx)
            game_view.create_grid()
            await game_view.update_message(interaction, f"🎮 La partie commence !", is_start=True)
        return False

########################################
# View du Jeu
########################################

class MorpionView(discord.ui.View):
    def __init__(self, parent_cog, joueurs, ctx):
        super().__init__(timeout=600)
        self.parent_cog, self.joueurs, self.ctx = parent_cog, joueurs, ctx
        self.tour, self.grille = 0, EMOJIS_POS.copy()

    def create_grid(self, final=False):
        self.clear_items()
        # Grille (Lignes 0, 1, 2)
        for i in range(9):
            style = discord.ButtonStyle.secondary if self.grille[i] in EMOJIS_POS else discord.ButtonStyle.primary
            btn = discord.ui.Button(label=self.grille[i], style=style, row=i//3, disabled=final)
            btn.callback = self.make_callback(i)
            self.add_item(btn)
        # Bouton fusionné profil+classement (ligne 3)
        btn_lb = discord.ui.Button(emoji="🏆", label=None, style=discord.ButtonStyle.gray, row=3)
        btn_lb.callback = self.lb_game_callback
        self.add_item(btn_lb)

    async def lb_game_callback(self, interaction):
        lb_view = MorpionLeaderboardView(self.parent_cog, interaction)
        await interaction.response.send_message(embed=lb_view.get_embed(interaction), view=lb_view, ephemeral=True)

    def make_callback(self, pos):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.joueurs[self.tour].id:
                return await interaction.response.send_message(f"❌ C'est le tour de {self.joueurs[self.tour].display_name} !", ephemeral=True)
            
            if self.grille[pos] in JOUEURS_SYM: return
            
            self.grille[pos] = JOUEURS_SYM[self.tour]
            win, line = self.check_victory(JOUEURS_SYM[self.tour])
            
            if win:
                self.parent_cog.update_stats(self.joueurs[self.tour].id, self.joueurs[1-self.tour].id, False)
                await self.update_message(interaction, f"🎉 Victoire de {self.joueurs[self.tour].mention} !", final=True, win_line=line)
            elif all(c in JOUEURS_SYM for c in self.grille):
                self.parent_cog.update_stats(self.joueurs[0].id, self.joueurs[1].id, True)
                await self.update_message(interaction, "🤝 Match nul !", final=True)
            else:
                self.tour = 1 - self.tour
                await self.update_message(interaction, f"⏳ Au tour de {self.joueurs[self.tour].display_name}")
        return callback

    def check_victory(self, p):
        l = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
        for x in l:
            if all(self.grille[i] == p for i in x): return True, x
        return False, []

    async def update_message(self, interaction, content, final=False, win_line=[], is_start=False):
        self.create_grid(final=final)
        
        if final and win_line:
            # Colorer la ligne gagnante en vert (les boutons sont indexés de 0 à 8 dans la view)
            for i in win_line:
                self.children[i].style = discord.ButtonStyle.success

        s0 = self.parent_cog.get_user_data(self.joueurs[0].id)
        s1 = self.parent_cog.get_user_data(self.joueurs[1].id)

        embed = self.parent_cog.create_base_embed(interaction, "🎮 Match Morpion", f"### {content}")
        
        tour_mark = " ⬅️ **SON TOUR**"
        embed.add_field(
            name=f"⭕ {self.joueurs[0].display_name}{tour_mark if self.tour == 0 and not final else ''}",
            value=format_stats_field(s0),
            inline=True
        )
        embed.add_field(
            name=f"❌ {self.joueurs[1].display_name}{tour_mark if self.tour == 1 and not final else ''}",
            value=format_stats_field(s1),
            inline=True
        )

        if is_start or not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.edit_original_response(embed=embed, view=self)

        # Notification par tag
        if not final:
            try:
                tag = await interaction.channel.send(f"🔔 {self.joueurs[self.tour].mention}, à toi de jouer !")
                await asyncio.sleep(2.5)
                await tag.delete()
            except: pass

########################################
# Cog Morpion
########################################

class Morpion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Nouveau chemin de data
        self.data_dir = Path("data/public/jeux/data_morpion")
        self.data_dir.mkdir(parents=True, exist_ok=True)

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
                with open(path, "r", encoding='utf-8') as f:
                    d.update(json.load(f))
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

    @commands.hybrid_command(name="morpion", description="Ouvre un salon de Morpion")
    async def morpion(self, ctx: commands.Context):
        view = MorpionLobbyView(self, ctx.author, ctx)
        embed = view.get_lobby_embed()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Morpion(bot))