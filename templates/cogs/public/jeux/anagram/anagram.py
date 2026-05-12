import discord
from discord.ext import commands
import random
import json
import asyncio
import time
import math
import traceback
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

class AnagramAnswerModal(discord.ui.Modal, title="🧩 Ta Réponse"):
    answer_input = discord.ui.TextInput(
        label="Quel est le mot caché ?",
        placeholder="Écris ta réponse ici...",
        style=discord.TextStyle.short,
        required=True
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_answer = self.answer_input.value.strip().upper()
            if user_answer == self.view.original_word:
                self.view.is_won = True
                self.view.winner = interaction.user
                self.view.parent_cog.save_progression(interaction.user.id, self.view.word_id)
                await interaction.response.defer()
            else:
                await interaction.response.send_message(" Ce n'est pas le bon mot !", ephemeral=True)
        except Exception:
            traceback.print_exc()

########################################
# View du Jeu
########################################

class AnagramView(discord.ui.View):
    def __init__(self, parent_cog, ctx, word_id, original_word, scrambled_word):
        super().__init__(timeout=600) # Timeout long pour laisser les boutons actifs
        self.parent_cog, self.ctx = parent_cog, ctx
        self.word_id, self.original_word, self.scrambled_word = word_id, original_word, scrambled_word
        self.start_time, self.duration = time.time(), 90
        self.is_won, self.winner = False, None
        self.message, self.hints_count = None, 0
        self.shuffle_count, self.max_shuffles = 0, 5
        self.revealed = ["_" for _ in original_word]

    @discord.ui.button(label="Répondre", style=discord.ButtonStyle.success, emoji="✍️")
    async def action_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.is_won or (time.time() - self.start_time) >= self.duration:
            await interaction.response.defer()
            # Relance la commande pour une nouvelle partie
            await self.parent_cog.anagram.callback(self.parent_cog, self.ctx)
        else:
            await interaction.response.send_modal(AnagramAnswerModal(self))

    @discord.ui.button(label="Mélanger (5)", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.shuffle_count < self.max_shuffles:
            self.shuffle_count += 1
            scrambled_list = list(self.original_word)
            random.shuffle(scrambled_list)
            self.scrambled_word = "".join(scrambled_list)
            while self.scrambled_word == self.original_word and len(self.original_word) > 1:
                random.shuffle(scrambled_list); scrambled = "".join(scrambled_list)
            
            button.label = f"Mélanger ({self.max_shuffles - self.shuffle_count})"
            if self.shuffle_count >= self.max_shuffles: button.disabled = True
            await self.update_message()
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Classement", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def lb_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            lb_view = AnagramLeaderboardView(self.parent_cog, interaction)
            embed = lb_view.get_embed(interaction)
            
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, view=lb_view, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, view=lb_view, ephemeral=True)
        except Exception as e:
            print(f"[DEBUG ANAGRAM] Erreur lors de l'envoi: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f" Erreur: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f" Erreur: {str(e)}", ephemeral=True)

    async def update_message(self, final=False):
        try:
            elapsed = time.time() - self.start_time
            remaining = max(0, self.duration - int(elapsed))
            
            # Indices à 60s et 30s
            if remaining <= 60 and self.hints_count == 0:
                self.revealed[0] = self.original_word[0]; self.hints_count = 1
            if remaining <= 30 and self.hints_count == 1 and len(self.original_word) > 1:
                for idx, char in enumerate(self.revealed):
                    if char == "_": self.revealed[idx] = self.original_word[idx]; break
                self.hints_count = 2

            if not final:
                title, status = f" Anagramme #{self.word_id}", f" Temps restant : **{remaining}s**"
                display_progression = ' '.join(self.revealed)
            else:
                if self.is_won:
                    title, status = f" Anagramme #{self.word_id} Trouvée !", f" Gagné par : {self.winner.mention}"
                    display_progression = ' '.join(list(self.original_word))
                    self.action_button.label, self.action_button.emoji = "Nouvelle Anagramme", "🔄"
                else:
                    title, status = f" Temps écoulé (#{self.word_id})", f"Le mot était : **{self.original_word}**"
                    display_progression = ' '.join(self.revealed)
                    self.action_button.disabled = True
                
                # Supprimer le bouton mélanger à la fin
                for child in list(self.children):
                    if hasattr(child, 'label') and child.label and "Mélanger" in child.label:
                        self.remove_item(child)

            desc = (f"Mot à décoder :\n# `{self.scrambled_word}`\n\n"
                    f" **Progression :** `{display_progression}` \n\n{status}")

            if config_manager:
                embed = config_manager.get_formatted_embed(guild=self.ctx.guild, user=self.ctx.author, bot=self.parent_cog.bot, title=title, description=desc, target_id=self.ctx.guild.id if self.ctx.guild else None)
            else:
                embed = discord.Embed(title=title, description=desc, color=0x2b2d31)
            
            if self.message: await self.message.edit(embed=embed, view=self)
            return embed
        except: traceback.print_exc()

    async def run_loop(self):
        while not self.is_won and (time.time() - self.start_time) < self.duration:
            await self.update_message(); await asyncio.sleep(5)
        await self.update_message(final=True)

########################################
# Menu avancé de classement inspiré de flags.py
########################################

class AnagramLeaderboardView(discord.ui.View):
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
                all_words = json.load(f)
        except Exception as e:
            print(f"[DEBUG ANAGRAM] Erreur chargement words.json: {e}")
            all_words = {}
            
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
                print(f"[DEBUG ANAGRAM] Erreur lecture fichier {file}: {e}")
                pass
                
        if self.mode == "server" and interaction.guild:
            member_ids = [m.id for m in interaction.guild.members]
            all_stats = [s for s in all_stats if s["uid"] in member_ids]
            
        all_stats.sort(key=lambda x: x["count"], reverse=True)
        user_id = interaction.user.id
        user_rank = next((i for i, s in enumerate(all_stats) if s["uid"] == user_id), -1)
        
        desc = "### Ton Profil\n"
        if user_rank != -1:
            u_data = all_stats[user_rank]
            desc += f"> **Position :** `#{user_rank + 1}`\n"
            desc += f"> **Score :** `{u_data['count']}/{len(all_words)}`\n\n"
        else:
            desc += "> *Tu n'as encore trouvé aucun mot.*\n\n"
            
        desc += "### Top 10\n"
        if not all_stats:
            desc += "*Aucun joueur classé pour le moment.*"
        else:
            for i, s in enumerate(all_stats[:10]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"`#{i+1:02d}`"
                desc += f"{medal} <@{s['uid']}> — `{s['count']}/{len(all_words)}` mots\n"
                
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
# Cog Anagramme
########################################

class Anagram(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_path = Path(__file__).parent
        self.json_path = self.base_path / "words.json"
        self.data_dir = Path("data/public/jeux/data_anagram")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.words_data = self.ensure_words_file()

    def ensure_words_file(self):
        if not self.json_path.exists():
            default = {"1": "BOL", "2": "CHAT", "3": "DRAGON"}
            with open(self.json_path, "w", encoding="utf-8") as f: json.dump(default, f, indent=4)
            return default
        with open(self.json_path, "r", encoding="utf-8") as f: return json.load(f)

    def get_user_data(self, user_id: int):
        path = self.data_dir / f"{user_id}.json"
        if not path.exists(): return {"found_ids": []}
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d if "found_ids" in d else {"found_ids": []}
        except: return {"found_ids": []}

    def save_progression(self, user_id: int, word_id: str):
        data = self.get_user_data(user_id)
        if "found_ids" not in data: data["found_ids"] = []
        if str(word_id) not in data["found_ids"]:
            data["found_ids"].append(str(word_id))
            with open(self.data_dir / f"{user_id}.json", "w", encoding="utf-8") as f: 
                json.dump(data, f, indent=4)

    def get_leaderboard_data(self):
        scores = []
        for file in self.data_dir.glob("*.json"):
            try:
                with open(file, "r") as f: count = len(json.load(f).get("found_ids", []))
                if count > 0: scores.append((int(file.stem), count))
            except: continue
        return sorted(scores, key=lambda x: x[1], reverse=True)

    async def create_lb_embed(self, guild, scores, total_max, page, author):
        start, end = page * 10, (page * 10) + 10
        slice_data = scores[start:end]
        lines = []
        for i, (uid, count) in enumerate(slice_data, start=start + 1):
            user = self.bot.get_user(uid)
            name = user.display_name if user else f"ID: {uid}"
            prefix = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
            bold = "**" if uid == author.id else ""
            lines.append(f"{prefix} {bold}{name}{bold} — `{count} / {total_max}` mots")
        
        desc = "\n".join(lines) if lines else "Aucun joueur."
        title = "🏆 Classement Anagrammes"
        if config_manager:
            return config_manager.get_formatted_embed(guild=guild, user=author, bot=self.bot, title=title, description=desc, target_id=guild.id if guild else None)
        return discord.Embed(title=title, description=desc, color=0xffd700)

    async def send_leaderboard(self, source):
        author = source.user if isinstance(source, discord.Interaction) else source.author
        try:
            data = self.get_leaderboard_data()
            total_max = len(self.words_data)
            embed = await self.create_lb_embed(source.guild, data, total_max, 0, author)
            view = AnagramLeaderboardView(self, data, total_max, author)
            if isinstance(source, discord.Interaction): await source.response.send_message(embed=embed, view=view, ephemeral=True)
            else: await source.send(embed=embed, view=view)
        except: traceback.print_exc()

    @commands.hybrid_command(name="anagram", description="Lance une anagramme.")
    async def anagram(self, ctx: commands.Context):
        try:
            user_data = self.get_user_data(ctx.author.id)
            available = [i for i in self.words_data.keys() if i not in user_data["found_ids"]]
            if not available: return await ctx.send("🎉 Tu as trouvé tous les mots !", ephemeral=True)
            
            word_id = random.choice(available)
            word = self.words_data[word_id].upper()
            scrambled_list = list(word); random.shuffle(scrambled_list)
            scrambled = "".join(scrambled_list)
            while scrambled == word and len(word) > 1:
                random.shuffle(scrambled_list); scrambled = "".join(scrambled_list)
            
            view = AnagramView(self, ctx, word_id, word, scrambled)
            embed = await view.update_message()
            view.message = await ctx.send(embed=embed, view=view)
            asyncio.create_task(view.run_loop())
        except: traceback.print_exc()

async def setup(bot):
    await bot.add_cog(Anagram(bot))