import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from pathlib import Path
from datetime import datetime
import asyncio

# ==============================================================================
# --------------------------- CONFIGURATION ------------------------------------
# ==============================================================================
DB_PATH = Path(__file__).parent / "dev_stats.db"

try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# --------------------------- INTERFACE UI (VIEW) ------------------------------
# ==============================================================================

class DevStatsView(discord.ui.View):
    def __init__(self, cog, ctx: commands.Context):
        super().__init__(timeout=180)
        self.cog = cog
        self.ctx = ctx
        self.current_tab = "servers"
        self.current_page = 0
        self.pages_cache = []

    async def get_content(self):
        if self.current_tab == "servers":
            self.pages_cache = await self.cog.get_server_list_pages()
        elif self.current_tab == "user_stats":
            self.pages_cache = await self.cog.get_user_stats_pages()
        elif self.current_tab == "guild_stats":
            self.pages_cache = await self.cog.get_guild_stats_pages()
        else: # global_commands
            self.pages_cache = await self.cog.get_global_commands_pages()
        return self.pages_cache

    def update_components(self):
        self.clear_items()
        
        # 1. Sélecteur de CATÉGORIE
        cat_options = [
            discord.SelectOption(label="Liste des Serveurs", emoji="🌐", value="servers", default=(self.current_tab == "servers")),
            discord.SelectOption(label="Utilisation des Commandes", emoji="🛠️", value="global_commands", default=(self.current_tab == "global_commands")),
            discord.SelectOption(label="Statistiques Utilisateurs", emoji="👤", value="user_stats", default=(self.current_tab == "user_stats")),
            discord.SelectOption(label="Statistiques Serveurs", emoji="📊", value="guild_stats", default=(self.current_tab == "guild_stats")),
        ]
        select_cat = discord.ui.Select(placeholder="📁 Choisir une catégorie...", options=cat_options)
        select_cat.callback = self.change_category
        self.add_item(select_cat)

        # 2. Sélecteur d'INSPECTION (Onglet serveurs)
        if self.current_tab == "servers" and self.pages_cache:
            current_guilds = self.cog.last_guild_chunks.get(self.current_page, [])
            if current_guilds:
                options_srv = [
                    discord.SelectOption(label=g.name[:100], description=f"ID: {g.id} | {g.member_count} membres", value=str(g.id))
                    for g in current_guilds
                ]
                select_srv = discord.ui.Select(placeholder="🔍 Inspecter un serveur de cette page...", options=options_srv)
                select_srv.callback = self.inspect_server
                self.add_item(select_srv)

        # 3. Sélecteur de PAGE
        if len(self.pages_cache) > 1:
            options_pg = [
                discord.SelectOption(label=f"Page {i+1}", value=str(i), default=(i == self.current_page))
                for i in range(min(len(self.pages_cache), 25))
            ]
            select_pg = discord.ui.Select(placeholder="📖 Changer de page...", options=options_pg)
            select_pg.callback = self.select_page
            self.add_item(select_pg)

    async def refresh(self, interaction: discord.Interaction):
        await self.get_content()
        if self.current_page >= len(self.pages_cache): self.current_page = 0
        self.update_components()
        await interaction.response.edit_message(embed=self.pages_cache[self.current_page], view=self)

    async def change_category(self, it: discord.Interaction):
        self.current_tab = it.data["values"][0]
        self.current_page = 0
        await self.refresh(it)

    async def select_page(self, it: discord.Interaction):
        self.current_page = int(it.data["values"][0])
        await self.refresh(it)

    async def inspect_server(self, it: discord.Interaction):
        guild_id = int(it.data["values"][0])
        embed = await self.cog.get_detailed_guild_embed(guild_id)
        await it.response.send_message(embed=embed, ephemeral=True)

# ==============================================================================
# --------------------------- COG PRINCIPAL ------------------------------------
# ==============================================================================

class DevStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_guild_chunks = {}
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER, guild_id INTEGER, username TEXT, 
                slash_count INTEGER DEFAULT 0, prefix_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id))""")
            conn.execute("""CREATE TABLE IF NOT EXISTS global_guild_stats (
                guild_id INTEGER PRIMARY KEY, guild_name TEXT,
                slash_count INTEGER DEFAULT 0, prefix_count INTEGER DEFAULT 0)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS command_stats (
                command_name TEXT, guild_id INTEGER,
                slash_count INTEGER DEFAULT 0, prefix_count INTEGER DEFAULT 0,
                PRIMARY KEY (command_name, guild_id))""")

    def _update_stats(self, user, guild, command_name, is_slash):
        col = "slash_count" if is_slash else "prefix_count"
        g_id = guild.id if guild else 0
        g_name = guild.name if guild else "DMs"
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(f"""INSERT INTO user_stats (user_id, guild_id, username, {col}) VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET {col} = {col} + 1, username = ?""", (user.id, g_id, str(user), str(user)))
            conn.execute(f"""INSERT INTO command_stats (command_name, guild_id, {col}) VALUES (?, ?, 1)
                ON CONFLICT(command_name, guild_id) DO UPDATE SET {col} = {col} + 1""", (command_name, g_id))
            if guild:
                conn.execute(f"""INSERT INTO global_guild_stats (guild_id, guild_name, {col}) VALUES (?, ?, 1)
                    ON CONFLICT(guild_id) DO UPDATE SET {col} = {col} + 1, guild_name = ?""", (g_id, g_name, g_name))

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command):
        self._update_stats(interaction.user, interaction.guild, command.name, True)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        self._update_stats(ctx.author, ctx.guild, ctx.command.name, False)

    def create_embed(self, title, description, thumbnail=None):
        if config_manager:
            return config_manager.get_formatted_embed(None, self.bot.user, self.bot, title, description, thumbnail)
        emb = discord.Embed(title=title, description=description, color=0x3498db)
        if thumbnail: emb.set_thumbnail(url=thumbnail)
        return emb

    async def _get_best_invite(self, guild: discord.Guild):
        """Force la récupération d'une invitation par tous les moyens possibles"""
        # 1. Tenter de trouver une invitation existante
        try:
            invites = await guild.invites()
            for inv in invites:
                if inv.max_age == 0 or not inv.expired: return inv.url
        except: pass

        # 2. Tenter de créer une invitation sur le premier salon disponible
        # On trie pour essayer les salons textuels d'abord
        channels = sorted(guild.channels, key=lambda x: isinstance(x, discord.TextChannel), reverse=True)
        for channel in channels:
            try:
                if channel.permissions_for(guild.me).create_instant_invite:
                    new_inv = await channel.create_invite(max_age=3600, max_uses=1, reason="DevStats Inspection")
                    return new_inv.url
            except: continue
        
        # 3. Vanité URL si disponible
        if guild.vanity_url_code:
            return f"https://discord.gg/{guild.vanity_url_code}"
            
        return "⚠️ Impossible de créer une invitation (Permissions manquantes)"

    async def get_detailed_guild_embed(self, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if not guild: return self.create_embed("Erreur", "Serveur introuvable.")
        
        invite_url = await self._get_best_invite(guild)
        with sqlite3.connect(DB_PATH) as conn:
            g_data = conn.execute("SELECT slash_count, prefix_count FROM global_guild_stats WHERE guild_id = ?", (guild_id,)).fetchone()
            top_users = conn.execute("SELECT username, slash_count, prefix_count FROM user_stats WHERE guild_id = ? ORDER BY (slash_count + prefix_count) DESC LIMIT 10", (guild_id,)).fetchall()
            top_cmds = conn.execute("SELECT command_name, slash_count, prefix_count FROM command_stats WHERE guild_id = ? ORDER BY (slash_count + prefix_count) DESC LIMIT 10", (guild_id,)).fetchall()

        s_cnt, p_cnt = (g_data[0], g_data[1]) if g_data else (0, 0)
        humans = len([m for m in guild.members if not m.bot])
        bots = guild.member_count - humans

        desc = (
            f"### 🌐 Informations Serveur\n"
            f"**Nom :** [{guild.name}]({invite_url})\n"
            f"**ID :** `{guild.id}`\n"
            f"**Création :** <t:{int(guild.created_at.timestamp())}:D>\n**Boosts :** `{guild.premium_subscription_count}`\n\n"
            f"### 👥 Membres\n└ Total : `{guild.member_count}` | Humains : `{humans}` | Bots : `{bots}`\n\n"
            f"### 📈 Utilisation\n└ Total : `{s_cnt + p_cnt}` | `Slash: {s_cnt}` | `Prefix: {p_cnt}`\n\n"
            f"### 🏆 Top 10 Utilisateurs\n"
        )
        desc += "\n".join([f"`{i+1}.` **{n}** : `{s+p}` `[S:{s}|P:{p}]`" for i, (n, s, p) in enumerate(top_users)])
        desc += "\n\n### 🛠️ Top 10 Commandes\n"
        desc += "\n".join([f"`{i+1}.` **{c}** : `{s+p}` `[S:{s}|P:{p}]`" for i, (c, s, p) in enumerate(top_cmds)])

        return self.create_embed(f"Inspection : {guild.name}", desc, guild.icon.url if guild.icon else None)

    async def get_server_list_pages(self):
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)
        per_page, pages = 25, []
        self.last_guild_chunks = {}
        for p in range(0, len(guilds), per_page):
            chunk = guilds[p:p+per_page]
            self.last_guild_chunks[p//per_page] = chunk
            desc = "### 🌐 Liste des Serveurs\n" + "\n".join([f"`{i+1:02d}.` **{g.name}** (`{g.id}`) • 👥 `{g.member_count}`" for i, g in enumerate(chunk, p)])
            pages.append(self.create_embed(f"Serveurs - Page {(p//per_page)+1}", desc))
        return pages

    async def get_global_commands_pages(self):
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT command_name, SUM(slash_count), SUM(prefix_count) FROM command_stats GROUP BY command_name ORDER BY (SUM(slash_count) + SUM(prefix_count)) DESC").fetchall()
        per_page, pages = 50, []
        for p in range(0, len(rows), per_page):
            chunk = rows[p:p+per_page]
            desc = "### 🛠️ Utilisation Globale des Commandes\n" + "\n".join([f"`{i+1:02d}.` **{c}** : `{s+pr}` `[S:{s}|P:{pr}]`" for i, (c, s, pr) in enumerate(chunk, p)])
            pages.append(self.create_embed(f"Commandes - Page {(p//per_page)+1}", desc))
        return pages if pages else [self.create_embed("Commandes", "Aucune donnée.")]

    async def get_user_stats_pages(self):
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT username, SUM(slash_count), SUM(prefix_count) FROM user_stats GROUP BY user_id ORDER BY (SUM(slash_count) + SUM(prefix_count)) DESC LIMIT 100").fetchall()
        pages = [self.create_embed("Stats Utilisateurs", "### 👤 Top Users Globaux\n" + "\n".join([f"`#{i+1:02d}` **{n}**\n└ Total: `{s+p}` `[S:{s}|P:{p}]`" for i, (n, s, p) in enumerate(rows[p:p+10], p+1)])) for p in range(0, len(rows), 10)]
        return pages if pages else [self.create_embed("Stats Users", "Aucune donnée.")]

    async def get_guild_stats_pages(self):
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT guild_name, slash_count, prefix_count FROM global_guild_stats ORDER BY (slash_count + prefix_count) DESC LIMIT 100").fetchall()
        pages = [self.create_embed("Stats Serveurs", "### 📊 Top Guilds Global\n" + "\n".join([f"`#{i+1:02d}` **{n}**\n└ Total: `{s+p}` `[S:{s}|P:{p}]`" for i, (n, s, p) in enumerate(rows[p:p+10], p+1)])) for p in range(0, len(rows), 10)]
        return pages if pages else [self.create_embed("Stats Guilds", "Aucune donnée.")]

    @commands.hybrid_command(name="devstats", description="Menu statistiques de développement")
    async def devstats(self, ctx: commands.Context):
        is_owner = await self.bot.is_owner(ctx.author)
        if not is_owner:
            return await ctx.send("❌ Seul l'owner du bot peut utiliser cette commande.", ephemeral=True)
        try:
            if hasattr(ctx, 'interaction') and ctx.interaction:
                await ctx.defer(ephemeral=True)
            else:
                pass
            view = DevStatsView(self, ctx)
            await view.get_content()
            view.update_components()
            if hasattr(ctx, 'interaction') and ctx.interaction:
                await ctx.send(embed=view.pages_cache[0], view=view, ephemeral=True)
            else:
                await ctx.send(embed=view.pages_cache[0], view=view)
        except Exception as e:
            raise

async def setup(bot: commands.Bot):
    await bot.add_cog(DevStats(bot))