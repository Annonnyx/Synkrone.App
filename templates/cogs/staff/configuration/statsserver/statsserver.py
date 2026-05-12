import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import shutil

# --- IMPORTATION DU MANAGER ---
try:
    from .utils import config_manager
    HAS_MANAGER = True
except ImportError:
    try:
        from cogs.addons.embed_type.utils import config_manager
        HAS_MANAGER = True
    except ImportError:
        config_manager = None
        HAS_MANAGER = False

# --- GESTION DE LA DATA ---
BASE_PATH = os.path.join(os.path.dirname(__file__), "data")

def get_server_path(guild_id: int):
    path = os.path.join(BASE_PATH, str(guild_id))
    os.makedirs(path, exist_ok=True)
    return path

def save_config(guild_id: int, data: dict):
    with open(os.path.join(get_server_path(guild_id), "config.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_config(guild_id: int) -> dict:
    path = os.path.join(get_server_path(guild_id), "config.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

# --- UI COMPONENTS ---

class StatsDropdown(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(label="Membres (Humains)", value="member", emoji="👤"),
            discord.SelectOption(label="En ligne", value="online", emoji="🟢"),
            discord.SelectOption(label="Bots", value="bots", emoji="🤖"),
            discord.SelectOption(label="En Vocal", value="voice", emoji="🎙️")
        ]
        super().__init__(placeholder="Choisissez vos compteurs...", min_values=0, max_values=4, options=options)

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Permission insuffisante.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        old_data = load_config(guild.id)
        new_data = {}
        
        if len(self.values) == 0:
            for key in ["member", "online", "bots", "voice"]:
                if key in old_data:
                    ch = guild.get_channel(old_data[key])
                    if ch: await ch.delete()
            if "category_id" in old_data:
                cat = guild.get_channel(old_data["category_id"])
                if cat: await cat.delete()
            return await interaction.followup.send("✅ Statistiques désactivées.", ephemeral=True)

        category = guild.get_channel(old_data.get("category_id")) if old_data.get("category_id") else None
        if not category:
            overwrites = {guild.default_role: discord.PermissionOverwrite(connect=False)}
            category = await guild.create_category("📊│𝑆𝑡𝑎𝑡𝑖𝑠𝑡𝑖𝑞𝑢𝑒𝑠", overwrites=overwrites)
        
        new_data["category_id"] = category.id
        vals = self.cog.get_stats_values(guild)
        names = {
            "member": f"👤│{vals['member']} 𝑀𝑒𝑚𝑏𝑟𝑒𝑠",
            "online": f"🟢│{vals['online']} 𝐸𝑛 𝑙𝑖𝑔𝑛𝑒",
            "bots": f"🤖│{vals['bots']} 𝐵𝑜𝑡𝑠",
            "voice": f"🎙️│{vals['voice']} 𝐸𝑛 𝑣𝑜𝑐𝑎𝑙"
        }

        for key in ["member", "online", "bots", "voice"]:
            if key in self.values:
                channel = guild.get_channel(old_data.get(key))
                if not channel:
                    channel = await guild.create_voice_channel(names[key], category=category)
                new_data[key] = channel.id
            else:
                if key in old_data:
                    ch = guild.get_channel(old_data[key])
                    if ch: await ch.delete()

        save_config(guild.id, new_data)
        await interaction.followup.send("✅ Configuration mise à jour.", ephemeral=True)

# --- COG PRINCIPAL ---

class VoiceStatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    def get_stats_values(self, guild):
        humans = [m for m in guild.members if not m.bot]
        bots = [m for m in guild.members if m.bot]
        online = [m for m in humans if m.status != discord.Status.offline]
        voice = sum(len(vc.members) for vc in guild.voice_channels)
        return {"member": len(humans), "online": len(online), "bots": len(bots), "voice": voice}

    async def refresh_guild_channels(self, guild, voice_only=False):
        data = load_config(guild.id)
        if not data: return
        vals = self.get_stats_values(guild)
        mapping = {
            "member": (data.get("member"), f"👤│{vals['member']} 𝑀𝑒𝑚𝑏𝑟𝑒𝑠"),
            "online": (data.get("online"), f"🟢│{vals['online']} 𝐸𝑛 𝑙𝑖𝑔𝑛𝑒"),
            "bots": (data.get("bots"), f"🤖│{vals['bots']} 𝐵𝑜𝑡𝑠"),
            "voice": (data.get("voice"), f"🎙️│{vals['voice']} 𝐸𝑛 𝑣𝑜𝑐𝑎𝑙")
        }
        for key, (cid, name) in mapping.items():
            if cid:
                if voice_only and key != "voice": continue
                ch = guild.get_channel(cid)
                if ch and ch.name != name:
                    try: await ch.edit(name=name)
                    except: pass

    @tasks.loop(minutes=10.0)
    async def update_stats(self):
        for guild in self.bot.guilds:
            await self.refresh_guild_channels(guild)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            await self.refresh_guild_channels(member.guild, voice_only=True)

    # --- NOM DE COMMANDE MODIFIÉ POUR ÉVITER LE CONFLIT ---
    @commands.hybrid_command(name="statsserver", description="Configure les statistiques")
    @commands.has_permissions(administrator=True)
    async def statsserver(self, ctx: commands.Context):
        title = "📊│𝑆𝑡𝑎𝑡𝑖𝑠𝑡𝑖𝑞𝑢𝑒𝑠"
        description = "Configurez vos compteurs. (Commande : `/statsserver`)"
        
        if HAS_MANAGER and config_manager:
            embed = config_manager.get_formatted_embed(ctx.guild, ctx.author, self.bot, title, description, ctx.guild.id)
        else:
            embed = discord.Embed(title=title, description=description, color=0x2b2d31)

        await ctx.send(embed=embed, view=discord.ui.View().add_item(StatsDropdown(self)), ephemeral=True if ctx.interaction else False)

async def setup(bot):
    if not os.path.exists(BASE_PATH):
        os.makedirs(BASE_PATH)
    await bot.add_cog(VoiceStatsCog(bot))