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

class NumberAnswerModal(discord.ui.Modal, title="🎯 Ta Proposition"):
    answer_input = discord.ui.TextInput(
        label="Quel est ton nombre ?",
        placeholder="Entre un nombre entre 1 et 100...",
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=3
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val_str = self.answer_input.value.strip()
            if not val_str.isdigit():
                return await interaction.response.send_message("❌ Propose un nombre valide !", ephemeral=True)
            
            guess = int(val_str)
            self.view.attempts += 1
            
            if guess == self.view.target_number:
                self.view.is_won = True
                self.view.winner = interaction.user
                self.view.parent_cog.save_progression(interaction.user.id)
                await interaction.response.defer()
                await self.view.update_message(final=True) # Appel immédiat pour le win
            else:
                diff = "↑ Plus !" if guess < self.view.target_number else "↓ Moins !"
                # Ajout du tag de l'utilisateur dans l'historique
                entry = f"{interaction.user.mention} : `{guess}` ({diff})"
                self.view.history.append(entry)
                if len(self.view.history) > 5: self.view.history.pop(0)
                
                await interaction.response.defer()
                await self.view.update_message()
                
                # Vérification défaite
                if self.view.attempts >= self.view.max_attempts and not self.view.is_won:
                    await self.view.update_message(final=True)
        except:
            traceback.print_exc()

########################################
# View Leaderboard (Pagination)
########################################

class NumberLeaderboardView(discord.ui.View):
    def __init__(self, parent_cog, data, author, current_page=0):
        super().__init__(timeout=120)
        self.parent_cog, self.data, self.author, self.current_page = parent_cog, data, author, current_page
        self.per_page = 10
        self.max_pages = math.ceil(len(data) / self.per_page)
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.max_pages > 1:
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
        embed = await self.parent_cog.create_lb_embed(interaction.guild, self.data, self.current_page, self.author)
        await interaction.response.edit_message(embed=embed, view=self)

########################################
# View du Jeu
########################################

class NumberView(discord.ui.View):
    def __init__(self, parent_cog, ctx, target_number):
        super().__init__(timeout=300)
        self.parent_cog, self.ctx = parent_cog, ctx
        self.target_number = target_number
        self.attempts, self.max_attempts = 0, 7
        self.is_won, self.winner = False, None
        self.message, self.history = None, []

    @discord.ui.button(label="Deviner", style=discord.ButtonStyle.success, emoji="🎯")
    async def guess_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.is_won or self.attempts >= self.max_attempts:
            await interaction.response.defer()
            await self.parent_cog.nombre.callback(self.parent_cog, self.ctx)
        else:
            await interaction.response.send_modal(NumberAnswerModal(self))

    @discord.ui.button(label=None, style=discord.ButtonStyle.secondary, emoji="🏆")
    async def lb_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Affiche à la fois le profil et le classement dans un embed unique
        user = interaction.user
        data = self.parent_cog.get_user_data(user.id)
        all_scores = self.parent_cog.get_leaderboard_data()
        rank = next((i for i, (uid, _) in enumerate(all_scores, 1) if uid == user.id), "N/A")
        desc = f"### 👤 Ton Profil\n> **Rang :** `#{rank}`\n> **Victoires :** `{data.get('wins', 0)}`\n\n### 🏆 Top 10\n"
        for i, (uid, count) in enumerate(all_scores[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i:02d}`"
            desc += f"{medal} <@{uid}> — `{count}` victoires\n"
        title = "🏆 Profil & Classement Nombre Magique"
        if config_manager:
            embed = config_manager.get_formatted_embed(guild=interaction.guild, user=user, bot=self.parent_cog.bot, title=title, description=desc, target_id=interaction.guild.id if interaction.guild else None)
        else:
            embed = discord.Embed(title=title, description=desc, color=0xffd700)
        embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def update_message(self, final=False):
        try:
            if not final:
                title = "🎯 Nombre Magique"
                hist_text = "\n".join(self.history) if self.history else "*Aucun essai pour le moment*"
                desc = (f"Un nombre entre **1** et **100** a été choisi.\n"
                        f"Essais restants : **{self.max_attempts - self.attempts}** / **{self.max_attempts}**\n\n"
                        f"📝 **Dernières tentatives :**\n{hist_text}")
            else:
                if self.is_won:
                    title = "🎉 Victoire !"
                    desc = (f"Le nombre magique était bien : **{self.target_number}**\n\n"
                            f"🏆 Trouvé par : {self.winner.mention}\n"
                            f"🔢 Nombre d'essais : `{self.attempts}`")
                    self.guess_btn.label, self.guess_btn.emoji = "Rejouer", "🆕"
                else:
                    title = "❌ Game Over"
                    desc = f"Dommage ! Personne n'a trouvé.\nLe nombre magique était : **{self.target_number}**"
                    self.guess_btn.disabled = True
                
                # On ne stop pas pour garder LB et Stats cliquables
                self.remove_item(self.guess_btn) if not self.is_won else None 

            if config_manager:
                embed = config_manager.get_formatted_embed(guild=self.ctx.guild, user=self.ctx.author, bot=self.parent_cog.bot, title=title, description=desc, target_id=self.ctx.guild.id if self.ctx.guild else None)
            else:
                color = 0x2ecc71 if self.is_won else 0xe74c3c if final else 0x2b2d31
                embed = discord.Embed(title=title, description=desc, color=color)
            
            if self.message: await self.message.edit(embed=embed, view=self)
            return embed
        except: traceback.print_exc()

########################################
# Cog GuessNumber
########################################

class GuessNumber(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path("data/public/jeux/data_nombre")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_user_data(self, user_id: int):
        path = self.data_dir / f"{user_id}.json"
        d = {"wins": 0}
        if path.exists():
            try:
                with open(path, "r", encoding='utf-8') as f:
                    d.update(json.load(f))
            except: pass
        return d

    def save_progression(self, user_id: int):
        data = self.get_user_data(user_id)
        data["wins"] = data.get("wins", 0) + 1
        with open(self.data_dir / f"{user_id}.json", "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_leaderboard_data(self):
        scores = []
        for file in self.data_dir.glob("*.json"):
            try:
                with open(file, "r", encoding='utf-8') as f:
                    count = json.load(f).get("wins", 0)
                if count > 0:
                    scores.append((int(file.stem), count))
            except: continue
        return sorted(scores, key=lambda x: x[1], reverse=True)

    async def create_lb_embed(self, guild, scores, page, author):
        start, end = page * 10, (page * 10) + 10
        slice_data = scores[start:end]
        lines = []
        for i, (uid, count) in enumerate(slice_data, start=start + 1):
            user = self.bot.get_user(uid)
            name = user.display_name if user else f"ID: {uid}"
            prefix = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`#{i}`"
            bold = "**" if uid == author.id else ""
            lines.append(f"{prefix} {bold}{name}{bold} — `{count}` victoires")
        
        desc = "\n".join(lines) if lines else "Aucun joueur."
        title = "🏆 Classement Nombre Magique"
        if config_manager:
            return config_manager.get_formatted_embed(guild=guild, user=author, bot=self.bot, title=title, description=desc, target_id=guild.id if guild else None)
        return discord.Embed(title=title, description=desc, color=0xffd700)

    async def send_leaderboard(self, source):
        author = source.user if isinstance(source, discord.Interaction) else source.author
        data = self.get_leaderboard_data()
        embed = await self.create_lb_embed(source.guild, data, 0, author)
        view = NumberLeaderboardView(self, data, author)
        if isinstance(source, discord.Interaction): await source.response.send_message(embed=embed, view=view, ephemeral=True)
        else: await source.send(embed=embed, view=view)

    async def send_profile_embed(self, source, user):
        data = self.get_user_data(user.id)
        all_scores = self.get_leaderboard_data()
        rank = next((i for i, (uid, _) in enumerate(all_scores, 1) if uid == user.id), "N/A")
        
        title = f"📊 Stats de {user.display_name}"
        desc = f"**🏆 Rang :** `#{rank}`\n**✅ Victoires :** `{data.get('wins', 0)}`"
        
        if config_manager:
            embed = config_manager.get_formatted_embed(guild=source.guild, user=user, bot=self.bot, title=title, description=desc, target_id=source.guild.id if source.guild else None)
        else:
            embed = discord.Embed(title=title, description=desc, color=0x3498db)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        if isinstance(source, discord.Interaction): await source.response.send_message(embed=embed, ephemeral=True)
        else: await source.send(embed=embed)

    @commands.hybrid_command(name="nombre", description="Devine un nombre entre 1 et 100.")
    async def nombre(self, ctx: commands.Context):
        target = random.randint(1, 100)
        view = NumberView(self, ctx, target)
        embed = await view.update_message()
        view.message = await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(GuessNumber(bot))