import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
import time
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "stats_bot.db")

# --- IMPORTATION MANAGER ---
try:
    from .utils import config_manager
except ImportError:
    try:
        from cogs.addons.embed_type.utils import config_manager
    except ImportError:
        config_manager = None

# ==============================================================================
# ----------------------- VUES POUR LES BOUTONS --------------------------------
# ==============================================================================

class StatsView(discord.ui.View):
    """Vue pour le classement du serveur ou le profil d'un membre ciblé"""
    def __init__(self, cog, target_member, guild_id, executor, current_period="30j"):
        super().__init__(timeout=None)
        self.cog = cog
        self.target_member = target_member
        self.guild_id = guild_id
        self.executor = executor
        self.current_period = periode = current_period
        self.update_buttons()

    def update_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label in ["1h", "24h", "7j", "30j"]:
                child.style = discord.ButtonStyle.primary if child.label == self.current_period else discord.ButtonStyle.secondary

    @discord.ui.button(label="1h")
    async def one_h(self, it, bt): await self.handle_period(it, "1h")
    @discord.ui.button(label="24h")
    async def twenty_four_h(self, it, bt): await self.handle_period(it, "24h")
    @discord.ui.button(label="7j")
    async def seven_d(self, it, bt): await self.handle_period(it, "7j")
    @discord.ui.button(label="30j")
    async def thirty_d(self, it, bt): await self.handle_period(it, "30j")

    @discord.ui.button(label="Regarder mon profil", style=discord.ButtonStyle.success)
    async def my_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        # On génère le profil éphémère avec sa propre vue pour changer de période
        embed = await self.cog.generate_stats_embed(interaction.user, interaction.guild.id, self.current_period, interaction.user, is_profile=True)
        view = ProfileView(self.cog, interaction.guild.id, interaction.user, self.current_period)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def handle_period(self, interaction: discord.Interaction, periode: str):
        self.current_period = periode
        self.update_buttons()
        embed = await self.cog.generate_stats_embed(self.target_member, self.guild_id, periode, interaction.user)
        await interaction.response.edit_message(embed=embed, view=self)

class ProfileView(discord.ui.View):
    """Vue spécifique pour le message éphémère 'Mon Profil'"""
    def __init__(self, cog, guild_id, user, current_period="30j"):
        super().__init__(timeout=120)
        self.cog = cog
        self.guild_id = guild_id
        self.user = user
        self.current_period = current_period
        self.update_buttons()

    def update_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.style = discord.ButtonStyle.primary if child.label == self.current_period else discord.ButtonStyle.secondary

    async def handle_click(self, interaction: discord.Interaction, periode: str):
        self.current_period = periode
        self.update_buttons()
        embed = await self.cog.generate_stats_embed(self.user, self.guild_id, periode, self.user, is_profile=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="1h")
    async def one_h(self, it, bt): await self.handle_click(it, "1h")
    @discord.ui.button(label="24h")
    async def twenty_four_h(self, it, bt): await self.handle_click(it, "24h")
    @discord.ui.button(label="7j")
    async def seven_d(self, it, bt): await self.handle_click(it, "7j")
    @discord.ui.button(label="30j")
    async def thirty_d(self, it, bt): await self.handle_click(it, "30j")

