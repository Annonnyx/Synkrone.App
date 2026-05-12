import discord
from discord.ext import commands
import random
import json
import traceback
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

COLORS = [("🔴", "Rouge"), ("🔵", "Bleu"), ("🟢", "Vert"), ("🟡", "Jaune")]

def format_stats_field(data):
    return (f"✨ **Élo :** `{data['elo']}`\n"
            f"📊 **V/D :** `{data['wins']}`/`{data['losses']}`")

########################################
# Logique de Jeu Mastermind
########################################

class MastermindGame:
    def __init__(self):
        self.secret = random.choices(COLORS, k=4)
        self.attempts = []

    def check_combination(self, guess):
        exact = sum(g == s for g, s in zip(guess, self.secret))
        rem_s = [s for g, s in zip(guess, self.secret) if g != s]
        rem_g = [g for g, s in zip(guess, self.secret) if g != s]
        partial = 0
        for g in rem_g:
            if g in rem_s:
                partial += 1
                rem_s.remove(g)
        return exact, partial

########################################
# Boutons et Composants
########################################

class ServerLBButton(discord.ui.Button):
    def __init__(self, active):
        super().__init__(label="Serveur", style=discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary, emoji="🏢")
    async def callback(self, interaction: discord.Interaction):
        await self.view.server_callback(interaction)

class GlobalLBButton(discord.ui.Button):
    def __init__(self, active):
        super().__init__(label="Global", style=discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary, emoji="🌍")
    async def callback(self, interaction: discord.Interaction):
        await self.view.global_callback(interaction)

class JoinButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Rejoindre", style=discord.ButtonStyle.primary, emoji="🎮", row=0)
    async def callback(self, interaction: discord.Interaction):
        await self.view.join_callback(interaction)

class SoloButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Jouer Solo", style=discord.ButtonStyle.secondary, emoji="🕹️", row=0)
    async def callback(self, interaction: discord.Interaction):
        await self.view.solo_callback(interaction)

class LobbyLBButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Classement", emoji="🏆", style=discord.ButtonStyle.gray, row=2)
    async def callback(self, interaction: discord.Interaction):
        await self.view.lb_lobby_callback(interaction)

class OpponentSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Choisir un adversaire...", options=options, row=1)
    async def callback(self, interaction: discord.Interaction):
        await self.view.start_duel_callback(interaction, self.values)

class ResetButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="🔄", label="Reset", style=discord.ButtonStyle.danger, row=1, disabled=True)
    async def callback(self, interaction: discord.Interaction):
        await self.view.reset_callback(interaction)

class GameLBButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="🏆", label="Classement", style=discord.ButtonStyle.gray, row=1)
    async def callback(self, interaction: discord.Interaction):
        await self.view.lb_game_callback(interaction)

class MasterButton(discord.ui.Button):
    def __init__(self, emoji, name, row):
        super().__init__(label=name, emoji=emoji, style=discord.ButtonStyle.primary, row=row)
        self.color_data = (emoji, name)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if interaction.user.id != view.turn.id:
            return await interaction.response.send_message(f"⚠️ C'est au tour de {view.turn.display_name} !", ephemeral=True)

        if len(view.current_guess) >= 4:
            return await interaction.response.defer()

        view.current_guess.append(self.color_data)
        view.btn_reset.disabled = False
        
        if len(view.current_guess) == 4:
            await view.next_turn(interaction)
        else:
            await interaction.response.edit_message(embed=view.get_game_embed(), view=view)

########################################
# Base View avec Gestion d'erreurs
########################################

class BaseSafeView(discord.ui.View):
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        print(f"Erreur UI attrapée : {error}")
        traceback.print_exc()
        err_msg = f"⚠️ Oups, une erreur est survenue en arrière-plan : `{error}`"
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(err_msg, ephemeral=True)
            else:
                await interaction.followup.send(err_msg, ephemeral=True)
        except:
            pass

########################################
# View du Classement Éphémère
########################################

class LeaderboardView(BaseSafeView):
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

########################################
# View du Lobby
########################################

