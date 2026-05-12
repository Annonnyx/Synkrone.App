########################################
# Imports et dépendances
########################################

import discord
from discord.ext import commands
import random
import json
import traceback
import re
import asyncio
import time
import math
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

########################################
# Modals
########################################

class EnigmeAnswerModal(discord.ui.Modal, title="🧩 Ta Réponse"):
    answer_input = discord.ui.TextInput(
        label="Quelle est ta réponse ?",
        placeholder="Écris ici...",
        style=discord.TextStyle.short,
        required=True
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        user_raw = self.answer_input.value
        user_clean = self.view.parent_cog.normalize_answer(user_raw)
        target_clean = self.view.parent_cog.normalize_answer(self.view.dev_data["reponse"])

        if user_clean == target_clean:
            self.view.is_won = True
            self.view.winner = interaction.user
            self.view.parent_cog.save_progression(interaction.user.id, self.view.dev_index)
            await interaction.response.defer()
        else:
            entry = f"❌ **{interaction.user.display_name}** : `{user_raw}`"
            self.view.history.append(entry)
            if len(self.view.history) > 5: self.view.history.pop(0)
            await interaction.response.send_message("Ce n'est pas la bonne réponse !", ephemeral=True)
            await self.view.update_message()

########################################
# View Avancée Solo (Pagination)
########################################

class AvanceePaginationView(discord.ui.View):
    def __init__(self, parent_cog, user, all_devs, found_ids, rank, current_page=0):
        super().__init__(timeout=60)
        self.parent_cog = parent_cog
        self.user = user
        self.all_devs = all_devs
        self.found_ids = found_ids
        self.rank = rank
        self.current_page = current_page
        self.not_found = [i + 1 for i in range(len(all_devs)) if i not in found_ids]
        self.per_page = 50
        self.max_pages = min(25, math.ceil(len(self.not_found) / self.per_page))
        self.update_components()

    def update_components(self):
        self.clear_items()
        if self.max_pages > 1:
            select = discord.ui.Select(placeholder=f"Page {self.current_page + 1}...")
            for i in range(self.max_pages):
                select.add_option(label=f"Page {i+1}", value=str(i), default=(i == self.current_page))
            select.callback = self.select_callback
            self.add_item(select)

        btn_prev = discord.ui.Button(emoji="⬅️", style=discord.ButtonStyle.gray, disabled=(self.current_page <= 0))
        btn_prev.callback = self.prev_page
        self.add_item(btn_prev)

        btn_next = discord.ui.Button(emoji="➡️", style=discord.ButtonStyle.gray, disabled=(self.current_page >= self.max_pages - 1 or self.max_pages == 0))
        btn_next.callback = self.next_page
        self.add_item(btn_next)

    async def select_callback(self, interaction: discord.Interaction):
        self.current_page = int(interaction.data['values'][0])
        await self.update_view(interaction)

    async def prev_page(self, interaction: discord.Interaction):
        self.current_page -= 1
        await self.update_view(interaction)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page += 1
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        self.update_components()
        embed = self.parent_cog.create_avancee_embed(interaction.guild, self.user, self.all_devs, self.found_ids, self.rank, self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)

########################################
# View Leaderboard (Pagination)
########################################

class LeaderboardView(discord.ui.View):
    def __init__(self, parent_cog, data, total_max, author, current_page=0):
        super().__init__(timeout=120)
        self.parent_cog, self.data, self.total_max, self.author, self.current_page = parent_cog, data, total_max, author, current_page
        self.per_page = 50
        self.max_pages = math.ceil(len(data) / self.per_page)
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        btn_prev = discord.ui.Button(emoji="⬅️", disabled=(self.current_page <= 0))
        btn_prev.callback = self.prev_page
        self.add_item(btn_prev)

        btn_next = discord.ui.Button(emoji="➡️", disabled=(self.current_page >= self.max_pages - 1))
        btn_next.callback = self.next_page
        self.add_item(btn_next)

    async def prev_page(self, interaction):
        self.current_page -= 1
        await self.update_view(interaction)

    async def next_page(self, interaction):
        self.current_page += 1
        await self.update_view(interaction)

    async def update_view(self, interaction):
        self.update_buttons()
        embed = await self.parent_cog.create_lb_embed(interaction.guild, self.data, self.total_max, self.current_page, self.author)
        await interaction.response.edit_message(embed=embed, view=self)

########################################
# Menu avancé de classement inspiré de flags.py
########################################

class EnigmeLeaderboardView(discord.ui.View):
    def __init__(self, parent_cog, interaction, mode="server"):
        super().__init__(timeout=600)
        self.parent_cog = parent_cog
        self.interaction = interaction
        self.mode = mode
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        btn_server = discord.ui.Button(label="Serveur", style=discord.ButtonStyle.primary if self.mode=="server" else discord.ButtonStyle.secondary, custom_id="lb_server", emoji="🏢")
        btn_global = discord.ui.Button(label="Global", style=discord.ButtonStyle.primary if self.mode=="global" else discord.ButtonStyle.secondary, custom_id="lb_global", emoji="🌍")
        self.add_item(btn_server)
        self.add_item(btn_global)

    def get_embed(self, interaction=None):
        # Utiliser l'interaction stockée si aucune n'est fournie
        if interaction is None:
            interaction = self.interaction
            
        try:
            with open(self.parent_cog.json_path, "r", encoding="utf-8") as f:
                all_devs = json.load(f)
        except Exception as e:
            print(f"[DEBUG ENIGME] Erreur chargement devinettes.json: {e}")
            all_devs = []
            
        all_stats = []
        for file in self.parent_cog.data_dir.glob("*.json"):
            try:
                uid = int(file.stem)
                with open(file, "r", encoding="utf-8") as f2:
                    data = json.load(f2)
                    count = len(data.get("found_ids", []))
                    if count > 0:
                        all_stats.append({"uid": uid, "count": count})
            except Exception as e:
                print(f"[DEBUG ENIGME] Erreur lecture fichier {file}: {e}")
                pass
                
        if self.mode == "server" and interaction.guild:
            member_ids = [m.id for m in interaction.guild.members]
            all_stats = [s for s in all_stats if s["uid"] in member_ids]
            
        all_stats.sort(key=lambda x: x["count"], reverse=True)
        user_id = interaction.user.id
        user_rank = next((i for i, s in enumerate(all_stats) if s["uid"] == user_id), -1)
        
        desc = "###  Ton Profil\n"
        if user_rank != -1:
            u_data = all_stats[user_rank]
            desc += f"> **Position :** `#{user_rank + 1}`\n"
            desc += f"> **Score :** `{u_data['count']}/{len(all_devs)}`\n\n"
        else:
            desc += "> *Tu n'as encore résolu aucune énigme.*\n\n"
            
        desc += "### 🏆 Top 10\n"
        if not all_stats:
            desc += "*Aucun joueur classé pour le moment.*"
        else:
            for i, s in enumerate(all_stats[:10]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"`#{i+1:02d}`"
                desc += f"{medal} <@{s['uid']}> — `{s['count']}/{len(all_devs)}` énigmes\n"
                
        title = "🌍 Classement Interserveur" if self.mode == "global" else f"🏢 Classement {interaction.guild.name if interaction.guild else 'Serveur'}" 
        
        if config_manager:
            embed = config_manager.get_formatted_embed(guild=interaction.guild, user=interaction.user, bot=self.parent_cog.bot, title=title, description=desc, target_id=interaction.guild.id if interaction.guild else None)
        else:
            embed = discord.Embed(title=title, description=desc, color=0xffd700)
            
        return embed

    async def interaction_check(self, interaction):
        cid = interaction.data.get('custom_id')
        
        if cid == "lb_server":
            self.mode = "server"
            self.update_buttons()
            embed = self.get_embed(interaction)
            await interaction.response.edit_message(embed=embed, view=self)
        elif cid == "lb_global":
            self.mode = "global"
            self.update_buttons()
            embed = self.get_embed(interaction)
            await interaction.response.edit_message(embed=embed, view=self)
            
        return False

########################################
# View Enigme (Jeu)
########################################

class EnigmeView(discord.ui.View):
    def __init__(self, parent_cog, ctx, dev_data, dev_index):
        super().__init__(timeout=600)
        self.parent_cog, self.ctx, self.dev_data, self.dev_index = parent_cog, ctx, dev_data, dev_index
        self.start_time, self.duration, self.is_won, self.winner = time.time(), 300, False, None
        self.message, self.history, self.revealed_hints = None, [], []
        self.indices_config = {270: 0, 240: 1, 210: 2}

    @discord.ui.button(label="Répondre", style=discord.ButtonStyle.success, emoji="✍️")
    async def answer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EnigmeAnswerModal(self))

    @discord.ui.button(label="Classement", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def lb_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            lb_view = EnigmeLeaderboardView(self.parent_cog, interaction)
            embed = lb_view.get_embed(interaction)
            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, view=lb_view, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, view=lb_view, ephemeral=True)
        except Exception as e:
            print(f"[DEBUG ENIGME] Erreur lors de l'envoi: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)

    async def update_message(self, final=False):
        elapsed = time.time() - self.start_time
        remaining = max(0, self.duration - int(elapsed))
        indices = self.dev_data.get("indices", [])
        for t_limit, idx in self.indices_config.items():
            if remaining <= t_limit and idx < len(indices):
                hint_str = f"💡 **Indice :** {indices[idx]}"
                if hint_str not in self.revealed_hints: self.revealed_hints.append(hint_str)

        hints_text = "\n".join(self.revealed_hints) if self.revealed_hints else "*En attente...*"
        desc = f"**Énigme #{self.dev_index + 1} :**\n```\n{self.dev_data.get('enigme', self.dev_data.get('question', ''))}\n```\n🔎 **Indices :**\n{hints_text}\n"

        if not final:
            hist_text = "\n".join(self.history) if self.history else "*Aucun essai*"
            desc += f"\n⏳ Temps restant : **{remaining}s**\n📝 **Derniers essais :**\n{hist_text}"
            title = "🧩 Énigme en cours"
        else:
            res = f"🏆 **Gagné par {self.winner.mention} !**" if self.is_won else "⏱️ **Temps écoulé !**"
            desc += f"\n{res}\nLa réponse était : **{self.dev_data['reponse']}**"
            title = "🧩 Fin de l'Énigme"

        if config_manager:
            embed = config_manager.get_formatted_embed(guild=self.ctx.guild, user=self.ctx.author, bot=self.parent_cog.bot, title=title, description=desc, target_id=self.ctx.guild.id if self.ctx.guild else None)
        else:
            embed = discord.Embed(title=title, description=desc, color=0x2b2d31)

        if self.message:
            if final:
                self.children[0].disabled = True
                self.timeout = 180 
            try: await self.message.edit(embed=embed, view=self)
            except: pass
        return embed

    async def run_loop(self):
        while not self.is_won and (time.time() - self.start_time) < self.duration:
            await self.update_message(); await asyncio.sleep(5)
        await self.update_message(final=True)

    async def on_timeout(self):
        for item in self.children: item.disabled = True
        try: await self.message.edit(view=self)
        except: pass

########################################
# Cog Enigme
########################################

class Enigme(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.base_path = Path(__file__).parent
        self.json_path = self.base_path / "devinettes.json"
        self.data_dir = Path("data/public/jeux/data_enigme")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def normalize_answer(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"^(le |la |les |un |une |du |des |l'|d')", "", text)
        return text.translate(str.maketrans('', '', '?.!,;')).strip()

    def get_user_data(self, user_id: int):
        path = self.data_dir / f"{user_id}.json"
        if not path.exists(): return {"found_ids": []}
        with open(path, "r") as f: return json.load(f)

    def save_progression(self, user_id: int, dev_index: int):
        data = self.get_user_data(user_id)
        if dev_index not in data["found_ids"]:
            data["found_ids"].append(dev_index)
            with open(self.data_dir / f"{user_id}.json", "w") as f: json.dump(data, f, indent=4)

    def get_leaderboard_data(self):
        scores = []
        for file in self.data_dir.glob("*.json"):
            try:
                user_id = int(file.stem)
                with open(file, "r") as f: count = len(json.load(f).get("found_ids", []))
                if count > 0: scores.append((user_id, count))
            except: continue
        return sorted(scores, key=lambda x: x[1], reverse=True)

    def create_avancee_embed(self, guild, user, all_devs, found_ids, rank, page):
        total_devs, found_count = len(all_devs), len(found_ids)
        percent = (found_count / total_devs) * 100 if total_devs > 0 else 0
        not_found = [i + 1 for i in range(total_devs) if i not in found_ids]
        start, end = page * 50, (page * 50) + 50
        slice_ids = not_found[start:end]
        not_found_str = ", ".join([f"`#{idx}`" for idx in slice_ids]) if slice_ids else "Toutes les énigmes résolues ! 🎉"
        
        title = f"🏃 Progression : {user.display_name}"
        description = (f"**🏆 Classement :** `#{rank}`\n**📈 Progression :** `{found_count}`/`{total_devs}` (**{percent:.1f}%**)\n\n"
                       f"**🧩 Énigmes non résolues (Page {page+1}) :**\n{not_found_str}")
        if config_manager:
            return config_manager.get_formatted_embed(guild=guild, user=user, bot=self.bot, title=title, description=description, target_id=guild.id if guild else None)
        return discord.Embed(title=title, description=description, color=0x3498db)

    async def send_profile_embed(self, source, user):
        try:
            with open(self.json_path, "r", encoding="utf-8") as f: all_devs = json.load(f)
            user_data = self.get_user_data(user.id)
            all_scores = self.get_leaderboard_data()
            rank = next((i for i, (uid, _) in enumerate(all_scores, 1) if uid == user.id), "N/A")
            view = AvanceePaginationView(self, user, all_devs, user_data["found_ids"], rank)
            embed = self.create_avancee_embed(source.guild, user, all_devs, user_data["found_ids"], rank, 0)
            if isinstance(source, discord.Interaction): await source.response.send_message(embed=embed, view=view, ephemeral=True)
            else: await source.send(embed=embed, view=view)
        except: traceback.print_exc()

    async def create_lb_embed(self, guild, scores, total_max, page, author):
        start, end = page * 50, (page * 50) + 50
        slice_data = scores[start:end]
        lines = []
        for i, (uid, count) in enumerate(slice_data, start=start + 1):
            user = self.bot.get_user(uid)
            name = user.display_name if user else f"ID: {uid}"
            prefix = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
            if 3 < i <= 10: prefix = f"⭐ `{i}`"
            bold = "**" if uid == author.id else ""
            lines.append(f"{prefix} {bold}{name}{bold} — `{count} / {total_max}` pts")
        
        desc = "\n".join(lines) if lines else "Aucun joueur."
        title = "🏆 Classement des Énigmes"
        if config_manager:
            return config_manager.get_formatted_embed(guild=guild, user=author, bot=self.bot, title=title, description=desc, target_id=guild.id if guild else None)
        return discord.Embed(title=title, description=desc, color=0xffd700)

    async def send_leaderboard(self, source):
        author = source.user if isinstance(source, discord.Interaction) else source.author
        try:
            with open(self.json_path, "r", encoding="utf-8") as f: total_max = len(json.load(f))
            data = self.get_leaderboard_data()
            embed = await self.create_lb_embed(source.guild, data, total_max, 0, author)
            view = LeaderboardView(self, data, total_max, author)
            if isinstance(source, discord.Interaction): await source.response.send_message(embed=embed, view=view, ephemeral=True)
            else: await source.send(embed=embed, view=view)
        except: traceback.print_exc()

    @commands.hybrid_command(name="enigme", description="Lance une énigme.")
    async def enigme(self, ctx: commands.Context):
        try:
            with open(self.json_path, "r", encoding="utf-8") as f: all_devs = json.load(f)
            user_data = self.get_user_data(ctx.author.id)
            available = [i for i in range(len(all_devs)) if i not in user_data["found_ids"]]
            if not available: 
                await ctx.send("🎉 Tu as résolu toutes les énigmes !")
                return
            idx = random.choice(available)
            view = EnigmeView(self, ctx, all_devs[idx], idx)
            embed = await view.update_message()
            view.message = await ctx.send(embed=embed, view=view)
            asyncio.create_task(view.run_loop())
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")
            traceback.print_exc()

    
async def setup(bot: commands.Bot):
    await bot.add_cog(Enigme(bot))
