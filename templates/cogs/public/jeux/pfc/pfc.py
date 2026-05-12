import discord
from discord.ext import commands
from discord import ui
import json
import io
import aiohttp
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps

# Importation du manager comme dans ton pingpong.py
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None


# ==========================================
# GESTION DES DONNÉES (anciennement util_data.py)
# ==========================================

class EloManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_user_data(self, user_id: int):
        file = self.data_dir / f"{user_id}.json"
        if file.exists():
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"elo": 1000, "wins": 0, "losses": 0, "draws": 0}

    def save_user_data(self, user_id: int, data: dict):
        with open(self.data_dir / f"{user_id}.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def update_match(self, p1_id, p2_id, result):
        p1, p2 = self.get_user_data(p1_id), self.get_user_data(p2_id)
        old_p1, old_p2 = p1["elo"], p2["elo"]
        ea = 1 / (1 + 10 ** ((old_p2 - old_p1) / 400))
        eb = 1 / (1 + 10 ** ((old_p1 - old_p2) / 400))
        p1["elo"] = round(old_p1 + 32 * (result - ea))
        p2["elo"] = round(old_p2 + 32 * ((1 - result) - eb))
        if result == 1: p1["wins"]+=1; p2["losses"]+=1
        elif result == 0: p1["losses"]+=1; p2["wins"]+=1
        else: p1["draws"]+=1; p2["draws"]+=1
        self.save_user_data(p1_id, p1); self.save_user_data(p2_id, p2)
        return old_p1, p1["elo"], old_p2, p2["elo"]


# ==========================================
# GESTION DES IMAGES (anciennement util_image.py)
# ==========================================

def create_circle_mask(size):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    return mask

def add_border(img, border_width, color):
    size = img.size
    mask = create_circle_mask(size)
    bg_size = (size[0] + border_width * 2, size[1] + border_width * 2)
    border_img = Image.new("RGBA", bg_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img)
    draw.ellipse((0, 0) + bg_size, fill=color)
    border_img.paste(img, (border_width, border_width), mask)
    return border_img

async def create_result_img(p1, c1, p2, c2, winner_user):
    assets = Path(__file__).parent / "assets"
    choice_map = {'pierre': 'pierre.png', 'feuille': 'feuille.png', 'ciseaux': 'ciseaux.png'}
    
    # Fond
    if (assets / "fond.jpg").exists():
        bg = Image.open(assets / "fond.jpg").convert("RGBA").resize((1000, 500))
    else:
        bg = Image.new('RGBA', (1000, 500), (30, 30, 30, 255))

    # VS Central
    if (assets / "vs.jpg").exists():
        vs = Image.open(assets / "vs.jpg").convert("RGBA").resize((220, 220))
        bg.paste(vs, (390, 30), vs)

    draw = ImageDraw.Draw(bg)
    try: 
        font = ImageFont.truetype("arial.ttf", 30)
        font_big = ImageFont.truetype("arial.ttf", 45)
    except: font = font_big = ImageFont.load_default()

    async def get_avatar(user, size):
        async with aiohttp.ClientSession() as s:
            async with s.get(str(user.display_avatar.url)) as r:
                return Image.open(BytesIO(await r.read())).convert("RGBA").resize((size, size))

    # --- Préparation des pseudos (Majuscule 1ère lettre, pas de @) ---
    name1 = p1.name.capitalize()
    name2 = p2.name.capitalize()

    # --- Joueurs côtés ---
    av1 = await get_avatar(p1, 150)
    bg.paste(av1, (100, 100), create_circle_mask((150, 150)))
    draw.text((175, 270), name1, font=font, fill="white", anchor="mm")
    
    av2 = await get_avatar(p2, 150)
    bg.paste(av2, (750, 100), create_circle_mask((150, 150)))
    draw.text((825, 270), name2, font=font, fill="white", anchor="mm")

    # --- Signes ---
    for choice, x, mirror in [(c1, 100, False), (c2, 750, True)]:
        s_path = assets / choice_map[choice]
        if s_path.exists():
            s_img = Image.open(s_path).convert("RGBA").resize((150, 150))
            if mirror: s_img = s_img.transpose(Image.FLIP_LEFT_RIGHT)
            bg.paste(s_img, (x, 300), s_img)

    # --- LE GAGNANT (Sous le VS) ---
    if winner_user:
        win_av = await get_avatar(winner_user, 130)
        win_av_bordered = add_border(win_av, 6, (144, 238, 144, 255)) 
        
        # Positionnement sous le VS
        bg.paste(win_av_bordered, (429, 230), create_circle_mask(win_av_bordered.size))
        
        # Texte Vainqueur formaté
        win_name = winner_user.name.capitalize()
    else:
        draw.text((500, 300), "MATCH NUL", font=font_big, fill="#bdc3c7", anchor="mm")

    return bg


# ==========================================
# GESTION DE L'INTERFACE (anciennement util_embed.py)
# ==========================================

class SearchUserModal(ui.Modal, title="Chercher un profil"):
    user_id = ui.TextInput(label="ID Discord de l'utilisateur", placeholder="Collez l'ID ici...", min_length=17, max_length=20)
    def __init__(self, view):
        super().__init__()
        self.view = view
    async def on_submit(self, it: discord.Interaction):
        try:
            target = await self.view.cog.bot.fetch_user(int(self.user_id.value))
            await self.view.send_profile(it, target)
        except: await it.response.send_message("Utilisateur introuvable.", ephemeral=True)

class DuelView(ui.View):
    def __init__(self, cog, p1, p2):
        super().__init__(timeout=180)
        self.cog, self.p1, self.p2 = cog, p1, p2
        self.choices = {p1.id: None, p2.id: None}

    async def pick(self, it, c):
        import random
        if it.user.id not in self.choices:
            return await it.response.send_message("Pas ton match.", ephemeral=True)
        if self.choices[it.user.id]:
            return await it.response.send_message("Déjà fait !", ephemeral=True)
        self.choices[it.user.id] = c

        # Si solo contre le bot, le bot joue automatiquement
        is_vs_bot = self.p2.bot if hasattr(self.p2, 'bot') else False
        if is_vs_bot and self.choices[self.p2.id] is None:
            self.choices[self.p2.id] = random.choice(["pierre", "feuille", "ciseaux"])

        await it.response.send_message(f"Coup enregistré !", ephemeral=True)

        if all(self.choices.values()):
            res_idx = self.cog.get_winner(self.choices[self.p1.id], self.choices[self.p2.id])
            winner = [None, self.p1, self.p2][res_idx]
            looser = [None, self.p2, self.p1][res_idx]
            o1, n1, o2, n2 = self.cog.elo_manager.update_match(self.p1.id, self.p2.id, 0.5 if res_idx == 0 else (1 if res_idx == 1 else 0))

            content = f"🏆 {winner.mention} ({n1}) a gagné ! Tendu que {looser.mention} ({n2}) lui.." if winner else "🤝 Match nul !"

            img = await create_result_img(self.p1, self.choices[self.p1.id], self.p2, self.choices[self.p2.id], winner)
            with io.BytesIO() as out:
                img.save(out, 'PNG'); out.seek(0)
                desc = f"{self.p1.mention} : `{o1}` ➔ `{n1}`\n{self.p2.mention} : `{o2}` ➔ `{n2}`"
                emb = self.cog.make_emb(it, "🏁 Fin du Duel", desc)
                emb.set_image(url="attachment://res.png")
                await it.channel.send(content=content, embed=emb, file=discord.File(out, "res.png"))
                await it.message.delete()

    @ui.button(label="Pierre", emoji="✊")
    async def p(self, it, b): await self.pick(it, "pierre")
    @ui.button(label="Feuille", emoji="✋")
    async def f(self, it, b): await self.pick(it, "feuille")
    @ui.button(label="Ciseaux", emoji="✌️")
    async def c(self, it, b): await self.pick(it, "ciseaux")


# ===================== NOUVEAU LOBBY & CLASSEMENT =====================
class PFCLeaderboardView(ui.View):
    def __init__(self, cog, interaction, mode="server"):
        super().__init__(timeout=600)
        self.cog = cog
        self.interaction = interaction
        self.mode = mode
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        self.add_item(ui.Button(label="Serveur", style=discord.ButtonStyle.primary if self.mode=="server" else discord.ButtonStyle.secondary, custom_id="lb_server", emoji="🏢"))
        self.add_item(ui.Button(label="Global", style=discord.ButtonStyle.primary if self.mode=="global" else discord.ButtonStyle.secondary, custom_id="lb_global", emoji="🌍"))

    def get_embed(self, interaction):
        all_stats = []
        for file in self.cog.data_path.glob("*.json"):
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
        return self.cog.make_emb(interaction, title, desc)

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

class PFCLobbyView(ui.View):
    def __init__(self, cog, host_user, ctx):
        super().__init__(timeout=600)
        self.cog = cog
        self.host_user = host_user
        self.ctx = ctx
        self.waiting_list = []
        self.update_lobby()

    def get_lobby_embed(self):
        desc = (f"👤 **Hôte :** {self.host_user.mention}\n\n"
                f"🧠 **Mode :** Duel Pierre-Feuille-Ciseaux\n\n"
                f"👥 **Candidats en attente :**\n" + 
                ("\n".join([f"• <@{uid}>" for uid in self.waiting_list]) if self.waiting_list else "> *En attente d'adversaires...*"))
        return self.cog.make_emb(self.ctx, "⏳ Salon PFC", desc)

    def update_lobby(self, interaction=None):
        self.clear_items()
        self.add_item(ui.Button(label="Rejoindre", style=discord.ButtonStyle.primary, custom_id="join", emoji="🎮"))
        self.add_item(ui.Button(label="Jouer Solo", style=discord.ButtonStyle.secondary, custom_id="solo", emoji="🕹️"))
        self.add_item(ui.Button(label="Classement", style=discord.ButtonStyle.gray, custom_id="lb", emoji="🏆"))
        if self.waiting_list:
            options = []
            for uid in self.waiting_list[:25]:
                member = self.ctx.guild.get_member(uid) if self.ctx.guild else self.cog.bot.get_user(uid)
                name = member.display_name if member else f"Joueur inconnu ({uid})"
                options.append(discord.SelectOption(label=name[:100], value=str(uid), emoji="⚔️"))
            if options:
                self.add_item(ui.Select(placeholder="Choisir l'adversaire...", options=options, custom_id="select_adv"))
        # embed = self.get_lobby_embed()
        # if interaction:
        #     await interaction.response.edit_message(embed=embed, view=self)
        # return embed

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
        elif cid == "solo":
            if interaction.user.id != self.host_user.id:
                return await interaction.response.send_message("Seul l'hôte peut lancer le solo.", ephemeral=True)
            # Solo = duel contre le bot
            bot_user = self.cog.bot.user
            await interaction.response.edit_message(embed=self.cog.make_emb(interaction, "🕹️ Solo PFC", f"{self.host_user.mention} vs {bot_user.mention}"), view=DuelView(self.cog, self.host_user, bot_user))
        elif cid == "lb":
            lb_view = PFCLeaderboardView(self.cog, interaction)
            await interaction.response.send_message(embed=lb_view.get_embed(interaction), view=lb_view, ephemeral=True)
        elif cid == "select_adv":
            if interaction.user.id != self.host_user.id:
                return await interaction.response.send_message("Seul l'hôte peut choisir l'adversaire.", ephemeral=True)
            target_id = int(interaction.data['values'][0])
            target = self.ctx.guild.get_member(target_id) if self.ctx.guild else await self.cog.bot.fetch_user(target_id)
            if not target:
                return await interaction.response.send_message("❌ Joueur introuvable.", ephemeral=True)
            await interaction.response.edit_message(embed=self.cog.make_emb(interaction, "🕹️ Duel", f"{self.host_user.mention} vs {target.mention}"), view=DuelView(self.cog, self.host_user, target))
        return False


# ==========================================
# COG PRINCIPAL (anciennement pfc.py)
# ==========================================

class PFC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Nouveau chemin de data
        self.data_path = Path("data/public/jeux/data_pfc")
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.elo_manager = EloManager(self.data_path)

    def get_winner(self, c1, c2):
        if c1 == c2: return 0
        return 1 if (c1, c2) in [("pierre", "ciseaux"), ("feuille", "pierre"), ("ciseaux", "feuille")] else 2

    def make_emb(self, ctx_or_it, title, desc):
        """Le fameux Manager d'embed identique à pingpong.py"""
        user = ctx_or_it.author if isinstance(ctx_or_it, commands.Context) else ctx_or_it.user
        guild = ctx_or_it.guild
        
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=guild,
                user=user,
                bot=self.bot,
                title=title,
                description=desc,
                target_id=guild.id if guild else None
            )
        else:
            # Fallback si le manager est absent
            emb = discord.Embed(title=title, description=desc, color=0x2b2d31)
            if user:
                emb.set_footer(text=f"Demandé par {user.name}", icon_url=user.display_avatar.url)
            return emb

    @commands.hybrid_command(name="pfc")
    async def pfc(self, ctx: commands.Context):
        """Lance un salon pour jouer à Pierre-Feuille-Ciseaux (Solo ou Duel)."""
        view = PFCLobbyView(self, ctx.author, ctx)
        embed = view.get_lobby_embed()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(PFC(bot))