class MasterLobbyView(BaseSafeView):
    def __init__(self, parent_cog, host_user, ctx):
        super().__init__(timeout=600)
        self.parent_cog = parent_cog
        self.host_user = host_user
        self.ctx = ctx
        self.waiting_list = []

    def get_lobby_embed(self):
        desc = (f"👤 **Hôte :** {self.host_user.mention}\n\n"
                f"🧠 **Mode :** Duel Mastermind\n\n"
                f"👥 **Candidats en attente :**\n" + 
                ("\n".join([f"• <@{uid}>" for uid in self.waiting_list]) if self.waiting_list else "> *En attente d'adversaires...*"))
        return self.parent_cog.create_base_embed(self.ctx, "⏳ Salon Mastermind", desc)

    async def update_lobby(self, interaction: discord.Interaction = None):
        self.clear_items()
        self.add_item(JoinButton())
        self.add_item(SoloButton())
        self.add_item(LobbyLBButton())

        if self.waiting_list:
            options = []
            for uid in self.waiting_list[:25]:
                member = self.ctx.guild.get_member(uid) if self.ctx.guild else self.parent_cog.bot.get_user(uid)
                name = member.display_name if member else f"Joueur inconnu ({uid})"
                options.append(discord.SelectOption(label=name[:100], value=str(uid), emoji="⚔️"))
            if options:
                self.add_item(OpponentSelect(options))

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
        else:
            await interaction.response.send_message("Tu es déjà inscrit !", ephemeral=True)

    async def solo_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.host_user.id:
            return await interaction.response.send_message("Seul l'hôte peut lancer le solo.", ephemeral=True)
        
        game_view = MasterView(self.parent_cog, self.host_user, ctx=self.ctx)
        embed = game_view.get_game_embed()
        
        # On évite d'utiliser content=None qui peut faire bugger les vieilles API Discord
        await interaction.response.edit_message(embed=embed, view=game_view)

    async def start_duel_callback(self, interaction: discord.Interaction, values):
        if interaction.user.id != self.host_user.id:
            return await interaction.response.send_message("Seul l'hôte peut choisir l'adversaire.", ephemeral=True)
        
        target_id = int(values[0])
        target = self.ctx.guild.get_member(target_id) if self.ctx.guild else self.parent_cog.bot.get_user(target_id)
        
        if not target:
            return await interaction.response.send_message("❌ Joueur introuvable.", ephemeral=True)
        
        players = [self.host_user, target]
        random.shuffle(players)
        p1, p2 = players[0], players[1]
        
        game_view = MasterView(self.parent_cog, player1=p1, player2=p2, ctx=self.ctx)
        await interaction.response.edit_message(content=f"🔔 {game_view.turn.mention}, c'est à toi de commencer !", embed=game_view.get_game_embed(), view=game_view)

    async def lb_lobby_callback(self, interaction: discord.Interaction):
        lb_view = LeaderboardView(self.parent_cog, interaction)
        await interaction.response.send_message(embed=lb_view.get_embed(interaction), view=lb_view, ephemeral=True)

########################################
# View du Jeu Mastermind
########################################