# ==============================================================================
# ------------------------------- COG STATS ------------------------------------
# ==============================================================================

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect(DB_PATH)
        self.cursor = self.db.cursor()
        self.create_tables()
        self.cleanup_task.start()
        self.voice_tracking = {}

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS activity (
            user_id INTEGER, guild_id INTEGER, type TEXT, value INTEGER, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.db.commit()

    @tasks.loop(hours=1)
    async def cleanup_task(self):
        limit = datetime.now() - timedelta(days=30)
        self.cursor.execute("DELETE FROM activity WHERE timestamp < ?", (limit,))
        self.db.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        self.cursor.execute("INSERT INTO activity (user_id, guild_id, type, value) VALUES (?, ?, 'message', 1)",
                           (message.author.id, message.guild.id))
        self.db.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not before.channel and after.channel:
            self.voice_tracking[member.id] = time.time()
        elif before.channel and not after.channel:
            start_time = self.voice_tracking.pop(member.id, None)
            if start_time:
                duration = int(time.time() - start_time)
                if duration > 1:
                    self.cursor.execute("INSERT INTO activity (user_id, guild_id, type, value) VALUES (?, ?, 'voice', ?)",
                                       (member.id, member.guild.id, duration))
                    self.db.commit()

    def format_duration(self, total_seconds):
        hours, remainder = divmod(int(max(0, total_seconds)), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"

    async def get_user_info(self, user_id, guild):
        member = guild.get_member(user_id)
        if member:
            return f"{member.mention} | `{member.name}` | `({user_id})`"
        try:
            user = await self.bot.fetch_user(user_id)
            return f"`{user.name}` | `({user_id})`"
        except:
            return f"`Inconnu` | `({user_id})`"

    async def generate_stats_embed(self, member, guild_id, periode, executor, is_profile=False):
        deltas = {"1h": 1, "24h": 24, "7j": 168, "30j": 720}
        since = (datetime.now() - timedelta(hours=deltas.get(periode, 720))).strftime('%Y-%m-%d %H:%M:%S')
        guild = self.bot.get_guild(guild_id)
        
        title = f"📊 Statistiques — {periode}"
        description = ""

        if member or is_profile:
            target = member or executor
            self.cursor.execute("SELECT type, SUM(value) FROM activity WHERE user_id = ? AND guild_id = ? AND timestamp > ? GROUP BY type", 
                               (target.id, guild_id, since))
            res = dict(self.cursor.fetchall())
            v_live = int(time.time() - self.voice_tracking.get(target.id, time.time())) if target.id in self.voice_tracking else 0
            user_msg = res.get('message', 0)
            user_voice = res.get('voice', 0) + v_live

            # Rangs (Messages)
            self.cursor.execute("SELECT user_id, SUM(value) FROM activity WHERE guild_id = ? AND type = 'message' AND timestamp > ? GROUP BY user_id ORDER BY SUM(value) DESC", (guild_id, since))
            rank_m = [r[0] for r in self.cursor.fetchall()]
            pos_m = rank_m.index(target.id) + 1 if target.id in rank_m else "N/A"

            # Rangs (Vocal)
            self.cursor.execute("SELECT user_id, SUM(value) FROM activity WHERE guild_id = ? AND type = 'voice' AND timestamp > ? GROUP BY user_id", (guild_id, since))
            v_totals = {r[0]: r[1] for r in self.cursor.fetchall()}
            for u_id, start_t in self.voice_tracking.items():
                v_totals[u_id] = v_totals.get(u_id, 0) + int(time.time() - start_t)
            
            sorted_v = sorted(v_totals.items(), key=lambda x: x[1], reverse=True)
            rank_v = [r[0] for r in sorted_v]
            pos_v = rank_v.index(target.id) + 1 if target.id in rank_v else "N/A"

            description = (
                f"### {'Mon Profil Personnel' if is_profile else f'Activité de {target.mention}'}\n"
                f"📝 Messages : `{user_msg}` (Rang : `#{pos_m}`)\n"
                f"🎙️ Vocal : `{self.format_duration(user_voice)}` (Rang : `#{pos_v}`)"
            )
        else:
            # --- CLASSEMENT SERVEUR ---
            self.cursor.execute("SELECT type, SUM(value) FROM activity WHERE guild_id = ? AND timestamp > ?", (guild_id, since))
            totals = dict(self.cursor.fetchall())
            total_msg = totals.get('message', 0) or 0
            total_voice_sec = totals.get('voice', 0) or 0
            for u_id, start_t in self.voice_tracking.items():
                total_voice_sec += int(time.time() - start_t)

            self.cursor.execute("SELECT user_id, SUM(value) FROM activity WHERE guild_id = ? AND type = 'message' AND timestamp > ? GROUP BY user_id ORDER BY SUM(value) DESC LIMIT 10", (guild_id, since))
            m_list = [f"**{i+1}.** {await self.get_user_info(r[0], guild)} : `{r[1]}`" for i, r in enumerate(self.cursor.fetchall())]

            self.cursor.execute("SELECT user_id, SUM(value) FROM activity WHERE guild_id = ? AND type = 'voice' AND timestamp > ? GROUP BY user_id", (guild_id, since))
            v_data = {r[0]: r[1] for r in self.cursor.fetchall()}
            for u_id, start_t in self.voice_tracking.items():
                v_data[u_id] = v_data.get(u_id, 0) + int(time.time() - start_t)
            
            sorted_v = sorted(v_data.items(), key=lambda x: x[1], reverse=True)[:10]
            v_list = [f"**{i+1}.** {await self.get_user_info(u_id, guild)} : `{self.format_duration(sec)}`" for i, (u_id, sec) in enumerate(sorted_v)]

            description = (
                f"📊 **Cumul Serveur** : `{total_msg}` messages | `{self.format_duration(total_voice_sec)}` vocal\n\n"
                f"### 🏆 Top 10 Messages\n" + ("\n".join(m_list) or "Aucune donnée") + "\n\n"
                f"### 🎙️ Top 10 Vocal\n" + ("\n".join(v_list) or "Aucune donnée")
            )

        if config_manager:
            embed = config_manager.get_formatted_embed(guild, executor, self.bot, title, description, guild_id)
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)
            embed.set_footer(text=f"Demandé par {executor.display_name}")

        return embed

    @commands.hybrid_command(name="stats", description="Statistiques d'activité du serveur")
    async def stats(self, ctx: commands.Context, membre: discord.Member = None):
        await ctx.defer()
        embed = await self.generate_stats_embed(membre, ctx.guild.id, "30j", ctx.author)
        view = StatsView(self, membre, ctx.guild.id, ctx.author, "30j")
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Stats(bot))