class MasterView(BaseSafeView):
    def __init__(self, parent_cog, player1, player2=None, ctx=None):
        super().__init__(timeout=600)
        self.parent_cog = parent_cog
        self.game = MastermindGame()
        self.player1 = player1
        self.player2 = player2
        self.ctx = ctx
        self.turn = player1
        self.current_guess = []
        self.max_attempts = 12
        self.is_final = False
        self.setup_buttons()

    def setup_buttons(self):
        self.clear_items()
        for emoji, name in COLORS:
            self.add_item(MasterButton(emoji, name, row=0))
        self.btn_reset = ResetButton()
        self.add_item(self.btn_reset)
        self.btn_lb = GameLBButton()
        self.add_item(self.btn_lb)

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

    async def reset_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.turn.id:
            return await interaction.response.send_message("Ce n'est pas ton tour !", ephemeral=True)
        self.current_guess.clear()
        self.btn_reset.disabled = True
        
        if self.player2:
            await interaction.response.edit_message(content=f"🔔 {self.turn.mention}, c'est ton tour !", embed=self.get_game_embed(), view=self)
        else:
            await interaction.response.edit_message(embed=self.get_game_embed(), view=self)

    async def lb_game_callback(self, interaction: discord.Interaction):
        lb_view = LeaderboardView(self.parent_cog, interaction)
        await interaction.response.send_message(embed=lb_view.get_embed(interaction), view=lb_view, ephemeral=True)

    def get_game_embed(self, status_msg="🎮 Match en cours"):
        history = ""
        for i, (player, guess) in enumerate(self.game.attempts):
            emotes = "".join([e[0] for e in guess])
            ex, pa = self.game.check_combination(guess)
            p_name = f" | **{player.display_name[:10]}**" if self.player2 else ""
            history += f"`{i+1:02d}` | {emotes} | 🔘 `{ex}` ⚪ `{pa}`{p_name}\n"

        selection = "".join([c[0] for c in self.current_guess]).ljust(4, "⬛")
        embed = self.parent_cog.create_base_embed(self.ctx, "🧠 Mastermind Challenge", f"### {status_msg}\n\n📜 **Historique :**\n{history or '> *En attente du premier essai...*'}")
        
        if self.player2:
            s1 = self.parent_cog.get_user_data(self.player1.id)
            tour_mark = " ⬅️ **TOUR**"
            embed.add_field(name=f"⭕ {self.player1.display_name}{tour_mark if self.turn == self.player1 and not self.is_final else ''}", value=format_stats_field(s1), inline=True)
            
            s2 = self.parent_cog.get_user_data(self.player2.id)
            embed.add_field(name=f"❌ {self.player2.display_name}{tour_mark if self.turn == self.player2 and not self.is_final else ''}", value=format_stats_field(s2), inline=True)

        embed.add_field(name="🎨 Ta sélection", value=f"`{selection}`", inline=False)
        
        regles = "🔘 **Bien placé** (Couleur & Position)\n⚪ **Mal placé** (Bonne couleur, Mauvaise position)\n"
        regles += f"🎯 **Essais max :** `{self.max_attempts}`"
        embed.add_field(name="📋 Règles du jeu", value=regles, inline=False)
        
        game_footer_text = "Devine la bonne combinaison pour remporter la victoire !"
        
        try:
            existing_text = getattr(embed.footer, "text", None)
            existing_icon = getattr(embed.footer, "icon_url", None)
            
            is_empty_text = not existing_text or existing_text == discord.Embed.Empty
            is_empty_icon = not existing_icon or existing_icon == discord.Embed.Empty
            
            new_text = game_footer_text if is_empty_text else f"{game_footer_text} | {existing_text}"
            
            new_icon = existing_icon
            if is_empty_icon and getattr(self.parent_cog.bot.user, "display_avatar", None):
                new_icon = self.parent_cog.bot.user.display_avatar.url

            if new_icon:
                embed.set_footer(text=new_text, icon_url=new_icon)
            else:
                embed.set_footer(text=new_text)
        except Exception:
            pass # Securité si embed.footer cause une erreur inattendue
            
        return embed

    async def next_turn(self, interaction: discord.Interaction):
        self.game.attempts.append((self.turn, list(self.current_guess)))
        exact, _ = self.game.check_combination(self.current_guess)
        
        if exact == 4:
            self.is_final = True
            if self.player2: 
                loser = self.player2 if self.turn == self.player1 else self.player1
                self.parent_cog.update_stats(self.turn.id, loser.id)
            self.disable_all_items()
            await interaction.response.edit_message(embed=self.get_game_embed(f"🎉 VICTOIRE de {self.turn.display_name} !"), view=self)
            return

        if len(self.game.attempts) >= self.max_attempts:
            self.is_final = True
            secret_str = "".join([e[0] for e in self.game.secret])
            self.disable_all_items()
            await interaction.response.edit_message(embed=self.get_game_embed(f"🔚 DÉFAITE ! Le secret était : {secret_str}"), view=self)
            return

        self.current_guess.clear()
        self.btn_reset.disabled = True
        
        if self.player2: 
            self.turn = self.player2 if self.turn == self.player1 else self.player1
            await interaction.response.edit_message(content=f"🔔 {self.turn.mention}, c'est ton tour !", embed=self.get_game_embed(), view=self)
        else:
            await interaction.response.edit_message(embed=self.get_game_embed(), view=self)


########################################
# Cog Mastermind
########################################

class Mastermind(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path("./data/public/jeux/data_mastermind")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def create_base_embed(self, source, title, description):
        guild = getattr(source, 'guild', None)
        user = getattr(source, 'user', getattr(source, 'author', None))
        
        # Bloc Try/Except pour empêcher un crash silencieux venant du config_manager
        if config_manager:
            try:
                return config_manager.get_formatted_embed(
                    guild=guild, user=user, bot=self.bot, 
                    title=title, description=description, 
                    target_id=guild.id if guild else None
                )
            except Exception as e:
                print(f"[Mastermind] Erreur Config Manager : {e}")
                
        return discord.Embed(title=title, description=description, color=0x2b2d31)

    def get_user_data(self, uid):
        path = self.data_dir / f"{uid}.json"
        d = {"wins": 0, "losses": 0, "elo": 1000}
        if path.exists():
            try:
                with open(path, "r", encoding='utf-8') as f:
                    d.update(json.load(f))
            except Exception as e:
                pass
        else:
            try:
                self.data_dir.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding='utf-8') as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
            except Exception as e:
                pass
        return d

    def update_stats(self, wid, lid):
        w, l = self.get_user_data(wid), self.get_user_data(lid)
        ew = 1/(1+10**((l['elo']-w['elo'])/400))
        el = 1/(1+10**((w['elo']-l['elo'])/400))
        w['wins'] += 1; l['losses'] += 1
        diff = round(32*(1-ew))
        
        w['elo'] += diff
        l['elo'] = max(0, l['elo'] - diff)
        
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.data_dir/f"{wid}.json", "w", encoding='utf-8') as f:
                json.dump(w, f, ensure_ascii=False, indent=2)
            with open(self.data_dir/f"{lid}.json", "w", encoding='utf-8') as f:
                json.dump(l, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @commands.hybrid_command(name="mastermind", aliases=["master"])
    async def mastermind(self, ctx):
        """Lance un salon pour jouer au Mastermind (Solo ou Duel)."""
        view = MasterLobbyView(self, ctx.author, ctx)
        embed = await view.update_lobby()
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Mastermind(bot))